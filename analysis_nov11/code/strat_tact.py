"""Strategic vs tactical attribution. Usage: strat_tact.py <scratch> <repo_dir>
exposure (years) x yield/spread change -> monthly P&L; strategic = window-average exposure, tactical = deviation."""
import sys, numpy as np, pandas as pd
from scipy import stats
S, R = sys.argv[1:3]; A = f"{S}/anna-zip2"; C = f"{A}/cleaned_data"; OUT = f"{S}/out"
TEN = ["3MON", "1YR", "5YR", "10YR", "30YR"]; FED = {"3MON": "zc_3m_chg_bp", "1YR": "zc_1y_chg_bp", "5YR": "zc_5y_chg_bp", "10YR": "zc_10y_chg_bp", "30YR": "zc_30y_chg_bp"}
u = pd.read_csv(f"{C}/4_reference/universe.csv", dtype=str); bad = set(pd.read_csv(f"{OUT}/excluded_return_flag_funds.csv").series_id)
prim = [x for x in u[u.group == "PRIMARY"].series_id if x not in bad]
pan = pd.read_csv(f"{C}/1_fund_quarter/positioning_panel_full.csv", usecols=["series_id", "report_date", "usd_duration_econ_yrs", "usd_rate_sensitivity_years_signed", "econ_sign_flag", "ig_spread_dur_econ_yrs", "hy_spread_dur_econ_yrs", "credit_screen_flag"], low_memory=False)
tp = pd.read_csv(f"{R}/analysis/results/rate_tenor_positions.csv", usecols=["series_id", "report_month"] + TEN).rename(columns={"report_month": "report_date"})
d = pan.merge(tp, on=["series_id", "report_date"], how="inner"); d = d[d.series_id.isin(prim)].copy(); d["date"] = pd.to_datetime(d.report_date)
tot = d[TEN].sum(axis=1); sgn = np.sign(d.usd_duration_econ_yrs / d.usd_rate_sensitivity_years_signed.replace(0, np.nan))
for t in TEN: d[t + "_e"] = d[t] * sgn
d["tenor_sum_e"] = d[[t + "_e" for t in TEN]].sum(axis=1)
d["rate_ok"] = d.econ_sign_flag.eq("ok") & sgn.notna() & ((d.tenor_sum_e - d.usd_duration_econ_yrs).abs() < 0.3)
d["cred_ok"] = d.credit_screen_flag.eq("ok") & d.ig_spread_dur_econ_yrs.notna() & d.hy_spread_dur_econ_yrs.notna(); d["cred"] = d.ig_spread_dur_econ_yrs + d.hy_spread_dur_econ_yrs
d["curve_exp"] = d["10YR_e"] + d["30YR_e"] - d["3MON_e"] - d["1YR_e"]
print(f"fund-quarter rows with tenor data {len(d)}; rate exposures usable {int(d.rate_ok.sum())}; credit usable {int(d.cred_ok.sum())}; tenor-sum matches econ duration within 0.3y on {np.mean(abs(d.tenor_sum_e-d.usd_duration_econ_yrs)<0.3):.1%} of rows")
fed = pd.read_csv(f"{C}/3_factors/fed_zero_curve_monthly.csv"); fed.index = pd.PeriodIndex(fed.month_end, freq="M")
fac = pd.read_csv(f"{A}/analysis/factor8_and_signs/factors_monthly.csv"); fac.index = pd.PeriodIndex(fac.month_end, freq="M")
r = pd.read_csv(f"{A}/analysis/factor8_and_signs/fund_monthly_return_median_class.csv", index_col=0); r.index = pd.PeriodIndex(r.index, freq="M")
W = {"W1": ("2019-07", "2022-12"), "W2": ("2023-01", "2026-06")}
rows = []; hitrows = []
for s in prim:
    g = d[d.series_id == s].sort_values("date")
    for w, (a, b) in W.items():
        months = pd.period_range(a, b, freq="M"); res = dict(series_id=s, window=w)
        for kind, ok, cols in [("rate", "rate_ok", [t + "_e" for t in TEN]), ("cred", "cred_ok", ["cred"])]:
            gg = g[g[ok]].dropna(subset=cols)
            inwin = gg[(gg.date >= pd.Timestamp(a + "-01")) & (gg.date <= pd.Period(b, "M").end_time)]
            if len(inwin) < 8: res[f"n_{kind}"] = len(inwin); continue
            mbar = inwin[cols].mean()
            mdf = pd.DataFrame({"m": months, "start": [m.start_time for m in months]})
            ass = pd.merge_asof(mdf.sort_values("start"), gg[["date"] + cols].sort_values("date"), left_on="start", right_on="date", direction="backward", allow_exact_matches=False, tolerance=pd.Timedelta(days=130))
            ass = ass.dropna(subset=["date"])  # earlier-window report may carry into the first months (exposure known at the time)
            if len(ass) < 18: res[f"n_{kind}"] = len(inwin); continue
            if kind == "rate":
                dy = pd.DataFrame({t: fed.loc[ass.m, FED[t]].values for t in TEN}, index=ass.index)
                E = ass[cols].values; Eb = np.tile(mbar.values, (len(ass), 1)); dyv = dy.values
                tot_ = -(E * dyv).sum(axis=1) / 100; str_ = -(Eb * dyv).sum(axis=1) / 100
            else:
                dc = fac.loc[ass.m, "d_credit_bp"].values; tot_ = -ass.cred.values * dc / 100; str_ = -mbar["cred"] * dc / 100
            tac_ = tot_ - str_
            res[f"{kind}_strategic_pp"] = str_.mean() * 12; res[f"{kind}_tactical_pp"] = tac_.mean() * 12; res[f"{kind}_tact_t"] = tac_.mean() / (tac_.std(ddof=1) / np.sqrt(len(tac_))) if tac_.std() > 0 else np.nan
            res[f"n_{kind}"] = len(inwin); res[f"months_{kind}"] = len(ass)
            if kind == "rate":
                res["duration_sd_yrs"] = inwin[cols].sum(axis=1).std(); res["curve_sd_yrs"] = inwin.curve_exp.std(); res["mean_duration_yrs"] = inwin[cols].sum(axis=1).mean()
                ma = ass.copy(); ma["tac"] = tac_; ma["tot"] = tot_; ma["mo"] = ass.m.values
                res["fit_corr_rate_pnl_vs_fund_ret"] = np.corrcoef(ma.tot, r.loc[ma.mo, s].values)[0, 1] if r[s].reindex(ma.mo).notna().all() else np.nan
            else:
                res["mean_credit_dur_yrs"] = inwin.cred.mean(); res["credit_sd_yrs"] = inwin.cred.std()
            ps = pd.Series(tac_, index=ass.date.values).groupby(level=0).agg(["sum", "count"]); ps = ps[ps["count"] >= 2]
            res[f"{kind}_hit_rate"] = (ps["sum"] > 0).mean() if len(ps) >= 6 else np.nan; res[f"{kind}_periods"] = len(ps)
        rows.append(res)
