"""Small pandas helpers for Jupyter. Pipeline itself does not require pandas."""
import sqlite3
from pathlib import Path
import pandas as pd

DEFAULT_DB = Path(__file__).resolve().parent / 'output' / 'nport.sqlite'

def read(table, db_path=DEFAULT_DB):
    with sqlite3.connect(db_path) as db:
        if not db.execute('SELECT 1 FROM sqlite_master WHERE name=?',(table,)).fetchone():
            raise ValueError(f'Unknown table: {table}')
        return pd.read_sql_query('SELECT * FROM "'+table.replace('"','""')+'"', db)

def snapshots_asof(decision_date, db_path=DEFAULT_DB):
    """One most-recent public snapshot per series. Uses assumed availability unless overridden.

    First filter eligible versions, THEN rank report date and amendment date.
    The result includes age, so stale holdings never masquerade as current holdings.
    """
    date = pd.Timestamp(decision_date).strftime('%Y-%m-%d')
    with sqlite3.connect(db_path) as db:
        return pd.read_sql_query('''SELECT *, JULIANDAY(?) - JULIANDAY(report_date) AS snapshot_age_days
           FROM (SELECT f.*, ROW_NUMBER() OVER (PARTITION BY series_id
             ORDER BY report_date DESC, filing_date DESC, accession_number DESC) AS snapshot_rank
             FROM filings f WHERE available_date_assumed<=? AND report_date<=?)
           WHERE snapshot_rank=1''',db,params=(date,date,date))

def reference_class_panel(class_map, db_path=DEFAULT_DB):
    """Merge one explicitly chosen class per fund with monthly fund-level flows.

    class_map has series_id and class_id. For an actually classless return use
    __NO_CLASS__. This helper deliberately rejects overlaps and missing selections;
    no averaging, automatic class switching or forward filling is performed.
    Historical class changes require a separately audited, date-effective crosswalk.
    """
    mapping = class_map[['series_id','class_id']].copy()
    if mapping.isna().any().any() or (mapping.astype(str).apply(lambda s:s.str.strip()).eq('')).any().any():
        raise ValueError('Specify a class_id for each requested series; blank is not a selection')
    if mapping.series_id.duplicated().any():
        raise ValueError('Choose exactly one class per fund in this helper')
    returns = read('monthly_returns_latest',db_path)
    returns['class_id'] = returns.class_id.fillna('__NO_CLASS__')
    selected = returns.merge(mapping,on=['series_id','class_id'],how='inner',validate='many_to_one')
    missing=set(mapping.series_id)-set(selected.series_id)
    if missing:
        raise ValueError(f'No returns for selected class in these series: {sorted(missing)}')
    if selected.duplicated(['series_id','month_end']).any():
        raise ValueError('Overlapping return reports: resolve source versions before building a monthly panel')
    flows=read('monthly_flows_latest',db_path)
    if flows.duplicated(['series_id','month_end']).any():
        raise ValueError('Overlapping monthly flows: inspect source filings')
    fields=['series_id','month_end','sales_usd','redemptions_usd','reinvestment_usd','net_external_flow_usd','net_flow_including_reinvestment_usd']
    return selected.merge(flows[fields],on=['series_id','month_end'],how='left',validate='one_to_one')

def merge_class_fees(panel, fees):
    """Exact month merge only. Input fees must already reflect effective/public timing.
    No automatic annual fee forward-fill or percentage-unit guessing.
    """
    return panel.merge(fees,on=['series_id','class_id','month_end'],how='left',validate='many_to_one')
