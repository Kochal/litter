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


def closure_plot(path: Path):
    """Event study around recycling centre closures (closure_study.py), in three
    samples, with the number of closures and neighbourhoods in each title."""
    r = pd.read_csv(OUT / "closure_study.csv")
    infl = OUT / "closure_study_influence.csv"
    r = r[(r["model"] == "event study") & (r["outcome"] == "flytip")]
    panels = [("all verified closures", r[r["sample"] == "all verified closures"]),
              ("confirmed or likely closures only", r[r["sample"] == "confirmed or likely closures only"])]
    if infl.exists():
        i = pd.read_csv(infl)
        i = i[(i["model"] == "event study") & (i["sample"] == "without the 3 largest closures")]
        panels.append(("without the 3 closures with most reports", i))
    fig, axes = plt.subplots(1, len(panels), figsize=(4.2 * len(panels), 3.6), sharey=True)
    for ax, (title, d) in zip(axes, panels):
        d = d.copy()
        d["k"] = [int(t[4:]) * (-1 if t[3] == "m" else 1) for t in d["term"]]
        d = pd.concat([d, pd.DataFrame({"k": [-1], "irr": [1.0], "lo": [1.0], "hi": [1.0]})]).sort_values("k")
        ax.fill_between(d["k"], d["lo"], d["hi"], color=SERIES, alpha=0.15, lw=0)
        ax.plot(d["k"], d["irr"], "-o", color=SERIES, lw=2, ms=5, mec=SURFACE, mew=1.2)
        ax.axhline(1, color=INK2, lw=1)
        ax.axvline(-0.5, color=GRID, lw=1, ls="--")
        ax.set_yscale("log")
        ax.yaxis.set_minor_locator(NullLocator())
        ax.yaxis.set_minor_formatter(NullFormatter())
        ax.set_yticks([0.5, 0.75, 1, 1.5, 2], ["0.5", "0.75", "1", "1.5", "2"])
        ax.set_ylim(0.45, 2.2)
        ax.grid(axis="y", color=GRID, lw=0.8)
        n = d.dropna(subset=["n_closures"]).iloc[0]
        ax.set_title(f"{title}\n{int(n.n_closures)} closures, {int(n.n_affected_lsoas):,} affected and "
                     f"{int(n.n_comparison_lsoas):,} comparison areas", fontsize=9, loc="left")
        ax.set_xlabel("Years since closure")
    axes[0].set_ylabel("Fly-tipping reports, ratio to\ncomparison areas (vs year before)")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def cutoff_plot(path: Path):
    """Fly-tipping reports by 2-minute drive-time band (cutoff_analysis.py), with
    neighbourhood-years per band under each point."""
    b = pd.read_csv(OUT / "cutoff_bands.csv")
    b = b[(b["outcome"] == "flytip") & (b["lsoa_years"] >= 100)].reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(9, 3.8))
    x = np.arange(len(b))
    ax.vlines(x, b["lo"], b["hi"], color=SERIES, lw=2)
    ax.plot(x, b["irr"], "o", color=SERIES, ms=6, mec=SURFACE, mew=1.5)
    ax.axhline(1, color=INK2, lw=1)
    ax.set_yscale("log")
    ax.yaxis.set_minor_locator(NullLocator())
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.set_yticks([0.25, 0.5, 1, 2], ["0.25", "0.5", "1", "2"])
    ax.set_ylim(0.3, 2.5)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_xticks(x, [f"{r.band}\n{int(r.lsoa_years):,}" for r in b.itertuples()], fontsize=8)
    ax.set_xlabel("Drive time to nearest recycling centre (minutes) / neighbourhood-years in band")
    ax.set_ylabel("Fly-tipping reports vs 0-2 min")
    ax.set_title(f"Same council and year; {int(b['lsoa_years'].sum()):,} neighbourhood-years in "
                 f"{int(b['n_councils'].iloc[0])} councils (bands with 100+ shown)", fontsize=9, loc="left")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def council_records_plot(path: Path):
    """Council records versus FixMyStreet: rate ratios per driver by council
    (council_records.py), pooled rows, and the Leeds closure year by year."""
    r = pd.read_csv(OUT / "council_records_models.csv")
    r = r[(r["model"] == "same council and year") & (r["outcome"] == "n_council")]
    f = pd.read_csv(OUT / "fms_model_results.csv")
    f = f[(f["outcome"] == "flytip") & (f["spec"] == "plus housing and cars")].set_index("term")
    ev = pd.read_csv(OUT / "council_records_leeds_closure.csv")
    ev = ev[ev["outcome"] == "n_council"]
    terms = [("t_hwrc_5", "Drive time to recycling centre\n(per 5 extra minutes)"),
             ("private_rent_10", "Private renting\n(per 10 points)"), ("no_car_10", "No car\n(per 10 points)")]
    tot = r[r["term"] == "no_car_10"].set_index("council")["n_records"]
    single = tot[~tot.index.str.startswith("All")].sort_values(ascending=False).index.tolist()
    pooled = ["All except Leeds (pooled)", "All except Leeds and Newham (pooled)"]
    rows = single + pooled
    labels = {"All except Leeds (pooled)": "Pooled, 11 councils", "All except Leeds and Newham (pooled)": "Pooled, without Newham"}
    fig = plt.figure(figsize=(15, 6.2))
    gs = fig.add_gridspec(2, 3, height_ratios=[1.55, 1], hspace=0.55)
    for k, (t, label) in enumerate(terms):
        ax = fig.add_subplot(gs[0, k])
        d = r[r["term"] == t].set_index("council").reindex(rows)
        y = np.arange(len(rows))[::-1]
        col = [INK if c in pooled else SERIES for c in rows]
        ax.hlines(y, d["lo"], d["hi"], color=col, lw=2)
        ax.scatter(d["irr"], y, color=col, s=36, edgecolor=SURFACE, linewidth=1.2, zorder=3)
        ax.axvline(f.loc[t, "irr"], color="#d98a1f", lw=1.5, ls="--")
        ax.axhline(1.5, color=GRID, lw=1)
        _ratio_axis(ax, 0.4, 4)
        ax.set_xticks([0.5, 1, 2, 4], ["0.5", "1", "2", "4"])
        ax.set_title(label, fontsize=9, loc="left")
        ax.set_yticks(y, [f"{labels.get(c, c)} ({int(tot[c]):,})" for c in rows] if k == 0 else [], fontsize=8)
    fig.text(0.01, 0.43, "Dashed: FixMyStreet, 212 councils. Records per council in brackets.", fontsize=8, color="#d98a1f")
    ax = fig.add_subplot(gs[1, :2])
    e = pd.concat([ev, pd.DataFrame({"year": [2013], "irr": [1.0], "lo": [1.0], "hi": [1.0]})]).sort_values("year")
    ax.fill_between(e["year"], e["lo"], e["hi"], color=SERIES, alpha=0.15, lw=0)
    ax.plot(e["year"], e["irr"], "-o", color=SERIES, lw=2, ms=5, mec=SURFACE, mew=1.2)
    ax.axhline(1, color=INK2, lw=1)
    ax.axvline(2013.5, color=GRID, lw=1, ls="--")
    ax.axvline(2016.5, color="#d98a1f", lw=1, ls=":")
    ax.text(2016.6, 3.3, "new recording system", fontsize=7, color="#d98a1f", va="top")
    ax.set_yscale("log")
    ax.yaxis.set_minor_locator(NullLocator())
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.set_yticks([0.5, 1, 2, 4], ["0.5", "1", "2", "4"])
    ax.set_ylim(0.45, 4.2)
    ax.grid(axis="y", color=GRID, lw=0.8)
    n = ev.iloc[0]
    ax.set_title(f"Leeds closure: {int(n.n_treated_sectors)} sectors lost access in 2014, vs "
                 f"{int(n.n_comparison_sectors)} other sectors (2013 = 1)", fontsize=9, loc="left")
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def policy_plot(path: Path):
    """DIY charge ban event studies (diy_ban.py) and opening hours estimates
    (hours_analysis.py)."""
    r = pd.read_csv(OUT / "diy_ban.csv")
    h = pd.read_csv(OUT / "hours_models.csv")
    fig, axes = plt.subplots(1, 3, figsize=(15, 3.9), gridspec_kw={"width_ratios": [1, 1, 1.1]})
    panels = [
        (r[(r["source"] == "official counts") & (r["outcome"] == "cde") & (r["comparison"] == "charged vs did not charge")
           & r["term"].str.startswith("y")], 2022, 2023.75, "Official counts (financial years, 2023 = 2023/24): construction\nand demolition fly-tipping, charging vs non-charging councils"),
        (r[(r["source"] == "FixMyStreet") & (r["outcome"] == "construction as share of all reports")
           & r["term"].str.startswith("y")], 2023, 2023.5, "FixMyStreet (calendar years): builders' waste as a\nshare of all reports, same comparison"),
    ]
    for ax, (d, ref, ban, title) in zip(axes[:2], panels):
        d = pd.concat([d, pd.DataFrame({"year": [ref], "irr": [1.0], "lo": [1.0], "hi": [1.0]})]).sort_values("year")
        ax.fill_between(d["year"], d["lo"], d["hi"], color=SERIES, alpha=0.15, lw=0)
        ax.plot(d["year"], d["irr"], "-o", color=SERIES, lw=2, ms=5, mec=SURFACE, mew=1.2)
        ax.axhline(1, color=INK2, lw=1)
        ax.axvline(ban, color="#d98a1f", lw=1, ls=":")
        ax.text(ban + 0.05, 1.9, "ban", fontsize=8, color="#d98a1f")
        ax.set_yscale("log")
        ax.yaxis.set_minor_locator(NullLocator())
        ax.yaxis.set_minor_formatter(NullFormatter())
        ax.set_yticks([0.5, 0.75, 1, 1.5, 2], ["0.5", "0.75", "1", "1.5", "2"])
        ax.set_ylim(0.45, 2.2)
        ax.grid(axis="y", color=GRID, lw=0.8)
        n = d.dropna(subset=["n_councils_treated"]).iloc[0]
        ax.set_title(f"{title}\n{int(n.n_councils_treated)} vs {int(n.n_councils_comparison)} councils "
                     f"(ratio to {ref} = 1)", fontsize=9, loc="left")
    ax = axes[2]
    rows = [("FixMyStreet", "nearest centre unchanged", "same neighbourhood over time", "hours_cut_10",
             "10 fewer opening hours a week\n(same neighbourhood over time)"),
            ("FixMyStreet", "nearest centre unchanged", "same neighbourhood over time", "log_crowding",
             "2.7x more households per\nopening hour (over time)"),
            ("FixMyStreet", "all neighbourhoods", "between neighbourhoods, same council and year", "log_crowding",
             "2.7x more households per\nopening hour (between places)")]
    y = np.arange(len(rows))[::-1]
    for yy, (src, smp, comp, term, lab) in zip(y, rows):
        x = h[(h["source"] == src) & (h["sample"] == smp) & (h["comparison"] == comp) & (h["term"] == term)].iloc[0]
        ax.hlines(yy, x.lo, x.hi, color=SERIES, lw=2)
        ax.plot(x.irr, yy, "o", color=SERIES, ms=6, mec=SURFACE, mew=1.5)
    _ratio_axis(ax, 0.5, 2)
    ax.set_xticks([0.5, 0.75, 1, 1.5, 2], ["0.5", "0.75", "1", "1.5", "2"])
    ax.set_yticks(y, [r[4] for r in rows], fontsize=8)
    n = h[(h["sample"] == "nearest centre unchanged") & (h["source"] == "FixMyStreet")].iloc[0]
    ax.set_title(f"Opening hours: FixMyStreet reports\n{int(n.n_lsoa_years):,} neighbourhood-years, "
                 f"{int(n.n_councils)} councils", fontsize=9, loc="left")
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
    if (OUT / "closure_study.csv").exists():
        closure_plot(OUT / "fig_closure_study.png")
    if (OUT / "council_records_models.csv").exists():
        council_records_plot(OUT / "fig_council_records.png")
    if (OUT / "diy_ban.csv").exists() and (OUT / "hours_models.csv").exists():
        policy_plot(OUT / "fig_policy.png")
    spec_plot(res, {"hwrc_type": "Bulky / HWRC-type household", "total": "All incidents",
                    "placebo": "Placebo"}, OUT / "fig_within_specs.png")
