"""Clean Bloomberg HP (Historical Price Table) copy-paste exports into tidy CSVs.

Usage:
    python clean_bbg_rates.py MAIN_XLSX [--backfill OLD_XLSX] [--out DIR]

MAIN_XLSX   Workbook with one or more HP pages pasted into it. Pages may be one
            per sheet or stacked vertically in one sheet.
--backfill  Optional older workbook. Govt yields (``... Index`` tickers) on dates
            missing from MAIN_XLSX are taken from it; overlapping points must match.
--out       Output directory (default: this script's folder).

Each HP page is: a title row ("Historical Price Table  <TICKER>  Export ..."),
a summary block, a header row, then three side-by-side 4-column blocks
(date, H/L flag, Last Price, Bid Price). US Treasury futures are quoted in 32nds
(e.g. 107-20¾) and are converted to decimals.
"""
import argparse
import re
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

FRAC = {"": 0, "+": 0.5, "¼": 0.25, "½": 0.5, "¾": 0.75,
        "⅛": 0.125, "⅜": 0.375, "⅝": 0.625, "⅞": 0.875}

# field -> (asset_class, market, tenor); also fixes column order
INFO = {
    "USGG2YR": ("govt_yield", "US", "2Y"), "USGG10YR": ("govt_yield", "US", "10Y"),
    "USGG30YR": ("govt_yield", "US", "30Y"),
    "GJGB2": ("govt_yield", "JP", "2Y"), "GJGB10": ("govt_yield", "JP", "10Y"),
    "GJGB30": ("govt_yield", "JP", "30Y"),
    "GDBR2": ("govt_yield", "DE", "2Y"), "GDBR10": ("govt_yield", "DE", "10Y"),
    "GDBR30": ("govt_yield", "DE", "30Y"),
    "USSW2": ("swap_rate", "US", "2Y"), "USSW10": ("swap_rate", "US", "10Y"),
    "USSW30": ("swap_rate", "US", "30Y"),
    "EUSA2": ("swap_rate", "EU", "2Y"), "EUSA10": ("swap_rate", "EU", "10Y"),
    "EUSA30": ("swap_rate", "EU", "30Y"),
    "JYSO2": ("swap_rate", "JP", "2Y"), "JYSO10": ("swap_rate", "JP", "10Y"),
    "JYSO30": ("swap_rate", "JP", "30Y"),
    "TU1": ("bond_future", "US", "2Y"), "TY1": ("bond_future", "US", "10Y"),
    "US1": ("bond_future", "US", "30Y"), "JB1": ("bond_future", "JP", "10Y"),
    "RX1": ("bond_future", "DE", "10Y"),
}

# Known bad Bloomberg values, blanked after parsing: (bbg_ticker, date, column)
BAD = [("TU1 COMB Comdty", "2022-12-30", "bid")]  # bid 85-00 vs last 102-16


def num(c):
    if isinstance(c, (int, float)):
        return float(c)
    c = str(c).strip()
    if c in ("", "nan"):
        return np.nan
    m = re.fullmatch(r"(\d+)-(\d{2})([+¼½¾⅛⅜⅝⅞]?)", c)
    if not m:
        raise ValueError(f"unparsed price {c!r}")
    return int(m[1]) + (int(m[2]) + FRAC[m[3]]) / 32


