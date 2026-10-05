"""Is there a drive time beyond which fly-tipping jumps?

Uses FixMyStreet reports per neighbourhood (LSOA) and year, compared only within
the same council and year (as in fms_analysis.py), with drive time from where
residents live to the nearest recycling centre (verified closure history).

1. Fine bands: rate ratios for 2-minute drive-time bands against the closest band,
   with the number of neighbourhood-years in each band.
2. Break-point search: a model where reports change at one rate up to a cutoff
   and another rate beyond it, fitted for every whole-minute cutoff from 4 to 25;
   the best-fitting cutoff and the slope beyond it are reported.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import pyfixest as pf

from fms_analysis import INTERIM, OUT, active_council_years, lsoa_panel

BANDS = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 25, 30, 999]
CONTROLS = "private_rent_10 + no_car_10 + log_density + rural"


def data() -> pd.DataFrame:
    d = lsoa_panel().drop(columns=["t_hwrc_min", "t_hwrc_5"])
    t = pd.read_csv(INTERIM / "lsoa_hwrc_times_panel_verified.csv")[["LSOA21CD", "year", "t_hwrc_min"]]
    d = d.merge(t, on=["LSOA21CD", "year"]).dropna(subset=["t_hwrc_min"])
    return active_council_years(d, "flytip")


def bands(d: pd.DataFrame, outcome: str) -> pd.DataFrame:
    labels = [f"{a}-{b}" if b < 999 else f"{a}+" for a, b in zip(BANDS[:-1], BANDS[1:])]
    d = d.assign(band=pd.cut(d["t_hwrc_min"], BANDS, labels=labels, right=False).astype(str))
    m = pf.fepois(f"n_{outcome} ~ C(band, contr.treatment(base='0-2')) + {CONTROLS} | lad_year",
                  data=d, offset="log_residents", vcov={"CRV1": "LAD25CD"})
    counts = d.groupby("band").agg(lsoa_years=("LSOA21CD", "size"), lsoas=("LSOA21CD", "nunique"),
                                   reports=(f"n_{outcome}", "sum"))
    rows = [{"band": "0-2", "irr": 1.0, "lo": 1.0, "hi": 1.0, "p": np.nan}]
    for t in m.coef().index:
        if "band" not in t:
            continue
        b, se = m.coef()[t], m.se()[t]
        rows.append({"band": t.split("[T.")[1].rstrip("]"), "irr": np.exp(b), "lo": np.exp(b - 1.96 * se),
                     "hi": np.exp(b + 1.96 * se), "p": m.pvalue()[t]})
    out = pd.DataFrame(rows).merge(counts, left_on="band", right_index=True)
    out["order"] = out["band"].map({l: i for i, l in enumerate(labels)})
    return out.sort_values("order").drop(columns="order").assign(outcome=outcome, n_councils=d["LAD25CD"].nunique())


def breakpoints(d: pd.DataFrame, outcome: str) -> pd.DataFrame:
    rows = []
    for k in range(4, 26):
        x = d.assign(below=np.minimum(d["t_hwrc_min"], k) / 5, beyond=np.maximum(d["t_hwrc_min"] - k, 0) / 5)
        m = pf.fepois(f"n_{outcome} ~ below + beyond + {CONTROLS} | lad_year", data=x,
                      offset="log_residents", vcov={"CRV1": "LAD25CD"})
        c, se = m.coef(), m.se()
        rows.append({"outcome": outcome, "cutoff_min": k, "deviance": m.deviance,
                     "irr_per5_below": np.exp(c["below"]), "irr_per5_beyond": np.exp(c["beyond"]),
                     "beyond_lo": np.exp(c["beyond"] - 1.96 * se["beyond"]),
                     "beyond_hi": np.exp(c["beyond"] + 1.96 * se["beyond"]), "p_beyond": m.pvalue()["beyond"],
                     "lsoa_years_beyond": int((d["t_hwrc_min"] > k).sum())})
    out = pd.DataFrame(rows)
    out["best"] = out["deviance"] == out["deviance"].min()
    # Deviance difference from the best cutoff: under about 4 means no meaningful preference
    out["deviance_vs_best"] = out["deviance"] - out["deviance"].min()
    return out


if __name__ == "__main__":
    d = data()
    b = pd.concat([bands(d, o) for o in ("flytip", "litter")])
    b.to_csv(OUT / "cutoff_bands.csv", index=False)
    bp = breakpoints(d, "flytip")
    bp.to_csv(OUT / "cutoff_breakpoints.csv", index=False)
    pd.set_option("display.width", 200)
    print(b.round(3).to_string(index=False))
    print(bp.round(3).to_string(index=False))
