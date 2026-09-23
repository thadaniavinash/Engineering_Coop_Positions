"""Offline validation, history and report helper. Web research is performed by the desktop agent.
Usage: python report.py findings.json --output reports
No network calls, API keys or third-party Python packages required.
"""
import argparse
import csv
import html
import json
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

MIN_START = '2027-05'

def key(row):
    if row.get('job_id'):
        return row['employer'].casefold().strip() + ':' + row['job_id'].casefold().strip()
    u = urlsplit(row['url'])
    query=urlencode(sorted((k,v) for k,v in parse_qsl(u.query) if not k.lower().startswith('utm_') and k.lower() not in ('source','ref','trackingid')))
    return row['employer'].casefold().strip() + ':' + urlunsplit((u.scheme, u.netloc.lower(), u.path.rstrip('/'), query, ''))

def classify(row):
    if row.get('closed') is True:
        return 'Closed'
    if row.get('excluded_reason'):
        return 'Excluded'
    if row.get('computer_engineering') is True:
        return 'Excluded'
    if row.get('ontario') is False or row.get('engineering_fit', row.get('mechanical_fit')) is False or row.get('student_role') is False:
        return 'Excluded'
    start = row.get('start_month')
    if start:
        date.fromisoformat(start + '-01')
        if start < MIN_START:
            return 'Excluded'
    months = row.get('duration_months', [])
    if row.get('duration_complete') and not set(months).intersection({12, 16}):
        return 'Excluded'
    required = ('ontario', 'student_role', 'official_verified', 'live_verified', 'eligibility_compatible')
    if (all(row.get(k) is True for k in required) and row.get('engineering_fit',row.get('mechanical_fit')) is True and start and start >= MIN_START
            and set(months).intersection({12, 16}) and row.get('evidence') and row.get('verified_on')):
        return 'Verified match'
    return 'Needs confirmation'

def validate(data):
    date.fromisoformat(data['checked_on'])
    seen = set()
    for row in data['jobs']:
        for field in ('employer', 'title', 'url', 'summary', 'evidence'):
            if not row.get(field):
                raise ValueError('Missing required field: ' + field)
        if urlsplit(row['url']).scheme not in ('http', 'https'):
            raise ValueError('Only public web URLs accepted')
        for field in ('ontario','mechanical_fit','engineering_fit','computer_engineering','student_role','official_verified','live_verified','eligibility_compatible','closed','duration_complete'):
            if row.get(field) is not None and type(row[field]) is not bool:
                raise ValueError('Expected boolean or null: ' + field)
        if any(type(m) is not int or m <= 0 for m in row.get('duration_months', [])):
            raise ValueError('Invalid month duration')
        k = key(row)
        if k in seen:
            raise ValueError('Duplicate job; merge evidence before reporting: ' + k)
        seen.add(k)
        classify(row)

def merge(data, previous):
    history = {key(r): dict(r) for r in previous}
    for r in history.values():
        r['checked_this_run'] = False
    changes = []
    for row in data['jobs']:
        k = key(row)
        old = history.get(k)
        current = dict(row)
        current['status'] = classify(row)
        current['first_found'] = old.get('first_found', data['checked_on']) if old else data['checked_on']
        current['last_checked'] = data['checked_on']
        current['checked_this_run'] = True
        fields = ('status','start_month','duration_months','deadline','summary','live_verified')
        current['change'] = 'Newly found' if not old else ('Changed' if any(old.get(f) != current.get(f) for f in fields) else 'Unchanged')
        if current['change'] != 'Unchanged':
            changes.append({'key': k, 'change': current['change'], 'status': current['status']})
        history[k] = current
    order = {'Verified match':0, 'Needs confirmation':1, 'Excluded':2, 'Closed':3}
    rows = sorted(history.values(), key=lambda r: (not r['checked_this_run'], order.get(r['status'],4), r.get('location_priority',1), r.get('distance_km') if r.get('distance_km') is not None else 9999, r['employer']))
    return rows, changes

