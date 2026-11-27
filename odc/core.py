"""Deterministic checks of declared evidence; never verifies source truth or authorizes action."""
from datetime import datetime, timezone, timedelta
from hashlib import sha256
import json
import re

MAX_EVIDENCE = 10000
MAX_DECISIONS = 1000
MAX_REFERENCES = 1000
MAX_DEPTH = 128
MAX_VISITS = 100000
ISO_TIME = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?(?:Z|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])")


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def timestamp(value):
    if not isinstance(value, str) or not ISO_TIME.fullmatch(value) or value.endswith('-00:00'):
        raise ValueError('explicit RFC3339 timestamp required')
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
    if len(rows) > MAX_EVIDENCE or len(decisions) > MAX_DECISIONS:
        raise ValueError('bundle exceeds evidence or decision limit')
    evidence, conflicted = {}, set()
    visits = 0
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
        if not isinstance(refs,list) or not refs or len(refs)>MAX_REFERENCES or not all(identity(r) for r in refs) or len(set(refs)) != len(refs):
            finding('INVALID_EVIDENCE_REFS','BLOCK',did,did); continue
        if decision.get('mode') not in ('OBSERVED_REPLAY','PROVIDER_ASOF'):
            finding('DECISION_MODE_UNVERIFIED','UNVERIFIED',did,did)
        done, active = set(), set()
        def visit(rid, depth=0):
            nonlocal visits
            visits += 1
            if depth > MAX_DEPTH or visits > MAX_VISITS:
                raise ValueError('lineage exceeds audit traversal limit')
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
            minute_proxy = row.get('precision') == 'MINUTE' and kind == 'PROVIDER_PUBLISHED' and row.get('received_at') is None
            if row.get('precision') != 'SECOND' and not minute_proxy:
                finding('UNSUPPORTED_PRECISION','UNVERIFIED',rid,did)
            if minute_proxy:
                for field in ('published_at','available_at'):
                    if field in times:
                        start = times[field]
                        if start.second or start.microsecond:
                            finding('INVALID_MINUTE_BOUNDARY','BLOCK',rid,did)
                        elif start <= cutoff < start + timedelta(minutes=1):
                            finding('WITHIN_PUBLICATION_MINUTE','UNVERIFIED',rid,did)
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
                before, uncertain = False, False
                for field in ('published_at','received_at','available_at'):
                    if field not in times or times['event_time'] <= times[field]: continue
                    if minute_proxy and field != 'received_at' and times['event_time'] < times[field]+timedelta(minutes=1):
                        uncertain = True
                    else:
                        before = True
                if before: finding('OBSERVATION_BEFORE_EVENT','BLOCK',rid,did)
                if uncertain: finding('OBSERVATION_TIME_ORDER_UNVERIFIED','UNVERIFIED',rid,did)
            if not identity(row.get('source_ref')): finding('MISSING_SOURCE_REF','UNVERIFIED',rid,did)
            if 'value' not in row: finding('MISSING_VALUE','BLOCK',rid,did)
            parents = row.get('parents')
            if 'parents' not in row:
                finding('MISSING_LINEAGE','UNVERIFIED',rid,did)
            elif not isinstance(parents,list) or len(parents)>MAX_REFERENCES or not all(identity(p) for p in parents) or len(set(parents))!=len(parents): finding('INVALID_LINEAGE','BLOCK',rid,did)
            else:
                for parent in parents:
                    visit(parent, depth+1)
                    parent_row = evidence.get(parent, {})
                    try:
                        parent_start = timestamp(parent_row.get('available_at'))
                        child_start = times['available_at']
                        parent_minute = parent_row.get('precision') == 'MINUTE'
                        child_minute = minute_proxy
                        if parent_start > child_start and (not child_minute or parent_start >= child_start + timedelta(minutes=1)):
                            finding('DERIVED_BEFORE_PARENT','BLOCK',rid,did)
                        elif (parent_minute and parent_start <= child_start < parent_start + timedelta(minutes=1)) or (child_minute and child_start < parent_start < child_start + timedelta(minutes=1)):
                            finding('LINEAGE_TIME_ORDER_UNVERIFIED','UNVERIFIED',rid,did)
                    except (KeyError,ValueError,TypeError,OverflowError):
                        pass
            active.remove(rid); done.add(rid)
        for rid in refs: visit(rid)
    if not decisions: finding('NO_DECISIONS','UNVERIFIED',None)
    findings.sort(key=lambda f: (f['decision'] or '',f['record'] or '',f['code'],f['status']))
    counts = {s:sum(f['status']==s for f in findings) for s in ('BLOCK','UNVERIFIED')}
    status = 'BLOCK' if counts['BLOCK'] else 'UNVERIFIED' if counts['UNVERIFIED'] else 'PASS'
    result = dict(schema_version=1,policy='temporal-evidence-v0.3',input_sha256=digest(bundle),status=status,counts=counts,decisions=len(decisions),findings=findings,scope='Declared temporal evidence only; no source authentication, predictive validation or action authorization.')
    return dict(result,receipt_sha256=digest(result))


