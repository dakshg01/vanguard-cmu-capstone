"""Fund-family style profiles. Usage: family_styles.py <scratch> <repo_dir>"""
import sys, numpy as np, pandas as pd
from scipy import stats
from scipy.cluster.hierarchy import linkage, fcluster
from sklearn.metrics import silhouette_score
S, R = sys.argv[1:3]; A = f"{S}/anna-zip2"; C = f"{A}/cleaned_data"; OUT = f"{S}/out"
TEN = ["3MON", "1YR", "5YR", "10YR", "30YR"]
u = pd.read_csv(f"{C}/4_reference/universe.csv", dtype=str); prim = u[u.group == "PRIMARY"][["series_id", "fund_name", "manager", "style"]]
bad = set(pd.read_csv(f"{OUT}/excluded_return_flag_funds.csv").series_id)
pan = pd.read_csv(f"{C}/1_fund_quarter/positioning_panel_full.csv", usecols=["series_id", "report_date", "usd_duration_econ_yrs", "usd_rate_sensitivity_years_signed", "econ_sign_flag", "ig_spread_dur_econ_yrs", "hy_spread_dur_econ_yrs", "credit_screen_flag"], low_memory=False)
tp = pd.read_csv(f"{R}/analysis/results/rate_tenor_positions.csv", usecols=["series_id", "report_month"] + TEN).rename(columns={"report_month": "report_date"})
d = pan.merge(tp, on=["series_id", "report_date"], how="left")
sg = np.sign(d.usd_duration_econ_yrs / d.usd_rate_sensitivity_years_signed.replace(0, np.nan))
for t in TEN: d[t] = d[t] * sg
d["rate_ok"] = d.econ_sign_flag.eq("ok") & sg.notna(); d["curve_exp"] = d["10YR"] + d["30YR"] - d["3MON"] - d["1YR"]
d["cred"] = (d.ig_spread_dur_econ_yrs + d.hy_spread_dur_econ_yrs).where(d.credit_screen_flag.eq("ok"))
def agg(g):
    r = g[g.rate_ok]; ok = len(r) >= 8
    return pd.Series(dict(mean_duration_yrs=r.usd_duration_econ_yrs.mean() if ok else np.nan, duration_sd_yrs=r.usd_duration_econ_yrs.std() if ok else np.nan,
        curve_exposure_yrs=r.curve_exp.mean() if ok else np.nan, curve_sd_yrs=r.curve_exp.std() if ok else np.nan, credit_sd_yrs=g.cred.std() if g.cred.notna().sum() >= 8 else np.nan,
        reports_used=len(r)))
