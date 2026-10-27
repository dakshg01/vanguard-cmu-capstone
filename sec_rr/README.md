# sec_rr_fees_panel.csv

Fund fees and portfolio turnover from SEC mutual fund prospectuses (data path 3), one row per fund per quarter, ready for modeling.

| | |
|---|---|
| Grain | one row per fund (`series_id`) per calendar quarter |
| Primary key | `series_id` + `quarter` (unique) |
| Funds | 59 (every `series_id` in `../universe.csv`) |
| Period | 2011Q1 – 2026Q2 (42 funds start in 2011Q1; later starts are fund launches) |
| Rows | 3,220 |
| Missing values | only `turnover` (125 rows, see below) |
| Units | all fee and turnover columns are decimals of net assets: `0.0035` = 0.35%, `1.31` = 131% |

To get fund names, style (Core / Core-Plus), group or manager, join `../universe.csv` on `series_id`.

## Columns

### Keys

| Column | Type | Description |
|---|---|---|
| `series_id` | string | SEC series ID of the fund, e.g. `S000009707` (PIMCO Total Return). Same ID used in N-PORT. |
| `quarter` | string | Calendar quarter, e.g. `2026Q2`. |
| `quarter_end` | date | Last day of the quarter, e.g. `2026-06-30`. |

### Fee breakdown of the fund's cheapest share class

A fund sells several share classes (retail A/C shares, institutional, R6, ...) that hold the same portfolio but charge different fees. These columns describe the **cheapest investable class**, which is normally the institutional one and the best proxy for what the manager charges to run the portfolio. Sales-driven fees such as 12b-1 are mostly excluded this way.

| Column | Description |
|---|---|
| `mgmt_fee` | Management (advisory) fee. |
| `other_exp` | Other operating expenses: custody, admin, transfer agency and similar. Some funds also include interest expense here (e.g. PIMCO Income 2019–2021). |
| `acquired_fund_exp` | Acquired fund fees and expenses: the cost of other funds the fund invests in. Almost always 0. |
| `gross_exp` | Total annual fund operating expenses before waivers. Equals `mgmt_fee + other_exp + acquired_fund_exp` (+ 12b-1, which is 0 for this class) up to rounding. |
| `fee_waiver` | Fee waiver or expense reimbursement by the manager. **Negative or 0.** |
| `net_exp` | Net expense ratio after waivers = `gross_exp + fee_waiver`. This is the expense ratio investors actually pay. |

### Across all share classes of the fund

| Column | Description |
|---|---|
| `net_exp_median` | Median net expense ratio across the fund's share classes. |
| `net_exp_max` | Highest net expense ratio across share classes (usually the retail C class). |
| `n_classes` | Number of share classes with a fee table in effect. |
| `share_classes_waived` | Fraction of share classes with a fee waiver (0–1). |

### Fund level

| Column | Description |
|---|---|
| `turnover` | Portfolio turnover rate for the fund's last completed fiscal year, as stated in the prospectus. `1.31` = 131%. Reported once per fund, not per class. |

## How the panel is built

**Source.** SEC [Mutual Fund Prospectus Risk/Return Summary data sets](https://www.sec.gov/data-research/sec-markets-data/mutual-fund-prospectus-riskreturn-summary-data-sets), quarterly files 2010Q4–2026Q2. These are the XBRL fee tables that funds file with their prospectuses (forms 485BPOS and 497). The SEC set has no PIMCO filings after mid-2024, so PIMCO's July 2025 and July 2026 prospectuses were parsed directly from EDGAR.

**Point in time, no look-ahead.** Each quarter uses the latest prospectus **filed** on or before the quarter end. Prospectuses are usually updated once a year, so a value is carried forward until the next filing, for at most 24 months. A quarter never sees a fee table that was not yet public.

**Backfill at the start.** The sample starts in 2011Q1. Share classes that already existed then, but whose first filing in the data is later in 2011, use that first 2011 fee table for the earlier 2011 quarters. Turnover is not backfilled, because it changes too much from year to year.

**Cleaning applied to the raw fee tables:**
- Missing waiver → 0 (no waiver line in the table means no waiver); missing net → gross + waiver.
- Missing other expenses → gross minus the other components.
- Positive waivers (a tagging convention in post-2024 filings) → flipped to negative.
- Duplicate filings of the same table on the same day → kept the 485BPOS.
- Share classes that a filer tagged under the wrong fund (15 cases, e.g. an equity fund's classes under Diamond Hill Core Bond in 2011) → dropped. A class's true fund is the one it appears under in most SEC filings.
- Fully waived internal classes (net 0%, used only by the manager's own funds-of-funds: T. Rowe Price New Income Z, Nuveen Core Bond W, Nuveen Core Plus Bond W, one Voya class) → excluded from every column, since outside investors cannot buy them.

## Things to know before modeling

- **`turnover` missing (125 rows).** Two cases: (1) 2011 quarters before a fund's first filing in the data, and (2) the first year or so after a fund launches, when its prospectus has no completed fiscal year yet (e.g. Vanguard Core-Plus 2021–22, Vanguard Core Bond ETF and Core-Plus Bond ETF 2023–24, Vanguard STAR Core-Plus 2025, Harbor Core Bond 2018).
- **Large gross fees with large waivers are real.** Small or new funds (e.g. Lord Abbett Core Plus 2016–2020, BNY Mellon Core Plus 2018–19) show `other_exp` up to 2% with an almost equal `fee_waiver`. `net_exp` stays normal. Use `net_exp` if you want what investors pay.
- **`mgmt_fee` = 0 for some Vanguard quarters.** Vanguard runs at cost, and in some years its prospectus puts the whole cost under other expenses.
- **Fees are sticky.** Most funds change fees rarely, so most quarter-over-quarter changes are 0. Expect little time variation within a fund. The variation is mainly across funds.
- **2026Q3 onward is not included yet.** SEC had not published the 2026Q3 data set when this was built.

## Rebuilding

From `sec_rr/`:

```bash
python3 pull_sec_rr.py      # download SEC quarterly files (cached in raw/), extract universe funds
python3 pull_pimco_gap.py   # parse PIMCO 2025+ prospectuses from EDGAR
python3 clean_sec_rr.py     # clean and build sec_rr_fees_panel.csv
```

Share-class-level detail and intermediate files are written to `intermediate/` (not committed, like `raw/`).
