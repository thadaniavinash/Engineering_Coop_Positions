import copy
import tempfile
import unittest
from pathlib import Path
import report

class MatchingTests(unittest.TestCase):
    def setUp(self):
        self.row = dict(employer='Example',title='Mechanical Co-op',job_id='A1',url='https://example.org/job/A1',summary='Test',evidence='Test evidence',start_month='2027-05',duration_months=[16],duration_complete=True,ontario=True,mechanical_fit=True,student_role=True,official_verified=True,live_verified=True,eligibility_compatible=True,verified_on='2026-09-23')
    def test_matching_boundaries(self):
        for updates, expected in [({},'Verified match'),({'duration_months':[4,8,12]},'Verified match'),({'start_month':'2027-04'},'Excluded'),({'start_month':'2027-09'},'Verified match'),({'start_month':None},'Needs confirmation'),({'duration_months':[4]},'Excluded'),({'duration_months':[],'duration_complete':False},'Needs confirmation'),({'official_verified':False},'Needs confirmation'),({'live_verified':False},'Needs confirmation'),({'eligibility_compatible':False},'Needs confirmation'),({'mechanical_fit':False},'Excluded'),({'ontario':False},'Excluded'),({'closed':True},'Closed')]:
            with self.subTest(updates=updates):
                self.assertEqual(report.classify(dict(self.row,**updates)),expected)
    def test_duplicate_rejected(self):
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            report.validate({'checked_on':'2026-09-23','jobs':[self.row,self.row]})
    def test_absence_does_not_close_job(self):
        rows,_=report.merge({'checked_on':'2026-09-23','jobs':[self.row]},[])
        newer,_=report.merge({'checked_on':'2026-09-24','jobs':[]},rows)
        self.assertFalse(newer[0]['checked_this_run'])
        self.assertEqual(newer[0]['status'],'Verified match')
    def test_repeat_and_change(self):
        data={'checked_on':'2026-09-23','jobs':[self.row]}
        rows,_=report.merge(data,[])
        again,changes=report.merge(data,rows)
        self.assertEqual(changes,[])
        self.assertEqual(again[0]['first_found'],'2026-09-23')
        changed=copy.deepcopy(data)
        changed['jobs'][0]['start_month']='2027-01'
        updated,changes=report.merge(changed,rows)
        self.assertEqual(updated[0]['status'],'Excluded')
        self.assertEqual(changes[0]['change'],'Changed')
    def test_formula_injection(self):
        self.assertEqual(report.safe_csv('=HYPERLINK("bad")'),'\'=HYPERLINK("bad")')
    def test_unsafe_url(self):
        with self.assertRaises(ValueError):
            report.validate({'checked_on':'2026-09-23','jobs':[dict(self.row,url='javascript:bad')]})
    def test_nearby_priority(self):
        far=dict(self.row,job_id='FAR',employer='A Far Company',location_priority=1)
        near=dict(self.row,job_id='NEAR',employer='Z Nearby Company',location_priority=0)
        rows,_=report.merge({'checked_on':'2026-09-23','jobs':[far,near]},[])
        self.assertEqual(rows[0]['job_id'],'NEAR')

if __name__=='__main__': unittest.main()
