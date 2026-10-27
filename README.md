# Vanguard / CMU capstone: N-PORT data pipeline

## Team quick start: view or rerun the analysis

Start with **[Capstone_EDA.ipynb](Capstone_EDA.ipynb)**. It includes saved outputs, 11 figures, common-window share-class performance, flow analysis, sector/risk comparisons, regressions, and interpretation. GitHub can render its saved notebook outputs.

- [EDA findings](analysis/eda/FINDINGS.md)
- [Data guide](analysis/DATA_GUIDE.md) and [complete field catalogue](analysis/FIELD_CATALOGUE.md)
- [Sponsor analysis conclusions](analysis/results/conclusions.md)
- [EDA browser copy](analysis/eda/Capstone_EDA.html) and [sponsor report](analysis/results/report.html): download the HTML file and open it locally; GitHub displays HTML source rather than hosting it as a website.

The CSV inputs, small derived tables, graphs, and reports are included. **The EDA notebook runs from those CSVs without the large SQLite database or SEC ZIP downloads.** Clone the repository, open a terminal in its root, and run:

```bash
python -m pip install -r requirements_analysis.txt
python -m jupyterlab Capstone_EDA.ipynb
```

The repository excludes SEC ZIPs, the roughly 9 GB SQLite database, the roughly 105 MB per-holding classification Parquet audit, local dependencies, and scratch files. To rebuild the full extraction or per-holding audit, follow the original pipeline instructions below, download the archives into `data/zips/`, run `python run.py`, then `python analyze_sponsor.py`.

Read the limitations before interpreting returns or risk: the universe is a supplied starting list, risk signs and class mappings require verification, and the notebook flags inconsistent class-return conventions. The sponsor email is included for project context; this repository is intended for private team collaboration.

This package implements **source 1 in your task image** for the attached 59-fund universe: 49 PRIMARY, 4 BENCHMARK, 4 ADJACENT and 2 CHECK funds. Because benchmark funds use exactly the same archives, they are included too. Their labels remain separate. Use PRIMARY for the main peer group.

It collects holdings, debt details, identifiers, reported fund risk, monthly share-class returns, monthly flows, derivative P&L, and the full derivative/related tables. No paid API, SEC account, API key, database server or Bloomberg connection is required.

## 1. Quick start

1. Extract this package to a folder on your computer. Keep its files together.
2. Install **Python 3.10 or newer** if needed. Anaconda Python also works. The extractor uses only Python's standard library, so it needs no pip installation.
3. Open the [official SEC download page](https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets).
4. Download **one ZIP first**, preferably 2019 Q4. Put the intact file in `data/zips/`. Do not unzip it.
5. On Windows, double-click `run_windows.bat`. Alternatively, open a terminal in this package folder and run:

```bash
python run.py
```

6. Read `output/quality_report.json` and `output/csv/coverage.csv`. `REVIEW_REQUIRED` is a prompt to inspect the named issues; it is not necessarily a failed extraction. A one-quarter test will legitimately lack some funds.
7. Add the remaining quarterly ZIPs, starting at 2019 Q4 and continuing through your intended collection cutoff. Run the same command again.

At preparation time, the SEC page listed releases through **2026 Q3**. You can collect all those releases, then choose the study's report-date cutoff downstream. A report for your final sample month can arrive in a later ZIP; amendments can arrive much later. Do not stop downloads solely at the ZIP quarter matching the last desired holdings date.

If your downloaded files are elsewhere:

```bash
python run.py --zip-dir "D:/SEC/NPORT" --output "D:/capstone/nport_output"
```

Mac/Linux: use `python3` if that is your Python command. The `.bat` file uses the Windows `py` launcher; if you use Anaconda without that launcher, run `python run.py` in Anaconda Prompt instead.

## 2. What you receive

The authoritative working file is **`output/nport.sqlite`**. It is a normal local SQLite database that pandas can query directly. Small analysis tables also export automatically to CSV. Holdings remain in SQLite to avoid repeatedly writing huge spreadsheets.

