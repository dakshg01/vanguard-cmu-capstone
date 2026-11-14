"""Risk-adjusted persistence with ETF factor returns. Usage: alpha_etf.py <scratch> <etf_csv>"""
import sys, numpy as np, pandas as pd
from scipy import stats
S, E = sys.argv[1:3]; A = f"{S}/anna-zip2"; OUT = f"{S}/out"
e = pd.read_csv(E); e.index = pd.PeriodIndex(e.Date, freq="M"); e = e.drop(columns="Date") * 100   # % per month
F5 = pd.DataFrame({"rate": e.IEF - e.SHY, "curve": e.TLT - e.IEF, "ig": e.LQD - e.IEF, "hy": e.HYG - e.LQD, "mbs": e.MBB - e.IEF})
F3 = F5[["rate", "ig", "hy"]]; cash = e.SHY
r = pd.read_csv(f"{A}/analysis/factor8_and_signs/fund_monthly_return_median_class.csv", index_col=0); r.index = pd.PeriodIndex(r.index, freq="M")
u = pd.read_csv(f"{A}/cleaned_data/4_reference/universe.csv", dtype=str)
bad = set(pd.read_csv(f"{OUT}/excluded_return_flag_funds.csv").series_id)
prim = [x for x in u[u.group == "PRIMARY"].series_id if x not in bad]; B = "S000017334"
def ols(y, X, minn=30):
    d = pd.concat([y.rename("y"), X], axis=1).dropna()
    if len(d) < minn: return None
    Z = np.c_[np.ones(len(d)), d.iloc[:, 1:].values]; yy = d.y.values
    b, *_ = np.linalg.lstsq(Z, yy, rcond=None); res = yy - Z @ b; k = Z.shape[1]
    s2 = res @ res / (len(d) - k); se = np.sqrt(np.diag(s2 * np.linalg.inv(Z.T @ Z)))
    out = dict(n=len(d), alpha=b[0] * 12, alpha_t=b[0] / se[0], resid_sd=res.std(ddof=k) * np.sqrt(12), r2=1 - res.var() / yy.var())
    for i, c in enumerate(X.columns): out[f"b_{c}"] = b[i + 1]
    return out
def windows(drop2020):
    w1 = list(pd.period_range("2019-07", "2022-12", freq="M")); w2 = list(pd.period_range("2023-01", "2026-06", freq="M"))
    return ([m for m in w1 if m.year != 2020] if drop2020 else w1), w2
def run(target, F, drop2020):
    w1, w2 = windows(drop2020); rows = []
    for s in prim:
        y = (r[s] - cash) if target == "cash" else (r[s] - r[B])
        a, b = ols(y.reindex(w1), F.reindex(w1), 24 if drop2020 else 30), ols(y.reindex(w2), F.reindex(w2), 30)
        if a and b: rows.append(dict(series_id=s, **{f"{k}1": v for k, v in a.items()}, **{f"{k}2": v for k, v in b.items()}))
    d = pd.DataFrame(rows); d["ir1"] = d.alpha1 / d.resid_sd1; d["ir2"] = d.alpha2 / d.resid_sd2; return d
specs = [("5-factor, excess over cash", "cash", F5, False), ("5-factor, excess over cash, 2020 dropped", "cash", F5, True),
         ("5-factor, excess over SPAB", "spab", F5, False), ("5-factor, excess over SPAB, 2020 dropped", "spab", F5, True),
         ("3-factor, excess over cash", "cash", F3, False), ("3-factor, excess over cash, 2020 dropped", "cash", F3, True)]
