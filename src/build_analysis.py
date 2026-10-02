"""Assemble the council-by-year analysis table (England and Wales, 2012/13 to
2024/25) from the interim outputs of the other scripts."""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INTERIM = ROOT / "data" / "interim"
OUT = ROOT / "data" / "analysis"

# Statutory joint waste disposal authorities in metropolitan areas and London.
# Elsewhere the WDA is the county (two-tier areas) or the unitary council itself.
JOINT_WDA = {
    "Greater Manchester": ["Bolton", "Bury", "Manchester", "Oldham", "Rochdale", "Salford",
                           "Stockport", "Tameside", "Trafford"],
    "Merseyside": ["Knowsley", "Liverpool", "St. Helens", "Sefton", "Wirral"],
    "North London": ["Barnet", "Camden", "Enfield", "Hackney", "Haringey", "Islington",
                     "Waltham Forest"],
    "West London": ["Brent", "Ealing", "Harrow", "Hillingdon", "Hounslow", "Richmond upon Thames"],
    "East London": ["Barking and Dagenham", "Havering", "Newham", "Redbridge"],
    "Western Riverside": ["Hammersmith and Fulham", "Kensington and Chelsea", "Lambeth",
                          "Wandsworth"],
}

# Waste-type groupings used as outcomes (see docs/research_brief.md, section 5)
OUTCOMES = {
    "hwrc_type": ["waste_other_household", "waste_white_goods", "waste_electrical", "waste_green"],
    "bags_household": ["waste_bags_household"],
    "cde": ["waste_cde"],
    "commercial": ["waste_bags_commercial", "waste_other_commercial"],
    "placebo": ["waste_animal", "waste_clinical", "waste_vehicle"],
    "car_boot_to_van": ["size_car_boot", "size_small_van", "size_transit_van"],
    "tipper_plus": ["size_tipper", "size_multi"],
    "highway_alley": ["land_highway", "land_back_alley", "land_footpath"],
}


def wda_lookup(h: pd.DataFrame) -> pd.Series:
    wda = h["CTYUA25NM"].copy()
    for name, members in JOINT_WDA.items():
        wda[h["LAD25NM"].isin(members)] = name
    return wda


def build() -> pd.DataFrame:
    ft = pd.read_csv(INTERIM / "flytipping_panel.csv")
    pop = pd.read_csv(INTERIM / "population.csv")
    cen = pd.read_csv(INTERIM / "census_council.csv")
    acc = pd.read_csv(INTERIM / "council_access_panel.csv")
    h = pd.read_csv(INTERIM / "lad25_hierarchy.csv")
    h["region"] = h["RGN25NM"].fillna("Wales")
    h["wda"] = wda_lookup(h)

    d = (ft.merge(pop, on=["LAD25CD", "year"], how="left")
           .merge(cen, on="LAD25CD", how="left")
           .merge(acc, on=["LAD25CD", "year"], how="left")
           .merge(h[["LAD25CD", "region", "wda", "CTYUA25NM"]], on="LAD25CD", how="left"))
    for k, cols in OUTCOMES.items():
        d[k] = d[cols].sum(axis=1, min_count=len(cols))

    rb = d["reporting_basis"].fillna(":")
    d["basis_public_only"] = rb.str.startswith("Customer").astype(int)
    d["basis_changed"] = rb.str.contains("changed|Mixed", regex=True).astype(int)
    d["two_tier"] = (d["CTYUA25NM"] != d["LAD25NM"] if "LAD25NM" in d else False).astype(int)
    d["log_pop"] = np.log(d["population"])
    area = pd.read_csv(INTERIM / "lad25_area.csv") if (INTERIM / "lad25_area.csv").exists() else None
    if area is not None:
        d = d.merge(area, on="LAD25CD", how="left")
        d["log_density"] = np.log(d["population"] / d["area_km2"])
    return d


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    d = build()
    d.to_csv(OUT / "council_year.csv", index=False)
    print(d.shape)
    print(d[["total", "hwrc_type", "t_hwrc_mean", "private_rent_share", "population"]].describe().T)
