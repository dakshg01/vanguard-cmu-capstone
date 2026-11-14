# Caroline's first-pass analysis (record of work)

Added as a record, separate from the main analysis notebook and deck. Nothing here replaces or edits any other file in the repo.
Written 11-14 Nov 2026 for the Nov 12 sponsor call. Windows: 2019-07 to 2022-12 and 2023-01 to 2026-06. Benchmark proxy: SPAB (then AGG, SCHZ). Four return-flagged funds (series IDs in `csv/excluded_return_flag_funds.csv`) are excluded from return tests, so persistence uses 43 funds.

## excel/
| File | What it holds |
|---|---|
| persistence_first_pass.xlsx | Excess-return persistence across the two windows; winner vs laggard features |
| alpha_persistence.xlsx | Alpha persistence, Fed curve and Baa spread factors |
| alpha_persistence_etf.xlsx | Alpha persistence, 5 ETF factors (over cash and over SPAB), 2020-dropped versions |
| strategic_tactical.xlsx | Strategic vs tactical P&L from filed exposures, and its persistence |
| risk_mix_provisional.xlsx | Risk mix by bucket (government/agency, corporate, securitized, EM), by fund, style and family |
| family_styles.xlsx | Fund-family consistency (ICC) and Ward clusters |
| derivative_pnl_layer.xlsx | Derivative P&L by type, by fund, style and family (P&L only, not risk) |

Every workbook has a `notes` sheet with definitions and exclusions.

## code/
Python scripts that produced the workbooks. They read the repo's CSV exports and Anna's cleaned data; paths are set by command-line arguments, so adjust them to your clone before running. They were developed in a separate environment, so run them on a copy first.
`pull_prospectus_strategy.py` needs the `SEC_UA` environment variable set to a real name and email.

## Known limits
Small sample (43 to 49 funds), no multiple-testing correction, current-snapshot universe (not survivorship-free), corporates not yet split into IG/HY (needs Bloomberg ratings), attribution excludes carry and security selection.