| Table/view | Observation / purpose |
|---|---|
| `universe` | One row per SEC series; your original groups, roles, names and benchmark notes |
| `filings_all` | One filing per source archive, retaining amendments and archive copies |
| `filings` | One copy per accession number, with all distinct original/amended accessions |
| `filings_latest` | Latest filing per series and exact report date; retrospective |
| `fund_quarter` | One latest fund snapshot per exact report date, fund characteristics, net assets, delayed-delivery payables, cash, and signed USD/IG/HY sensitivities normalized to years |
| `holdings_latest` | One reported position per selected filing; keeps derivatives and original classification codes |
| `holdings_enriched_latest` | Same positions plus unambiguous debt maturity, coupon and years to maturity; derivative indicator is the SEC flag, not a TBA detector |
| `identifiers_latest` | Long table of ISIN, ticker and other identifiers attached to positions |
| `debt_security_latest` | All debt records, including any ambiguous duplicate debt records |
| `monthly_returns_latest` | Share class × month, with percent and decimal returns |
| `monthly_flows_latest` | Fund × month, independent of share class |
| `risk_normalized_latest` | Currency/credit bucket × tenor × shock size, with raw dollar sensitivity and DV01 normalized by net assets |
| `risk_totals_latest` | Sum across all five tenor buckets, only when all five are present and nonmissing |
| `derivative_pnl_latest` | Fund × month × asset category × derivative instrument kind |
| `nonforeign_exchange_swap_latest`, `fut_fwd_nonforeigncur_contract_latest`, etc. | Original long derivative tables, linked to selected filings |
| `fund_var_info_latest_raw` | Designated risk-reference index when present; **not a performance benchmark mapping** |
| `raw_*` | Selected original SEC table values retained as text for audit and exact numeric precision |
| `t_*` | Same selected rows, dates converted to ISO and metadata-defined numeric fields converted to REAL |
| `coverage`, `coverage_gaps`, `holdings_checks`, `risk_review_flags` | Coverage, potential reporting gaps and data-quality diagnostics |
| `archives`, `inventory`, `schema_dictionary`, `ingest_issues` | ZIP hashes, counts, actual schemas and conversion problems |

Each `raw_*` and `t_*` row has `source_archive_id` (ZIP SHA-256) and `source_row` (the parsed source record number). The actual ZIPs remain the ultimate original files. Keep them.

To export a large table explicitly:

```bash
python run.py --export-table holdings_enriched_latest
python run.py --export-table identifiers_latest
python run.py --export-table nonforeign_exchange_swap_latest
```

Use the same `--output` argument if you used a non-default output directory. Exports are written to that directory's `csv/` subfolder. Excel may truncate large exports at its row limit; use pandas/SQL instead.

## 3. The keys you should give your teammates

**Fund identity:** `series_id`, not fund name and not CIK. One registrant CIK can cover many funds. CIK is retained as a zero-padded string and checked against your universe.

**Fund snapshot:** `series_id + report_date` in the latest views. `report_month` converts a last-business-day report date to calendar month-end for monthly data joins, while retaining the exact original date. Check for multiple distinct report dates in the same month before using `report_month` as a key.

**Share-class performance/fees:** `series_id + class_id + month_end`. N-PORT's return ID is a source-row surrogate, not an external share-class identifier. Do not use a holdings ticker as a fund ticker.

**Raw parent-child relationships:** `(source_archive_id, ACCESSION_NUMBER)` for filing tables and `(source_archive_id, HOLDING_ID)` for holding children. Never join on `HOLDING_ID` across archives alone. Its numeric-looking value is stored as text, so large surrogate IDs retain their precision.

**External bond data:** CUSIP/ISIN with an explicitly reviewed security mapping. `HOLDING_ID` identifies a reported position, not a permanent bond identifier. A fund can have several positions in the same security. Do not deduplicate positions by CUSIP. Some identifiers are missing, placeholders or relate to derivative reference instruments. Multiple identifier rows are preserved without choosing one arbitrarily.

**Later sources:** fee tables need class IDs plus effective/public dates; FRED and Treasury curves need date alignment; Bloomberg needs a separate fund/class/security crosswalk. The notebook creates a blank crosswalk template. Validate join cardinality instead of assuming names or tickers provide unique matches.

## 4. Research choices already handled

