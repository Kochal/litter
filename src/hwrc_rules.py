"""Opening hours, booking and DIY charges of recycling centres by year, from the
archived council page snippets collected by scripts/wayback_hwrc_rules.py.

Per site and year (from snippets on the site's own page or right after its name):
- daily opening hours: time ranges such as "8am to 4pm", "8.30am - 6pm" or
  "09:00-17:00"; the summer (longest) and winter (shortest) ranges are averaged;
- days open per week: 7, minus weekdays named after "closed on" (or "closed every");
- weekly hours = daily hours x days open.
Per council domain and year (from any snippet):
- booking: "book a slot", "booking is required/essential", "must book",
  "pre-book" ("by appointment only" is left out: councils use it for asbestos);
- DIY charges: a charge (a price, "charge", "fee") within 120 characters of
  DIY waste (rubble, hardcore, soil, plasterboard, DIY, construction), unless the
  text says such waste is free.
Matches near asbestos, museums, libraries and similar services are ignored.
These are text rules, so each output row keeps the snippet it came from for
checking. Output: data/interim/hwrc_rules_site_year.csv and
data/interim/hwrc_rules_council_year.csv.
"""
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SNIPPETS = ROOT / "data" / "wayback" / "out" / "rules" / "snippets.csv.gz"
SITES = ROOT / "data" / "wayback" / "hwrc_sites_all.csv"
INTERIM = ROOT / "data" / "interim"

TIME = r"(\d{1,2})(?:[.:](\d{2}))?\s?(am|pm|noon)?"
RANGE = re.compile(TIME + r"\s?(?:to|until|till|-|–)\s?" + TIME)
DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
CLOSED_DAYS = re.compile(r"closed (?:on |every |all day )?((?:(?:mon|tues|wednes|thurs|fri|satur|sun)days?"
                         r"(?:,| and| &| or)?\s?)+)")
BOOKING = re.compile(r"book (?:a |your )?(?:time )?slot|booking (?:is )?(?:required|essential|compulsory|mandatory)|"
                     r"must (?:pre-?)?book|pre-?book|need to book|booking system")
DIY = r"(?:rubble|hardcore|soil|plasterboard|\bdiy\b|construction waste|building waste|non-household)"
CHARGE = r"(?:£\s?\d|\bcharge[sd]?\b|\bcharging\b|\bfees?\b)"
DIY_CHARGE = re.compile(DIY + r".{0,120}?" + CHARGE + "|" + CHARGE + r".{0,120}?" + DIY)
DIY_FREE = re.compile(DIY + r".{0,80}?(?:free of charge|no charge|free\b)|(?:free of charge|no longer charge)"
                      r".{0,80}?" + DIY)


NOT_VISITS = re.compile(r"asbestos|museum|discovery centre|librar|galler|gas bottle|ceremon|tickets?\b")


def first_valid(pattern: re.Pattern, text: str):
    """First match not about asbestos appointments or other council services."""
    for m in pattern.finditer(text):
        if not NOT_VISITS.search(text[max(0, m.start() - 300): m.end() + 80]):
            return m
    return None


def to_hours(h, m, ap) -> float | None:
    h = int(h)
    m = int(m) if m else 0
    if h > 24 or m > 59:
        return None
    if ap == "pm" and h < 12:
        h += 12
    if ap == "noon":
        h = 12
    return h + m / 60


def daily_ranges(text: str) -> list[float]:
    out = []
    for g in RANGE.findall(text):
        a, b = to_hours(*g[:3]), to_hours(*g[3:])
        if a is None or b is None:
            continue
        if not g[2] and not g[5] and ":" not in text:  # bare numbers without am/pm or 24h clock: skip
            continue
        if b <= a and b + 12 > a:  # "8 to 4" style
            b += 12
        span = b - a
        if 3 <= span <= 14 and 5 <= a <= 12:
            out.append(span)
    return out


def closed_days(text: str) -> int:
    found = set()
    for m in CLOSED_DAYS.finditer(text):
        for i, d in enumerate(DAYS):
            if d[:3] in m.group(1):
                found.add(i)
    return len(found)


def site_of_page(url: str, sites: pd.DataFrame) -> str | None:
    """The site whose distinctive name word appears in a site page's address."""
    words = re.sub(r"[^a-z]+", " ", url.split("/", 1)[-1].lower())
    hits = [r.site_id for r in sites.itertuples() if r.tok and r.tok in words.replace(" ", "")]
    return hits[0] if len(hits) == 1 else None


def main():
    s = pd.read_csv(SNIPPETS, dtype={"site_id": str})
    sites = pd.read_csv(SITES, dtype={"site_id": str})
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from wayback_hwrc_check import tokens
    sites["tok"] = sites["name"].map(lambda n: (tokens(n) or [""])[0])
    s["text"] = s["text"].fillna("").str.lower()
    # Topic snippets on a site's own page belong to that site
    dom_sites = {d: g for d, g in sites.assign(dom=sites["domains"].str.split(";")).explode("dom").groupby("dom")}
    page_site = {}
    for (d, u) in s.loc[s["page_kind"] == "site", ["domain", "url"]].drop_duplicates().itertuples(index=False):
        page_site[(d, u)] = site_of_page(u, dom_sites.get(d, sites.iloc[:0]))
    s["sid"] = s["site_id"].where(s["site_id"].notna() & (s["site_id"] != ""),
                                  [page_site.get((d, u)) if k == "site" else None
                                   for d, u, k in zip(s["domain"], s["url"], s["page_kind"])])

    rows = []
    for (sid, y), g in s.dropna(subset=["sid"]).groupby(["sid", "year"]):
        text = " ".join(g["text"])
        spans = daily_ranges(text)
        if not spans:
            continue
        daily = (max(spans) + min(spans)) / 2
        days = 7 - closed_days(text)
        rows.append({"site_id": sid, "year": y, "daily_hours": daily, "summer_hours": max(spans),
                     "winter_hours": min(spans), "days_open": days, "weekly_hours": daily * days,
                     "n_snippets": len(g), "example": g["text"].iloc[0][:300]})
    site_year = pd.DataFrame(rows)

    rows = []
    for (d, y), g in s.groupby(["domain", "year"]):
        text = " ".join(g["text"])
        b = first_valid(BOOKING, text)
        c = first_valid(DIY_CHARGE, text)
        free = DIY_FREE.search(text)
        rows.append({"domain": d, "year": y, "booking": bool(b), "diy_charge": bool(c) and not (free and not c),
                     "diy_free_mentioned": bool(free), "booking_text": text[max(0, b.start() - 80): b.end() + 80] if b else "",
                     "charge_text": text[max(0, c.start() - 80): c.end() + 80] if c else "", "n_snippets": len(g)})
    council_year = pd.DataFrame(rows)
    site_year.to_csv(INTERIM / "hwrc_rules_site_year.csv", index=False)
    council_year.to_csv(INTERIM / "hwrc_rules_council_year.csv", index=False)
    print(f"{site_year['site_id'].nunique()} sites with opening hours in {len(site_year)} site-years; "
          f"{council_year['domain'].nunique()} council domains")
    return site_year, council_year


if __name__ == "__main__":
    sy, cy = main()
    pd.set_option("display.width", 250, "display.max_colwidth", 120)
    print(sy.drop(columns="example").round(1).to_string(index=False))
    print(cy.drop(columns=["booking_text"]).to_string(index=False))
