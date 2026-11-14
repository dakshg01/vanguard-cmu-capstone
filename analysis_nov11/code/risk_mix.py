"""Provisional risk mix per fund. Usage: risk_mix.py <anna_cleaned_data_dir> <out_dir>"""
import sys, numpy as np, pandas as pd
from scipy import stats
C, OUT = sys.argv[1:3]
p = pd.read_csv(f"{C}/1_fund_quarter/positioning_panel_full.csv", low_memory=False)
T = lambda s: s.astype(str).str.lower().isin(["true", "1", "1.0"])
p["complete"] = T(p.sector_complete)
SEC = {"UST": "US Treasury (nominal)", "TIPS": "TIPS (description identified)", "AGY": "Agency / other government", "AMBS": "Agency MBS",
       "NAMBS": "Non-agency MBS / CMBS", "ABS": "ABS / CLO", "CORP": "Corporate debt (ratings pending)", "NUSD": "Non-US sovereign (non-EM list)",
       "EM": "Emerging markets (fixed country list)", "MUNI": "Municipal", "CASH": "Cash / short-term / repo", "DERIV": "Derivatives (market value)", "OTH": "Other / unresolved"}
def mix(df, pre=""):
    g = lambda *k: sum(df[pre + SEC[x]].fillna(0) for x in k)
    out = pd.DataFrame({"gov_agency_pct": g("UST", "TIPS", "AGY", "AMBS", "NUSD", "CASH"),
                        "corporate_pct": g("CORP"), "securitized_credit_pct": g("NAMBS", "ABS"), "em_pct": g("EM"),
                        "other_pct": g("MUNI", "DERIV", "OTH")}, index=df.index)
    out["credit_total_pct"] = out.corporate_pct + out.securitized_credit_pct + out.em_pct
    return out
d = p[p.complete].copy(); d = pd.concat([d, mix(d)], axis=1)
ok = d.credit_screen_flag.eq("ok") & d.econ_sign_flag.ne("rate duration implausible (>10 yrs total or in one tenor)")
d["ig_dur"] = d.ig_spread_dur_econ_yrs.where(d.credit_screen_flag.eq("ok")); d["hy_dur"] = d.hy_spread_dur_econ_yrs.where(d.credit_screen_flag.eq("ok"))
d["hy_share_of_credit_risk"] = d.hy_dur / (d.ig_dur.abs() + d.hy_dur.abs())
d["period"] = np.where(d.report_date < "2023-01-01", "2019-2022", "2023-2026")
# ---- verification vs Qiang's VCOBX March 2026 example
v = p[(p.fund_name.str.contains("Vanguard Core Bond", na=False)) & p.report_date.str.startswith("2026-03")]
if len(v):
    r = v.iloc[0]; print("VCOBX 2026-03 (ours vs Qiang): UST %.1f vs 20.7 | Corp %.1f vs 43.2 | Non-US sov %.1f vs 10.4 | Agency MBS %.1f vs 18.4 | Other agency %.1f vs 7.2 | Muni %.1f vs 0.1 | duration %.2f vs 5.70 | IG spread dur %.2f vs 3.53" % (
        r[SEC["UST"]], r[SEC["CORP"]], r[SEC["NUSD"]], r[SEC["AMBS"]], r[SEC["AGY"]], r[SEC["MUNI"]], r.usd_duration_econ_yrs, r.ig_spread_dur_econ_yrs))
# ---- per fund
num = ["gov_agency_pct", "corporate_pct", "securitized_credit_pct", "em_pct", "other_pct", "credit_total_pct", "ig_dur", "hy_dur", "hy_share_of_credit_risk", "Other / unresolved"]
f = d.groupby(["series_id", "fund_name", "manager", "style"])[num].mean().round(2).reset_index().rename(columns={"Other / unresolved": "unresolved_pct"})
f["quarters_sector"] = d.groupby("series_id").size().reindex(f.series_id).values
f["quarters_credit_ok"] = d.groupby("series_id").ig_dur.count().reindex(f.series_id).values
lat = d.sort_values("report_date").groupby("series_id").tail(1).set_index("series_id")
f["latest_quarter"] = f.series_id.map(lat.report_date); f["latest_gov_pct"] = f.series_id.map(lat.gov_agency_pct).round(1); f["latest_credit_pct"] = f.series_id.map(lat.credit_total_pct).round(1)
for per in ["2019-2022", "2023-2026"]:
    x = d[d.period == per].groupby("series_id")[["credit_total_pct", "hy_dur"]].mean().round(2); f[f"credit_pct_{per}"] = f.series_id.map(x.credit_total_pct); f[f"hy_dur_{per}"] = f.series_id.map(x.hy_dur)
f["flag_unresolved_gt8"] = f.unresolved_pct > 8
# ---- benchmark reference mix
bm = p[T(p.benchmark_sector_complete)].copy(); b = mix(bm, "benchmark_sector__"); b["proxy"] = bm.benchmark_proxy.values
b["bench_ig_dur"] = bm.bench_ig_spread_dur_econ_yrs.where(bm.bench_credit_screen_flag.eq("ok")).values; b["bench_hy_dur"] = bm.bench_hy_spread_dur_econ_yrs.where(bm.bench_credit_screen_flag.eq("ok")).values
bref = b.groupby("proxy").mean(numeric_only=True).round(2); bref["rows"] = b.groupby("proxy").size()
# ---- by style, family
pd.set_option("display.width", 250, "display.max_columns", 40)
sty = f.groupby("style")[["gov_agency_pct", "corporate_pct", "securitized_credit_pct", "em_pct", "credit_total_pct", "ig_dur", "hy_dur", "hy_share_of_credit_risk"]].agg(["mean", "median"]).round(2); sty["funds"] = f.groupby("style").size()
print("\nBY STYLE"); print(sty.to_string())
for col in ["gov_agency_pct", "credit_total_pct", "corporate_pct", "securitized_credit_pct", "hy_dur", "hy_share_of_credit_risk"]:
    a, c = f[f["style"] == "Core"][col].dropna(), f[f["style"] == "Core-Plus"][col].dropna()
    print(f"  Core vs Core-Plus {col}: n={len(a)}/{len(c)}  medians {a.median():.2f} vs {c.median():.2f}  Mann-Whitney p={stats.mannwhitneyu(a, c).pvalue:.3f}")
