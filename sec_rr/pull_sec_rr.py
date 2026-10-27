"""
Pull SEC Mutual Fund Prospectus Risk/Return Summary data sets and filter to the capstone fund universe.

Source: https://www.sec.gov/data-research/sec-markets-data/mutual-fund-prospectus-riskreturn-summary-data-sets
Each quarterly zip has sub.tsv (one row per filing) and num.tsv (numeric XBRL facts by series/class).

Outputs (in ./intermediate, inputs to clean_sec_rr.py):
  rr_fees_panel.csv               one row per filing x series x class, key fee/expense fields as columns
  rr_num_universe_long.csv        every numeric fact for universe series (incl. returns), for reference
  class_series_votes.csv          how often each share class is tagged with each series, market-wide
  dropped_mistagged_classes.csv   class-filings dropped because the filer tagged them to the wrong series

Usage: python3 pull_sec_rr.py [--start 2010q4] [--end 2026q2]
"""
import argparse
import json
import time
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

BASE = "https://www.sec.gov/files/dera/data/mutual-fund-prospectus-risk/return-summary-data-sets/{q}_rr1.zip"
TICKERS_URL = "https://www.sec.gov/files/company_tickers_mf.json"
# SEC asks for a descriptive User-Agent with contact info; replace with your own email if requests get blocked
USER_AGENT = "MSCF-Capstone research admin@example.com"

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"
INTER = HERE / "intermediate"
UNIVERSE = HERE.parent / "universe.csv"

FEE_TAGS = [
    "ManagementFeesOverAssets",
    "DistributionAndService12b1FeesOverAssets",
    "OtherExpensesOverAssets",
    "AcquiredFundFeesAndExpensesOverAssets",
    "ExpensesOverAssets",  # total annual fund operating expenses (gross)
    "FeeWaiverOrReimbursementOverAssets",
    "NetExpensesOverAssets",  # after waiver/reimbursement
    "PortfolioTurnoverRate",
    "MaximumSalesChargeImposedOnPurchasesOverOfferingPrice",
    "MaximumDeferredSalesChargeOverOfferingPrice",
    "RedemptionFeeOverRedemption",
]
SUB_COLS = ["adsh", "cik", "name", "form", "filed", "effdate", "pdate", "fye"]


def quarters(start, end):
    y, q = int(start[:4]), int(start[-1])
    ey, eq = int(end[:4]), int(end[-1])
    while (y, q) <= (ey, eq):
        yield f"{y}q{q}"
        y, q = (y + 1, 1) if q == 4 else (y, q + 1)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.read()


def download(q):
    path = RAW / f"{q}_rr1.zip"
    if path.exists() and zipfile.is_zipfile(path):
        return path
    print(f"  downloading {q} ...", flush=True)
    data = fetch(BASE.format(q=q))
    path.write_bytes(data)
    time.sleep(0.5)  # stay well under SEC's 10 req/s limit
    return path


def read_tsv(z, name, **kw):
    return pd.read_csv(z.open(name), sep="\t", dtype=str, keep_default_na=False, na_values=[""], **kw)


def process_quarter(q, series_ids):
    """Universe facts, plus class-level facts with a blank series column (OEF taxonomy) to be mapped later."""
    with zipfile.ZipFile(download(q)) as z:
        num = read_tsv(z, "num.tsv")
        sub = read_tsv(z, "sub.tsv", usecols=lambda c: c in SUB_COLS)
    # OEF taxonomy (2024+) puts the share class in otherdims ("Class=C000002163;") and leaves series blank
    dim_class = num["otherdims"].str.extract(r"(?:^|;)Class=(C\d+);", expand=False)
    num["class"] = num["class"].fillna(dim_class)
    num["otherdims"] = (num["otherdims"].str.replace(r"(?:^|(?<=;))Class=C\d+;", "", regex=True)
                        .replace("", pd.NA))
    # Every (filing, series, class) in the whole market, used to vote on which series a class belongs to
    pairs = num.dropna(subset=["series", "class"])[["adsh", "series", "class"]].drop_duplicates()
    num = num[num["series"].isin(series_ids) | (num["series"].isna() & num["class"].notna())]
    num = num.merge(sub, on="adsh", how="left")
    num.insert(0, "dataset_quarter", q)
    return num, pairs


