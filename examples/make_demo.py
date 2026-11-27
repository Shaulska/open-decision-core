"""Generate clearly synthetic decision receipts. Run from repository root."""
from pathlib import Path
from copy import deepcopy
import json
from odc import audit
from odc.__main__ import html_report

out=Path(__file__).parent
base={'id':'load-v1','source':'mock-server','entity':'demo-service','feature':'load','version':'1','value':42,'event_time':'2026-01-01T10:00:00Z','published_at':'2026-01-01T10:01:00Z','received_at':'2026-01-01T10:02:00Z','available_at':'2026-01-01T10:03:00Z','precision':'SECOND','availability_kind':'OBSERVED','usage':'OBSERVATION','source_ref':'synthetic:server-telemetry','parents':[]}
evidence=[base,dict(base,id='load-v2',version='2',value=78,received_at='2026-01-01T12:15:00Z',available_at='2026-01-01T12:16:00Z'),dict(base,id='load-unknown',version='3',received_at=None,available_at=None,availability_kind='UNKNOWN')]
all_decisions=[]
for name,eid in [('timely','load-v1'),('future-revision','load-v2'),('unknown','load-unknown')]:
    d={'id':name,'decision_at':'2026-01-01T12:00:00Z','evidence_ids':[eid],'mode':'OBSERVED_REPLAY'}; all_decisions.append(d)
    b={'schema_version':1,'evidence':evidence,'decisions':[d]}; r=audit(b)
    (out/f'{name}.json').write_text(json.dumps(b,indent=2)+'\n'); (out/f'{name}.receipt.json').write_text(json.dumps(r,indent=2)+'\n')
    print(name,r['status'],r['counts'])
b={'schema_version':1,'evidence':evidence,'decisions':all_decisions}; r=audit(b)
(out/'demo.json').write_text(json.dumps(b,indent=2)+'\n'); (out/'demo.receipt.json').write_text(json.dumps(r,indent=2)+'\n')
(out/'demo.html').write_text(html_report(r))
