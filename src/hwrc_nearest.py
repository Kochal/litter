"""Which recycling centre is nearest (by drive time) to each neighbourhood (LSOA),
year by year, using the verified closure history for England and the current
register for Wales (the same sites as data/wayback/hwrc_sites_all.csv, whose
site_ids are used). Residents are routed to centres in their own nation, as in
access_panel.py.

Output: data/interim/lsoa_nearest_hwrc.csv (LSOA21CD, year, site_id, minutes).
"""
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra

from accessibility import load_network, snap

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
SITES = ROOT / "data" / "wayback" / "hwrc_sites_all.csv"
YEARS = range(2014, 2025)


def nearest_site(graph, f_node, f_extra) -> tuple[np.ndarray, np.ndarray]:
    """Minutes to, and index of, the nearest facility for every node. Each facility
    gets its own virtual node linked by its connector time, so that a multi-source
    search can report which facility each node is closest to."""
    n, k = graph.shape[0], len(f_node)
    g = graph.tocoo()
    v = n + np.arange(k)
    big = coo_matrix((np.r_[g.data, f_extra + 1e-6], (np.r_[g.row, v], np.r_[g.col, f_node])),
                     shape=(n + k, n + k)).tocsr()
    dist, _, src = dijkstra(big, directed=True, indices=v, min_only=True, return_predecessors=True)
    return dist[:n], np.where(src[:n] >= n, src[:n] - n, -1)


def main():
    graph, xy, entry = load_network()
    lsoa = gpd.read_file(RAW / "lsoa21_pwc.gpkg")
    nation = np.where(lsoa["LSOA21CD"].str[0] == "E", "England", "Wales")
    c_node, c_extra = snap(np.c_[lsoa.geometry.x, lsoa.geometry.y], xy, entry)
    sites = pd.read_csv(SITES, dtype={"site_id": str})
    out = []
    for year in YEARS:
        open_ = sites[(sites["first_year"] <= year) & (sites["last_year"] >= year)]
        sid = np.full(len(lsoa), None, dtype=object)
        mins = np.full(len(lsoa), np.nan)
        for nat in ("England", "Wales"):
            f = open_[open_["nation"] == nat].reset_index(drop=True)
            f_node, f_extra = snap(f[["easting", "northing"]].to_numpy(float), xy, entry)
            ok = f_node >= 0
            f, f_node, f_extra = f[ok].reset_index(drop=True), f_node[ok], f_extra[ok]
            dist, idx = nearest_site(graph, f_node, f_extra)
            m = (nation == nat) & (c_node >= 0)
            node = c_node[m]
            mins[m] = dist[node] + c_extra[m]
            sid[m] = np.where(idx[node] >= 0, f["site_id"].to_numpy()[np.clip(idx[node], 0, None)], None)
        out.append(pd.DataFrame({"LSOA21CD": lsoa["LSOA21CD"], "year": year, "site_id": sid, "minutes": mins}))
        print(year, len(open_), np.nanmedian(mins), flush=True)
    pd.concat(out).to_csv(INTERIM / "lsoa_nearest_hwrc.csv", index=False)


if __name__ == "__main__":
    main()
