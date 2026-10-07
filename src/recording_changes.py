"""Which councils' fly-tipping trends reflect changes in how they record, rather
than in how much is dumped?

For each English council, 2012/13 to 2024/25 (official counts per 1,000 people):

1. Step change: for each possible year k (2015 to 2022), the ratio of the median
   rate in the three years from k to the median in the three years before k. The
   year with the largest ratio (up or down) is the council's step; it counts as a
   step if the rate doubles or halves and the move is at least three times the
   council's typical year-to-year change.
2. Signs that a step is a recording change, comparing the same two three-year
   windows:
   - small items (single bags, single items and car-boot loads) become a larger
     share, by 10 percentage points or more: councils that start logging what crews
     find, or open an app, mostly add small incidents;
   - large loads (tipper lorry or larger), which are hard to miss and recorded
     anyway, rise by less than half as much as the total (in log terms; only where
     the council recorded 30 or more large loads in the three years before);
   - FixMyStreet reports in the council rise at least threefold (a new reporting
     channel; councils with 30+ reports a year after the step);
   - the council's reporting basis changed (Defra's flag, from 2019/20) or it was
     formed from merged councils.
3. Class: "recording change likely" (a step with at least one sign), "step, cause
   unclear", "steady rise" (median rate in 2022 to 2024 at least 1.25 times 2012 to
   2014 without a step), "little change" otherwise.

The national trend is then shown for all councils and for councils without a
likely recording change, next to large loads.
Outputs: outputs/recording_changes.csv (one row per council), outputs/trend.csv.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INTERIM = ROOT / "data" / "interim"
OUT = ROOT / "outputs"
SMALL = ["size_single_bag", "size_single_item", "size_car_boot"]
LARGE = ["size_tipper", "size_multi"]
SIZE = SMALL + ["size_small_van", "size_transit_van"] + LARGE
STEP = 2.0  # a step is a doubling or halving of the recorded rate


def fms_by_council() -> pd.DataFrame:
    from access_panel import lsoa_to_lad
    f = pd.read_csv(INTERIM / "fms_flytip_lsoa_year.csv").merge(lsoa_to_lad(), on="LSOA21CD")
    return f.groupby(["LAD25CD", "year"])["n_flytip"].sum().rename("fms").reset_index()


def classify(g: pd.DataFrame) -> dict:
    g = g.sort_values("year").set_index("year")
    rate = g["rate"]
    out = {"LAD25CD": g["LAD25CD"].iloc[0], "council": g["LAD25NM"].iloc[0]}
    best, k_best = 0.0, None
    for k in range(2015, 2023):
        before, after = rate.loc[k - 3:k - 1], rate.loc[k:k + 2]
        if len(before) < 3 or len(after) < 3 or before.median() <= 0 or after.median() <= 0:
            continue
        r = np.log(after.median() / before.median())
        if abs(r) > abs(best):
            best, k_best = r, k
    yy = np.log(rate.clip(lower=0.01)).diff().abs().median()
    step = k_best is not None and abs(best) >= np.log(STEP) and abs(best) >= 3 * yy
    early, late = rate.loc[2012:2014].median(), rate.loc[2022:2024].median()
    out.update({"rate_2012_14": early, "rate_2022_24": late, "change_2012_24": late / early if early else np.nan,
                "step_year": k_best if step else None, "step_ratio": float(np.exp(best)) if step else None})
    if step:
        b, a = g.loc[k_best - 3:k_best - 1], g.loc[k_best:k_best + 2]

        def share(x, cols):
            tot = x[SIZE].sum().sum()
            return x[cols].sum().sum() / tot if tot else np.nan
        small_shift = share(a, SMALL) - share(b, SMALL)
        lt, ll = np.log(a["total"].sum() / b["total"].sum()), np.log((a[LARGE].sum().sum() + 1) / (b[LARGE].sum().sum() + 1))
        fms_b, fms_a = b["fms"].sum(), a["fms"].sum()
        signs = []
        if small_shift >= 0.10:
            signs.append(f"small items +{small_shift * 100:.0f} pts")
        if lt > 0 and ll < lt / 2 and b[LARGE].sum().sum() >= 30:
            signs.append("large loads did not rise with the total")
        if fms_a / 3 >= 30 and fms_a >= 3 * max(fms_b, 1):
            signs.append("FixMyStreet reports rose 3-fold or more")
        basis = g["reporting_basis"].dropna().astype(str)
        basis = basis[~basis.isin([":", "nan"])]
        if basis.nunique() > 1 or basis.str.contains("changed|Mixed").any():
            signs.append("reporting basis changed")
        if g["n_predecessors"].max() > 1 and k_best >= 2019:
            signs.append("formed from merged councils")
        out.update({"small_item_shift_pts": small_shift * 100, "large_vs_total": float(np.exp(ll - lt)),
                    "fms_before": int(fms_b), "fms_after": int(fms_a), "signs": "; ".join(signs)})
        out["class"] = "recording change likely" if signs else "step, cause unclear"
    else:
        out["class"] = "steady rise" if out["change_2012_24"] >= 1.25 else "little change"
    return out


def main():
    d = pd.read_csv(ROOT / "data" / "analysis" / "council_year.csv")
    d = d[d["nation"] == "England"].merge(fms_by_council(), on=["LAD25CD", "year"], how="left")
    d["fms"] = d["fms"].fillna(0)
    d["rate"] = d["total"] / d["population"] * 1000
    res = pd.DataFrame([classify(g) for _, g in d.groupby("LAD25CD")])
    res.to_csv(OUT / "recording_changes.csv", index=False)

    rec = set(res.loc[res["class"] == "recording change likely", "LAD25CD"])
    smooth = set(res.loc[res["class"].isin(["steady rise", "little change"]), "LAD25CD"])
    d["large"] = d[LARGE].sum(axis=1)
    rows = []
    for y, g in d.groupby("year"):
        keep = g[~g["LAD25CD"].isin(rec)]
        sm = g[g["LAD25CD"].isin(smooth)]
        rows.append({"year": y, "all_per_1000": g["total"].sum() / g["population"].sum() * 1000,
                     "no_recording_change_per_1000": keep["total"].sum() / keep["population"].sum() * 1000,
                     "no_step_per_1000": sm["total"].sum() / sm["population"].sum() * 1000,
                     "large_loads": g["large"].sum(), "total": g["total"].sum(),
                     "large_per_100k": g["large"].sum() / g["population"].sum() * 1e5,
                     "councils_no_step": sm["LAD25CD"].nunique(),
                     "councils": g["LAD25CD"].nunique(), "councils_no_recording_change": keep["LAD25CD"].nunique()})
    w = pd.read_csv(ROOT / "data" / "analysis" / "council_year.csv")
    w = w[w["nation"] == "Wales"].groupby("year")[["total", "population"]].sum()
    t = pd.DataFrame(rows).set_index("year")
    t["wales_per_1000"] = w["total"] / w["population"] * 1000
    t.round(3).to_csv(OUT / "trend.csv")
    pd.set_option("display.width", 220)
    print(res["class"].value_counts())
    print(t.round(2).to_string())
    return res, t


if __name__ == "__main__":
    main()
