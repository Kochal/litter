"""Council-by-year HWRC access, 2012 to 2024.

For each year, drive time from every LSOA population-weighted centroid to the
nearest HWRC open that year (English LSOAs to English HWRCs from that year's
Waste Data Interrogator; Welsh LSOAs to the current NRW list, since no Welsh
history is available), then population-weighted council averages.

Most councils restrict HWRCs to their own residents, so cross-border use is
ignored apart from the England/Wales split; council boundaries inside England are
not enforced (a resident's nearest site may be in a neighbouring council)."""
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

from accessibility import load_network, nearest_time, snap

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
YEARS = range(2012, 2025)


MATCH_M = 250  # sites within this distance in different years are the same site


def english_hwrc_history() -> pd.DataFrame:
    """One row per physical English HWRC with the years it appears in the WDI.

    Sites are matched across years by location. A site missing from a year's
    returns but present before and after is treated as open in the gap, so only
    sites that stop appearing count as closures (and only new ones as openings)."""
    frames = []
    for y in YEARS:
        f = INTERIM / ("hwrc_england_2024.csv" if y == 2024 else f"hwrc_england_{y}.csv")
        frames.append(pd.read_csv(f).assign(year=y))
    allh = pd.concat(frames, ignore_index=True)
    xy = allh[["easting", "northing"]].to_numpy(float)
    # Link site-year points within MATCH_M of each other into physical sites
    pairs = cKDTree(xy).query_pairs(MATCH_M, output_type="ndarray")
    n = len(allh)
    adj = coo_matrix((np.ones(len(pairs)), (pairs[:, 0], pairs[:, 1])), shape=(n, n))
    allh["site_id"] = connected_components(adj, directed=False)[1]
    sites = allh.groupby("site_id").agg(
        easting=("easting", "median"), northing=("northing", "median"),
        name=("Site Name", "last"), first=("year", "min"), last=("year", "max"),
        n_years=("year", "nunique")).reset_index()
    return sites


def hwrc_for_year(year: int, history: pd.DataFrame) -> pd.DataFrame:
    eng = history[(history["first"] <= year) & (history["last"] >= year)]
    wal = pd.read_csv(INTERIM / "hwrc_all.csv").query("nation == 'Wales'")
    return pd.concat([eng[["easting", "northing"]].assign(nation="England"),
                      wal[["easting", "northing"]].assign(nation="Wales")])


def lsoa_times() -> pd.DataFrame:
    graph, xy, entry = load_network()
    lsoa = gpd.read_file(RAW / "lsoa21_pwc.gpkg")
    nation = np.where(lsoa["LSOA21CD"].str[0] == "E", "England", "Wales")
    c_node, c_extra = snap(np.c_[lsoa.geometry.x, lsoa.geometry.y], xy, entry)
    history = english_hwrc_history()
    history.to_csv(INTERIM / "hwrc_england_history.csv", index=False)
    out = []
    for year in YEARS:
        h = hwrc_for_year(year, history)
        t = np.full(len(lsoa), np.nan)
        for nat in ("England", "Wales"):
            f = h[h["nation"] == nat]
            f_node, f_extra = snap(f[["easting", "northing"]].to_numpy(float), xy, entry)
            tn = nearest_time(graph, f_node, f_extra)
            m = (nation == nat) & (c_node >= 0)
            t[m] = tn[c_node[m]] + c_extra[m]
        t[np.isinf(t)] = np.nan
        out.append(pd.DataFrame({"LSOA21CD": lsoa["LSOA21CD"], "year": year, "t_hwrc_min": t,
                                 "n_hwrc_nation": h.groupby("nation").size().reindex(nation).values}))
        print(year, len(h), np.nanmedian(t))
    return pd.concat(out, ignore_index=True)


def lsoa_to_lad() -> pd.DataFrame:
    lsoa = gpd.read_file(RAW / "lsoa21_pwc.gpkg")[["LSOA21CD", "geometry"]]
    lad = gpd.read_file(RAW / "lad25_bgc.gpkg")[["LAD25CD", "geometry"]]
    j = gpd.sjoin(lsoa, lad, how="left", predicate="within")
    miss = j["LAD25CD"].isna()
    if miss.any():  # centroids just outside generalised coastlines
        near = gpd.sjoin_nearest(lsoa[miss.values], lad, how="left")
        j.loc[miss, "LAD25CD"] = near["LAD25CD"].values
    return j[["LSOA21CD", "LAD25CD"]].drop_duplicates("LSOA21CD")


def council_panel(times: pd.DataFrame) -> pd.DataFrame:
    cen = pd.read_csv(INTERIM / "census_lsoa.csv")
    acc24 = pd.read_csv(INTERIM / "lsoa_access.csv")
    d = (times.merge(lsoa_to_lad(), on="LSOA21CD")
              .merge(cen, on="LSOA21CD")
              .merge(acc24[["LSOA21CD", "t_landfill_min", "t_transfer_min", "n_hwrc_15min"]], on="LSOA21CD"))
    d = d.dropna(subset=["t_hwrc_min"])
    d["w"] = d["residents"]
    d["w_nocar"] = d["households"] * d["no_car_share"]

    def agg(g):
        w, wn = g["w"], g["w_nocar"]
        return pd.Series({
            "t_hwrc_mean": np.average(g["t_hwrc_min"], weights=w),
            "t_hwrc_nocar": np.average(g["t_hwrc_min"], weights=wn),
            "share_over_15": np.average(g["t_hwrc_min"] > 15, weights=w),
            "share_over_20": np.average(g["t_hwrc_min"] > 20, weights=w),
            "t_landfill_mean": np.average(g["t_landfill_min"], weights=w),
            "t_transfer_mean": np.average(g["t_transfer_min"], weights=w),
            "n_hwrc_15min_mean": np.average(g["n_hwrc_15min"], weights=w),
        })
    return d.groupby(["LAD25CD", "year"]).apply(agg).reset_index()


if __name__ == "__main__":
    cache = INTERIM / "lsoa_hwrc_times_panel.csv"
    times = pd.read_csv(cache) if cache.exists() else lsoa_times()
    times.to_csv(cache, index=False)
    p = council_panel(times)
    p.to_csv(INTERIM / "council_access_panel.csv", index=False)
    print(p.groupby("year")[["t_hwrc_mean", "share_over_15"]].mean().to_string())
