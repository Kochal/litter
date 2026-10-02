"""Build a site-level table of permitted waste facilities in England from the
EA Waste Data Interrogator (wastes received), one row per permit."""
from pathlib import Path

import geopandas as gpd
import pandas as pd
from pyxlsb import open_workbook

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"

SITE_COLS = ["Facility RPA", "Facility WPA", "Facility District", "Permit", "Site Name",
             "Operator", "Permit Type", "Easting ", "Northing", "Post Code",
             "Site Category", "Facility Type"]


def read_received(path: Path) -> pd.DataFrame:
    with open_workbook(str(path)) as wb, wb.get_sheet(next(s for s in wb.sheets if s.endswith("Waste Received") and not s.startswith("Interrogator"))) as sh:
        rows = sh.rows()
        header = [c.v for c in next(rows)]
        data = [[c.v for c in r] for r in rows]
    df = pd.DataFrame(data, columns=header).dropna(how="all")
    return df


HWRC_NAME = (r"household (?:waste|recycling|reuse)|\bH ?W ?R ?C\b|\bH ?R ?C\b|civic amenity"
             r"|\bC ?A\b site|reuse (?:and|&) recycling centre|amenity site")
COUNCIL_OP = r"council|borough|county|city of|district|waste authority"
TRANSFER_TYPES = {"Non-Haz Waste Transfer", "Non Haz Waste Transfer / Treatment",
                  "Inert Waste Transfer / Treatment", "Inert Waste Transfer",
                  "Haz Waste Transfer", "Haz Waste Transfer / Treatment"}


def classify(sites: pd.DataFrame) -> pd.Series:
    """Label each site as hwrc, landfill, transfer (where traders can tip) or other.

    Most household waste recycling centres carry the EA facility type 'CA Site', but
    some are permitted as transfer stations, so names are matched as well."""
    name = sites["Site Name"].astype(str)
    op = sites["Operator"].astype(str)
    named_hwrc = (name.str.contains(HWRC_NAME, case=False, regex=True)
                  | (op.str.contains(COUNCIL_OP, case=False, regex=True)
                     & ~op.str.contains(r"\b(?:ltd|limited)\b", case=False, regex=True)
                     & name.str.contains(r"recycling centre|waste site|\btip\b", case=False, regex=True)))
    named_hwrc &= ~name.str.contains(r"water recycling|former", case=False, regex=True)
    hwrc = sites["Facility Type"].eq("CA Site") | named_hwrc
    landfill = sites["Site Category"].eq("Landfill") & ~hwrc
    transfer = sites["Facility Type"].isin(TRANSFER_TYPES) & ~hwrc
    return pd.Series(pd.NA, index=sites.index, dtype="object").mask(hwrc, "hwrc").mask(
        landfill, "landfill").mask(transfer, "transfer").fillna("other")


def build_sites(year: int = 2024) -> pd.DataFrame:
    xlsb = next((RAW / f"wdi{year}").glob("*Wastes Received*.xlsb"))
    df = read_received(xlsb)
    df["Tonnes Received"] = pd.to_numeric(df["Tonnes Received"], errors="coerce")
    df["Permit"] = df["Permit"].astype(str).str.replace(r"\.0$", "", regex=True)
    hh = df["Basic Waste Cat"].eq("Hhold/Ind/Com")
    df["tonnes_hic"] = df["Tonnes Received"].where(hh, 0)
    sites = (df.groupby(SITE_COLS, dropna=False)
               .agg(tonnes=("Tonnes Received", "sum"), tonnes_hic=("tonnes_hic", "sum"))
               .reset_index()
               .rename(columns={"Easting ": "easting", "Northing": "northing"}))
    sites["year"] = year
    sites["kind"] = classify(sites)
    return sites


HWA_ACTIVITY = r"^(?:A13a?|S0813):"
LANDFILL_ACTIVITY = r"^(?:A0[1-6]|L0\d):"
TRANSFER_ACTIVITY = r"transfer st|\bTS\b|WTS"


def wales_sites() -> pd.DataFrame:
    """Operational permitted waste sites in Wales (NRW), one row per permit, in the
    same layout as the English site table."""
    g = gpd.read_file(RAW / "nrw_waste_permits.json")
    # Many permits carry no operational status; drop only those known to be closed
    g = g[~g["operational_status"].isin(["Closed", "Pre-Operational"])]
    act = g["waste_activity"].fillna("")
    g = g.assign(is_hwa=act.str.contains(HWA_ACTIVITY, regex=True),
                 is_landfill=act.str.contains(LANDFILL_ACTIVITY, regex=True),
                 is_transfer=act.str.contains(TRANSFER_ACTIVITY, case=False, regex=True))
    per = g.groupby("permit_number").agg(
        site_name=("site_name", "first"), operator=("operator", "first"),
        district=("local_aurthority", "first"), postcode=("site_postcode", "first"),
        activity=("waste_activity", "first"), easting=("geometry", lambda x: x.iloc[0].x),
        northing=("geometry", lambda x: x.iloc[0].y), is_hwa=("is_hwa", "any"),
        is_landfill=("is_landfill", "any"), is_transfer=("is_transfer", "any")).reset_index()
    out = pd.DataFrame({
        "Facility RPA": "Wales", "Facility WPA": per["district"], "Facility District": per["district"],
        "Permit": per["permit_number"], "Site Name": per["site_name"], "Operator": per["operator"],
        "Permit Type": per["activity"], "easting": per["easting"], "northing": per["northing"],
        "Post Code": per["postcode"], "Site Category": "", "Facility Type": "",
        "tonnes": float("nan"), "tonnes_hic": float("nan"), "year": 2025})
    # Reuse the English name rules, then let the NRW activity codes take precedence
    kind = classify(out)
    kind = kind.mask(per["is_transfer"].values & kind.eq("other"), "transfer")
    kind = kind.mask(per["is_landfill"].values, "landfill")
    out["kind"] = kind.mask(per["is_hwa"].values, "hwrc")
    return out


def hwrc_layer(sites: pd.DataFrame) -> pd.DataFrame:
    """One row per physical HWRC. A site can hold several permits or permit types
    (e.g. a CA site plus a transfer station on the same plot), so collapse by
    permit and then by location."""
    h = sites[sites["kind"] == "hwrc"].sort_values("tonnes", ascending=False)
    agg = {"Site Name": "first", "Operator": "first", "Facility District": "first",
           "Facility WPA": "first", "Post Code": "first", "easting": "first",
           "northing": "first", "tonnes": "sum", "tonnes_hic": "sum"}
    h = h.groupby("Permit", as_index=False).agg(agg)
    return h.groupby(["easting", "northing"], as_index=False).agg(
        {**{k: v for k, v in agg.items() if k not in ("easting", "northing")}, "Permit": "first"})


if __name__ == "__main__":
    INTERIM.mkdir(parents=True, exist_ok=True)
    s = build_sites()
    s.to_csv(INTERIM / "wdi2024_sites.csv", index=False)
    w = wales_sites()
    w.to_csv(INTERIM / "wales_sites.csv", index=False)
    print("Wales:", w["kind"].value_counts().to_dict())
    print(s.shape)
    print(s["kind"].value_counts().to_string())
    h = hwrc_layer(s)
    h.to_csv(INTERIM / "hwrc_england_2024.csv", index=False)
    hw = hwrc_layer(w)
    pd.concat([h.assign(nation="England"), hw.assign(nation="Wales")]).to_csv(
        INTERIM / "hwrc_all.csv", index=False)
    print("distinct HWRCs: England", len(h), "Wales", len(hw))
