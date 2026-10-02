"""Count models of council fly-tipping (see docs/research_brief.md, section 5.3).

1. Between-council: which council characteristics go with higher fly-tipping
   rates? Pooled 2022/23 to 2024/25, Poisson pseudo-maximum likelihood (PPML)
   with a log-population offset, region and year effects. Associational only.
2. Within-council: do changes in HWRC drive time over 2012/13 to 2024/25 go with
   changes in fly-tipping? PPML with council fixed effects and region-by-year
   effects, so national trends (landfill tax, FPN reforms, Covid) and fixed
   council traits (recording culture, urbanity) are absorbed.
Outcomes are split by waste type, size and land type, with placebo waste types
(animal carcasses, clinical, vehicle parts) that HWRC access should not affect.
Standard errors are clustered by waste disposal authority."""
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "analysis" / "council_year.csv"
OUT = ROOT / "outputs"

OUTCOME_LABELS = {
    "total": "All incidents",
    "hwrc_type": "HWRC-type household (bulky, white goods, electrical, green)",
    "bags_household": "Household black bags",
    "cde": "Construction / demolition",
    "commercial": "Commercial waste",
    "car_boot_to_van": "Car boot to transit van size",
    "tipper_plus": "Tipper lorry or larger",
    "highway_alley": "Highway, footpath, back alley",
    "placebo": "Placebo: carcasses, clinical, vehicle parts",
}

# Rescaled so incidence rate ratios read per meaningful step
SCALES = {
    "t_hwrc_mean": 5,            # per 5 minutes' drive
    "t_transfer_mean": 5,
    "t_landfill_mean": 10,
    "private_rent_share": 0.10,  # per 10 percentage points
    "social_rent_share": 0.10,
    "no_car_share": 0.10,
    "flat_share": 0.10,
    "student_share": 0.05,
    "hh_deprived_2plus_share": 0.05,
    "churn_rate": 0.05,
    "log_density": 1,
}
BETWEEN_X = list(SCALES)


def load() -> pd.DataFrame:
    d = pd.read_csv(DATA)
    for k, s in SCALES.items():
        if k in d:
            d[k + "_s"] = d[k] / s
    return d


def fit_ppml(formula: str, data: pd.DataFrame):
    m = smf.glm(formula, data=data, family=sm.families.Poisson(), offset=data["log_pop"])
    return m.fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(data["wda"])[0]}, maxiter=200)


def tidy(res, terms, outcome, model) -> pd.DataFrame:
    rows = []
    for t in terms:
        b, se = res.params[t], res.bse[t]
        rows.append({"model": model, "outcome": outcome, "term": t.removesuffix("_s"),
                     "irr": np.exp(b), "lo": np.exp(b - 1.96 * se), "hi": np.exp(b + 1.96 * se),
                     "p": res.pvalues[t], "n": int(res.nobs)})
    return pd.DataFrame(rows)


def between(d: pd.DataFrame) -> pd.DataFrame:
    s = d[(d["year"] >= 2022)].copy()
    xs = [x + "_s" for x in BETWEEN_X]
    out = []
    for y in OUTCOME_LABELS:
        dd = s.dropna(subset=[y, "log_pop", *xs])
        f = f"{y} ~ {' + '.join(xs)} + basis_public_only + basis_changed + C(region) + C(year)"
        out.append(tidy(fit_ppml(f, dd), xs, y, "between"))
    return pd.concat(out)


def within(d: pd.DataFrame, nation: str | None = "England") -> pd.DataFrame:
    s = d if nation is None else d[d["nation"] == nation]
    out = []
    for y in OUTCOME_LABELS:
        dd = s.dropna(subset=[y, "log_pop", "t_hwrc_mean_s"])
        # Councils with all-zero outcomes add nothing under fixed effects
        dd = dd[dd.groupby("LAD25CD")[y].transform("sum") > 0]
        f = (f"{y} ~ t_hwrc_mean_s + basis_public_only + basis_changed"
             " + C(LAD25CD) + C(region):C(year)")
        out.append(tidy(fit_ppml(f, dd), ["t_hwrc_mean_s"], y, "within"))
    return pd.concat(out)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    d = load()
    b = between(d)
    w = within(d)
    res = pd.concat([b, w])
    res["outcome_label"] = res["outcome"].map(OUTCOME_LABELS)
    res.to_csv(OUT / "model_results.csv", index=False)
    pd.set_option("display.width", 200)
    print(res.round(3).to_string(index=False))
