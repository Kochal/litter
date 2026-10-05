"""Closure-by-closure study: what happens to fly-tipping reports in the
neighbourhoods that lose their nearest recycling centre?

For each closure in the verified history (verified_history.py), with event year
E = the first year the site is gone:
- affected neighbourhoods: LSOAs whose drive time to the nearest centre rises by
  at least a minute in year E and that lie within 15 km of the closing site
  (each LSOA is tied to the nearest closing site that year);
- comparison neighbourhoods: LSOAs in the same council as an affected one, or
  within 20 km of the site, whose drive time moved by less than half a minute in
  every year from E-4 to E+4, and that are not affected by any closure.
Each closure forms a "stack" of these LSOAs over years E-4 to E+4. Stacks are
pooled and compared with fixed effects for stack-by-neighbourhood and
stack-by-council-by-year, so affected and comparison areas are only compared
within the same council and year of the same closure. Pre-closure years show
whether affected areas were already diverging. Litter reports are the placebo.
"""
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyfixest as pf

from access_panel import lsoa_to_lad

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
OUT = ROOT / "outputs"
WINDOW = 4
AFFECTED_KM, CONTROL_KM = 15, 20
YEARS = range(2012, 2025)
STRICT = "confirmed closure|likely closure"


def lsoa_frame() -> pd.DataFrame:
    t = pd.read_csv(INTERIM / "lsoa_hwrc_times_panel_verified.csv")[["LSOA21CD", "year", "t_hwrc_min"]]
    t = t.sort_values(["LSOA21CD", "year"])
    t["dt"] = t.groupby("LSOA21CD")["t_hwrc_min"].diff()
    pwc = gpd.read_file(RAW / "lsoa21_pwc.gpkg")
    xy = pd.DataFrame({"LSOA21CD": pwc["LSOA21CD"], "x": pwc.geometry.x, "y": pwc.geometry.y})
    cen = pd.read_csv(INTERIM / "census_lsoa.csv")[["LSOA21CD", "residents"]]
    d = t.merge(xy, on="LSOA21CD").merge(cen, on="LSOA21CD").merge(lsoa_to_lad(), on="LSOA21CD")
    for kind in ("flytip", "litter"):
        c = pd.read_csv(INTERIM / f"fms_{kind}_lsoa_year.csv")
        d = d.merge(c, on=["LSOA21CD", "year"], how="left")
        d[f"n_{kind}"] = d[f"n_{kind}"].fillna(0)
    return d[d["year"].isin(YEARS)]


def closures() -> pd.DataFrame:
    h = pd.read_csv(INTERIM / "hwrc_england_history_verified.csv")
    c = h[(h["last"] < YEARS.stop - 1) & (h["last"] >= YEARS.start - 1)].copy()
    c["event_year"] = c["last"] + 1
    c["strict"] = c["correction"].str.contains(STRICT, na=False)
    return c[c["event_year"].between(YEARS.start + 1, YEARS.stop - 1)]


def build_stacks(d: pd.DataFrame, ev: pd.DataFrame) -> pd.DataFrame:
    # Affected LSOAs: drive time up by 1+ min in the event year, tied to the nearest closing site
    cand = []
    for e in ev.itertuples():
        j = d[(d["year"] == e.event_year) & (d["dt"] >= 1)].copy()
        j["dist"] = np.hypot(j["x"] - e.easting, j["y"] - e.northing)
        j = j[j["dist"] < AFFECTED_KM * 1000]
        cand.append(j[["LSOA21CD", "dist", "dt"]].assign(site_id=e.site_id, event_year=e.event_year))
    cand = pd.concat(cand)
    affected = cand.sort_values("dist").drop_duplicates(["LSOA21CD", "event_year"])
    ever_affected = set(affected["LSOA21CD"])

    stacks = []
    for e in ev.itertuples():
        a = affected[affected["site_id"] == e.site_id]
        if a.empty:
            continue
        lo, hi = e.event_year - WINDOW, e.event_year + WINDOW
        win = d[d["year"].between(lo, hi)]
        stable = win.groupby("LSOA21CD")["dt"].apply(lambda s: s.abs().max() < 0.5)
        lads = set(d.loc[d["LSOA21CD"].isin(a["LSOA21CD"]), "LAD25CD"])
        near = d.drop_duplicates("LSOA21CD")
        near = near[(np.hypot(near["x"] - e.easting, near["y"] - e.northing) < CONTROL_KM * 1000)
                    | near["LAD25CD"].isin(lads)]["LSOA21CD"]
        controls = set(near) & set(stable[stable].index) - ever_affected
        s = win[win["LSOA21CD"].isin(set(a["LSOA21CD"]) | controls)].copy()
        s["treated"] = s["LSOA21CD"].isin(set(a["LSOA21CD"])).astype(int)
        s["jump_min"] = s["LSOA21CD"].map(a.set_index("LSOA21CD")["dt"]).fillna(0)
        s["stack"] = e.site_id
        s["strict"] = e.strict
        s["rel"] = s["year"] - e.event_year
        stacks.append(s)
    return pd.concat(stacks, ignore_index=True)


