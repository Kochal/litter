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
import pyfixest as pf

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
    "t_hwrc_mean_cens": 5,
    "t_hwrc_mean_verified": 5,
    "t_hwrc_mean_strict": 5,
    "t_hwrc_mean_lag": 5,
    "t_hwrc_nocar": 5,
    "share_over_15": 0.10,       # per 10 points of population >15 minutes away
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
BETWEEN_X = ["t_hwrc_mean", "t_transfer_mean", "t_landfill_mean", "private_rent_share",
             "social_rent_share", "no_car_share", "flat_share", "student_share",
             "hh_deprived_2plus_share", "churn_rate", "log_density"]
# Within-council specifications: (label, treatment, sample filter, extra controls)
WITHIN_SPECS = [
    ("main", "t_hwrc_mean", None, ""),
    ("censored recent dropouts", "t_hwrc_mean_cens", None, ""),
    ("verified closures", "t_hwrc_mean_verified", None, ""),
    ("strict: only confirmed or likely closures", "t_hwrc_mean_strict", None, ""),
    ("2012 to 2019 only", "t_hwrc_mean", "year <= 2019", ""),
    ("lagged one year", "t_hwrc_mean_lag", None, ""),
    ("no-car weighted", "t_hwrc_nocar", None, ""),
    ("share >15 min", "share_over_15", None, ""),
    ("all-incidents basis only", "t_hwrc_mean", "basis_public_only == 0 and basis_changed == 0", ""),
    ("2017 on, no spend control", "t_hwrc_mean_cens", "year >= 2017 and log_cleansing_pc == log_cleansing_pc", ""),
    ("2017 on, street cleansing spend", "t_hwrc_mean_cens", "year >= 2017 and log_cleansing_pc == log_cleansing_pc",
     " + log_cleansing_pc"),
]


def load() -> pd.DataFrame:
    d = pd.read_csv(DATA)
    for k, s in SCALES.items():
        if k in d:
            d[k + "_s"] = d[k] / s
    return d


def fit_ppml(formula: str, data: pd.DataFrame):
    """PPML (Poisson) with absorbed fixed effects (after '|'), log-population offset
    and errors clustered by waste disposal authority."""
    return pf.fepois(formula, data=data, offset="log_pop", vcov={"CRV1": "wda"},
                     iwls_maxiter=200)


def tidy(res, terms, outcome, model) -> pd.DataFrame:
    coef, se, p = res.coef(), res.se(), res.pvalue()
    rows = []
    for t in terms:
        b, s_ = coef[t], se[t]
        rows.append({"model": model, "outcome": outcome, "term": t.removesuffix("_s"),
                     "irr": np.exp(b), "lo": np.exp(b - 1.96 * s_), "hi": np.exp(b + 1.96 * s_),
                     "p": p[t], "n": int(res._N)})
    return pd.DataFrame(rows)


def between(d: pd.DataFrame) -> pd.DataFrame:
    s = d[(d["year"] >= 2022)].copy()
    xs = [x + "_s" for x in BETWEEN_X]
    out = []
    for y in OUTCOME_LABELS:
        dd = s.dropna(subset=[y, "log_pop", *xs])
        f = f"{y} ~ {' + '.join(xs)} + basis_public_only + basis_changed | region + year"
        out.append(tidy(fit_ppml(f, dd), xs, y, "between"))
    return pd.concat(out)


def within(d: pd.DataFrame, nation: str | None = "England") -> pd.DataFrame:
    s = d if nation is None else d[d["nation"] == nation]
    out = []
    for label, x, cond, extra in WITHIN_SPECS:
        ss = s.query(cond) if cond else s
        for y in OUTCOME_LABELS:
            dd = ss.dropna(subset=[y, "log_pop", x + "_s"])
            f = f"{y} ~ {x}_s + basis_public_only + basis_changed{extra} | LAD25CD + region^year"
            try:
                r = tidy(fit_ppml(f, dd), [x + "_s"], y, "within")
            except Exception as e:  # e.g. no variation left after a sample restriction
                print("skip", label, y, e)
                continue
            out.append(r.assign(spec=label))
    return pd.concat(out)


def event_study(d: pd.DataFrame, x: str = "t_hwrc_mean_cens", jump: float = 1.0,
                window: int = 4) -> pd.DataFrame:
    """Fly-tipping before and after the first year a council's mean HWRC drive time
    rises by at least `jump` minutes, against councils whose access never moved by
    more than half a minute in any year (clean never-treated controls). Event-time
    dummies are binned at +/- window, with the year before the event as reference."""
    e = d[d["nation"] == "England"].sort_values(["LAD25CD", "year"]).copy()
    e["dt"] = e.groupby("LAD25CD")[x].diff()
    first = e[e["dt"] >= jump].groupby("LAD25CD")["year"].min().rename("event_year")
    maxabs = e.groupby("LAD25CD")["dt"].apply(lambda s: s.abs().max())
    controls = maxabs[maxabs < 0.5].index
    e = e.merge(first, on="LAD25CD", how="left")
    e = e[e["LAD25CD"].isin(controls) | e["event_year"].notna()].copy()
    rel = (e["year"] - e["event_year"]).clip(-window, window)
    names = []
    for k in range(-window, window + 1):
        if k == -1:
            continue
        nm = f"ev_m{-k}" if k < 0 else f"ev_p{k}"
        e[nm] = (rel == k).astype(int)
        names.append(nm)
    out = []
    for y in ["total", "hwrc_type", "bags_household", "cde", "placebo"]:
        dd = e.dropna(subset=[y, "log_pop"])
        r = fit_ppml(f"{y} ~ {' + '.join(names)} + basis_public_only + basis_changed"
                     " | LAD25CD + region^year", dd)
        t = tidy(r, names, y, "event study")
        t["event_time"] = [int(n[4:]) * (-1 if n[3] == "m" else 1) for n in names]
        t["n_treated"] = int(e["event_year"].notna().groupby(e["LAD25CD"]).first().sum())
        out.append(t)
    return pd.concat(out)


def between_simple(d: pd.DataFrame) -> pd.DataFrame:
    """HWRC drive time with region and year effects only, to show how much the
    full covariate set changes the picture."""
    s = d[d["year"] >= 2022]
    out = []
    for y in OUTCOME_LABELS:
        dd = s.dropna(subset=[y, "log_pop", "t_hwrc_mean_s"])
        r = fit_ppml(f"{y} ~ t_hwrc_mean_s + basis_public_only + basis_changed | region + year", dd)
        out.append(tidy(r, ["t_hwrc_mean_s"], y, "between (no covariates)"))
    return pd.concat(out)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    d = load()
    b = between(d).assign(spec="full covariates")
    b0 = between_simple(d).assign(spec="region and year only")
    w = within(d)
    ev = pd.concat([
        event_study(d).assign(spec="first rise of 1+ min, never-moved controls"),
        event_study(d, x="t_hwrc_mean_verified").assign(spec="verified closures"),
    ])
    ev.to_csv(OUT / "event_study.csv", index=False)
    res = pd.concat([b, b0, w])
    res["outcome_label"] = res["outcome"].map(OUTCOME_LABELS)
    res.to_csv(OUT / "model_results.csv", index=False)
    pd.set_option("display.width", 200)
    print(res.round(3).to_string(index=False))