- The attached CSV is included unchanged as `universe.csv`. Every matching historical filing in the supplied ZIPs is retained even if the fund subsequently closes. Names may change; matching remains by series ID. CIK is a diagnostic, not a restrictive filter.
- Monthly slot 1 is the oldest of the three months: for a November report, slots 1/2/3 mean September/October/November. Dates are based on the report month, not the filing or ZIP month.
- `return_pct = 1.25` means 1.25%; `return_decimal = 0.0125`. `weight_fraction = PERCENTAGE / 100`. Original raw strings remain available. Coupon rate is treated similarly.
- `net_external_flow_usd = sales - redemptions`. The separate `net_flow_including_reinvestment_usd = sales + reinvestment - redemptions` makes the convention visible. Neither is a flow percentage or an inferred return-adjusted asset change.
- Fund risk is already derivative-inclusive. Do not add estimated derivative risk to the reported totals; that would double count. USD rate sensitivity and non-USD curve sensitivities stay separate.
- DV01-derived years use **reported dollar sensitivity × 10,000 / positive net assets**, following the sponsor's convention, preserving the reported sign. There is no absolute-value operation or automatic sign reversal. DV100 is retained as a separate 100-bp shock and is not converted with the DV01 formula. Risk totals are missing if any of the five tenor buckets is missing.
- The normalized outputs are named `usd_rate_sensitivity_years_signed`, `ig_spread_sensitivity_years_signed` and `hy_spread_sensitivity_years_signed`. They preserve the sign of the filed value change and are **not automatically positive economic duration**. Real test filings contain both signs. If a value denotes the signed price change for a +1 bp yield move, conventional positive duration is its negative after normalization; if a filer reports a DV01 magnitude, that reversal would be wrong. Validate and document the convention before comparing signed exposures across filers. Never fix this with an unconditional absolute value.
- USD sensitivity magnitude above 10 years is flagged for review, not deleted. The threshold is a transparent starter diagnostic for this universe, not an investment constraint. Cross-family credit spread sensitivities also need coverage/convention checks before ranking, as Qiang emphasized. A value inside the bounds does not establish the sign convention or economic accuracy.
- All derivative subtypes, counterparties, payment/receipt legs, reference instruments, reset tenors, basket components, notionals and currency details are retained when publicly present. Some SEC risk fields are not public. Empty fields do not establish zero exposure.
- Holdings enrichment cannot multiply rows through one-to-many identifiers or derivative children. Debt enrichment uses only one unambiguous debt row per position; duplicate debt rows remain in the separate source table and are flagged.
- Sector labels, TBA heuristics, swap direction, rating buckets and exposure estimates are deliberately left for an explicit analysis layer. All inputs needed from N-PORT are retained. The SEC derivative flag alone does not identify mortgage TBAs, and not every swap is an interest-rate swap.
- Reported holdings weights are preserved. They are not normalized during extraction. For the later sector allocation layer, define the cash/derivative/payable treatment, normalize the intended sector denominator, and retain the unnormalized values for audit.

## 5. Timing and amendments: read before running a backtest

`report_date` says when the portfolio was measured; `filing_date` says when the filing was submitted. The bulk dataset does not provide a verified public-dissemination timestamp for every record. Do not label filing date alone as a guaranteed historical availability date.

The pipeline therefore creates an explicitly named **`available_date_assumed`**:

```
max(filing_date, report_date + 60 calendar days) + 1 calendar day
```

This is an adjustable research proxy, **not a verified point-in-time data history or a universal statement of SEC rules**. The extra day avoids treating an unknown intraday publication time as available before a same-day decision. If a trading calendar matters, map it to your next permitted trading decision time separately.

You can change the assumed lag with `--availability-lag-days`, or supply actual verified public dates:

```bash
python run.py --availability-overrides availability_overrides.csv
```

The override CSV needs `accession_number,public_date,source`. Use a source citation for the actual public release date; do not rename the filing date. The pipeline adds one calendar day and preserves the exact override input used. Overrides do not magically make other filings verified.

All `*_latest` views choose the latest filing by filing date, then accession number for a deterministic same-day tie break. They are intended for retrospective research. For historical decisions, filter eligible versions **before** choosing a report/amendment. `research.snapshots_asof()` implements that order and returns snapshot age. It never substitutes a later amendment into an earlier decision date. Availability remains only as accurate as the supplied dates/proxy.

When an accession appears in multiple archives, the canonical copy comes from the lexicographically latest ZIP filename, then a deterministic hash tie break. Such cases are explicitly flagged. This rule avoids double counting but does not establish which conflicting archive copy is authoritative: inspect the original filing if copies differ. Use the SEC's original filenames.

Monthly reports that overlap remain visible and are flagged rather than silently collapsed. The reference-class helper refuses an ambiguous fund-month panel.

## 6. Jupyter workflow

Optional packages:

```bash
python -m pip install -r requirements_optional.txt
jupyter lab
```

