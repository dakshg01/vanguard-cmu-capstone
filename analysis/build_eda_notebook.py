"""Build the editable EDA notebook. The analysis itself lives in notebook cells."""
from pathlib import Path
import textwrap
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
cells = []
def md(s): cells.append(nbf.v4.new_markdown_cell(textwrap.dedent(s).strip()))
def code(s): cells.append(nbf.v4.new_code_cell(textwrap.dedent(s).strip()))

md('''
# Capstone EDA: funds, flows, allocations and reported risk

**Question:** What does our N-PORT panel reveal about fund behavior, and which comparisons are defensible?

This notebook uses the supplied 59-fund universe and the previously extracted SEC data. The main peer group is the 49 PRIMARY funds. It reads source data without modifying it, creates its own charts/tables in `analysis/eda/`, and can be run from top to bottom.

We examine coverage and missingness, fund size and flows, **common-window share-class performance**, sector allocation, filed risk conventions, a descriptive flow/reallocation relationship, a one-factor return regression, and the sponsor's Vanguard Core Bond swap case.

**Interpretation:** retrospective EDA, not a point-in-time backtest or an estimate of manager skill. Sector classifications are provisional. Filed risk signs and credit conventions are not harmonized. We never average class returns into a fund return or add estimated derivative risk to reported totals.
''')
md('''
## 1. Setup and input validation

The notebook uses small CSV exports and cached audited analysis results rather than repeatedly loading the 8.95 GB database. Hash checks stop execution if those cached results no longer match the extraction inputs. Run `python analyze_sponsor.py` first if the check fails.

Dependencies: pandas, numpy, matplotlib and statsmodels. The current environment already has them. No downloads or network calls occur in the analysis.
''')
code('''
from pathlib import Path
import hashlib, json, platform
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
from IPython.display import display, Markdown

roots = [Path.cwd(), *Path.cwd().parents]
ROOT = next((p for p in roots if (p / 'universe.csv').exists() and (p / 'output/csv/fund_quarter.csv').exists()), None)
assert ROOT is not None, 'Run this notebook from inside the capstone project.'
CSV = ROOT / 'output/csv'
RESULTS = ROOT / 'analysis/results'
EDA = ROOT / 'analysis/eda'
(EDA / 'charts').mkdir(parents=True, exist_ok=True)
(EDA / 'tables').mkdir(exist_ok=True)

manifest = json.loads((RESULTS / 'analysis_manifest.json').read_text())
for name, expected in manifest['csv_input_sha256'].items():
    actual = hashlib.sha256((CSV / name).read_bytes()).hexdigest()
    assert actual == expected, f'{name} changed. Rerun python analyze_sponsor.py.'

plt.rcParams.update({'figure.figsize': (11, 4.5), 'figure.dpi': 110,
    'axes.spines.top': False, 'axes.spines.right': False,
    'axes.titleweight': 'bold', 'axes.titlesize': 14,
    'axes.facecolor': '#fbfcfe', 'figure.facecolor': '#fbfcfe',
    'axes.prop_cycle': plt.cycler(color=['#24698d','#df8751','#168b83','#815fa5','#b59a45'])})
pd.set_option('display.max_columns', 20)
pd.set_option('display.max_colwidth', 70)

def save_chart(name, fig=None):
    fig = fig or plt.gcf()
    fig.savefig(EDA / 'charts' / f'{name}.png', dpi=170, bbox_inches='tight')
    fig.savefig(EDA / 'charts' / f'{name}.svg', bbox_inches='tight')
    plt.show()
    plt.close(fig)

def save_table(frame, name):
    frame.to_csv(EDA / 'tables' / f'{name}.csv', index=False)
    return frame

def note(text):
    display(Markdown('**Interpretation.** ' + text))

print('Project:', ROOT)
print('Python', platform.python_version(), '| pandas', pd.__version__, '| numpy', np.__version__)
''')
code('''
universe = pd.read_csv(ROOT / 'universe.csv', dtype={'series_id': str, 'cik': str})
funds = pd.read_csv(CSV / 'fund_quarter.csv', dtype={'series_id': str, 'cik': str})
returns = pd.read_csv(CSV / 'monthly_returns_latest.csv', dtype={'series_id': str, 'class_id': str})
flows = pd.read_csv(CSV / 'monthly_flows_latest.csv', dtype={'series_id': str})
holdings_checks = pd.read_csv(CSV / 'holdings_checks.csv')
positions = pd.read_csv(RESULTS / 'positioning_panel.csv')
sectors = pd.read_csv(RESULTS / 'sector_weights.csv')
swap_audit = pd.read_csv(RESULTS / 'vcobx_swap_audit.csv', dtype={'HOLDING_ID': str})
quality = json.loads((ROOT / 'output/quality_report.json').read_text())

for frame in [funds, returns, flows, positions, sectors]:
    for col in ['report_date','report_month','month_end','filing_date','available_date_assumed']:
        if col in frame:
            frame[col] = pd.to_datetime(frame[col])
primary_ids = set(universe.loc[universe['group'].eq('PRIMARY'), 'series_id'])
primary = funds[funds.series_id.isin(primary_ids)].copy()
META = universe[['series_id','fund_name','manager','style','group']]
assert not funds.duplicated(['series_id','report_date']).any()
assert len(primary_ids) == 49

inventory = pd.DataFrame({
    'dataset': ['Universe','Latest fund snapshots','Latest holdings','Class-month return rows','Fund-month flow rows'],
    'rows': [len(universe),len(funds),int(holdings_checks.holding_count.sum()),len(returns),len(flows)]})
display(save_table(inventory, 'data_inventory'))
display(funds.groupby('universe_group').agg(funds=('series_id','nunique'),snapshots=('series_id','size'),
    first_report=('report_date','min'),last_report=('report_date','max')))
print('Snapshot dates:', funds.report_date.min().date(), 'to', funds.report_date.max().date())
print('Monthly dates:', returns.month_end.min().date(), 'to', returns.month_end.max().date())
''')
md('''
## 2. Coverage: when do we actually observe each fund?

Holdings are fiscal snapshots. The heatmap below records whether a fund has a report in a calendar quarter; it does **not** turn those filings into synchronized quarter-end observations. New funds and incomplete histories should remain visible.
''')
code('''
coverage = primary.groupby(['series_id','fund_name']).agg(
    first_report=('report_date','min'),last_report=('report_date','max'),snapshots=('report_date','size')).reset_index()
q = primary.assign(quarter=primary.report_date.dt.to_period('Q').astype(str))
matrix = q.groupby(['fund_name','quarter']).size().unstack(fill_value=0).sort_index()
fig, ax = plt.subplots(figsize=(13, 11))
im = ax.imshow(matrix.gt(0), aspect='auto', cmap='Blues', vmin=0, vmax=1, interpolation='none')
ax.set_yticks(range(len(matrix)), matrix.index, fontsize=7)
ax.set_xticks(range(len(matrix.columns)), matrix.columns, rotation=65, ha='right', fontsize=8)
ax.set(title='Observed PRIMARY-fund reporting quarters', xlabel='Calendar quarter containing report date')
fig.tight_layout(); save_chart('01_coverage_heatmap', fig)
display(save_table(coverage.sort_values('snapshots'), 'fund_coverage').head(10))
note(f'The primary sample spans {len(coverage)} funds, with {coverage.snapshots.min()}–{coverage.snapshots.max()} snapshots per fund. '
     'Empty cells are not zero holdings. The current fund list also omits historical funds that were never supplied, so it cannot establish survivorship-free performance.')
''')
md('''
## 3. Data quality, missingness and reporting lags

A successful extraction is different from economically comparable data. We separate parser checks, missing values, overlapping monthly observations and risk-magnitude diagnostics.
''')
code('''
checks = pd.Series(quality['checks'], name='flagged_count').rename_axis('check').reset_index()
display(save_table(checks, 'quality_checks'))
numeric_fields = ['net_assets','cash_not_in_holdings_usd','delayed_delivery_payables_usd',
    'usd_rate_sensitivity_years_signed','ig_spread_sensitivity_years_signed','hy_spread_sensitivity_years_signed']
missing = pd.DataFrame({'field': numeric_fields,
    'missing_snapshots': [funds[c].isna().sum() for c in numeric_fields],
    'missing_pct': [100*funds[c].isna().mean() for c in numeric_fields]})
display(save_table(missing, 'snapshot_missingness'))
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
axes[0].barh(missing.field.str.replace('_',' '), missing.missing_pct)
axes[0].set(title='Snapshot-field missingness', xlabel='Missing observations (%)')
axes[1].hist(funds.filing_lag_days, bins=25, color='#168b83')
axes[1].set(title='Reporting lag', xlabel='Filing date minus report date (days)', ylabel='Snapshots')
fig.tight_layout(); save_chart('02_missingness_and_lags', fig)
note(f'There are {returns.return_decimal.isna().sum()} missing monthly returns. Median filing lag is '
     f'{funds.filing_lag_days.median():.0f} calendar days. Filing date alone is not verified historical public availability. '
     'Overlapping monthly reports are excluded in the analyses below; missing values are never filled with zero.')
''')
md('''
## 4. Fund size: scale and changing assets

Net assets combine investment results and investor flows. A large AUM decline is not a cumulative investment loss. The selected histories are descriptive examples, not a representative industry index.
''')
code('''
latest = primary.sort_values('report_date').groupby('series_id', as_index=False).tail(1).copy()
display(save_table(latest[['series_id','fund_name','report_date','net_assets']].sort_values('net_assets',ascending=False), 'latest_fund_size').head(12))
fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
axes[0].hist(np.log10(latest.net_assets / 1e9), bins=14)
axes[0].set(title='Latest observed assets across primary funds', xlabel='log10(net assets / USD billion)', ylabel='Funds')
examples = primary[primary.fund_name.str.contains('Western Asset|Vanguard Core Bond Fund|PIMCO Total Return',case=False,regex=True)]
for sid, g in examples.groupby('series_id'):
    g = g.sort_values('report_date')
    axes[1].plot(g.report_date, g.net_assets / 1e9, label=g.fund_name.iloc[0], lw=2)
axes[1].set(title='Illustrative AUM histories', ylabel='Net assets (USD billions)')
axes[1].legend(fontsize=7, frameon=False)
fig.autofmt_xdate(); fig.tight_layout(); save_chart('03_fund_size', fig)
note(f'The median latest observed PRIMARY fund has USD {latest.net_assets.median()/1e9:.2f} billion in assets. '
     'These latest dates differ by fiscal calendar; inspect the displayed dates before comparing funds.')
''')
md('''
## 5. Investor flows: amounts and scale-adjusted quarterly intervals

We first remove **all rows** in overlapping fund/month groups. For a scale-adjusted measure, we sum the three monthly external-flow observations from a filing and divide by the previous snapshot's net assets **only when snapshots are exactly three report months apart**. This is an interval flow / beginning-assets measure, not a reported monthly flow percentage.
''')
code('''
flow_overlap = flows.duplicated(['series_id','month_end'], keep=False)
clean_flows = flows.loc[~flow_overlap].copy()
save_table(flows[flow_overlap], 'excluded_flow_overlap_rows')
assert not clean_flows.duplicated(['series_id','month_end']).any()

fq = clean_flows.groupby(['series_id','accession_number','report_date'], as_index=False).agg(
    net_external_flow_usd=('net_external_flow_usd','sum'), n_flow_months=('month_end','nunique'),
    first_flow_month=('month_end','min'), last_flow_month=('month_end','max'))
intervals = primary.sort_values(['series_id','report_month']).copy()
intervals['previous_report_month'] = intervals.groupby('series_id').report_month.shift()
intervals['previous_net_assets'] = intervals.groupby('series_id').net_assets.shift()
intervals['month_number'] = intervals.report_month.dt.year * 12 + intervals.report_month.dt.month
intervals['months_since_previous'] = intervals.groupby('series_id').month_number.diff()
intervals = intervals.merge(fq,on=['series_id','accession_number','report_date'],how='left',validate='one_to_one')
intervals['three_month_interval'] = intervals.months_since_previous.eq(3) & intervals.n_flow_months.eq(3) & intervals.previous_net_assets.gt(0)
intervals['interval_net_flow_pct'] = (100*intervals.net_external_flow_usd/intervals.previous_net_assets).where(intervals.three_month_interval)
valid_flows = intervals[intervals.interval_net_flow_pct.notna()].copy()
display(save_table(valid_flows[['series_id','fund_name','report_date','previous_net_assets','net_external_flow_usd','interval_net_flow_pct']], 'three_month_flow_intervals').describe(include='number'))

fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
within_plot = valid_flows.interval_net_flow_pct.between(-30,30)
axes[0].hist(valid_flows.loc[within_plot,'interval_net_flow_pct'],bins=40)
axes[0].set(title='Three-month external flow / beginning assets',xlabel='Interval net flow (%)',ylabel='Fund intervals')
axes[0].text(.02,.94,f'{(~within_plot).sum()} tail observations outside ±30% not shown',transform=axes[0].transAxes,fontsize=8,va='top')
annual_flows = clean_flows[clean_flows.series_id.isin(primary_ids)].assign(year=lambda d:d.month_end.dt.year).groupby('year').net_external_flow_usd.sum()/1e9
axes[1].bar(annual_flows.index,annual_flows.values,color=np.where(annual_flows.ge(0),'#168b83','#df8751'))
axes[1].set(title='Observed primary-sample net external flows',ylabel='USD billions',xlabel='2019 and 2026 are partial years')
for ax in axes: ax.axhline(0,color='gray',lw=.6)
fig.tight_layout(); save_chart('04_investor_flows',fig)
note(f'{len(valid_flows):,} three-month intervals meet the timing and flow-coverage checks. Their median net flow is '
     f'{valid_flows.interval_net_flow_pct.median():+.2f}% of beginning assets. The annual dollar bars reflect the supplied, changing sample; '
     'they are not total industry flows and do not prove that poor returns caused redemptions.')
''')
md('''
## 6. Returns on a common window: January 2021–December 2025

Comparing tracking errors over different periods can confuse market conditions with fund differences. Here every eligible **share class** must have all 60 monthly returns in the same window, with no duplicated class/month observations. SPAB's sole reported class is the common Aggregate proxy.

Metrics: annualized tracking error = monthly excess-return sample standard deviation × √12; annualized volatility = monthly-return sample standard deviation × √12; CAGR compounds the actual 60 returns; maximum drawdown is measured at month-end with starting wealth of 1.
''')
code('''
START, END = pd.Timestamp('2021-01-31'), pd.Timestamp('2025-12-31')
EXPECTED_MONTHS = pd.date_range(START, END, freq='ME')
return_overlap = returns.duplicated(['series_id','class_id','month_end'],keep=False)
clean_returns = returns[~return_overlap & returns.return_decimal.notna()].copy()
save_table(returns[return_overlap], 'excluded_return_overlap_rows')
window = clean_returns[clean_returns.month_end.between(START, END)].copy()
assert window.return_decimal.gt(-1).all(), 'Return <= -100% requires investigation before compounding.'
benchmark = window[window.series_id.eq('S000017334')].copy()
assert benchmark.class_id.nunique() == 1 and not benchmark.month_end.duplicated().any()
assert set(benchmark.month_end) == set(EXPECTED_MONTHS)
paired = window[window.series_id.isin(primary_ids)].merge(
    benchmark[['month_end','return_decimal']].rename(columns={'return_decimal':'benchmark_return'}),
    on='month_end',validate='many_to_one')
counts = paired.groupby(['series_id','class_id']).month_end.nunique()
eligible_keys = counts[counts.eq(len(EXPECTED_MONTHS))].reset_index()[['series_id','class_id']]
balanced_returns = paired.merge(eligible_keys,on=['series_id','class_id'],validate='many_to_one')
assert not balanced_returns.duplicated(['series_id','class_id','month_end']).any()

benchmark_cagr = 100*(np.prod(1+benchmark.sort_values('month_end').return_decimal)**(12/len(EXPECTED_MONTHS))-1)
metric_rows = []
for (sid,cid), g in balanced_returns.groupby(['series_id','class_id']):
    g = g.sort_values('month_end'); x = g.return_decimal; excess = x-g.benchmark_return
    wealth = (1+x).cumprod(); drawdown = wealth/wealth.cummax().clip(lower=1)-1
    fit = sm.OLS(x.to_numpy(), sm.add_constant(g.benchmark_return.to_numpy())).fit()
    metric_rows.append({'series_id':sid,'class_id':cid,'months':len(g),
        'cagr_pct':100*(wealth.iloc[-1]**(12/len(g))-1),
        'annualized_volatility_pct':100*x.std(ddof=1)*np.sqrt(12),
        'annualized_tracking_error_pct':100*excess.std(ddof=1)*np.sqrt(12),
        'max_month_end_drawdown_pct':100*drawdown.min(),
        'proxy_beta':fit.params[1],'proxy_r_squared':fit.rsquared})
class_metrics = pd.DataFrame(metric_rows).merge(META,on='series_id',validate='many_to_one')
save_table(class_metrics, 'common_window_class_metrics')
fund_metrics = class_metrics.groupby(['series_id','fund_name','style'],as_index=False).agg(
    classes=('class_id','nunique'), median_class_te=('annualized_tracking_error_pct','median'),
    min_class_te=('annualized_tracking_error_pct','min'),max_class_te=('annualized_tracking_error_pct','max'),
    median_class_cagr=('cagr_pct','median'), min_class_cagr=('cagr_pct','min'),max_class_cagr=('cagr_pct','max'),
    median_class_beta=('proxy_beta','median'))
class_month_ranges = balanced_returns.groupby(['series_id','month_end']).return_decimal.agg(
    lambda s:100*(s.max()-s.min())).rename('monthly_class_range_pp').reset_index()
class_consistency = class_month_ranges.groupby('series_id',as_index=False).agg(
    median_monthly_class_range_pp=('monthly_class_range_pp','median'),
    max_monthly_class_range_pp=('monthly_class_range_pp','max'))
fund_metrics = fund_metrics.merge(class_consistency,on='series_id',validate='one_to_one')
fund_metrics['class_cagr_range_pp'] = fund_metrics.max_class_cagr-fund_metrics.min_class_cagr
# A diagnostic, not a correction: exclude the entire flagged fund from the return scatter.
fund_metrics['return_convention_review'] = fund_metrics.median_monthly_class_range_pp.gt(.5) | fund_metrics.class_cagr_range_pp.gt(3)
class_metrics = class_metrics.merge(fund_metrics[['series_id','return_convention_review']],on='series_id',validate='many_to_one')
save_table(class_metrics, 'common_window_class_metrics')
save_table(fund_metrics, 'common_window_fund_metric_ranges')
save_table(fund_metrics[fund_metrics.return_convention_review], 'class_return_convention_review')
display(fund_metrics.sort_values('median_class_te').head(12).round(3))
note(f'The common window retains {len(class_metrics)} classes across {fund_metrics.series_id.nunique()} primary funds. '
     f'SPAB CAGR is {benchmark_cagr:.2f}% over the same window. Fund summaries are medians/ranges of separately computed class statistics, '
     'not returns on a fabricated average share class. Fees and class histories still matter; no verified reference class is selected.')
display(fund_metrics.loc[fund_metrics.return_convention_review,
    ['fund_name','classes','min_class_cagr','max_class_cagr','median_monthly_class_range_pp']].round(3))
note(f'{fund_metrics.return_convention_review.sum()} funds trigger a class-consistency review: median within-month class return range above 0.5 percentage points '
     'or a class CAGR range above 3 percentage points per year. All class results remain saved. The whole flagged fund is omitted from the return-comparison chart; '
     'we do not select a better-performing class. Possible explanations include return/reporting conventions, class-specific characteristics or data issues; inspect the original filings. '
     'Passing this diagnostic does not independently validate returns, and single-class funds cannot receive a within-fund cross-check.')
''')
code('''
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
screened_fund_metrics = fund_metrics[~fund_metrics.return_convention_review].copy()
plot = screened_fund_metrics.sort_values('median_class_te').head(12).iloc[::-1]
axes[0].barh(plot.fund_name.str.replace(' Fund','',regex=False),plot.median_class_te)
axes[0].set(title='Common-window tracking error',xlabel='Median class annualized tracking error (%)')
axes[1].scatter(screened_fund_metrics.median_class_te,screened_fund_metrics.median_class_cagr,s=45,alpha=.7)
axes[1].axhline(benchmark_cagr,color='#df8751',ls='--',label='SPAB CAGR')
axes[1].set(title='Return versus benchmark deviation',xlabel='Median class tracking error (%)',ylabel='Median class CAGR (%)')
axes[1].legend(frameon=False)
fig.tight_layout(); save_chart('05_common_window_tracking_error',fig)
note('Low tracking error means returns were close to the proxy; it does not mean low absolute bond risk. '
     f'{len(screened_fund_metrics)} funds pass the stated class-dispersion screen. Higher tracking error does not establish either skill or poor management. '
     'These are ex-post descriptive screens in the supplied survivor sample.')
''')
md('''
## 7. A closer look at Vanguard Core Bond returns and drawdown

Both observed classes are plotted separately rather than guessing which class should represent the fund. The reference line is an investable Aggregate proxy, not the official index return.
''')
code('''
CASE = 'S000053068'
case_returns = balanced_returns[balanced_returns.series_id.eq(CASE)].copy()
fig, axes = plt.subplots(2,1,figsize=(11,7),sharex=True)
for cid,g in case_returns.groupby('class_id'):
    g=g.sort_values('month_end'); w=np.r_[1.0,(1+g.return_decimal).cumprod().to_numpy()]
    dates=pd.DatetimeIndex([START-pd.offsets.MonthEnd(1),*g.month_end])
    dd=w/np.maximum.accumulate(w)-1
    axes[0].plot(dates,w,label=f'Class {cid}',lw=2)
    axes[1].plot(dates,100*dd,label=f'Class {cid}',lw=2)
b=benchmark.sort_values('month_end'); bw=np.r_[1.0,(1+b.return_decimal).cumprod().to_numpy()]
bd=pd.DatetimeIndex([START-pd.offsets.MonthEnd(1),*b.month_end])
axes[0].plot(bd,bw,label='SPAB proxy',ls='--',color='#555555')
axes[1].plot(bd,100*(bw/np.maximum.accumulate(bw)-1),label='SPAB proxy',ls='--',color='#555555')
axes[0].set(title='Vanguard Core Bond: two classes and the common proxy',ylabel='Growth of 1, monthly observations')
axes[1].set(ylabel='Month-end drawdown (%)',xlabel='Common window: 2021–2025')
for ax in axes:ax.legend(frameon=False,fontsize=8);ax.grid(alpha=.15)
fig.tight_layout();save_chart('06_case_returns_and_drawdown',fig)
display(class_metrics[class_metrics.series_id.eq(CASE)].drop(columns=['group','manager']).round(3))
''')
md('''
## 8. A one-factor regression: co-movement with the Aggregate proxy

For each Vanguard Core Bond class, estimate `class return = intercept + beta × SPAB return + residual`. Standard errors use monthly HAC/Newey-West with three lags. This is **not** Qiang's rates/credit hedging regression: SPAB bundles both risks, and we do not yet have independent rate and credit factor returns.

The intercept is reported as a descriptive annualized arithmetic intercept, not manager alpha. A high R² is co-movement, not evidence that the holdings or economic risks are identical.
''')
code('''
regression_rows=[]
fig,ax=plt.subplots(figsize=(8,5))
for cid,g in case_returns.groupby('class_id'):
    g=g.sort_values('month_end')
    fit=sm.OLS(g.return_decimal.to_numpy(),sm.add_constant(g.benchmark_return.to_numpy())).fit(
        cov_type='HAC',cov_kwds={'maxlags':3})
    ci=fit.conf_int()
    regression_rows.append({'class_id':cid,'months':len(g),'beta':fit.params[1],
        'beta_95ci_low':ci[1,0],'beta_95ci_high':ci[1,1],
        'annualized_arithmetic_intercept_pct':1200*fit.params[0],
        'intercept_95ci_low_pct':1200*ci[0,0],'intercept_95ci_high_pct':1200*ci[0,1],
        'r_squared':fit.rsquared})
    ax.scatter(100*g.benchmark_return,100*g.return_decimal,alpha=.45,s=25,label=f'Class {cid}')
grid=np.linspace(100*benchmark.return_decimal.min(),100*benchmark.return_decimal.max(),100)
ax.plot(grid,grid,color='gray',ls='--',label='Equal return line')
ax.set(title='Monthly class returns versus SPAB',xlabel='SPAB monthly return (%)',ylabel='Class monthly return (%)')
ax.legend(frameon=False,fontsize=8);save_chart('07_proxy_regression_scatter',fig)
regression_results=save_table(pd.DataFrame(regression_rows),'case_proxy_regressions_hac')
display(regression_results.round(4))
note('HAC intervals address some serial dependence in regression errors; they do not solve omitted factors, proxy differences, class selection or survivorship. '
     'This is a descriptive exposure model with 60 observations per class, not a causal or out-of-sample result.')
''')
md('''
## 9. Layer 1: active sector allocation

The prior sponsor analysis assigns every position to one sector or `Other / unresolved`, normalizes reported holdings plus separately reported cash, then subtracts a same-report-month Aggregate proxy. Corporate IG/HY are combined pending ratings; TIPS/TBA identification and the study EM list need review.

This heatmap uses one actual month with at least 15 complete fund/proxy pairs, rather than combining each fund's latest date into an apparently synchronized cross-section.
''')
code('''
active_columns=[c for c in positions if c.startswith('active_sector_pp__')]
sector_names=[c.removeprefix('active_sector_pp__') for c in active_columns]
complete=positions[positions.sector_pair_complete].copy()
assert complete[active_columns].sum(axis=1).abs().max()<1e-8
month_counts=complete.groupby('report_month').series_id.nunique()
eligible_months=month_counts[month_counts.ge(15)]
assert len(eligible_months)>0
COHORT_MONTH=eligible_months.index.max()
cohort=complete[complete.report_month.eq(COHORT_MONTH)].sort_values('active_sector_pp__US Treasury (nominal)')
selected_sectors=['US Treasury (nominal)','Agency MBS','Non-agency MBS / CMBS','ABS / CLO',
    'Corporate debt (ratings pending)','Emerging markets (fixed country list)','Cash / short-term / repo','Other / unresolved']
labels=['Treasury','Agency MBS','Non-agency MBS','ABS / CLO','Corporate*','EM*','Cash/repo','Other*']
heat=cohort[['active_sector_pp__'+s for s in selected_sectors]].to_numpy()
fig,ax=plt.subplots(figsize=(12,max(5,len(cohort)*.25)))
bound=max(10,np.nanpercentile(np.abs(heat),95))
im=ax.imshow(heat,aspect='auto',cmap='RdBu',vmin=-bound,vmax=bound)
ax.set_yticks(range(len(cohort)),cohort.fund_name,fontsize=8)
ax.set_xticks(range(len(labels)),labels,rotation=30,ha='right')
ax.set_title(f'Active sector weights: {COHORT_MONTH.date()} | {len(cohort)} funds\\nColors capped at ±{bound:.1f} pp; exact values remain in the data')
fig.colorbar(im,ax=ax,label='Fund minus same-month proxy (percentage points)')
fig.tight_layout();save_chart('08_same_month_sector_heatmap',fig)
display(save_table(cohort[['series_id','fund_name','report_date','benchmark_proxy','benchmark_report_date','sector_reallocation_pct']], 'sector_cohort_dates'))
note(f'Across all dates, {len(complete):,} complete-input pairs cover {complete.series_id.nunique()} primary funds. '
     'The heatmap shows only the named month. Stars mark classification-dependent categories. Each full active-sector row sums to zero; '
     'half the sum of absolute active weights is sector-level reallocation, not security-level active share.')
''')
md('''
## 10. Layer 2: reported rate signs and the curve

We preserve source signs. Opposite signs across fund families are a data-convention warning, not evidence that half the industry is economically short duration. The curve example below compares two negative-sign filings in the sponsor's March 2026 case; even agreement of signs does not independently verify the convention.
''')
code('''
signs=primary.assign(sign=np.select([primary.usd_rate_sensitivity_years_signed.gt(0),
    primary.usd_rate_sensitivity_years_signed.lt(0)],['Positive','Negative'],default='Missing / zero'))
sign_table=signs.groupby(['manager','sign']).size().unstack(fill_value=0).reindex(columns=['Positive','Negative','Missing / zero'],fill_value=0)
fig,axes=plt.subplots(1,2,figsize=(14,10))
sign_table.plot.barh(stacked=True,ax=axes[0],color=['#168b83','#815fa5','#cccccc'])
axes[0].set(title='Filed USD sensitivity signs by manager',xlabel='Snapshot count',ylabel='');axes[0].tick_params(axis='y',labelsize=7)
tenors=pd.read_csv(RESULTS / 'rate_tenor_positions.csv',parse_dates=['report_month'])
case_tenor=tenors[tenors.series_id.eq(CASE)&tenors.report_month.eq('2026-03-31')].iloc[0]
T=['3MON','1YR','5YR','10YR','30YR'];x=np.arange(5)
axes[1].bar(x-.18,[case_tenor[t] for t in T],.36,label='Vanguard Core Bond')
axes[1].bar(x+.18,[case_tenor[t+'_benchmark'] for t in T],.36,label='SPAB proxy')
axes[1].set_xticks(x,T,rotation=30)
axes[1].set(title='March 2026 USD tenor sensitivities',ylabel='Reported signed years')
axes[1].legend(frameon=False);axes[1].axhline(0,color='gray',lw=.6)
fig.tight_layout();save_chart('09_rate_signs_and_curve',fig)
save_table(sign_table.reset_index(),'risk_sign_counts')
note(f'{primary.usd_rate_sensitivity_years_signed.abs().gt(10).sum()} primary snapshots exceed the absolute 10-year diagnostic; '
     'they are retained in source data. No cross-family economic-duration or credit-risk ranking is produced. '
     'Reported totals already include derivatives, and missing risk buckets are not zero.')
''')
md('''
## 11. Exploratory relationship: flow pressure and allocation changes

Do large investor flows coincide with larger changes in allocations? For consecutive three-month, complete sector snapshots, define an **allocation-shift measure** as half the sum of absolute changes in normalized sector weights. This is not trading turnover: prices, cash flows and mortgage rolls can change weights without discretionary trades.

We compare the measure with the absolute interval net flow / beginning assets. Both variables are demeaned within fund to reduce persistent cross-fund differences. The Spearman correlation is descriptive. A fund-cluster bootstrap gives a sensitivity interval while retaining each sampled fund's observations together; it does not establish causality or remove common-time shocks.
''')
code('''
sector_changes=positions.sort_values(['series_id','report_month']).copy()
sector_changes['months_since_previous']=sector_changes.groupby('series_id').report_month.transform(lambda s:(s.dt.year*12+s.dt.month).diff())
prior=sector_changes.groupby('series_id')[sector_names].shift()
prior_complete=sector_changes.groupby('series_id').sector_complete.shift().eq(True)
eligible_change=sector_changes.sector_complete & prior_complete & sector_changes.months_since_previous.eq(3)
sector_changes['allocation_shift_pp']=(.5*(sector_changes[sector_names]-prior).abs().sum(axis=1,min_count=len(sector_names))).where(eligible_change)
relation=sector_changes[['series_id','fund_name','report_date','allocation_shift_pp']].merge(
    valid_flows[['series_id','report_date','interval_net_flow_pct']],on=['series_id','report_date'],validate='one_to_one').dropna()
relation['absolute_flow_pct']=relation.interval_net_flow_pct.abs()
# A transparent scale screen; the excluded intervals remain in a separate file.
scale_ok=relation.absolute_flow_pct.le(100)
save_table(relation[~scale_ok],'excluded_flow_scale_intervals')
relation=relation[scale_ok].copy()
for col in ['absolute_flow_pct','allocation_shift_pp']:
    relation[col+'_within']=relation[col]-relation.groupby('series_id')[col].transform('mean')
xcol,ycol='absolute_flow_pct_within','allocation_shift_pp_within'
rho=relation[xcol].corr(relation[ycol],method='spearman')
rng=np.random.default_rng(20261026)
fund_blocks={sid:g[[xcol,ycol]].to_numpy() for sid,g in relation.groupby('series_id')}
ids=list(fund_blocks);boot=[]
for _ in range(500):
    sampled=rng.choice(ids,len(ids),replace=True)
    z=np.concatenate([fund_blocks[sid] for sid in sampled])
    boot.append(pd.Series(z[:,0]).corr(pd.Series(z[:,1]),method='spearman'))
rho_interval=np.nanpercentile(boot,[2.5,97.5])
fig,ax=plt.subplots(figsize=(9,5))
ax.scatter(relation[xcol],relation[ycol],s=18,alpha=.25)
ax.axhline(0,color='gray',lw=.6);ax.axvline(0,color='gray',lw=.6)
ax.set(title='Flow scale and sector-weight changes: within-fund association',
    xlabel='Absolute interval flow (% of beginning assets), fund-demeaned',
    ylabel='Sector allocation shift (pp), fund-demeaned')
save_chart('10_flows_and_allocation_changes',fig)
save_table(relation,'flow_allocation_association_panel')
association_summary=pd.DataFrame([{'intervals':len(relation),'funds':relation.series_id.nunique(),
    'spearman_rho':rho,'fund_bootstrap_95_low':rho_interval[0],'fund_bootstrap_95_high':rho_interval[1],
    'bootstrap_draws':500,'excluded_above_100pct_flow':int((~scale_ok).sum())}])
display(save_table(association_summary,'flow_allocation_association_summary').round(4))
note(f'The within-fund rank correlation is {rho:.3f}; the fund-block bootstrap interval is '
     f'[{rho_interval[0]:.3f}, {rho_interval[1]:.3f}] across {relation.series_id.nunique()} funds. '
     'Treat this as a hypothesis-generating association. Endogenous flows, return-driven weight changes, classification issues and market-wide shocks remain.')
''')
md('''
## 12. Sponsor case: notional, currency and swap direction

Qiang emphasizes that swap risk depends on direction and maturity, not notional alone. The March 2026 filing has 65 non-FX swap-table records, of which 56 are classified as interest-rate swaps. This table also contains non-USD interest-rate swaps despite its name.

The existing approximation includes only explicit USD fixed/floating interest-rate swaps. It uses remaining maturity and a flat-coupon annuity estimate, lacks an observed discount curve/schedule, and must not be added to the derivative-inclusive reported fund risk.
''')
code('''
display(pd.read_csv(RESULTS / 'vcobx_irs_notionals_by_currency.csv'))
swap_summary=pd.read_csv(RESULTS / 'vcobx_usd_swap_summary.csv').set_index('direction').reindex(['Pay fixed','Receive fixed'])
fig,axes=plt.subplots(1,2,figsize=(11,4.5))
colors=['#df8751','#168b83']
axes[0].bar(swap_summary.index,swap_summary.gross_usd_notional/1e9,color=colors)
axes[0].set(title='Eligible USD IRS gross notionals',ylabel='USD billions')
axes[1].bar(swap_summary.index,swap_summary.approximation_years,color=colors)
axes[1].set(title='Rough USD-only duration contributions',ylabel='Flat-coupon annuity approximation (years)')
axes[1].axhline(0,color='gray',lw=.6)
fig.tight_layout();save_chart('11_swap_currency_and_risk',fig)
ir=swap_audit.is_interest_rate_swap
note(f'The audit identifies {ir.sum()} interest-rate swaps: '
     f'{swap_audit.loc[ir,"direction"].eq("Pay fixed").sum()} pay-fixed and '
     f'{swap_audit.loc[ir,"direction"].eq("Receive fixed").sum()} receive-fixed across currencies. '
     f'The eligible USD-only approximation sums to {swap_summary.approximation_years.sum():+.3f} years. '
     "It does not validate the email's approximate +0.6-year all-swap estimate: JPY/HUF notionals require currency treatment, and the model omits non-USD swaps and full valuation details.")
''')
md('''
## 13. Findings, diagnostics and next analyses

The following summary is generated from this notebook's results, so it updates on a rerun. Read the earlier methods before quoting a number.
''')
code('''
case_positions=positions[positions.series_id.eq(CASE)&positions.report_month.eq('2026-03-31')].iloc[0]
case_common=class_metrics[class_metrics.series_id.eq(CASE)]
summary = {
    'primary_funds':len(primary_ids), 'primary_snapshots':len(primary),
    'complete_sector_pairs':len(complete),'funds_with_complete_sector_pairs':complete.series_id.nunique(),
    'common_window':f'{START.date()} to {END.date()}',
    'common_window_funds':fund_metrics.series_id.nunique(),'common_window_classes':len(class_metrics),
    'funds_flagged_class_convention_review':int(fund_metrics.return_convention_review.sum()),
    'funds_in_screened_return_scatter':len(screened_fund_metrics),
    'spab_common_window_cagr_pct':benchmark_cagr,
    'vcobx_common_window_te_min_pct':case_common.annualized_tracking_error_pct.min(),
    'vcobx_common_window_te_max_pct':case_common.annualized_tracking_error_pct.max(),
    'vcobx_march2026_active_treasury_pp':case_positions['active_sector_pp__US Treasury (nominal)'],
    'vcobx_march2026_active_signed_rate_years':case_positions.active_usd_rate_signed_years,
    'flow_allocation_spearman_rho':rho,
    'flow_allocation_fund_bootstrap_95':[float(v) for v in rho_interval],
    'excluded_flow_overlap_rows':int(flow_overlap.sum()),
    'excluded_return_overlap_rows':int(return_overlap.sum()),
}
(EDA/'key_findings.json').write_text(json.dumps(summary,indent=2,default=lambda x:x.item()),encoding='utf-8')
findings = f"""# EDA findings

- The primary panel has {len(primary):,} snapshots across {len(primary_ids)} funds; fiscal calendars and fund starts make it unbalanced.
- The complete 2021–2025 return window retains {len(class_metrics)} share classes across {fund_metrics.series_id.nunique()} primary funds. SPAB CAGR is {benchmark_cagr:.2f}%.
- {fund_metrics.return_convention_review.sum()} funds trigger the within-fund class-return consistency screen; all original metrics remain saved, but these funds are excluded as a whole from the return-comparison chart pending review. {len(screened_fund_metrics)} funds remain in that chart. This avoids choosing classes based on better performance.
- Vanguard Core Bond's two class tracking errors over that same window range from {case_common.annualized_tracking_error_pct.min():.3f}% to {case_common.annualized_tracking_error_pct.max():.3f}% annualized.
- In March 2026, Vanguard Core Bond's nominal Treasury active weight is {case_positions['active_sector_pp__US Treasury (nominal)']:+.2f} percentage points, while its reported USD rate sensitivity differs by {case_positions.active_usd_rate_signed_years:+.3f} signed years. Allocation and total rate sensitivity answer different questions.
- Flow scale and allocation shift have within-fund Spearman correlation {rho:.3f}, with a fund-block bootstrap interval [{rho_interval[0]:.3f}, {rho_interval[1]:.3f}]. This is a contemporaneous descriptive association, not evidence that flows cause trading.
- The swap case reproduces 56 IRS records and separates currency units. The USD-only approximation does not validate an all-currency risk claim.

## Remaining work

Verify reference-class and external security mappings; independently validate sector classifications and filer risk signs; obtain ratings, fees, official benchmark analytics and independent rates/credit factors; expand the historical universe; and verify point-in-time public availability before predictive work. Do not interpret this EDA as a manager-skill ranking.
"""
(EDA/'FINDINGS.md').write_text(findings,encoding='utf-8')
display(Markdown(findings))
print('Saved charts:', len(list((EDA/'charts').glob('*.png'))))
print('Tables and reproducible findings:', EDA)
''')
md('''
### Reproduce and extend

- Change `START`/`END` in section 6 to study another **complete common return window**.
- Change `CASE` and the explicitly dated case queries together for another fund.
- Inspect `analysis/eda/tables/` before adding a regression; retain fund/class keys and missingness.
- `analysis/DATA_GUIDE.md` documents the source data; `analysis/FIELD_CATALOGUE.md` lists every database field.
- Rerun all cells after changing assumptions. Figures and tables are replaced; source data is not modified.

For execution from a terminal in this project: `python -m nbconvert --to notebook --execute Capstone_EDA.ipynb --inplace --ExecutePreprocessor.timeout=600`.
''')

import ast
for i, cell in enumerate(cells):
    if cell.cell_type == 'code':
        ast.parse(cell.source, filename=f'notebook cell {i}')
nb = nbf.v4.new_notebook(cells=cells)
nb.metadata = {
    'kernelspec': {'display_name':'Python 3','language':'python','name':'python3'},
    'language_info': {'name':'python','version':'3.13'},
}
path = ROOT / 'Capstone_EDA.ipynb'
nbf.write(nb,path)
print(f'Created {path}: {len(cells)} cells, {sum(c.cell_type == "code" for c in cells)} code cells')
