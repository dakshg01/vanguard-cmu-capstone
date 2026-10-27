# Guide to the capstone dataset

This describes the production database and analysis outputs currently in this folder. Counts refer to selected latest filings unless stated otherwise. Source: the supplied SEC N-PORT ZIPs, the extraction's schema dictionary and quality report, and direct inspection of `output/nport.sqlite`.

For every database field, including less frequently used derivative and audit fields, see [FIELD_CATALOGUE.md](FIELD_CATALOGUE.md). The machine-readable equivalent is [database_schema.json](database_schema.json). SEC source types and descriptions by archive are in `../output/csv/schema_dictionary.csv`.

## 1. What the dataset represents

It is a historical panel of portfolio disclosures for a supplied list of 59 SEC fund series. It contains portfolio positions, reported risk sensitivities, share-class monthly returns, fund-level monthly flows, derivative positions and monthly derivative P&L. It also retains original filed strings and provenance.

It is not the complete mutual-fund industry, a daily pricing database, an official index-constituent history, or a survivorship-free research universe. The raw retained data is filtered to the supplied series IDs and their related positions; the complete industry-wide originals remain inside the ZIPs.

| Fund group | Funds | Selected snapshots | Intended use |
|---|---:|---:|---|
| PRIMARY | 49 | 1,333 | Main active core/core-plus peer comparison |
| BENCHMARK | 4 | 111 | Index-fund holdings/risk proxies |
| ADJACENT | 4 | 111 | Related strategies, separate from core peers |
| CHECK | 2 | 22 | Active ETF cross-checks; avoid double-counting related strategies |
| Total | 59 | 1,577 | All selected latest fund/report-date observations |

### Size

| Data | Rows / count | Interpretation |
|---|---:|---|
| Supplied archives | 28 | 2019 Q4 through 2026 Q3 |
| Distinct filing accessions retained | 1,597 | Originals and amendments retained |
| Latest fund/report-date snapshots | 1,577 | One selected accession per fund and exact report date |
| Latest holdings | 4,234,703 | Reported positions, not unique permanent securities |
| Latest share-class monthly return rows | 26,748 | Includes overlapping source reports flagged for review |
| Distinct reported fund/class pairs | 343 | Between 1 and 21 classes per fund; median 5 |
| Latest monthly fund-flow rows | 4,731 | Three monthly slots per selected filing |
| Latest long risk rows | 62,840 | Risk type/currency/bucket/tenor/shock observations |
| Latest risk-total rows | 12,568 | Five-tenor aggregates by risk dimension; totals may be missing |
| Latest monthly derivative-P&L rows | 109,359 | Month x asset category x instrument kind from selected filings |

There are 71 physical SQLite tables and 51 views, representing 30 retained SEC source-table families plus derived tables and diagnostics. These are not 122 independent datasets: much of the structure preserves raw, typed and selected versions of the same records.

## 2. Exact date coverage

| Date dimension | First | Last | Meaning |
|---|---|---|---|
| ZIP release labels | 2019 Q4 | 2026 Q3 | Archive batches, not portfolio measurement dates |
| Holdings / fund-risk report dates | 2019-09-30 | 2026-07-31 | When the portfolio was measured |
| Monthly return dates | 2019-07-31 | 2026-07-31 | 85 distinct calendar months across the dataset |
| Monthly flow dates | 2019-07-31 | 2026-07-31 | Same overall monthly range |
| Monthly derivative-P&L dates | 2019-07-31 | 2026-07-31 | Monthly P&L unpacked from quarterly reports |
| Filing dates | 2019-11-19 | 2026-09-29 | Submission dates of retained filings |
| Assumed availability, selected snapshots | 2019-11-30 | 2026-09-30 | Research proxy, not verified release timestamps |

Returns and flows begin before holdings because a September 2019 report contains July, August and September monthly slots. Slot 1 is the oldest month; slot 3 is the report month.

Coverage is unbalanced. Funds have 6 to 30 selected report snapshots, with a median of 28. Vanguard Core-Plus first appears here in December 2021; the two check ETFs in December 2023; Vanguard STAR Core-Plus in April 2025. These are first observations in this dataset, not independently verified inception dates.

