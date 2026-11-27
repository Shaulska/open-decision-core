"""Generate a self-contained interactive browser view of actual Python audit receipts."""
import argparse
import json
from pathlib import Path
from .benchmark import build_results

HTML = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Open Decision Core | Evidence replay</title>
<style>
:root{color-scheme:light;--navy:#12283b;--blue:#004e89;--line:#dce4eb;--muted:#506477}*{box-sizing:border-box}body{margin:0;font:15px/1.6 system-ui,sans-serif;color:var(--navy);background:#f4f7fa}main{max-width:1040px;margin:auto;padding:30px 24px 60px}header{border-bottom:1px solid var(--line);padding-bottom:20px;margin-bottom:24px}h1{font-size:clamp(27px,5vw,42px);line-height:1.15;margin:12px 0;color:var(--blue);letter-spacing:-.04em}h2{font-size:18px;margin:0 0 12px}p{margin:8px 0}.eyebrow{font-size:11px;letter-spacing:.14em;font-weight:700;color:var(--blue)}.muted,small{color:var(--muted)}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.panel{background:white;border:1px solid var(--line);border-radius:12px;padding:20px;margin:16px 0}.stat{padding:16px;background:white;border:1px solid var(--line);border-radius:10px}.stat strong{display:block;font-size:28px;line-height:1.2;color:var(--blue)}.form{display:grid;grid-template-columns:repeat(2,1fr);gap:16px}label{font-size:13px;font-weight:650}select{display:block;width:100%;font:inherit;padding:10px 8px;margin-top:5px;background:white;border:1px solid #a9bac8;border-radius:6px;color:var(--navy)}.verdict{font-size:28px;font-weight:750;margin:0}.PASS{color:#08734c}.BLOCK{color:#ae2932}.UNVERIFIED{color:#966000}table{border-collapse:collapse;width:100%;font-size:13px}th,td{padding:10px;text-align:left;border-bottom:1px solid var(--line)}th{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.06em}tr.selected{background:#e9f2fa}pre{white-space:pre-wrap;overflow-wrap:anywhere;max-height:340px;overflow:auto;background:#f4f7fa;padding:12px;border-radius:6px;font-size:12px}code{overflow-wrap:anywhere}a{color:var(--blue)}button{background:var(--blue);border:0;color:white;padding:10px 15px;border-radius:6px;font:inherit;cursor:pointer}button:focus-visible,select:focus-visible{outline:3px solid #76a9df;outline-offset:2px}summary{cursor:pointer;font-weight:650}footer{font-size:12px;color:var(--muted)}@media(max-width:600px){main{padding:20px 14px}.grid{grid-template-columns:1fr 1fr}.form{grid-template-columns:1fr}.panel{padding:15px}table{font-size:12px}td,th{padding:6px}}
</style></head><body><main>
<header><div class="eyebrow">OPEN DECISION CORE / MVP 0.3</div><h1>Could you have known it then?</h1><p>Explore a real-data audit of historical GDP revisions. Select a decision date and an exact version of the evidence.</p><small>Offline interactive view • generated from actual Python audit receipts, not a browser reimplementation.</small></header>
<div class="grid" id="stats"></div>
<section class="panel"><h2>1 / Choose a replay</h2><div class="form">
<label>Quarter<select id="quarter"><option>2024-Q1</option><option>2024-Q2</option></select></label>
<label>Decision after release<select id="cutoff"><option value="advance">Advance estimate</option><option value="second">Second estimate</option><option value="third">Third estimate</option></select></label>
<label>Evidence version<select id="version"><option value="advance">Advance estimate</option><option value="second">Second estimate</option><option value="third">Third estimate</option></select></label>
<label>Evidence requirement<select id="mode"><option value="PROVIDER_ASOF">Provider release time proxy</option><option value="OBSERVED_REPLAY">Historical local receipt</option></select></label></div><p id="hint" class="muted"></p></section>
<section class="panel" aria-live="polite"><h2>2 / Audit verdict</h2><div id="verdict" class="verdict"></div><p id="explain"></p><p id="times"></p><table><thead><tr><th>Version</th><th>GDP growth</th><th>Release (UTC−4)</th><th>Relative to decision</th></tr></thead><tbody id="timeline"></tbody></table><p><a id="source" target="_blank" rel="noopener noreferrer">Official release →</a></p></section>
<section class="panel"><h2>3 / Evidence and reproducibility</h2><p id="reason"></p><details><summary>Inspect full receipt</summary><pre id="receipt"></pre></details><p><button id="export">Save audit case JSON</button></p></section>
<section class="panel"><h2>One ecosystem, three stages</h2><p><b>Temporal audit (this MVP)</b> → verifies declared timing and exact versions.</p><p><b>Decision policy (planned)</b> → evaluates risk and abstention.</p><p><b>Research Lab (planned)</b> → compares forecasts and policies with independent outcomes.</p></section>
<footer>Source: U.S. Bureau of Economic Analysis. <a href="https://www.bea.gov/help/faq/147">Reuse policy</a>. Six curated releases, not a complete GDP vintage history. Published schedule is a proxy; actual local receipt is unknown. PASS is contract consistency, not authenticated provenance, predictive accuracy or authorization. No BEA endorsement implied.</footer>
</main><script type="application/json" id="data">__DATA__</script><script type="application/json" id="raw-records">__RECORDS__</script><script>
'use strict';const d=JSON.parse(document.getElementById('data').textContent);const el=id=>document.getElementById(id);const fmt=t=>t.slice(0,10)+' '+t.slice(11,16);let current;
for(const [k,v] of [['Cases',d.summary.cases],['Expected verdicts matched',d.summary.matched],['Future versions blocked',d.summary.counts.BLOCK]]){const a=document.createElement('div');a.className='stat';const b=document.createElement('strong');b.textContent=v;const c=document.createElement('small');c.textContent=k;a.append(b,c);el('stats').append(a)}
function render(){let q=el('quarter').value,c=el('cutoff').value,v=el('version').value,m=el('mode').value;
// Local-receipt controls are limited to matching-version cases in this benchmark.
if(m==='OBSERVED_REPLAY'){el('version').value=c;v=c;el('version').disabled=true;el('hint').textContent='Local-receipt examples use the matching release; no historical local receipt was recorded.'}else{el('version').disabled=false;el('hint').textContent='Select any of the three official release versions.'}
current=d.cases.find(x=>x.quarter===q&&x.cutoff_stage===c&&x.selected_stage===v&&x.mode===m);const r=current.receipt,e=current.evidence;
el('verdict').textContent=r.status;el('verdict').className='verdict '+r.status;el('explain').textContent={PASS:'No violation of the declared provider-time contract.',BLOCK:'The selected release was scheduled after the decision. The value itself need not change for its version to be unavailable.',UNVERIFIED:'Publication metadata cannot establish when the local system received this evidence.'}[r.status];el('times').textContent='Decision: '+fmt(current.decision.decision_at)+' EDT · selected value: '+e.value.toFixed(1)+'%';el('source').href=e.source_ref;el('reason').textContent=r.findings.length?r.findings.map(f=>f.code).join(' · '):'No findings under the implemented policy.';el('receipt').textContent=JSON.stringify(r,null,2);el('timeline').replaceChildren();
for(const a of d.records.filter(x=>x.entity===q)){const tr=document.createElement('tr');if(a.id===e.id)tr.className='selected';for(const val of [a.id.split('-').at(-1),a.value.toFixed(1)+'%',fmt(a.published_at),Date.parse(a.published_at)>Date.parse(current.decision.decision_at)?'After':'Before']){const td=document.createElement('td');td.textContent=val;tr.append(td)}el('timeline').append(tr)}}
for(const id of ['quarter','cutoff','version','mode'])el(id).addEventListener('change',render);el('export').addEventListener('click',()=>{const payload='{"bundle":{"schema_version":1,"evidence":'+el('raw-records').textContent+',"decisions":['+JSON.stringify(current.decision)+']},"receipt":'+JSON.stringify(current.receipt)+'}';const u=URL.createObjectURL(new Blob([payload],{type:'application/json'}));const a=document.createElement('a');a.href=u;a.download='odc-audit-case.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000)});render();
</script></body></html>'''


def render(results):
    data=json.dumps(results,ensure_ascii=True,separators=(',',':')).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    records=json.dumps(results['records'],ensure_ascii=True,separators=(',',':')).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    return HTML.replace('__RECORDS__',records).replace('__DATA__',data)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('fixture');p.add_argument('-o','--output',required=True)
    args=p.parse_args(argv)
    results=build_results(json.loads(Path(args.fixture).read_text(encoding='utf-8')))
    Path(args.output).write_text(render(results),encoding='utf-8')
    return 0

if __name__=='__main__': raise SystemExit(main())
