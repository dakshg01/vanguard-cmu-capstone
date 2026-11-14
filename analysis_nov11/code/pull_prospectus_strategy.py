"""Pull each primary fund's latest prospectus and extract mandate limits + portfolio managers.
Run locally (the SEC blocks cloud sandboxes). From the repo root:
    pip install requests pandas
    python pull_prospectus_strategy.py universe.csv prospectus_strategy.csv
Set SEC_UA below to 'Your Name your.email@cmu.edu' (SEC requires a contact in the User-Agent).
Output is for MANUAL REVIEW: registrant filings cover many funds, section matching is heuristic.
"""
import sys, re, time, json, html, pathlib, requests, pandas as pd
SEC_UA = "Caroline Liu YOUR_EMAIL@andrew.cmu.edu"
H = {"User-Agent": SEC_UA, "Accept-Encoding": "gzip, deflate"}
CACHE = pathlib.Path("prospectus_cache"); CACHE.mkdir(exist_ok=True)
KEY = re.compile(r"below investment[- ]grade|high[- ]yield|junk|non-U\.S\.|foreign|emerging|derivative|futures|swap|mortgage|asset-backed|TBA|"
                 r"duration|dollar roll|leverage|illiquid|credit rating|\bBaa\b|\bBBB\b|\bBB\b", re.I)
LIMIT = re.compile(r"(up to|no more than|at most|maximum of|not exceed|at least|minimum of|normally invests?)[^.]{0,120}?\d+(\.\d+)?\s?%[^.]*\.", re.I)

def get(url, name):
    f = CACHE / name
    if f.exists(): return f.read_text(errors="ignore")
    time.sleep(0.15); r = requests.get(url, headers=H, timeout=60); r.raise_for_status(); f.write_text(r.text); return r.text

def latest_prospectus(cik):
    j = json.loads(get(f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json", f"sub_{int(cik)}.json"))
    rec = j["filings"]["recent"]; rows = [(d, f, a, p) for d, f, a, p in zip(rec["filingDate"], rec["form"], rec["accessionNumber"], rec["primaryDocument"]) if f in ("485BPOS", "497")]
    rows.sort(reverse=True)
    for d, f, a, p in rows:                      # newest first; skip tiny supplements
        url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{a.replace('-', '')}/{p}"
        txt = get(url, f"{a}_{p}.txt")
        if len(txt) > 200_000: return d, f, url, txt
    return None

def clean(h):
    h = re.sub(r"(?is)<(script|style).*?</\1>", " ", h); h = re.sub(r"(?s)<[^>]+>", " ", h)
    return re.sub(r"\s+", " ", html.unescape(h))

def fund_section(text, name):
    core = re.sub(r"\b(Fund|Portfolio|Class|Bond|Trust)\b", "", name, flags=re.I).strip()
    pos = [m.start() for m in re.finditer(re.escape(name), text, re.I)] or [m.start() for m in re.finditer(re.escape(core), text, re.I)]
    for m in re.finditer(r"principal (investment )?strateg", text, re.I):
        prior = [p for p in pos if p < m.start()]
        if prior and m.start() - prior[-1] < 6000: return text[m.start(): m.start() + 12000]
    return ""

u = pd.read_csv(sys.argv[1], encoding="utf-8-sig", dtype=str); u = u[u.group == "PRIMARY"]
out = []
for _, r in u.iterrows():
    try:
        res = latest_prospectus(r.cik)
        if not res: out.append(dict(series_id=r.series_id, fund_name=r.fund_name, status="no prospectus found")); continue
        d, f, url, raw = res; sec = fund_section(clean(raw), r.fund_name)
        sents = re.split(r"(?<=[.;])\s+", sec)
        pm = re.search(r"Portfolio Managers?[: ].{0,500}", clean(raw)[clean(raw).find(r.fund_name):], re.I) if sec else None
        out.append(dict(series_id=r.series_id, fund_name=r.fund_name, filing_date=d, form=f, url=url, status="ok" if sec else "section not found - read manually",
                        limits=" | ".join(m.group(0) for m in LIMIT.finditer(sec))[:1500], key_sentences=" | ".join(s for s in sents if KEY.search(s))[:3000],
                        portfolio_managers=(pm.group(0)[:500] if pm else "")))
    except Exception as e: out.append(dict(series_id=r.series_id, fund_name=r.fund_name, status=f"error: {e}"))
    print(r.fund_name, out[-1]["status"])
pd.DataFrame(out).to_csv(sys.argv[2], index=False, encoding="utf-8-sig")
