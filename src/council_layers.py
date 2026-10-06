"""Download council fly-tipping incident points published as public ArcGIS Online
layers (found by searching ArcGIS Online; see DATASETS.md).

These layers are publicly viewable but are not released under a stated open
licence, and some hold personal data (staff names, house numbers, addresses).
Only the date, point location, waste type, land type and size are requested from
the server; nothing else is downloaded or stored. Outputs go to
data/raw/council_incidents/arcgis/<council>.csv (not committed); only counts per
neighbourhood and year are used downstream.
"""
import json
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
OUTDIR = ROOT / "data" / "raw" / "council_incidents" / "arcgis"
MONTHLY = ROOT / "data" / "council_layers_monthly.json"
S = requests.Session()
S.headers["User-Agent"] = "litter-research/0.1 (academic study of fly-tipping)"

# council: (layer url, date field, {standard name: source field})
LAYERS = {
    "Newham": ("https://services1.arcgis.com/trOdpHvvP7HrTfdb/arcgis/rest/services/FlytipsAll/FeatureServer/0",
               "Job_raised", {"wtype": "Waste_Type", "land": "Land_Type", "size": "Waste_Size"}),
    "Epping Forest": ("https://services-eu1.arcgis.com/SDWAhoV6ICvQHz6h/arcgis/rest/services/ClosedFlyTips/FeatureServer/0",
                      "Date_Received", {"wtype": "Waste_Type", "land": "Land_Type", "size": "Waste_Size"}),
    "Darlington": ("https://services7.arcgis.com/blduutbadUr0h2Um/arcgis/rest/services/FlyTip_Locations/FeatureServer/0",
                   "CREATED_DT", {"wtype": "TYPE_"}),
    "Wolverhampton": ("https://services2.arcgis.com/5K9ykSNwoxdIgeYH/arcgis/rest/services/Flytipping_April_2024/FeatureServer/0",
                      "Job_Entry", {"wtype": "Job_Type_N"}),
    "Stratford-on-Avon": ("https://services3.arcgis.com/M5OlHZ2eXvqB8aGO/arcgis/rest/services/flytip_contrators/FeatureServer/0",
                          "RECEPD", {}),
    "Kingston upon Thames": ("https://services2.arcgis.com/HGokIRbN2kiuIxW5/arcgis/rest/services/CRM_Flytip/FeatureServer/0",
                             "REQUEST_DATE", {}),
}


def fetch(url: str, fields: list[str]) -> pd.DataFrame:
    """All features, paged by object id, with only the given fields and the point
    geometry in British National Grid."""
    ids = S.get(url + "/query", params={"where": "1=1", "returnIdsOnly": "true", "f": "json"}, timeout=120).json()
    oids = sorted(ids.get("objectIds") or [])
    rows = []
    for i in range(0, len(oids), 1000):
        for attempt in range(5):
            try:
                r = S.post(url + "/query", data={"objectIds": ",".join(map(str, oids[i:i + 1000])),
                                                 "outFields": ",".join(fields) or "", "returnGeometry": "true",
                                                 "outSR": "27700", "f": "json"}, timeout=120).json()
                break
            except (requests.RequestException, ValueError):
                time.sleep(5 * (attempt + 1))
        for f in r.get("features", []):
            g = f.get("geometry") or {}
            rows.append({**f["attributes"], "x": g.get("x"), "y": g.get("y")})
    return pd.DataFrame(rows)


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    for council, (url, date_field, extra) in LAYERS.items():
        d = fetch(url, [date_field] + list(extra.values()))
        t = d[date_field]
        dates = pd.to_datetime(t, unit="ms", errors="coerce") if pd.api.types.is_numeric_dtype(t) \
            else pd.to_datetime(t, dayfirst=True, errors="coerce")
        out = pd.DataFrame({"year": dates.dt.year, "month": dates.dt.month, "x": d["x"], "y": d["y"]})
        for k, v in extra.items():
            out[k] = d[v]
        out.to_csv(OUTDIR / f"{council}.csv", index=False)
        print(f"{council}: {len(out):,} incidents, {out['year'].min()} to {out['year'].max()}")
    for council in ("West Oxfordshire", "Cotswold"):
        frames = []
        for m in [m for m in json.load(open(MONTHLY)) if m["council"] == council]:
            d = fetch(m["url"], [])
            frames.append(pd.DataFrame({"year": m["year"], "month": m["month"], "x": d.get("x"), "y": d.get("y")}))
        out = pd.concat(frames, ignore_index=True)
        out.to_csv(OUTDIR / f"{council}.csv", index=False)
        print(f"{council}: {len(out):,} incidents from {len(frames)} monthly layers")


if __name__ == "__main__":
    main()