def verify(bundle, receipt):
    """Recompute from original input; no signature or external anchor."""
    try:
        return digest(audit(bundle)) == digest(receipt)
    except (ValueError, TypeError, OverflowError, RecursionError):
        return False


def replay(bundle, decision_id):
    """Return exact referenced evidence closure and the associated audit (never latest)."""
    matches=[d for d in bundle['decisions'] if isinstance(d,dict) and d.get('id')==decision_id]
    if len(matches)!=1: raise ValueError('expected unique decision ID')
    if not isinstance(matches[0].get('evidence_ids'),list) or not all(identity(x) for x in matches[0]['evidence_ids']): raise ValueError('invalid evidence references')
    # Audit all IDs to avoid silently selecting an ambiguous version.
    scoped=dict(bundle, decisions=matches)
    receipt=audit(scoped)
    # Index all valid IDs, retaining duplicate rows for diagnostics.
    indexed = {}
    for row in bundle['evidence']:
        if isinstance(row,dict) and identity(row.get('id')):
            indexed.setdefault(row['id'], []).append(row)
    ids=set(); pending=list(matches[0]['evidence_ids'])
    while pending:
        rid=pending.pop()
        if rid in ids: continue
        ids.add(rid)
        for row in indexed.get(rid, []):
            parents=row.get('parents')
            if isinstance(parents,list): pending.extend(p for p in parents if identity(p))
    return dict(decision=matches[0],evidence=[r for r in bundle['evidence'] if isinstance(r,dict) and identity(r.get('id')) and r['id'] in ids],receipt=receipt)


def split_check(manifest):
    """Minimal split manifest audit; explicit memberships, label availability, group isolation."""
    issues=set(); incomplete=False
    def read_time(row,key):
        nonlocal incomplete
        try: return timestamp(row[key])
        except (KeyError,ValueError,TypeError,OverflowError): incomplete=True; return None
    if not isinstance(manifest,dict): return {'status':'UNVERIFIED','issues':['INVALID_OR_INCOMPLETE_MANIFEST']}
    fit=read_time(manifest,'fit_at'); test_start=read_time(manifest,'test_start')
    embargo=manifest.get('embargo_seconds',0)
    if type(embargo) is not int or not 0<=embargo<=3153600000: embargo=None; incomplete=True
    if fit and test_start and fit>test_start: issues.add('FIT_AFTER_TEST_START')
    train_ids,test_ids=set(),set(); train_groups,test_groups=set(),set()
    for name,ids,groups in [('train',train_ids,train_groups),('test',test_ids,test_groups)]:
        rows=manifest.get(name)
        if not isinstance(rows,list) or not rows or len(rows)>MAX_EVIDENCE:
            incomplete=True; continue
        for r in rows:
            if not isinstance(r,dict): incomplete=True; continue
            if identity(r.get('id')):
                if r['id'] in ids: issues.add('DUPLICATE_ID')
                ids.add(r['id'])
            else: incomplete=True
            if identity(r.get('group')): groups.add(r['group'])
            else: incomplete=True
            sample=read_time(r,'sample_at')
            if name=='test':
                if sample and test_start and sample<test_start: issues.add('TEST_BEFORE_START')
                continue
            label=read_time(r,'label_available_at')
            if label and fit and label>fit: issues.add('LATE_TRAIN_LABEL')
            if sample and fit and sample>fit: issues.add('TRAIN_AFTER_FIT')
            if label and sample and label<sample: issues.add('LABEL_BEFORE_SAMPLE')
            if label and sample and test_start and embargo is not None:
                if (test_start-max(label,sample)).total_seconds()<embargo: issues.add('EMBARGO_VIOLATION')
    if train_ids & test_ids: issues.add('SPLIT_ID_OVERLAP')
    if train_groups & test_groups: issues.add('SPLIT_GROUP_OVERLAP')
    status='BLOCK' if issues else 'UNVERIFIED' if incomplete else 'PASS'
    if incomplete: issues.add('INVALID_OR_INCOMPLETE_MANIFEST')
    return {'status':status,'issues':sorted(issues)}