Open `Start_here.ipynb`. The notebook does not download anything or rerun extraction unless you explicitly execute the subprocess cell. It loads the small tables first, shows class availability, demonstrates selecting a reference class, and queries holdings in bounded batches. It also shows optional Parquet export.

Minimal example:

```python
import sqlite3
import pandas as pd
con = sqlite3.connect('output/nport.sqlite')
funds = pd.read_sql_query("SELECT * FROM fund_quarter WHERE universe_group='PRIMARY'", con)
risk = pd.read_sql_query('SELECT * FROM risk_normalized_latest', con)
returns = pd.read_sql_query('SELECT * FROM monthly_returns_latest', con)
```

All class returns are delivered. Before turning returns into one fund-month row, choose a reference share class from a verified fund/class crosswalk. Do not average all class returns or sum flows after joining to every class. The helper requires an explicit class choice, rejects overlaps, and does not switch classes silently. Historical class replacements need a dated crosswalk beyond this helper's one-class-per-series interface.

## 7. Coverage and scope limits

This extraction covers the **supplied list**, not a proven survivorship-free research universe. Qiang explicitly describes the list as a starting snapshot. Preserving historical filings of these 59 funds does not recover omitted dead funds. Historical universe expansion/classification is a later task; after adding series IDs, use a new output directory and reprocess the ZIPs so earlier archives are not accidentally skipped.

Some funds entered after 2019. A missing observation can mean a newer fund, an unprovided ZIP, a delayed filing, a merger, a changed identifier or an actual data problem. The program labels no-match funds and gaps over 110 days but does not invent inception/closure dates, forward-fill holdings, create zero returns, or declare missing data to be zero.

Qiang's **October 6 instruction supersedes the earlier benchmark suggestion**: Bloomberg U.S. Aggregate is the common research benchmark for PRIMARY funds; each fund's own performance benchmark is separately recorded. The N-PORT designated index is a regulatory risk reference and is not used as that mapping. Index funds are holdings proxies, not exact index constituents; fiscal report dates may not coincide. Do not claim active individual-bond weights from a sampled proxy or use a future benchmark snapshot to fill a missing month.

This package does not collect prospectus fees, FRED, Federal Reserve curves or Bloomberg ratings/analytics. It prepares the identifiers and dates needed to combine those later. It does not yet produce the final sector/factor attribution or regressions.

## 8. Operations, memory and reproducibility

- Only one ZIP is processed at a time, directly from the compressed file; there is no giant extraction directory.
- TSVs are read sequentially, with batches of 5,000 retained rows. Only selected holding IDs and small filing metadata stay in memory. Time is driven primarily by scanning the industry-wide holdings and identifier tables.
- Each ZIP commits atomically. If interrupted, rerun: completed ZIP hashes are skipped and the unfinished archive starts again. A changed file under the same filename fails explicitly; use a fresh output directory to ingest a replacement archive release.
- The output database intentionally retains both raw strings and typed values, so allow disk space for those plus all downloaded ZIPs. At the SEC's listed sizes, the complete historical download is many gigabytes. Do not assume it fits in RAM or in Excel.
- Adding future tables with accession/holding keys preserves them automatically. An unknown relationship stops extraction. Added columns are retained; `schema_dictionary.csv` records the metadata for each release. A ZIP without SEC metadata is rejected rather than guessing data types.
- Ordinary numeric analytics use SQLite REAL (floating point); exact filed numeric text is in `raw_*`. Use Decimal on those original strings if exact high-precision monetary reconciliation is necessary.
- CSV outputs are replaced on rerun; they are generated outputs, not a place for manual annotations. Keep your crosswalks/analysis separately.
- Use `run_manifest.json` to record archive hashes, universe hash, software version and availability settings. Never move just the database while a run is active; let it finish so its WAL is checkpointed.
- Tests: `python -m unittest discover -s tests -v`.

## 9. Sources and verification

- User-provided `capstone_email.pdf`: Qiang's September 30, October 6 and October 23 guidance; the later instructions above take precedence where they revise earlier guidance.
- User-provided `capstone_fund_universe.csv` and task screenshot.
- [SEC Form N-PORT data releases](https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets).
- [SEC table definitions](https://www.sec.gov/files/nport_readme.pdf), plus the `nport_metadata.json` bundled within each actual quarterly ZIP.

See `VALIDATION.md` for the actual live-archive test results. `validation_sample/` contains small outputs from the test archives only. They are examples from real filings, **not the full historical dataset**, and are separate from your production `output/` folder.
