"""Reproduce Qiang's N-PORT-only positioning analysis.

Run: python analyze_sponsor.py
Inputs are read-only. Outputs go to analysis/results. No external data calls.
Dependencies: pandas, numpy, matplotlib, pyarrow (already installed for this project).
"""
from pathlib import Path
import argparse
import base64
import hashlib
import html
import json
import sqlite3
import time

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parent
CASE = 'S000053068'
CASE_MONTH = '2026-03-31'
# Preference is fixed before observing holdings/risk values. All track unadjusted Agg.
PROXIES = ['S000017334', 'S000004362', 'S000033156']
PROXY_NAMES = dict(zip(PROXIES, ['SPAB', 'AGG', 'SCHZ']))
VBM = 'S000002564'  # float-adjusted; diagnostic only, not common research benchmark
SECTORS = [
    'US Treasury (nominal)', 'TIPS (description identified)',
    'Agency / other government', 'Agency MBS', 'Non-agency MBS / CMBS',
    'ABS / CLO', 'Corporate debt (ratings pending)',
    'Non-US sovereign (non-EM list)', 'Emerging markets (fixed country list)',
    'Municipal', 'Cash / short-term / repo', 'Derivatives (market value)',
    'Other / unresolved',
]
# A research convention, not a claim to reproduce an external provider's EM index.
EM_COUNTRIES = set('AR BR CL CN CO CZ EG HU ID IN MX MY PE PH PL RO RU SA TH TR TW UA VE VN ZA AE QA'.split())
KNOWN_COUNTRIES = set('US CA GB UK DE FR IT ES PT IE NL BE LU CH AT DK SE NO FI IS JP AU NZ HK SG IL KR'.split()) | EM_COUNTRIES
TENORS = ['3MON', '1YR', '5YR', '10YR', '30YR']


def csv(df, path):
    df.to_csv(path, index=False)


def classify(h):
    """Exclusive, ordered Layer-1 rules. Preserve unresolved cases for audit."""
    a = h.ASSET_CAT.fillna('').str.upper()
    i = h.ISSUER_TYPE.fillna('').str.upper()
    country = h.INVESTMENT_COUNTRY.fillna('').str.upper()
    desc = (h.ISSUER_NAME.fillna('') + ' ' + h.ISSUER_TITLE.fillna('')).str.upper()
    derivative = h.DERIVATIVE_CAT.fillna('').ne('') | a.isin(['DIR', 'DCR', 'DCO', 'DFE', 'DE', 'DO'])
    cash = a.isin(['STIV', 'RA'])
    mbs = a.eq('ABS-MBS')
    agency_code = i.isin(['USGA', 'USGSE'])
    agency_name = desc.str.contains(r'FANNIE|FREDDIE|GINNIE|FEDERAL NATIONAL MORTGAGE|FEDERAL HOME LOAN MORTGAGE|GOVERNMENT NATIONAL MORTGAGE', regex=True)
    tips = i.eq('UST') & desc.str.contains(r'INFL|\bTIPS\b', regex=True)
    em = country.isin(EM_COUNTRIES) & (i.isin(['NUSS', 'CORP'])) & a.isin(['DBT', 'LON', 'SN'])
    conditions = [derivative, cash, tips, i.eq('UST'),
                  mbs & agency_code, mbs & agency_name,
                  mbs & i.eq('CORP'), a.str.startswith('ABS-') & ~mbs,
                  agency_code & ~mbs, i.eq('MUN'), em,
                  i.eq('NUSS') & country.isin(KNOWN_COUNTRIES - EM_COUNTRIES - {'US'}),
                  i.eq('CORP') & a.isin(['DBT', 'LON', 'SN'])]
    sectors = [SECTORS[11], SECTORS[10], SECTORS[1], SECTORS[0],
               SECTORS[3], SECTORS[3], SECTORS[4], SECTORS[5], SECTORS[2],
               SECTORS[9], SECTORS[8], SECTORS[7], SECTORS[6]]
    rules = ['derivative_flag_or_asset_code', 'short_term_or_repo_code',
             'UST_and_inflation_description', 'UST_without_inflation_description',
             'MBS_and_agency_code', 'MBS_and_agency_name_fallback',
             'MBS_and_corporate_issuer', 'non_mortgage_ABS_code',
             'agency_issuer_non_MBS', 'municipal_issuer_code',
             'fixed_EM_country_list_debt', 'non_EM_known_foreign_sovereign',
             'corporate_debt_loan_or_note_code']
    out = h[['source_archive_id', 'HOLDING_ID', 'ACCESSION_NUMBER', 'series_id', 'report_month']].copy()
    out['sector'] = np.select(conditions, sectors, default=SECTORS[12])
    out['classification_rule'] = np.select(conditions, rules, default='unresolved_keep_for_review')
    out['reported_weight_pct'] = h.PERCENTAGE
    out['weight_missing'] = h.PERCENTAGE.isna().astype('int64')
    out['abs_reported_weight_pct'] = h.PERCENTAGE.abs()
    # Candidate only: no settlement date is present in these holding fields.
    out['tba_description_candidate'] = (~derivative & mbs & h.ISSUER_TITLE.fillna('').str.upper().str.contains(r'\bTBA\b|^(?:FNCL|FNCI|FGLMC|G2SF)\b', regex=True)).astype('int64')
    out['currency'] = h.CURRENCY_CODE.fillna('UNKNOWN')
    return out


