"""Census 2021 covariates from the ONS Census API, for councils (on December 2025
codes) and LSOAs.

Variables follow the drivers in docs/research_brief.md: tenure (private renting
as a proxy for residential churn), car availability (ability to reach an HWRC),
flats and converted/shared houses (communal bins, HMOs), full-time students and
household deprivation."""
import time
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
API = "https://api.beta.ons.gov.uk/v1/population-types/{pt}/census-observations"

TABLES = {  # name: (population type, dimension)
    "tenure": ("HH", "hh_tenure_9a"),
    "cars": ("HH", "number_of_cars_6a"),
    "accommodation": ("HH", "accommodation_type"),
    "deprivation": ("HH", "hh_deprivation"),
    "econ": ("UR", "economic_activity_status_12a"),
}


def _get(pt: str, area_param: str, dim: str) -> list:
    for attempt in range(6):
        r = requests.get(API.format(pt=pt), params={"area-type": area_param, "dimensions": dim}, timeout=600)
        if r.ok:
            return [(o["dimensions"][0]["option_id"], o["dimensions"][1]["option_id"],
                     o["dimensions"][1]["option"], o["observation"]) for o in r.json()["observations"]]
        time.sleep(2 ** attempt)
    r.raise_for_status()


def fetch(area_type: str, pt: str, dim: str, batch: int = 300) -> pd.DataFrame:
    cache = RAW / f"census_{area_type}_{dim}.csv"
    if cache.exists():
        return pd.read_csv(cache)
    if area_type == "lsoa":
        # The API refuses whole-country LSOA queries, so request code lists in batches
        codes = gpd.read_file(RAW / "lsoa21_pwc.gpkg", columns=["LSOA21CD"], ignore_geometry=True)["LSOA21CD"].tolist()
        rows = []
        for i in range(0, len(codes), batch):
            rows += _get(pt, "lsoa," + ",".join(codes[i:i + batch]), dim)
    else:
        rows = _get(pt, area_type, dim)
    df = pd.DataFrame(rows, columns=["area", "option_id", "option", "n"])
    df.to_csv(cache, index=False)
    return df


def shares(area_type: str) -> pd.DataFrame:
    out = {}
    for name, (pt, dim) in TABLES.items():
        d = fetch(area_type, pt, dim)
        d = d[d["option_id"].astype(str) != "-8"]
        w = d.pivot_table(index="area", columns="option", values="n", aggfunc="sum")
        tot = w.sum(axis=1)
        if name == "tenure":
            out["households"] = tot
            out["private_rent_share"] = w.filter(like="Private rented").sum(axis=1) / tot
            out["social_rent_share"] = w.filter(like="Social rented").sum(axis=1) / tot
        elif name == "cars":
            out["no_car_share"] = w["No cars or vans in household"] / tot
        elif name == "accommodation":
            out["flat_share"] = (w.filter(like="flats").sum(axis=1)
                                 + w.filter(like="converted").sum(axis=1)
                                 + w.filter(like="commercial building").sum(axis=1)) / tot
            out["converted_share"] = w.filter(like="converted or shared house").sum(axis=1) / tot
            out["terraced_share"] = w["Terraced"] / tot
        elif name == "deprivation":
            out["hh_deprived_2plus_share"] = w.filter(regex="two|three|four").sum(axis=1) / tot
        elif name == "econ":
            out["residents_16plus"] = tot
            out["student_share"] = w.filter(regex="full-time student: |Inactive: Student|inactive: Student").sum(axis=1) / tot
    return pd.DataFrame(out).rename_axis("code").reset_index()


def lsoa_covariates() -> pd.DataFrame:
    """Residents (for population weighting), households, car availability and tenure."""
    pop = fetch("lsoa", "UR", "sex").groupby("area")["n"].sum().rename("residents")
    cars = fetch("lsoa", "HH", "number_of_cars_6a")
    cars = cars[cars["option_id"].astype(str) != "-8"]
    hh = cars.groupby("area")["n"].sum().rename("households")
    no_car = cars[cars["option_id"].astype(str) == "0"].groupby("area")["n"].sum() / hh
    ten = fetch("lsoa", "HH", "hh_tenure_9a")
    ten = ten[ten["option_id"].astype(str) != "-8"]
    prs = ten[ten["option_id"].astype(str).isin(["5", "6"])].groupby("area")["n"].sum() / ten.groupby("area")["n"].sum()
    return pd.concat([pop, hh, no_car.rename("no_car_share"), prs.rename("private_rent_share")],
                     axis=1).rename_axis("LSOA21CD").reset_index()


def council_covariates() -> pd.DataFrame:
    s = shares("ltla")
    lk = pd.read_csv(INTERIM / "lad_to_lad25.csv")[["old_code", "LAD25CD"]]
    s = s.merge(lk, left_on="code", right_on="old_code")
    # Recombine shares for merged councils, weighting by households / residents
    hh_cols = [c for c in s.columns if c.endswith("_share") and c != "student_share"]
    for c in hh_cols:
        s[c] = s[c] * s["households"]
    s["student_share"] = s["student_share"] * s["residents_16plus"]
    g = s.groupby("LAD25CD")[hh_cols + ["student_share", "households", "residents_16plus"]].sum()
    g[hh_cols] = g[hh_cols].div(g["households"], axis=0)
    g["student_share"] = g["student_share"] / g["residents_16plus"]
    return g.reset_index()


if __name__ == "__main__":
    c = council_covariates()
    c.to_csv(INTERIM / "census_council.csv", index=False)
    print(c.describe().T.to_string())
    l = lsoa_covariates()
    l.to_csv(INTERIM / "census_lsoa.csv", index=False)
    print(l.describe().T.to_string())