The last observed holdings dates are May 31, 2026 for 12 funds, June 30 for 34 funds and July 31 for 13 funds. The benchmark group ends in June 2026. There are no holdings observations through September 2026 merely because the final ZIP is labeled 2026 Q3.

Use `output/csv/coverage.csv` for each fund's individual start/end dates and report count. `coverage_gaps.csv` has no report-date gaps greater than 110 days; this does not prove a complete or balanced monthly return panel.

### Dates you must keep separate

- `report_date`: exact measurement date.
- `report_month`: that report date aligned to calendar month-end; useful for last-business-day versus calendar-end matching. Check uniqueness before using it as a key.
- `month_end`: the economic month of a return, flow or P&L observation.
- `filing_date`: when the filing was submitted.
- `available_date_assumed`: `max(filing_date, report_date + 60 calendar days) + 1 calendar day` under the current default. Availability overrides were not supplied.
- `fiscal_year_end`: fiscal-calendar information; it is not the current holdings date.

All `*_latest` views are retrospective. For a historical decision, filter eligible filing versions before selecting the latest report/amendment. `research.snapshots_asof()` implements that ordering, but its availability dates remain proxies unless independently verified.

## 3. Where to find the data

| Location | Role |
|---|---|
| `universe.csv` | Original supplied fund list and group assignments |
| `data/zips/` | Intact SEC archives; ultimate originals |
| `output/nport.sqlite` | Authoritative extracted working database, about 8.95 GB |
| `output/csv/` | Smaller exported tables and extraction-review files |
| `output/quality_report.json` | Extraction quality counts |
| `output/run_manifest.json` | Archive hashes, software/settings and universe hash |
| `Start_here.ipynb` | Notebook examples using the database |
| `analysis/results/` | Our derived classifications, benchmark comparisons, plots and report |

Holdings are kept in SQLite rather than a huge Excel sheet. `holdings_classification_audit.parquet` is a compact per-position classification audit, not a replacement for the complete holdings source.

## 4. The main analytical tables and fields

### Fund identity: `universe`

One row per fund series:

- Identity: `series_id`, `cik`, `fund_name`, `manager`.
- Research grouping: `group`, `role`, `style`.
- Fund classification: `ncen_is_index`, `ncen_is_etf`.
- Reference notes: `nport_var_reference_index`, `prospectus_benchmark_to_verify`, `note`.

Use `series_id` as the fund identity. Names can change; one registrant CIK can contain several funds. The N-PORT designated risk index is not a verified performance benchmark mapping. The prospectus benchmark column remains a field to verify.

### Fund snapshot: `fund_quarter`

One row per fund/exact report date. Despite the name, this is a fiscal reporting snapshot rather than an imposed synchronized calendar quarter.

- Traceability: `source_archive_id`, `accession_number`.
- Identity: `series_id`, `cik`, `series_name`, `fund_name`, `manager`, `universe_group`, `role`, `style`.
- Timing: `report_date`, `report_month`, `fiscal_year_end`, `filing_date`, `filing_lag_days`, `available_date_assumed`, `availability_basis`.
- Filing status: `submission_type`, `is_last_filing`, `archive_copy_rank`, `amendment_rank`.
- Balance sheet: `total_assets`, `total_liabilities`, `net_assets`.
- Additional funding/cash information: `delayed_delivery_payables_usd`, `cash_not_in_holdings_usd`.
- Reported risk: `usd_rate_sensitivity_years_signed`, `ig_spread_sensitivity_years_signed`, `hy_spread_sensitivity_years_signed`.

Uses: fund size histories, funding/payable diagnostics, risk histories and a compact fund-snapshot regression panel after dates, conventions and other inputs are resolved. This table does not contain expense ratios or a single chosen class return.

### Positions: `holdings_enriched_latest`

One row per reported position in a selected filing. Keeps derivatives as well as cash securities.

