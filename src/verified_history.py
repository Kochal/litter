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
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INTERIM = ROOT / "data" / "interim"
EVIDENCE = ROOT / "data" / "wayback" / "out" / "site_evidence.csv"
START, END = 2012, 9999


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
    return h.drop(columns=["event", "verdict"])


if __name__ == "__main__":
    for name, strict in [("verified", False), ("strict", True)]:
        c = corrected(strict)
        c.to_csv(INTERIM / f"hwrc_england_history_{name}.csv", index=False)
        n_close = ((c["last"] < 2024) & (c["last"] != END)).sum()
        n_open = (c["first"] > START).sum()
        print(f"{name}: {len(c)} sites, {n_close} closures before 2024, {n_open} openings after {START}")
