"""Neighbourhood (LSOA) analysis of FixMyStreet fly-tipping and litter reports.

Each report is placed in its 2021 LSOA. Counts per LSOA and year are compared
across neighbourhoods *within the same council and year* (council-by-year fixed
effects), so anything that differs between councils, including whether the
council uses FixMyStreet at all and how it records incidents, drops out. What is
left is whether, inside a council, neighbourhoods further from a recycling centre
report more fly-tipping, net of their housing and car ownership.

Also produced:
- validation of FixMyStreet against Defra/StatsWales council counts;
- report rates by rural-urban class and drive-time band, with observation counts.
"""
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyfixest as pf

from fixmystreet import load_reports

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
OUT = ROOT / "outputs"
YEARS = range(2012, 2025)  # complete calendar years that match the access panel


def reports_by_lsoa(kind: str) -> pd.DataFrame:
    """Reports per LSOA and calendar year."""
    cache = INTERIM / f"fms_{kind}_lsoa_year.csv"
    if cache.exists():
        return pd.read_csv(cache)
    r = load_reports(kind)
    r = r.dropna(subset=["lat", "long"])
    pts = gpd.GeoDataFrame(r[["service_request_id", "requested_datetime", "council"]],
                           geometry=gpd.points_from_xy(r["long"], r["lat"]), crs=4326).to_crs(27700)
    lsoa = gpd.read_file(RAW / "lsoa21_bsc_ruc.gpkg", columns=["LSOA21CD"])
    j = gpd.sjoin(pts, lsoa, predicate="within", how="inner")
    j["year"] = j["requested_datetime"].dt.year
    out = j.groupby(["LSOA21CD", "year"]).size().rename(f"n_{kind}").reset_index()
    out.to_csv(cache, index=False)
    return out


def lsoa_panel() -> pd.DataFrame:
    """LSOA-year table: report counts, drive time, census covariates, rural-urban
    class and council."""
    from access_panel import lsoa_to_lad
    lsoa = gpd.read_file(RAW / "lsoa21_bsc_ruc.gpkg", ignore_geometry=True)[
        ["LSOA21CD", "RUC21NM", "Urban_rura", "Shape__Area"]]
    times = pd.read_csv(INTERIM / "lsoa_hwrc_times_panel_censored.csv")[["LSOA21CD", "year", "t_hwrc_min"]]
    acc24 = pd.read_csv(INTERIM / "lsoa_access.csv")[["LSOA21CD", "t_landfill_min", "t_transfer_min"]]
    cen = pd.read_csv(INTERIM / "census_lsoa.csv")
    grid = times[times["year"].isin(YEARS)]
    d = (grid.merge(lsoa, on="LSOA21CD").merge(acc24, on="LSOA21CD").merge(cen, on="LSOA21CD")
             .merge(lsoa_to_lad(), on="LSOA21CD"))
    for kind in ("flytip", "litter"):
        d = d.merge(reports_by_lsoa(kind), on=["LSOA21CD", "year"], how="left")
        d[f"n_{kind}"] = d[f"n_{kind}"].fillna(0)
    d["log_residents"] = np.log(d["residents"])
    d["log_density"] = np.log(d["residents"] / (d["Shape__Area"] / 1e6))
    d["rural"] = (d["Urban_rura"] == "Rural").astype(int)
    d["t_hwrc_5"] = d["t_hwrc_min"] / 5
    d["t_landfill_10"] = d["t_landfill_min"] / 10
    d["t_transfer_5"] = d["t_transfer_min"] / 5
    d["private_rent_10"] = d["private_rent_share"] / 0.10
    d["no_car_10"] = d["no_car_share"] / 0.10
    d["lad_year"] = d["LAD25CD"] + "_" + d["year"].astype(str)
    return d


