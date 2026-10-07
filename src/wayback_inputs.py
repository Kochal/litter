"""Input for scripts/wayback_hwrc_rules.py: every recycling centre in England and
Wales with the website domains of the councils that would publish its opening
hours, booking rules and charges.

- England: sites from the corrected history (verified_history.py); Wales: the
  current NRW permit register.
- Council websites come from Wikidata (official website, P856, by ONS code,
  P836), saved in data/raw/wikidata_council_websites.json. Each site gets the
  domain of the council that runs recycling centres there (the county in
  two-tier areas, otherwise the unitary or borough), the district it sits in, and
  the joint waste authority where there is one.
- Postcodes come from the Environment Agency records (nearest record of the
  site); they are a reliable way to find a site on a council page.
Operator names are not included.
"""
import json
import re
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
OUT = ROOT / "data" / "wayback" / "hwrc_sites_all.csv"

# Joint waste authorities that run the centres and publish their details
JOINT = {
    **{f"E0800000{i}": ["recycleforgreatermanchester.com", "gmwda.gov.uk"] for i in range(1, 10)},
    "E08000010": ["recycleforgreatermanchester.com", "gmwda.gov.uk"],
    **{c: ["merseysidewda.gov.uk"] for c in ["E08000011", "E08000012", "E08000013", "E08000014", "E08000015", "E06000006"]},
}


def domain(url: str) -> str:
    return re.sub(r"^www\.", "", re.sub(r"^https?://", "", url).split("/")[0].lower())


def websites() -> dict:
    rows = json.load(open(RAW / "wikidata_council_websites.json"))["results"]["bindings"]
    out = {}
    for r in rows:
        out.setdefault(r["code"]["value"], set()).add(domain(r["site"]["value"]))
    return out


def postcodes(sites: pd.DataFrame) -> list:
    frames = [pd.read_csv(f) for f in sorted(INTERIM.glob("hwrc_england_20*.csv"))]
    allh = pd.concat(frames).dropna(subset=["Post Code"]).sort_values("year")
    allh = allh.drop_duplicates(["easting", "northing"], keep="last")
    d, i = cKDTree(allh[["easting", "northing"]].to_numpy(float)).query(sites[["easting", "northing"]].to_numpy(float))
    pc = allh["Post Code"].to_numpy()[i]
    return [p.upper().strip() if dist < 500 else "" for p, dist in zip(pc, d)]


def main():
    eng = pd.read_csv(INTERIM / "hwrc_england_history_verified.csv")
    eng = eng.assign(nation="England", postcode=postcodes(eng))
    wal = pd.read_csv(INTERIM / "hwrc_all.csv").query("nation == 'Wales'")
    wal = pd.DataFrame({"site_id": [f"W{i}" for i in range(len(wal))], "easting": wal["easting"].values,
                        "northing": wal["northing"].values, "name": wal["Site Name"].values, "first": 2012,
                        "last": 9999, "nation": "Wales", "postcode": wal["Post Code"].fillna("").str.upper().values})
    s = pd.concat([eng[wal.columns], wal], ignore_index=True)
    lad = gpd.read_file(RAW / "lad25_bgc.gpkg")[["LAD25CD", "geometry"]]
    pts = gpd.GeoDataFrame(s, geometry=gpd.points_from_xy(s["easting"], s["northing"]), crs=27700)
    j = gpd.sjoin_nearest(pts, lad, how="left").drop_duplicates("site_id")
    hier = pd.read_csv(INTERIM / "lad25_hierarchy.csv")[["LAD25CD", "LAD25NM", "CTYUA25CD", "CTYUA25NM"]]
    j = j.merge(hier, on="LAD25CD", how="left")
    web = websites()
    doms = []
    for r in j.itertuples():
        d = []
        for code in (r.CTYUA25CD, r.LAD25CD):
            d += sorted(web.get(code, []))
        if not d:  # not on Wikidata: most councils use their name, e.g. sheffield.gov.uk
            d.append(re.sub(r"[^a-z]", "", str(r.CTYUA25NM).lower().replace("upon tyne", "")) + ".gov.uk")
        d += JOINT.get(r.LAD25CD, [])
        doms.append(";".join(dict.fromkeys(x for x in d if x)))
    out = pd.DataFrame({"site_id": j["site_id"], "name": j["name"], "nation": j["nation"], "postcode": j["postcode"],
                        "easting": j["easting"], "northing": j["northing"],
                        "council": j["CTYUA25NM"], "district": j["LAD25NM"], "first_year": j["first"],
                        "last_year": j["last"], "domains": doms})
    out.to_csv(OUT, index=False)
    print(len(out), "sites;", out["domains"].str.split(";").explode().nunique(), "domains;",
          (out["domains"] == "").sum(), "without a domain;", (out["postcode"] == "").sum(), "without a postcode")


if __name__ == "__main__":
    main()
