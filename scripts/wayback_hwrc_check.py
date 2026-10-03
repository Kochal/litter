#!/usr/bin/env python3
"""Check apparent recycling centre (HWRC) closures and openings against archived
council web pages in the Internet Archive's Wayback Machine.

Run this locally (it needs access to web.archive.org):

    pip install requests
    python scripts/wayback_hwrc_check.py                      # all councils
    python scripts/wayback_hwrc_check.py --domains kent.gov.uk  # try one first

Input:  data/wayback/hwrc_sites_to_check.csv (one row per site whose presence in
        the Environment Agency records starts after 2012 or ends before 2025, with
        the website domains of the council responsible).
Output: data/wayback/out/site_evidence.csv  one row per site with a verdict
        data/wayback/out/list_pages.csv     which archived pages were read
        data/wayback/out/cdx/<domain>.csv   raw Wayback index rows per domain
Commit the out/ folder (not cache/) and push, or upload it, when done.

Method, per council domain:
1. Ask the Wayback CDX index for every archived HTML page on the domain whose
   address mentions recycling centres, tips, household waste or civic amenity
   sites.
2. Pick "list pages": addresses that look like the council's page listing all its
   recycling centres (for example /household-waste-recycling-centres), choosing
   the most-captured ones separately for each year.
3. For each list page and each year, read one archived copy (closest to July)
   and look for each site's distinctive name words.
4. Per site: which years its name (or an alias from the input) appears on a list,
   and which years a page about the site itself (address contains its name) was
   captured; both count as evidence the site was open.
5. Verdict, by comparing with the years the site appears in the EA records.

Responses are cached in data/wayback/cache/, so an interrupted run resumes.
The Wayback Machine rate-limits heavy use; keep --sleep at 2 seconds or more.
"""
import argparse
import csv
import hashlib
import html
import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
WB = ROOT / "data" / "wayback"
CACHE = WB / "cache"
OUT = WB / "out"
CDX = "https://web.archive.org/cdx/search/cdx"
YEARS = range(2011, 2026)
HEADERS = {"User-Agent": "litter-research/0.1 (academic study of fly-tipping and recycling centre access)"}

URL_KEYWORDS = r"recycl|household-waste|household_waste|hwrc|\btips?\b|civic-amenity|amenity-site|waste-site|rubbish-tip"
LIST_PAGE = re.compile(
    r"/(?:[a-z-]*recycling-centres?|household-waste-recycling-centres?|hwrcs?|tips?|"
    r"civic-amenity-sites?|household-waste-sites?|recycling-and-waste-centres?|"
    r"find-a-recycling-centre|recycling-centres-and-tips?)/?(?:index\.[a-z]+)?$", re.I)
GENERIC = set("""household waste recycling centre center centres site sites civic amenity hwrc hrc
    hwrs transfer station and the of reuse re use tip tips depot road lane street way
    farm park industrial estate facility recycle community local council county borough
    new old former north south east west mrf composting landfill treatment plant ltd
    limited epr c a wtc wts rts tls ivc mbt green garden bring bank point""".split())


# ---------------------------------------------------------------- fetching
class Fetcher:
    def __init__(self, sleep: float):
        self.sleep = sleep
        self.s = requests.Session()
        self.s.headers.update(HEADERS)
        CACHE.mkdir(parents=True, exist_ok=True)

    def get(self, url: str, params: dict | None = None) -> str | None:
        key = hashlib.sha1((url + json.dumps(params or {}, sort_keys=True)).encode()).hexdigest()
        f = CACHE / f"{key}.txt"
        if f.exists():
            t = f.read_text(encoding="utf-8", errors="replace")
            return None if t == "\x00MISSING" else t
        for attempt in range(7):
            time.sleep(self.sleep)
            try:
                r = self.s.get(url, params=params, timeout=120)
            except requests.RequestException as e:
                print(f"  network error ({e.__class__.__name__}), retrying", file=sys.stderr)
                time.sleep(10 * (attempt + 1))
                continue
            if r.status_code == 200:
                f.write_text(r.text, encoding="utf-8")
                return r.text
            if r.status_code in (404, 403):
                f.write_text("\x00MISSING", encoding="utf-8")
                return None
            wait = 60 * (attempt + 1) if r.status_code == 429 else 10 * (attempt + 1)
            print(f"  HTTP {r.status_code}, waiting {wait}s", file=sys.stderr)
            time.sleep(wait)
        print(f"  giving up on {url} {params}", file=sys.stderr)
        return None


