# Validation performed

The package was run against complete official SEC bulk archives, not only mocked rows:

| SEC release | Matched filings | Matched series | Retained holdings |
|---|---:|---:|---:|
| 2019 Q4 | 43 | 43 | 97,368 |
| 2026 Q1 | 59 | 59 | 177,039 |
| Combined test | 102 | 59 distinct | 274,407 |

The combined test produced 1,656 share-class/month return rows, 306 fund/month flow rows, and 4,450 long risk rows. The 2026 Q1 archive also exercised FUND_VAR_INFO, which was absent in the 2019 archive.

Checks found zero numeric/date conversion issues, zero CIK mismatches, zero balance-sheet reconciliation discrepancies at the defined tolerance, zero missing holdings snapshots, zero ambiguous debt parent rows, and zero duplicate class-month or flow-month observations. All expected core tables were present. Every supplied fund was observed in the newer ZIP.

One observation exceeded the diagnostic 10-year USD sensitivity magnitude threshold: Neuberger Berman Core Bond (S000007835), report date 2026-01-31, signed normalized sensitivity approximately -10.153 years. It is retained and flagged, not corrected. Signs across actual filings vary, so normalized fields retain the source sign and require convention verification before economic interpretation. This is distinct from the known cross-family credit-spread coverage differences.

Eight automated regression tests passed: month order/units/leading zeros/large IDs/no identifier fanout; resumable archives plus amendments and historical eligibility; malformed numeric preservation; duplicate accession archives; changed-universe protection; missing metadata failure; transaction rollback on an unknown table relationship; and missing risk-tenor handling. Run them with `python -m unittest discover -s tests -v`.

All notebook code cells were executed against the combined real dataset. The optional Parquet branch and user-provided reference-class mapping branch were not executed, since neither an export nor a verified class mapping was supplied. Core extraction needs no third-party packages. Notebook validation used pandas.

Re-running the extractor skipped both already-processed ZIPs and rebuilt the analysis outputs without duplicating observations. Full testing against every release from 2019 onward has not been performed. The included examples are two nonconsecutive release batches, not a complete historical panel.

The exact ZIP checksums and universe checksum are in validation_sample/run_manifest.json. Production output retains its own hashes and quality report.