def safe_csv(value):
    text = '' if value is None else str(value)
    return "'" + text if text.lstrip().startswith(('=', '+', '-', '@')) else text

def run(input_path, output):
    data = json.loads(Path(input_path).read_text(encoding='utf-8-sig'))
    validate(data)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    state_path = output / 'history.json'
    previous = json.loads(state_path.read_text(encoding='utf-8')) if state_path.exists() else []
    rows, changes = merge(data, previous)
    active = [r for r in rows if r['checked_this_run']]
    columns = ['status','employer','title','location','distance_km','distance_basis','start_label','duration_label','pay','deadline','summary','action','job_id','url','evidence','verified_on','first_found','last_checked','checked_this_run','change']
    with (output / 'jobs.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows({c:safe_csv(r.get(c)) for c in columns} for r in rows)
    counts = {s:sum(r['status']==s for r in active) for s in ['Verified match','Needs confirmation','Excluded','Closed']}
    blocks = []
    for status in counts:
        cards = []
        for r in active:
            if r['status'] != status: continue
            esc = lambda k: html.escape(str(r.get(k) or 'Not stated'))
            cards.append(f'<article><h3>{esc("employer")} â€” {esc("title")}</h3><p class="meta">{esc("location")} Â· {esc("duration_label")} Â· {esc("start_label")}</p><p>{esc("summary")}</p><p><b>Next step:</b> {esc("action")}</p><p><b>Pay:</b> {esc("pay")} &nbsp; <b>Deadline:</b> {esc("deadline")}</p><a href="{esc("url")}">View source posting</a><details><summary>Evidence and verification</summary><p>{esc("evidence")}</p><p>Verified: {esc("verified_on")}. Distance: {esc("distance_basis")}</p></details></article>')
        blocks.append(f'<h2>{html.escape(status)} ({counts[status]})</h2>'+''.join(cards))
    coverage = ''.join('<tr>'+''.join('<td>'+html.escape(str(s.get(k,'')))+'</td>' for k in ['source','method','result'])+'</tr>' for s in data.get('coverage',[]))
    report = '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Engineering co-op search</title><style>body{font:16px/1.55 Arial,sans-serif;max-width:1000px;margin:40px auto;padding:0 24px;color:#203047;background:#f6f8fb}h1,h2{color:#173657}h2{margin-top:38px}article{background:white;border:1px solid #dbe2eb;border-radius:8px;padding:18px 24px;margin:15px 0}h3{margin-top:0}.meta{color:#526477}a{color:#1558a5}table{border-collapse:collapse;background:white;width:100%}td,th{padding:10px;text-align:left;border-bottom:1px solid #ddd}details{margin-top:14px}p{margin:10px 0}</style>'
    report += f'<h1>Engineering co-op search</h1><p>Checked {data["checked_on"]}. May 2027 onwards. Only 12- or 16-month placements qualify.</p><p>{html.escape(data["scope_note"])}</p>'+''.join(blocks)
    report += '<h2>Search coverage</h2><p>A site search or landing-page check is not a complete inventory. Access gaps are shown below.</p><table><tr><th>Source</th><th>Method</th><th>Outcome</th></tr>'+coverage+'</table></html>'
    (output/'Search-results.html').write_text(report,encoding='utf-8')
    (output/'summary.json').write_text(json.dumps({'checked_on':data['checked_on'],'counts':counts,'changes':changes},indent=2),encoding='utf-8')
    # Replace history only after validation and report generation succeed.
    temp = output/'history.tmp'
    temp.write_text(json.dumps(rows,indent=2,ensure_ascii=False),encoding='utf-8')
    temp.replace(state_path)
    snapshot = output/('history-'+data['checked_on']+'.json')
    if not snapshot.exists(): snapshot.write_text(json.dumps(rows,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({'counts':counts,'records':len(rows),'output':str(output)},indent=2))
    return rows

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('findings')
    parser.add_argument('--output', default='reports')
    args = parser.parse_args()
    run(args.findings,args.output)