def class_tickers():
    cache = RAW / "company_tickers_mf.json"
    try:
        cache.write_bytes(fetch(TICKERS_URL))
    except Exception as e:
        print(f"  ticker map download failed ({e}); using cache" if cache.exists() else f"  ticker map unavailable: {e}")
    if not cache.exists():
        return pd.DataFrame(columns=["series", "class", "ticker"])
    js = json.loads(cache.read_bytes())
    df = pd.DataFrame(js["data"], columns=js["fields"])
    df = df.rename(columns={"seriesId": "series", "classId": "class", "symbol": "ticker"})
    return df[["series", "class", "ticker"]].drop_duplicates(["series", "class"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2010q4")
    ap.add_argument("--end", default="2026q2")
    args = ap.parse_args()
    RAW.mkdir(exist_ok=True)
    INTER.mkdir(exist_ok=True)

    uni = pd.read_csv(UNIVERSE, dtype=str, encoding="utf-8-sig")
    series_ids = set(uni["series_id"])
    meta = uni[["series_id", "group", "role", "style", "fund_name", "manager"]].rename(columns={"series_id": "series"})

    frames, pair_frames = [], []
    for q in quarters(args.start, args.end):
        try:
            df, pairs = process_quarter(q, series_ids)
        except Exception as e:
            print(f"  {q}: FAILED ({e})")
            continue
        frames.append(df)
        pair_frames.append(pairs)

    long = pd.concat(frames, ignore_index=True)
    # A class's true series = the series it is tagged with in most filings market-wide. Filers occasionally
    # tag a class under the wrong series (e.g. an equity fund's classes under Diamond Hill Core Bond in 2011)
    tickers = class_tickers()
    # Only real EDGAR class ids vote; filer labels like "Class529F2" are reused across many series
    pairs = pd.concat(pair_frames)
    votes = (pairs[pairs["class"].str.match(r"C\d+$")].drop_duplicates()
               .groupby(["class", "series"]).size().rename("n_filings").reset_index()
               .sort_values(["class", "n_filings"], ascending=[True, False]))
    class_map = votes.drop_duplicates("class").set_index("class")["series"]
    class_map = pd.concat([class_map, tickers.drop_duplicates("class").set_index("class")["series"]])
    class_map = class_map[~class_map.index.duplicated()]
    votes.to_csv(INTER / "class_series_votes.csv", index=False)

    long["series"] = long["series"].fillna(long["class"].map(class_map))
    true_series = long["class"].map(class_map)
    mistagged = long["class"].notna() & true_series.notna() & (true_series != long["series"])
    if mistagged.any():
        bad = long[mistagged].groupby(["series", "class", "adsh"]).size().reset_index()
        print(f"  dropping {mistagged.sum()} facts from {len(bad)} class-filings tagged to the wrong series")
        bad.to_csv(INTER / "dropped_mistagged_classes.csv", index=False)
    long = long[~mistagged & long["series"].isin(series_ids)]
    for q, df in long.groupby("dataset_quarter"):
        print(f"  {q}: {len(df):6d} facts, {df['series'].nunique():2d} series", flush=True)

    long["value_num"] = pd.to_numeric(long["value"], errors="coerce")
    long = meta.merge(long, on="series", how="right")
    long.to_csv(INTER / "rr_num_universe_long.csv", index=False)

    # Fee panel: plain facts only (no extra dimensions), one row per filing x series x class
    keys = ["series", "class", "adsh", "dataset_quarter", "form", "filed", "effdate", "ddate"]
    plain = long[long["tag"].isin(FEE_TAGS) & long["otherdims"].isna() & long["class"].notna()]
    # pivot_table silently drops rows with a missing key; most OEF filings have no effdate
    panel = (plain.fillna({k: "" for k in keys})
                  .pivot_table(index=keys, columns="tag", values="value_num", aggfunc="first")
                  .reset_index().replace({k: {"": pd.NA} for k in keys}))
    panel.columns.name = None
    panel = meta.merge(panel, on="series", how="right").merge(tickers, on=["series", "class"], how="left")
    panel = panel[[c for c in meta.columns] + ["class", "ticker"] + keys[2:] +
                  [t for t in FEE_TAGS if t in panel.columns]]
    # Expense ratios above 5% in a bond fund are tagging errors (percent entered as a number); flag, don't drop
    ratio_cols = [t for t in FEE_TAGS if t.endswith("OverAssets") and t in panel.columns]
    panel["flag_suspect_value"] = (panel[ratio_cols].abs() > 0.05).any(axis=1)
    panel = panel.sort_values(["series", "class", "filed", "adsh"])
    panel.to_csv(INTER / "rr_fees_panel.csv", index=False)

    # Turnover is reported once per fund (no share class), one row per filing x series
    turn = long[(long["tag"] == "PortfolioTurnoverRate") & long["class"].isna() & long["otherdims"].isna()]
    turn = (turn.rename(columns={"value_num": "turnover"})
                .drop_duplicates(["series", "adsh"])[["series", "adsh", "form", "filed", "turnover"]])
    turn.sort_values(["series", "filed"]).to_csv(INTER / "rr_turnover.csv", index=False)

    missing = series_ids - set(long["series"])
    print(f"\n{long['series'].nunique()}/{len(series_ids)} universe series found; {len(panel)} panel rows")
    if missing:
        print("Never found:", uni[uni["series_id"].isin(missing)][["series_id", "fund_name"]].to_string(index=False))


if __name__ == "__main__":
    main()
