# Datasets: UK litter / fly-tipping vs. access to waste facilities

Research question: do areas with poorer access to landfill sites and household
waste recycling centres (HWRCs) experience more fly-tipping and litter?

Coverage key: **E** England, **W** Wales, **S** Scotland, **NI** Northern Ireland.
Unless noted, government data is under the Open Government Licence (OGL v3).

---

## 1. Fly-tipping and litter (outcome variables)

### Official fly-tipping statistics

| Dataset | Coverage | Granularity | Period | Access |
|---|---|---|---|---|
| Defra, *Fly-tipping in England* (incidents and enforcement actions per local authority, broken down by waste type, size and land type) | E | Local authority (district / unitary), annual | 2012/13 to 2024/25 | CSV: <https://www.data.gov.uk/dataset/1388104c-3599-4cd2-abb5-ca8ddeeb4c9c/fly-tipping_in_england_> ; release: <https://www.gov.uk/government/statistics/fly-tipping-in-england> |
| Welsh Government, *Local authority recorded fly-tipping* (by LA, land type, waste type, size) | W | Local authority, annual | 2007/08 onward | StatsWales: <https://statswales.gov.wales/Catalogue/Environment-and-Countryside/Fly-tipping/recordedflytippingincidents-by-localauthority> ; release: <https://www.gov.wales/local-authority-recorded-fly-tipping-april-2024-march-2025> |
| Scotland: WasteDataFlow fly-tipping returns, collated by Keep Scotland Beautiful for Zero Waste Scotland | S | Local authority, annual | Patchy | No routine open table. Request from Zero Waste Scotland / KSB; context at <https://www.gov.scot/policies/managing-waste/litter-and-flytipping/> |
| Northern Ireland | NI | None published | n/a | No routine statistics. NIEA illegal waste site investigations and individual council figures only (FOI to councils if needed) |

Notes:
- England and Wales both come from **WasteDataFlow** returns, so definitions are
  comparable. Scotland and NI are not directly comparable; most studies restrict
  to E+W.
- These only count incidents on public land reported to councils. Private-land
  fly-tipping is largely missing, and recording effort differs by council
  (a council that tries harder records more). Control for this (e.g. LA fixed
  effects, or enforcement actions as a proxy for effort).
- ~300 English + 22 Welsh LAs gives a modest sample. For a finer spatial unit
  you need point data (below).

### Point-level fly-tipping reports (for LSOA / grid analysis)

| Dataset | Coverage | Notes |
|---|---|---|
| **FixMyStreet** (mySociety) | UK | Citizen reports with lat/long and category (fly-tipping is one of the largest). Browse at <https://www.fixmystreet.com/reports>; per-council RSS/Open311 feeds. mySociety has released multi-year report-location data for research (contact mySociety for bulk access). Reporting bias towards digitally engaged areas. |
| Individual council open data | Varies | Several councils publish incident-level fly-tipping/street cleansing requests (search data.gov.uk for "fly tipping", plus portals such as London Datastore, Camden, Leeds, Birmingham). Good for city-level case studies. |
| Council incident-level open data with locations | York, Leeds, Bradford, Calderdale, Bassetlaw | York (by neighbourhood): <https://data.yorkopendata.org/dataset/fly-tipping-all-incidents>; Leeds environmental service requests (by ward): <https://datamillnorth.org/dataset/environmental-service-requests-e61k0>; Bradford: <https://datahub.bradford.gov.uk/datasets/street-cleansing/bradford-fly-tipping>; Calderdale: <https://dataworks.calderdale.gov.uk/dataset/2w73y/fly-tipping>; Bassetlaw: <https://data.bassetlaw.gov.uk/fly-tipping/>. Barnsley has released ward data under FOI. Council-recorded, so not limited to public reports; used in `src/council_records.py` (York, Bassetlaw, Bradford, Leeds; Calderdale publishes only totals). Bassetlaw: monthly files 2011 to 2017 with coordinates and waste type, <https://data.bassetlaw.gov.uk/fly-tipping/>. |
| Council incident points on ArcGIS Online (public map layers, no stated licence) | Newham, Epping Forest, Darlington, Wolverhampton, Stratford-on-Avon, Kingston upon Thames, West Oxfordshire, Cotswold | Found by searching ArcGIS Online for fly-tipping layers; layer addresses in `src/council_layers.py` and `data/council_layers_monthly.json`. Some layers include staff names and addresses: only date, point, waste type, land type and size are downloaded. Used in `src/council_records.py`. |
| mySociety FixMyStreet geographic dataset | UK | Aggregated FixMyStreet reports by area: <https://data.mysociety.org/datasets/fms-geographic/>. |
| FOI requests to councils | E/W | Councils hold incident-level location data from their WasteDataFlow returns. Feasible for a targeted sample of LAs. |

### Related work: IECR fly-tipping map (October 2026)