dyn = d.groupby("series_id").apply(agg, include_groups=False).reset_index()
rm = pd.read_excel(f"{OUT}/risk_mix_provisional.xlsx", sheet_name="by_fund")[["series_id", "gov_agency_pct", "corporate_pct", "securitized_credit_pct", "em_pct", "credit_total_pct", "hy_dur", "ig_dur", "unresolved_pct", "flag_unresolved_gt8"]]
m = pd.read_csv(f"{C}/1_fund_quarter/master_fund_quarter_panel.csv"); mm = m.groupby("series_id")[["sector_active_share", "log_nav_bn", "age_yrs_lowerbound"]].mean().reset_index()
fp = pd.read_csv(f"{R}/sec_rr/sec_rr_fees_panel.csv"); fp = fp[(fp.quarter_end >= "2019-07-01") & (fp.quarter_end <= "2026-06-30")]
fp["net_exp_bp"] = fp.net_exp * 1e4; fp["mgmt_fee_bp"] = fp.mgmt_fee * 1e4
fee = fp.groupby("series_id").agg(net_exp_bp=("net_exp_bp", "mean"), mgmt_fee_bp=("mgmt_fee_bp", "mean"), turnover=("turnover", "mean")).reset_index()
old = m.groupby("series_id")[["turnover", "net_exp_bp"]].mean().reset_index(); print("corr old vs SEC-RR panel: turnover", round(old.merge(fee, on="series_id").pipe(lambda x: x.turnover_x.corr(x.turnover_y)), 3), " net_exp", round(old.merge(fee, on="series_id").pipe(lambda x: x.net_exp_bp_x.corr(x.net_exp_bp_y)), 3))
mm = mm.merge(fee, on="series_id", how="left")
r = pd.read_csv(f"{A}/analysis/factor8_and_signs/fund_monthly_return_median_class.csv", index_col=0); r.index = pd.PeriodIndex(r.index, freq="M")
ex = (r.sub(r["S000017334"], axis=0).loc["2019-07":"2026-06"].mean() * 12).rename("excess_vs_spab_pp").reset_index().rename(columns={"index": "series_id"})
al = pd.read_excel(f"{OUT}/alpha_persistence_etf.xlsx", sheet_name="by_fund_5f_cash"); al["alpha_5f_pp"] = (al.alpha1 * al.n1 + al.alpha2 * al.n2) / (al.n1 + al.n2)
F = prim.merge(dyn, on="series_id", how="left").merge(rm, on="series_id", how="left").merge(mm, on="series_id", how="left").merge(ex, on="series_id", how="left").merge(al[["series_id", "alpha_5f_pp"]], on="series_id", how="left")
F.loc[F.series_id.isin(bad), ["excess_vs_spab_pp", "alpha_5f_pp"]] = np.nan
STYLE = ["gov_agency_pct", "corporate_pct", "securitized_credit_pct", "em_pct", "hy_dur", "mean_duration_yrs", "curve_exposure_yrs", "duration_sd_yrs", "curve_sd_yrs", "credit_sd_yrs", "turnover", "net_exp_bp"]
print("feature coverage (funds with value, of 49):", F[STYLE].notna().sum().to_dict())
# ---- within-family consistency
rows = []
fam2 = F.groupby("manager").filter(lambda g: len(g) >= 2)
for c in STYLE:
    g = fam2[["manager", c]].dropna(); g = g.groupby("manager").filter(lambda x: len(x) >= 2)
    groups = [x[c].values for _, x in g.groupby("manager")]
    if len(groups) < 5: continue
    Fst, p = stats.f_oneway(*groups); k = len(groups); N = len(g); n0 = (N - sum(len(x) ** 2 for x in groups) / N) / (k - 1)
    msb = sum(len(x) * (x.mean() - g[c].mean()) ** 2 for x in groups) / (k - 1); msw = sum(((x - x.mean()) ** 2).sum() for x in groups) / (N - k)
    rows.append(dict(feature=c, families=k, funds=N, F=round(Fst, 2), p=round(p, 3), icc=round(max((msb - msw) / (msb + (n0 - 1) * msw), -1), 2)))
cons = pd.DataFrame(rows).sort_values("p"); print("\nDo funds in the same family resemble each other? (one-way ANOVA across families with >=2 funds; ICC = share of variance between families)"); print(cons.to_string(index=False))
# ---- family profiles with z-scores
Z = (F[STYLE] - F[STYLE].mean()) / F[STYLE].std()
fam = F.groupby("manager").agg(funds=("series_id", "count"), **{c: (c, "mean") for c in STYLE + ["excess_vs_spab_pp", "alpha_5f_pp"]}).round(2)
fz = Z.groupby(F.manager).mean()
LAB = {"gov_agency_pct": "government/agency-heavy", "corporate_pct": "corporate-heavy", "securitized_credit_pct": "securitized-credit-heavy", "em_pct": "EM-heavy", "hy_dur": "high-yield risk", "mean_duration_yrs": "long duration",
       "curve_exposure_yrs": "long-end curve tilt", "duration_sd_yrs": "active duration changes", "curve_sd_yrs": "active curve changes", "credit_sd_yrs": "active credit changes", "turnover": "high turnover", "net_exp_bp": "high fees"}
LOW = {k: v for k, v in LAB.items()}; LOW.update({"gov_agency_pct": "light in government/agency", "corporate_pct": "light in corporates", "securitized_credit_pct": "light in securitized credit", "em_pct": "no EM", "hy_dur": "little high-yield risk", "mean_duration_yrs": "short duration",
       "curve_exposure_yrs": "front-end curve tilt", "duration_sd_yrs": "stable duration", "curve_sd_yrs": "stable curve", "credit_sd_yrs": "stable credit", "turnover": "low turnover", "net_exp_bp": "low fees"})
