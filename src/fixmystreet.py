"""Download fly-tipping reports from the FixMyStreet Open311 API (mySociety).

The public GeoReport v2 endpoint returns at most 1,000 reports per request and
filters by one category (service_code) and a date window. Categories are set by
each council, so fly-tipping appears under hundreds of names. The pipeline is:

1. discover: pull every report for one day a month (2012 onward) and tally the
   categories, so retired categories are found as well as current ones;
2. classify categories as fly-tipping by name (FLYTIP / EXCLUDE patterns);
3. download: for each fly-tipping category and year, fetch the year in one
   window, halving the window whenever it hits the 1,000 cap.

Requests are spaced out (REQUEST_GAP_S) to be gentle on mySociety's servers.
Raw reports contain free text from the public, so they stay in data/raw/ and only
aggregates are published."""
import json
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "fixmystreet"
API = "https://www.fixmystreet.com/open311/v2/requests.json"
HEADERS = {"User-Agent": "litter-research/0.1 (academic analysis of fly-tipping)"}
REQUEST_GAP_S = 1.0
CAP = 1000
YEARS = range(2012, 2026)

FLYTIP = re.compile(r"fly.?tip|flytip|fly.?tipped|dumped|dumping|illegal.?dump|abandoned (?:rubbish|waste|items|material)"
                    r"|side waste|rubbish left|waste left|bulky.*(?:dump|street|pavement)", re.I)
EXCLUDE = re.compile(r"fly.?post|poster|vehicle|car\b|cars\b|bike|cycle|trolley|needle|syringe|dog|"
                     r"graffiti|boat|caravan|animal|carcass|shopping", re.I)

_session = requests.Session()
_session.headers.update(HEADERS)


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch(start: datetime, end: datetime, code: str | None = None) -> list[dict]:
    params = {"jurisdiction_id": "fixmystreet.com", "start_date": _iso(start), "end_date": _iso(end)}
    if code:
        params["service_code"] = code
    for attempt in range(6):
        time.sleep(REQUEST_GAP_S * (2 ** attempt if attempt else 1))
        try:
            r = _session.get(API, params=params, timeout=120)
            if r.ok:
                return r.json().get("service_requests", [])
        except (requests.RequestException, ValueError):
            pass
    raise RuntimeError(f"FixMyStreet request failed: {params}")


def fetch_window(start: datetime, end: datetime, code: str | None = None) -> list[dict]:
    """All reports in [start, end), splitting the window while it hits the cap."""
    rows = fetch(start, end, code)
    if len(rows) < CAP or end - start <= timedelta(minutes=10):
        return rows
    mid = start + (end - start) / 2
    return fetch_window(start, mid, code) + fetch_window(mid, end, code)


def discover(sample_day: int = 10) -> pd.DataFrame:
    """Category counts from one full day a month across YEARS."""
    out = RAW / "categories_sample.csv"
    if out.exists():
        return pd.read_csv(out)
    recs = []
    for y in YEARS:
        for m in range(1, 13):
            day = datetime(y, m, sample_day, tzinfo=timezone.utc)
            if day > datetime.now(timezone.utc):
                break
            for r in fetch_window(day, day + timedelta(days=1)):
                recs.append({"year": y, "service_code": r.get("service_code"),
                             "service_name": r.get("service_name"),
                             "council": ";".join((r.get("agency_responsible") or {}).get("recipient", []))})
        print("discovered", y, len(recs), flush=True)
    df = pd.DataFrame(recs)
    tally = (df.groupby(["service_code", "service_name"], dropna=False)
               .agg(n=("year", "size"), first_year=("year", "min"), last_year=("year", "max"),
                    councils=("council", lambda s: "; ".join(sorted(set(s))[:5])))
               .reset_index())
    tally.to_csv(out, index=False)
    return tally


def is_flytip(code: str, name: str) -> bool:
    text = f"{code} {name}"
    return bool(FLYTIP.search(text)) and not EXCLUDE.search(text)


def download(codes: list[str]) -> None:
    """One JSON-lines file per category and year; existing files are skipped so the
    download can resume."""
    now = datetime.now(timezone.utc)
    for code in codes:
        safe = re.sub(r"[^A-Za-z0-9]+", "_", code)[:80]
        for y in YEARS:
            out = RAW / "reports" / f"{safe}__{y}.jsonl"
            if out.exists():
                continue
            start = datetime(y, 1, 1, tzinfo=timezone.utc)
            end = min(datetime(y + 1, 1, 1, tzinfo=timezone.utc), now)
            rows = fetch_window(start, end, code)
            out.parent.mkdir(parents=True, exist_ok=True)
            with out.open("w") as f:
                for r in rows:
                    f.write(json.dumps(r) + "\n")
            if rows:
                print(code, y, len(rows), flush=True)


def load_reports() -> pd.DataFrame:
    keep = ["service_request_id", "requested_datetime", "service_code", "service_name",
            "status", "lat", "long", "interface_used"]
    rows = []
    for f in sorted((RAW / "reports").glob("*.jsonl")):
        for line in f.open():
            r = json.loads(line)
            rec = {k: r.get(k) for k in keep}
            rec["council"] = ";".join((r.get("agency_responsible") or {}).get("recipient", []))
            rows.append(rec)
    df = pd.DataFrame(rows).drop_duplicates("service_request_id")
    df["requested_datetime"] = pd.to_datetime(df["requested_datetime"], utc=True)
    df[["lat", "long"]] = df[["lat", "long"]].astype(float)
    return df


if __name__ == "__main__":
    import sys
    RAW.mkdir(parents=True, exist_ok=True)
    cats = discover()
    cats["flytip"] = [is_flytip(str(c), str(n)) for c, n in zip(cats["service_code"], cats["service_name"])]
    cats.to_csv(RAW / "categories_sample.csv", index=False)
    print(cats["flytip"].sum(), "fly-tipping categories of", len(cats))
    if "--download" in sys.argv:
        codes = cats.loc[cats["flytip"], "service_code"].dropna().unique().tolist()
        download(codes)
