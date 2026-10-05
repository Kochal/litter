"""Classify FixMyStreet fly-tipping reports by waste type and setting from their
title, description and category, and count them per neighbourhood (LSOA) and year.

The report text is used only inside this pipeline: reporter names are never
loaded, and only counts per neighbourhood and year are written out.
"""
import json
import re
from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
REPORTS = RAW / "fixmystreet" / "reports" / "flytip"

# Waste types (a report can match several)
TYPES = {
    "bags": r"\b(?:black|bin|rubbish|refuse|carrier|blue|plastic)? ?(?:bags?|sacks?)\b|\bbin ?bags?\b|household (?:waste|rubbish)",
    "bulky": r"mattress|sofa|settee|couch|armchair|furniture|wardrobe|\bbeds?\b|bed ?frame|chest of drawers|"
             r"\bchairs?\b|\btables?\b|cabinet|\bdesk\b|fridge|freezer|washing machine|dishwasher|cooker|\boven\b|"
             r"microwave|white goods|\btvs?\b|television|carpet|rug|suite",
    "construction": r"rubble|builders?|building (?:waste|materials?)|plasterboard|\bbricks?\b|\btiles?\b|concrete|"
                    r"hardcore|\bsoil\b|\btimber\b|kitchen units?|bathroom|\btoilet\b|\bsink\b|\bbath\b|"
                    r"\bdoors?\b|windows?|asbestos|paint tins?|insulation|roofing|scaffold|\bdiy\b|renovation",
    "garden": r"garden waste|green waste|cuttings|branches|hedge trimmings|grass|\bleaves\b|tree (?:waste|cuttings)",
    "tyres": r"\btyres?\b|\btires?\b",
}
# Setting, where the text says so
SETTING = {
    "doorstep": r"\b(?:outside|opposite|side of|front of|rear of|next to|by) (?:\w+ ){0,3}(?:no\.? ?)?\d+[a-z]?\b|\boutside (?:my|our|the) (?:house|home|flat|property|door|gate)|"
                r"\bpavement\b|next to (?:the )?(?:bins?|communal bins?|bin store)|bin store|"
                r"\bfront (?:garden|of (?:the )?(?:house|property|flats?))|\bdoorstep\b|\bflats?\b",
    "out_of_the_way": r"off[- ]road|lay[- ]?by|\bfield\b|field gate|\bgateway\b|hedge ?row|\bhedge\b|\bwoods\b|woodland|"
                      r"\bverge\b|country lane|farm track|\btrack\b|bridleway|\bcanal\b|\briver\b|\bstream\b|"
                      r"industrial estate|car park",
}


def classify(text: str) -> dict:
    t = text.lower()
    out = {k: bool(re.search(p, t)) for k, p in {**TYPES, **SETTING}.items()}
    out["unclassified"] = not any(out[k] for k in TYPES)
    return out


def load() -> pd.DataFrame:
    rows = []
    for f in sorted(REPORTS.glob("*.jsonl")):
        for line in f.open():
            r = json.loads(line)
            text = " ".join(str(r.get(k) or "") for k in ("service_code", "title", "detail"))
            rows.append({"id": r.get("service_request_id"), "datetime": r.get("requested_datetime"),
                         "lat": r.get("lat"), "long": r.get("long"), **classify(text)})
    df = pd.DataFrame(rows).drop_duplicates("id").dropna(subset=["lat", "long"])
    df["year"] = pd.to_datetime(df["datetime"], utc=True).dt.year
    return df


def by_lsoa(df: pd.DataFrame) -> pd.DataFrame:
    pts = gpd.GeoDataFrame(df.drop(columns=["lat", "long"]),
                           geometry=gpd.points_from_xy(df["long"].astype(float), df["lat"].astype(float)),
                           crs=4326).to_crs(27700)
    lsoa = gpd.read_file(RAW / "lsoa21_bsc_ruc.gpkg", columns=["LSOA21CD"])
    j = gpd.sjoin(pts, lsoa, predicate="within", how="inner")
    cols = list(TYPES) + list(SETTING) + ["unclassified"]
    out = j.groupby(["LSOA21CD", "year"])[cols].sum().astype(int)
    # Joint type-by-setting counts for the two hypotheses
    for t in ("bags", "bulky", "construction"):
        for s in SETTING:
            out[f"{t}_{s}"] = (j[t] & j[s]).groupby([j["LSOA21CD"], j["year"]]).sum().astype(int)
    return out.reset_index()


if __name__ == "__main__":
    df = load()
    cols = list(TYPES) + list(SETTING) + ["unclassified"]
    share = df[cols].mean().round(3)
    print(len(df), "reports"); print(share.to_string())
    by_lsoa(df).to_csv(INTERIM / "fms_types_lsoa_year.csv", index=False)
