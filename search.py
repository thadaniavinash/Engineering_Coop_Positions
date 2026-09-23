"""Free, best-effort discovery. Every automated lead remains unverified.
Search indexes plus bounded direct employer-page discovery; no paid API.
"""
import argparse
import csv
import json
import re
import time
import subprocess
import sys
import tempfile
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen
import report

STUDENT = re.compile(r'\b(?:co[ -]?op|intern(?:ship)?s?|student|placement)\b', re.I)
ENGINEERING = re.compile(r'engineer|mechanical|electrical|mechatronic|manufactur|solidworks|robotic|automation|\bCAD\b|tooling|technician|quality|design|systems', re.I)

class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.text=[]; self.links=[]; self.hidden=0
    def handle_starttag(self, tag, attrs):
        if tag in ('script','style'): self.hidden += 1
        if tag == 'a':
            self.links.extend(v for k,v in attrs if k=='href')
    def handle_endtag(self, tag):
        if tag in ('script','style'): self.hidden=max(0,self.hidden-1)
    def handle_data(self, value):
        if not self.hidden: self.text.append(value)

def fetch(url):
    req=Request(url,headers={'User-Agent':'OntarioCoopResearch/1.0 (public job research)'})
    with urlopen(req, timeout=15) as response:
        if 'text/html' not in response.headers.get('Content-Type',''):
            raise ValueError('Not an HTML page')
        page=Page(); page.feed(response.read(2_000_000).decode('utf-8','replace'))
        return re.sub(r'\s+',' ',' '.join(page.text)).strip(), page.links

def canonical(url):
    u=urlsplit(url)
    return urlunsplit((u.scheme,u.netloc.lower(),u.path.rstrip('/'),u.query,''))

def bounded_search(query):
    # A process boundary enforces the timeout even when an engine ignores its socket timeout.
    with tempfile.TemporaryDirectory(dir='.') as folder:
        result=Path(folder)/'result.json'
        subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',query,str(result.resolve())],timeout=12,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        return json.loads(result.read_text(encoding='utf-8'))

def queries(config, full=False, day=None):
    day=day or date.today()
    disciplines=['mechanical','electrical','mechatronics','civil structural','chemical process',
                 'industrial manufacturing','materials','aerospace','environmental','biomedical',
                 'nuclear energy','quality reliability','automation robotics','design systems']
    result=[f'{d} engineering co-op Ontario 2027 12 16 months' for d in disciplines]
    result += [f'{d} intern Ontario "May 2027"' for d in disciplines]
    result += [f'site:{urlsplit(s["url"]).netloc} engineering student intern co-op 2027' for s in config['seed_sources']]
    employers=config['additional_employers']
    if not full:
        # Rotate through the entire employer queue; never restrict to the same first entries.
        offset=(day.toordinal()*15)%len(employers)
        employers=(employers+employers)[offset:offset+15]
    result += [f'"{e}" engineering co-op internship Ontario 2027' for e in employers]
    result += [f'site:{d} engineering co-op Ontario "2027" "months"' for d in config['discovery_domains']]
    return list(dict.fromkeys(result))

def candidate(hit, today):
    title=hit.get('title') or hit['url']
    snippet=hit.get('body','')
    combined=title+' '+snippet
    if not STUDENT.search(combined) or not ENGINEERING.search(combined): return None
    if re.search(r'resume|curriculum vitae|admission|college diploma|bachelor of|program availability|co-op.*program|engineering technology.*college',title,re.I): return None
    if re.search(r'/search(?:/|\?|$)|/q-[^/]+jobs',hit['url'],re.I) or re.search(r'\b\d+\s+.*jobs\b',title,re.I): return None
    computer=bool(re.search(r'computer engineering',title,re.I))
    # A discipline in a list of eligible degrees is not the role's primary discipline.
    return dict(employer=hit.get('employer') or urlsplit(hit['url']).netloc,
        title=title,url=hit['url'],location='Ontario searched; location unverified',
        summary=snippet[:1600] or 'Direct employer link; description needs review.',
        evidence='Unverified automated discovery. Query/source: '+hit.get('query','direct board'),
        action='Confirm employer, Ontario location, May 2027+ start, 12/16 months and degree eligibility.',
        start_label='Unverified',duration_label='Unverified',duration_months=[],
        duration_complete=False,engineering_fit=True,computer_engineering=computer,
        student_role=True,ontario=None,official_verified=False,live_verified=False,
        eligibility_compatible=None,verified_on=None,discovered_on=today,
        distance_basis='No distance cutoff; commute unverified')

