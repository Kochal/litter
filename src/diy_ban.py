"""Did the England ban on charging residents for DIY waste at recycling centres
(from 31 December 2023) change fly-tipping?

Treatment: waste disposal authorities (the councils that run recycling centres)
that charged residents for DIY waste such as rubble, plasterboard or soil before
the ban, read from archived council pages (hwrc_rules.py): a council domain counts
as charging if its pages mention such charges in at least two of the years 2019
to 2023, and an authority counts as charging if any domain describing its centres
does. Authorities with no archived pages in those years are left out.

Comparison: English authorities that did not charge. Wales, where the ban does not
apply, is a second comparison in a variant.

Outcome: official council fly-tipping counts per council and year (Defra and
StatsWales), 2018/19 to 2024/25. 2024/25 is the first full year after the ban;
2023/24 had one quarter under it. Construction and demolition waste is the waste
type the ban targets; household bags and the placebo types (animal carcasses,
clinical waste, vehicle parts) should not respond.

Models: Poisson with council and year fixed effects and a log-population offset;
errors clustered by waste disposal authority. Event study relative to 2022/23.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyfixest as pf

ROOT = Path(__file__).resolve().parents[1]
INTERIM = ROOT / "data" / "interim"
OUT = ROOT / "outputs"
sys.path.insert(0, str(Path(__file__).parent))
from build_analysis import JOINT_WDA, OUTCOMES  # noqa: E402

YEARS = range(2018, 2025)
REF = 2022
PRE_BAN = range(2019, 2024)


def charging_authorities() -> pd.DataFrame:
    cy = pd.read_csv(INTERIM / "hwrc_rules_council_year.csv")
    pre = cy[cy["year"].isin(PRE_BAN)]
    dom = pre.groupby("domain").agg(years_charging=("diy_charge", "sum"), years_seen=("year", "nunique"),
                                    example=("charge_text", lambda s: next((t for t in s if isinstance(t, str) and t), "")))
    dom["charging"] = dom["years_charging"] >= 2
    sites = pd.read_csv(ROOT / "data" / "wayback" / "hwrc_sites_all.csv")
    sites["wda"] = sites["council"]
    for name, members in JOINT_WDA.items():
        sites.loc[sites["district"].isin(members), "wda"] = name
    pairs = sites.assign(domain=sites["domains"].str.split(";")).explode("domain")[["wda", "nation", "domain"]]
    pairs = pairs.drop_duplicates().merge(dom, left_on="domain", right_index=True)
    w = pairs.groupby(["wda", "nation"]).agg(charging=("charging", "max"), domains=("domain", "nunique"),
                                             domains_charging=("charging", "sum"),
                                             example=("example", lambda s: max(s, key=len))).reset_index()
    return w


def panel(w: pd.DataFrame) -> pd.DataFrame:
    d = pd.read_csv(ROOT / "data" / "analysis" / "council_year.csv")
    for k, cols in OUTCOMES.items():
        d[k] = d[cols].sum(axis=1, min_count=1)
    d = d[d["year"].isin(YEARS) & d["population"].gt(0)].copy()
    d["log_pop"] = np.log(d["population"])
    d = d.merge(w[["wda", "charging"]].drop_duplicates("wda"), on="wda", how="left")
    d["group"] = np.where(d["nation"] == "Wales", "Wales",
                          np.where(d["charging"] == True, "charged", np.where(d["charging"] == False, "did not charge", "unknown")))  # noqa: E712
    return d[d["group"] != "unknown"]


def fit(d: pd.DataFrame, outcome: str, event: bool, treated: str, control: str) -> list[dict]:
    d = d[d["group"].isin([treated, control])].dropna(subset=[outcome]).copy()
    d["treat"] = (d["group"] == treated).astype(int)
    if event:
        names = []
        for y in YEARS:
            if y != REF:
                d[f"y{y}"] = ((d["year"] == y) & (d["treat"] == 1)).astype(int)
                names.append(f"y{y}")
        rhs = " + ".join(names)
    else:
        d = d[d["year"] != 2023]  # one quarter under the ban
        d["after_ban"] = ((d["year"] >= 2024) & (d["treat"] == 1)).astype(int)
        rhs = "after_ban"
    m = pf.fepois(f"{outcome} ~ {rhs} | LAD25CD + year", data=d, offset="log_pop", vcov={"CRV1": "wda"})
    rows = []
    for t in m.coef().index:
        b, se = m.coef()[t], m.se()[t]
        rows.append({"comparison": f"{treated} vs {control}", "outcome": outcome, "term": t,
                     "year": int(t[1:]) if t.startswith("y") else 2024, "irr": np.exp(b), "lo": np.exp(b - 1.96 * se),
                     "hi": np.exp(b + 1.96 * se), "p": m.pvalue()[t], "n_council_years": int(m._N),
                     "n_councils_treated": d.loc[d["treat"] == 1, "LAD25CD"].nunique(),
                     "n_councils_comparison": d.loc[d["treat"] == 0, "LAD25CD"].nunique(),
                     "n_authorities_treated": d.loc[d["treat"] == 1, "wda"].nunique(),
                     "incidents": int(d[outcome].sum())})
    return rows


FMS_YEARS = range(2019, 2026)


def fms_panel(w: pd.DataFrame) -> pd.DataFrame:
    """FixMyStreet reports per neighbourhood and year, by waste type from the report
    text (fms_types.py), in councils with at least 50 reports in every year."""
    from access_panel import lsoa_to_lad
    t = pd.read_csv(INTERIM / "fms_types_lsoa_year.csv")
    n = pd.read_csv(INTERIM / "fms_flytip_lsoa_year.csv")
    cen = pd.read_csv(INTERIM / "census_lsoa.csv")[["LSOA21CD", "residents"]]
    lad = lsoa_to_lad()
    cy = pd.read_csv(ROOT / "data" / "analysis" / "council_year.csv")[["LAD25CD", "wda", "nation"]].drop_duplicates("LAD25CD")
    grid = pd.MultiIndex.from_product([cen["LSOA21CD"], list(FMS_YEARS)], names=["LSOA21CD", "year"]).to_frame(index=False)
    d = (grid.merge(n, on=["LSOA21CD", "year"], how="left").merge(t, on=["LSOA21CD", "year"], how="left")
             .merge(cen, on="LSOA21CD").merge(lad, on="LSOA21CD").merge(cy, on="LAD25CD"))
    for c in ("n_flytip", "bags", "bulky", "construction"):
        d[c] = d[c].fillna(0)
    yearly = d.groupby(["LAD25CD", "year"])["n_flytip"].sum().unstack()
    active = yearly.index[(yearly >= 50).all(axis=1)]
    d = d[d["LAD25CD"].isin(active)].copy()
    d["log_pop"] = np.log(d["residents"])
    d = d.merge(w[["wda", "charging"]].drop_duplicates("wda"), on="wda", how="left")
    d["group"] = np.where(d["nation"] == "Wales", "Wales",
                          np.where(d["charging"] == True, "charged", np.where(d["charging"] == False, "did not charge", "unknown")))  # noqa: E712
    return d[d["group"] != "unknown"]


def fit_fms(d: pd.DataFrame, outcome: str, event: bool, share: bool = False) -> list[dict]:
    """share=True compares the outcome with all fly-tipping reports in the same
    neighbourhood and year (offset log reports), so changes in how much people use
    FixMyStreet cancel out."""
    d = d[d["group"].isin(["charged", "did not charge"])].copy()
    if share:
        d = d[d["n_flytip"] > 0]
        d["log_pop"] = np.log(d["n_flytip"])
    d["treat"] = (d["group"] == "charged").astype(int)
    d = d[d.groupby("LSOA21CD")[outcome].transform("sum") > 0]
    if event:
        names = [f"y{y}" for y in FMS_YEARS if y != 2023]
        for nm in names:
            d[nm] = ((d["year"] == int(nm[1:])) & (d["treat"] == 1)).astype(int)
        rhs = " + ".join(names)
    else:
        d["after_ban"] = ((d["year"] >= 2024) & (d["treat"] == 1)).astype(int)
        rhs = "after_ban"
    m = pf.fepois(f"{outcome} ~ {rhs} | LSOA21CD + year", data=d, offset="log_pop", vcov={"CRV1": "wda"})
    rows = []
    for t in m.coef().index:
        b, se = m.coef()[t], m.se()[t]
        rows.append({"source": "FixMyStreet", "comparison": "charged vs did not charge",
                     "outcome": outcome + (" as share of all reports" if share else ""), "term": t,
                     "year": int(t[1:]) if t.startswith("y") else 2024, "irr": np.exp(b),
                     "lo": np.exp(b - 1.96 * se), "hi": np.exp(b + 1.96 * se), "p": m.pvalue()[t],
                     "n_lsoa_years": int(m._N), "n_councils_treated": d.loc[d["treat"] == 1, "LAD25CD"].nunique(),
                     "n_councils_comparison": d.loc[d["treat"] == 0, "LAD25CD"].nunique(),
                     "reports": int(d[outcome].sum())})
    return rows


if __name__ == "__main__":
    w = charging_authorities()
    w.to_csv(OUT / "diy_charging_authorities.csv", index=False)
    print(w.groupby("nation")["charging"].agg(["sum", "size"]))
    d = panel(w)
    rows = []
    for outcome in ("cde", "total", "bags_household", "hwrc_type", "placebo"):
        for event in (False, True):
            rows += fit(d, outcome, event, "charged", "did not charge")
        rows += fit(d, outcome, False, "charged", "Wales")
    res = pd.DataFrame(rows).assign(source="official counts")
    f = fms_panel(w)
    frows = []
    for outcome in ("construction", "bags", "bulky", "n_flytip"):
        for event in (False, True):
            frows += fit_fms(f, outcome, event)
    for outcome in ("construction", "bags", "bulky"):
        for event in (False, True):
            frows += fit_fms(f, outcome, event, share=True)
    res = pd.concat([res, pd.DataFrame(frows)], ignore_index=True)
    res.to_csv(OUT / "diy_ban.csv", index=False)
    pd.set_option("display.width", 220)
    print(res.round(3).to_string(index=False))
