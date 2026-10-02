"""Council street cleansing spending (MHCLG revenue outturn, RO5), 2017/18 to
2024/25, on December 2025 codes. Street cleansing is where fly-tips are found and
recorded, so spending is a proxy for recording effort (docs/research_brief.md,
section 5.2). England only."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"

COLS = {"RO5_envstr_net_cur_exp": "street_cleansing_k", "RO5_envcll_net_cur_exp": "waste_collection_k"}


def build() -> pd.DataFrame:
    ro = pd.read_csv(RAW / "ro_timeseries.csv", usecols=["year_ending", "ONS_code", *COLS], low_memory=False)
    ro = ro[ro["ONS_code"].astype(str).str.match(r"^E0[6-9]\d{6}$")]
    ro["year"] = ro["year_ending"].astype(str).str[:4].astype(int) - 1  # 201803 -> 2017/18
    for c in COLS:
        ro[c] = pd.to_numeric(ro[c], errors="coerce")
    lk = pd.read_csv(INTERIM / "lad_to_lad25.csv")[["old_code", "LAD25CD"]]
    ro = ro.merge(lk, left_on="ONS_code", right_on="old_code", how="inner")
    out = ro.groupby(["LAD25CD", "year"])[list(COLS)].sum(min_count=1).rename(columns=COLS)
    return out.reset_index()


if __name__ == "__main__":
    f = build()
    f.to_csv(INTERIM / "finance.csv", index=False)
    print(f.groupby("year")[["street_cleansing_k"]].agg(["count", "sum"]).to_string())
