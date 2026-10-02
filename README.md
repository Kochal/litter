# Fly-tipping, litter and access to waste facilities

Research project on what drives fly-tipping and littering in the UK, starting
with whether access to household waste recycling centres (HWRCs) and landfills
is related to recorded fly-tipping.

- [`DATASETS.md`](DATASETS.md): catalogue of UK data sources
- [`docs/research_brief.md`](docs/research_brief.md): literature review, hypotheses and designs
- [`docs/results.md`](docs/results.md): first results (council-level, England and Wales)

## Running the pipeline

Python 3.11 with `pandas geopandas pyogrio shapely pyproj scipy statsmodels pyfixest
openpyxl pyxlsb matplotlib requests`. Raw downloads go to `data/raw/` and
intermediate files to `data/interim/` (both gitignored, about 3 GB). Some
downloads are manual one-off `curl` calls; the URLs are listed below.

| Step | Script | Inputs |
|---|---|---|
| 1 | `src/geography.py` | ONS LSOA population-weighted centroids, LAD Dec 2025 boundaries (fetched) |
| 2 | `src/lad_lookup.py` | historic LAD boundaries (fetched); maps old council codes to 2025 |
| 3 | `src/flytipping.py` | Defra LA fly-tipping CSVs, StatsWales full download |
| 4 | `src/population.py` | ONS mid-year estimates detailed time series 2011 to 2025 |
| 5 | `src/facilities.py` | EA Waste Data Interrogator 2012 to 2025 (`data/raw/wdi2024/`, `data/raw/wdi_hist/`), NRW waste permits WFS |
| 6 | `src/census.py` | ONS Census 2021 API (fetched) |
| 7 | `src/accessibility.py` | OS Open Roads GeoPackage; LSOA drive times to HWRC, landfill, transfer |
| 8 | `src/access_panel.py` | yearly HWRC access by council (main and censored variants) |
| 9 | `src/finance.py` | MHCLG revenue outturn time series (RO5 street cleansing) |
| 10 | `src/build_analysis.py` | council-year analysis table (`data/analysis/`) |
| 11 | `src/models.py`, `src/figures.py` | `outputs/` |

Also needed in `data/interim/`: `lad25_hierarchy.csv` (ONS WD25 to LAD25,
CTYUA and region lookup) and `lad25_area.csv` (from the LAD boundaries); see the
commit history for the one-off commands.

Source URLs:

- Defra fly-tipping: <https://www.data.gov.uk/dataset/1388104c-3599-4cd2-abb5-ca8ddeeb4c9c/fly-tipping_in_england_>
- StatsWales fly-tipping: <https://stats.gov.wales/en-GB/1d891896-2866-4fe8-a6fd-90f7caea2a24> (POST the download form, unfiltered CSV)
- EA Waste Data Interrogator: data.gov.uk datasets "YYYY Waste Data Interrogator"
- NRW waste permits: `https://datamap.gov.wales/geoserver/ows` layer `geonode:nrw_waste_permits`
- OS Open Roads: <https://api.os.uk/downloads/v1/products/OpenRoads/downloads>
- ONS mid-year estimates: <https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates/datasets/estimatesofthepopulationforenglandandwales>
- MHCLG revenue outturn time series: <https://www.gov.uk/government/statistics/local-authority-revenue-expenditure-and-financing-england-revenue-outturn-multi-year-data-set>

## Licences

Contains Environment Agency information © Environment Agency and/or database
right. The Waste Data Interrogator is supplied under the Environment Agency
conditional licence, and some older extracts (e.g. 2016) add restrictions on
publishing because of personal data, so do not commit raw or site-level WDI data.
Contains OS data © Crown copyright and database right. Other sources are under
the Open Government Licence v3.0.
