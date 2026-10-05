"""Where does each kind of fly-tipping happen, relative to who lives nearby?

Hypotheses (from the owner):
- private renting: bags left near the home, so bag reports rise with private
  renting in the neighbourhood itself;
- no car: either large items left outside the home (bulky reports rise with
  car-less households in the neighbourhood itself), or waste handed to paid
  carriers and dumped elsewhere (construction and bulky reports rise with
  car-less households in the surrounding area, not the neighbourhood itself).

For each waste type, FixMyStreet reports per neighbourhood (LSOA) and year are
compared within the same council and year, with both the neighbourhood's own
shares of private renters and car-less households and the same shares across
the surrounding area (other neighbourhoods within RING_KM, weighted by
households), plus density and rural or urban.
"""
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyfixest as pf
from scipy.spatial import cKDTree

from fms_analysis import INTERIM, OUT, RAW, lsoa_panel

RING_KM = 8
OUTCOMES = {
    "bags": "Bags", "bulky": "Bulky items", "construction": "Construction / DIY",
    "garden": "Garden waste", "bags_doorstep": "Bags, doorstep or street",
    "bulky_doorstep": "Bulky items, doorstep or street",
    "construction_out_of_the_way": "Construction, out-of-the-way place",
    "bulky_out_of_the_way": "Bulky items, out-of-the-way place",
}


def surrounding_shares() -> pd.DataFrame:
    """Household-weighted private renting and no-car shares of all other
    neighbourhoods within RING_KM of each neighbourhood's centre."""
    pwc = gpd.read_file(RAW / "lsoa21_pwc.gpkg")
    cen = pd.read_csv(INTERIM / "census_lsoa.csv")
    p = pd.DataFrame({"LSOA21CD": pwc["LSOA21CD"], "x": pwc.geometry.x, "y": pwc.geometry.y}).merge(cen, on="LSOA21CD")
    xy = p[["x", "y"]].to_numpy()
    hh = p["households"].to_numpy(float)
    prs = (p["private_rent_share"] * p["households"]).to_numpy(float)
    nocar = (p["no_car_share"] * p["households"]).to_numpy(float)
    nbrs = cKDTree(xy).query_ball_point(xy, RING_KM * 1000)
    out = np.zeros((len(p), 2))
    for i, nb in enumerate(nbrs):
        nb = [j for j in nb if j != i]
        w = hh[nb].sum()
        out[i] = (prs[nb].sum() / w, nocar[nb].sum() / w) if w else (np.nan, np.nan)
    return pd.DataFrame({"LSOA21CD": p["LSOA21CD"], "ring_private_rent_10": out[:, 0] / 0.10,
                         "ring_no_car_10": out[:, 1] / 0.10})


def data() -> pd.DataFrame:
    d = lsoa_panel()
    types = pd.read_csv(INTERIM / "fms_types_lsoa_year.csv")
    d = d.merge(types, on=["LSOA21CD", "year"], how="left")
    for c in OUTCOMES:
        d[c] = d[c].fillna(0)
    d = d.merge(surrounding_shares(), on="LSOA21CD")
    tot = d.groupby("lad_year")["n_flytip"].transform("sum")
    return d[tot >= 50]


def models(d: pd.DataFrame) -> pd.DataFrame:
    rhs = "private_rent_10 + no_car_10 + ring_private_rent_10 + ring_no_car_10 + log_density + rural"
    rows = []
    for y, label in OUTCOMES.items():
        m = pf.fepois(f"{y} ~ {rhs} | lad_year", data=d, offset="log_residents", vcov={"CRV1": "LAD25CD"})
        for t in ["private_rent_10", "no_car_10", "ring_private_rent_10", "ring_no_car_10", "rural"]:
            b, se = m.coef()[t], m.se()[t]
            rows.append({"outcome": y, "outcome_label": label, "term": t, "irr": np.exp(b),
                         "lo": np.exp(b - 1.96 * se), "hi": np.exp(b + 1.96 * se), "p": m.pvalue()[t],
                         "n_lsoa_years": int(m._N), "n_councils": d["LAD25CD"].nunique(),
                         "n_reports": int(d[y].sum())})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    d = data()
    r = models(d)
    r.to_csv(OUT / "location_models.csv", index=False)
    pd.set_option("display.width", 220)
    print(r.round(3).to_string(index=False))
