#!/usr/bin/env python3
"""Collect recycling centre (HWRC) opening hours, booking rules and DIY waste
charges, year by year, from archived council web pages in the Internet
Archive's Wayback Machine.

Run this locally (it needs access to web.archive.org), from the repository root:

    pip install requests
    python scripts/wayback_hwrc_rules.py --domains leeds.gov.uk kent.gov.uk   # trial
    python scripts/wayback_hwrc_rules.py                                     # everything

Input:  data/wayback/hwrc_sites_all.csv (every recycling centre in England and
        Wales with its postcode and the website domains of the councils that
        would describe it; built by src/wayback_inputs.py).
Output: data/wayback/out/rules/snippets.csv.gz  text near each site's name or
                                                postcode, and near words about
                                                booking, charges and permits
        data/wayback/out/rules/pages.csv        which archived pages were read
Commit the out/rules folder and push, or upload it, when done. Nothing is
parsed here: the opening hours, booking and charging rules are worked out from
the snippets in the analysis (src/hwrc_rules.py), so the rules can be improved
without fetching again.

Method, per council domain:
1. Ask the Wayback CDX index for archived HTML pages whose address mentions
   recycling centres, tips, opening times, booking, permits or charges.
2. For each year from 2014 to 2025, pick the pages to read: up to 2 pages that
   look like the council's list of centres, up to 3 pages about booking,
   charges, permits or opening times, and each site's own page (address
   contains the site's name). Read one archived copy per page and year, the one
   closest to July.
3. From each page keep short pieces of text: after each mention of a site (its
   distinctive name words or its postcode), and around each mention of booking,
   charges, permits, DIY waste, rubble, plasterboard or opening hours.

Responses are cached in data/wayback/cache/ (shared with wayback_hwrc_check.py),
so an interrupted run resumes and pages already read are not fetched again. The
Wayback Machine rate-limits heavy use; keep --sleep at 2 seconds or more.
Domains are processed in order of how many sites they cover, so the councils
that run most centres come first and a partial run is still useful.
"""
import argparse
import csv
import gzip
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wayback_hwrc_check import CDX, LIST_PAGE, Fetcher, norm_path, snapshot_text, tokens  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
WB = ROOT / "data" / "wayback"
OUT = WB / "out" / "rules"
YEARS = range(2014, 2026)

URL_KEYWORDS = (r"recycl|household-waste|household_waste|hwrc|hrc|\btips?\b|civic-amenity|amenity-site|"
                r"waste-site|rubbish-tip|opening-times|opening-hours|book|permit|charg|diy|non-household|"
                r"rubble|plasterboard|van|trailer")
RULES_PAGE = re.compile(r"book|appointment|slot|permit|charg|diy|non-household|rubble|plasterboard|"
                        r"opening-(?:times|hours)|vans?-|trailer|what-you-can", re.I)
TOPIC = re.compile(
    r"book(?:ing|ed)?\b|appointment|time slot|\bslots?\b|permits?\b|\bvans?\b|trailers?|"
    r"charg(?:e|es|ed|ing)\b|\bfees?\b|£\s?\d|free of charge|\bdiy\b|non-household|rubble|hardcore|"
    r"plasterboard|soil|tyres?\b|asbestos|"
    r"opening (?:times|hours)|open(?:s|ing)? (?:daily|every day|\d)|closed on|summer|winter|"
    r"\d{1,2}(?:[.:]\d{2})?\s?(?:am|pm)\b", re.I)
POSTCODE = re.compile(r"\b[a-z]{1,2}\d[a-z\d]? ?\d[a-z]{2}\b", re.I)
SITE_WINDOW, TOPIC_WINDOW, MAX_TOPIC = 700, 220, 60


def cdx_rows(fx: Fetcher, domain: str) -> list[dict]:
    rows, resume = [], None
    while True:
        params = {"url": domain, "matchType": "domain", "output": "json",
                  "fl": "original,timestamp,statuscode", "from": str(YEARS.start), "to": str(YEARS.stop - 1),
                  "filter": ["mimetype:text/html", "statuscode:200", f"original:(?i).*({URL_KEYWORDS}).*"],
                  "collapse": "timestamp:6", "limit": "10000", "showResumeKey": "true"}
        if resume:
            params["resumeKey"] = resume
        text = fx.get(CDX, params)
        if not text or not text.strip():
            break
        data = json.loads(text)
        if not data:
            break
        resume, body = None, data[1:]
        if len(body) >= 2 and body[-2] == []:
            resume, body = body[-1][0], body[:-2]
        rows += [dict(zip(data[0], r)) for r in body if len(r) == len(data[0])]
        if not resume:
            break
    return rows


