# What drives fly-tipping? First results

Council-level analysis of recorded fly-tipping in England and Wales, 2012/13 to
2024/25, guided by the hypotheses in [`research_brief.md`](research_brief.md).
Code is in `src/` (see the [README](../README.md)); estimates are in
`outputs/model_results.csv` and `outputs/event_study.csv`.

## Summary

1. **Access to household waste recycling centres (HWRCs) shows no reliable link
   to recorded fly-tipping.** Across councils, once housing and deprivation are
   accounted for, a council whose residents live 5 minutes further from their
   nearest HWRC has essentially the same fly-tipping rate (all incidents: rate
   ratio 1.07, 95% CI 0.89 to 1.30; bulky household waste: 1.01, 0.84 to 1.21).
   Within councils over time, estimates swing in sign between periods and the
   placebo waste types move too, so they cannot be read as causal in either
   direction.
2. **Housing is the strongest correlate, and it matches the type of waste.**
   Each extra 10 percentage points of households renting privately goes with
   about 80% more bulky household fly-tips (1.80, 1.24 to 2.62) and about twice
   as many household black-bag fly-tips (2.07, 1.17 to 3.65). Student share is
   also linked to black bags (1.60 per 5 points, 1.10 to 2.33). This fits the
   brief's tenant-turnover and communal-bin explanations.
3. **Deprivation goes with more fly-tipping overall** (1.29 per 5 points of
   households deprived in 2+ dimensions, 1.03 to 1.60), and car-less households
   with more construction and tipper-sized incidents.
4. **The raw pattern is the opposite of the access hypothesis.** Without
   covariates, councils further from HWRCs record *less* fly-tipping (0.74 per
   5 min, 0.60 to 0.92), most likely because remote councils are rural, and rural
   councils record less (more private land, less proactive cleansing). Landfill drive time keeps a negative association even with
   covariates, which most likely reflects the same rurality and recording effects.
5. **The main limits are measurement:** official counts reflect council
   recording effort as much as dumping, and site disappearances in the Environment
   Agency returns are not reliable evidence of closure (see Data quality).

## Data and design

- **Outcome:** incidents reported by councils to WasteDataFlow (Defra for England,
  StatsWales for Wales), harmonised to December 2025 council boundaries: 318
  councils, 13 years. Split by waste type, size and land type (groupings in
  `src/build_analysis.py`).
- **HWRC access:** drive time from each of 35,672 neighbourhood (LSOA)
  population-weighted centroids to the nearest HWRC over OS Open Roads, using
  nominal free-flow speeds by road class, then population-weighted per council.
  English HWRCs come from each year's EA Waste Data Interrogator (705 sites in
  2012, about 659 in 2024) and Welsh ones from the current NRW permit register.
  Times are a consistent relative measure, not realistic journey times (no
  congestion; median about 6 minutes).
- **Covariates:** Census 2021 tenure, car availability, flats, students and
  household deprivation; ONS mid-year population and migration churn; population
  density; drive time to the nearest landfill and waste transfer station; council
  recording basis (all incidents vs public-reported only); street cleansing
  spending (MHCLG revenue outturn, 2017/18 onward).
- **Models:** Poisson pseudo-maximum likelihood with a log-population offset,
  so coefficients are rate ratios. Standard errors are clustered by waste disposal
  authority (county in two-tier areas, joint authorities in Greater Manchester,
  Merseyside and London).
  - *Between councils:* 2022/23 to 2024/25 pooled, with region and year effects
    (950 council-years).
  - *Within councils:* England 2012/13 to 2024/25, with council fixed effects and
    region-by-year effects, so fixed council traits and national shocks (landfill
    tax, fixed penalty reforms, Covid) are absorbed (about 3,800 council-years).
  - *Event study:* 30 councils whose average drive time first rose by at least a
    minute in one year, against councils whose access never moved by more than
    half a minute.
  - *Placebo outcome:* animal carcasses, clinical waste and vehicle parts, which
    HWRC access should not affect.

## Results

### Which councils have more fly-tipping?

![Between-council rate ratios](../outputs/fig_between.png)

All coefficients come from one model per outcome, so each is net of the others.
Key estimates (rate ratio, 95% CI):

