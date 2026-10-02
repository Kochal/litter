"""Download ONS geography (LSOA population-weighted centroids, LAD boundaries)
from the ONS Open Geography Portal ArcGIS feature services."""
import time
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import LinearRing, MultiPolygon, Point, Polygon

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
ONS = "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services"
LAYERS = {
    "lsoa21_pwc": f"{ONS}/LSOA_PopCentroids_EW_2021_V4/FeatureServer/0",
    "lad25_bgc": f"{ONS}/Local_Authority_Districts_DEC_2025_Boundaries_UK_BGC/FeatureServer/0",
}


def _esri_geometry(g: dict):
    if g is None:
        return None
    if "x" in g:
        return Point(g["x"], g["y"])
    # Esri polygons are a flat list of rings: clockwise rings are shells,
    # anticlockwise rings are holes belonging to the shell that contains them
    shells, holes = [], []
    for ring in g["rings"]:
        (shells if not LinearRing(ring).is_ccw else holes).append(ring)
    polys = []
    for sh in shells:
        shell_poly = Polygon(sh)
        inner = [h for h in holes if shell_poly.contains(Point(h[0]))]
        polys.append(Polygon(sh, inner))
    return polys[0] if len(polys) == 1 else MultiPolygon(polys)


def _esri_to_gdf(js: dict) -> gpd.GeoDataFrame:
    """These services only return Esri JSON, so convert it by hand."""
    feats = js.get("features", [])
    attrs = pd.DataFrame([f["attributes"] for f in feats])
    geoms = [_esri_geometry(f.get("geometry")) for f in feats]
    return gpd.GeoDataFrame(attrs, geometry=geoms, crs=27700)


def _get_with_retry(url: str, params: dict, tries: int = 8) -> requests.Response:
    """The ONS ArcGIS services intermittently answer valid queries with HTTP 400 /
    'Invalid query parameters', so retry with backoff."""
    for i in range(tries):
        r = requests.get(url, params=params, timeout=300)
        if r.ok and '"error"' not in r.text[:200]:
            return r
        time.sleep(2 ** i)
    raise RuntimeError(f"{url} failed after {tries} tries: {r.text[:300]}")


def fetch_layer(url: str, page: int = 1000) -> gpd.GeoDataFrame:
    """Page through an ArcGIS feature layer (by object id, which these services
    handle more reliably than resultOffset) and return it in British National Grid."""
    meta = _get_with_retry(url, {"f": "json"}).json()
    oid = meta.get("objectIdField") or next(
        f["name"] for f in meta["fields"] if f["type"] == "esriFieldTypeOID")
    frames, last = [], -1
    while True:
        params = {"where": f"{oid} > {last}", "outFields": "*", "outSR": 27700, "f": "json",
                  "orderByFields": oid, "resultRecordCount": page}
        r = _get_with_retry(f"{url}/query", params)
        gdf = _esri_to_gdf(r.json())
        if gdf.empty:
            break
        frames.append(gdf)
        last = int(gdf[oid].max())
    return gpd.GeoDataFrame(pd.concat(frames, ignore_index=True), crs=27700)

if __name__ == "__main__":
    RAW.mkdir(parents=True, exist_ok=True)
    for name, url in LAYERS.items():
        out = RAW / f"{name}.gpkg"
        if out.exists():
            continue
        g = fetch_layer(url)
        g.to_file(out, driver="GPKG")
        print(name, len(g), list(g.columns))
