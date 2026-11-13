# Bloomberg rates data (quarterly)

Government bond yields, interest-rate swap rates and bond futures for the US, Japan and Germany/Euro area, pulled from the Bloomberg Terminal Historical Price Table (`HP`) and cleaned from two exports:

- `Book1 (1).xlsx` (main source; one `HP` page per ticker, stacked in a single sheet).
- `Book1.xlsx` (earlier pull, one sheet per ticker). Used only for govt yields before 2020-06-30. On the 498 points the two files share, values are identical.

- **Frequency:** quarterly, quarter-end. Dates are the last business day of the quarter (e.g. `2019-03-29`).
- **Range:** the wide file covers 2018-12-31 to 2026-09-30 (32 quarter-ends). Coverage by group:

  | Group | From | To | Quarters |
  |---|---|---|---|
  | Govt yields (USGG, GJGB, GDBR) | 2018-12-31 | 2026-09-30 | 32 (USGG10YR: 30) |
  | USD swaps (USSW) | 2018-12-31 | 2023-06-30 | 19 |
  | EUR / JPY swaps (EUSA, JYSO) | 2018-12-31 | 2026-09-30 | 32 |
  | Futures (TU1, TY1, US1, JB1, RX1) | 2018-12-31 | 2026-09-30 | 32 |

  The only gaps inside a range are USGG10YR on 2019-03-29 and 2019-06-28 (no data in the Bloomberg pull). Blank cells outside a range mean no data was pulled for that date.
- **Units:** yields and swap rates are in **percent** (4.25 = 4.25%). Futures are **prices** in points per 100 of face value.

## Files

| File | Layout |
|---|---|
| `bbg_rates_quarterly_wide.csv` | One row per date, one column per field (`px_last` only). Blank = no data. |
| `bbg_rates_quarterly_long.csv` | One row per date × field, with metadata and both `px_last` and `px_bid`. |

### Columns in the long file

| Column | Meaning |
|---|---|
| `date` | Quarter-end date (YYYY-MM-DD) |
| `field` | Short name, also used as the column name in the wide file |
| `bbg_ticker` | Full Bloomberg ticker as pulled |
| `asset_class` | `govt_yield`, `swap_rate`, or `bond_future` |
| `market` | `US`, `JP`, `DE` (German Bund), `EU` (euro swaps) |
| `tenor` | Maturity of the yield/swap, or the underlying bond tenor of the future |
| `currency` | Currency of the instrument |
| `px_last` | Bloomberg `PX_LAST` (last price / closing mid yield) |
| `px_bid` | Bloomberg `PX_BID` |

## Fields

### Government bond yields (generic benchmark yields, %)

| Field | Bloomberg ticker | Description |
|---|---|---|
| USGG2YR / USGG10YR / USGG30YR | `USGG2YR Index` etc. | US Treasury generic 2Y / 10Y / 30Y yield |
| GJGB2 / GJGB10 / GJGB30 | `GJGB2 Index` etc. | Japan Government Bond 2Y / 10Y / 30Y yield (Bloomberg quotes these as *simple yield*) |
| GDBR2 / GDBR10 / GDBR30 | `GDBR2 Index` etc. | German Bund generic 2Y (Schatz) / 10Y / 30Y yield |

### Swap rates (par fixed rate, %)

| Field | Bloomberg ticker | Description |
|---|---|---|
| USSW2 / USSW10 / USSW30 | `USSW2 BGN Curncy` etc. | USD swap, semi-annual 30/360 fixed vs **3M USD LIBOR** (legacy; LIBOR ended 2023-06-30) |
| EUSA2 / EUSA10 / EUSA30 | `EUSA2 BGN Curncy` etc. | EUR swap, annual fixed vs **6M EURIBOR** |
| JYSO2 / JYSO10 / JYSO30 | `JYSO2 BGN Curncy` etc. | JPY OIS, fixed vs **TONA** (overnight) |

`BGN` = Bloomberg Generic composite pricing source.

### Bond futures (generic 1st contract, price)

| Field | Bloomberg ticker | Underlying |
|---|---|---|
| TU1 | `TU1 COMB Comdty` | CBOT 2Y US Treasury Note future |
| TY1 | `TY1 COMB Comdty` | CBOT 10Y US Treasury Note future |
| US1 | `US1 COMB Comdty` | CBOT US Treasury Bond (long bond) future |
| JB1 | `JB1 COMB Comdty` | OSE 10Y JGB future |
| RX1 | `RX1 Comdty` | Eurex Euro-Bund (10Y German) future |

`COMB` = combined pit + electronic session pricing. Generic "1" = front-month contract, rolled by Bloomberg's default rule.

## Cleaning notes

1. **US futures converted from 32nds.** Bloomberg shows US Treasury futures in 32nds, e.g. `107-20¾` = 107 + 20.75/32 = 107.6484; `+` = half a 32nd. These are converted to decimals.
2. **Bad bid removed.** `TU1` on 2022-12-30 had `px_bid` = 85-00 against `px_last` = 102-16; the bid is set to blank. `px_last` is kept.
3. **JYSO bid vs last.** For 2019–2020 the JYSO bid is about 5bp below last. This reflects wide bid/ask in a then-illiquid market and is kept as-is.
4. **Futures are unadjusted.** Generic contracts splice the front month without roll adjustment, so quarter-on-quarter price changes include roll gaps. Use yields or a roll-adjusted series for return calculations.
5. **Sanity check.** Yields were compared on the same quarter-end dates to free official series (FRED Treasury CMT, Japan MOF JGB rates, Bundesbank par yields). Median differences were within ±3bp. Larger gaps (up to ~17bp for German 2Y) come from Bloomberg generic benchmark bonds vs the official fitted curves, not from parsing errors.

## Known limitations / to-do

- USSW is LIBOR-based and has no data after mid-2023. For a current USD swap series use SOFR swaps (`USOSFR2 / USOSFR10 / USOSFR30 Curncy`, confirm on the terminal). LIBOR and SOFR swaps are different benchmarks, so do not splice them without adjusting for the basis.
- Slope factors (10Y−2Y, 30Y−10Y) are not stored. Compute them from the wide file.

## Reproduce

The raw Bloomberg exports are not committed. With them in hand:

```bash
python clean_bbg_rates.py "Book1 (1).xlsx" --backfill Book1.xlsx
```

This rewrites both CSVs in this folder. The script checks the layout of every HP page, verifies each ticker has one row per quarter in its stated range, and asserts that the backfill file agrees with the main file on all overlapping points. To add tickers, paste more HP pages in the same format and add the field to `INFO` in the script.
