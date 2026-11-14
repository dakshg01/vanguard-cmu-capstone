"""Risk-adjusted persistence. Usage: alpha_persistence.py <anna_dir> <out_dir>
Regress monthly fund return (%) on d_rate_bp and d_credit_bp (Anna's factors) inside each window;
alpha = intercept*12 (annualised %). Also the same on excess return over SPAB."""
import sys, numpy as np, pandas as pd
from scipy import stats
A, OUT = sys.argv[1], sys.argv[2]
r = pd.read_csv(f"{A}/analysis/factor8_and_signs/fund_monthly_return_median_class.csv", index_col=0); r.index = pd.PeriodIndex(r.index, freq="M")
fac = pd.read_csv(f"{A}/analysis/factor8_and_signs/factors_monthly.csv"); fac.index = pd.PeriodIndex(fac.month_end, freq="M"); fac = fac[["d_rate_bp","d_credit_bp"]]
u = pd.read_csv(f"{A}/cleaned_data/4_reference/universe.csv", dtype=str)
bad = set(pd.read_csv(f"{OUT}/excluded_return_flag_funds.csv").series_id)
prim = [x for x in u[u.group == "PRIMARY"].series_id if x not in bad]
B = "S000017334"
def ols(y, X):
    d = pd.concat([y, X], axis=1).dropna()
    if len(d) < 24: return None
    Z = np.c_[np.ones(len(d)), d.iloc[:, 1:].values]; yy = d.iloc[:, 0].values
    b, *_ = np.linalg.lstsq(Z, yy, rcond=None); e = yy - Z @ b
    return dict(n=len(d), alpha=b[0] * 12, b_rate=b[1], b_credit=b[2], resid_sd=e.std(ddof=3) * np.sqrt(12), r2=1 - e.var() / yy.var())
def windows(drop2020=False):
    w1 = list(pd.period_range("2019-07", "2022-12", freq="M")); w2 = list(pd.period_range("2023-01", "2026-06", freq="M"))
    if drop2020: w1 = [m for m in w1 if m.year != 2020]
    return w1, w2
def run(target, label, drop2020=False):
    w1, w2 = windows(drop2020); rows = []
    for s in prim:
        y = r[s] - (r[B] if target == "excess" else 0)
        a, b = ols(y.reindex(w1), fac.reindex(w1)), ols(y.reindex(w2), fac.reindex(w2))
        if a and b: rows.append(dict(series_id=s, **{f"{k}1": v for k, v in a.items()}, **{f"{k}2": v for k, v in b.items()}))
    d = pd.DataFrame(rows); d["ir1"] = d.alpha1 / d.resid_sd1; d["ir2"] = d.alpha2 / d.resid_sd2
    out = dict(spec=label, n=len(d))
    for k in ["alpha", "ir", "b_rate", "b_credit"]:
        c, p = stats.spearmanr(d[f"{k}1"], d[f"{k}2"]); out[f"rho_{k}"] = round(c, 3); out[f"p_{k}"] = round(p, 3)
    c, p = stats.spearmanr(d.alpha1.append(d.alpha2) if False else pd.concat([d.alpha1, d.alpha2]), pd.concat([d.b_credit1, d.b_credit2])); out["rho_alpha_vs_credit_beta(pooled)"] = round(c, 3)
    return out, d
specs = [("raw", "Fund return on factors", False), ("raw", "Fund return on factors, 2020 dropped", True),
         ("excess", "Excess over SPAB on factors", False), ("excess", "Excess over SPAB on factors, 2020 dropped", True)]
summ, store = [], {}
for t, lab, d20 in specs:
    o, d = run(t, lab, d20); summ.append(o); store[lab] = d
S_ = pd.DataFrame(summ); pd.set_option("display.width", 250, "display.max_columns", 30); print(S_.to_string(index=False))
# by-fund table for main spec + names
main = store["Excess over SPAB on factors"].merge(u[["series_id","fund_name","manager","style"]], on="series_id")
main["alpha_group"] = "mixed"
q1, q2 = main.alpha1.rank(pct=True), main.alpha2.rank(pct=True)
main.loc[(q1 >= 2/3) & (q2 >= 2/3), "alpha_group"] = "top third both"; main.loc[(q1 <= 1/3) & (q2 <= 1/3), "alpha_group"] = "bottom third both"
print(main.alpha_group.value_counts().to_dict())
print(main[main.alpha_group != "mixed"][["fund_name","alpha_group","alpha1","alpha2","b_credit1","b_credit2"]].round(2).sort_values(["alpha_group","alpha1"]).to_string(index=False))
# sanity vs Anna's own full-period betas
f8 = pd.read_csv(f"{A}/analysis/factor8_and_signs/F8_full_period_by_fund.csv"); print("F8 columns:", list(f8.columns))
with pd.ExcelWriter(f"{OUT}/alpha_persistence.xlsx") as w:
    S_.to_excel(w, "summary", index=False); main.to_excel(w, "by_fund_excess_spec", index=False)
    store["Fund return on factors"].to_excel(w, "by_fund_raw_spec", index=False)
    pd.DataFrame({"note": ["Factors are Anna's: d_rate_bp = monthly change in mean(2y,5y,10y) Fed zero-coupon yield; d_credit_bp = monthly change in Moody's Baa-10y spread (FRED BAA10Y). Both are yield/spread CHANGES, not returns.",
       "alpha = regression intercept x12 (annualised %, window-specific). Windows 2019-07..2022-12 and 2023-01..2026-06; min 24 months.",
       "Because the credit factor is a spread change and carries no income, the carry earned from credit exposure lands in alpha. Alpha is therefore not a pure skill measure; see rho_alpha_vs_credit_beta.",
       "Excluded: 4 funds failing repo class-return screen. No multiple-testing adjustment."]}).to_excel(w, "notes", index=False)