def load_holdings(db, f, out):
    """Stream positions once; write compact per-position rule audit and aggregates."""
    db.execute('CREATE TEMP TABLE selected (source_archive_id TEXT, accession_number TEXT, series_id TEXT, report_month TEXT, PRIMARY KEY(source_archive_id,accession_number))')
    db.executemany('INSERT INTO selected VALUES (?,?,?,?)', f[['source_archive_id', 'accession_number', 'series_id', 'report_month']].itertuples(index=False, name=None))
    fields = ['HOLDING_ID', 'ISSUER_NAME', 'ISSUER_TITLE', 'ASSET_CAT', 'ISSUER_TYPE',
              'INVESTMENT_COUNTRY', 'DERIVATIVE_CAT', 'PERCENTAGE', 'CURRENCY_CODE']
    sql = 'SELECT h.source_archive_id,h.ACCESSION_NUMBER,s.series_id,s.report_month,' + ','.join('h.'+x for x in fields) + ' FROM t_fund_reported_holding h JOIN selected s ON h.source_archive_id=s.source_archive_id AND h.ACCESSION_NUMBER=s.accession_number'
    groups, currency_groups, samples = [], [], []
    writer = None
    case_holdings = []
    count = 0
    try:
        for h in pd.read_sql_query(sql, db, chunksize=100_000):
            a = classify(h)
            table = pa.Table.from_pandas(a, preserve_index=False)
            if writer is None:
                writer = pq.ParquetWriter(out/'holdings_classification_audit.parquet', table.schema, compression='zstd')
            writer.write_table(table)
            g = a.groupby(['series_id','report_month','sector','classification_rule'], dropna=False).agg(
                reported_weight_pct=('reported_weight_pct','sum'),
                abs_reported_weight_pct=('abs_reported_weight_pct','sum'),
                holding_count=('HOLDING_ID','size'), missing_weight_count=('weight_missing','sum'),
                tba_candidate_count=('tba_description_candidate','sum')).reset_index()
            groups.append(g)
            cur = a.groupby(['series_id','report_month','currency']).reported_weight_pct.sum().reset_index()
            currency_groups.append(cur)
            uncertain = a.sector.eq(SECTORS[12]) | a.classification_rule.eq('MBS_and_agency_name_fallback')
            if uncertain.any():
                sample = h.loc[uncertain].copy()
                sample['sector'] = a.loc[uncertain, 'sector']
                sample['classification_rule'] = a.loc[uncertain, 'classification_rule']
                samples.append(sample.assign(abs_weight=sample.PERCENTAGE.abs()).nlargest(100,'abs_weight'))
            case_holdings.append(h.loc[h.series_id.eq(CASE) & h.report_month.eq(CASE_MONTH)])
            count += len(h)
            print(f'Classified {count:,} holdings', flush=True)
    finally:
        if writer:
            writer.close()
    keys = ['series_id','report_month','sector','classification_rule']
    audit = pd.concat(groups).groupby(keys, as_index=False).sum(numeric_only=True)
    csv(audit, out/'classification_rule_totals.csv')
    csv(pd.concat(samples).nlargest(1000,'abs_weight'), out/'classification_review_sample.csv')
    currency = pd.concat(currency_groups).groupby(['series_id','report_month','currency'],as_index=False).reported_weight_pct.sum()
    csv(currency, out/'holdings_by_currency.csv')
    csv(pd.concat(case_holdings), out/'vcobx_case_holdings.csv')
    totals = audit.groupby(['series_id','report_month'],as_index=False).agg(
        reported_holdings_sum_pct=('reported_weight_pct','sum'), holdings=('holding_count','sum'),
        missing_weight_count=('missing_weight_count','sum'), gross_reported_weight_pct=('abs_reported_weight_pct','sum'))
    s = audit.groupby(['series_id','report_month','sector'],as_index=False).reported_weight_pct.sum()
    pivot = s.pivot(index=['series_id','report_month'],columns='sector',values='reported_weight_pct').reindex(columns=SECTORS).fillna(0).reset_index()
    panel = f.merge(totals,on=['series_id','report_month'],validate='one_to_one').merge(pivot,on=['series_id','report_month'],validate='one_to_one')
    panel['cash_outside_holdings_pct'] = 100*panel.cash_not_in_holdings_usd/panel.net_assets
    panel['cash_outside_holdings_missing'] = panel.cash_outside_holdings_pct.isna()
    # CASH_NOT_RPTD_IN_C_OR_D is explicitly outside the holdings table.
    # An unavailable value is not assumed zero: that snapshot remains incomplete.
    panel[SECTORS[10]] += panel.cash_outside_holdings_pct.fillna(0)
    panel['normalization_denominator_pct'] = panel[SECTORS].sum(axis=1)
    panel['sector_complete'] = (panel.missing_weight_count.eq(0) & ~panel.cash_outside_holdings_missing & panel.normalization_denominator_pct.gt(0))
    panel['unresolved_gross_share_pct'] = 100*panel[SECTORS[12]].abs()/panel.gross_reported_weight_pct
    for sector in SECTORS:
        panel['raw__'+sector] = panel[sector]
        panel[sector] = (100*panel[sector]/panel.normalization_denominator_pct).where(panel.sector_complete)
    csv(panel, out/'sector_weights.csv')
    return panel, count


def choose_benchmarks(f):
    b=f[f.series_id.isin(PROXIES)].copy()
    b['proxy_priority']=b.series_id.map({s:i for i,s in enumerate(PROXIES)})
    # All exact dates retained in raw source; ambiguity is rejected earlier.
    return b.sort_values('proxy_priority').drop_duplicates('report_month')