def site_terms(site: dict) -> list[re.Pattern]:
    """Patterns that find a site on a page: its distinctive name words (all of
    them, within 60 characters) or its postcode (with or without the space)."""
    pats = []
    toks = tokens(site["name"])
    if toks:
        pats.append(re.compile(r"\b" + r"\b.{0,60}?\b".join(re.escape(t) for t in toks) + r"\b"))
    pc = (site.get("postcode") or "").lower().replace(" ", "")
    if len(pc) >= 5:
        pats.append(re.compile(re.escape(pc[:-3]) + r"\s?" + re.escape(pc[-3:])))
    return pats


def snippets(text: str, sites: list[dict]) -> list[tuple[str, str, str]]:
    """(site_id or '', kind, text) pieces worth keeping from one page."""
    out = []
    for s in sites:
        hits = sorted(m.start() for p in site_terms(s) for m in p.finditer(text))
        last, kept = -10**9, 0
        for h in hits:
            if h < last + SITE_WINDOW or kept >= 3:  # same passage, or enough
                continue
            last, kept = h, kept + 1
            out.append((s["site_id"], "site", text[max(0, h - 150): h + SITE_WINDOW]))
    seen = -10**9
    n = 0
    for m in TOPIC.finditer(text):
        if m.start() < seen + TOPIC_WINDOW or n >= MAX_TOPIC:
            continue
        seen = m.start()
        n += 1
        out.append(("", "topic", text[max(0, m.start() - TOPIC_WINDOW): m.end() + TOPIC_WINDOW]))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--domains", nargs="*", help="only these domains (for a trial run)")
    ap.add_argument("--sleep", type=float, default=2.0, help="seconds between requests")
    ap.add_argument("--max-site-pages", type=int, default=12, help="site pages to read per domain and year")
    a = ap.parse_args()

    sites = list(csv.DictReader(open(WB / "hwrc_sites_all.csv", encoding="utf-8")))
    by_domain = defaultdict(list)
    for s in sites:
        for d in s["domains"].split(";"):
            if d and (not a.domains or d in a.domains):
                by_domain[d].append(s)
    order = sorted(by_domain, key=lambda d: (-len(by_domain[d]), d))
    fx = Fetcher(a.sleep)
    OUT.mkdir(parents=True, exist_ok=True)
    done_file = OUT / "done_domains.txt"
    done = set(done_file.read_text().split()) if done_file.exists() else set()
    snip_path, page_path = OUT / "snippets.csv.gz", OUT / "pages.csv"
    new = not snip_path.exists()
    sf = gzip.open(snip_path, "at", encoding="utf-8", newline="")
    pf = open(page_path, "a", encoding="utf-8", newline="")
    sw = csv.writer(sf)
    pw = csv.writer(pf)
    if new:
        sw.writerow(["domain", "year", "timestamp", "url", "page_kind", "site_id", "kind", "text"])
        pw.writerow(["domain", "year", "timestamp", "url", "page_kind", "read", "chars", "n_snippets"])

    for n, domain in enumerate(order, 1):
        if domain in done:
            continue
        dsites = by_domain[domain]
        print(f"[{n}/{len(order)}] {domain}: {len(dsites)} sites", flush=True)
        by_url = defaultdict(list)
        for r in cdx_rows(fx, domain):
            by_url[norm_path(r["original"])].append(r)
        lists = [u for u in by_url if LIST_PAGE.search("/" + u.split("/", 1)[-1])]
        rules = [u for u in by_url if RULES_PAGE.search(u.split("/", 1)[-1]) and u not in lists]
        own = set()
        for s in dsites:
            toks = tokens(s["name"])
            if not toks:
                continue
            for u in by_url:
                words = re.sub(r"[^a-z]+", " ", u.split("/", 1)[-1]).split()
                if toks[0] in words or (len(toks[0]) >= 6 and toks[0] in "".join(words)):
                    own.add(u)
        own -= set(lists) | set(rules)
        print(f"  {len(by_url)} pages: {len(lists)} lists, {len(rules)} rules, {len(own)} site pages", flush=True)
        for y in YEARS:
            def pick(urls, k):
                yc = [(u, [c for c in by_url[u] if c["timestamp"][:4] == str(y)]) for u in urls]
                return [x for x in sorted(yc, key=lambda x: -len(x[1])) if x[1]][:k]
            for kind, chosen in (("list", pick(lists, 2)), ("rules", pick(rules, 3)), ("site", pick(own, a.max_site_pages))):
                for u, caps in chosen:
                    c = min(caps, key=lambda c: abs(int(c["timestamp"][4:8]) - 701))
                    text = snapshot_text(fx, c["timestamp"], c["original"])
                    pieces = snippets(text, dsites) if text and len(text) > 300 else []
                    for sid, k, t in pieces:
                        sw.writerow([domain, y, c["timestamp"], u, kind, sid, k, t])
                    pw.writerow([domain, y, c["timestamp"], u, kind, text is not None, len(text or ""), len(pieces)])
        sf.flush()
        pf.flush()
        with open(done_file, "a") as f:
            f.write(domain + "\n")
    sf.close()
    pf.close()
    print(f"Done. Results in {OUT}")


if __name__ == "__main__":
    main()