def active_council_years(d: pd.DataFrame, kind: str, min_reports: int = 50) -> pd.DataFrame:
    """Keep council-years where FixMyStreet is used enough to compare neighbourhoods."""
    tot = d.groupby("lad_year")[f"n_{kind}"].transform("sum")
    return d[tot >= min_reports]


def models(d: pd.DataFrame) -> pd.DataFrame:
    rows = []
    specs = {
        "drive time only": "t_hwrc_5",
        "plus housing and cars": "t_hwrc_5 + private_rent_10 + no_car_10 + log_density + rural",
        "plus landfill and transfer": ("t_hwrc_5 + private_rent_10 + no_car_10 + log_density + rural"
                                       " + t_landfill_10 + t_transfer_5"),
    }
    for kind in ("flytip", "litter"):
        dd = active_council_years(d, kind)
        if dd.empty:
            print("no active council-years for", kind)
            continue
        for label, rhs in specs.items():
            fit = pf.fepois(f"n_{kind} ~ {rhs} | lad_year", data=dd, offset="log_residents",
                            vcov={"CRV1": "LAD25CD"})
            coef, se, p = fit.coef(), fit.se(), fit.pvalue()
            for t in coef.index:
                rows.append({"outcome": kind, "spec": label, "term": t, "irr": np.exp(coef[t]),
                             "lo": np.exp(coef[t] - 1.96 * se[t]), "hi": np.exp(coef[t] + 1.96 * se[t]),
                             "p": p[t], "n_lsoa_years": int(fit._N),
                             "n_lsoas": dd["LSOA21CD"].nunique(), "n_councils": dd["LAD25CD"].nunique(),
                             "n_reports": int(dd[f"n_{kind}"].sum())})
    return pd.DataFrame(rows)


def descriptives(d: pd.DataFrame) -> pd.DataFrame:
    """Reports per 1,000 residents by rural-urban class and drive-time band, using
    only council-years where FixMyStreet is in active use."""
    dd = active_council_years(d, "flytip")
    dd = dd.assign(band=pd.cut(dd["t_hwrc_min"], [0, 5, 10, 15, 20, 999],
                               labels=["under 5", "5-10", "10-15", "15-20", "20+"]))
    g = dd.groupby(["Urban_rura", "band"], observed=True).agg(
        lsoa_years=("LSOA21CD", "size"), lsoas=("LSOA21CD", "nunique"),
        residents=("residents", "sum"), flytip=("n_flytip", "sum"), litter=("n_litter", "sum")).reset_index()
    g["flytip_per_1000"] = g["flytip"] / g["residents"] * 1000
    g["litter_per_1000"] = g["litter"] / g["residents"] * 1000
    return g


def validate(d: pd.DataFrame) -> pd.DataFrame:
    """FixMyStreet reports against official council counts (calendar year vs April
    to March year, so only a rough check)."""
    fms = d.groupby(["LAD25CD", "year"])["n_flytip"].sum().reset_index()
    off = pd.read_csv(INTERIM / "flytipping_panel.csv")[["LAD25CD", "year", "total"]]
    v = fms.merge(off, on=["LAD25CD", "year"]).dropna()
    v["fms_share"] = v["n_flytip"] / v["total"]
    return v


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    d = lsoa_panel()
    m = models(d)
    m.to_csv(OUT / "fms_model_results.csv", index=False)
    desc = descriptives(d)
    desc.to_csv(OUT / "fms_descriptives.csv", index=False)
    v = validate(d)
    v.to_csv(INTERIM / "fms_validation.csv", index=False)
    pd.set_option("display.width", 200)
    print(m[m.term.isin(["t_hwrc_5", "private_rent_10", "no_car_10", "rural"])].round(3).to_string(index=False))
    print(desc.round(2).to_string(index=False))
    act = v[v["n_flytip"] >= 50]
    print("validation: council-years with 50+ reports", len(act),
          "| log-log correlation", round(np.corrcoef(np.log(act["n_flytip"]), np.log(act["total"]))[0, 1], 2))