def risk_analysis(f, r, selected_bench, out):
    r = r[r.shock_bp.eq(1)].copy()
    usd=r[r.risk_type.eq('interest_rate') & r.currency.eq('USD')]
    unique=['series_id','report_month','tenor']
    usd=usd.merge(f[['series_id','report_date','report_month']],on=['series_id','report_date'],validate='many_to_one')
    if usd.duplicated(unique).any():
        raise ValueError('Multiple USD risk records per snapshot/tenor; inspect source')
    tenor=usd.pivot(index=['series_id','report_month'],columns='tenor',values='reported_sensitivity_years').reindex(columns=TENORS).reset_index()
    tenor['curve_long_minus_short_signed']=tenor[['10YR','30YR']].sum(axis=1,min_count=2)-tenor[['1YR','5YR']].sum(axis=1,min_count=2)
    bench=selected_bench[['report_month','series_id']].merge(tenor,on=['series_id','report_month'],validate='one_to_one')
    joined=tenor.merge(bench.drop(columns='series_id'),on='report_month',suffixes=('','_benchmark'),how='left',validate='many_to_one')
    for t in TENORS+['curve_long_minus_short_signed']:
        joined['active_signed__'+t]=joined[t]-joined[t+'_benchmark']
    csv(joined,out/'rate_tenor_positions.csv')
    nonusd=r[r.risk_type.eq('interest_rate') & ~r.currency.eq('USD')]
    nonusd=nonusd.groupby(['series_id','report_date','currency'],as_index=False).agg(
        tenor_rows=('tenor','size'),distinct_tenors=('tenor','nunique'),nonmissing=('reported_sensitivity_years','count'),
        reported_sensitivity_years=('reported_sensitivity_years',lambda x:x.sum(min_count=5)))
    nonusd.loc[~(nonusd.tenor_rows.eq(5)&nonusd.distinct_tenors.eq(5)&nonusd.nonmissing.eq(5)),'reported_sensitivity_years']=np.nan
    csv(nonusd,out/'non_us_rate_sensitivities.csv')
    sign=f.assign(negative=f.usd_rate_sensitivity_years_signed.lt(0),positive=f.usd_rate_sensitivity_years_signed.gt(0),
                  magnitude_flag=f.usd_rate_sensitivity_years_signed.abs().gt(10)).groupby('manager',as_index=False).agg(
        snapshots=('series_id','size'),nonmissing=('usd_rate_sensitivity_years_signed','count'),
        negative=('negative','sum'),positive=('positive','sum'),magnitude_flags=('magnitude_flag','sum'))
    csv(sign,out/'rate_sign_audit_by_manager.csv')
    return joined, sign


def returns_analysis(f, out):
    r=pd.read_csv(ROOT/'output/csv/monthly_returns_latest.csv',dtype={'class_id':'string'})
    r['class_id']=r.class_id.fillna('__NO_CLASS__')
    ambiguous=r.duplicated(['series_id','class_id','month_end'],keep=False)
    csv(r[ambiguous],out/'excluded_overlapping_returns.csv')
    clean=r[~ambiguous & r.return_decimal.notna()].copy()
    b=clean[clean.series_id.eq(PROXIES[0])]
    if b.class_id.nunique()!=1 or b.month_end.duplicated().any():
        raise ValueError('SPAB benchmark class is ambiguous; supply verified mapping')
    p=clean.merge(b[['month_end','return_decimal']].rename(columns={'return_decimal':'benchmark_return_decimal'}),on='month_end',validate='many_to_one')
    p['excess_return_decimal']=p.return_decimal-p.benchmark_return_decimal
    u=f[['series_id','fund_name','manager','universe_group']].drop_duplicates()
    p=p.merge(u,on='series_id',validate='many_to_one')
    p=p[p.universe_group.eq('PRIMARY')]
    g=p.groupby(['series_id','class_id','fund_name','manager'],as_index=False).agg(
        n_months=('month_end','nunique'),first_month=('month_end','min'),last_month=('month_end','max'),
        annualized_tracking_error_pct=('excess_return_decimal',lambda x:100*np.sqrt(12)*x.std(ddof=1)),
        annualized_arithmetic_excess_pct=('excess_return_decimal',lambda x:1200*x.mean()))
    g['eligible_36_months']=g.n_months.ge(36)
    csv(g,out/'share_class_tracking_error.csv')
    csv(p,out/'share_class_monthly_excess_returns.csv')
    byfund=g[g.eligible_36_months].groupby(['series_id','fund_name','manager'],as_index=False).agg(
        classes=('class_id','nunique'),minimum_months=('n_months','min'),
        median_class_tracking_error_pct=('annualized_tracking_error_pct','median'),
        minimum_class_tracking_error_pct=('annualized_tracking_error_pct','min'),
        maximum_class_tracking_error_pct=('annualized_tracking_error_pct','max'))
    csv(byfund,out/'fund_class_tracking_error_ranges.csv')
    return g,byfund,len(r[ambiguous])


def swap_case(db,f,out):
    case=f[f.series_id.eq(CASE)&f.report_month.eq(CASE_MONTH)].iloc[0]
    sql='''SELECT h.ISSUER_TITLE,h.ASSET_CAT,h.DERIVATIVE_CAT,s.*
      FROM t_nonforeign_exchange_swap s JOIN t_fund_reported_holding h
      ON h.source_archive_id=s.source_archive_id AND h.HOLDING_ID=s.HOLDING_ID
      WHERE h.source_archive_id=? AND h.ACCESSION_NUMBER=?'''
    s=pd.read_sql_query(sql,db,params=(case.source_archive_id,case.accession_number))
    s['direction']=np.select([
        s.FIXED_OR_FLOATING_PAYMENT.eq('Fixed')&s.FIXED_OR_FLOATING_RECEIPT.eq('Floating'),
        s.FIXED_OR_FLOATING_PAYMENT.eq('Floating')&s.FIXED_OR_FLOATING_RECEIPT.eq('Fixed')],
        ['Pay fixed','Receive fixed'],default='Other')
    s['is_interest_rate_swap']=s.ASSET_CAT.eq('DIR')&s.DERIVATIVE_CAT.eq('SWP')
    s['remaining_years']=(pd.to_datetime(s.TERMINATION_DATE)-pd.Timestamp(case.report_date)).dt.days/365.25
    s['fixed_coupon_decimal']=np.where(s.direction.eq('Pay fixed'),s.FIXED_RATE_PAYMENT,s.FIXED_RATE_RECEIPT)/100
    eligible=s.is_interest_rate_swap&s.direction.ne('Other')&s.CURRENCY_CODE.eq('USD')&s.CURRENCY_CODE_PAYMENT.eq('USD')&s.CURRENCY_CODE_RECEIPT.eq('USD')&s.remaining_years.gt(0)&s.fixed_coupon_decimal.ge(0)&s.NOTIONAL_AMOUNT.notna()
    s['usd_vanilla_approximation_eligible']=eligible
    t=s.remaining_years;r=s.fixed_coupon_decimal
    annuity=pd.Series(np.nan,index=s.index)
    zero=eligible&r.abs().lt(1e-10)
    annuity.loc[zero]=t.loc[zero]
    nz=eligible&~zero
    annuity.loc[nz]=-np.expm1(-t.loc[nz]*np.log1p(r.loc[nz]))/r.loc[nz]
    s['flat_coupon_annuity_years']=annuity
    direction=s.direction.map({'Pay fixed':-1,'Receive fixed':1})
    # Magnitude used only for gross notional scale; direction is from explicit legs.
    s['approx_duration_contribution_years']=direction*s.NOTIONAL_AMOUNT.abs()*annuity/case.net_assets
    csv(s,out/'vcobx_swap_audit.csv')
    currency_summary=s[s.is_interest_rate_swap].groupby(['CURRENCY_CODE','direction'],as_index=False).agg(
        contracts=('HOLDING_ID','size'),gross_notional_in_currency_units=('NOTIONAL_AMOUNT',lambda x:x.abs().sum()))
    csv(currency_summary,out/'vcobx_irs_notionals_by_currency.csv')
    g=s[eligible].groupby('direction',as_index=False).agg(
        contracts=('HOLDING_ID','size'),gross_usd_notional=('NOTIONAL_AMOUNT',lambda x:x.abs().sum()),
        approximation_years=('approx_duration_contribution_years','sum'))
    csv(g,out/'vcobx_usd_swap_summary.csv')
    return s,g,case