- Parent metadata: `series_id`, `report_date`, `report_month`, `filing_date`, `available_date_assumed`, `availability_basis`, `ACCESSION_NUMBER`.
- Position/audit keys: `source_archive_id`, `source_row`, `HOLDING_ID`.
- Issuer/security description: `ISSUER_NAME`, `ISSUER_LEI`, `ISSUER_TITLE`, `ISSUER_CUSIP`.
- Quantity/value/currency: `BALANCE`, `UNIT`, `OTHER_UNIT_DESC`, `CURRENCY_CODE`, `CURRENCY_VALUE`, `EXCHANGE_RATE`.
- Filed weights: `PERCENTAGE`, `weight_fraction`.
- Classification: `ASSET_CAT`, `OTHER_ASSET`, `ISSUER_TYPE`, `OTHER_ISSUER`, `INVESTMENT_COUNTRY`.
- Position properties: `PAYOFF_PROFILE`, `IS_RESTRICTED_SECURITY`, `FAIR_VALUE_LEVEL`, `DERIVATIVE_CAT`, `is_reported_derivative`.
- Debt enrichment: `MATURITY_DATE`, `COUPON_TYPE`, `coupon_pct`, `coupon_decimal`, `IS_DEFAULT`, `years_to_maturity`.

Keep reported value, currency and exchange-rate fields together; do not assume any notional or quantity is already a USD amount. `PERCENTAGE` is in percent: 2.5 means 2.5%; `weight_fraction` is 0.025. Neither is extraction-normalized. Filed holdings totals need not equal 100%.

Debt enrichment uses only an unambiguous debt row, preventing one-to-many joins from multiplying holdings. Missing maturity/coupon information is normal for non-debt positions and is not automatically a data error.

Uses: sector allocation, geography, security concentration, maturity/coupon profiles, issuer exposure, derivatives' market-value footprint and inputs for external security matching. A repeated CUSIP can represent several valid positions; do not deduplicate positions by CUSIP.

### Security details: `identifiers_latest`, `debt_security_latest`

Identifiers include `HOLDING_ID`, `IDENTIFIERS_ID`, `IDENTIFIER_ISIN`, `IDENTIFIER_TICKER`, `OTHER_IDENTIFIER`, `OTHER_IDENTIFIER_DESC`, plus archive/filing/fund/report metadata.

Debt records include `MATURITY_DATE`, `COUPON_TYPE`, `ANNUALIZED_RATE`, `IS_DEFAULT`, `ARE_ANY_INTEREST_PAYMENT`, `IS_ANY_PORTION_INTEREST_PAID`, `IS_CONVTIBLE_MANDATORY`, `IS_CONVTIBLE_CONTINGENT`, plus parent keys.

Uses: join Bloomberg or other bond information via a reviewed security crosswalk; refine maturity, coupon, default and convertible analyses. Holdings tickers are not automatically fund/share-class tickers. Identifiers can be missing, placeholders, reference-instrument identifiers or non-unique.

### Share-class performance: `monthly_returns_latest`

Fields: `source_archive_id`, `accession_number`, `series_id`, `report_date`, `month_end`, `return_row_id`, `class_id`, `month_slot`, `return_pct`, `return_decimal`, `filing_date`, `available_date_assumed`, `availability_basis`.

`return_pct = 1.25` and `return_decimal = 0.0125` both mean a 1.25% monthly return. `return_row_id` is a source surrogate, not an external class ID.

Uses: cumulative class returns, volatility, drawdown, tracking error, excess returns versus a matched proxy, rolling performance and later persistence tests. Choose a verified reference class before creating one fund/month return series. Never average all class returns as a shortcut.

### Investor money and non-derivative P&L: `monthly_flows_latest`

Fields: fund/filing/date metadata, `month_slot`, `sales_usd`, `reinvestment_usd`, `redemptions_usd`, `net_external_flow_usd`, `net_flow_including_reinvestment_usd`, `nonderivative_realized_pnl_usd`, `nonderivative_unrealized_change_usd`.

- External net flow = sales - redemptions.
- Flow including reinvestment = sales + reinvestment - redemptions.
- These are dollar amounts, not return-adjusted flow rates or percentages.

Uses: subscriptions/redemptions, investor flow persistence, flows around poor performance and whether repositioning coincides with investor money. A clean monthly flow percentage needs a defensible monthly asset denominator; do not silently use quarterly assets as if they were monthly assets. Do not sum fund flows after copying them onto every share class.

### Rate and credit risk: `risk_normalized_latest`, `risk_totals_latest`

