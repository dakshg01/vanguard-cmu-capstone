import sys, numpy as np, pandas as pd
from scipy import stats
S, R = sys.argv[1:3]; OUT = f"{S}/out"; C = f"{S}/anna-zip2/cleaned_data"
d = pd.read_csv(f"{R}/output/csv/derivative_pnl_latest.csv", encoding="utf-8-sig")
d["pnl"] = d.realized_pnl_usd.fillna(0) + d.unrealized_change_usd.fillna(0)
print("rows with blank instrument_kind (category subtotals duplicating a kind row):", d.instrument_kind.isna().sum()); d = d.dropna(subset=["instrument_kind"])
nd = d.duplicated(["series_id", "month_end", "asset_category", "instrument_kind"]).sum(); print("duplicate keys across overlapping filings, keeping earliest filing:", nd)
d = d.sort_values("filing_date").drop_duplicates(["series_id", "month_end", "asset_category", "instrument_kind"], keep="first")
p = pd.read_csv(f"{R}/analysis/results/positioning_panel.csv", usecols=["series_id", "accession_number", "net_assets"]).drop_duplicates(["series_id", "accession_number"])
d = d.merge(p, on=["series_id", "accession_number"], how="left"); print("rows without net assets:", d.net_assets.isna().sum(), "of", len(d))
d = d.dropna(subset=["net_assets"]); d = d[d.net_assets > 0]
def grp(r):
    a, k = r.asset_category, r.instrument_kind
    if a == "Interest Rate Contracts": return "ir_futures" if k == "Future Category" else "ir_swaps" if k == "Swap Category" else "ir_options" if k in ("Option Category", "Swaption Category") else "ir_other"
    if a == "Credit Contracts": return "credit_swaps" if k == "Swap Category" else "credit_options" if k in ("Option Category", "Swaption Category") else "credit_other"
    if a == "Foreign Exchange Contracts": return "fx"
    return "other_deriv"
k = d[["asset_category", "instrument_kind"]].drop_duplicates(); k["bucket"] = k.apply(grp, axis=1); d = d.merge(k, on=["asset_category", "instrument_kind"])
d["bp"] = d.pnl / d.net_assets * 1e4
mo = d.pivot_table(index=["series_id", "month_end"], columns="bucket", values="bp", aggfunc="sum", fill_value=0).reset_index()
B = [c for c in mo.columns if c not in ("series_id", "month_end")]; core = [c for c in B if c != "fx"]; mo["total"] = mo[core].sum(axis=1); mo["date"] = pd.PeriodIndex(pd.to_datetime(mo.month_end), freq="M")
mo = mo[(mo.date >= "2019-07") & (mo.date <= "2026-06")]
def ann(g): return pd.Series({**{c: g[c].mean() * 12 for c in B + ["total"]}, "months": len(g), "gross_abs_bp_ann": g[[c for c in B if c != "fx"]].abs().sum(axis=1).mean() * 12})
byf = mo.groupby("series_id").apply(ann, include_groups=False).reset_index()
u = pd.read_csv(f"{C}/4_reference/universe.csv", dtype=str); u = u[u.group == "PRIMARY"][["series_id", "fund_name", "manager", "style"]]
byf = u.merge(byf, on="series_id", how="left"); print("primary funds with deriv P&L rows:", byf.total.notna().sum(), "of", len(byf))
# window persistence
w1 = mo[mo.date <= "2022-12"].groupby("series_id").apply(ann, include_groups=False); w2 = mo[mo.date >= "2023-01"].groupby("series_id").apply(ann, include_groups=False)
pers = []
for c in B + ["total", "gross_abs_bp_ann"]:
    j = w1[[c, "months"]].join(w2[[c, "months"]], lsuffix="1", rsuffix="2", how="inner"); j = j[(j.months1 >= 24) & (j.months2 >= 24)]
    if len(j) >= 15 and j[c + "1"].nunique() > 2:
        r, pv = stats.spearmanr(j[c + "1"], j[c + "2"]); pers.append(dict(measure=c, n=len(j), spearman=round(r, 3), p=round(pv, 3)))
pers = pd.DataFrame(pers); print("\nPERSISTENCE of derivative P&L between 2019-22 and 2023-26"); print(pers.to_string(index=False))
sty = byf.groupby("style")[B + ["total", "gross_abs_bp_ann"]].agg(["mean"]).round(1); sty.columns = [c[0] for c in sty.columns]; print("\nBY STYLE (bp of net assets per year)"); print(sty.to_string())
fam = byf.groupby("manager")[["ir_futures", "ir_swaps", "ir_options", "credit_swaps", "fx", "total", "gross_abs_bp_ann"]].mean().round(1).sort_values("gross_abs_bp_ann", ascending=False); print("\nTOP FAMILIES by gross derivative P&L"); print(fam.head(10).to_string())
print("\nFUND-LEVEL distribution of annual total derivative P&L (bp):", byf.total.describe().round(1).to_dict())
print("funds with ~no derivative P&L (gross<5bp):", int((byf.gross_abs_bp_ann < 5).sum()))
cmp = byf.sort_values("gross_abs_bp_ann", ascending=False).head(8)[["fund_name", "ir_futures", "ir_swaps", "credit_swaps", "fx", "total", "gross_abs_bp_ann"]].round(0); print(cmp.to_string(index=False))
with pd.ExcelWriter(f"{OUT}/derivative_pnl_layer.xlsx") as w:
    byf.round(2).to_excel(w, "by_fund", index=False); sty.to_excel(w, "by_style"); fam.to_excel(w, "by_family"); pers.to_excel(w, "persistence", index=False)
    mo.to_csv(f"{OUT}/derivative_pnl_monthly.csv", index=False)
    pd.DataFrame({"note": ["Source: repo output/csv/derivative_pnl_latest.csv (monthly realized + unrealized derivative P&L by asset category x instrument kind, unpacked from quarterly N-PORT).", "Scaled by net assets at the filing's report date (accession-level), shown as bp of net assets per year. Approximation: ignores intra-quarter asset changes.",
     "Buckets: ir_futures, ir_swaps, ir_options (options+swaptions), credit_swaps, credit_options, fx, other_deriv.", "FX forward/swap P&L is shown but EXCLUDED from total and gross: it is the hedge leg only (e.g. Vanguard Core Bond shows +300 to +500 bp per month in 2020-21) and its offset sits in the foreign-currency bond holdings, so it is not interpretable alone.", "P&L is a result of positions and market moves. It shows how much each derivative type contributed, NOT the size of the risk. Risk (DV01) is already included in the filed total rate sensitivity; do not add.",
     "A fund using futures to hedge duration will show losses in rising-rate periods that are offset by cash bonds. Do not read derivative P&L as skill or alpha.", "Notionals, direction and maturity of swaps/futures need the SQLite tables (nonforeign_exchange_swap_latest, fut_fwd_nonforeigncur_contract_latest) - see export script.",
     "Window 1 = 2019-07..2022-12, window 2 = 2023-01..2026-06; persistence needs >=24 months in each."]}).to_excel(w, "notes", index=False)