def parse_page(v, s):
    tk = re.search(r"Historical Price Table\s+(.+?)\s{2,}", s.iat[0, 0]).group(1).strip()
    txt = " ".join(s.values.ravel())
    assert txt.count("Historical Price Table") == 1 and "Page 1/1" in txt, tk
    hr = [i for i in range(len(v)) if s.iat[i, 0] == "Date"]
    assert len(hr) == 1, (tk, hr)
    hr = hr[0]
    assert list(s.iloc[hr, :9]) == ["Date", "Last Price", "Bid Price"] * 3, tk
    cur = re.search(r"Currency\s+(\w+)", txt).group(1)
    r0, r1 = re.search(r"Range\s+(\S+)\s+-\s+(\S+)", txt).groups()
    recs = []
    for dc in (0, 4, 8):
        for i in range(hr + 1, len(v)):
            d = v.iat[i, dc]
            if not isinstance(d, datetime):
                assert str(d).strip() in ("", "nan"), (tk, i, dc, d)
                continue
            assert str(v.iat[i, dc + 1]).strip() in ("", "H", "L", "nan"), (tk, i)
            last, bid = num(v.iat[i, dc + 2]), num(v.iat[i, dc + 3])
            if np.isnan(last) and np.isnan(bid):
                continue
            recs.append(dict(date=pd.Timestamp(d), ticker=tk, last=last, bid=bid))
    expected = len(pd.date_range(pd.Timestamp(r0) - pd.offsets.QuarterEnd(0),
                                 pd.Timestamp(r1), freq="QE"))
    return recs, dict(ticker=tk, currency=cur, range=f"{r0}-{r1}",
                      expected_q=expected, n=len(recs))


def parse_workbook(path):
    recs, meta = [], []
    for _, V in pd.read_excel(path, sheet_name=None, header=None).items():
        assert V.shape[1] == 12, V.shape
        S = V.astype(str)
        starts = [i for i in range(len(V)) if "Historical Price Table" in S.iat[i, 0]]
        for a, b in zip(starts, starts[1:] + [len(V)]):
            r, m = parse_page(V.iloc[a:b].reset_index(drop=True),
                              S.iloc[a:b].reset_index(drop=True))
            recs += r
            meta.append(m)
    L, M = pd.DataFrame(recs), pd.DataFrame(meta)
    assert not L.duplicated(["date", "ticker"]).any()
    return L, M


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("main_xlsx")
    ap.add_argument("--backfill")
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent))
    a = ap.parse_args()

    L, M = parse_workbook(a.main_xlsx)
    print(M.to_string())
    if a.backfill:
        O, _ = parse_workbook(a.backfill)
        both = L.merge(O, on=["date", "ticker"], suffixes=("", "_o"))
        assert np.allclose(both["last"], both["last_o"], equal_nan=True), "backfill mismatch"
        key = L.set_index(["date", "ticker"]).index
        add = O[O.ticker.str.endswith("Index")
                & ~O.set_index(["date", "ticker"]).index.isin(key)]
        print(f"backfilled {len(add)} rows; {len(both)} overlapping points identical")
        L = pd.concat([L, add], ignore_index=True)

    for tk, d, col in BAD:
        L.loc[(L.ticker == tk) & (L.date == d), col] = np.nan

    L["field"] = L.ticker.str.split().str[0]
    unknown = set(L.field) - set(INFO)
    assert not unknown, f"add to INFO: {unknown}"
    L["asset_class"] = L.field.map(lambda f: INFO[f][0])
    L["market"] = L.field.map(lambda f: INFO[f][1])
    L["tenor"] = L.field.map(lambda f: INFO[f][2])
    L = L.merge(M[["ticker", "currency"]], on="ticker")
    L = L.rename(columns={"ticker": "bbg_ticker", "last": "px_last", "bid": "px_bid"})
    order = list(INFO)
    L["_o"] = L.field.map(order.index)
    L = L.sort_values(["_o", "date"]).drop(columns="_o")
    L["date"] = L.date.dt.strftime("%Y-%m-%d")

    out = Path(a.out)
    cols = ["date", "field", "bbg_ticker", "asset_class", "market", "tenor",
            "currency", "px_last", "px_bid"]
    L[cols].to_csv(out / "bbg_rates_quarterly_long.csv", index=False)
    W = L.pivot(index="date", columns="field", values="px_last")
    W[[f for f in order if f in W]].to_csv(out / "bbg_rates_quarterly_wide.csv")
    print(f"wrote {len(L)} long rows, wide {W.shape} to {out}")


if __name__ == "__main__":
    main()