def plot_style():
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
        'axes.spines.right':False,'axes.titleweight':'bold','axes.titlesize':14,
        'figure.facecolor':'#fbfcfe','axes.facecolor':'#fbfcfe','savefig.facecolor':'#fbfcfe',
        'axes.labelcolor':'#263449','text.color':'#17273c','xtick.color':'#42546a','ytick.color':'#42546a'})


def savefig(fig,name,out):
    fig.savefig(out/'charts'/f'{name}.png',dpi=170,bbox_inches='tight')
    fig.savefig(out/'charts'/f'{name}.svg',bbox_inches='tight')
    plt.close(fig)


def make_charts(f,sectors,panel,tenor,byfund,swaps,swap_summary,out):
    plot_style()
    # Coverage chart also makes non-synchronous fiscal calendars visible.
    counts=f[f.universe_group.eq('PRIMARY')].groupby('report_month').series_id.nunique()
    fig,ax=plt.subplots(figsize=(10,3.7));ax.bar(pd.to_datetime(counts.index),counts,width=22,color='#2c698d')
    ax.set(title='Different fiscal calendars produce different snapshot months',ylabel='Primary funds reporting',xlabel='Report month')
    fig.autofmt_xdate();savefig(fig,'01_reporting_calendar',out)
    case=panel[panel.series_id.eq(CASE)&panel.report_month.eq(CASE_MONTH)].iloc[0]
    vals=pd.Series({s:case['active_sector_pp__'+s] for s in SECTORS}).sort_values()
    fig,ax=plt.subplots(figsize=(10,6));ax.barh(vals.index,vals,color=np.where(vals.ge(0),'#1a8c83','#d5794a'))
    ax.axvline(0,color='#667085',lw=1);ax.set(xlabel='Normalized fund weight minus proxy weight (percentage points)',title=f'Vanguard Core Bond: sector positioning vs {case.benchmark_proxy}\n{CASE_MONTH}')
    ax.grid(axis='x',alpha=.15);savefig(fig,'02_vcobx_active_sectors',out)
    ct=tenor[tenor.series_id.eq(CASE)&tenor.report_month.eq(CASE_MONTH)].iloc[0]
    fig,ax=plt.subplots(figsize=(9,4));x=np.arange(5)
    ax.bar(x-.18,[ct[t] for t in TENORS],.36,label='Vanguard Core Bond',color='#2c698d')
    ax.bar(x+.18,[ct[t+'_benchmark'] for t in TENORS],.36,label=f'{case.benchmark_proxy} proxy',color='#c69c54')
    ax.set_xticks(x,['3 months','1 year','5 years','10 years','30 years']);ax.axhline(0,color='gray',lw=.7)
    ax.set(title='Where reported USD rate sensitivity sits on the curve',ylabel='Signed sensitivity / net assets × 10,000 (years)')
    ax.legend(frameon=False);savefig(fig,'03_vcobx_rate_curve',out)
    # Compare allocations vs signed rate differences within the case, not cross-family ranks.
    casehist=panel[panel.series_id.eq(CASE)&panel.sector_pair_complete].sort_values('report_month')
    fig,axes=plt.subplots(2,1,figsize=(10,6.5),sharex=True)
    dates=pd.to_datetime(casehist.report_month)
    for sector,color in [(SECTORS[0],'#2c698d'),(SECTORS[6],'#d5794a'),(SECTORS[3],'#1a8c83')]:
        axes[0].plot(dates,casehist['active_sector_pp__'+sector],label=sector,color=color,lw=2)
    axes[0].set(ylabel='Active sector weight (pp)',title='Allocation differences and rate differences answer separate questions');axes[0].legend(fontsize=8,frameon=False,ncol=2)
    safe=casehist.same_rate_sign & ~casehist.rate_magnitude_flag & ~casehist.benchmark_rate_magnitude_flag
    axes[1].plot(dates,casehist.active_usd_rate_signed_years.where(safe),color='#674f91',marker='o',markersize=3)
    axes[1].set(ylabel='Active signed USD sensitivity (years)',xlabel='Report month; matched index-fund proxy only')
    for ax in axes:ax.axhline(0,color='gray',lw=.6);ax.grid(alpha=.15)
    fig.autofmt_xdate();savefig(fig,'04_vcobx_positioning_history',out)
    fig,axes=plt.subplots(1,2,figsize=(11,4),sharex=True)
    for sid,name in list(PROXY_NAMES.items())+[(VBM,'Vanguard total bond (float-adjusted)')]:
        b=f[f.series_id.eq(sid)].sort_values('report_month')
        for ax,col in zip(axes,['usd_rate_sensitivity_years_signed','ig_spread_sensitivity_years_signed']):
            ax.plot(pd.to_datetime(b.report_month),b[col],label=name,lw=1.6)
    axes[0].set(title='USD rate sensitivity',ylabel='Reported signed years');axes[1].set(title='IG credit-spread sensitivity')
    for ax in axes:ax.axhline(0,color='gray',lw=.6);ax.grid(alpha=.15);ax.tick_params(axis='x',rotation=30)
    axes[1].legend(fontsize=8,frameon=False,loc='best')
    fig.suptitle('Index-fund diagnostics: reporting conventions differ',fontweight='bold')
    fig.tight_layout();savefig(fig,'05_benchmark_reporting_conventions',out)
    latest=panel[panel.sector_pair_complete].copy()
    latest['year']=pd.to_datetime(latest.report_month).dt.year
    selected=[SECTORS[0],SECTORS[3],SECTORS[4],SECTORS[6],SECTORS[8]]
    fig,ax=plt.subplots(figsize=(10,4.5))
    for sector in selected:
        v=latest.groupby('year')['active_sector_pp__'+sector].median()
        ax.plot(v.index,v.values,marker='o',label=sector,lw=1.8)
    ax.set(title='Median active allocation in the observed primary-fund sample',ylabel='Median active weight (percentage points)',xlabel='Report year (2026 is partial)')
    ax.axhline(0,color='gray',lw=.6);ax.legend(fontsize=8,frameon=False,ncol=2);ax.grid(alpha=.15)
    savefig(fig,'06_peer_sector_history',out)
    plot=byfund.sort_values('median_class_tracking_error_pct').head(15).copy()
    plot['label']=plot.fund_name.str.replace(' Fund','',regex=False)
    fig,ax=plt.subplots(figsize=(10,6));ax.barh(plot.label.iloc[::-1],plot.median_class_tracking_error_pct.iloc[::-1],color='#2c698d')
    ax.set(title='Lowest median share-class tracking error: descriptive screen',xlabel='Annualized monthly tracking error vs SPAB (%)\nAt least 36 paired months per class; class medians, no averaged fund returns')
    ax.grid(axis='x',alpha=.15);savefig(fig,'07_tracking_error_screen',out)
    fig,axes=plt.subplots(1,2,figsize=(10,4.3))
    z=swap_summary.set_index('direction').reindex(['Pay fixed','Receive fixed'])
    colors=['#d5794a','#1a8c83']
    axes[0].bar(z.index,z.gross_usd_notional/1e9,color=colors);axes[0].set(title='Gross USD IRS notionals',ylabel='USD billions')
    axes[1].bar(z.index,z.approximation_years,color=colors);axes[1].axhline(0,color='gray',lw=.7)
    axes[1].set(title='Approximate contribution',ylabel='Years, flat-coupon annuity approximation')
    fig.suptitle('Vanguard Core Bond: notional alone misses maturity and direction',fontweight='bold')
    fig.tight_layout();savefig(fig,'08_swap_notional_vs_approx_risk',out)


