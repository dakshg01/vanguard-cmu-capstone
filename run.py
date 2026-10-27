#!/usr/bin/env python3
"""SEC bulk N-PORT -> scoped SQLite research database. Python 3.10+, no dependencies."""
from __future__ import annotations
import argparse
import calendar
import csv
import hashlib
import io
import json
import math
import re
import sqlite3
import sys
import zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VERSION = '1.0.0'
csv.field_size_limit(100_000_000)

def qi(s):
    return '"' + s.replace('"', '""') + '"'

def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()

def iso(v):
    if not v or not str(v).strip():
        return None
    s = str(v).strip()
    # Locale-independent SEC DD-MON-YYYY, as well as ISO and US dates.
    m = re.fullmatch(r'(\d{1,2})-([A-Za-z]{3})-(\d{4})', s)
    if m:
        months = 'JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC'.split()
        return date(int(m[3]), months.index(m[2].upper()) + 1, int(m[1])).isoformat()
    for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%Y%m%d'):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            pass
    raise ValueError(f'Unrecognized date: {s!r}')

def month_end(report_date, offset):
    d = date.fromisoformat(report_date)
    y, m0 = divmod(d.year * 12 + d.month - 1 + offset, 12)
    return date(y, m0 + 1, calendar.monthrange(y, m0 + 1)[1]).isoformat()

def number(v):
    if v is None or not str(v).strip():
        return None
    x = float(v)
    if not math.isfinite(x):
        raise ValueError('Nonfinite number')
    return x

def table_exists(db, name):
    return db.execute('SELECT 1 FROM sqlite_master WHERE name=?', (name,)).fetchone() is not None

def cols(db, name):
    return [r[1] for r in db.execute(f'PRAGMA table_info({qi(name)})')]

def ensure_table(db, name, fields):
    db.execute(f'CREATE TABLE IF NOT EXISTS {qi(name)} (' + ','.join(f'{qi(k)} {v}' for k,v in fields.items()) + ')')
    old = cols(db, name)
    for k,v in fields.items():
        if k not in old:
            db.execute(f'ALTER TABLE {qi(name)} ADD COLUMN {qi(k)} {v}')

def insert_rows(db, name, fields, rows):
    if rows:
        db.executemany(f'INSERT INTO {qi(name)} (' + ','.join(map(qi, fields)) + ') VALUES (' + ','.join('?' for _ in fields) + ')', rows)