rows, store = [], {}
keep = None
for lab, t, F, d20 in specs:
    d = run(t, F, d20)
    if lab=="5-factor, excess over cash, 2020 dropped": keep=set(d.series_id)
    store[lab] = d; o = dict(spec=lab, n=len(d), median_r2=round(pd.concat([d.r21, d.r22]).median(), 2),
        median_alpha_w1=round(d.alpha1.median(), 2), median_alpha_w2=round(d.alpha2.median(), 2))
    for k in ["alpha", "alpha_t", "ir"]:
        c, p = stats.spearmanr(d[f"{k}1"], d[f"{k}2"]); o[f"rho_{k}"] = round(c, 3); o[f"p_{k}"] = round(p, 3)
    for k in [c for c in d.columns if c.startswith("b_") and c.endswith("1")]:
        c, p = stats.spearmanr(d[k], d[k[:-1] + "2"]); o[f"rho_{k[:-1]}"] = round(c, 2)
    cr = "b_ig"; pooled_a = pd.concat([d.alpha1, d.alpha2]); pooled_b = pd.concat([d[cr + "1"], d[cr + "2"]]) if cr + "1" in d else None
    if pooled_b is not None: o["rho_alpha_vs_ig_beta"] = round(stats.spearmanr(pooled_a, pooled_b)[0], 2)
    t1 = d.alpha1.rank(pct=True) >= 2/3; b1 = d.alpha1.rank(pct=True) <= 1/3
    o["W2_alpha_top_third_W1"] = round(d.alpha2[t1].mean(), 2); o["W2_alpha_bottom_third_W1"] = round(d.alpha2[b1].mean(), 2)
    o["spread_t_p"] = round(stats.ttest_ind(d.alpha2[t1], d.alpha2[b1], equal_var=False).pvalue, 3)
    rows.append(o)
S_ = pd.DataFrame(rows); pd.set_option("display.width", 300, "display.max_columns", 40, "display.max_colwidth", 50)
print(S_.T.to_string(header=False))
main = store["5-factor, excess over cash"].merge(u[["series_id", "fund_name", "manager", "style"]], on="series_id")
q1, q2 = main.alpha1.rank(pct=True), main.alpha2.rank(pct=True); main["group"] = "mixed"
main.loc[(q1 >= 2/3) & (q2 >= 2/3), "group"] = "top third both"; main.loc[(q1 <= 1/3) & (q2 <= 1/3), "group"] = "bottom third both"
print(main.group.value_counts().to_dict()); print(main[main.group != "mixed"][["fund_name", "group", "alpha1", "alpha2", "alpha_t1", "alpha_t2"]].round(2).sort_values(["group", "alpha1"]).to_string(index=False))
print("full-sample alpha by fund (5-factor, cash): median %.2f, share with |t|>2 in W1 %.0f%%, W2 %.0f%%" % (pd.concat([main.alpha1, main.alpha2]).median(), 100*(main.alpha_t1.abs() > 2).mean(), 100*(main.alpha_t2.abs() > 2).mean()))
with pd.ExcelWriter(f"{OUT}/alpha_persistence_etf.xlsx") as w:
    S_.to_excel(w, "summary", index=False); main.to_excel(w, "by_fund_5f_cash", index=False)
    store["5-factor, excess over SPAB"].merge(u[["series_id", "fund_name", "manager", "style"]], on="series_id").to_excel(w, "by_fund_5f_spab", index=False)
    pd.DataFrame({"note": ["Factors from the team's ETF file (monthly total returns, %): rate = IEF-SHY; curve = TLT-IEF; ig = LQD-IEF; hy = HYG-LQD; mbs = MBB-IEF. 3-factor set = rate, ig, hy. Fund returns are median-class monthly returns, net of fees.",
      "Target 'cash' = fund return minus SHY (SHY used as the cash leg, so it is a short-Treasury return, not a bill). Target 'SPAB' = fund return minus SPAB.",
      "alpha = intercept x12 (annualised %), estimated separately in 2019-07..2022-12 and 2023-01..2026-06; min 30 months. alpha_t = intercept t-stat (OLS standard errors).",
      "Verified: SPAB (N-PORT) vs AGG (ETF) monthly correlation 0.9987 at lag 0, so month alignment is correct.",
      "Caveats: ETF returns are net of ETF fees; MBB/LQD/HYG are imperfect stand-ins for index returns; five factors on 42 months give noisy betas; excluded 4 funds failing the repo class-return screen; no multiple-testing adjustment."]}).to_excel(w, "notes", index=False)
