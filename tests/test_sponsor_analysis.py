"""Research-rule checks for cases that can materially change allocation results."""
import unittest
import pandas as pd
from analyze_sponsor import classify, SECTORS


class ClassificationTests(unittest.TestCase):
    def test_overlapping_security_labels_obey_economic_precedence(self):
        # A swap issued by a corporation is not corporate cash-bond allocation;
        # an agency TBA remains mortgage allocation despite its forward nature.
        examples = [
            ('Swap bank', 'USD swap', 'DIR', 'CORP', 'US', 'SWP', 0.1),
            ('FNMA', 'FNCL 30 YEAR TBA', 'ABS-MBS', 'USGSE', 'US', None, 12.0),
            ('US Treasury', 'Inflation indexed bonds', 'DBT', 'UST', 'US', None, 3.0),
            ('Brazil', 'Government note', 'DBT', 'NUSS', 'BR', None, 2.0),
            ('Canada', 'Government note', 'DBT', 'NUSS', 'CA', None, 1.0),
            ('Unknown', 'Unknown security', None, None, None, None, None),
        ]
        h = pd.DataFrame(examples,columns=['ISSUER_NAME','ISSUER_TITLE','ASSET_CAT','ISSUER_TYPE','INVESTMENT_COUNTRY','DERIVATIVE_CAT','PERCENTAGE'])
        h['source_archive_id']='archive'; h['ACCESSION_NUMBER']='filing'
        h['series_id']='series'; h['report_month']='2026-03-31'
        h['HOLDING_ID']=[str(i) for i in range(len(h))]; h['CURRENCY_CODE']='USD'
        result=classify(h)
        self.assertEqual(result.sector.tolist(),[SECTORS[11],SECTORS[3],SECTORS[1],SECTORS[8],SECTORS[7],SECTORS[12]])
        self.assertEqual(result.tba_description_candidate.tolist(),[0,1,0,0,0,0])
        self.assertEqual(result.weight_missing.sum(),1)
        self.assertTrue(pd.isna(result.iloc[-1].reported_weight_pct))
        self.assertEqual(len(result),len(h))


if __name__=='__main__':
    unittest.main()
