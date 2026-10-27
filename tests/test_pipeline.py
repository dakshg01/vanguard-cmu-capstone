import csv
import io
import json
import sqlite3
import tempfile
import unittest
import zipfile
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import run

SERIES='S000053068'
ACC='0000836906-19-000001'
AMEND='0000836906-20-000002'

def fixture(path, acc=ACC, filing='15-DEC-2019', ret='2', bad=False, extra=False):
    h='123456789012345678901234567890'
    tables={
      'FUND_REPORTED_INFO':{'ACCESSION_NUMBER':acc,'SERIES_ID':SERIES,'SERIES_NAME':'Example',
        'TOTAL_ASSETS':'101','TOTAL_LIABILITIES':'1','NET_ASSETS':'100','DELAYED_DELIVERY':'3','CASH_NOT_RPTD_IN_C_OR_D':'2',
        **{k+str(m):v for m in (1,2,3) for k,v in [('SALES_FLOW_MON','10'),('REINVESTMENT_FLOW_MON','2'),('REDEMPTION_FLOW_MON','3')]},
        **{'CREDIT_SPREAD_'+t+'_'+b:'0.01' for t in ('3MON','1YR','5YR','10YR','30YR') for b in ('INVEST','NONINVEST')}},
      'SUBMISSION':{'ACCESSION_NUMBER':acc,'REPORT_DATE':'29-NOV-2019','REPORT_ENDING_PERIOD':'31-MAY-2020','FILING_DATE':filing,'SUB_TYPE':'NPORT-P/A' if acc==AMEND else 'NPORT-P','IS_LAST_FILING':'N'},
      'REGISTRANT':{'ACCESSION_NUMBER':acc,'CIK':'0000836906'},
      'FUND_REPORTED_HOLDING':{'ACCESSION_NUMBER':acc,'HOLDING_ID':h,'ISSUER_CUSIP':'001234567','ISSUER_NAME':'Example issuer','PERCENTAGE':'bad' if bad else '25','CURRENCY_VALUE':'25','DERIVATIVE_CAT':''},
      'MONTHLY_TOTAL_RETURN':{'ACCESSION_NUMBER':acc,'MONTHLY_TOTAL_RETURN_ID':'1','CLASS_ID':'C000000001','MONTHLY_TOTAL_RETURN1':'1','MONTHLY_TOTAL_RETURN2':ret,'MONTHLY_TOTAL_RETURN3':'3'},
      'DEBT_SECURITY':{'HOLDING_ID':h,'MATURITY_DATE':'30-NOV-2029','COUPON_TYPE':'Fixed','ANNUALIZED_RATE':'5','IS_DEFAULT':'N'},
      'IDENTIFIERS':{'HOLDING_ID':h,'IDENTIFIERS_ID':'1','IDENTIFIER_ISIN':'US0012345678','IDENTIFIER_TICKER':''},
      'INTEREST_RATE_RISK':{'ACCESSION_NUMBER':acc,'INTEREST_RATE_RISK_ID':'1','CURRENCY_CODE':'USD',**{'INTRST_RATE_CHANGE_'+t+'_DV01':'0.01' for t in ('3MON','1YR','5YR','10YR','30YR')}},
      'MONTHLY_RETURN_CAT_INSTRUMENT':{'ACCESSION_NUMBER':acc,'ASSET_CAT':'IR','INSTRUMENT_KIND':'SW','NET_REALIZED_GAIN_MON1':'5','NET_UNREALIZED_AP_MON1':'-2'}
    }
    if extra:tables['FUND_REPORTED_INFO']['NEW_FIELD']='new'
    numeric={'TOTAL_ASSETS','TOTAL_LIABILITIES','NET_ASSETS','DELAYED_DELIVERY','CASH_NOT_RPTD_IN_C_OR_D','PERCENTAGE','CURRENCY_VALUE','ANNUALIZED_RATE'}
    meta={'tables':[]}
    with zipfile.ZipFile(path,'w') as z:
        for table,row in tables.items():
            s=io.StringIO();w=csv.DictWriter(s,fieldnames=row,delimiter='\t');w.writeheader();w.writerow(row)
            if table=='IDENTIFIERS':
                w.writerow({**row,'IDENTIFIERS_ID':'2','IDENTIFIER_ISIN':'US0099999999'})
            # Unrelated series with same CIK must never pass a series filter.
            if table=='FUND_REPORTED_INFO':
                w.writerow({**row,'ACCESSION_NUMBER':'other','SERIES_ID':'S000000002'})
            z.writestr(table+'.tsv',s.getvalue())
            fields=[]
            for c in row:
                base='date (DD-MON-YYYY)' if c.endswith('_DATE') or c=='REPORT_ENDING_PERIOD' else 'NUMBER' if c in numeric or any(c.startswith(p) for p in ('SALES_FLOW','REINVESTMENT_FLOW','REDEMPTION_FLOW','CREDIT_SPREAD','INTRST_RATE_CHANGE','MONTHLY_TOTAL_RETURN1','MONTHLY_TOTAL_RETURN2','MONTHLY_TOTAL_RETURN3','NET_REALIZED','NET_UNREALIZED')) else 'string'
                fields.append({'name':c,'datatype':{'base':base}})
            meta['tables'].append({'url':table+'.tsv','tableSchema':{'columns':fields}})
        z.writestr('nport_metadata.json',json.dumps(meta))

