"""Does fly-tipping change when the nearest recycling centre cuts its opening hours?

Opening hours per centre and year come from archived council pages
(hwrc_rules.py). Because one archived page may show only summer or only winter
hours, each centre's weekly hours are smoothed (median of the year and its
observed neighbours) and carried across unobserved years between two
observations; values below 14 or above 100 hours a week are treated as misread.

Each neighbourhood (LSOA) is linked to its nearest centre by drive time, year by
year (hwrc_nearest.py), giving:
- weekly opening hours of the nearest centre;
- crowding: households for which that centre is the nearest, per weekly opening
  hour (as in IECR's map, which found crowding linked to fly-tipping across
  neighbourhoods at one point in time).

Models compare each neighbourhood with itself over time (neighbourhood fixed
effects) within the same council and year (council-by-year fixed effects), so a
coefficient answers: when the hours at a neighbourhood's nearest centre fall,
do its fly-tipping reports rise compared with other neighbourhoods in the same
council that year? The main sample keeps neighbourhoods whose nearest centre did
not change, so only changes in hours (not closures) count. Outcomes: FixMyStreet
reports (councils with 50+ reports a year) and councils' own incident records
(council_records.py) where they span several years.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import pyfixest as pf

from fms_analysis import INTERIM, OUT, active_council_years, lsoa_panel

YEARS = range(2014, 2025)


def site_hours() -> pd.DataFrame:
    sy = pd.read_csv(INTERIM / "hwrc_rules_site_year.csv", dtype={"site_id": str})
    sy = sy[sy["weekly_hours"].between(14, 100)].sort_values(["site_id", "year"])
    sy["weekly"] = sy.groupby("site_id")["weekly_hours"].transform(
        lambda s: s.rolling(3, center=True, min_periods=1).median())
    out = []
    for sid, g in sy.groupby("site_id"):
        full = pd.DataFrame({"year": range(g["year"].min(), g["year"].max() + 1)})
        full = full.merge(g[["year", "weekly"]], on="year", how="left")
        full["weekly"] = full["weekly"].ffill()
        out.append(full.assign(site_id=sid))
    return pd.concat(out, ignore_index=True)


def lsoa_hours() -> pd.DataFrame:
    near = pd.read_csv(INTERIM / "lsoa_nearest_hwrc.csv", dtype={"site_id": str})
    near = near[near["year"].isin(YEARS)]
    hh = pd.read_csv(INTERIM / "census_lsoa.csv")[["LSOA21CD", "households"]]
    near = near.merge(hh, on="LSOA21CD")
    load = near.groupby(["site_id", "year"])["households"].sum().rename("site_households").reset_index()
    d = near.merge(site_hours(), on=["site_id", "year"], how="left").merge(load, on=["site_id", "year"])
    d["crowding"] = d["site_households"] / d["weekly"]
    d = d.sort_values(["LSOA21CD", "year"])
    d["same_site"] = d.groupby("LSOA21CD")["site_id"].transform("nunique") == 1
    return d[["LSOA21CD", "year", "site_id", "weekly", "crowding", "same_site", "site_households"]]


def fit(d: pd.DataFrame, y: str, x: str, label: dict) -> list[dict]:
    d = d.dropna(subset=[x, y])
    d = d[d.groupby("LSOA21CD")[y].transform("sum") > 0]
    m = pf.fepois(f"{y} ~ {x} | LSOA21CD + lad_year", data=d, offset="log_residents", vcov={"CRV1": "LAD25CD"})
    b, se = m.coef()[x], m.se()[x]
    sd = d.groupby("LSOA21CD")[x].transform(lambda s: s - s.mean())
    changed = d.groupby("LSOA21CD")[x].agg(lambda s: s.max() - s.min())
    return [{**label, "outcome": y, "term": x, "irr": np.exp(b), "lo": np.exp(b - 1.96 * se),
             "hi": np.exp(b + 1.96 * se), "p": m.pvalue()[x], "n_lsoa_years": int(m._N),
             "n_lsoas": d["LSOA21CD"].nunique(), "n_councils": d["LAD25CD"].nunique(),
             "n_lsoas_changed": int((changed > (1 if x == "hours_cut_10" else 0.1)).sum()),
             "within_sd": float(sd.std()), "reports": int(d[y].sum())}]


def prepare(base: pd.DataFrame, h: pd.DataFrame) -> pd.DataFrame:
    d = base.merge(h, on=["LSOA21CD", "year"])
    d["hours_cut_10"] = -d["weekly"] / 10          # +1 = 10 fewer opening hours a week
    d["log_crowding"] = np.log(d["crowding"])      # +1 = 2.7 times more households per hour
    return d


if __name__ == "__main__":
    h = lsoa_hours()
    base = lsoa_panel()
    base = base[base["year"].isin(YEARS)]
    d = prepare(active_council_years(base, "flytip"), h)
    rows = []
    for sample, dd in (("nearest centre unchanged", d[d["same_site"]]), ("all neighbourhoods", d)):
        for x in ("hours_cut_10", "log_crowding"):
            rows += fit(dd, "n_flytip", x, {"source": "FixMyStreet", "sample": sample})
    # Councils' own records, where they cover several years (council_records.py)
    try:
        import council_records as cr
        cb = cr.lsoa_base()
        cb = cb[cb["year"].isin(YEARS)]
        recs = {"York": cr.load_york(), "Bassetlaw": cr.load_bassetlaw(), "Bradford": cr.load_bradford(),
                **{c: cr.load_arcgis(c) for c in ("Epping Forest", "Darlington", "West Oxfordshire")}}
        panels = [cr.lsoa_panel_for(r, cb, c) for c, r in recs.items()]
        cd = prepare(pd.concat(panels, ignore_index=True), h)
        cd = cd[cd["year"] <= max(YEARS)]
        for sample, dd in (("nearest centre unchanged", cd[cd["same_site"]]), ("all neighbourhoods", cd)):
            for x in ("hours_cut_10", "log_crowding"):
                rows += fit(dd.rename(columns={}), "n_council", x, {"source": "council records", "sample": sample})
    except Exception as e:  # council files not downloaded
        print("council records skipped:", e)
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "hours_models.csv", index=False)
    pd.set_option("display.width", 220)
    print(res.round(3).to_string(index=False))
