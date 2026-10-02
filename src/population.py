"""Council mid-year population and migration churn, 2012 to 2025, on December 2025
local authority codes (ONS MYEB3, April 2023 geography)."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"


def build() -> pd.DataFrame:
    m = pd.read_excel(RAW / "mye_ts_2011_2025.xlsx", sheet_name="MYEB3", header=1)
    long = m.melt(id_vars=["ladcode23", "laname23", "country"])
    long[["measure", "year"]] = long["variable"].str.rsplit("_", n=1, expand=True)
    long["year"] = long["year"].astype(int)
    keep = {"population", "internal_in", "internal_out", "international_in", "international_out"}
    wide = long[long["measure"].isin(keep)].pivot_table(
        index=["ladcode23", "year"], columns="measure", values="value").reset_index()
    lk = pd.read_csv(INTERIM / "lad_to_lad25.csv")[["old_code", "LAD25CD"]]
    wide = wide.merge(lk, left_on="ladcode23", right_on="old_code", how="left")
    assert wide["LAD25CD"].notna().all()
    out = wide.groupby(["LAD25CD", "year"], as_index=False)[sorted(keep)].sum()
    # Gross migration flows per head: a proxy for residential turnover
    out["churn_rate"] = (out["internal_in"] + out["internal_out"]
                         + out["international_in"] + out["international_out"]) / out["population"]
    return out


if __name__ == "__main__":
    p = build()
    p.to_csv(INTERIM / "population.csv", index=False)
    print(p.shape, p.year.min(), p.year.max(), p.LAD25CD.nunique())