| Driver | All incidents | Bulky household | Household black bags | Construction / demolition | Placebo |
|---|---|---|---|---|---|
| HWRC drive time (+5 min) | 1.07 (0.89 to 1.30) | 1.01 (0.84 to 1.21) | 1.03 (0.71 to 1.50) | 0.97 (0.75 to 1.24) | 0.91 (0.63 to 1.31) |
| Private renting (+10 pts) | 1.18 (0.82 to 1.71) | **1.80 (1.24 to 2.62)** | **2.07 (1.17 to 3.65)** | 1.13 (0.64 to 2.00) | 1.04 (0.55 to 1.98) |
| Students (+5 pts) | 1.19 (1.00 to 1.43) | 1.17 (0.95 to 1.44) | **1.60 (1.10 to 2.33)** | 0.83 (0.60 to 1.15) | 1.18 (0.77 to 1.81) |
| Deprived households (+5 pts) | **1.29 (1.03 to 1.60)** | 1.10 (0.77 to 1.56) | 1.06 (0.78 to 1.44) | 0.95 (0.56 to 1.62) | 1.52 (0.98 to 2.37) |
| No car (+10 pts) | 1.28 (0.93 to 1.76) | 1.22 (0.76 to 1.96) | 0.87 (0.49 to 1.53) | **2.15 (1.16 to 3.97)** | 1.09 (0.59 to 2.04) |
| Landfill drive time (+10 min) | **0.84 (0.75 to 0.94)** | **0.79 (0.69 to 0.90)** | **0.67 (0.55 to 0.82)** | **0.80 (0.69 to 0.92)** | 0.93 (0.74 to 1.16) |

Bold: 95% CI excludes 1.

Reading the pattern:

- **Housing tracks waste type.** Private renting and students line up with
  household black bags and bulky household items, which is what end-of-tenancy
  clear-outs and communal bins would produce. They do not predict
  construction or placebo waste. Migration churn turns negative once tenure and
  students are in the model. It overlaps heavily with both, so it should not be
  read on its own.
- **HWRC access is flat across every outcome**, including the bulky
  household items people would take to an HWRC, and the confidence intervals rule
  out large effects (more than about +30% per 5 minutes).
- **Landfill distance** is negative for every household outcome but not the
  placebo, the reverse of what a "too far to dump legally" story predicts. The
  likely reason is that landfills sit in rural areas, where councils record less
  (more private land, less proactive cleansing).

### Does fly-tipping change when HWRC access changes?

![Within-council estimates across specifications](../outputs/fig_within_specs.png)

Within councils the estimates are imprecise and unstable:

| Specification | All incidents | Bulky household | Placebo |
|---|---|---|---|
| Main, 2012/13 to 2024/25 | 0.96 (0.65 to 1.42) | 0.82 (0.55 to 1.21) | 1.37 (0.96 to 1.97) |
| 2012/13 to 2019/20 only | 1.40 (0.97 to 2.02) | 1.17 (0.81 to 1.69) | **1.60 (1.07 to 2.40)** |
| 2017/18 on, with street cleansing spend | 0.61 (0.33 to 1.12) | 0.54 (0.27 to 1.06) | 1.38 (0.71 to 2.70) |

The event study tells the same story differently: recorded fly-tipping in the 30
"worsening" councils is about 20% lower in the years after access drops, with
flat pre-trends, but the placebo series is also below 1.

![Event study](../outputs/fig_event_study.png)

**Interpretation.** A genuine behavioural response to HWRC access should raise
bulky household fly-tipping and leave the placebo flat. Instead the sign flips
between periods, the placebo responds about as much as the target outcomes, and
tipper-lorry incidents (which HWRCs cannot take) show the largest "effects". The
within-council variation is therefore picking up something other than dumping
behaviour: changes in council recording or service levels that coincide with
site changes, and noise in the site data (below). Controlling for street cleansing
spending changes nothing, so cleansing budgets are not the whole story. The
honest conclusion is that this panel cannot identify the causal effect of HWRC
access; it can only say that large effects are not visible.

## Data quality issues found