def cdx_rows(fx: Fetcher, domain: str) -> list[dict]:
    """All archived HTML captures on the domain (and subdomains) whose address
    matches URL_KEYWORDS, paging with a resume key."""
    rows, resume = [], None
    while True:
        params = {"url": domain, "matchType": "domain", "output": "json",
                  "fl": "original,timestamp,statuscode", "from": str(YEARS.start), "to": str(YEARS.stop - 1),
                  "filter": ["mimetype:text/html", f"original:(?i).*({URL_KEYWORDS}).*"],
                  "limit": "10000", "showResumeKey": "true"}
        if resume:
            params["resumeKey"] = resume
        text = fx.get(CDX, params)
        if not text or not text.strip():
            break
        data = json.loads(text)
        if not data:
            break
        resume = None
        body = data[1:]
        if len(body) >= 2 and body[-2] == []:  # [..., [], [resumeKey]]
            resume = body[-1][0]
            body = body[:-2]
        rows += [dict(zip(data[0], r)) for r in body if len(r) == len(data[0])]
        if not resume:
            break
    return rows


def snapshot_text(fx: Fetcher, timestamp: str, original: str) -> str | None:
    raw = fx.get(f"https://web.archive.org/web/{timestamp}id_/{original}")
    if raw is None:
        return None
    raw = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", raw))).lower()


# ---------------------------------------------------------------- matching
def tokens(name: str) -> list[str]:
    words = [w for w in re.findall(r"[a-z]+", name.lower()) if w not in GENERIC]
    long = [w for w in words if len(w) >= 4]
    return (long or [w for w in words if len(w) >= 3])[:2]


def name_variants(site: dict) -> list[list[str]]:
    """Search words for the EA name and any 'also known as' names (semicolon
    separated in the input's aliases column, e.g. a site renamed by the council)."""
    names = [site["name"]] + [a for a in (site.get("aliases") or "").split(";") if a.strip()]
    return [t for t in (tokens(n) for n in names) if t]


def on_page(text: str, variants: list[list[str]]) -> tuple[bool, str]:
    """True if every search word of any name variant is on the page. Words are also
    matched with spaces removed, so 'rosehill' finds 'rose hill'."""
    squashed = re.sub(r"[^a-z]", "", text)
    for toks in variants:
        hits = [re.search(rf"\b{re.escape(t)}\b", text) for t in toks]
        if all(hits):
            i = hits[0].start()
            return True, text[max(0, i - 80): i + 120]
        if all(t in squashed for t in toks) and len("".join(toks)) >= 6:
            return True, "(matched with spaces removed) " + " ".join(toks)
    return False, ""


def norm_path(url: str) -> str:
    return re.sub(r"^https?://(www\.)?", "", url.lower()).split("?")[0].rstrip("/")


