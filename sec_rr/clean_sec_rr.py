"""
Clean the prospectus fee panel and expand it to a quarterly series x class panel.

Input:  intermediate/rr_fees_panel.csv (pull_sec_rr.py) + intermediate/rr_fees_pimco_supplement.csv (pull_pimco_gap.py)
Output:
  sec_rr_fees_panel.csv                     THE deliverable: series x quarter, keyed on (series_id, quarter)
  intermediate/rr_fees_quarterly_class.csv  same panel at share-class level, for reference
  intermediate/rr_fees_events_clean.csv     one row per prospectus fee table (series x class x filing), cleaned

Point-in-time rule: a fee table is used from the quarter in which it was FILED (not its effective date),
so a quarter only sees prospectuses that were public by quarter end. Values carry forward until the next
filing, for at most MAX_STALE_MONTHS; after that the class is treated as closed/merged.

Usage: python3 clean_sec_rr.py [--start 2011q1] [--end 2026q2]
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
INTER = HERE / "intermediate"
OUT = HERE
MAX_STALE_MONTHS = 24  # one missing annual prospectus
STALE_FLAG_MONTHS = 15
TOL = 0.0002  # fee tables are rounded to 0.01%

M, B, O, A = ("ManagementFeesOverAssets", "DistributionAndService12b1FeesOverAssets",
              "OtherExpensesOverAssets", "AcquiredFundFeesAndExpensesOverAssets")
G, W, N = "ExpensesOverAssets", "FeeWaiverOrReimbursementOverAssets", "NetExpensesOverAssets"
RENAME = {M: "mgmt_fee", B: "fee_12b1", O: "other_exp", A: "acquired_fund_exp", G: "gross_exp",
          W: "fee_waiver", N: "net_exp", "PortfolioTurnoverRate": "turnover",
          "MaximumSalesChargeImposedOnPurchasesOverOfferingPrice": "max_front_load",
          "MaximumDeferredSalesChargeOverOfferingPrice": "max_deferred_load",
          "RedemptionFeeOverRedemption": "redemption_fee"}
META = ["series", "group", "role", "style", "fund_name", "manager"]


def clean_events(p):
    p = p.copy()
    p["filed"] = pd.to_datetime(p["filed"], format="%Y%m%d")
    p["effdate"] = pd.to_datetime(p["effdate"], format="%Y%m%d", errors="coerce")
    notes = pd.Series("", index=p.index)

    def note(mask, text):
        notes.loc[mask] = notes.loc[mask] + text + ";"

    # 497 supplements that restate only part of the table carry no expense ratio: unusable
    p = p[p[G].notna() | p[N].notna()].copy()
    notes = notes.loc[p.index]

    # Waivers are reductions; OEF-era filers sometimes tag them positive
    m = p[W] > 0
    p.loc[m, W] = -p.loc[m, W]
    note(m, "waiver_sign_flipped")

    # Missing gross: rebuild from net and waiver, else from components
    m = p[G].isna() & p[N].notna()
    p.loc[m, G] = p.loc[m, N] - p.loc[m, W].fillna(0)
    note(m, "gross_from_net")

    # No 12b-1 / acquired-fund line in the table means none charged
    for col in (B, A):
        m = p[col].isna()
        p.loc[m, col] = 0.0
        note(m, f"{RENAME[col]}_missing_set_0")

    # Missing other expenses: residual of gross over the other components
    m = p[O].isna() & p[M].notna()
    p.loc[m, O] = (p.loc[m, G] - p.loc[m, [M, B, A]].sum(axis=1)).clip(lower=0).round(4)
    note(m, "other_exp_residual")

    # Waiver / net: fill whichever is missing; no waiver line means none
    m = p[W].isna() & p[N].notna()
    p.loc[m, W] = (p.loc[m, N] - p.loc[m, G]).clip(upper=0).round(4)
    note(m, "waiver_from_net")
    m = p[W].isna()
    p.loc[m, W] = 0.0
    note(m, "waiver_missing_set_0")
    m = p[N].isna()
    p.loc[m, N] = (p.loc[m, G] + p.loc[m, W]).round(4)
    note(m, "net_from_gross")

    p["has_waiver"] = p[W] < 0
    p["flag_components_mismatch"] = (p[[M, B, O, A]].sum(axis=1) - p[G]).abs() > TOL
    p["flag_net_mismatch"] = (p[G] + p[W] - p[N]).abs() > TOL
    p["clean_notes"] = notes.str.rstrip(";")

    # Same table filed more than once on a day (485BPOS + 497): keep the 485BPOS, else the last
    p["_form_rank"] = (p["form"] == "485BPOS").astype(int)
    p = (p.sort_values(["series", "class", "filed", "_form_rank", "adsh"])
          .drop_duplicates(["series", "class", "filed"], keep="last")
          .drop(columns="_form_rank"))
    return p.rename(columns=RENAME)


def quarter_ends(start, end):
    return pd.period_range(start.upper(), end.upper(), freq="Q")


def to_quarterly(ev, start, end):
    qs = quarter_ends(start, end)
    grid = pd.DataFrame({"quarter": qs, "quarter_end": qs.to_timestamp(how="end").normalize()})
    keys = ev[["series", "class"]].drop_duplicates()
    grid = keys.merge(grid, how="cross").sort_values("quarter_end")

    ev = ev.sort_values("filed")
    q = pd.merge_asof(grid, ev, left_on="quarter_end", right_on="filed",
                      by=["series", "class"], direction="backward")

    # Before a class's first filing in the sample: backfill only if the class already existed
    # when the data set starts (first filing within the first year), flagged as bfill
    first = ev.groupby(["series", "class"])["filed"].min().rename("first_filed")
    q = q.merge(first, on=["series", "class"])
    sample_start = grid["quarter_end"].min()
    early = q["filed"].isna() & (q["first_filed"] <= sample_start + pd.DateOffset(years=1))
    nxt = pd.merge_asof(grid, ev, left_on="quarter_end", right_on="filed",
                        by=["series", "class"], direction="forward")
    nxt = nxt.set_index(["series", "class", "quarter"])
    idx = q.loc[early].set_index(["series", "class", "quarter"]).index
    fill = nxt.loc[idx].reset_index()
    fill.index = q.index[early]
    cols = [c for c in ev.columns if c not in ("series", "class")]
    q.loc[early, cols] = fill[cols].values
    q["fill_method"] = np.where(early, "bfill",
                                np.where(q["filed"].dt.to_period("Q") == q["quarter"], "new_filing", "ffill"))

    q = q[q["filed"].notna()]
    q["months_since_filing"] = ((q["quarter_end"] - q["filed"]).dt.days / 30.44).round(1)
    q = q[(q["fill_method"] == "bfill") | (q["months_since_filing"] <= MAX_STALE_MONTHS)]
    q.loc[q["fill_method"] == "bfill", "months_since_filing"] = np.nan
    q["flag_stale"] = q["months_since_filing"] > STALE_FLAG_MONTHS
    q["quarter"] = q["quarter"].astype(str)
    return q.drop(columns="first_filed").sort_values(["series", "class", "quarter"])


def fund_summary(qc):
    """One row per series x quarter: the cheapest share class's full fee breakdown plus cross-class spread."""
    # Fully waived classes (net 0%, e.g. T. Rowe Z, Nuveen W) are internal fund-of-funds vehicles, not investable
    qc = qc[~((qc["net_exp"] <= 0.00005) & (qc["fee_waiver"] < 0))]
    g = qc.groupby(["series", "quarter"])
    s = g.agg(quarter_end=("quarter_end", "first"),
              n_classes=("class", "nunique"),
              net_exp_median=("net_exp", "median"),
              net_exp_max=("net_exp", "max"),
              share_classes_waived=("has_waiver", "mean"),
              months_since_filing=("months_since_filing", "max")).reset_index()
    # Cheapest class is usually the institutional one, the closest to the fund's pure management cost
    cols = ["class", "ticker", "mgmt_fee", "fee_12b1", "other_exp", "acquired_fund_exp",
            "gross_exp", "fee_waiver", "net_exp", "filed"]
    cheapest = qc.loc[g["net_exp"].idxmin(), ["series", "quarter"] + cols]
    cheapest = cheapest.rename(columns={"class": "inst_class", "ticker": "inst_ticker", "filed": "prospectus_filed"})
    s = s.merge(cheapest, on=["series", "quarter"])
    s = qc[META].drop_duplicates("series").merge(s, on="series")
    lead = META + ["quarter", "quarter_end", "inst_class", "inst_ticker", "mgmt_fee", "fee_12b1", "other_exp",
                   "acquired_fund_exp", "gross_exp", "fee_waiver", "net_exp", "n_classes", "net_exp_median",
                   "net_exp_max", "share_classes_waived", "prospectus_filed", "months_since_filing"]
    return s[lead].rename(columns={"series": "series_id"}).sort_values(["series_id", "quarter"])


