"""Can changes in private renting and car ownership explain why recorded
fly-tipping rose between 2012/13 and 2024/25?

1. Shares of households renting privately and without a car or van, Census 2011
   (Nomis KS402EW, KS404EW) and Census 2021 (census.py), per council on 2025
   boundaries, and nationally.
2. Predicted change: the change in each share times the council-comparison
   estimates (models.py, between councils), against the actual change.
3. Council by council: growth in fly-tipping per person (2012/13 to 2014/15
   against 2022/23 to 2024/25) against the change in each share, allowing for the
   2021 levels, deprivation, density and region (least squares weighted by
   population). In all councils and in the councils with no sudden step in
   recording (recording_changes.py).
4. A widening gap: Poisson model of each council's yearly counts with council and
   year fixed effects, plus each 2021 characteristic times years since 2012, so
   each coefficient is the extra growth per decade in places with 10 percentage
   points more of that characteristic.
5. Other candidate causes, same council over time (council and year fixed
   effects): residents moving in or out (churn, per 5 percentage points of the
   population a year, 2012 to 2024) and street-cleansing spending per person (log,
   2017/18 onwards, from council revenue outturns).
6. National descriptives by year: churn, cleansing spending (nominal), and
   enforcement (prosecutions and fixed penalty notices per 1,000 incidents).
   Spending is also given in 2024/25 prices (ONS consumer prices index D7BT,
   data/cpi_ons_d7bt.csv).
By size of load: all, small items, van loads, tipper lorry or larger.
Outputs: outputs/composition_shares.csv, outputs/composition_change.csv,
outputs/rise_factors_by_year.csv.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import pyfixest as pf
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "census2011"
INTERIM = ROOT / "data" / "interim"
OUT = ROOT / "outputs"
SIZES = {"all": ["total"], "small items": ["size_single_bag", "size_single_item", "size_car_boot"],
         "van loads": ["size_small_van", "size_transit_van"], "tipper lorry or larger": ["size_tipper", "size_multi"]}


def shares_2011() -> pd.DataFrame:
    t = pd.read_csv(RAW / "ks402_tenure_lad.csv").pivot_table(index="GEOGRAPHY_CODE", columns="CELL_NAME", values="OBS_VALUE")
    c = pd.read_csv(RAW / "ks404_cars_lad.csv").pivot_table(index="GEOGRAPHY_CODE", columns="CELL_NAME", values="OBS_VALUE")
    d = pd.DataFrame({"households": t["All households"], "private": t["Private rented"],
                      "nocar": c["No cars or vans in household"]})
    lk = pd.read_csv(INTERIM / "lad_to_lad25.csv")
    m = dict(zip(lk["old_code"], lk["LAD25CD"]))
    d["LAD25CD"] = [m.get(k, k) for k in d.index]
    g = d.groupby("LAD25CD")[["households", "private", "nocar"]].sum()
    return pd.DataFrame({"households_2011": g["households"], "rent_2011": g["private"] / g["households"],
                         "nocar_2011": g["nocar"] / g["households"]})


def main():
    s21 = pd.read_csv(INTERIM / "census_council.csv").set_index("LAD25CD")
    s = shares_2011().join(s21[["households", "private_rent_share", "no_car_share", "hh_deprived_2plus_share"]], how="inner")
    s = s.rename(columns={"households": "households_2021", "private_rent_share": "rent_2021", "no_car_share": "nocar_2021"})
    s["d_rent"] = (s["rent_2021"] - s["rent_2011"]) * 100      # percentage points
    s["d_nocar"] = (s["nocar_2021"] - s["nocar_2011"]) * 100
    s.reset_index().round(4).to_csv(OUT / "composition_shares.csv", index=False)
    nat = {}
    for nation, pre in (("England", "E"), ("Wales", "W")):
        x = s[s.index.str.startswith(pre)]
        for y in ("2011", "2021"):
            nat[(nation, y)] = {"rent": (x[f"rent_{y}"] * x[f"households_{y}"]).sum() / x[f"households_{y}"].sum(),
                                "nocar": (x[f"nocar_{y}"] * x[f"households_{y}"]).sum() / x[f"households_{y}"].sum()}
    print("National shares:", {k: {a: round(b * 100, 1) for a, b in v.items()} for k, v in nat.items()})

    d = pd.read_csv(ROOT / "data" / "analysis" / "council_year.csv")
    rec = pd.read_csv(OUT / "recording_changes.csv")
    smooth = set(rec.loc[rec["class"].isin(["steady rise", "little change"]), "LAD25CD"])
    for k, cols in SIZES.items():
        d[k] = d[cols].sum(axis=1, min_count=1)
    rows = []

    # 2. Predicted national change from composition (council-comparison estimates, per 10 points)
    m = pd.read_csv(OUT / "model_results.csv")
    sz = pd.read_csv(OUT / "size_land_drivers.csv")
    est = {"all": ("total", None), "small items": (None, "small items (single bag, single item, car boot)"),
           "van loads": (None, "van loads"), "tipper lorry or larger": ("tipper_plus", None)}
    dr = (nat[("England", "2021")]["rent"] - nat[("England", "2011")]["rent"]) * 10   # in 10-point steps
    dn = (nat[("England", "2021")]["nocar"] - nat[("England", "2011")]["nocar"]) * 10
    for k, (mo, so) in est.items():
        src = m[(m["model"] == "between") & (m["outcome"] == mo)] if mo else sz[sz["outcome"] == so]
        b = src.set_index("term")["irr"]
        pred = b["private_rent_share"] ** dr * b["no_car_share"] ** dn
        e = d[(d["nation"] == "England")]
        a = e.groupby("year")[[k, "population"]].sum()
        actual = (a.loc[2022:2024, k].sum() / a.loc[2022:2024, "population"].sum()) / \
                 (a.loc[2012:2014, k].sum() / a.loc[2012:2014, "population"].sum())
        rows.append({"analysis": "predicted from national change in shares", "outcome": k,
                     "predicted_change": pred - 1, "actual_change": actual - 1,
                     "from_renting": b["private_rent_share"] ** dr - 1, "from_no_car": b["no_car_share"] ** dn - 1})

    # 3. Council by council
    e = d[d["nation"] == "England"].copy()
    for k in SIZES:
        a = e[e["year"].between(2012, 2014)].groupby("LAD25CD")[[k, "population"]].sum()
        b = e[e["year"].between(2022, 2024)].groupby("LAD25CD")[[k, "population"]].sum()
        g = np.log((b[k] / b["population"]) / (a[k] / a["population"])).rename("growth")
        x = s.join(g, how="inner").join(e.drop_duplicates("LAD25CD").set_index("LAD25CD")[["region", "population", "log_density"]]
                                         if "log_density" in e else e.drop_duplicates("LAD25CD").set_index("LAD25CD")[["region", "population"]])
        x = x.replace([np.inf, -np.inf], np.nan).dropna(subset=["growth"])
        x["rent10"], x["nocar10"] = x["rent_2021"] * 10, x["nocar_2021"] * 10
        x["d_rent10"], x["d_nocar10"] = x["d_rent"] / 10, x["d_nocar"] / 10
        x["dep5"] = x["hh_deprived_2plus_share"] * 20
        for sample, xx in (("all councils", x), ("councils with no sudden step", x[x.index.isin(smooth)])):
            f = "growth ~ d_rent10 + d_nocar10 + rent10 + nocar10 + dep5 + C(region)"
            r = smf.wls(f, data=xx, weights=xx["population"]).fit(cov_type="HC1")
            for t in ("d_rent10", "d_nocar10", "rent10", "nocar10", "dep5"):
                rows.append({"analysis": "council growth vs change in shares", "outcome": k, "sample": sample, "term": t,
                             "growth_ratio": float(np.exp(r.params[t])), "lo": float(np.exp(r.conf_int().loc[t, 0])),
                             "hi": float(np.exp(r.conf_int().loc[t, 1])), "p": float(r.pvalues[t]), "n_councils": int(r.nobs)})

    # 4. Widening gap: 2021 characteristics x decades since 2012
    p = e.merge(s[["rent_2021", "nocar_2021"]], left_on="LAD25CD", right_index=True)
    p = p[p["population"] > 0].copy()
    p["log_pop"] = np.log(p["population"])
    tdec = (p["year"] - 2012) / 10
    p["rent_x_t"], p["nocar_x_t"], p["dep_x_t"] = p["rent_2021"] * 10 * tdec, p["nocar_2021"] * 10 * tdec, \
        p["hh_deprived_2plus_share"] * 20 * tdec
    for k in SIZES:
        for sample, pp in (("all councils", p), ("councils with no sudden step", p[p["LAD25CD"].isin(smooth)])):
            pp = pp.dropna(subset=[k])
            mm = pf.fepois(f"Q('{k}') ~ rent_x_t + nocar_x_t + dep_x_t | LAD25CD + year", data=pp, offset="log_pop",
                           vcov={"CRV1": "wda"})
            for t in ("rent_x_t", "nocar_x_t", "dep_x_t"):
                b, se = mm.coef()[t], mm.se()[t]
                rows.append({"analysis": "extra growth per decade by 2021 characteristic", "outcome": k, "sample": sample,
                             "term": t, "growth_ratio": float(np.exp(b)), "lo": float(np.exp(b - 1.96 * se)),
                             "hi": float(np.exp(b + 1.96 * se)), "p": float(mm.pvalue()[t]),
                             "n_councils": pp["LAD25CD"].nunique(), "n_council_years": int(mm._N)})
    # 5. Other candidate causes, same council over time
    p["churn5"] = p["churn_rate"] * 20                     # +1 = 5 more movers per 100 residents
    for k in SIZES:
        for sample, pp in (("all councils", p), ("councils with no sudden step", p[p["LAD25CD"].isin(smooth)])):
            for spec, rhs, sub in (("churn", "churn5", pp),
                                   ("churn and cleansing spending, 2017 on", "churn5 + log_cleansing_pc",
                                    pp[pp["year"] >= 2017])):
                sub = sub.dropna(subset=[k] + rhs.split(" + "))
                sub = sub[sub.groupby("LAD25CD")[k].transform("sum") > 0]
                mm = pf.fepois(f"Q('{k}') ~ {rhs} | LAD25CD + year", data=sub, offset="log_pop",
                               vcov={"CRV1": "wda"})
                for t in rhs.split(" + "):
                    b, se = mm.coef()[t], mm.se()[t]
                    rows.append({"analysis": "same council over time: " + spec, "outcome": k, "sample": sample,
                                 "term": t, "growth_ratio": float(np.exp(b)), "lo": float(np.exp(b - 1.96 * se)),
                                 "hi": float(np.exp(b + 1.96 * se)), "p": float(mm.pvalue()[t]),
                                 "n_councils": sub["LAD25CD"].nunique(), "n_council_years": int(mm._N)})
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "composition_change.csv", index=False)

    # 6. National descriptives (England)
    yr = e.groupby("year").agg(population=("population", "sum"), total=("total", "sum"),
                               prosecutions=("actions_prosecution", "sum"), fpn=("actions_fpn", "sum"),
                               cleansing_k=("street_cleansing_k", "sum"), councils=("LAD25CD", "nunique"))
    yr["churn_pct"] = (e["churn_rate"] * e["population"]).groupby(e["year"]).sum() / yr["population"] * 100
    yr["prosecutions_per_1000_incidents"] = yr["prosecutions"] / yr["total"] * 1000
    yr["fpn_per_1000_incidents"] = yr["fpn"] / yr["total"] * 1000
    has = e[e["street_cleansing_k"].notna()].groupby("year")["population"].sum()
    yr["cleansing_per_person_gbp"] = (yr["cleansing_k"] * 1000 / has).where(yr["cleansing_k"] > 0)
    # In 2024/25 prices: ONS CPI (D7BT), financial year = 3/4 of its first calendar year + 1/4 of the next
    cpi = pd.read_csv(ROOT / "data" / "cpi_ons_d7bt.csv").set_index("year")["cpi_2015_100"]
    fycpi = pd.Series({y: 0.75 * cpi[y] + 0.25 * cpi[y + 1] for y in yr.index if y + 1 in cpi.index})
    yr["cleansing_per_person_gbp_2024_prices"] = yr["cleansing_per_person_gbp"] * fycpi[2024] / fycpi
    yr.drop(columns="cleansing_k").round(3).to_csv(OUT / "rise_factors_by_year.csv")
    print(yr.round(2).to_string())
    pd.set_option("display.width", 230)
    print(res.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