def run_search(config_path, output, full=False, max_queries=None, seconds=840):
    config=json.loads(Path(config_path).read_text(encoding='utf-8-sig'))
    out=Path(output); out.mkdir(parents=True,exist_ok=True)
    today=date.today().isoformat(); started=time.monotonic()
    raw=[]; coverage=[]; successful=0
    planned=queries(config,full)
    if max_queries is not None: planned=planned[:max_queries]
    for query in planned:
        if time.monotonic()-started > seconds: break
        try:
            found=bounded_search(query)
            successful+=1
            for r in found:
                url=r.get('href') or r.get('url')
                if url and urlsplit(url).scheme in ('http','https'):
                    raw.append(dict(url=url,title=r.get('title',''),body=r.get('body',''),query=query))
            outcome=f'{len(found)} search hits; indexed results are unverified'
        except Exception as exc:
            outcome='ACCESS GAP: '+type(exc).__name__
        coverage.append(dict(source=query,method='Public metasearch',result=outcome,checked_on=today,url=''))
        (out/'raw-search-hits.json').write_text(json.dumps(raw,indent=2),encoding='utf-8')
        (out/'coverage-checkpoint.json').write_text(json.dumps(coverage,indent=2),encoding='utf-8')
        print(f'Search {len(coverage)}/{len(planned)}: {outcome}',flush=True)
        time.sleep(1)
    # Direct visits complement search indexes. JS-only and inaccessible boards remain coverage gaps.
    for seed in config['seed_sources']:
        if time.monotonic()-started > seconds: break
        try:
            text, links=fetch(seed['url']); count=0
            for link in dict.fromkeys(links):
                url=urljoin(seed['url'],link)
                if urlsplit(url).scheme not in ('http','https'): continue
                if not STUDENT.search(url) or not ENGINEERING.search(url): continue
                if count>=15: break
                raw.append(dict(url=url,title=urlsplit(url).path.replace('-',' '),body='Employer board link; page content unverified.',employer=seed['source'],query=seed['url']))
                count+=1
            outcome=f'Page retrieved; {count} candidate links. Static-page coverage only; not a full board inventory.'
        except Exception as exc: outcome='ACCESS GAP: '+type(exc).__name__
        coverage.append(dict(source=seed['source'],method='Direct employer page',result=outcome,checked_on=today,url=seed['url']))
    unique={}
    for hit in raw: unique.setdefault(canonical(hit['url']),hit)
    jobs=list({report.key(r):r for hit in unique.values() if (r:=candidate(hit,today))}.values())
    attempted=sum(c['method']=='Public metasearch' for c in coverage)
    gap_count=sum('ACCESS GAP' in c['result'] for c in coverage)
    data=dict(checked_on=today,scope_note=f'All Ontario; all engineering disciplines except computer engineering. Automated leads require review. Unknown term/location/eligibility is retained. {successful}/{attempted} queries completed; {gap_count} access gaps. Search coverage is bounded, not exhaustive.',jobs=jobs,coverage=coverage)
    (out/'automated-findings.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
    (out/'raw-search-hits.json').write_text(json.dumps(raw,indent=2),encoding='utf-8')
    with (out/'all-search-hits.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=['title','url','body','query','employer']); w.writeheader()
        w.writerows({k:report.safe_csv(r.get(k)) for k in w.fieldnames} for r in raw)
    # Research baseline remains separate and dated; automated retrieval cannot renew its verification.
    report.run(out/'automated-findings.json',out)
    metrics=dict(planned_queries=len(planned),attempted_queries=attempted,successful_queries=successful,access_gaps=gap_count,partial_coverage=bool(gap_count or attempted<len(planned)),unique_hits=len(unique),candidate_leads=len(jobs),elapsed_seconds=round(time.monotonic()-started))
    (out/'run-health.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8')
    print(json.dumps(metrics))
    return 0 if successful and unique else 2

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--worker':
        from ddgs import DDGS
        hits=DDGS(timeout=5).text(sys.argv[2],region='ca-en',max_results=20,backend='auto')
        Path(sys.argv[3]).write_text(json.dumps(hits),encoding='utf-8')
        raise SystemExit(0)
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',default='search-config.json'); p.add_argument('--output',default='daily-results')
    p.add_argument('--full',action='store_true'); p.add_argument('--max-queries',type=int)
    p.add_argument('--seconds',type=int,default=840)
    a=p.parse_args(); raise SystemExit(run_search(a.config,a.output,a.full,a.max_queries,a.seconds))