def add_turnover(qf, turn):
    """Fund-level turnover (last fiscal year, as stated in the prospectus), same as-of-filing rule as fees."""
    turn = turn.assign(filed=pd.to_datetime(turn["filed"].astype(str), format="%Y%m%d"),
                       series_id=turn["series"])
    turn = turn.sort_values(["filed", "form"]).drop_duplicates(["series_id", "filed"], keep="last")
    qf = qf.assign(quarter_end=pd.to_datetime(qf["quarter_end"])).sort_values("quarter_end")
    qf = pd.merge_asof(qf, turn[["series_id", "filed", "turnover"]].sort_values("filed"),
                       left_on="quarter_end", right_on="filed", by="series_id", direction="backward")
    stale = (qf["quarter_end"] - qf["filed"]).dt.days / 30.44 > MAX_STALE_MONTHS
    qf.loc[stale, "turnover"] = np.nan
    qf["turnover_filed"] = qf["filed"].where(~stale)
    cols = list(qf.columns.drop(["filed", "turnover", "turnover_filed"]))
    at = cols.index("share_classes_waived") + 1
    cols[at:at] = ["turnover", "turnover_filed"]
    return qf[cols].sort_values(["series_id", "quarter"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2011q1")
    ap.add_argument("--end", default="2026q2")
    args = ap.parse_args()

    p = pd.read_csv(INTER / "rr_fees_panel.csv", dtype={"effdate": str, "filed": str, "ddate": str})
    sup = INTER / "rr_fees_pimco_supplement.csv"
    if sup.exists():
        p = pd.concat([p, pd.read_csv(sup, dtype={"effdate": str, "filed": str, "ddate": str})],
                      ignore_index=True)
    p = p.drop(columns=["flag_suspect_value"], errors="ignore")

    INTER.mkdir(exist_ok=True)
    ev = clean_events(p)
    ev.to_csv(INTER / "rr_fees_events_clean.csv", index=False)

    qc = to_quarterly(ev, args.start, args.end)
    lead = META + ["class", "ticker", "quarter", "quarter_end", "fill_method", "months_since_filing",
                   "adsh", "form", "filed"]
    fees = [c for c in RENAME.values() if c in qc.columns] + ["has_waiver"]
    flags = ["flag_stale", "flag_components_mismatch", "flag_net_mismatch", "clean_notes"]
    qc = qc[lead + fees + flags]
    qc.to_csv(INTER / "rr_fees_quarterly_class.csv", index=False)

    turn = pd.concat([pd.read_csv(f, dtype={"filed": str}) for f in
                      (INTER / "rr_turnover.csv", INTER / "rr_turnover_pimco_supplement.csv") if f.exists()])
    qf = add_turnover(fund_summary(qc), turn)
    # Model-ready: keys + numeric features only; fund names/styles join back from the universe file by series_id
    # fee_12b1 is dropped: the cheapest class never charges one, so it is constant 0
    qf = qf[["series_id", "quarter", "quarter_end", "mgmt_fee", "other_exp", "acquired_fund_exp",
             "gross_exp", "fee_waiver", "net_exp", "net_exp_median", "net_exp_max", "n_classes",
             "share_classes_waived", "turnover"]]
    qf.to_csv(OUT / "sec_rr_fees_panel.csv", index=False)

    print(f"events: {len(ev)} rows; components mismatch {ev['flag_components_mismatch'].sum()}, "
          f"net mismatch {ev['flag_net_mismatch'].sum()}")
    print(f"quarterly class panel: {len(qc)} rows, {qc['class'].nunique()} classes, {qc['series'].nunique()} series")
    print(qc["fill_method"].value_counts().to_string())
    print(f"quarterly fund panel: {len(qf)} rows")


if __name__ == "__main__":
    main()