The Institute for Environmental and Civic Research published *Mapping fly-tipping
in England* on 2 October 2026: <https://iecr.org.uk/research/fly-tipping-map/>.
It shares each council's Defra total across its 33,755 neighbourhoods with a model
trained on FixMyStreet reports (allowing for how readily residents report) and on
the six councils' incident records above, and adds an estimate of fly-tipping on
farms (about 108,000 incidents in 2024/25). Its access findings agree with ours:
within councils, drive distance to the nearest recycling centre shows no
association (1.02 per standard deviation), while crowding at the nearest centre
(households per opening hour) goes with about 17% more; between councils, no car
(1.21), private renting (1.16) and residents who moved in (1.10) go with more
recorded fly-tipping. The neighbourhood figures are model estimates, not counts,
so they should not be used as an outcome in our models; their method and source
list are a useful reference.

### Litter

| Dataset | Coverage | Granularity | Access |
|---|---|---|---|
| **OpenLitterMap** | Global incl. UK | Point (lat/long, item type, brand, timestamp) | Free CSV, no restriction: `https://openlittermap.com/maps/United Kingdom/download` (also city/region levels); QGIS plugin: <https://plugins.qgis.org/plugins/openlittermap/> |
| Keep Scotland Beautiful **LEAMS** (Local Environmental Audit and Management System) | S | Survey of random street transects per LA, annual; litter and LEQ scores | Dashboard and reports: <https://www.keepscotlandbeautiful.org/local-environmental-audit-and-management-system-leams/> ; site-level data on request |
| Keep Wales Tidy LEAMS / *How clean are our streets?* | W | LA-level cleanliness indicators | Annual reports; data on request |
| Keep Britain Tidy *Local Environmental Quality Survey of England* | E | National sample survey | Reports only; microdata on request |
| Marine Conservation Society **Beachwatch / Great British Beach Clean** | UK coast | Per-beach item counts per 100 m | Dashboard + reports: <https://www.mcsuk.org/what-you-can-do/beach-clean/beachwatch-reports/> (coastal only, less relevant for HWRC access) |

---

## 2. Landfill sites and recycling centres (exposure variables)

Important distinction: households cannot use landfills directly. For household
fly-tipping, the relevant facility is the **HWRC** ("the tip"). Landfills,
transfer stations and commercial sites matter more for trade waste fly-tipping
(e.g. tipper-lorry-sized incidents).

| Dataset | Coverage | Content | Access |
|---|---|---|---|
| EA **Permitted Waste Sites: Authorised Landfill Site Boundaries** | E | Polygons of currently permitted landfills, updated daily | <https://environment.data.gov.uk/dataset/692eaecf-d465-11e4-ac2e-f0def148f590> (SHP/GPKG/GeoJSON, WFS, OGC API) |
| EA **Historic Landfill Sites** | E | Closed landfills (useful for history, not access) | <https://environment.data.gov.uk/dataset/7a955570-d465-11e4-a37c-f0def148f590> |
| EA **Waste Data Interrogator** (annual) | E | ~6,000 permitted waste sites with site type (incl. "Household, Commercial & Industrial Waste Transfer Station", "Civic Amenity Site" = HWRC), grid reference, tonnages in/out | 2024: <https://environment.data.gov.uk/dataset/a6dc56e6-fdbd-4f06-b8bc-f358cb1ec471> ; earlier years also on data.gov.uk. **Best single national source for HWRC locations in England** (filter facility type to civic amenity / HWRC). |
| EA public register of environmental permits (waste operations) | E | All permitted waste operations with location | <https://environment.data.gov.uk/public-register> |
| NRW **Waste Permit Returns Data Interrogator** + permitted waste sites | W | Site-level returns and locations | <https://metadata.naturalresources.wales/geonetwork/srv/api/records/NRW_DS116336?language=eng> ; DataMapWales |
| SEPA **Waste sites and capacity** / **Landfill sites and capacity** tools | S | All licensed waste sites and landfills, tonnages, capacity, locations | <https://www.sepa.org.uk/environment/waste/waste-data/waste-data-reporting/waste-site-information/> |
| NIEA public register of waste management licences | NI | Licensed sites | DAERA public registers; HWRC lists on council sites |
| **OpenStreetMap** | UK | `amenity=recycling` + `recycling_type=centre` (HWRCs), `recycling_type=container` (bring banks), `amenity=waste_transfer_station`, `landuse=landfill`. Includes opening hours for some sites | Geofabrik GB extract: <https://download.geofabrik.de/europe/united-kingdom.html> ; or Overpass API. Consistent UK-wide, but check completeness against EA/SEPA lists. |
| Council open data on HWRCs | Varies | Name, address, coordinates, sometimes opening hours/booking rules | e.g. North London: <https://www.data.gov.uk/dataset/fa887a22-f0b4-4ccc-8d76-f63b2b6543c7/north-london-household-waste-recycling-centres2>, Sheffield, Calderdale, North Yorkshire, Durham (search data.gov.uk "household waste recycling centres") |

Useful HWRC attributes worth collecting beyond location (they likely matter as
much as distance): opening hours/days, booking requirement (introduced widely
since 2020), charges for DIY/rubble waste, van/trailer permit restrictions,
residency checks. These mostly need scraping council websites or FOI.

---

## 3. Road network (to compute travel time/distance)