Long-table fields: parent/date metadata, `risk_row_id`, `risk_type`, `currency`, `credit_bucket`, `tenor`, `shock_bp`, `value_change_usd`, `source_column`, `net_assets`, `reported_sensitivity_years`.

- `risk_type`: `interest_rate` or `credit_spread`.
- `tenor`: `3MON`, `1YR`, `5YR`, `10YR`, `30YR`.
- `shock_bp`: 1 or 100; retain these as different shocks.
- `credit_bucket`: `INVEST` or `NONINVEST` for reported credit-spread risk; not a rating attached to an individual bond.
- `currency`: the relevant rate curve's currency. Non-USD currency sensitivity is not the same as net FX exposure.
- For DV01 and positive net assets, signed normalized years = filed dollar sensitivity x 10,000 / net assets.

Risk totals include `tenor_rows`, `distinct_tenors`, `nonmissing_tenors`, `total_value_change_usd`, `total_reported_sensitivity_years`. A total requires all five distinct nonmissing tenor buckets. A DV100 total is retained without applying the DV01-years formula.

Uses: reported total rate risk, tenor/curve positioning, currency-specific rate risk and reported IG/HY spread-risk histories. The reports already include derivative effects: do not add estimated swap risk to these totals. Filed signs differ across filers, and credit-risk coverage conventions differ across families; raw active differences are not automatically comparable economic durations.

### Derivatives and their P&L

| Table | Important additional fields | Downstream use |
|---|---|---|
| `nonforeign_exchange_swap_latest` | `TERMINATION_DATE`, `NOTIONAL_AMOUNT`, `CURRENCY_CODE`, payment/receipt currencies, `FIXED_OR_FLOATING_PAYMENT/RECEIPT`, fixed rates, floating indices/spreads, upfront amounts, unrealized appreciation | Separate IRS from credit/other swaps; inspect maturity, direction, currencies and implementation |
| `fut_fwd_nonforeigncur_contract_latest` | `PAYOFF_PROFILE`, `EXPIRATION_DATE`, `NOTIONAL_AMOUNT`, `CURRENCY_CODE`, `UNREALIZED_APPRECIATION` | Futures/forward implementation and curve-position diagnostics |
| `fwd_foreigncur_contract_swap_latest` | Sold and purchased currency amounts/codes, `SETTLEMENT_DATE`, `UNREALIZED_APPRECIATION` | Currency hedging implementation; needs careful leg/currency matching |
| `swaption_option_warnt_deriv_latest` | Put/call, written/purchased, shares/principal, currency, exercise price, expiry, unrealized appreciation | Optionality and volatility-position descriptions; notional is not delta risk |
| `derivative_pnl_latest` | `month_end`, `asset_category`, `instrument_kind`, `realized_pnl_usd`, `unrealized_change_usd` | Monthly P&L decomposition by derivative type/category |

Other retained tables cover counterparties, reference instruments, index baskets/components, floating-rate reset tenors, other derivatives and their notionals. Their complete names and fields are in the field catalogue.

`nonforeign_exchange_swap` does not mean every row is an interest-rate swap. Classify using holding asset/derivative codes and leg/reference information. Notionals stay in their specified currency; do not add JPY, HUF, EUR and USD values together as dollars. Swaption risk is not proportional to notional. Mortgage TBAs can appear as ordinary mortgage positions without an SEC derivative flag.

### Additional financing and operational data

Retained SEC families include repurchase agreements, their collateral and counterparties; securities lending; borrowers/aggregate borrowing; explanatory notes; and fund/registrant/submission reference data. These support implementation and financing checks, subject to each table's public coverage. `fund_var_info_latest_raw` contains a designated regulatory risk-reference index, not a verified performance-benchmark mapping.

## 5. Raw, typed, all and latest layers

- `raw_*`: selected original SEC strings; preserve exact numeric text and source traceability.
- `t_*`: the same selected source rows with metadata-defined dates/numbers converted to usable types. Monetary analytics use floating-point REAL; use original text plus Decimal for exact reconciliation.
- `filings_all`: filing records by source archive, retaining all original/amended accessions and any archive copies.
- `filings`: one canonical copy per accession. It still contains different original/amended accessions for a report date.
- `filings_latest`: latest filing version per series/exact report date.
- `*_all` analytical tables: transformed returns/flows/risk/P&L across retained filing versions.
- Analytical views without `_latest`, such as `monthly_returns` and `risk`: restrict to canonical accession copies while retaining report versions.
- `*_latest`: records linked to selected latest filings. This does not automatically resolve overlapping economic months across different report dates.