class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)
        self.db=sqlite3.connect(self.path/'test.sqlite')
        run.setup(self.db,[{'series_id':SERIES,'cik':'0000836906','fund_name':'Example','group':'PRIMARY','role':'VANGUARD','style':'Core','manager':'Vanguard'}],'test')
        self.z=self.path/'2019q4.zip';fixture(self.z)
    def tearDown(self):
        self.db.close();self.tmp.cleanup()
    def ingest(self,z=None):run.ingest(self.db,z or self.z,{SERIES})
    def test_dates_month_order_units_and_no_class_fanout(self):
        self.ingest();run.rebuild(self.db)
        rows=self.db.execute('SELECT month_end,return_decimal FROM monthly_returns_latest ORDER BY month_end').fetchall()
        self.assertEqual(rows,[('2019-09-30',.01),('2019-10-31',.02),('2019-11-30',.03)])
        self.assertEqual(self.db.execute('SELECT net_external_flow_usd,net_flow_including_reinvestment_usd FROM monthly_flows_latest LIMIT 1').fetchone(),(7,9))
        self.assertEqual(self.db.execute('SELECT weight_fraction,ISSUER_CUSIP,HOLDING_ID FROM holdings_latest').fetchone(),(.25,'001234567','123456789012345678901234567890'))
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM holdings_enriched_latest').fetchone()[0],1)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM identifiers_latest').fetchone()[0],2)
        self.assertAlmostEqual(self.db.execute('SELECT usd_rate_sensitivity_years_signed FROM fund_quarter').fetchone()[0],5)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM filings').fetchone()[0],1)
    def test_resume_and_amendment_and_asof(self):
        self.ingest();self.ingest()
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM archives').fetchone()[0],1)
        z=self.path/'2020q1.zip';fixture(z,AMEND,'15-FEB-2020','8',extra=True);self.ingest(z);run.rebuild(self.db)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM filings').fetchone()[0],2)
        self.assertEqual(self.db.execute('SELECT accession_number FROM filings_latest').fetchone()[0],AMEND)
        self.assertEqual(self.db.execute('SELECT return_pct FROM monthly_returns_latest WHERE month_slot=2').fetchone()[0],8)
        self.assertEqual(self.db.execute('SELECT accession_number FROM filings WHERE available_date_assumed<=? ORDER BY filing_date DESC LIMIT 1',('2020-02-01',)).fetchone()[0],ACC)
        self.assertIn('NEW_FIELD',run.cols(self.db,'raw_fund_reported_info'))
        # Holding ID reused across ZIPs does not join the amendment to the original.
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM debt_security_latest').fetchone()[0],1)
    def test_bad_number_is_null_not_zero_and_raw_retained(self):
        fixture(self.z,bad=True);self.ingest();run.rebuild(self.db)
        self.assertIsNone(self.db.execute('SELECT weight_fraction FROM holdings_latest').fetchone()[0])
        self.assertEqual(self.db.execute('SELECT PERCENTAGE FROM raw_fund_reported_holding').fetchone()[0],'bad')
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM ingest_issues').fetchone()[0],1)
    def test_duplicate_archive_accessions_not_double_counted(self):
        self.ingest();z=self.path/'2020q1.zip';fixture(z,extra=True);self.ingest(z);run.rebuild(self.db)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM filings_all').fetchone()[0],2)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM holdings_latest').fetchone()[0],1)
    def test_changed_universe_rejected(self):
        with self.assertRaises(ValueError):run.setup(self.db,[{'series_id':SERIES}],'different')
    def test_missing_metadata_fails_before_mutation(self):
        z=self.path/'broken.zip'
        with zipfile.ZipFile(self.z) as source,zipfile.ZipFile(z,'w') as target:
            for n in source.namelist():
                if not n.endswith('.json'):target.writestr(n,source.read(n))
        with self.assertRaises(ValueError):self.ingest(z)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM archives').fetchone()[0],0)
    def test_unknown_relationship_rolls_back_archive(self):
        with zipfile.ZipFile(self.z,'a') as z:
            z.writestr('UNKNOWN.tsv','MYSTERY\n1\n')
        with self.assertRaises(ValueError):self.ingest()
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM archives').fetchone()[0],0)
        self.assertFalse(run.table_exists(self.db,'raw_fund_reported_info'))
    def test_incomplete_risk_total_not_silently_zero(self):
        self.ingest()
        self.db.execute('UPDATE t_interest_rate_risk SET INTRST_RATE_CHANGE_5YR_DV01=NULL')
        run.rebuild(self.db)
        self.assertIsNone(self.db.execute('SELECT usd_rate_sensitivity_years_signed FROM fund_quarter').fetchone()[0])

if __name__=='__main__':unittest.main()
