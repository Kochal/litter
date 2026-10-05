"""Check the FixMyStreet results against councils' own records of where fly-tipping
was found (data/raw/council_incidents, see DATASETS.md).

Councils and how each incident is placed:
- York (2019 on): exact point, with waste type; neighbourhood (LSOA) by point.
- Bassetlaw (2011 to 2017): exact point, with waste type; LSOA by point.
- Bradford (2010 to 2017): street and locality only; placed on the OS Open Roads
  links with that street name in Bradford, if those links lie within 1.5 km of
  each other (otherwise the name is ambiguous and the record is dropped).
- Leeds (2012 on): postcode sector (e.g. "LS6 1"); neighbourhoods are grouped into
  the sector that holds most of their postcodes, and the analysis is by sector.
  From 2017 each record says how it reached the council: found by council staff
  ("generated proactively", officer witness, internal) or reported by the public.

For each council the models match the FixMyStreet neighbourhood models: counts
per area and year, compared only within the same council and year, with a
log-residents offset, private renting, car ownership, density, rural or urban
and drive time to the nearest recycling centre (verified closure history).
A second model compares each area with itself over time (area and year fixed
effects) to see whether drive time changes go with changes in fly-tipping.
Only counts per area and year are written out.
"""
import glob
import re
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyfixest as pf

from fms_analysis import INTERIM, OUT, RAW, lsoa_panel

SRC = RAW / "council_incidents"
LADS = {"York": "E06000014", "Bassetlaw": "E07000171", "Bradford": "E08000032", "Leeds": "E08000035"}
TYPES = [("bags", r"bag"), ("construction", r"constr|build|rubble|demol|diy"),
         ("bulky", r"furniture|white goods|electric|fridge|mattress|sofa"), ("garden", r"garden|green"),
         ("tyres", r"tyre")]
CONTROLS = "private_rent_10 + no_car_10 + log_density"


def waste_type(s: pd.Series) -> pd.Series:
    s = s.fillna("").str.lower()
    out = pd.Series("other", index=s.index)
    for name, pat in reversed(TYPES):
        out[s.str.contains(pat)] = name
    return out


def to_lsoa(df: pd.DataFrame, x: str, y: str) -> pd.DataFrame:
    df = df.dropna(subset=[x, y])
    df = df[(df[x] > 0) & (df[y] > 0)]
    pts = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[x].astype(float), df[y].astype(float)), crs=27700)
    lsoa = gpd.read_file(RAW / "lsoa21_bsc_ruc.gpkg", columns=["LSOA21CD"])
    return pd.DataFrame(gpd.sjoin(pts, lsoa, predicate="within").drop(columns=["geometry", "index_right"]))


def load_york() -> pd.DataFrame:
    y = pd.read_csv(SRC / "york.csv", encoding="utf-8-sig")
    y = pd.DataFrame({"year": pd.to_datetime(y["Date_Created"].str[:10]).dt.year, "x": y["Easting"],
                      "y": y["Northing"], "wtype": waste_type(y["CategoryId"])})
    return to_lsoa(y, "x", "y").assign(council="York")


def load_bassetlaw() -> pd.DataFrame:
    frames = []
    for f in sorted(glob.glob(str(SRC / "bassetlaw" / "*.csv"))):
        d = pd.read_csv(f, encoding="latin-1")
        d.columns = [re.sub(r"[^a-z]", "", c.lower()) for c in d.columns]
        frames.append(d[[c for c in ("ticketdate", "eastings", "northings", "typeofwaste") if c in d]])
    d = pd.concat(frames, ignore_index=True)
    d = pd.DataFrame({"year": pd.to_datetime(d["ticketdate"], dayfirst=True, errors="coerce").dt.year,
                      "x": pd.to_numeric(d["eastings"], errors="coerce"),
                      "y": pd.to_numeric(d["northings"], errors="coerce"), "wtype": waste_type(d["typeofwaste"])})
    return to_lsoa(d.dropna(subset=["year"]), "x", "y").assign(council="Bassetlaw")


