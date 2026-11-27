"""Deterministic checks of declared evidence; never verifies source truth or authorizes action."""
from datetime import datetime, timezone, timedelta
from hashlib import sha256
import json


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError('missing timestamp')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None or parsed.utcoffset() is None or 'T' not in value:
        raise ValueError('timezone-aware datetime required')
    return parsed.astimezone(timezone.utc)


def identity(value):
    return isinstance(value, str) and bool(value.strip())


def audit(bundle):
    findings = []
    def finding(code, status, record, decision=None):
        findings.append(dict(code=code, status=status, record=record, decision=decision))
    if not isinstance(bundle, dict) or bundle.get('schema_version') != 1 or type(bundle.get('schema_version')) is not int:
        raise ValueError('expected schema_version 1 bundle')
    rows, decisions = bundle.get('evidence'), bundle.get('decisions')
    if not isinstance(rows, list) or not isinstance(decisions, list):
        raise ValueError('evidence and decisions must be lists')
    evidence, conflicted = {}, set()
    versions = {}
    for row in rows:
        if not isinstance(row, dict) or not identity(row.get('id')):
            finding('INVALID_EVIDENCE_ID', 'BLOCK', None); continue
        rid = row['id']
        if rid in evidence:
            if digest(row) != digest(evidence[rid]):
                conflicted.add(rid); finding('CONFLICTING_ID', 'BLOCK', rid)
            continue
        evidence[rid] = row
        key = tuple(row.get(k) for k in ('source','entity','feature','version'))
        if not all(identity(k) for k in key):
            finding('INVALID_VERSION_KEY','BLOCK',rid); conflicted.add(rid)
        elif key in versions:
            other = versions[key]; conflicted.update((rid,other)); finding('DUPLICATE_VERSION_KEY','BLOCK',rid)
        else: versions[key] = rid
    seen_decisions = set()
    for decision in decisions:
        if not isinstance(decision, dict) or not identity(decision.get('id')):
            finding('INVALID_DECISION_ID','BLOCK',None); continue
        did = decision['id']
        if did in seen_decisions:
            finding('DUPLICATE_DECISION','BLOCK',did,did); continue
        seen_decisions.add(did)
        try: cutoff = timestamp(decision.get('decision_at'))
        except (ValueError, TypeError, OverflowError):
            finding('INVALID_DECISION_TIME','BLOCK',did,did); continue
        refs = decision.get('evidence_ids')
        if not isinstance(refs,list) or not refs or not all(identity(r) for r in refs) or len(set(refs)) != len(refs):
            finding('INVALID_EVIDENCE_REFS','BLOCK',did,did); continue
        if decision.get('mode') not in ('OBSERVED_REPLAY','PROVIDER_ASOF'):
            finding('DECISION_MODE_UNVERIFIED','UNVERIFIED',did,did)
        done, active = set(), set()
        def visit(rid):
            if rid in active:
                finding('LINEAGE_CYCLE','BLOCK',rid,did); return
            if rid in done: return
            if rid not in evidence:
                finding('MISSING_EVIDENCE','BLOCK',rid,did); return
            if rid in conflicted:
                finding('AMBIGUOUS_EVIDENCE','BLOCK',rid,did); return
            row = evidence[rid]; active.add(rid)
            times = {}
            for field in ('event_time','published_at','received_at','available_at'):
                if row.get(field) is not None:
                    try: times[field] = timestamp(row[field])
                    except (ValueError,TypeError,OverflowError): finding('INVALID_'+field.upper(),'BLOCK',rid,did)
            kind = row.get('availability_kind')
            usage = row.get('usage')
            if usage not in ('OBSERVATION','SCHEDULED','FORECAST'):
                finding('UNKNOWN_USAGE','UNVERIFIED',rid,did)
            if usage == 'OBSERVATION' and times.get('event_time',cutoff) > cutoff:
                finding('FUTURE_OBSERVATION','BLOCK',rid,did)
            if usage == 'OBSERVATION' and 'event_time' not in times:
                finding('UNKNOWN_EVENT_TIME','UNVERIFIED',rid,did)
            if row.get('precision') != 'SECOND':
                finding('UNSUPPORTED_PRECISION','UNVERIFIED',rid,did)
            if kind not in ('OBSERVED','PROVIDER_PUBLISHED'):
                finding('AVAILABILITY_UNVERIFIED','UNVERIFIED',rid,did)
            if kind == 'OBSERVED' and ('received_at' not in times or 'available_at' not in times):
                finding('MISSING_LOCAL_AVAILABILITY','UNVERIFIED',rid,did)
            if kind == 'PROVIDER_PUBLISHED':
                if decision.get('mode') != 'PROVIDER_ASOF': finding('NO_LOCAL_RECEIPT','UNVERIFIED',rid,did)
                if 'published_at' not in times: finding('MISSING_PUBLICATION_TIME','UNVERIFIED',rid,did)
                if 'published_at' in times and times.get('available_at') != times['published_at']:
                    finding('PUBLICATION_PROXY_MISMATCH','UNVERIFIED',rid,did)
            if 'available_at' not in times: finding('UNKNOWN_AVAILABILITY','UNVERIFIED',rid,did)
            for field in ('published_at','received_at','available_at'):
                if times.get(field,cutoff) > cutoff: finding('LATE_'+field.upper(),'BLOCK',rid,did)
            for a,b in [('published_at','received_at'),('published_at','available_at'),('received_at','available_at')]:
                if a in times and b in times and times[a]>times[b]: finding('TIME_ORDER_VIOLATION','BLOCK',rid,did)
            if usage == 'OBSERVATION' and 'event_time' in times:
                if any(times['event_time']>times[x] for x in ('published_at','received_at','available_at') if x in times):
                    finding('OBSERVATION_BEFORE_EVENT','BLOCK',rid,did)
            if not identity(row.get('source_ref')): finding('MISSING_SOURCE_REF','UNVERIFIED',rid,did)
            if 'value' not in row: finding('MISSING_VALUE','BLOCK',rid,did)
            parents = row.get('parents',[])
            if not isinstance(parents,list) or not all(identity(p) for p in parents): finding('INVALID_LINEAGE','BLOCK',rid,did)
            else:
                for parent in parents:
                    visit(parent)
                    parent_row = evidence.get(parent, {})
                    try:
                        if timestamp(parent_row.get('available_at')) > times['available_at']:
                            finding('DERIVED_BEFORE_PARENT','BLOCK',rid,did)
                    except (KeyError,ValueError,TypeError,OverflowError):
                        pass
            active.remove(rid); done.add(rid)
        for rid in refs: visit(rid)
    if not decisions: finding('NO_DECISIONS','UNVERIFIED',None)
    findings.sort(key=lambda f: (f['decision'] or '',f['record'] or '',f['code'],f['status']))
    counts = {s:sum(f['status']==s for f in findings) for s in ('BLOCK','UNVERIFIED')}
    status = 'BLOCK' if counts['BLOCK'] else 'UNVERIFIED' if counts['UNVERIFIED'] else 'PASS'
    result = dict(schema_version=1,policy='temporal-evidence-v0.1',input_sha256=digest(bundle),status=status,counts=counts,decisions=len(decisions),findings=findings,scope='Declared temporal evidence only; no source authentication, predictive validation or action authorization.')
    return dict(result,receipt_sha256=digest(result))


