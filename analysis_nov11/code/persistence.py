"""First-pass persistence comparison. Usage: persistence.py <anna_dir> <out_dir>"""
import sys, numpy as np, pandas as pd
from scipy import stats
A, OUT = sys.argv[1], sys.argv[2]
BENCH = "S000017334"  # SPAB
r = pd.read_csv(f"{A}/analysis/factor8_and_signs/fund_monthly_return_median_class.csv", index_col=0)
r.index = pd.PeriodIndex(r.index, freq="M")
uni = pd.read_csv(f"{A}/cleaned_data/4_reference/universe.csv", dtype=str)
bad = pd.read_csv(f"{OUT}/excluded_return_flag_funds.csv").series_id.tolist()  # 4 funds failing repo class-return screen
prim = [x for x in uni[uni.group == "PRIMARY"].series_id.tolist() if x not in bad]
ex = r.sub(r[BENCH], axis=0).drop(columns=[BENCH])
w1 = ex.loc["2019-07":"2022-12"]; w2 = ex.loc["2023-01":"2026-06"]
def ann(w): return w.mean() * 12, (w.mean() * 12) / (w.std() * np.sqrt(12))
res = pd.DataFrame({"series_id": ex.columns})
res["n1"] = w1.notna().sum().values; res["n2"] = w2.notna().sum().values
res["xs1_pct"], res["ir1"] = [x.values for x in ann(w1)]
res["xs2_pct"], res["ir2"] = [x.values for x in ann(w2)]
res = res[res.series_id.isin(prim) & (res.n1 >= 30) & (res.n2 >= 30)].copy()
print(len(bad),"funds excluded for class-return convention issues;", len(res), "primary funds with >=30 months in both windows (of", len(prim), ")")
rho, p = stats.spearmanr(res.xs1_pct, res.xs2_pct)
print(f"Spearman rank corr of excess return, window1 vs window2: {rho:.3f} (p={p:.3f}, n={len(res)})")
rho_ir, p_ir = stats.spearmanr(res.ir1, res.ir2); print(f"  same on information ratio: {rho_ir:.3f} (p={p_ir:.3f})")
for lo, name in [(0, "all")]: pass
res["r1"] = res.xs1_pct.rank(pct=True); res["r2"] = res.xs2_pct.rank(pct=True)
res["group"] = "middle/mixed"
res.loc[(res.r1 >= 2/3) & (res.r2 >= 2/3), "group"] = "persistent outperformer"
res.loc[(res.r1 <= 1/3) & (res.r2 <= 1/3), "group"] = "persistent laggard"
res["xs_full_pct"] = (res.xs1_pct * res.n1 + res.xs2_pct * res.n2) / (res.n1 + res.n2)
print(res.group.value_counts().to_string())
# features: average over all quarters of the cleaned master panel
m = pd.read_csv(f"{A}/cleaned_data/1_fund_quarter/master_fund_quarter_panel.csv")
feat = ["act_treasury","act_agency_mbs","act_corporate","act_nonagency_mbs","act_abs_clo","act_em","act_nonus_dev","act_cash",
        "sector_active_share","act_duration_filed","curve_long_minus_short_signed","act_ig_spread_dur_filed","act_hy_spread_dur_filed",
        "F8_act_rate_dur_returns","F8_act_credit_dur_returns","net_exp_bp","turnover","log_nav_bn"]
fm = m.groupby("series_id")[feat].mean(numeric_only=True)
cnt = m.groupby("series_id")[["sector_pair_complete"]].sum().rename(columns={"sector_pair_complete":"n_complete_sector_q"})
res = res.merge(fm, on="series_id", how="left").merge(cnt, on="series_id", how="left").merge(
      uni[["series_id","fund_name","manager","style"]], on="series_id", how="left")
res.to_csv(f"{OUT}/persistence_by_fund.csv", index=False)
g = res.groupby("group")[feat].mean().T
g["n_funds_with_data"] = None
cn = res.groupby("group")[feat].count().T
tab = pd.concat([g.drop(columns="n_funds_with_data").add_suffix(" (mean)"), cn.add_suffix(" (n)")], axis=1)
tab.round(2).to_csv(f"{OUT}/group_feature_means.csv")
print(tab.round(2).to_string())
# cross-sectional rank correlation of each feature with full-period excess return
rows = []
for f in feat:
    d = res[["xs_full_pct", f]].dropna()
    if len(d) >= 15:
        rr, pp = stats.spearmanr(d.xs_full_pct, d[f]); rows.append((f, len(d), rr, pp))
cs = pd.DataFrame(rows, columns=["feature","n","spearman_vs_excess","p"]).sort_values("p")
cs.round(3).to_csv(f"{OUT}/feature_vs_excess_corr.csv", index=False); print(cs.round(3).to_string(index=False))
print(res.loc[res.group!="middle/mixed", ["fund_name","manager","group","xs1_pct","xs2_pct"]].sort_values(["group","xs_full_pct" if False else "xs1_pct"]).round(2).to_string(index=False))
# sanity: persistence by manager style
print(res.groupby("style")[["xs1_pct","xs2_pct"]].mean().round(2).to_string())