def load_bradford() -> pd.DataFrame:
    b = pd.read_csv(SRC / "bradford.csv")
    lad = gpd.read_file(RAW / "lad25_bgc.gpkg")
    area = lad[lad["LAD25CD"] == LADS["Bradford"]].geometry.buffer(500).iloc[0]
    roads = gpd.read_file(RAW / "oproad" / "Data" / "oproad_gb.gpkg", layer="road_link", bbox=area.bounds,
                          columns=["name_1"])
    roads = roads[roads["name_1"].notna() & roads.intersects(area)]
    c = roads.geometry.centroid
    roads = pd.DataFrame({"street": roads["name_1"].str.upper().str.strip(), "x": c.x, "y": c.y})
    g = roads.groupby("street").agg(x=("x", "median"), y=("y", "median"))
    spread = roads.merge(g, left_on="street", right_index=True, suffixes=("", "_m"))
    spread = np.hypot(spread["x"] - spread["x_m"], spread["y"] - spread["y_m"]).groupby(spread["street"]).max()
    g = g[spread.reindex(g.index) < 1500]
    b["street"] = b["streetname"].str.upper().str.strip()
    b = b.merge(g, left_on="street", right_index=True, how="left")
    print(f"Bradford: {b['x'].notna().mean():.0%} of {len(b):,} records placed by street name")
    b = pd.DataFrame({"year": b["year"], "x": b["x"], "y": b["y"], "wtype": "unknown"})
    return to_lsoa(b, "x", "y").assign(council="Bradford")


def load_leeds() -> pd.DataFrame:
    frames = []
    for f in ("leeds_2012_2016.csv", "leeds_current.csv"):
        d = pd.read_csv(SRC / f, encoding="utf-8-sig", encoding_errors="replace", low_memory=False)
        d.columns = [re.sub(r"[^A-Z]", "", c.upper()) for c in d.columns]
        d = d[d["SRTYPEDESC"].str.contains(r"^fly ?tip", case=False, na=False)]
        how = d["HOWRECIEVED"] if "HOWRECIEVED" in d else pd.Series(np.nan, index=d.index)
        frames.append(pd.DataFrame({"year": pd.to_datetime(d[[c for c in d.columns if c.startswith("REC")][0]],
                                                           dayfirst=True, errors="coerce").dt.year,
                                    "sector": d["PC"].str.upper().str.strip(), "how": how}))
    d = pd.concat(frames, ignore_index=True).dropna(subset=["year", "sector"])
    proactive = r"Proactive|Witness|Internal"
    d["received"] = np.where(d["how"].isna(), "unknown",
                             np.where(d["how"].str.contains(proactive, na=False), "found by council staff",
                                      "reported by the public"))
    return d.assign(council="Leeds")


def extra_covariates(codes: list) -> pd.DataFrame:
    """Social renting, household deprivation (2+ dimensions), flats and terraced
    houses per LSOA from the ONS Census 2021 API, for these councils only."""
    from census import _get
    out = {}
    for name, dim in (("tenure", "hh_tenure_9a"), ("deprivation", "hh_deprivation"),
                      ("accommodation", "accommodation_type")):
        cache = RAW / f"census_lsoa_4councils_{dim}.csv"
        if cache.exists():
            d = pd.read_csv(cache)
        else:
            rows = []
            for i in range(0, len(codes), 300):
                rows += _get("HH", "lsoa," + ",".join(codes[i:i + 300]), dim)
            d = pd.DataFrame(rows, columns=["area", "option_id", "option", "n"])
            d.to_csv(cache, index=False)
        d = d[d["option_id"].astype(str) != "-8"]
        w = d.pivot_table(index="area", columns="option", values="n", aggfunc="sum")
        tot = w.sum(axis=1)
        if name == "tenure":
            out["social_rent_share"] = w.filter(like="Social rented").sum(axis=1) / tot
        elif name == "deprivation":
            out["deprived_share"] = w.filter(regex="two|three|four").sum(axis=1) / tot
        else:
            out["flat_share"] = (w.filter(like="flats").sum(axis=1) + w.filter(like="converted").sum(axis=1)
                                 + w.filter(like="commercial building").sum(axis=1)) / tot
            out["terraced_share"] = w["Terraced"] / tot
    return pd.DataFrame(out).rename_axis("LSOA21CD").reset_index()


