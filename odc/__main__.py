import argparse, json, sys, math
from pathlib import Path
from html import escape
from .core import audit, replay, verify, split_check

def load(path):
    def pairs(items):
        result={}
        for k,v in items:
            if k in result: raise ValueError('duplicate JSON key: '+k)
            result[k]=v
        return result
    def invalid(value): raise ValueError('invalid number: '+value)
    p=Path(path)
    if p.stat().st_size > 32*1024*1024: raise ValueError('input exceeds 32 MiB')
    def finite(value):
        result=float(value)
        if not math.isfinite(result): raise ValueError('nonfinite number')
        return result
    return json.loads(p.read_text(encoding='utf-8'),object_pairs_hook=pairs,parse_constant=invalid,parse_float=finite)

def html_report(receipt):
    esc=lambda x: escape(str(x))
    rows=''.join('<tr>'+''.join('<td>'+esc(f[k])+'</td>' for k in ('decision','record','code','status'))+'</tr>' for f in receipt['findings'])
    return f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ODC | Temporal evidence audit</title><style>body{{font:16px system-ui;max-width:1000px;margin:40px auto;padding:24px;color:#172b3c;background:#f5f7fa}}h1{{color:#004e89}}section{{background:white;border:1px solid #dce4eb;border-radius:12px;padding:24px;margin:20px 0}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{padding:12px;text-align:left;border-bottom:1px solid #dce4eb;overflow-wrap:anywhere}}code{{overflow-wrap:anywhere}}small{{color:#526778}}</style><small>OPEN DECISION CORE / EXPERIMENTAL MVP</small><h1>Temporal evidence audit</h1><section><small>DECLARED CONTRACT VERDICT</small><h2>{esc(receipt['status'])}</h2><p>{receipt['decisions']} decisions · {receipt['counts']['BLOCK']} blocking findings · {receipt['counts']['UNVERIFIED']} unverified findings</p><p>{esc(receipt['scope'])}</p></section><section><h2>Findings</h2><table><thead><tr><th>Decision</th><th>Evidence</th><th>Reason</th><th>Status</th></tr></thead><tbody>{rows}</tbody></table></section><section><h2>Reproducibility</h2><p>Input SHA-256<br><code>{esc(receipt['input_sha256'])}</code></p><p>Receipt SHA-256<br><code>{esc(receipt['receipt_sha256'])}</code></p><p>Hashes are not signatures.</p></section></html>'''

def main(argv=None):
    p=argparse.ArgumentParser(prog='odc'); sub=p.add_subparsers(dest='command',required=True)
    for cmd in ('audit','replay','verify','split-check','report'):
        s=sub.add_parser(cmd); s.add_argument('input'); s.add_argument('-o','--output')
        if cmd=='replay': s.add_argument('decision_id')
        if cmd=='verify': s.add_argument('receipt')
    args=p.parse_args(argv)
    try:
        data=load(args.input)
        if args.command=='verify': result={'verified':verify(data,load(args.receipt))}; status='PASS' if result['verified'] else 'BLOCK'
        elif args.command=='split-check': result=split_check(data); status=result['status']
        elif args.command=='replay': result=replay(data,args.decision_id); status=result['receipt']['status']
        else: result=audit(data); status=result['status']
        output=html_report(result) if args.command=='report' else json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n'
        if args.output: Path(args.output).write_text(output,encoding='utf-8')
        else: print(output,end='')
        return {'PASS':0,'BLOCK':2,'UNVERIFIED':3}[status]
    except (ValueError,KeyError,TypeError,OverflowError,OSError,RecursionError) as exc:
        print('odc: '+str(exc),file=sys.stderr); return 4

if __name__=='__main__': raise SystemExit(main())