1. **Sites vanishing from EA returns are not closures.** Both Trafford HWRCs
   (Chester Road and Woodhouse Lane) are missing from the 2023 to 2025 Waste
   Data Interrogator but are open
   ([Recycle for Greater Manchester](https://recycleforgreatermanchester.com/recycling-in-your-area/trafford/)).
   Gaps between appearances are filled, and a sensitivity check treats sites
   last seen from 2021 as still open, but the yearly HWRC list remains noisy.
   This biases within-council estimates towards zero and adds spurious events.
2. **Recording effort.** Councils that record "all incidents" against
   "public-reported only" are flagged, but effort also varies within each group.
   Rural councils appear to record less, which would explain the negative
   raw association between remoteness and fly-tipping.
3. **Wales** has no HWRC history (current NRW register only), so Welsh councils
   contribute to the between-council model only. Newport has no HWRC in the NRW
   permit data.
4. **DIY charges, booking systems and opening hours** (the brief's H2 and the
   strongest natural experiment, the England DIY-charge ban from 31 December 2023)
   are not in any public dataset found, so are untested.

## Neighbourhood analysis with FixMyStreet reports

### What the data is and how it was used

FixMyStreet is a website and app run by the charity mySociety where members of the
public report street problems, which are passed to the council. Each report has a
location, a date and a category chosen by the council (for example "Flytipping",
"Fly-tip Small - Less than one bag", "Dumped rubbish"). We downloaded every report
in 48 fly-tipping categories and 26 litter categories through mySociety's public
Open311 interface (2012 to October 2025), and placed each report in its
neighbourhood. A neighbourhood here is an ONS Lower Layer Super Output Area
(LSOA): a small area of about 1,500 to 1,700 residents. There are 35,672 in
England and Wales.

| Step | Fly-tipping reports |
|---|---|
| Downloaded | 915,941 |
| Inside England and Wales | 904,027 |
| In complete years 2012 to 2024 | 721,733 |
| In council-years with at least 50 reports (used in the models) | 674,572 |

The 50-report threshold drops council-years where FixMyStreet is barely used,
because comparing neighbourhoods needs enough reports to compare. The models use
183,799 neighbourhood-years from 27,056 neighbourhoods in 212 councils. Litter
reports are much rarer: 66,416 reports in 22 councils, so litter results are less
reliable.

**How FixMyStreet compares with official counts.** In a typical council-year,
FixMyStreet reports equal about 5% of the incidents the council records
officially (middle half of council-years: 2% to 12%; 1,278 council-years with 50
or more reports). In 2024, 118,560 FixMyStreet reports compare with 1,305,724
official incidents. The two only loosely agree (correlation of 0.38 between their
logarithms), so FixMyStreet is a partial view: it captures what members of the
public choose to report through this one channel.

**The comparison.** For each council and year separately, we compared its
neighbourhoods with each other: do neighbourhoods further from a recycling centre
report more fly-tipping per resident than neighbourhoods closer by, when their
housing is similar? Comparing only within a council and year removes everything
that differs between councils or years, including how much a council uses
FixMyStreet and how it records incidents. That was the main weakness of the
council-level analysis.

The drivers in these models, all measured per neighbourhood:

- **Drive time to the nearest recycling centre**, in minutes, as in the council
  analysis, for each year.
- **Private renting**: the share of households renting from a private landlord or
  letting agency (Census 2021).
- **No car**: the share of households without a car or van (Census 2021).
- **Population density**: residents per square kilometre.
- **Rural**: whether ONS classes the neighbourhood as rural rather than urban.

Results are rate ratios: 1.20 means 20% more reports per resident; 0.80 means 20%
fewer; 1 means no difference.

### Results

**1. Within the same council and year, neighbourhoods further from a recycling
centre do not report more fly-tipping.** A neighbourhood 5 minutes further away
has a rate ratio of 0.93 (95% confidence interval 0.81 to 1.07), allowing for
housing and car ownership. Looking at distance bands rather than a straight line,
neighbourhoods 20 minutes or more away report fewer fly-tipping incidents than
those under 5 minutes away (0.67, 0.48 to 0.93), not more.

**2. Private renting and car-less households are linked to more fly-tipping, as
in the council analysis.** Each extra 10 percentage points of households renting
privately goes with 15% more fly-tipping reports (1.15, 1.07 to 1.24). Each extra
10 points of households without a car goes with 23% more (1.23, 1.11 to 1.36).
The same two drivers are linked to litter reports (1.13 and 1.21 per 10 points).

**3. Rural neighbourhoods report about as much fly-tipping per resident as urban
ones in the same council** (1.14, 0.81 to 1.60). In the official council data,
councils further from recycling centres, which are mostly rural, record less
fly-tipping. Comparing neighbourhoods within councils, that difference does not
appear, which supports the view that the council-level pattern reflects how
councils record incidents rather than less dumping in rural areas. Litter reports,
in contrast, are 43% lower in rural neighbourhoods (0.57, 0.46 to 0.71).

Reports per 1,000 residents per year, in council-years where FixMyStreet is in
active use:

| Area | Drive time to centre | Neighbourhood-years | Neighbourhoods | Fly-tipping | Litter |
|---|---|---|---|---|---|
| Rural | under 5 min | 2,565 | 473 | 1.16 | 0.04 |
| Rural | 5 to 10 min | 9,179 | 1,578 | 1.73 | 0.05 |
| Rural | 10 to 15 min | 7,843 | 1,426 | 1.84 | 0.04 |
| Rural | 15 to 20 min | 2,929 | 551 | 1.41 | 0.05 |
| Rural | 20 min or more | 1,304 | 260 | 1.35 | 0.08 |
| Urban | under 5 min | 62,664 | 9,368 | 1.88 | 0.07 |
| Urban | 5 to 10 min | 83,680 | 12,571 | 2.70 | 0.19 |
| Urban | 10 to 15 min | 10,606 | 2,008 | 1.31 | 0.08 |
| Urban | 15 to 20 min | 2,183 | 387 | 0.96 | 0.00 |
| Urban | 20 min or more | 846 | 165 | 0.55 | 0.01 |

These raw rates mix different councils together; the model results above compare
neighbourhoods within the same council and year.

**4. When the same neighbourhood loses its nearest recycling centre, its
fly-tipping reports rise, but the evidence is not conclusive.** Following each
neighbourhood over the years, a 5-minute increase in its drive time (from a
closure) goes with 21% more fly-tipping reports (1.21, 1.03 to 1.44). This
comparison removes everything fixed about the neighbourhood. It rests on the
2,322 neighbourhoods whose drive time changed by at least a minute (1,264 by 3
minutes or more), out of 27,056.

| Check | Rate ratio per 5 min (95% CI) | Neighbourhood-years |
|---|---|---|
| Main estimate | 1.21 (1.03 to 1.44) | 146,508 |
| Uncorrected closure data | 1.30 (1.02 to 1.64) | 146,508 |
| Excluding 2020 and 2021 (Covid) | 1.27 (1.06 to 1.54) | 109,900 |
| 2012 to 2019 only | 1.22 (0.99 to 1.49) | 59,441 |
| Adding next year's drive time: this year | 1.14 (0.88 to 1.48) | 123,041 |
| Adding next year's drive time: next year | 1.09 (0.92 to 1.30) | 123,041 |

The estimate is stable across the first four checks. The last check asks whether
next year's access already predicts this year's reports, which would point to a
trend that existed before the closure. Because closures are permanent, this
year's and next year's drive times are nearly identical, so the effect splits
between them and neither is clearly different from 1 on its own. That neither
confirms nor rules out a prior trend. Two further reasons for caution: litter
reports fall (0.86, 0.81 to 0.92) when access worsens, although access should not
affect littering, which suggests something else changes around closures; and
some apparent closures in the Environment Agency data are not real (see Data
quality issues). This is the most promising lead so far and the one a verified
closure history would test properly.

## What to do next

In order of expected value:

1. **Build a verified HWRC history.** Cross-check WDI site disappearances against
   council web pages (current and Wayback Machine) or FOI, and collect booking
   system dates, DIY charges and opening hours at the same time. This fixes the
   main measurement problem and enables the DIY-ban difference-in-differences
   and booking-system event study.
2. **Test the closure result with verified closures.** The FixMyStreet
   neighbourhood estimate (+21% per 5 minutes) is the strongest lead. Verified
   closure dates, and an event study around each confirmed closure with
   neighbouring unaffected areas as the comparison, would show whether it holds.
3. **Housing mechanisms.** Test the private-renting association more sharply
   with HMO licensing registers, tenancy turnover and student term dates
   (seasonality needs the WasteDataFlow quarterly returns).
4. **Litter.** No administrative litter series exists; OpenLitterMap points or
   Keep Scotland Beautiful / Keep Wales Tidy survey microdata would be needed.

## Attribution and licences

Contains Environment Agency information © Environment Agency and/or database
right (Waste Data Interrogator, used under the Environment Agency conditional
licence; some older extracts carry extra restrictions on publishing site-level
data, so only council-level aggregates are published here). Contains OS data ©
Crown copyright and database right (OS Open Roads). Contains public sector
information licensed under the Open Government Licence v3.0 (Defra, Welsh
Government, ONS, MHCLG, Natural Resources Wales).
