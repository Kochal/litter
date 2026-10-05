"""Correct the English recycling centre history with the Wayback Machine check
(data/wayback/out/site_evidence.csv, from scripts/wayback_hwrc_check.py).

Two corrected versions of data/interim/hwrc_england_history.csv:
- verified: sites listed by the council after their EA records end stay open to
  the end of the panel; sites listed before their EA records start count as open
  from the start. Confirmed and likely closures keep their EA dates. Unclear
  cases keep the EA dates.
- strict: as verified, but an apparent closure only counts if the check confirmed
  it or found it likely; unclear closures stay open and unclear openings count as
  open from the start.

Both versions then apply two further corrections:
- duplicate records: a "closed" site with another record of the same name
  within DUPLICATE_KM that carries on afterwards is the same centre re-recorded
  (often with a different grid reference); the record that carries on is kept
  and counts as open across both records' years;
- checks by hand (data/wayback/manual_checks.csv): closures that drive the
  closure-by-closure study, checked against council pages and local news.
"""
from pathlib import Path

import re

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INTERIM = ROOT / "data" / "interim"
EVIDENCE = ROOT / "data" / "wayback" / "out" / "site_evidence.csv"
MANUAL = ROOT / "data" / "wayback" / "manual_checks.csv"
START, END = 2012, 9999
DUPLICATE_KM = 1.5
GENERIC = set("household waste recycling centre centres reuse re use and the hwrc h w r c civic amenity amenities "
              "site of road lane depot transfer station facility recycle recovery park ltd limited".split())


def _tokens(name: str) -> set:
    return {w for w in re.findall(r"[a-z]+", name.lower()) if w not in GENERIC and len(w) > 2}


def merge_duplicates(h: pd.DataFrame) -> pd.DataFrame:
    """Merge a closed record into a later record of the same name nearby."""
    h = h.copy()
    drop = []
    for r in h[h["last"] < END - 1].sort_values("last").itertuples():
        later = h[(h["site_id"] != r.site_id) & (h["last"] > r.last) & ~h["site_id"].isin(drop)]
        km = np.hypot(later["easting"] - r.easting, later["northing"] - r.northing) / 1000
        later = later[(km < DUPLICATE_KM) & later["name"].map(lambda n: bool(_tokens(n) & _tokens(r.name)))]
        if later.empty:
            continue
        keep = later.index[0]
        h.loc[keep, "first"] = min(h.loc[keep, "first"], r.first)
        h.loc[keep, "correction"] = f"merged with duplicate record {r.site_id} ({r.name})"
        drop.append(r.site_id)
    return h[~h["site_id"].isin(drop)]


def apply_manual(h: pd.DataFrame) -> pd.DataFrame:
    m = pd.read_csv(MANUAL).set_index("site_id")
    h = h.copy()
    for sid, r in m.iterrows():
        i = h["site_id"] == sid
        if pd.notna(r["set_first"]):
            h.loc[i, "first"] = int(r["set_first"])
        if pd.notna(r["set_last"]):
            h.loc[i, "last"] = int(r["set_last"])
        h.loc[i, "correction"] = r["verdict"]
    return h


def corrected(strict: bool) -> pd.DataFrame:
    h = pd.read_csv(INTERIM / "hwrc_england_history.csv")
    ev = pd.read_csv(EVIDENCE)[["site_id", "event", "verdict"]].set_index("site_id")
    h = h.join(ev, on="site_id")
    v = h["verdict"].fillna("")
    still_open = v.str.contains("still open")
    existed = v.str.contains("existed before")
    real_closure = v.str.contains("confirmed closure|likely closure")
    real_opening = v.str.contains("confirmed opening")
    h.loc[still_open, "last"] = END
    h.loc[existed, "first"] = START
    if strict:
        closure = h["event"].fillna("").str.contains("closure")
        opening = h["event"].fillna("").str.contains("opening")
        h.loc[closure & ~real_closure, "last"] = END
        h.loc[opening & ~real_opening, "first"] = START
    h["correction"] = v.where(v != "", "not checked (open throughout the EA records)")
    h = merge_duplicates(h.drop(columns=["event", "verdict"]))
    return apply_manual(h)


if __name__ == "__main__":
    for name, strict in [("verified", False), ("strict", True)]:
        c = corrected(strict)
        c.to_csv(INTERIM / f"hwrc_england_history_{name}.csv", index=False)
        n_close = ((c["last"] < 2024) & (c["last"] != END)).sum()
        n_open = (c["first"] > START).sum()
        print(f"{name}: {len(c)} sites, {n_close} closures before 2024, {n_open} openings after {START}")
