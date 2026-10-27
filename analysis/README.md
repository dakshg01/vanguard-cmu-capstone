# Sponsor analysis

Run from the project folder:

```powershell
python analyze_sponsor.py
```

The script reads `output/nport.sqlite` and the small extraction CSVs without modifying them. It needs pandas, numpy, matplotlib and pyarrow. It streams holdings in 100,000-row batches. It makes no network calls and does not need PDF-reading packages to rerun.

Open `results/report.html` in a browser. It is self-contained, with embedded charts. Read `results/conclusions.md` for the text-only version.

Main outputs:

- `results/positioning_panel.csv`: one row per primary fund/report month, with dates, normalized sectors, active weights, filed signed risk differences and comparability flags. Multiple exact report dates in one fund/month are excluded and saved separately rather than silently collapsed. This is a fiscal snapshot table, not a synchronized calendar-quarter panel.
- `results/sector_weights.csv`: all groups, raw denominators, separately reported cash, missingness and normalized allocations.
- `results/holdings_classification_audit.parquet`: a rule and sector for each retained position, keyed by archive and holding ID.
- `results/classification_rule_totals.csv`: classification rule aggregates for every fund snapshot.
- `results/classification_review_sample.csv`: up to 1,000 large unresolved/fallback position examples. This is a sample; use the Parquet file for the complete audit.
- `results/rate_tenor_positions.csv`: filed signed USD tenor exposures and matched proxy differences.
- `results/non_us_rate_sensitivities.csv` and `holdings_by_currency.csv`: separate rate and unhedged holdings-currency diagnostics; neither is net FX exposure.
- `results/share_class_tracking_error.csv`: every class's observed-window tracking error vs SPAB, with dates and the 36-month eligibility flag. No reference class is guessed.
- `results/vcobx_swap_audit.csv`: individually classified swaps for the sponsor's March 2026 Vanguard Core Bond case, with currency, leg direction and approximation eligibility.
- `results/factor_delivery_status.csv`: what is available for each of Qiang's eight factors and which inputs remain missing.
- `results/analysis_manifest.json`: analysis code and source hashes, benchmark policy and fixed study EM-country list.
- `results/charts/`: standalone PNG and editable SVG charts.

Source instructions are in `../email_capstone.pdf`, especially the October 6 email on pages 11-12 and the October 23 email on pages 14-17. `source_pages/` contains local renderings used to read the scanned email.

The report is a retrospective descriptive first pass. It preserves filed risk signs; it does not manufacture economic sign conventions, ratings, a verified class mapping, missing benchmark months or a survivorship-free universe. See the report's methods section before interpreting active risk or tracking error.