def verify(bundle, receipt):
    """Recompute from original input; no signature or external anchor."""
    return audit(bundle) == receipt


def replay(bundle, decision_id):
    """Return exact referenced evidence closure and the associated audit (never latest)."""
    matches=[d for d in bundle['decisions'] if isinstance(d,dict) and d.get('id')==decision_id]
    if len(matches)!=1: raise ValueError('expected unique decision ID')
    if not isinstance(matches[0].get('evidence_ids'),list) or not all(identity(x) for x in matches[0]['evidence_ids']): raise ValueError('invalid evidence references')
    # Audit all IDs to avoid silently selecting an ambiguous version.
    scoped=dict(bundle, decisions=matches)
    receipt=audit(scoped)
    ids=set(matches[0].get('evidence_ids',[])); changed=True
    while changed:
        old=len(ids)
        for row in bundle['evidence']:
            if isinstance(row,dict) and row.get('id') in ids and isinstance(row.get('parents'),list):
                ids.update(p for p in row['parents'] if identity(p))
        changed=len(ids)!=old
    return dict(decision=matches[0],evidence=[r for r in bundle['evidence'] if isinstance(r,dict) and r.get('id') in ids],receipt=receipt)


def split_check(manifest):
    """Minimal split manifest audit; explicit memberships, label availability, group isolation."""
    issues=[]
    try:
        fit=timestamp(manifest['fit_at']); test_start=timestamp(manifest['test_start'])
        embargo=manifest.get('embargo_seconds',0)
        if type(embargo) is not int or embargo<0: raise ValueError('embargo')
        train, test=manifest['train'],manifest['test']
        if not isinstance(train,list) or not isinstance(test,list) or not train or not test: raise ValueError('empty split')
        if fit>test_start: issues.append('FIT_AFTER_TEST_START')
        train_ids, test_ids=set(),set(); train_groups,test_groups=set(),set()
        for subset,ids,groups in [(train,train_ids,train_groups),(test,test_ids,test_groups)]:
            for r in subset:
                if not identity(r['id']) or not identity(r['group']): raise ValueError('ID/group')
                if r['id'] in ids: issues.append('DUPLICATE_ID')
                ids.add(r['id']); groups.add(r['group'])
        if train_ids & test_ids: issues.append('SPLIT_ID_OVERLAP')
        if train_groups & test_groups: issues.append('SPLIT_GROUP_OVERLAP')
        for r in train:
            label=timestamp(r['label_available_at']); sample=timestamp(r['sample_at'])
            if label>fit: issues.append('LATE_TRAIN_LABEL')
            if sample>fit: issues.append('TRAIN_AFTER_FIT')
            if label<sample: issues.append('LABEL_BEFORE_SAMPLE')
            if max(label,sample)+timedelta(seconds=embargo)>test_start: issues.append('EMBARGO_VIOLATION')
        for r in test:
            if timestamp(r['sample_at'])<test_start: issues.append('TEST_BEFORE_START')
    except (KeyError,ValueError,TypeError,OverflowError): return {'status':'UNVERIFIED','issues':sorted(set(issues+['INVALID_OR_INCOMPLETE_MANIFEST']))}
    return {'status':'BLOCK' if issues else 'PASS','issues':sorted(set(issues))}