Audit tables: `archives`, `inventory`, `schema_dictionary`, `ingest_issues`, `settings`. Review views: `coverage`, `coverage_gaps`, `holdings_checks`, `risk_review_flags`.

## 6. Correct join keys

| Task | Key / rule |
|---|---|
| Join fund metadata | `series_id` |
| Identify selected snapshot | `series_id + report_date` |
| Use month-aligned snapshots | `series_id + report_month`, after checking for multiple exact dates |
| Connect source filing tables | `source_archive_id + ACCESSION_NUMBER` (derived tables use lowercase `accession_number`) |
| Connect holding child tables | `source_archive_id + HOLDING_ID` |
| Build class performance panel | `series_id + class_id + month_end`, after resolving overlapping reports |
| Build fund flow panel | `series_id + month_end`, after resolving overlapping reports |
| Match external securities | Reviewed CUSIP/ISIN crosswalk with date/cardinality checks |

Multiple identifiers, reference instruments or counterparties can belong to one position. Aggregate or keep those children separately before joining several of them to holdings, otherwise you can multiply position values. Do not merge quarterly holdings onto each of three monthly returns and then sum holdings as if those were three independent portfolios.

## 7. Quality and missingness you should know

The extraction finished with `REVIEW_REQUIRED`, not an extraction failure:

- 20 amended/repeated fund-report-date groups.
- 27 overlapping class/month groups and 6 overlapping flow/month groups in latest views.
- 13 all-group snapshot sensitivities above the absolute 10-year USD diagnostic; 12 of these are PRIMARY snapshots. They remain in the data.
- 38 monthly return rows have missing reported returns.
- Among latest holdings, 3,034 positions have missing reported weights and 2,448 have a NULL CUSIP. Non-NULL placeholder or invalid CUSIPs are additional mapping concerns, not included in that NULL count.
- Of 1,577 fund snapshots, 73 have missing cash-outside-holdings values. The three main normalized risk totals each have 20 missing observations.
- Zero numeric/date parse issues, unmatched funds, CIK mismatches, cross-archive accession duplicates, balance-sheet discrepancies, selected snapshots without holdings, missing expected tables, ambiguous debt rows or unknown metadata types under the implemented checks.

Zero parse errors means the recorded strings converted successfully, not that every economic value or identifier is correct. NULL is not zero. The raw table dictionary's empty optional fields and optional tables need separate coverage checks.

## 8. Derived analysis already available

These fields are our analysis outputs, not additional SEC observations:

| Output | What it adds |
|---|---|
| `results/positioning_panel.csv` | Primary snapshots, matched proxy identity/date, normalized sector weights, active sector percentage points, sector-level reallocation, signed risk differences, tenor differences and comparability flags |
| `results/sector_weights.csv` | All fund groups; reported weight sums, separately reported cash, normalization denominator and completeness flags |
| `results/holdings_classification_audit.parquet` | Archive/holding keys, assigned sector, classification rule, filed weight, missingness, TBA-description candidate and currency for each position |
| `results/classification_rule_totals.csv` | Auditable allocation/count totals by rule and snapshot |
| `results/rate_tenor_positions.csv` | Five signed USD tenor exposures and matched proxy differences; long-minus-short curve diagnostic |
| `results/non_us_rate_sensitivities.csv` | Reported complete currency-specific non-USD rate totals; not net FX |
| `results/share_class_tracking_error.csv` | Class-specific monthly tracking error against SPAB, dates, paired-month count and 36-month eligibility |
| `results/fund_class_tracking_error_ranges.csv` | Range/median of class-specific tracking errors; not an averaged fund-return series |
| `results/vcobx_swap_audit.csv` | March 2026 Vanguard Core Bond swap classification, currency, direction, remaining maturity and USD approximation eligibility |
| `results/factor_delivery_status.csv` | Available versus missing components of Qiang's eight-factor framework |

