"""Build a site-level table of permitted waste facilities in England from the
EA Waste Data Interrogator (wastes received), one row per permit."""
import re
from pathlib import Path

import geopandas as gpd
import pandas as pd
import openpyxl
from pyxlsb import open_workbook

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"

SITE_COLS = ["Facility RPA", "Facility WPA", "Facility District", "Permit", "Site Name",
             "Operator", "Permit Type", "Easting ", "Northing", "Post Code",
             "Site Category", "Facility Type"]


# Column names used by the 2016 extract, mapped to the 2024 layout
ALIASES = {
    "fomer planning region of facility": "Facility RPA",
    "waste planning authority of facility": "Facility WPA",
    "local authority of facility": "Facility District",
    "permit reference": "Permit",
    "facility name": "Site Name",
    "facility postcode": "Post Code",
    "basic waste category": "Basic Waste Cat",
    "site type": "Facility Type",
}


def _rows(path: Path):
    """Yield raw rows from the 'waste received' sheet of a WDI workbook (.xlsb or .xlsx)."""
    if path.suffix == ".xlsb":
        with open_workbook(str(path)) as wb:
            name = next(s for s in wb.sheets if s.lower().endswith("waste received")
                        and not s.lower().startswith("interrogator"))
            with wb.get_sheet(name) as sh:
                for r in sh.rows():
                    yield [c.v for c in r]
    else:
        wb = openpyxl.load_workbook(path, read_only=True)
        name = next(s for s in wb.sheetnames if "received" in s.lower())
        yield from (list(r) for r in wb[name].iter_rows(values_only=True))


def read_received(path: Path) -> pd.DataFrame:
    rows = _rows(path)
    for header in rows:  # older extracts have a preamble above the header row
        names = {str(h).strip().lower() for h in header or [] if h}
        if "easting" in names and names & {"site name", "facility name"}:
            break
    # Normalise case so every year matches the 2024 layout
    canon = {c.lower(): c for c in SITE_COLS + ["Easting", "Basic Waste Cat", "Tonnes Received", "SitePC"]}
    canon.update(ALIASES)
    header = [canon.get(str(h).strip().lower(), str(h).strip()) if h is not None else "" for h in header]
    # Some extracts pad the sheet with thousands of empty 'ColumnN' fields
    keep = [i for i, h in enumerate(header)
            if h and not re.fullmatch(r"Column\d+", h) and h not in header[:i]]
    df = pd.DataFrame([[r[i] if i < len(r) else None for i in keep] for r in rows],
                      columns=[header[i] for i in keep]).dropna(how="all")
    return df.rename(columns={"SitePC": "Post Code", "Easting": "Easting "})


def wdi_path(year: int) -> Path:
    if year == 2024:
        return next((RAW / "wdi2024").glob("*Wastes Received*.xlsb"))
    hist = RAW / "wdi_hist"
    found = list((hist / str(year)).glob("*.xlsb")) + list(hist.glob(f"{year}.xlsx"))
    return found[0]


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
    df = read_received(wdi_path(year))
    df["Tonnes Received"] = pd.to_numeric(df["Tonnes Received"], errors="coerce")
    # Early years write permits as 'EPR number (licence number)'; keep the first token
    df["Permit"] = (df["Permit"].astype(str).str.replace(r"\.0$", "", regex=True)
                    .str.split(" ").str[0])
    for c in SITE_COLS:
        if c not in df:
            df[c] = None
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


def build_history(years=range(2012, 2024)) -> pd.DataFrame:
    """HWRC layer for each earlier WDI year, for the panel of access over time."""
    out = []
    for y in years:
        cache = INTERIM / f"hwrc_england_{y}.csv"
        if not cache.exists():
            hwrc_layer(build_sites(y)).assign(year=y).to_csv(cache, index=False)
        h = pd.read_csv(cache)
        print(y, len(h))
        out.append(h)
    return pd.concat(out)


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
