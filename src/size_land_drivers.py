"""Council comparison (as models.between: 2022/23 to 2024/25, region and year
effects, all council characteristics together) with fly-tipping split by size of
load and by type of land, to see which drivers go with small items, van loads and
lorry loads, and with kerbside versus countryside dumping.
Output: outputs/size_land_drivers.csv
"""
from pathlib import Path

import pandas as pd

from models import BETWEEN_X, OUT, fit_ppml, load, tidy

GROUPS = {
    "small items (single bag, single item, car boot)": ["size_single_bag", "size_single_item", "size_car_boot"],
    "van loads": ["size_small_van", "size_transit_van"],
    "tipper lorry or larger": ["size_tipper", "size_multi"],
    "highways, footpaths and back alleys": ["land_highway", "land_footpath", "land_back_alley"],
    "council land": ["land_council"],
    "private and residential land": ["land_private"],
    "agricultural land": ["land_agricultural"],
}

if __name__ == "__main__":
    d = load()
    s = d[d["year"] >= 2022].copy()
    xs = [x + "_s" for x in BETWEEN_X]
    out = []
    for name, cols in GROUPS.items():
        s[name] = s[cols].sum(axis=1, min_count=1)
        dd = s.dropna(subset=[name, "log_pop", *xs])
        r = tidy(fit_ppml(f"Q('{name}') ~ {' + '.join(xs)} + basis_public_only + basis_changed | region + year", dd),
                 xs, name, "between")
        out.append(r.assign(n_council_years=len(dd), incidents=int(dd[name].sum())))
    res = pd.concat(out)
    res.to_csv(OUT / "size_land_drivers.csv", index=False)
    k = res[res["term"].isin(["private_rent_share", "no_car_share", "t_hwrc_mean", "hh_deprived_2plus_share"])]
    print(k.pivot_table(index="outcome", columns="term", values="irr").round(2).to_string())
    print(k.pivot_table(index="outcome", columns="term", values="p").round(3).to_string())
    print(res.groupby("outcome")[["n_council_years", "incidents"]].first())
