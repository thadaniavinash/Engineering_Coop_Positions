import unittest
import tempfile
import json
import types
from pathlib import Path
from unittest.mock import patch, Mock
from datetime import date
import search
import report

class DiscoveryTests(unittest.TestCase):
    def test_unknown_kept(self):
        r=search.candidate(dict(title='Electrical engineering co-op',url='https://example.com/job',body='Ontario electrical or computer engineering students'), '2026-09-23')
        self.assertEqual(report.classify(r),'Needs confirmation')
    def test_primary_computer_excluded(self):
        r=search.candidate(dict(title='Computer Engineering Co-op',url='https://example.com/job'), '2026-09-23')
        self.assertEqual(report.classify(r),'Excluded')
    def test_weeks_not_months(self):
        r=search.candidate(dict(title='Mechanical intern',url='https://example.com/job',body='16 weeks'), '2026-09-23')
        self.assertEqual(r['duration_months'],[])
        self.assertEqual(report.classify(r),'Needs confirmation')
    def test_rotation(self):
        c=dict(seed_sources=[],additional_employers=[str(i) for i in range(60)],discovery_domains=[])
        a=search.queries(c,day=date(2026,9,23)); b=search.queries(c,day=date(2026,9,24))
        self.assertNotEqual(a,b)
        self.assertEqual(len(search.queries(c,full=True)),88)
    def test_page_hides_scripts(self):
        p=search.Page(); p.feed('<script>bad</script><a href="/jobs">Real role</a>')
        self.assertEqual(p.links,['/jobs']); self.assertNotIn('bad',p.text)
    def test_engineering_degree_scope(self):
        r=dict(ontario=True,engineering_fit=True,mechanical_fit=False,student_role=True)
        self.assertEqual(report.classify(r),'Needs confirmation')
    def test_query_job_ids_remain_distinct(self):
        a=dict(employer='Indeed',url='https://ca.indeed.com/viewjob?jk=abc&utm_source=x')
        b=dict(employer='Indeed',url='https://ca.indeed.com/viewjob?jk=def')
        self.assertNotEqual(report.key(a),report.key(b))
        self.assertEqual(report.key(a),report.key(dict(a,url='https://ca.indeed.com/viewjob?jk=abc')))
    def test_non_job_pages_only_in_raw_hits(self):
        for title,url in [('Mechanical engineering student resume','https://x.ca/resume'),('20 mechanical co-op jobs','https://x.ca/search')]:
            self.assertIsNone(search.candidate(dict(title=title,url=url),'2026-09-23'))
    def test_complete_pipeline_and_failed_discovery(self):
        with tempfile.TemporaryDirectory(dir='.') as tmp:
            root=Path(tmp); config=root/'config.json'
            config.write_text(json.dumps(dict(seed_sources=[],additional_employers=['Test'],discovery_domains=[])))
            for found,code in [([dict(title='Electrical engineering co-op',href='https://example.com/jobs/1',body='Ontario; May 2027')],0),([],2)]:
                client=Mock(); client.text.return_value=found
                module=types.SimpleNamespace(DDGS=Mock(return_value=client))
                with patch('search.bounded_search',return_value=found),patch('search.time.sleep'):
                    self.assertEqual(search.run_search(config,root/'results',max_queries=1),code)
                self.assertTrue((root/'results'/'Search-results.html').exists())
                self.assertEqual(json.loads((root/'results'/'run-health.json').read_text())['unique_hits'],len(found))

if __name__=='__main__': unittest.main()
