# Production run results

Processed all 28 supplied SEC archives, 2019 Q4 through 2026 Q3, using the README defaults. No downloads or package installations were needed.

- All 59 funds observed.
- 1,577 latest fund/report-date snapshots, spanning 2019-09-30 through 2026-07-31.
- 4,234,703 latest holdings; 26,748 class/month returns; 4,731 fund/month flow observations.
- Main database: `nport.sqlite` (about 8.95 GB).
- Archive hashes and settings: `run_manifest.json`.
- Coverage: `csv/coverage.csv`. No report-date gaps greater than 110 days.

## Quality review

Extraction completed with `REVIEW_REQUIRED`. The flagged records are preserved:

| Finding | Count | Review file |
|---|---:|---|
| Amended/repeated series/report dates | 20 | `csv/review_amended_report_dates.csv` |
| Overlapping class/month groups | 27 | `csv/review_overlapping_class_months.csv` |
| Overlapping fund/month flow groups | 6 | `csv/review_overlapping_flow_months.csv` |
| Absolute signed USD sensitivity above 10 years | 13 | `csv/review_risk_magnitude_flags.csv` |

There were zero numeric/date parsing issues, unmatched funds, CIK mismatches, cross-archive accession duplicates, balance-sheet discrepancies, snapshots without holdings, missing expected tables, ambiguous debt rows, or unknown metadata types. See `quality_report.json` for the full checks.

Review overlapping months before building a single-row monthly panel. Risk signs remain as filed; the magnitude flags are diagnostics, not corrections. Reference-class selection and external identifier mapping still require verified research inputs. The availability assumption remains the README's unverified 60-day proxy; latest views are retrospective.

## Implementation and validation

Removed redundant filing-version joins in `run.py`'s latest analytical views and normalized-risk view to resolve a slow full-history risk-total export. The selected filing logic and output columns are preserved. All eight regression tests pass. The fund-quarter, normalized-risk, monthly-return and monthly-flow CSVs are byte-for-byte identical before and after this change; original hashes are saved in `pre_optimization_hashes.json`.

To rerun extraction: `python run.py`. Completed archive hashes are skipped.

All 11 code cells in `Start_here.ipynb` executed successfully against the production database. Saved results: `Start_here.executed.ipynb` in this output folder. The notebook also created the blank `external_id_crosswalk.csv` in the project root. Optional Parquet export and the verified reference-class mapping branch remain disabled, as configured by the notebook. Use the original notebook in the project root for subsequent execution so its relative paths resolve correctly.

To open the notebook UI if the Jupyter launcher is unavailable on PATH: `python -m jupyterlab Start_here.ipynb`.