f = pd.DataFrame(rows)
al = pd.read_excel(f"{OUT}/alpha_persistence_etf.xlsx", sheet_name="by_fund_5f_cash")[["series_id", "alpha1", "alpha2"]]
w = f.pivot(index="series_id", columns="window"); w.columns = [f"{a}_{b}" for a, b in w.columns]; w = w.reset_index().merge(al, on="series_id", how="left").merge(u[["series_id", "fund_name", "manager", "style"]], on="series_id")
pd.set_option("display.width", 250, "display.max_columns", 40)
print("\nfunds with usable rate attribution in both windows:", int(w[["rate_tactical_pp_W1", "rate_tactical_pp_W2"]].notna().all(axis=1).sum()), "| credit:", int(w[["cred_tactical_pp_W1", "cred_tactical_pp_W2"]].notna().all(axis=1).sum()))
print("median fit corr (attributed rate P&L vs actual fund return, monthly):", round(f.fit_corr_rate_pnl_vs_fund_ret.median(), 2))
print("\nAverage P&L by layer (annualised pp, mean/median across funds) and share of funds positive:")
for kind in ["rate", "cred"]:
    for lay in ["strategic", "tactical"]:
        for wn in ["W1", "W2"]:
            x = w[f"{kind}_{lay}_pp_{wn}"].dropna(); print(f"  {kind:4s} {lay:9s} {wn}: n={len(x):2d} mean {x.mean():+.2f} median {x.median():+.2f} positive {np.mean(x>0):.0%}" + (f"  t(mean)={x.mean()/(x.std(ddof=1)/np.sqrt(len(x))):+.2f}" if lay=="tactical" else ""))
print("\nTactical success (share of report periods with positive tactical P&L), mean across funds:")
for kind in ["rate", "cred"]:
    for wn in ["W1", "W2"]:
        x = w[f"{kind}_hit_rate_{wn}"].dropna(); print(f"  {kind:4s} {wn}: {x.mean():.1%} (n funds {len(x)}); funds above 50%: {np.mean(x>0.5):.0%}")
print("\nPersistence of each layer across windows (Spearman rho, p):")
for col in ["rate_strategic_pp", "rate_tactical_pp", "cred_strategic_pp", "cred_tactical_pp", "duration_sd_yrs", "curve_sd_yrs", "credit_sd_yrs", "mean_duration_yrs", "mean_credit_dur_yrs", "rate_hit_rate", "cred_hit_rate"]:
    x = w[[f"{col}_W1", f"{col}_W2"]].dropna()
    if len(x) >= 12: c, p = stats.spearmanr(x.iloc[:, 0], x.iloc[:, 1]); print(f"  {col:22s} n={len(x):2d} rho={c:+.2f} p={p:.3f}")
print("\nDo layers line up with 5-factor alpha (same window)? Spearman rho (p):")
for wn, ac in [("W1", "alpha1"), ("W2", "alpha2")]:
    for col in ["rate_strategic_pp", "rate_tactical_pp", "cred_strategic_pp", "cred_tactical_pp"]:
        x = w[[f"{col}_{wn}", ac]].dropna()
        if len(x) >= 12: c, p = stats.spearmanr(x.iloc[:, 0], x.iloc[:, 1]); print(f"  {wn} {col:20s} n={len(x):2d} rho={c:+.2f} p={p:.3f}")
sd = w[["rate_strategic_pp_W2", "rate_tactical_pp_W2", "cred_strategic_pp_W2", "cred_tactical_pp_W2"]].std().round(2); print("\ncross-fund dispersion (sd, pp) in W2:", sd.to_dict())
w.to_csv(f"{OUT}/strategic_tactical_by_fund.csv", index=False)
