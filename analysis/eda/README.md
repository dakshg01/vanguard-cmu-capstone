# Capstone EDA notebook

Open `../../Capstone_EDA.ipynb` in VS Code or Jupyter. All code cells have been executed and their outputs saved. `Capstone_EDA.html` is a browser-readable copy.

The notebook contains 13 sections, 15 code cells, 11 figures, and explanatory interpretations:

1. Setup and source-hash checks
2. Reporting coverage
3. Missingness, quality flags and filing lags
4. Fund size and selected AUM histories
5. Monthly flows and valid three-month flow intervals
6. Common-window class return metrics and class-consistency checks
7. Vanguard Core Bond class returns and drawdowns
8. Proxy-return regressions with HAC intervals
9. Same-month active-sector heatmap
10. Filed risk signs and tenor exposures
11. Flow/allocation-change association with a fund-block bootstrap
12. Swap currency/direction cross-check
13. Automatically generated findings and remaining work

Inputs are the original extraction CSVs and audited outputs in `../results/`. They are read without modification. Small analysis tables are in `tables/`; PNG and SVG exports are in `charts/`. `FINDINGS.md` and `key_findings.json` contain the notebook's results.

From the project folder, open the UI with:

```powershell
python -m jupyterlab Capstone_EDA.ipynb
```

Or rerun everything from a terminal:

```powershell
python -m nbconvert --to notebook --execute Capstone_EDA.ipynb --inplace --ExecutePreprocessor.timeout=600
python -m nbconvert --to html Capstone_EDA.ipynb --output Capstone_EDA.html --output-dir analysis/eda
```

The analysis needs pandas, numpy, matplotlib and statsmodels, alongside Jupyter. Current package versions are recorded in `runtime_versions.json`.

The common return window is 2021-2025. The within-fund return diagnostic flags large class dispersion; it does not correct the source values or pick a winning class. Those funds remain in saved metrics and are excluded as whole funds from the screened return chart. Both raw and screened sample counts are reported.

Risk conventions and class mappings remain unverified. The regression is a single-proxy descriptive fit, not the sponsor's rates/credit-factor regression or a skill estimate. Sector-weight changes are not trading turnover. All source overlap exclusions, class-review flags, windows and approximation assumptions are retained in the notebook and outputs.

`../build_eda_notebook.py` is the notebook-construction source. Running that builder replaces the notebook with an unexecuted copy; it is not needed to use or edit the delivered notebook.