EXTRA = ["social_rent_share", "deprived_share", "flat_share", "terraced_share"]
EXTRA_RHS = "social_rent_10 + deprived_10 + flat_10 + terraced_10"


def lsoa_base() -> pd.DataFrame:
    """The FixMyStreet neighbourhood panel with drive times from the verified history."""
    d = lsoa_panel().drop(columns=["t_hwrc_min", "t_hwrc_5"])
    t = pd.read_csv(INTERIM / "lsoa_hwrc_times_panel_verified.csv")[["LSOA21CD", "year", "t_hwrc_min"]]
    d = d.merge(t, on=["LSOA21CD", "year"])
    d["t_hwrc_5"] = d["t_hwrc_min"] / 5
    d = d[d["LAD25CD"].isin(LADS.values())]
    d = d.merge(extra_covariates(sorted(d["LSOA21CD"].unique())), on="LSOA21CD", how="left")
    return add_steps(d)


def add_steps(d: pd.DataFrame) -> pd.DataFrame:
    for c in EXTRA:
        d[c.replace("_share", "_10")] = d[c] / 0.10
    return d


def lsoa_panel_for(rec: pd.DataFrame, base: pd.DataFrame, council: str) -> pd.DataFrame:
    years = sorted(set(rec["year"]) & set(base["year"]))
    d = base[(base["LAD25CD"] == LADS[council]) & base["year"].isin(years)].copy()
    cnt = rec.groupby(["LSOA21CD", "year"]).size().rename("n_council")
    d = d.merge(cnt, on=["LSOA21CD", "year"], how="left")
    if (rec["wtype"] != "unknown").any():
        bytype = rec.groupby(["LSOA21CD", "year", "wtype"]).size().unstack(fill_value=0).add_prefix("n_council_")
        d = d.merge(bytype, on=["LSOA21CD", "year"], how="left")
    d = d.fillna({c: 0 for c in d.columns if c.startswith("n_council")})
    return d.assign(unit=d["LSOA21CD"], council=council)