def verdict(event: str, ea_first: int, ea_last: int, present: dict[int, bool]) -> tuple[str, str]:
    checked = sorted(present)
    yes = [y for y in checked if present[y]]
    if not checked:
        return "unclear", "no archived list page found"
    if not yes:
        if "closure" in event and checked and min(checked) > ea_last:
            return ("likely closure (never listed afterwards)",
                    f"not on any list checked ({min(checked)} to {max(checked)}); no list from before {ea_last + 1} "
                    "to compare, and the council may use a different name")
        return "unclear", "name never found on the archived pages (name may differ)"
    notes = []
    out = []
    if "closure" in event:
        after = [y for y in checked if y > ea_last]
        if after and any(present[y] for y in after if y >= max(after) - 1):
            out.append("still open after EA records end")
        elif after and not any(present[y] for y in after) and any(present[y] for y in checked if y <= ea_last):
            last_seen = max(y for y in yes if y <= ea_last)
            out.append("confirmed closure")
            notes.append(f"last listed {last_seen}, missing from {min(y for y in after)}")
        else:
            out.append("closure unclear")
    if "opening" in event:
        before = [y for y in checked if y < ea_first - 1]
        if before and any(present[y] for y in before):
            out.append("existed before EA records start")
        elif before and any(present[y] for y in checked if y >= ea_first):
            out.append("confirmed opening")
        else:
            out.append("opening unclear")
    return "; ".join(out), "; ".join(notes)


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--domains", nargs="*", help="only these domains (for a trial run)")
    ap.add_argument("--sleep", type=float, default=2.0, help="seconds between requests")
    ap.add_argument("--list-pages", type=int, default=2, help="list pages to read per domain and year")
    a = ap.parse_args()

    sites = list(csv.DictReader(open(WB / "hwrc_sites_to_check.csv", encoding="utf-8")))
    by_domain = defaultdict(list)
    for s in sites:
        for d in s["domains"].split(";"):
            if d and (not a.domains or d in a.domains):
                by_domain[d].append(s)
    fx = Fetcher(a.sleep)
    (OUT / "cdx").mkdir(parents=True, exist_ok=True)

    present = defaultdict(dict)       # site_id -> {year: bool}
    context = defaultdict(dict)       # site_id -> {year: snippet}
    site_pages = defaultdict(list)    # site_id -> [(url, last_ok_ts, n_captures)]
    page_years = defaultdict(set)     # site_id -> years with a good capture of the site's own page
    list_log = []

    for n, (domain, dsites) in enumerate(sorted(by_domain.items()), 1):
        print(f"[{n}/{len(by_domain)}] {domain}: {len(dsites)} sites", flush=True)
        rows = cdx_rows(fx, domain)
        with open(OUT / "cdx" / f"{domain}.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["original", "timestamp", "statuscode"])
            w.writeheader()
            w.writerows(rows)
        ok = [r for r in rows if r.get("statuscode") == "200"]
        by_url = defaultdict(list)
        for r in ok:
            by_url[norm_path(r["original"])].append(r)

        # Pages about each site, by name in the address; a good capture in a year
        # counts as evidence the site was open that year
        for s in dsites:
            for toks in name_variants(s):
                for u, caps in by_url.items():
                    path_words = re.sub(r"[^a-z]+", " ", u.split("/", 1)[-1]).split()
                    if toks[0] in path_words or (len(toks[0]) >= 6 and toks[0] in "".join(path_words)):
                        site_pages[s["site_id"]].append((u, max(c["timestamp"] for c in caps), len(caps)))
                        for c in caps:
                            page_years[s["site_id"]].add(int(c["timestamp"][:4]))

        # List pages: addresses that look like the council's list of centres. Chosen
        # year by year, because councils restructure their websites.
        lists = [u for u in by_url if LIST_PAGE.search("/" + u.split("/", 1)[-1])]
        print(f"  {len(rows)} captures, {len(by_url)} pages, {len(lists)} list pages", flush=True)
        for y in YEARS:
            in_year = sorted(((u, [c for c in by_url[u] if c["timestamp"][:4] == str(y)]) for u in lists),
                             key=lambda x: -len(x[1]))
            for u, yc in [x for x in in_year if x[1]][: a.list_pages]:
                c = min(yc, key=lambda c: abs(int(c["timestamp"][4:8]) - 701))
                text = snapshot_text(fx, c["timestamp"], c["original"])
                list_log.append({"domain": domain, "url": u, "year": y, "timestamp": c["timestamp"],
                                 "read": text is not None, "chars": len(text or "")})
                if not text or len(text) < 500:
                    continue
                for s in dsites:
                    hit, snip = on_page(text, name_variants(s))
                    sid = s["site_id"]
                    present[sid][y] = present[sid].get(y, False) or hit
                    if hit and y not in context[sid]:
                        context[sid][y] = snip

    with open(OUT / "list_pages.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["domain", "url", "year", "timestamp", "read", "chars"])
        w.writeheader()
        w.writerows(list_log)

    fields = ["site_id", "name", "council", "event", "ea_first_year", "ea_last_year", "name_tokens",
              "verdict", "notes", "years_listed", "years_site_page", "years_checked", "site_pages", "example_text"]
    with open(OUT / "site_evidence.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for s in sites:
            if a.domains and not any(d in a.domains for d in s["domains"].split(";")):
                continue
            sid = s["site_id"]
            pr = dict(present.get(sid, {}))
            for y in page_years.get(sid, ()):  # the site's own page captured that year
                pr[y] = True
            v, notes = verdict(s["event"], int(s["ea_first_year"]), int(s["ea_last_year"]), pr)
            pages = sorted(site_pages.get(sid, []), key=lambda p: -p[2])[:3]
            snip = next(iter(context.get(sid, {}).values()), "")
            w.writerow({**{k: s[k] for k in ["site_id", "name", "council", "event", "ea_first_year", "ea_last_year"]},
                        "name_tokens": " / ".join(" ".join(t) for t in name_variants(s)), "verdict": v, "notes": notes,
                        "years_listed": " ".join(str(y) for y in sorted(pr) if pr[y]),
                        "years_site_page": " ".join(str(y) for y in sorted(page_years.get(sid, ()))),
                        "years_checked": " ".join(str(y) for y in sorted(pr)),
                        "site_pages": " | ".join(f"{u} (last ok {t[:8]})" for u, t, _ in pages),
                        "example_text": snip})
    print(f"Done. Results in {OUT / 'site_evidence.csv'}")


if __name__ == "__main__":
    main()