def desc(zr):
    z = zr.dropna(); hi = [LAB[k] for k, v in z.sort_values(ascending=False).items() if v >= 0.8][:3]; lo = [LOW[k] for k, v in z.sort_values().items() if v <= -0.8][:3]
    return "; ".join(hi + lo) if (hi or lo) else "close to the universe average"
fam["distinctive_traits"] = [desc(fz.loc[i]) for i in fam.index]
print("\nFAMILY STYLE CARDS (z-score vs all funds, |z|>=0.8):")
for i, rw in fam.sort_values("funds", ascending=False).iterrows(): print(f"  {i:18s} ({int(rw.funds)} fund{'s' if rw.funds>1 else ''}): {rw.distinctive_traits}")
# ---- clustering
cc = F.dropna(subset=STYLE).copy(); cc = cc[~cc.flag_unresolved_gt8.fillna(False).astype(bool)]
Zc = ((cc[STYLE] - cc[STYLE].mean()) / cc[STYLE].std()).clip(-3, 3); L = linkage(Zc.values, "ward")
print(f"\nclustering sample: {len(cc)} funds (excluded {int(F[STYLE].isna().any(axis=1).sum())} with missing features, {int(F.flag_unresolved_gt8.fillna(False).astype(bool).sum())} with unresolved>8%)")
sil = {k: round(silhouette_score(Zc.values, fcluster(L, k, "maxclust")), 3) for k in range(2, 7)}; print("silhouette by k:", sil)
K = 4; cc["cluster"] = fcluster(L, K, "maxclust")
prof = cc.groupby("cluster").agg(funds=("series_id", "count"), **{c: (c, "mean") for c in STYLE + ["excess_vs_spab_pp", "alpha_5f_pp"]}).round(2); print("\nCLUSTER PROFILES (k=4)"); print(prof.T.to_string())
for k, g in cc.groupby("cluster"): print(f"  cluster {k}: " + ", ".join(f"{a} ({b})" for a, b in zip(g.fund_name.str.replace(' Fund','').str.replace(' Bond',''), g.manager)))
# family purity: share of multi-fund families (>=2 clustered funds) whose funds sit in one cluster
gg = cc.groupby("manager").filter(lambda x: len(x) >= 2); pure = gg.groupby("manager").cluster.nunique().eq(1); print(f"\nfamilies with >=2 clustered funds: {len(pure)}; all funds in same cluster: {int(pure.sum())}  (random assignment would give about {np.mean([ (1/K)**(n-1) for n in gg.groupby('manager').size()]):.0%})")
print("performance by cluster (excess vs SPAB pp, 5f alpha pp):", prof[["excess_vs_spab_pp", "alpha_5f_pp"]].to_dict("index"))
with pd.ExcelWriter(f"{OUT}/family_styles.xlsx") as w:
    F.merge(cc[["series_id", "cluster"]], on="series_id", how="left").to_excel(w, "fund_features", index=False); fam.to_excel(w, "family_profiles"); fz.round(2).to_excel(w, "family_zscores")
    cons.to_excel(w, "family_consistency", index=False); prof.to_excel(w, "cluster_profiles"); cc[["series_id", "fund_name", "manager", "style", "cluster"]].to_excel(w, "cluster_members", index=False)
    pd.DataFrame({"note": ["Style features per fund, 2019-2026Q2: bucket weights (Layer 1 mix), HY spread duration, average duration and long-minus-short curve exposure, variability of duration/curve/credit exposure across reports (tactical activity), turnover and fees.",
     "IG spread duration is excluded from style features because filed IG spread duration is not comparable across families.", "Family z-scores are family means relative to all funds; a trait is listed when |z|>=0.8. With 1-3 funds per family these describe the funds in this universe, not the whole firm.",
     "Only 12 families have 2+ primary funds (25 funds), so consistency tests have limited power. PIMCO and BlackRock have one primary fund each.", "Clusters: Ward hierarchical on standardised, winsorised features; funds with missing features or >8% unresolved holdings excluded. Descriptive, not predictive.",
     "Excess return vs SPAB and 5-factor alpha are outcomes only, not clustering inputs; the 4 return-flagged funds have no outcome values."]}).to_excel(w, "notes", index=False)