| Dataset | Coverage | Notes | Access |
|---|---|---|---|
| **OS Open Roads** | GB (not NI) | Topologically connected road links with road class, form; ideal for network analysis | <https://osdatahub.os.uk/downloads/open/OpenRoads> |
| **OpenStreetMap** | UK incl. NI | Roads with speed limits, access restrictions; works directly with routing engines | Geofabrik extract (above) |
| OS MasterMap Highways Network | GB | Speeds, restrictions, routing info; licensed (free to public sector / academics via PSGA / Digimap) | OS / EDINA Digimap |
| OSNI Open Data | NI | Transport / road layers if not using OSM | <https://www.spatialni.gov.uk> |
| DfT **road traffic statistics** (AADF counts) | GB | Traffic volumes, optional covariate for roadside litter | <https://roadtraffic.dft.gov.uk/downloads> |
| DfT **Journey Time Statistics** | E | Pre-computed LSOA travel times to key services (not HWRCs), useful as a template/validation of method | <https://www.gov.uk/government/collections/journey-times-to-key-services> |

Routing tools: OSRM / Valhalla / GraphHopper (car travel time from OSM),
`r5r` (R) or `r5py` (Python) for multimodal, `pgRouting`, or `osmnx` +
`networkx` for smaller areas. Compute drive time from each LSOA / data zone
population-weighted centroid (or each 1 km grid cell) to the nearest HWRC,
plus a gravity/2SFCA-style accessibility score if you want to account for
facility capacity (tonnage from the Waste Data Interrogator).

---

## 4. Population density and small-area geography

| Dataset | Coverage | Granularity | Access |
|---|---|---|---|
| ONS **Census 2021 TS006 Population density** | E+W | OA / LSOA / MSOA / LA | Nomis: <https://www.nomisweb.co.uk/sources/census_2021_bulk> |
| ONS mid-year population estimates (small area) | E+W | LSOA, annual (to match fly-tipping years) | <https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates> |
| NRS **Scotland's Census 2022** and small area population estimates | S | Output area / Data Zone | <https://www.scotlandscensus.gov.uk> ; <https://www.nrscotland.gov.uk> |
| NISRA **Census 2021** | NI | Data Zone / Super Data Zone | <https://www.nisra.gov.uk/statistics/census> |
| **UKCEH UK gridded population 2021** (residential and workday) | UK | 1 km grid, consistent across all four nations | <https://catalogue.ceh.ac.uk/documents/7beefde9-c520-4ddf-897a-0167e8918595> ; data.gov.uk: <https://www.data.gov.uk/dataset/076cef76-337c-4e5f-8123-ef660e53a836> |
| WorldPop / GHSL / Meta High Resolution Settlement Layer | UK | 100 m / 30 m grids | <https://hub.worldpop.org> ; <https://ghsl.jrc.ec.europa.eu> |
| ONS **Open Geography Portal** | UK | Boundaries (LA, LSOA, OA), population-weighted centroids, lookups, rural/urban classification | <https://geoportal.statistics.gov.uk> |

The population-weighted centroids from the Open Geography Portal are the
standard origin points for travel-time calculations.

---

## 5. Recommended confounders

Fly-tipping correlates strongly with deprivation, housing tenure and urban
density, so a raw access-vs-fly-tipping correlation will be confounded.

| Dataset | Access |
|---|---|
| English Indices of Deprivation 2025 (LSOA) | <https://www.gov.uk/government/statistics/english-indices-of-deprivation-2025> |
| Welsh (WIMD), Scottish (SIMD) and NI (NIMDM) deprivation indices | gov.wales, gov.scot, nisra.gov.uk |
| Census 2021 tenure (TS054), car availability (TS045), household composition | Nomis (as above) |
| Census 2011 tenure (KS402EW) and car availability (KS404EW), by local authority | Nomis API (datasets NM_619_1 and NM_621_1), used in `src/composition_change.py` to measure 2011 to 2021 change |
| ONS consumer prices index, all items (D7BT), annual | <https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/d7bt/mm23>; saved as `data/cpi_ons_d7bt.csv`, used to put street-cleaning spending in 2024/25 prices |
| Rural-Urban Classification | ONS Open Geography Portal |
| Council waste service data (bulky waste collection charges, collection frequency) | Councils / WasteDataFlow (<https://www.wastedataflow.org>) |

---

## Suggested analysis pipeline

1. **Unit of analysis**: start with local authority (official stats, E+W, 2012/13 to
   2024/25 panel). Move to LSOA / 1 km grid with point data (FixMyStreet,
   OpenLitterMap, council data) for finer analysis.
2. **Facilities**: build an HWRC layer from the EA Waste Data Interrogator
   (civic amenity sites) + NRW + SEPA, cross-checked with OSM. Keep landfills /
   transfer stations as a separate layer.
3. **Accessibility**: drive time from population-weighted centroids to nearest
   HWRC over OS Open Roads / OSM; aggregate to LA as a population-weighted mean.
4. **Model**: negative binomial / Poisson count model of incidents with
   population offset, controlling for deprivation, density, tenure, car
   availability, and LA reporting effort; year fixed effects for the panel.
   Event-study designs around HWRC closures or booking-system introductions
   give stronger causal evidence than cross-sectional correlation.
