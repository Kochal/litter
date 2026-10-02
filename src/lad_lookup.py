"""Map every local authority code used in the fly-tipping returns (2012/13 onward)
to its December 2025 successor district.

All English reorganisations since 2012 merged or recoded whole districts, so a
point inside each old district identifies its successor."""
from pathlib import Path

import geopandas as gpd
import pandas as pd

from geography import ONS, RAW, fetch_layer

ROOT = Path(__file__).resolve().parents[1]
INTERIM = ROOT / "data" / "interim"
HISTORIC = {
    "LAD12": f"{ONS}/LAD_2012_GB_BSC/FeatureServer/0",
    "LAD18": f"{ONS}/LAD_December_2018_Boundaries_UK_BUC_2022/FeatureServer/0",
    "LAD20": f"{ONS}/LAD_DEC_2020_UK_BGC/FeatureServer/0",
    "LAD21": f"{ONS}/LAD_DEC_2021_EW_BUC_RUC/FeatureServer/0",
}


def build_lookup() -> pd.DataFrame:
    lad25 = gpd.read_file(RAW / "lad25_bgc.gpkg")[["LAD25CD", "LAD25NM", "geometry"]]
    rows = []
    for vintage, url in HISTORIC.items():
        cache = RAW / f"{vintage.lower()}_boundaries.gpkg"
        old = gpd.read_file(cache) if cache.exists() else fetch_layer(url)
        if not cache.exists():
            old.to_file(cache, driver="GPKG")
        code = next(c for c in old.columns if c.upper().endswith("CD") and c.upper().startswith("LAD"))
        pts = gpd.GeoDataFrame({"old_code": old[code]}, geometry=old.representative_point(), crs=27700)
        rows.append(gpd.sjoin(pts, lad25, predicate="within")[["old_code", "LAD25CD", "LAD25NM"]])
    current = lad25[["LAD25CD", "LAD25NM"]].assign(old_code=lad25["LAD25CD"])
    lk = pd.concat(rows + [current]).drop_duplicates("old_code", keep="last")
    return lk[lk["old_code"].str[0].isin(["E", "W"])].reset_index(drop=True)


if __name__ == "__main__":
    INTERIM.mkdir(parents=True, exist_ok=True)
    lk = build_lookup()
    lk.to_csv(INTERIM / "lad_to_lad25.csv", index=False)
    changed = lk[lk.old_code != lk.LAD25CD]
    print(len(lk), "codes;", len(changed), "map to a different 2025 code")
