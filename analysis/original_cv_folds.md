# Original cross-validation folds

`original_cv_folds.csv` contains one test-fold assignment per section, validation block, fund and quarter. It was recovered from the out-of-fold prediction tables in GitHub main's `capstone_results_with_bloomberg.zip` (SHA-256 `a913475a23c2841a42e589db5d3df5e4f59c83984dede2f5c3632dd5645fbe7c`). Predictions from multiple models were collapsed after checking that they agreed on each assignment.

| Section | Archive member under `final_analysis_output/` | Validations | Rows per validation |
| --- | --- | --- | ---: |
| 10 | `tables/ml_out_of_fold_predictions.csv` | `held_out_fund`, `held_out_family` | 1,094 |
| 14 | `sponsor/model_predictions.csv` | `competitor_fund`, `competitor_family` | 1,010 |

The notebook checks exact panel coverage, all five fold labels, and that each fund or manager belongs to a single test fold. The remaining four folds form the training set in each outer iteration. The original calendar and Vanguard holdouts follow their existing rules. The archive records outer test assignments and Section 10 selected hyperparameters. It does not contain the inner training/validation assignments, so tuning still uses the notebook's original grouped splitter and grids. The results archive includes a copy of the fold assignment CSV under `audit/`.