fam = f.groupby("manager").agg(funds=("series_id", "count"), gov_pct=("gov_agency_pct", "mean"), credit_pct=("credit_total_pct", "mean"), corp_pct=("corporate_pct", "mean"), sec_pct=("securitized_credit_pct", "mean"), hy_dur=("hy_dur", "mean"), hy_share=("hy_share_of_credit_risk", "mean")).round(2).sort_values("credit_pct", ascending=False)
print("\nBENCHMARK MIX (reference)"); print(bref.to_string())
print("\nTOP/BOTTOM FUNDS by credit share"); print(f.sort_values("credit_total_pct")[["fund_name", "style", "gov_agency_pct", "credit_total_pct", "hy_dur", "hy_share_of_credit_risk"]].iloc[[0,1,2,3,-4,-3,-2,-1]].to_string(index=False))
print("\ncoverage: funds", len(f), "| sector rows", len(d), "| credit-ok rows", int(d.ig_dur.notna().sum()), "| funds with zero credit-ok quarters", int((f.quarters_credit_ok == 0).sum()), "| funds unresolved>8%:", int(f.flag_unresolved_gt8.sum()))
print("rows removed as incomplete sector:", int((~p.complete).sum()), "of", len(p))
print("sum check gov+credit+other = 100 on all rows:", bool(np.allclose(d.gov_agency_pct + d.credit_total_pct + d.other_pct, 100, atol=0.05)))

fx = f[~f.flag_unresolved_gt8]
print("\nFUNDS WITH UNRESOLVED > 8% (excluded below):"); print(f[f.flag_unresolved_gt8][["fund_name","style","unresolved_pct","gov_agency_pct","credit_total_pct"]].to_string(index=False))
cols = ["gov_agency_pct","corporate_pct","securitized_credit_pct","em_pct","credit_total_pct","ig_dur","hy_dur","hy_share_of_credit_risk"]
sty2 = fx.groupby("style")[cols].agg(["mean","median"]).round(2); sty2["funds"] = fx.groupby("style").size()
print("\nBY STYLE, excluding those funds"); print(sty2.to_string())
for col in ["gov_agency_pct","credit_total_pct","corporate_pct","securitized_credit_pct","hy_dur","hy_share_of_credit_risk"]:
    a, c = fx[fx["style"]=="Core"][col].dropna(), fx[fx["style"]=="Core-Plus"][col].dropna()
    print(f"  {col}: n={len(a)}/{len(c)} medians {a.median():.2f} vs {c.median():.2f}  p={stats.mannwhitneyu(a,c).pvalue:.3f}")
print("benchmark vs funds: credit_total mean (excl) %.1f vs benchmark ~25.3-26.0 ; securitized %.1f vs ~1.2 ; corporate %.1f vs ~23.3" % (fx.credit_total_pct.mean(), fx.securitized_credit_pct.mean(), fx.corporate_pct.mean()))
mapping = pd.DataFrame([("Government/agency (lower credit risk)", "US Treasury, TIPS, Agency/other government, Agency MBS, Non-US developed sovereign, Cash/short-term/repo"),
  ("Corporate (IG + HY not yet split)", "Corporate debt - needs Bloomberg ratings to split"), ("Securitized credit", "Non-agency MBS/CMBS, ABS/CLO"), ("EM", "Emerging-market sovereign and corporate (fixed country list)"),
  ("Other", "Municipal, derivatives (market value), unresolved"), ("Credit total", "Corporate + Securitized credit + EM"),
  ("IG / HY spread duration (years)", "Filed N-PORT sensitivities in economic sign; rows failing the plausibility screen removed"), ("HY share of credit risk", "HY spread duration / (|IG| + |HY|), a risk-based proxy; family conventions differ, treat with care")], columns=["bucket", "definition"])
with pd.ExcelWriter(f"{OUT}/risk_mix_provisional.xlsx") as w:
    f.to_excel(w, "by_fund", index=False); sty.to_excel(w, "by_style"); sty2.to_excel(w, "by_style_excl_unresolved"); fam.to_excel(w, "by_family"); bref.to_excel(w, "benchmark_reference"); mapping.to_excel(w, "definitions", index=False)
    pd.DataFrame({"note": ["Means are simple averages over each fund's complete-sector quarters, 2019-2026Q2; weights normalised to 100% by the repo's classification.",
      "Corporate is still IG+HY combined; the true IG/HY split by weight needs Bloomberg ratings.", "Filed spread durations are not comparable across fund families (Qiang, Oct 6); compare within a family or against the same family's index fund.",
      "Hy_share and hy_dur use only rows passing Anna's plausibility screen; funds with few usable quarters are noisy.", "Mapping of securitized credit, EM and cash to buckets is provisional pending the team's decision."]}).to_excel(w, "notes", index=False)