def report(f,sectors,panel,tenor,byfund,swaps,swap_summary,count,excluded_returns,out):
    case=panel[panel.series_id.eq(CASE)&panel.report_month.eq(CASE_MONTH)].iloc[0]
    names=f[['series_id','fund_name']].drop_duplicates().set_index('series_id').fund_name.to_dict()
    paired=panel[panel.sector_pair_complete]
    active=pd.Series({s:case['active_sector_pp__'+s] for s in SECTORS})
    cash=f[f.series_id.eq(CASE)&f.report_month.eq(CASE_MONTH)].iloc[0]
    top=byfund.sort_values('median_class_tracking_error_pct').head(5)
    totals=f[f.universe_group.eq('PRIMARY')]
    signs=(totals.usd_rate_sensitivity_years_signed>0).sum(),(totals.usd_rate_sensitivity_years_signed<0).sum()
    rate_flags=totals.usd_rate_sensitivity_years_signed.abs().gt(10).sum()
    eligible=swaps.usd_vanilla_approximation_eligible
    net_approx=swaps.loc[eligible,'approx_duration_contribution_years'].sum()
    ir=swaps.is_interest_rate_swap
    data={
      'holdings_classified':count,'primary_snapshots':len(panel),'primary_funds':panel.series_id.nunique(),
      'matched_benchmark_snapshots':int(panel.benchmark_series_id.notna().sum()),
      'complete_sector_pairs':int(panel.sector_pair_complete.sum()),
      'funds_with_complete_sector_pairs':int(paired.series_id.nunique()),
      'positive_rate_observations':int(signs[0]),'negative_rate_observations':int(signs[1]),
      'rate_magnitude_flags':int(rate_flags),'excluded_overlapping_return_rows':excluded_returns,
      'eligible_tracking_error_funds':len(byfund),'case_benchmark':case.benchmark_proxy,
      'case_active_sector_pp':active.to_dict(),'case_signed_rate_years':case.usd_rate_sensitivity_years_signed,
      'case_benchmark_signed_rate_years':case.benchmark_usd_rate_sensitivity_years_signed,
      'case_active_signed_rate_years':case.active_usd_rate_signed_years,
      'case_sector_reallocation_pct':case.sector_reallocation_pct,
      'case_swap_records':len(swaps),'case_interest_rate_swap_records':int(ir.sum()),
      'case_other_swap_records':int((~ir).sum()),'case_usd_irs_approximation_records':int(eligible.sum()),
      'case_approx_usd_irs_duration_contribution_years':net_approx,
    }
    (out/'key_results.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
    sponsor='''Qiang\'s October 23 email (PDF pp. 14-17) asks for a fund-quarter positioning table with two layers: normalized sector allocations and active factor exposures. His October 6 instructions (pp. 11-12) specify the common Bloomberg U.S. Aggregate benchmark, a 49-fund primary sample, careful fiscal-date alignment, and warnings about survivorship and cross-family spread-risk conventions. The October 23 instructions supersede the earlier designated-index benchmark suggestion.

His three corrections are: measure swap direction using risk and maturity rather than gross notional; distinguish interest-rate swaps from credit and other swaps; and calculate benchmark weights from actual index-fund filings. This analysis implements those corrections to the extent the supplied data supports them.'''
    findings=[
      f'Of {len(panel):,} primary fund snapshots across {panel.series_id.nunique()} funds, {panel.benchmark_series_id.notna().sum():,} have a same-report-month Aggregate proxy. Complete sector comparisons are available for {len(paired):,} snapshots across {paired.series_id.nunique()} funds. Unmatched or incomplete snapshots remain in the panel with missing active sector values.',
      f'For Vanguard Core Bond on {CASE_MONTH}, the same-month {case.benchmark_proxy} proxy gives a nominal Treasury active weight of {active[SECTORS[0]]:+.2f} pp, corporate debt (ratings pending) {active[SECTORS[6]]:+.2f} pp, and agency MBS {active[SECTORS[3]]:+.2f} pp. Half the sum of absolute sector differences is {case.sector_reallocation_pct:.2f}%. This is sector-level reallocation, not security-level active share.',
      f'The same case reports USD rate sensitivity of {case.usd_rate_sensitivity_years_signed:.3f} signed years versus {case.benchmark_usd_rate_sensitivity_years_signed:.3f} for the proxy: a difference of {case.active_usd_rate_signed_years:+.3f} signed years. Large sector reallocations coexist with a much smaller difference in total reported rate sensitivity. Neither derivative market value nor Treasury weight alone measures duration.',
      f'The sample contains {ir.sum()} interest-rate swaps among {len(swaps)} non-FX swap records in the case filing. The other {(~ir).sum()} are kept outside the interest-rate bucket. There are {(swaps[ir].direction=="Pay fixed").sum()} pay-fixed and {(swaps[ir].direction=="Receive fixed").sum()} receive-fixed IRS records across currencies. For the {eligible.sum()} eligible USD fixed/floating swaps, the flat-coupon annuity approximation gives a net {net_approx:+.3f} years of duration contribution. This is a rough cross-check, not a replacement for the filed risk or an addition to it.',
      f'A unit reconciliation remains open with the emailed swap illustration: the filing includes JPY 25.23 billion and HUF 5.44 billion notionals, while eligible USD IRS gross notionals total USD {swap_summary.gross_usd_notional.sum()/1e9:.2f} billion. Currency-unit notionals cannot be summed and labeled dollars. This USD-only approximation does not reproduce the email\'s roughly +0.6-year all-swap estimate; seven non-USD IRS records are outside this approximation. Resolve currency conversion and valuation assumptions before treating that estimate as validated.',
      f'Across primary snapshots, {signs[0]} USD rate sensitivities are positive and {signs[1]} negative; {rate_flags} exceed the 10-year absolute-magnitude diagnostic. Therefore a raw cross-family duration league table would mix conventions. Signed fields and active signed differences are retained for audit, without automatic absolute-value or sign correction.',
      f'Class-level tracking-error estimates with at least 36 paired months are available for {len(byfund)} primary funds. These identify index-like behavior for follow-up; they do not identify manager skill. Different class fees, sample windows and proxy tracking differences remain. No reference share class is chosen and no class returns are averaged.'
    ]
    limitations=[
      'Benchmark: SPAB is the fixed first-choice unadjusted Aggregate proxy; AGG then SCHZ are used only when SPAB lacks the exact report month. Actual proxy ID, report date and lag in days are recorded. There is no nearest-quarter fill, future report substitution, interpolation or calendar-date forward filling. Report-month alignment permits last-business-day versus calendar-month-end differences; exact dates are retained.',
      'Sector denominator: reported position weights plus separately reported cash outside holdings are normalized to 100%. Original weights, cash and denominator are retained. Delayed-delivery payables remain a separate diagnostic and are not inserted as an extra negative sector. A missing position weight or unreported-cash value makes the snapshot incomplete; incomplete pairs have no active sector output. Negative weights are preserved.',
      f'Classification: SEC asset/issuer codes take precedence. Treasury inflation descriptions identify TIPS; nominal Treasury rows without an inflation description still require CUSIP validation. Agency-name fallback, TBA-description candidates and unresolved positions are auditable. There is no official EM-country membership source here: the fixed study list is exported. Countries outside both study lists remain unresolved (including some sovereigns). Corporate IG/HY ratings are unavailable and remain combined. The Vanguard case has {case[SECTORS[12]]:.2f}% in Other / unresolved. Sector completeness refers to input coverage, not independently verified classification accuracy.',
      'Risk: values use filed DV01 × 10,000 / positive net assets and require all five tenors. They include derivatives already. Sign alignment is not verification of economic duration. Same-sign status and magnitude flags are recorded, but cross-family economic rankings and credit-risk conclusions are withheld. No manual sign convention is assumed.',
      'Swaps: only explicit DIR/SWP fixed/floating USD legs are included in the approximation. Remaining maturity and the fixed coupon provide a flat annual discount-rate annuity estimate; there is no observed yield curve, schedule, collateral discounting, basis, optionality or FX conversion. Foreign-currency notionals are never added to USD notionals. Missing or ineligible swap records remain in the audit.',
      'Tracking error: monthly return differences versus the single reported SPAB ETF class; sample standard deviation × sqrt(12), in percent. All rows belonging to an overlapping fund/class/month group are excluded. At least 36 paired observed months are required, with each class\'s dates shown. These are observed-sample estimates, not common-window performance ranks or alpha estimates.',
      'Timing and universe: retrospective latest filings, not a point-in-time backtest. The supplied fund list is a current starting snapshot, not a survivorship-free universe. 2026 is partial and latest holdings dates differ by fiscal calendar. No holdings turnover or causal performance claim is made.',
    ]
    sector_table=pd.DataFrame({'Sector':SECTORS,'Fund %':[case[s] for s in SECTORS],
      'Proxy %':[case['benchmark_sector__'+s] for s in SECTORS],
      'Active pp':[active[s] for s in SECTORS]})
    csv(sector_table,out/'vcobx_sector_comparison.csv')
    factor_status=pd.DataFrame([
      ['1. US duration','Reported signed active sensitivity; economic sign unverified','active_usd_rate_signed_years'],
      ['2. US curve','Five signed tenors and long-minus-short diagnostic','rate_tenor_positions.csv'],
      ['3. Non-US rates / FX','Reported currency rate risk and holdings currency mix; net FX unavailable','non_us_rate_sensitivities.csv'],
      ['4. MBS','Active agency and non-agency weights; TBA candidates separately flagged','active_sector_pp__Agency MBS'],
      ['5. TIPS / breakevens / swap spreads','Description-identified TIPS and one-case USD IRS approximation only','active_sector_pp__TIPS (description identified)'],
      ['6. Credit risk','Filed IG/HY signed sensitivity differences for audit; cross-family comparability unverified','active_ig_spread_signed_years'],
      ['7. Credit quality','Not available without security ratings','not computed'],
      ['8. Rates / credit hedging','Not available without independent factor returns and verified reference classes','not computed'],
    ],columns=['Sponsor factor','Delivered status','Field / output'])
    csv(factor_status,out/'factor_delivery_status.csv')
    md='# Qiang sponsor analysis: N-PORT-only first pass\n\n'+sponsor+'\n\n## Findings\n\n'+'\n\n'.join(f'{i+1}. {x}' for i,x in enumerate(findings))+'\n\n## Methods and limits\n\n'+'\n\n'.join('- '+x for x in limitations)
    md+='\n\n## Reproduce\n\nRun `python analyze_sponsor.py` from the project folder. Inputs are read-only; outputs are in `analysis/results`. The HTML report embeds the charts and can be opened directly in a browser.\n'
    (out/'conclusions.md').write_text(md,encoding='utf-8')
    image_sections=[
      ('01_reporting_calendar','Dates determine which comparisons are possible', 'Quarterly fiscal snapshots do not form a synchronized monthly holdings panel.'),
      ('02_vcobx_active_sectors','Layer 1: where the money is', 'Weights are normalized separately. Derivatives remain a market-value sector; corporate ratings remain pending.'),
      ('03_vcobx_rate_curve','Layer 2: where reported rate sensitivity sits', 'Filed signs are preserved. Buckets are key-rate sensitivities, not maturity allocations.'),
      ('04_vcobx_positioning_history','Follow the same fund through time', 'Signed risk differences are shown only when both rate signs agree and neither magnitude exceeds 10 years. This screen does not verify sign conventions.'),
      ('05_benchmark_reporting_conventions','A comparability check before any credit ranking', 'The four proxies have different fiscal dates, signs and spread-risk conventions; the Vanguard proxy tracks the float-adjusted index.'),
      ('06_peer_sector_history','Scale the sector comparison to the supplied peer group', 'Each point is a median across available complete paired snapshots, not a balanced-panel trend or the total fund industry.'),
      ('07_tracking_error_screen','Find funds to investigate for index-like behavior', 'Median of class-specific tracking errors, with at least 36 paired months per class. Different windows prevent a strict performance ranking.'),
      ('08_swap_notional_vs_approx_risk','Use maturity and direction to interpret swaps', 'USD interest-rate swaps only. The approximation is a sensitivity cross-check and must not be added to filed fund risk.'),
    ]
    content=''
    for name,title,caption in image_sections:
        data64=base64.b64encode((out/'charts'/f'{name}.png').read_bytes()).decode()
        content+=f'<section><h2>{html.escape(title)}</h2><img src="data:image/png;base64,{data64}" alt="{html.escape(title)}"><p class="caption">{html.escape(caption)}</p></section>'
    cards=f'<div class="cards"><div><b>49</b>primary funds</div><div><b>{len(paired):,}</b>complete sector pairs</div><div><b>{count/1e6:.2f}m</b>positions classified</div><div><b>2 layers</b>allocation + reported risk</div></div>'
    body=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Qiang sponsor analysis</title><style>
body{{margin:0;background:#edf2f7;color:#17273c;font:16px/1.65 system-ui,sans-serif}}main{{max-width:1100px;margin:auto;padding:42px 28px}}h1{{font-size:42px;line-height:1.15;max-width:850px}}h2{{font-size:25px}}.eyebrow{{font-size:13px;letter-spacing:2px;color:#2c698d;font-weight:700}}section,.intro{{background:white;padding:28px;margin:24px 0;border-radius:12px}}img{{width:100%;height:auto}}.caption{{color:#52647b;font-size:14px}}.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}}.cards div{{background:#173c55;color:#fff;padding:20px;border-radius:10px}}.cards b{{display:block;font-size:28px}}table{{border-collapse:collapse;width:100%;font-size:13px}}th,td{{padding:9px;text-align:left;border-bottom:1px solid #dce4ec}}li{{margin:12px 0}}.notice{{border-left:4px solid #d5794a;padding-left:20px}}@media(max-width:700px){{.cards{{grid-template-columns:1fr 1fr}}main{{padding:20px 12px}}h1{{font-size:32px}}section{{padding:16px}}table{{display:block;overflow-x:auto}}}}
</style></head><body><main><div class="eyebrow">VANGUARD / CMU CAPSTONE · N-PORT ANALYSIS</div><h1>Where is the money,<br>and where is the risk?</h1><p>A reproducible first pass following Qiang's October 6 and October 23 instructions. Supplied archives: 2019 Q4–2026 Q3. Historical, descriptive research.</p>{cards}<div class="intro"><h2>What Qiang wants</h2><p>{html.escape(sponsor).replace(chr(10),'<br>')}</p><p class="notice">This report delivers sectors and reported sensitivities. Economic risk signs, ratings, independent factor returns and a survivorship-free universe still need work. It does not establish manager skill.</p></div><section><h2>What the data says</h2><ol>{''.join('<li>'+html.escape(x)+'</li>' for x in findings)}</ol></section>{content}<section><h2>Vanguard Core Bond sector detail · {CASE_MONTH}</h2>{sector_table.to_html(index=False,float_format=lambda x:f'{x:,.2f}',border=0)}</section><section><h2>Eight-factor delivery map</h2>{factor_status.to_html(index=False,border=0)}</section><section><h2>Methods, missing inputs and interpretation</h2><ul>{''.join('<li>'+html.escape(x)+'</li>' for x in limitations)}</ul></section><section><h2>Reproduce and inspect</h2><p>Run <code>python analyze_sponsor.py</code>. The main output is <code>positioning_panel.csv</code>. Supporting CSVs preserve proxy dates, classification rules, missingness, signed tenor exposures, individual swap records and class-level return statistics. Per-position rules are in <code>holdings_classification_audit.parquet</code>. Source: local <code>email_capstone.pdf</code>, especially pages 11–17; original SEC archives and <code>output/run_manifest.json</code>.</p><p>Standalone PNG and SVG charts are in <code>charts/</code>. No external data or network calls were used in the analysis.</p></section></main></body></html>'''
    (out/'report.html').write_text(body,encoding='utf-8')
    return data


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'analysis/results')
    args=parser.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=True);(out/'charts').mkdir(exist_ok=True)
    start=time.time()
    f=pd.read_csv(ROOT/'output/csv/fund_quarter.csv',dtype={'series_id':str})
    # Reject same-month multiple exact report dates instead of silently collapsing them.
    duplicate=f.duplicated(['series_id','report_month'],keep=False)
    csv(f[duplicate],out/'excluded_ambiguous_snapshot_months.csv')
    f=f[~duplicate].copy()
    r=pd.read_csv(ROOT/'output/csv/risk_normalized_latest.csv')
    db=sqlite3.connect('file:'+str(ROOT/'output/nport.sqlite').replace('\\','/')+'?mode=ro',uri=True)
    sectors,count=load_holdings(db,f,out)
    benchmark=choose_benchmarks(sectors)
    b=benchmark[['series_id','fund_name','report_month','report_date','sector_complete',
        'usd_rate_sensitivity_years_signed','ig_spread_sensitivity_years_signed','hy_spread_sensitivity_years_signed']+SECTORS].copy()
    b=b.rename(columns={c:('benchmark_sector__'+c if c in SECTORS else 'benchmark_'+c) for c in b.columns if c!='report_month'})
    panel=sectors[sectors.universe_group.eq('PRIMARY')].merge(b,on='report_month',how='left',validate='many_to_one')
    panel['benchmark_proxy']=panel.benchmark_series_id.map(PROXY_NAMES)
    panel['benchmark_date_difference_days']=(pd.to_datetime(panel.report_date)-pd.to_datetime(panel.benchmark_report_date)).dt.days
    panel['benchmark_match_status']=np.where(panel.benchmark_series_id.notna(),'SAME_REPORT_MONTH','NO_SAME_MONTH_PROXY')
    panel['sector_pair_complete']=panel.sector_complete & panel.benchmark_sector_complete.eq(True)
    for sector in SECTORS:
        panel['active_sector_pp__'+sector]=(panel[sector]-panel['benchmark_sector__'+sector]).where(panel.sector_pair_complete)
    acols=['active_sector_pp__'+s for s in SECTORS]
    panel['sector_reallocation_pct']=.5*panel[acols].abs().sum(axis=1,min_count=len(SECTORS))
    for name in ['usd_rate','ig_spread','hy_spread']:
        panel['active_'+name+'_signed_years']=panel[name+'_sensitivity_years_signed']-panel['benchmark_'+name+'_sensitivity_years_signed']
    panel['same_rate_sign']=np.sign(panel.usd_rate_sensitivity_years_signed).eq(np.sign(panel.benchmark_usd_rate_sensitivity_years_signed))
    panel['rate_magnitude_flag']=panel.usd_rate_sensitivity_years_signed.abs().gt(10)
    panel['benchmark_rate_magnitude_flag']=panel.benchmark_usd_rate_sensitivity_years_signed.abs().gt(10)
    panel['economic_rate_sign_verified']=False
    panel['cross_family_credit_comparability_verified']=False
    panel['factor7_credit_quality']=np.nan
    panel['factor8_rate_credit_hedging']=np.nan
    panel['delayed_delivery_payables_pct_net_assets']=100*panel.delayed_delivery_payables_usd/panel.net_assets
    tenor,signs=risk_analysis(f,r,benchmark,out)
    panel=panel.merge(tenor[['series_id','report_month']+['active_signed__'+t for t in TENORS]+['active_signed__curve_long_minus_short_signed']],on=['series_id','report_month'],how='left',validate='one_to_one')
    csv(panel,out/'positioning_panel.csv')
    g,byfund,excluded=returns_analysis(f,out)
    swaps,swap_summary,case=swap_case(db,f,out)
    db.close()
    # Invariants concern actual research correctness, not only successful execution.
    assert sectors.loc[sectors.sector_complete,SECTORS].sum(axis=1).sub(100).abs().max()<1e-8
    assert panel.loc[panel.sector_pair_complete,acols].sum(axis=1).abs().max()<1e-8
    assert panel.benchmark_date_difference_days.dropna().abs().max()<=3
    assert not panel.duplicated(['series_id','report_month']).any()
    assert not g.duplicated(['series_id','class_id']).any()
    make_charts(f,sectors,panel,tenor,byfund,swaps,swap_summary,out)
    data=report(f,sectors,panel,tenor,byfund,swaps,swap_summary,count,excluded,out)
    manifest={'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
      'input_run_manifest_sha256':hashlib.sha256((ROOT/'output/run_manifest.json').read_bytes()).hexdigest(),
      'email_pdf_sha256':hashlib.sha256((ROOT/'email_capstone.pdf').read_bytes()).hexdigest(),
      'proxy_priority':PROXIES,'tracking_error_proxy':PROXIES[0],
      'em_country_list':sorted(EM_COUNTRIES),'elapsed_seconds':round(time.time()-start,2),
      'csv_input_sha256':{name:hashlib.sha256((ROOT/'output/csv'/name).read_bytes()).hexdigest() for name in ['fund_quarter.csv','risk_normalized_latest.csv','monthly_returns_latest.csv']},
      'versions':{'pandas':pd.__version__,'numpy':np.__version__,'matplotlib':matplotlib.__version__,'pyarrow':pa.__version__},
      'assertions':'sector totals 100; active totals zero; benchmark month alignment; unique panel and class keys',
      'excluded_ambiguous_snapshot_rows':int(duplicate.sum())}
    (out/'analysis_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps(data,indent=2));print('Report:',out/'report.html',flush=True)


if __name__=='__main__':
    main()
