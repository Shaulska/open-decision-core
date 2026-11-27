"""Reproduce a small, public-data temporal audit. No network, no predictor."""
from collections import Counter
from datetime import date, timedelta
import json
from pathlib import Path
from .core import audit, digest

STAGES = ('advance', 'second', 'third')
ENDS = {'2024-Q1': '2024-03-31', '2024-Q2': '2024-06-30'}


def build_results(fixture):
    rows = fixture['releases']
    if len(rows) != 6 or {(r['quarter'], r['stage']) for r in rows} != {(q,s) for q in ENDS for s in STAGES}:
        raise ValueError('expected exactly six specified release vintages')
    records = []
    for r in rows:
        stamp = r['date'] + 'T08:30:00-04:00'
        records.append(dict(id=r['quarter']+'-'+r['stage'], source='US-BEA', entity=r['quarter'],
            feature='real_gdp_growth_annualized_pct', version=r['release'], value=r['value'],
            event_time=ENDS[r['quarter']]+'T23:59:59-04:00', published_at=stamp, available_at=stamp,
            received_at=None, precision='SECOND', availability_kind='PROVIDER_PUBLISHED',
            usage='OBSERVATION', source_ref=r['url'], parents=[]))
    cases = []
    for q in ENDS:
        for i,stage in enumerate(STAGES):
            cutoff = next(r for r in rows if r['quarter']==q and r['stage']==stage)
            day = (date.fromisoformat(cutoff['date'])+timedelta(days=1)).isoformat()
            for j,selected in enumerate(STAGES):
                for mode in ('PROVIDER_ASOF', 'OBSERVED_REPLAY') if i==j else ('PROVIDER_ASOF',):
                    rid=q+'-'+selected
                    did=f'{q}:{stage}:{selected}:{mode}'
                    decision=dict(id=did,decision_at=day+'T12:00:00-04:00',evidence_ids=[rid],mode=mode)
                    bundle=dict(schema_version=1,evidence=records,decisions=[decision])
                    receipt=audit(bundle)
                    expected='UNVERIFIED' if mode=='OBSERVED_REPLAY' else 'BLOCK' if j>i else 'PASS'
                    cases.append(dict(id=did,quarter=q,cutoff_stage=stage,selected_stage=selected,mode=mode,
                        decision=decision,evidence=next(r for r in records if r['id']==rid),expected=expected,receipt=receipt))
    counts=Counter(c['receipt']['status'] for c in cases)
    return dict(schema_version=1, fixture_sha256=digest(fixture), source=fixture['source'],
        scope=fixture['scope'], availability=fixture['availability'], unit=fixture['unit'],
        records=records, cases=cases, summary=dict(cases=len(cases), matched=sum(c['expected']==c['receipt']['status'] for c in cases),
        counts={k:counts[k] for k in ('PASS','BLOCK','UNVERIFIED')}))


def main(argv=None):
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('fixture');p.add_argument('-o','--output')
    args=p.parse_args(argv)
    result=build_results(json.loads(Path(args.fixture).read_text(encoding='utf-8')))
    output=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    if args.output: Path(args.output).write_text(output,encoding='utf-8')
    else: print(output,end='')
    return 0 if result['summary']['matched']==result['summary']['cases'] else 1

if __name__=='__main__': raise SystemExit(main())