def leeds_panel(rec: pd.DataFrame, base: pd.DataFrame) -> pd.DataFrame:
    """Postcode sector by year for Leeds. Each LSOA joins the sector holding most of
    its postcodes; sector values are sums or household-weighted averages."""
    pc = pd.read_csv(RAW / "pc_lookup_4councils.csv", dtype=str)
    pc = pc[pc["ladcd"] == LADS["Leeds"]]
    pc["sector"] = pc["pcds"].str.upper().str.strip().str[:-2].str.strip()
    dom = pc.groupby(["lsoa21cd", "sector"]).size().reset_index(name="n").sort_values("n")
    dom = dom.drop_duplicates("lsoa21cd", keep="last").rename(columns={"lsoa21cd": "LSOA21CD"})[["LSOA21CD", "sector"]]
    b = base[base["LAD25CD"] == LADS["Leeds"]].merge(dom, on="LSOA21CD")
    b["area_km2"] = b["Shape__Area"] / 1e6
    w = b["households"]

    def wavg(col):
        return (b[col] * w).groupby([b["sector"], b["year"]]).sum() / w.groupby([b["sector"], b["year"]]).sum()
    g = b.groupby(["sector", "year"])
    s = pd.DataFrame({"residents": g["residents"].sum(), "area": g["area_km2"].sum(), "n_flytip": g["n_flytip"].sum(),
                      "private_rent_share": wavg("private_rent_share"), "no_car_share": wavg("no_car_share"),
                      "t_hwrc_min": wavg("t_hwrc_min"), "rural": wavg("rural"), "n_lsoas": g.size(),
                      **{c: wavg(c) for c in EXTRA}}).reset_index()
    s = add_steps(s)
    s["log_residents"] = np.log(s["residents"])
    s["log_density"] = np.log(s["residents"] / s["area"])
    s["private_rent_10"] = s["private_rent_share"] / 0.10
    s["no_car_10"] = s["no_car_share"] / 0.10
    s["t_hwrc_5"] = s["t_hwrc_min"] / 5
    years = sorted(set(rec["year"]) & set(s["year"]))
    s = s[s["year"].isin(years)]
    cnt = rec.groupby(["sector", "year", "received"]).size().unstack(fill_value=0)
    cnt.columns = ["n_council_" + c.replace(" ", "_") for c in cnt.columns]
    cnt["n_council"] = cnt.sum(axis=1)
    s = s.merge(cnt.reset_index(), on=["sector", "year"], how="left").fillna(0)
    print(f"Leeds: {cnt['n_council'].sum():,.0f} records, {s['n_council'].sum():,.0f} in sectors matched to "
          f"neighbourhoods ({s['sector'].nunique()} sectors)")
    return s.assign(unit=s["sector"], council="Leeds", LAD25CD=LADS["Leeds"],
                    lad_year=LADS["Leeds"] + "_" + s["year"].astype(str))


def fit(d: pd.DataFrame, y: str, rhs: str, fe: str, label: dict) -> list[dict]:
    d = d[d.groupby(fe.split(" + ")[0])[y].transform("sum") > 0] if "unit" in fe else d
    try:
        m = pf.fepois(f"{y} ~ {rhs} | {fe}", data=d, offset="log_residents", vcov={"CRV1": "unit"})
    except Exception as e:  # e.g. no reports of this type
        return [{**label, "outcome": y, "term": "not estimable", "note": str(e)[:80]}]
    rows = []
    for t in m.coef().index:
        b, se = m.coef()[t], m.se()[t]
        rows.append({**label, "outcome": y, "term": t, "irr": np.exp(b), "lo": np.exp(b - 1.96 * se),
                     "hi": np.exp(b + 1.96 * se), "p": m.pvalue()[t], "n_area_years": int(m._N),
                     "n_areas": d["unit"].nunique(), "n_records": int(d[y].sum()),
                     "years": f"{int(d['year'].min())} to {int(d['year'].max())}"})
    return rows


def leeds_closure_event(s: pd.DataFrame) -> pd.DataFrame:
    """Leeds sectors whose drive time rose by at least a minute in 2014 (the
    closure of the Stanley Road site in Harehills after 2013) against sectors whose
    drive time never changed, year by year relative to 2013."""
    s = s.sort_values(["unit", "year"]).copy()
    s["dt"] = s.groupby("unit")["t_hwrc_min"].diff()
    changed = s[s["dt"].abs() >= 1]
    treated = set(changed.loc[changed["year"] == 2014, "unit"])
    d = s[~s["unit"].isin(set(changed["unit"]) - treated)].copy()
    d["treated"] = d["unit"].isin(treated).astype(int)
    names = []
    for y in sorted(d["year"].unique()):
        if y != 2013:
            d[f"y{y}"] = ((d["year"] == y) & (d["treated"] == 1)).astype(int)
            names.append(f"y{y}")
    rows = []
    for out in ("n_council", "n_council_found_by_council_staff", "n_council_reported_by_the_public"):
        dd = d if out == "n_council" else d[d["year"] >= 2017]
        nm = [n for n in names if int(n[1:]) in set(dd["year"])]
        base = "y2017" if out != "n_council" else None  # staff/public split starts in 2017
        nm = [n for n in nm if n != base]
        m = pf.fepois(f"{out} ~ {' + '.join(nm)} | unit + year", data=dd, offset="log_residents",
                      vcov={"CRV1": "unit"})
        for t in m.coef().index:
            b, se = m.coef()[t], m.se()[t]
            rows.append({"outcome": out, "year": int(t[1:]), "reference_year": 2013 if base is None else 2017,
                         "irr": np.exp(b), "lo": np.exp(b - 1.96 * se), "hi": np.exp(b + 1.96 * se),
                         "p": m.pvalue()[t], "n_treated_sectors": len(treated),
                         "n_comparison_sectors": d.loc[d["treated"] == 0, "unit"].nunique(),
                         "n_records": int(dd[out].sum())})
    return pd.DataFrame(rows)