def load_universe(path):
    with open(path, encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    if not rows or not {'series_id', 'cik', 'fund_name', 'group'} <= rows[0].keys():
        raise ValueError('Universe needs series_id, cik, fund_name, group columns')
    seen = set()
    for r in rows:
        r['series_id'] = r['series_id'].strip().upper()
        if not re.fullmatch(r'S\d{9}', r['series_id']) or r['series_id'] in seen:
            raise ValueError(f'Invalid/duplicate SERIES_ID: {r["series_id"]}')
        seen.add(r['series_id'])
        if not r['cik'].strip().isdigit():
            raise ValueError(f'Invalid CIK for {r["series_id"]}')
        r['cik'] = r['cik'].strip().zfill(10)
    return rows

def setup(db, universe, signature):
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('PRAGMA synchronous=NORMAL')
    db.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
    prev = db.execute("SELECT value FROM settings WHERE key='universe_sha256'").fetchone()
    if prev and prev[0] != signature:
        raise ValueError('Universe changed. Use a NEW --output directory to avoid incomplete historical extraction.')
    db.execute("INSERT OR REPLACE INTO settings VALUES ('universe_sha256',?)", (signature,))
    db.execute("INSERT OR REPLACE INTO settings VALUES ('pipeline_version',?)", (VERSION,))
    ensure_table(db, 'universe', {k:'TEXT' for k in universe[0]})
    db.execute('DELETE FROM universe')
    insert_rows(db, 'universe', list(universe[0]), [list(r.values()) for r in universe])
    db.execute('CREATE UNIQUE INDEX IF NOT EXISTS universe_series ON universe(series_id)')
    db.execute('CREATE TABLE IF NOT EXISTS archives (archive_id TEXT PRIMARY KEY, filename TEXT, bytes INTEGER, loaded_at TEXT)')
    db.execute('CREATE TABLE IF NOT EXISTS inventory (archive_id TEXT, table_name TEXT, source_rows INTEGER, retained_rows INTEGER, columns_json TEXT)')
    db.execute('CREATE TABLE IF NOT EXISTS schema_dictionary (archive_id TEXT, table_name TEXT, column_name TEXT, source_type TEXT, typed_type TEXT, description TEXT)')
    db.execute('CREATE TABLE IF NOT EXISTS ingest_issues (archive_id TEXT, table_name TEXT, source_row INTEGER, column_name TEXT, raw_value TEXT, reason TEXT)')
    db.commit()

def read_tsv(z, name):
    with io.TextIOWrapper(z.open(name), encoding='utf-8-sig', newline='') as f:
        r = csv.reader(f, delimiter='\t')
        header = [x.strip().upper() for x in next(r)]
        if len(header) != len(set(header)):
            raise ValueError(f'Duplicate columns: {name}')
        yield header
        for i, row in enumerate(r, 2):
            if not row:
                continue
            if len(row) != len(header):
                raise ValueError(f'{name}, line {i}: {len(row)} fields, expected {len(header)}')
            yield i, row

def ingest(db, path, wanted):
    aid = digest(path)
    if db.execute('SELECT 1 FROM archives WHERE archive_id=?', (aid,)).fetchone():
        print(f'SKIP already loaded: {path.name}', flush=True)
        return
    if db.execute('SELECT 1 FROM archives WHERE filename=?', (path.name,)).fetchone():
        raise ValueError(f'{path.name} has changed bytes. Use a new output directory; do not mix versions.')
    print(f'LOAD {path.name}', flush=True)
    with zipfile.ZipFile(path) as z:
        names = {}
        for n in z.namelist():
            if n.lower().endswith('.tsv') and not n.startswith('__MACOSX/'):
                stem = Path(n).stem.upper()
                if stem in names:
                    raise ValueError(f'Duplicate table {stem} in {path}')
                names[stem] = n
        required = {'SUBMISSION', 'REGISTRANT', 'FUND_REPORTED_INFO', 'FUND_REPORTED_HOLDING'}
        if not required <= names.keys():
            raise ValueError(f'Not a supported SEC bulk ZIP: missing {required - names.keys()}')
        metadata = {}
        for n in z.namelist():
            if Path(n).name.lower() == 'nport_metadata.json':
                doc = json.loads(z.read(n))
                for t in doc.get('tables', []):
                    metadata[Path(t['url']).stem.upper()] = {c['name'].upper():c for c in t.get('tableSchema', {}).get('columns', [])}
        if not metadata:
            raise ValueError('Missing nport_metadata.json: cannot safely infer numeric/date fields.')
        acc = set()
        it = read_tsv(z, names['FUND_REPORTED_INFO']); h = next(it)
        if not {'SERIES_ID','ACCESSION_NUMBER'} <= set(h):
            raise ValueError('FUND_REPORTED_INFO missing series/accession keys')
        si, ai = h.index('SERIES_ID'), h.index('ACCESSION_NUMBER')
        for _, row in it:
            if row[si].strip().upper() in wanted:
                if row[ai] in acc:
                    raise ValueError(f'Duplicate fund row for accession {row[ai]}')
                acc.add(row[ai])
        holdings = {}
        order = ['FUND_REPORTED_INFO','SUBMISSION','REGISTRANT','FUND_REPORTED_HOLDING']
        order += sorted(set(names) - set(order))
        # Each archive is a transaction: interruptions never leave a completed partial ZIP.
        with db:
            for table in order:
                it = read_tsv(z, names[table]); header = next(it)
                is_holding = table == 'FUND_REPORTED_HOLDING'
                if 'ACCESSION_NUMBER' in header:
                    key = header.index('ACCESSION_NUMBER'); kind = 'accession'
                elif 'HOLDING_ID' in header:
                    key = header.index('HOLDING_ID'); kind = 'holding'
                else:
                    raise ValueError(f'Unknown relational key in {table}; extraction stopped rather than silently omitting it.')
                types = {}
                for c in header:
                    spec = metadata.get(table, {}).get(c, {})
                    dtype = spec.get('datatype', {})
                    base = dtype.get('base', '') if isinstance(dtype, dict) else dtype
                    # Surrogate IDs can exceed 64 bits and are never floating-point numbers.
                    typ = 'TEXT' if c.endswith('_ID') or c in ('CIK','ACCESSION_NUMBER') else ('REAL' if str(base).upper() in ('NUMBER','DECIMAL','DOUBLE','INTEGER') else 'TEXT')
                    types[c] = (typ, str(base).lower().startswith('date'))
                    db.execute('INSERT INTO schema_dictionary VALUES (?,?,?,?,?,?)', (aid,table,c,str(base),typ,spec.get('dc:description','')))
                prefix = {'source_archive_id':'TEXT', 'source_row':'INTEGER'}
                ensure_table(db, 'raw_'+table.lower(), {**prefix, **{c:'TEXT' for c in header}})
                ensure_table(db, 't_'+table.lower(), {**prefix, **{c:types[c][0] for c in header}})
                fields = list(prefix) + header
                raw_batch, typed_batch = [], []
                count = kept = 0
                for line, row in it:
                    count += 1
                    if kind == 'accession' and row[key] not in acc:
                        continue
                    if kind == 'holding' and row[key] not in holdings:
                        continue
                    if is_holding:
                        hid = row[header.index('HOLDING_ID')]
                        if not hid or hid in holdings:
                            raise ValueError(f'Missing/duplicate HOLDING_ID within ZIP: {hid!r}')
                        holdings[hid] = row[key]
                    raw = [v if v != '' else None for v in row]
                    typed = []
                    for c,v in zip(header, raw):
                        try:
                            val = iso(v) if types[c][1] else number(v) if types[c][0] == 'REAL' else v
                        except (ValueError, OverflowError) as e:
                            db.execute('INSERT INTO ingest_issues VALUES (?,?,?,?,?,?)', (aid,table,line,c,v,str(e)))
                            val = None
                        typed.append(val)
                    raw_batch.append([aid,line] + raw)
                    typed_batch.append([aid,line] + typed)
                    kept += 1
                    if len(raw_batch) >= 5000:
                        insert_rows(db,'raw_'+table.lower(),fields,raw_batch)
                        insert_rows(db,'t_'+table.lower(),fields,typed_batch)
                        raw_batch.clear(); typed_batch.clear()
                insert_rows(db,'raw_'+table.lower(),fields,raw_batch)
                insert_rows(db,'t_'+table.lower(),fields,typed_batch)
                for pre in ('raw_', 't_'):
                    name = pre + table.lower()
                    db.execute(f'CREATE INDEX IF NOT EXISTS {qi(name+"_key")} ON {qi(name)} (source_archive_id, {qi(header[key])})')
                db.execute('INSERT INTO inventory VALUES (?,?,?,?,?)', (aid,table,count,kept,json.dumps(header)))
                print(f'  {table}: {kept:,} / {count:,}', flush=True)
            db.execute('INSERT INTO archives VALUES (?,?,?,?)', (aid,path.name,path.stat().st_size,datetime.now(timezone.utc).isoformat()))

def dictionaries(db, sql, params=()):
    cur = db.execute(sql, params)
    names = [d[0] for d in cur.description]
    for row in cur:
        yield dict(zip(names, row))

def rebuild(db, lag_days=60, overrides=None):
    if not table_exists(db, 't_fund_reported_info'):
        raise ValueError('No archives loaded')
    overrides = overrides or {}
    for name in ['filings_all','monthly_returns_all','monthly_flows_all','risk_all','derivative_pnl_all']:
        db.execute(f'DROP TABLE IF EXISTS {name}')
    db.execute('''CREATE TABLE filings_all (
      source_archive_id TEXT, accession_number TEXT, series_id TEXT, cik TEXT,
      series_name TEXT, report_date TEXT, report_month TEXT, fiscal_year_end TEXT,
      filing_date TEXT, submission_type TEXT, is_last_filing TEXT,
      available_date_assumed TEXT, availability_basis TEXT,
      total_assets REAL, total_liabilities REAL, net_assets REAL,
      PRIMARY KEY(source_archive_id, accession_number))''')
    fcols = cols(db, 'filings_all')
    sql = '''SELECT f.*, s.REPORT_DATE AS _report, s.FILING_DATE AS _file,
      s.REPORT_ENDING_PERIOD AS _fye, s.SUB_TYPE AS _type, s.IS_LAST_FILING AS _last,
      r.CIK AS _cik FROM t_fund_reported_info f
      JOIN t_submission s ON f.source_archive_id=s.source_archive_id AND f.ACCESSION_NUMBER=s.ACCESSION_NUMBER
      LEFT JOIN t_registrant r ON f.source_archive_id=r.source_archive_id AND f.ACCESSION_NUMBER=r.ACCESSION_NUMBER'''
    for r in dictionaries(db, sql):
        rd, fd = iso(r['_report']), iso(r['_file'])
        if not rd or not fd:
            raise ValueError(f'Missing filing/report date for {r["ACCESSION_NUMBER"]}; check ingest_issues')
        available = max(date.fromisoformat(fd), date.fromisoformat(rd)+timedelta(days=lag_days)) + timedelta(days=1)
        basis = f'max(filing_date, report_date+{lag_days}d)+1d; unverified proxy'
        av = available.isoformat()
        if r['ACCESSION_NUMBER'] in overrides:
            av = overrides[r['ACCESSION_NUMBER']]
            basis = 'user-supplied verified public date + 1 calendar day'
            av = (date.fromisoformat(av)+timedelta(days=1)).isoformat()
            if av <= fd or av <= rd:
                raise ValueError('Verified publication date cannot precede filing/report date')
        vals = [r['source_archive_id'],r['ACCESSION_NUMBER'],r['SERIES_ID'].strip().upper(),
                str(r['_cik']).zfill(10) if r['_cik'] else None,r.get('SERIES_NAME'),rd,month_end(rd,0),
                iso(r['_fye']),fd,r['_type'],r['_last'],av,basis,
                number(r.get('TOTAL_ASSETS')),number(r.get('TOTAL_LIABILITIES')),number(r.get('NET_ASSETS'))]
        insert_rows(db,'filings_all',fcols,[vals])
    prefix = 'source_archive_id TEXT, accession_number TEXT, series_id TEXT, report_date TEXT, month_end TEXT'
    db.execute(f'CREATE TABLE monthly_returns_all ({prefix}, return_row_id TEXT, class_id TEXT, month_slot INTEGER, return_pct REAL, return_decimal REAL)')
    db.execute(f'CREATE TABLE monthly_flows_all ({prefix}, month_slot INTEGER, sales_usd REAL, reinvestment_usd REAL, redemptions_usd REAL, net_external_flow_usd REAL, net_flow_including_reinvestment_usd REAL, nonderivative_realized_pnl_usd REAL, nonderivative_unrealized_change_usd REAL)')
    db.execute('CREATE TABLE risk_all (source_archive_id TEXT, accession_number TEXT, series_id TEXT, report_date TEXT, risk_row_id TEXT, risk_type TEXT, currency TEXT, credit_bucket TEXT, tenor TEXT, shock_bp INTEGER, value_change_usd REAL, source_column TEXT)')
    db.execute(f'CREATE TABLE derivative_pnl_all ({prefix}, asset_category TEXT, instrument_kind TEXT, month_slot INTEGER, realized_pnl_usd REAL, unrealized_change_usd REAL)')
    fs = {(r['source_archive_id'],r['accession_number']):r for r in dictionaries(db,'SELECT * FROM filings_all')}
    def scope(r):
        return fs[(r['source_archive_id'],r['ACCESSION_NUMBER'])]
    def pre(f,slot):
        return [f['source_archive_id'],f['accession_number'],f['series_id'],f['report_date'],month_end(f['report_date'],slot-3)]
    if table_exists(db,'t_monthly_total_return'):
        for r in dictionaries(db,'SELECT * FROM t_monthly_total_return'):
            f = scope(r)
            for slot in (1,2,3):
                v = number(r.get('MONTHLY_TOTAL_RETURN'+str(slot)))
                insert_rows(db,'monthly_returns_all',cols(db,'monthly_returns_all'),[pre(f,slot)+[r.get('MONTHLY_TOTAL_RETURN_ID'),r.get('CLASS_ID'),slot,v,v/100 if v is not None else None]])
    for r in dictionaries(db,'SELECT * FROM t_fund_reported_info'):
        f = scope(r)
        for slot in (1,2,3):
            s,i,d = [number(r.get(k+str(slot))) for k in ('SALES_FLOW_MON','REINVESTMENT_FLOW_MON','REDEMPTION_FLOW_MON')]
            ext = s-d if s is not None and d is not None else None
            total = ext+i if ext is not None and i is not None else None
            vals = pre(f,slot)+[slot,s,i,d,ext,total,number(r.get('NET_REALIZE_GAIN_NONDERIV_MON'+str(slot))),number(r.get('NET_UNREALIZE_AP_NONDERIV_MON'+str(slot)))]
            insert_rows(db,'monthly_flows_all',cols(db,'monthly_flows_all'),[vals])
        for c,v in r.items():
            m = re.fullmatch(r'CREDIT_SPREAD_(3MON|1YR|5YR|10YR|30YR)_(INVEST|NONINVEST)',c)
            if m:
                insert_rows(db,'risk_all',cols(db,'risk_all'),[[f['source_archive_id'],f['accession_number'],f['series_id'],f['report_date'],'fund','credit_spread','USD',m[2],m[1],1,number(v),c]])
    if table_exists(db,'t_interest_rate_risk'):
        for r in dictionaries(db,'SELECT * FROM t_interest_rate_risk'):
            f = scope(r)
            for c,v in r.items():
                m = re.fullmatch(r'INTRST_RATE_CHANGE_(3MON|1YR|5YR|10YR|30YR)_DV(01|100)',c)
                if m:
                    insert_rows(db,'risk_all',cols(db,'risk_all'),[[f['source_archive_id'],f['accession_number'],f['series_id'],f['report_date'],r.get('INTEREST_RATE_RISK_ID'),'interest_rate',r.get('CURRENCY_CODE'),None,m[1],int(m[2]),number(v),c]])
    if table_exists(db,'t_monthly_return_cat_instrument'):
        for r in dictionaries(db,'SELECT * FROM t_monthly_return_cat_instrument'):
            f = scope(r)
            for slot in (1,2,3):
                insert_rows(db,'derivative_pnl_all',cols(db,'derivative_pnl_all'),[pre(f,slot)+[r.get('ASSET_CAT'),r.get('INSTRUMENT_KIND'),slot,number(r.get('NET_REALIZED_GAIN_MON'+str(slot))),number(r.get('NET_UNREALIZED_AP_MON'+str(slot)))]])
    for name in ['monthly_returns_all','monthly_flows_all','risk_all','derivative_pnl_all']:
        db.execute(f'CREATE INDEX {name}_filing ON {name}(source_archive_id, accession_number)')
    create_views(db)
    db.commit()

def view(db,name,sql):
    db.execute(f'DROP VIEW IF EXISTS {qi(name)}')
    db.execute(f'CREATE VIEW {qi(name)} AS {sql}')

def create_views(db):
    # Same accession in two ZIPs is one filing, but raw archive copies remain.
    view(db,'filings','''SELECT * FROM (SELECT f.*, ROW_NUMBER() OVER (
       PARTITION BY accession_number ORDER BY a.filename DESC, f.source_archive_id) AS archive_copy_rank
       FROM filings_all f JOIN archives a ON a.archive_id=f.source_archive_id) WHERE archive_copy_rank=1''')
    view(db,'filings_latest','''SELECT * FROM (SELECT f.*, ROW_NUMBER() OVER (
       PARTITION BY series_id, report_date ORDER BY filing_date DESC, accession_number DESC) AS amendment_rank
       FROM filings f) WHERE amendment_rank=1''')
    for source in ['monthly_returns','monthly_flows','risk','derivative_pnl']:
        view(db,source, f'''SELECT x.*, f.filing_date, f.available_date_assumed, f.availability_basis
           FROM {source}_all x JOIN filings f USING(source_archive_id,accession_number)''')
        view(db,source+'_latest', f'''SELECT x.*, f.filing_date, f.available_date_assumed, f.availability_basis
           FROM {source}_all x JOIN filings_latest f USING(source_archive_id,accession_number)''')
    view(db,'fund_snapshots','''SELECT f.*, u.fund_name, u."group" AS universe_group, u.role, u.style, u.manager
         FROM filings_latest f JOIN universe u USING(series_id)''')
    view(db,'risk_normalized_latest','''SELECT r.*, f.filing_date, f.available_date_assumed, f.availability_basis, f.net_assets,
        CASE WHEN r.shock_bp=1 AND f.net_assets>0 THEN r.value_change_usd*10000.0/f.net_assets END AS reported_sensitivity_years
        FROM risk_all r JOIN filings_latest f USING(source_archive_id,accession_number)''')
    view(db,'risk_totals_latest','''SELECT source_archive_id,accession_number,series_id,report_date,
        risk_type,currency,credit_bucket,shock_bp,COUNT(*) AS tenor_rows,
        COUNT(DISTINCT tenor) AS distinct_tenors,COUNT(value_change_usd) AS nonmissing_tenors,
        CASE WHEN COUNT(*)=5 AND COUNT(DISTINCT tenor)=5 AND COUNT(value_change_usd)=5 THEN SUM(value_change_usd) END AS total_value_change_usd,
        CASE WHEN COUNT(*)=5 AND COUNT(DISTINCT tenor)=5 AND COUNT(reported_sensitivity_years)=5 THEN SUM(reported_sensitivity_years) END AS total_reported_sensitivity_years
        FROM risk_normalized_latest GROUP BY 1,2,3,4,5,6,7,8''')
    # Separate named factors, without mixing non-USD rate shocks with USD rate shocks.
    view(db,'fund_quarter','''SELECT f.*, r.DELAYED_DELIVERY AS delayed_delivery_payables_usd,
        r.CASH_NOT_RPTD_IN_C_OR_D AS cash_not_in_holdings_usd,
        JULIANDAY(f.filing_date)-JULIANDAY(f.report_date) AS filing_lag_days,
        ir.total_reported_sensitivity_years AS usd_rate_sensitivity_years_signed,
        ig.total_reported_sensitivity_years AS ig_spread_sensitivity_years_signed,
        hy.total_reported_sensitivity_years AS hy_spread_sensitivity_years_signed
        FROM fund_snapshots f JOIN t_fund_reported_info r
          ON f.source_archive_id=r.source_archive_id AND f.accession_number=r.ACCESSION_NUMBER
        LEFT JOIN risk_totals_latest ir ON f.source_archive_id=ir.source_archive_id AND f.accession_number=ir.accession_number
          AND ir.risk_type='interest_rate' AND ir.currency='USD' AND ir.shock_bp=1
        LEFT JOIN risk_totals_latest ig ON f.source_archive_id=ig.source_archive_id AND f.accession_number=ig.accession_number
          AND ig.risk_type='credit_spread' AND ig.credit_bucket='INVEST' AND ig.shock_bp=1
        LEFT JOIN risk_totals_latest hy ON f.source_archive_id=hy.source_archive_id AND f.accession_number=hy.accession_number
          AND hy.risk_type='credit_spread' AND hy.credit_bucket='NONINVEST' AND hy.shock_bp=1''')
    view(db,'holdings_all','''SELECT f.series_id, f.report_date, f.report_month, f.filing_date,
         f.available_date_assumed, f.availability_basis, h.*,
         h.PERCENTAGE / 100.0 AS weight_fraction
         FROM t_fund_reported_holding h JOIN filings f
         ON h.source_archive_id=f.source_archive_id AND h.ACCESSION_NUMBER=f.accession_number''')
    view(db,'holdings_latest','''SELECT h.* FROM holdings_all h JOIN filings_latest f
         ON h.source_archive_id=f.source_archive_id AND h.ACCESSION_NUMBER=f.accession_number''')
    # Child tables are kept long. Never multiply holdings by joining several 1:many tables.
    for (table,) in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 't_%'").fetchall():
        c = cols(db,table)
        if 'HOLDING_ID' in c and 'ACCESSION_NUMBER' not in c:
            view(db, table[2:]+'_latest',f'''SELECT h.series_id, h.report_date, h.ACCESSION_NUMBER, c.*
              FROM {qi(table)} c JOIN holdings_latest h
              ON c.source_archive_id=h.source_archive_id AND c.HOLDING_ID=h.HOLDING_ID''')
        elif 'ACCESSION_NUMBER' in c and table not in ('t_fund_reported_holding',):
            view(db,table[2:]+'_latest_raw',f'''SELECT f.series_id AS fund_series_id, f.report_date AS holdings_report_date, t.*
                FROM {qi(table)} t JOIN filings_latest f
                ON t.source_archive_id=f.source_archive_id AND t.ACCESSION_NUMBER=f.accession_number''')
    # For convenient bond analysis, enrich only unambiguous one-to-one debt records.
    if table_exists(db,'t_debt_security'):
        view(db,'debt_unique','''SELECT * FROM t_debt_security GROUP BY source_archive_id,HOLDING_ID HAVING COUNT(*)=1''')
        view(db,'holdings_enriched_latest','''SELECT h.*,
            CASE WHEN h.DERIVATIVE_CAT IS NOT NULL AND TRIM(h.DERIVATIVE_CAT) NOT IN ('','N/A','NA') THEN 1 ELSE 0 END AS is_reported_derivative,
            d.MATURITY_DATE, d.COUPON_TYPE, d.ANNUALIZED_RATE AS coupon_pct,
            d.ANNUALIZED_RATE/100.0 AS coupon_decimal, d.IS_DEFAULT,
            CASE WHEN d.MATURITY_DATE IS NOT NULL THEN (JULIANDAY(d.MATURITY_DATE)-JULIANDAY(h.report_date))/365.25 END AS years_to_maturity
            FROM holdings_latest h LEFT JOIN debt_unique d
            ON h.source_archive_id=d.source_archive_id AND h.HOLDING_ID=d.HOLDING_ID''')
    view(db,'coverage','''SELECT u.*, COUNT(f.accession_number) AS report_count,
       MIN(f.report_date) AS first_report_date, MAX(f.report_date) AS last_report_date,
       MIN(f.filing_date) AS first_filing_date, MAX(f.filing_date) AS last_filing_date,
       CASE WHEN COUNT(f.accession_number)=0 THEN 'NO_MATCH_IN_LOADED_ARCHIVES' ELSE 'OBSERVED' END AS coverage_status
       FROM universe u LEFT JOIN filings_latest f USING(series_id) GROUP BY u.series_id''')

def export(db, table, target):
    if not table_exists(db,table):
        raise ValueError(f'Unknown table/view: {table}')
    target.parent.mkdir(parents=True,exist_ok=True)
    cur = db.execute(f'SELECT * FROM {qi(table)}')
    with open(target,'w',encoding='utf-8-sig',newline='') as f:
        w = csv.writer(f);w.writerow([d[0] for d in cur.description]);w.writerows(cur)

def quality(db,output):
    checks = {}
    checks['numeric_or_date_parse_issues'] = db.execute('SELECT COUNT(*) FROM ingest_issues').fetchone()[0]
    checks['no_match_funds'] = db.execute("SELECT COUNT(*) FROM coverage WHERE report_count=0").fetchone()[0]
    checks['cik_mismatches'] = db.execute('SELECT COUNT(*) FROM filings f JOIN universe u USING(series_id) WHERE f.cik IS NULL OR f.cik<>u.cik').fetchone()[0]
    checks['accessions_in_multiple_archives'] = db.execute('SELECT COUNT(*) FROM (SELECT accession_number FROM filings_all GROUP BY accession_number HAVING COUNT(*)>1)').fetchone()[0]
    checks['amended_or_repeated_report_dates'] = db.execute('SELECT COUNT(*) FROM (SELECT series_id,report_date FROM filings GROUP BY series_id,report_date HAVING COUNT(*)>1)').fetchone()[0]
    checks['duplicate_class_month_latest'] = db.execute('SELECT COUNT(*) FROM (SELECT series_id,COALESCE(class_id,\'__NO_CLASS__\'),month_end FROM monthly_returns_latest GROUP BY 1,2,3 HAVING COUNT(*)>1)').fetchone()[0]
    checks['duplicate_flow_month_latest'] = db.execute('SELECT COUNT(*) FROM (SELECT series_id,month_end FROM monthly_flows_latest GROUP BY 1,2 HAVING COUNT(*)>1)').fetchone()[0]
    checks['balance_sheet_discrepancies'] = db.execute('SELECT COUNT(*) FROM filings_latest WHERE ABS(total_assets-total_liabilities-net_assets)>MAX(1,ABS(total_assets)*0.000001)').fetchone()[0]
    checks['snapshots_without_holdings'] = db.execute('SELECT COUNT(*) FROM filings_latest f WHERE NOT EXISTS (SELECT 1 FROM t_fund_reported_holding h WHERE h.source_archive_id=f.source_archive_id AND h.ACCESSION_NUMBER=f.accession_number)').fetchone()[0]
    expected = {'INTEREST_RATE_RISK','MONTHLY_TOTAL_RETURN','IDENTIFIERS','DEBT_SECURITY','MONTHLY_RETURN_CAT_INSTRUMENT'}
    missing = []
    for aid,filename in db.execute('SELECT archive_id,filename FROM archives'):
        present = {r[0] for r in db.execute('SELECT table_name FROM inventory WHERE archive_id=?',(aid,))}
        missing.extend({'archive':filename,'table':t} for t in sorted(expected-present))
    checks['missing_expected_tables'] = len(missing)
    checks['ambiguous_debt_rows'] = db.execute('SELECT COUNT(*) FROM (SELECT source_archive_id,HOLDING_ID FROM t_debt_security GROUP BY 1,2 HAVING COUNT(*)>1)').fetchone()[0] if table_exists(db,'t_debt_security') else 0
    checks['usd_sensitivity_magnitude_above_10_years'] = db.execute('SELECT COUNT(*) FROM fund_quarter WHERE ABS(usd_rate_sensitivity_years_signed)>10').fetchone()[0]
    checks['unknown_metadata_types'] = db.execute("SELECT COUNT(*) FROM schema_dictionary WHERE source_type=''").fetchone()[0]
    view(db,'risk_review_flags','''SELECT *, CASE WHEN usd_rate_sensitivity_years_signed IS NULL THEN 'MISSING_OR_INCOMPLETE_USD_RISK'
         WHEN ABS(usd_rate_sensitivity_years_signed)>10 THEN 'REVIEW_USD_SENSITIVITY_MAGNITUDE' ELSE 'WITHIN_MAGNITUDE_BOUNDS_SIGN_UNVERIFIED' END AS risk_review
         FROM fund_quarter''')
    view(db,'holdings_checks','''SELECT h.source_archive_id,h.ACCESSION_NUMBER,h.series_id,h.report_date,COUNT(*) AS holding_count,
       SUM(h.PERCENTAGE) AS reported_weight_sum_pct,
       SUM(CASE WHEN h.ISSUER_CUSIP IS NULL THEN 1 ELSE 0 END) AS missing_cusip_count,
       SUM(CASE WHEN h.PERCENTAGE IS NULL THEN 1 ELSE 0 END) AS missing_weight_count
       FROM holdings_latest h GROUP BY 1,2,3,4''')
    view(db,'coverage_gaps','''SELECT * FROM (SELECT series_id, report_date, LAG(report_date) OVER
       (PARTITION BY series_id ORDER BY report_date) AS previous_report_date,
       JULIANDAY(report_date)-JULIANDAY(LAG(report_date) OVER (PARTITION BY series_id ORDER BY report_date)) AS gap_days
       FROM filings_latest) WHERE gap_days>110''')
    for name in ['coverage','coverage_gaps','inventory','schema_dictionary','ingest_issues','holdings_checks','fund_quarter','monthly_returns_latest','monthly_flows_latest','risk_normalized_latest','risk_totals_latest','risk_review_flags','derivative_pnl_latest']:
        export(db,name,output/'csv'/(name+'.csv'))
    status = 'REVIEW_REQUIRED' if any(checks.values()) else 'CHECKS_PASSED'
    result = {'status':status,'checks':checks,'missing_expected_tables':missing,'notes':['A coverage gap is not proof of missing SEC data; check fund inception, fiscal calendar, mergers and ZIP coverage.',
      'Latest views are retrospective. For prediction use filings available by each decision date; default availability is an unverified lag proxy.',
      'Weights are diagnostic, not forced to 100%; cash, liabilities, derivatives and unreported positions can prevent reconciliation.',
      'Normalized risk fields retain the filed sign. Validate sign conventions before interpreting economic duration or comparing active signed risk across filers.',
      'Review inventory for missing optional tables. A missing value is not zero.',
      'Do not aggregate class returns or sum dollar flows after joining flows to multiple classes.']}
    (output/'quality_report.json').write_text(json.dumps(result,indent=2))
    db.commit()
    return result

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--zip-dir',type=Path,default=ROOT/'data'/'zips')
    p.add_argument('--universe',type=Path,default=ROOT/'universe.csv')
    p.add_argument('--output',type=Path,default=ROOT/'output')
    p.add_argument('--availability-lag-days',type=int,default=60)
    p.add_argument('--availability-overrides',type=Path,help='CSV accession_number,public_date,source; public_date is verified actual dissemination, not the filing date')
    p.add_argument('--export-table',help='Export any table/view from an existing database, without ingesting')
    args=p.parse_args(argv)
    if args.availability_lag_days<0:
        p.error('availability lag must be nonnegative')
    args.output.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(args.output/'nport.sqlite')
    try:
        if args.export_table:
            export(db,args.export_table,args.output/'csv'/(args.export_table+'.csv'));return
        universe=load_universe(args.universe)
        setup(db,universe,digest(args.universe))
        paths=sorted(args.zip_dir.glob('*.zip'))
        if not paths and not db.execute('SELECT 1 FROM archives LIMIT 1').fetchone():
            raise ValueError(f'No ZIP files found in {args.zip_dir}. Download SEC N-PORT quarterly ZIPs here; leave them zipped.')
        overrides={}
        if args.availability_overrides:
            with open(args.availability_overrides,encoding='utf-8-sig',newline='') as f:
                for r in csv.DictReader(f):
                    if not r.get('source') or r['accession_number'] in overrides:
                        raise ValueError('Availability override needs source evidence and unique accession_number')
                    overrides[r['accession_number']]=iso(r['public_date'])
            (args.output/'availability_overrides_used.csv').write_bytes(args.availability_overrides.read_bytes())
        for path in paths:
            ingest(db,path,{r['series_id'] for r in universe})
        with db:
            rebuild(db,args.availability_lag_days,overrides)
        result=quality(db,args.output)
        summary={'version':VERSION,'created_utc':datetime.now(timezone.utc).isoformat(),
                 'universe_sha256':digest(args.universe),'funds':len(universe),
                 'archives':list(dictionaries(db,'SELECT * FROM archives')),
                 'availability_lag_days':args.availability_lag_days,
                 'availability_overrides_sha256':digest(args.availability_overrides) if args.availability_overrides else None,
                 'quality':result}
        (args.output/'run_manifest.json').write_text(json.dumps(summary,indent=2))
        db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        print(f'\nDONE: {args.output / "nport.sqlite"}\nQA: {result["status"]}; read quality_report.json and csv/coverage.csv',flush=True)
    finally:
        db.close()

if __name__=='__main__':
    try:
        main()
    except Exception as e:
        print(f'ERROR: {e}',file=sys.stderr)
        sys.exit(1)
