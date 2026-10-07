"""Map of the change in drive time to the nearest recycling centre, 2012 to 2024,
for every neighbourhood (LSOA) in England and Wales, using the verified closure
history (verified_history.py, access_panel.py). Closures in that history are
marked. Writes outputs/fig_drive_time_map.png and outputs/drive_time_change.csv
(change per neighbourhood, for the shareable page).
"""
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
OUT = ROOT / "outputs"

BINS = [-99, -1, 1, 3, 5, 99]
LABELS = ["Shorter by 1+ min", "Little change (under 1 min)", "Longer by 1 to 3 min", "Longer by 3 to 5 min",
          "Longer by 5+ min"]
COLOURS = ["#7fb3e0", "#e9e7e1", "#f2c879", "#e0813a", "#b4311f"]
SURFACE, INK, INK2 = "#fcfcfb", "#0b0b0b", "#52514e"


def change() -> pd.DataFrame:
    t = pd.read_csv(INTERIM / "lsoa_hwrc_times_panel_verified.csv")
    w = t.pivot_table(index="LSOA21CD", columns="year", values="t_hwrc_min")
    out = pd.DataFrame({"t2012": w[2012], "t2024": w[2024]})
    out["change"] = out["t2024"] - out["t2012"]
    # Largest rise at any point (a centre may close and a new one open later)
    out["max_rise"] = (w.cummax(axis=1).sub(w[2012], axis=0)).max(axis=1)
    return out.reset_index()


def main():
    c = change()
    c.round(2).to_csv(OUT / "drive_time_change.csv", index=False)
    lsoa = gpd.read_file(RAW / "lsoa21_bsc_ruc.gpkg", columns=["LSOA21CD"]).merge(c, on="LSOA21CD")
    lsoa["band"] = pd.cut(lsoa["change"], BINS, labels=False, right=False)
    hist = pd.read_csv(INTERIM / "hwrc_england_history_verified.csv")
    closed = hist[(hist["last"] < 2024) & (hist["last"] >= 2012)]
    cmap, norm = ListedColormap(COLOURS), BoundaryNorm(np.arange(-0.5, 5), 5)

    fig = plt.figure(figsize=(12, 10.5), facecolor=SURFACE)
    ax = fig.add_axes([0.0, 0.0, 0.66, 0.93])
    lsoa.plot(column="band", cmap=cmap, norm=norm, ax=ax, linewidth=0)
    ax.scatter(closed["easting"], closed["northing"], s=10, marker="x", color=INK, linewidths=0.8)
    ax.set_xlim(150000, 660000)  # leaves out the Isles of Scilly
    ax.set_ylim(5000, 665000)
    ax.set_axis_off()
    fig.text(0.01, 0.975, "Change in drive time to the nearest recycling centre, 2012 to 2024 "
             "(England: verified closure history; Wales: current sites only)", fontsize=11, color=INK, va="top")
    n = lsoa["band"].value_counts().reindex(range(5), fill_value=0)
    handles = [Patch(color=COLOURS[i], label=f"{LABELS[i]} ({n[i]:,})") for i in range(5)]
    handles.append(plt.Line2D([], [], marker="x", ls="", color=INK, label=f"Closure, verified ({len(closed)})"))
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.0, 0.97), frameon=False, fontsize=9,
              title=f"Neighbourhoods ({len(lsoa):,})", title_fontsize=9, alignment="left")
    # Insets where several closures cluster
    insets = [("Greater London", (503000, 562000, 155000, 202000)),
              ("Leeds and Bradford", (400000, 450000, 415000, 450000)),
              ("Peterborough", (500000, 540000, 285000, 315000))]
    for k, (name, (x0, x1, y0, y1)) in enumerate(insets):
        ia = fig.add_axes([0.67, 0.64 - k * 0.315, 0.32, 0.27])
        sub = lsoa.cx[x0:x1, y0:y1]
        sub.plot(column="band", cmap=cmap, norm=norm, ax=ia, linewidth=0.05, edgecolor=SURFACE)
        cc = closed[closed["easting"].between(x0, x1) & closed["northing"].between(y0, y1)]
        ia.scatter(cc["easting"], cc["northing"], s=24, marker="x", color=INK, linewidths=1.2)
        ia.set_xlim(x0, x1)
        ia.set_ylim(y0, y1)
        ia.set_axis_off()
        k3 = int((sub["change"] >= 3).sum())
        ia.set_title(f"{name}\n{k3} neighbourhoods 3+ min longer", fontsize=9, loc="left", color=INK2)
    fig.savefig(OUT / "fig_drive_time_map.png", dpi=150, facecolor=SURFACE)
    print(n.to_dict(), "3+ min:", int((lsoa["change"] >= 3).sum()), "max rise 3+:", int((lsoa["max_rise"] >= 3).sum()))


if __name__ == "__main__":
    main()