def run(panels: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, val = [], []
    for council, d in panels.items():
        rural = " + rural" if d["rural"].std() > 0 else ""
        cross = f"t_hwrc_5 + {CONTROLS}{rural}"
        unit = "LSOA" if council != "Leeds" else "postcode sector"
        lab = {"council": council, "area": unit}
        outcomes = ["n_council", "n_flytip"] + sorted(c for c in d.columns if c.startswith("n_council_"))
        for y in outcomes:
            rows += fit(d, y, cross, "lad_year", {**lab, "model": "same council and year"})
        for y in ("n_council", "n_flytip"):
            rows += fit(d, y, f"{cross} + {EXTRA_RHS}", "lad_year",
                        {**lab, "model": "same council and year, plus deprivation and housing type"})
        changed = (d.groupby("unit")["t_hwrc_min"].agg(lambda s: s.max() - s.min()) >= 1).sum()
        for y in ("n_council", "n_flytip"):
            rows += [{**r, "areas_drive_time_changed": int(changed)}
                     for r in fit(d, y, "t_hwrc_5", "unit + year", {**lab, "model": "same area over time"})]
        tot = d.groupby("unit")[["n_council", "n_flytip", "residents"]].agg(
            {"n_council": "sum", "n_flytip": "sum", "residents": "first"})
        val.append({"council": council, "area": unit, "years": f"{int(d['year'].min())} to {int(d['year'].max())}",
                    "n_areas": len(tot), "council_records": int(tot["n_council"].sum()),
                    "fixmystreet_reports": int(tot["n_flytip"].sum()),
                    "fms_per_100_council_records": 100 * tot["n_flytip"].sum() / tot["n_council"].sum(),
                    "rank_correlation_per_resident": (tot["n_council"] / tot["residents"]).corr(
                        tot["n_flytip"] / tot["residents"], method="spearman")})
    return pd.DataFrame(rows), pd.DataFrame(val)


if __name__ == "__main__":
    base = lsoa_base()
    recs = {"York": load_york(), "Bassetlaw": load_bassetlaw(), "Bradford": load_bradford()}
    panels = {c: lsoa_panel_for(r, base, c) for c, r in recs.items()}
    panels["Leeds"] = leeds_panel(load_leeds(), base)
    res, val = run(panels)
    res.to_csv(OUT / "council_records_models.csv", index=False)
    ev = leeds_closure_event(panels["Leeds"])
    ev.to_csv(OUT / "council_records_leeds_closure.csv", index=False)
    print(ev[ev["outcome"] == "n_council"].round(2).to_string(index=False))
    val.to_csv(OUT / "council_records_validation.csv", index=False)
    pd.set_option("display.width", 250)
    print(val.round(3).to_string(index=False))
    keep = res[res["term"].isin(["t_hwrc_5", "private_rent_10", "no_car_10", "rural"])]
    print(keep[["council", "model", "outcome", "term", "irr", "lo", "hi", "p", "n_area_years", "n_records"]]
          .round(3).to_string(index=False))
