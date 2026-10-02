"""Drive time from every LSOA population-weighted centroid to the nearest waste
facility of each kind, over the OS Open Roads network.

Open Roads has no speed or one-way data, so links are treated as two-way and
given a nominal free-flow speed from their road function and form of way. The
resulting times are best read as a consistent relative measure of access, not
as realistic journey times (urban congestion is ignored)."""
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
ROADS = RAW / "oproad" / "Data" / "oproad_gb.gpkg"

SPEED_KMH = {
    "Motorway": 96, "A Road": 64, "B Road": 56, "Minor Road": 48, "Local Road": 32,
    "Local Access Road": 24, "Restricted Local Access Road": 16, "Secondary Access Road": 16,
}
DUAL_A_ROAD_KMH = 80
FORM_KMH = {"Slip Road": 48, "Roundabout": 24, "Traffic Island Link At Junction": 24}
CONNECTOR_KMH = 20      # straight-line hop from a centroid/facility to the network
MAX_SNAP_M = 2000       # points further than this from any road are left unmatched
TIME_BANDS = (10, 15, 20, 30)


def load_network():
    links = pyogrio.read_dataframe(ROADS, layer="road_link", read_geometry=False, columns=[
        "road_function", "form_of_way", "length", "start_node", "end_node"])
    nodes = pyogrio.read_dataframe(ROADS, layer="road_node", columns=["id"])
    speed = links["road_function"].map(SPEED_KMH).fillna(32).astype(float)
    speed[links["road_function"].eq("A Road") & links["form_of_way"].eq("Dual Carriageway")] = DUAL_A_ROAD_KMH
    form = links["form_of_way"].map(FORM_KMH)
    speed = form.fillna(speed)
    minutes = links["length"] / (speed * 1000 / 60)
    idx = pd.Series(np.arange(len(nodes)), index=nodes["id"].values)
    a, b = idx.reindex(links["start_node"]).values, idx.reindex(links["end_node"]).values
    ok = ~(np.isnan(a) | np.isnan(b))
    a, b, w = a[ok].astype(int), b[ok].astype(int), minutes.values[ok]
    n = len(nodes)
    graph = coo_matrix((np.r_[w, w], (np.r_[a, b], np.r_[b, a])), shape=(n, n)).tocsr()
    # Motorway nodes are not valid entry points (you cannot join a motorway mid-link)
    mway = links["road_function"].eq("Motorway").values[ok] | links["form_of_way"].eq("Slip Road").values[ok]
    non_mway_nodes = np.unique(np.r_[a[~mway], b[~mway]])
    xy = np.c_[nodes.geometry.x.values, nodes.geometry.y.values]
    return graph, xy, non_mway_nodes


def snap(points_xy: np.ndarray, xy: np.ndarray, candidates: np.ndarray):
    tree = cKDTree(xy[candidates])
    dist, i = tree.query(points_xy)
    node = candidates[i]
    node = np.where(dist <= MAX_SNAP_M, node, -1)
    return node, dist / (CONNECTOR_KMH * 1000 / 60)


def nearest_time(graph, sources: np.ndarray, source_extra: np.ndarray) -> np.ndarray:
    """Minutes from the nearest source to every node. Facility-side connector time is
    added by routing from a virtual super-source linked to each facility node."""
    n = graph.shape[0]
    keep = sources >= 0
    sources, source_extra = sources[keep], source_extra[keep]
    # Virtual node n, linked to each facility node with its connector time
    g = graph.tocoo()
    rows = np.r_[g.row, np.full(len(sources), n)]
    cols = np.r_[g.col, sources]
    data = np.r_[g.data, source_extra + 1e-6]
    big = coo_matrix((data, (rows, cols)), shape=(n + 1, n + 1)).tocsr()
    return dijkstra(big, directed=True, indices=n)[:n]


def facility_counts_within(graph, centroid_nodes, fac_nodes, bands=TIME_BANDS) -> pd.DataFrame:
    """Number of facilities reachable within each time band from each centroid,
    computed by a bounded search from each facility."""
    counts = np.zeros((len(centroid_nodes), len(bands)), dtype=int)
    valid = centroid_nodes >= 0
    for f in np.unique(fac_nodes[fac_nodes >= 0]):
        t = dijkstra(graph, directed=False, indices=f, limit=max(bands))
        tc = np.where(valid, t[np.clip(centroid_nodes, 0, None)], np.inf)
        for j, b in enumerate(bands):
            counts[:, j] += tc <= b
    return pd.DataFrame(counts, columns=[f"n_hwrc_{b}min" for b in bands])


def build() -> pd.DataFrame:
    graph, xy, entry_nodes = load_network()
    lsoa = gpd.read_file(RAW / "lsoa21_pwc.gpkg")
    lsoa_xy = np.c_[lsoa.geometry.x, lsoa.geometry.y]
    c_node, c_extra = snap(lsoa_xy, xy, entry_nodes)
    sites = pd.concat([pd.read_csv(INTERIM / "wdi2024_sites.csv"), pd.read_csv(INTERIM / "wales_sites.csv")])
    hwrc = pd.read_csv(INTERIM / "hwrc_all.csv")
    out = pd.DataFrame({"LSOA21CD": lsoa["LSOA21CD"], "snap_min": c_extra})
    layers = {"hwrc": hwrc,
              "landfill": sites[sites["kind"] == "landfill"],
              "transfer": sites[sites["kind"] == "transfer"]}
    for name, fac in layers.items():
        f_node, f_extra = snap(fac[["easting", "northing"]].to_numpy(float), xy, entry_nodes)
        t = nearest_time(graph, f_node, f_extra)
        tc = np.where(c_node >= 0, t[np.clip(c_node, 0, None)] + c_extra, np.nan)
        out[f"t_{name}_min"] = np.where(np.isinf(tc), np.nan, tc)
        if name == "hwrc":
            out = pd.concat([out, facility_counts_within(graph, c_node, f_node)], axis=1)
    return out


if __name__ == "__main__":
    acc = build()
    acc.to_csv(INTERIM / "lsoa_access.csv", index=False)
    print(acc.describe().T.to_string())
