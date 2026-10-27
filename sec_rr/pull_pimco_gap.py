"""
Fill PIMCO's 2025+ fee tables, which are missing from the SEC risk/return data sets, by parsing the
inline XBRL in PIMCO Funds' annual 485BPOS prospectuses straight from EDGAR.

Output (clean_sec_rr.py picks both up):
  intermediate/rr_fees_pimco_supplement.csv      same columns as intermediate/rr_fees_panel.csv
  intermediate/rr_turnover_pimco_supplement.csv  same columns as intermediate/rr_turnover.csv
Add a FILINGS row when PIMCO files its next annual prospectus (each July).

Usage: python3 pull_pimco_gap.py
"""
import json
import re
import time

import pandas as pd

from pull_sec_rr import FEE_TAGS, INTER, RAW, UNIVERSE, fetch

# (accession, primary document, filed) for PIMCO Funds (CIK 810893) annual prospectuses
CIK = "810893"
FILINGS = [
    ("0001193125-25-166715", "d943766d485bpos.htm", "20250729"),
    ("0001193125-26-321271", "d105159d485bpos.htm", "20260728"),
]
SERIES = {"S000009707", "S000016548"}  # PIMCO Total Return, PIMCO Income

CONTEXT_RE = re.compile(r'<xbrli:context id="([^"]+)">(.*?)</xbrli:context>', re.S)
MEMBER_RE = re.compile(r'<xbrldi:explicitMember dimension="([^"]+)">[^:<]*:([^<]+)</xbrldi:explicitMember>')
FACT_RE = re.compile(r"<ix:nonFraction([^>]*)>(.*?)</ix:nonFraction>", re.S)
ATTR_RE = re.compile(r'([\w:]+)="([^"]*)"')


def contexts(doc):
    """context id -> (series, class) for series x class contexts, and (series, None) for series-only ones."""
    out = {}
    for cid, body in CONTEXT_RE.findall(doc):
        dims = dict(MEMBER_RE.findall(body))
        if set(dims) == {"dei:LegalEntityAxis", "oef:ClassAxis"}:
            out[cid] = (dims["dei:LegalEntityAxis"].removesuffix("Member"),
                        dims["oef:ClassAxis"].removesuffix("Member"))
        elif set(dims) == {"dei:LegalEntityAxis"}:
            out[cid] = (dims["dei:LegalEntityAxis"].removesuffix("Member"), None)
    return out


def facts(doc, ctx):
    rows = []
    for attrs, inner in FACT_RE.findall(doc):
        a = dict(ATTR_RE.findall(attrs))
        tag = a.get("name", "").split(":")[-1]
        if tag not in FEE_TAGS or a.get("contextRef") not in ctx or a.get("xsi:nil") == "true":
            continue
        text = re.sub(r"<[^>]+>", "", inner).strip().replace(",", "")
        if a.get("format", "").endswith("fixed-zero") or text in ("—", "–", "-", "None"):
            value = 0.0
        else:
            value = float(text) * 10 ** int(a.get("scale", "0"))
        if a.get("sign") == "-":
            value = -value
        series, cls = ctx[a["contextRef"]]
        rows.append({"series": series, "class": cls, "tag": tag, "value": round(value, 6)})
    return rows


def main():
    cache = RAW / "edgar"
    cache.mkdir(parents=True, exist_ok=True)
    uni = pd.read_csv(UNIVERSE, dtype=str, encoding="utf-8-sig")
    meta = uni[["series_id", "group", "role", "style", "fund_name", "manager"]].rename(columns={"series_id": "series"})

    rows = []
    for adsh, doc_name, filed in FILINGS:
        path = cache / f"{adsh}_{doc_name}"
        if not path.exists():
            url = f"https://www.sec.gov/Archives/edgar/data/{CIK}/{adsh.replace('-', '')}/{doc_name}"
            path.write_bytes(fetch(url))
            time.sleep(1)
        doc = path.read_text(encoding="utf-8", errors="replace")
        found = [r for r in facts(doc, contexts(doc)) if r["series"] in SERIES]
        print(f"  {adsh}: {len(found)} fee facts for {len({r['class'] for r in found} - {None})} classes")
        for r in found:
            rows.append({**r, "adsh": adsh, "dataset_quarter": "edgar_ixbrl", "form": "485BPOS", "filed": filed})

    long = pd.DataFrame(rows)
    turn = long[long["class"].isna() & (long["tag"] == "PortfolioTurnoverRate")]
    turn = turn.rename(columns={"value": "turnover"})[["series", "adsh", "form", "filed", "turnover"]]
    turn.to_csv(INTER / "rr_turnover_pimco_supplement.csv", index=False)
    print(f"wrote {len(turn)} turnover rows")

    long = long[long["class"].notna()]
    keys = ["series", "class", "adsh", "dataset_quarter", "form", "filed"]
    panel = long.pivot_table(index=keys, columns="tag", values="value", aggfunc="first").reset_index()
    panel.columns.name = None

    tickers = RAW / "company_tickers_mf.json"
    if tickers.exists():
        js = json.loads(tickers.read_bytes())
        t = pd.DataFrame(js["data"], columns=js["fields"]).rename(
            columns={"seriesId": "series", "classId": "class", "symbol": "ticker"})
        panel = panel.merge(t[["series", "class", "ticker"]].drop_duplicates(["series", "class"]),
                            on=["series", "class"], how="left")
    panel = meta.merge(panel, on="series", how="right")
    panel.to_csv(INTER / "rr_fees_pimco_supplement.csv", index=False)
    print(f"wrote {len(panel)} rows")


if __name__ == "__main__":
    main()
