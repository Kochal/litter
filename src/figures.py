"""Figures for docs/results.md (static PNGs, light theme)."""
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import NullFormatter, NullLocator

matplotlib.use("Agg")
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"

SURFACE, INK, INK2, GRID, SERIES = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df", "#2a78d6"
plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "axes.edgecolor": GRID,
    "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2, "text.color": INK,
    "font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
})

TERM_LABELS = {
    "t_hwrc_mean": "HWRC drive time (+5 min)",
    "t_transfer_mean": "Transfer station drive time (+5 min)",
    "t_landfill_mean": "Landfill drive time (+10 min)",
    "private_rent_share": "Private renting (+10 pts)",
    "social_rent_share": "Social renting (+10 pts)",
    "no_car_share": "No car (+10 pts)",
    "flat_share": "Flats (+10 pts)",
    "student_share": "Students (+5 pts)",
    "hh_deprived_2plus_share": "Deprived households (+5 pts)",
    "churn_rate": "Migration churn (+5 pts)",
    "log_density": "Density (x2.7)",
}


def _ratio_axis(ax, lo=0.25, hi=4):
    ax.set_xscale("log")
    ax.set_xlim(lo, hi)
    ticks = [t for t in [0.25, 0.5, 1, 2, 4] if lo <= t <= hi]
    ax.set_xticks(ticks, [f"{t:g}" for t in ticks])
    ax.xaxis.set_minor_locator(NullLocator())
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.axvline(1, color=INK2, lw=1)
    ax.grid(axis="x", color=GRID, lw=0.8)


def forest(res: pd.DataFrame, outcomes: dict, path: Path, title: str):
    terms = list(TERM_LABELS)
    fig, axes = plt.subplots(1, len(outcomes), figsize=(4.2 * len(outcomes), 4.8), sharey=True)
    for ax, (o, label) in zip(axes, outcomes.items()):
        r = res[res["outcome"] == o].set_index("term").reindex(terms)
        y = np.arange(len(terms))[::-1]
        ax.hlines(y, r["lo"], r["hi"], color=SERIES, lw=2)
        ax.plot(r["irr"], y, "o", color=SERIES, ms=6, mec=SURFACE, mew=1.5)
        _ratio_axis(ax)
        ax.set_title(label, fontsize=10, loc="left", color=INK)
        ax.set_xlabel("Incidence rate ratio (95% CI)")
    axes[0].set_yticks(np.arange(len(terms))[::-1], [TERM_LABELS[t] for t in terms])
    fig.suptitle(title, x=0.01, ha="left", fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def event_plot(ev: pd.DataFrame, outcomes: dict, path: Path):
    fig, axes = plt.subplots(1, len(outcomes), figsize=(4 * len(outcomes), 3.4), sharey=True)
    for ax, (o, label) in zip(axes, outcomes.items()):
        r = ev[ev["outcome"] == o].sort_values("event_time")
        r = pd.concat([r, pd.DataFrame({"event_time": [-1], "irr": [1.0], "lo": [1.0], "hi": [1.0]})]).sort_values("event_time")
        ax.fill_between(r["event_time"], r["lo"], r["hi"], color=SERIES, alpha=0.15, lw=0)
        ax.plot(r["event_time"], r["irr"], "-o", color=SERIES, lw=2, ms=5, mec=SURFACE, mew=1.2)
        ax.axhline(1, color=INK2, lw=1)
        ax.axvline(-0.5, color=GRID, lw=1, ls="--")
        ax.set_yscale("log")
        ax.set_yticks([0.5, 0.75, 1, 1.5, 2], ["0.5", "0.75", "1", "1.5", "2"])
        ax.yaxis.set_minor_locator(NullLocator())
        ax.yaxis.set_minor_formatter(NullFormatter())
        ax.set_ylim(0.45, 2.2)
        ax.grid(axis="y", color=GRID, lw=0.8)
        ax.set_title(label, fontsize=10, loc="left")
        ax.set_xlabel("Years since access worsened (4 = 4+)")
    axes[0].set_ylabel("Rate ratio vs year before")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def spec_plot(res: pd.DataFrame, outcomes: dict, path: Path):
    w = res[res["model"] == "within"]
    specs = list(dict.fromkeys(w["spec"]))
    fig, axes = plt.subplots(1, len(outcomes), figsize=(4.2 * len(outcomes), 3.8), sharey=True)
    for ax, (o, label) in zip(axes, outcomes.items()):
        r = w[w["outcome"] == o].set_index("spec").reindex(specs)
        y = np.arange(len(specs))[::-1]
        ax.hlines(y, r["lo"], r["hi"], color=SERIES, lw=2)
        ax.plot(r["irr"], y, "o", color=SERIES, ms=6, mec=SURFACE, mew=1.5)
        _ratio_axis(ax, 0.05, 8)
        ax.set_xticks([0.1, 0.25, 0.5, 1, 2, 4, 8], ["0.1", "0.25", "0.5", "1", "2", "4", "8"])
        ax.set_title(label, fontsize=10, loc="left")
        ax.set_xlabel("Rate ratio per +5 min (95% CI)")
    axes[0].set_yticks(np.arange(len(specs))[::-1], specs)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    res = pd.read_csv(OUT / "model_results.csv")
    ev = pd.read_csv(OUT / "event_study.csv")
    forest(res[res["model"] == "between"],
           {"total": "All incidents", "hwrc_type": "Bulky / HWRC-type household",
            "bags_household": "Household black bags"},
           OUT / "fig_between.png",
           "Council characteristics and fly-tipping rates, England and Wales 2022/23 to 2024/25")
    event_plot(ev, {"total": "All incidents", "hwrc_type": "Bulky / HWRC-type household",
                    "placebo": "Placebo (carcasses, clinical, vehicle parts)"},
               OUT / "fig_event_study.png")
    spec_plot(res, {"hwrc_type": "Bulky / HWRC-type household", "total": "All incidents",
                    "placebo": "Placebo"}, OUT / "fig_within_specs.png")
