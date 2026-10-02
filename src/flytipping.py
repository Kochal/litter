"""Harmonised council-level fly-tipping panel for England and Wales on December
2025 local authority boundaries, 2012/13 to 2024/25."""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"

# Canonical column -> (England incidents/actions column, Wales 'Variable' label)
CATEGORIES = {
    "total": ("Total Incidents", "Total recorded incidents"),
    "land_highway": ("Highway Incidents", "Highway"),
    "land_footpath": ("Footpath / Bridleway Incidents", "Footpath / bridleway"),
    "land_back_alley": ("Back Alleyway Incidents", "Back alleyway"),
    "land_railway": ("Railway Incidents", "Railway"),
    "land_council": ("Council Land Incidents", "Council land"),
    "land_agricultural": ("Agricultural Incidents", "Agricultural"),
    "land_private": ("Private / Residential Incidents", "Private / residential"),
    "land_commercial": ("Commercial / Industrial Incidents", "Commercial / industrial"),
    "land_watercourse": ("Watercourse / Bank Incidents", "Watercourse / bank"),
    "land_other": ("Other (unidentified) Incidents", "Other land type (unidentified)"),
    "waste_animal": ("Animal Carcass Incidents", "Animal carcass"),
    "waste_green": ("Green Incidents", "Green"),
    "waste_vehicle": ("Vehicle Parts Incidents", "Vehicle parts"),
    "waste_white_goods": ("White Goods Incidents", "White goods"),
    "waste_electrical": ("Other Electrical Incidents", "Other electrical"),
    "waste_tyres": ("Tyres Incidents", "Tyres"),
    "waste_asbestos": ("Asbestos Incidents", "Asbestos"),
    "waste_clinical": ("Clinical Incidents", "Clinical"),
    "waste_cde": ("Constr / Demol / Excav Incidents", "Construction / demolition / excavation"),
    "waste_bags_commercial": ("Black Bags - Commercial Incidents", "Black bags - commercial"),
    "waste_bags_household": ("Black Bags - Household Incidents", "Black bags - household"),
    "waste_chemical": ("Chemical Drums, Oil, Fuel Incidents", "Chemical drums, oil, fuel"),
    "waste_other_household": ("Other Household Waste Incidents", "Other household"),
    "waste_other_commercial": ("Other Commercial Waste Incidents", "Other commercial waste"),
    "waste_other": ("Primary Waste Type Measures Other (unidentified) Incidents", "Other waste type (unidentified)"),
    "size_single_bag": ("Single Black Bag Incidents", "Single black bag"),
    "size_single_item": ("Single Item Incidents", "Single item"),
    "size_car_boot": ("Car Boot or Less Incidents", "Car boot or less"),
    "size_small_van": ("Small Van Load Incidents", "Small van load"),
    "size_transit_van": ("Transit Van Load Incidents", "Transit van load"),
    "size_tipper": ("Tipper Lorry Load Incidents", "Tipper lorry load"),
    "size_multi": ("Significant / Multi Loads Incidents", "Significant / multi loads"),
}
ACTIONS = {
    "actions_total": ("Total Actions", "Number of enforcement actions"),
    "actions_fpn": ("Total Fixed Penalty Notice Actions", "Fixed penalty notice"),
    "actions_prosecution": ("Prosecution Actions", "Prosecution"),
    "actions_warning": ("Warning Letter Actions", "Warning letter"),
    "actions_investigation": ("Investigation Actions", "Investigation"),
}


def _num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.astype(str).str.replace(",", "").str.strip(), errors="coerce")


def england() -> pd.DataFrame:
    inc = pd.read_csv(RAW / "Local_authority_flytipping_incidents_2012-13_to_2024-25.csv",
                      encoding="latin1", header=1)
    act = pd.read_csv(RAW / "Local_authority_flytipping_actions_2012-13_to_2024-25.csv",
                      encoding="latin1", header=1)
    inc.columns = inc.columns.str.strip()
    act.columns = act.columns.str.strip()
    inc = inc[inc["ONS Code"].str.match(r"^E0", na=False)]
    act = act[act["ONS Code"].str.match(r"^E0", na=False)]
    out = inc[["Year", "ONS Code", "Reporting basis"]].rename(
        columns={"ONS Code": "code", "Reporting basis": "reporting_basis"})
    for k, (col, _) in CATEGORIES.items():
        out[k] = _num(inc[col])
    out["cost_total"] = _num(inc["Total Incidents Clearance Costs (£)"])
    a = act[["Year", "ONS Code"]].rename(columns={"ONS Code": "code"})
    for k, (col, _) in ACTIONS.items():
        a[k] = _num(act[col])
    return out.merge(a, on=["Year", "code"], how="left")