def fit(df: pd.DataFrame, outcome: str, event_study: bool):
    df = df.copy()
    df["log_res"] = np.log(df["residents"])
    df["s_lsoa"] = df["stack"].astype(str) + "_" + df["LSOA21CD"]
    df["s_lad_year"] = df["stack"].astype(str) + "_" + df["LAD25CD"] + "_" + df["year"].astype(str)
    if event_study == "years 1 to 4":
        df["closure_year"] = ((df["rel"] == 0) & (df["treated"] == 1)).astype(int)
        df["years_1_to_4_after"] = ((df["rel"] >= 1) & (df["treated"] == 1)).astype(int)
        rhs = "closure_year + years_1_to_4_after"
    elif event_study:
        names = []
        for k in range(-WINDOW, WINDOW + 1):
            if k == -1:
                continue
            nm = f"ev_m{-k}" if k < 0 else f"ev_p{k}"
            df[nm] = ((df["rel"] == k) & (df["treated"] == 1)).astype(int)
            names.append(nm)
        rhs = " + ".join(names)
    else:
        df["after_closure"] = ((df["rel"] >= 0) & (df["treated"] == 1)).astype(int)
        rhs = "after_closure"
    m = pf.fepois(f"n_{outcome} ~ {rhs} | s_lsoa + s_lad_year", data=df, offset="log_res",
                  vcov={"CRV1": "stack"})
    return m, df


def tidy(m, df, label, outcome) -> pd.DataFrame:
    rows = []
    for t in m.coef().index:
        b, se = m.coef()[t], m.se()[t]
        k = {"after_closure": 0, "closure_year": 0, "years_1_to_4_after": 1}.get(t)
        if k is None:
            k = int(t[4:]) * (-1 if t[3] == "m" else 1)
        # Closures that contribute: those with any report of this kind in their stack
        used = df.groupby("stack")[f"n_{outcome}"].sum()
        uniq = df.drop_duplicates(["LSOA21CD", "year"])
        rows.append({"sample": label, "outcome": outcome, "term": t, "rel_year": k, "irr": np.exp(b),
                     "lo": np.exp(b - 1.96 * se), "hi": np.exp(b + 1.96 * se), "p": m.pvalue()[t],
                     "n_obs": int(m._N), "n_closures": df["stack"].nunique(),
                     "n_affected_lsoas": df.loc[df["treated"] == 1, "LSOA21CD"].nunique(),
                     "n_comparison_lsoas": df.loc[df["treated"] == 0, "LSOA21CD"].nunique(),
                     "n_closures_with_reports": int((used > 0).sum()),
                     "n_reports": int(uniq[f"n_{outcome}"].sum())})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    d = lsoa_frame()
    ev = closures()
    st = build_stacks(d, ev)
    samples = {
        "all verified closures": st,
        "confirmed or likely closures only": st[st["strict"]],
        "jump of 3+ minutes": st[(st["treated"] == 0) | (st["jump_min"] >= 3)],
    }
    res = []
    for label, s in samples.items():
        for outcome in ("flytip", "litter"):
            for es in (False, True, "years 1 to 4"):
                try:
                    m, df = fit(s, outcome, es)
                except ValueError as e:
                    print("skip", label, outcome, e)
                    continue
                res.append(tidy(m, df, label, outcome).assign(model={False: "before/after", True: "event study"}.get(es, es)))
    res = pd.concat(res)
    res.to_csv(OUT / "closure_study.csv", index=False)
    pd.set_option("display.width", 220)
    print(res.round(3).to_string(index=False))