The positioning panel has all 1,333 primary snapshots. Same-month unadjusted-Aggregate proxies exist for 1,002, and complete sector-input pairs for 882 snapshots across 37 funds. Unmatched/incomplete active sectors stay missing. Completeness describes input coverage, not independently verified classification accuracy.

The fixed proxy preference is SPAB, then AGG, then SCHZ, using the same report month only. Vanguard Total Bond Market is a separate float-adjusted diagnostic. Corporate IG/HY weights remain combined pending ratings. TIPS and TBA descriptions are provisional, and the EM country list is a disclosed study convention. The panel preserves raw signed risk differences and marks economic sign/cross-family credit comparability as unverified.

## 9. What you can do downstream

| Research question | Inputs available now | What to watch / add |
|---|---|---|
| How do core/core-plus funds allocate relative to the Aggregate? | Holdings, classification rules, same-month index-fund snapshots | Review unresolved sectors/cash denominator; index funds are sampled proxies |
| Do similar sector allocations hide different rate/curve risks? | Sector weights, USD totals and five tenor sensitivities | Verify filer signs; keep derivative-inclusive reported risk intact |
| How are exposures implemented? | Holdings, swaps, futures, options, FX forwards and counterparties | Distinguish instrument types, currencies, maturity and optionality |
| Which funds behave most like an index? | Monthly class returns and index-fund returns | Resolve duplicate months, select/verify classes, use common windows for formal comparisons |
| Do exposures or sector tilts persist? | Repeated fiscal snapshots and derived active-position panel | Match dates, control for changing sample and sign conventions |
| Are redemptions associated with repositioning? | Monthly flows and sequential snapshots | Quarterly observation limits; distinguish association from causation and cash-flow effects |
| Are concentration, geography or maturity profiles changing? | Holdings IDs, issuer names/LEIs, countries, weights, debt maturity/coupon | Review identifier mappings, derivative treatment and ambiguous/missing fields |
| How much monthly P&L comes from different derivative types? | Derivative realized/unrealized P&L by month/category/instrument | Not a full factor attribution or a security-return history |
| Can active positions explain future performance? | Historical versions, availability proxy, returns and positions | Verified availability, class/benchmark choices, fees, controls, out-of-sample design and survivor expansion needed |

### Inputs not present for the full sponsor analysis

- Bond-level credit ratings and rating history: needed for reliable IG/HY/AAA/AA/A/BBB weights and credit-quality factor 7.
- Official monthly Aggregate analytics/constituents, key-rate duration, sector weights and sub-index returns: current data supplies index-fund proxies only.
- Treasury/Federal Reserve yield curves and independent credit-factor series: needed for factor 8 rolling rates/credit return regressions and stronger swap valuation.
- Prospectus management fees, expense ratios and dated fee histories.
- A verified reference-share-class selection and dated replacements; fund tickers/external IDs need a reviewed crosswalk.
- A complete historical eligible universe, including omitted funds that closed or shrank.
- Verified historical public-dissemination timestamps.
- Daily bond prices, bond total returns, transaction records, derivative valuation schedules and a complete trade-based turnover measure.

Do not infer fund turnover or deliberate trading from raw changes in holdings alone: investor flows, mortgage TBA rolls, price movements, security maturities and identifier changes can all change positions.

## 10. Small starting queries

```python
import sqlite3
import pandas as pd

con = sqlite3.connect('file:output/nport.sqlite?mode=ro', uri=True)

# Compact snapshot panel for the intended peer group.
funds = pd.read_sql_query(
    "SELECT * FROM fund_quarter WHERE universe_group='PRIMARY'", con
)

# Query one fund/report date rather than loading 4.23 million holdings at once.
holdings = pd.read_sql_query(
    '''SELECT * FROM holdings_enriched_latest
       WHERE series_id=? AND report_date=?''',
    con, params=('S000053068', '2026-03-31')
)

# Keep class IDs: this is not one observation per fund/month.
returns = pd.read_sql_query(
    'SELECT series_id,class_id,month_end,return_decimal FROM monthly_returns_latest',
    con
)
con.close()

# Already-derived sector/risk comparison panel.
positions = pd.read_csv('analysis/results/positioning_panel.csv')
```

Use SQL filters/chunks for large holdings or child tables. Retain group labels, exact report dates, source keys, missingness and benchmark identity through downstream analysis.