def wales() -> pd.DataFrame:
    w = pd.read_csv(RAW / "wales_flytipping.csv")
    w = w[w["Area_reference"].str.startswith("W06")]
    w["value"] = _num(w["Data values"])
    labels = {**{v[1]: k for k, v in CATEGORIES.items()}}
    inc = w[w["Data description"].eq("Number of incidents") & w["Variable"].isin(labels)]
    # 'Tipper lorry load' etc. appear twice (incident sizes and a separate group);
    # keep the incidents-by-size hierarchy (62) or top-level rows.
    inc = inc[inc["Variable_hierarchy"].isna() | inc["Variable_hierarchy"].isin([60, 61, 62])]
    inc = inc.drop_duplicates(["Year", "Area_reference", "Variable"])
    wide = inc.pivot_table(index=["Year", "Area_reference"], columns="Variable",
                           values="value", aggfunc="first").rename(columns=labels)
    act_labels = {v[1]: k for k, v in ACTIONS.items()}
    act = w[w["Data description"].eq("Number of actions") & w["Variable"].isin(act_labels)]
    act = act.pivot_table(index=["Year", "Area_reference"], columns="Variable",
                          values="value", aggfunc="first").rename(columns=act_labels)
    cost = w[w["Data description"].eq("Clearance costs (£)") & w["Variable"].eq("Total recorded incidents")]
    cost = cost.set_index(["Year", "Area_reference"])["value"].rename("cost_total")
    out = wide.join(act).join(cost).reset_index().rename(columns={"Area_reference": "code"})
    out["reporting_basis"] = "Wales"
    return out


def build_panel() -> pd.DataFrame:
    df = pd.concat([england(), wales()], ignore_index=True)
    df["year"] = df["Year"].str[:4].astype(int)
    df = df[df["year"] >= 2012]
    lk = pd.read_csv(INTERIM / "lad_to_lad25.csv")
    df = df.merge(lk.rename(columns={"old_code": "code"}), on="code", how="left")
    assert df["LAD25CD"].notna().all(), df.loc[df["LAD25CD"].isna(), "code"].unique()
    value_cols = list(CATEGORIES) + ["cost_total"] + list(ACTIONS)
    # Successor councils are sums of their predecessors; a sum is missing if any part is
    g = df.groupby(["LAD25CD", "LAD25NM", "year"])
    panel = g[value_cols].sum(min_count=1)
    panel = panel.mask(g[value_cols].apply(lambda x: x.isna().any()))
    panel["n_predecessors"] = g.size()
    panel["reporting_basis"] = g["reporting_basis"].agg(
        lambda s: s.iloc[0] if s.nunique(dropna=False) == 1 else "Mixed (merged councils)")
    panel = panel.reset_index()
    panel["nation"] = np.where(panel["LAD25CD"].str[0] == "E", "England", "Wales")
    # Derived groupings used throughout the analysis
    panel["hh_waste"] = panel[["waste_bags_household", "waste_other_household"]].sum(axis=1, min_count=1)
    panel["commercial_waste"] = panel[["waste_bags_commercial", "waste_other_commercial"]].sum(axis=1, min_count=1)
    panel["large"] = panel[["size_tipper", "size_multi"]].sum(axis=1, min_count=1)
    panel["van"] = panel[["size_small_van", "size_transit_van"]].sum(axis=1, min_count=1)
    return panel


if __name__ == "__main__":
    p = build_panel()
    p.to_csv(INTERIM / "flytipping_panel.csv", index=False)
    print(p.shape, p.groupby("nation").LAD25CD.nunique().to_dict())
    print(p.groupby("year")["total"].agg(["count", "sum"]).to_string())
