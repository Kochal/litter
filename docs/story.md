# What drives fly-tipping in England and Wales

A summary of the project's findings, in six parts. Full results, tables and
caveats are in [results.md](results.md); code is in `src/`.

**How to read the numbers.** Results are given as percentage changes in
fly-tipping per resident, comparing places or years that differ in one thing and
are otherwise alike. "+45% per 10 percentage points of households without a car"
means that an area where 30% of households have no car is expected to have about
45% more fly-tipping per resident than an otherwise similar area where 20% have no
car. Each estimate comes with a likely range (95% confidence interval); if the
range includes 0%, the data cannot tell the effect apart from no effect. The
drivers are:

- **Drive time to the tip:** minutes by car from where residents live to the
  nearest household waste recycling centre, along the road network.
- **Private renting:** the share of households renting from a private landlord
  (Census 2021).
- **No car:** the share of households without a car or van (Census 2021).
- **Deprivation:** the share of households deprived in two or more of the Census's
  four dimensions (employment, education, health and housing).
- **Moving rate:** how many residents moved into or out of the council area in a
  year, from elsewhere in the UK or abroad, per 100 residents (ONS population
  estimates).
- **Street-cleaning spending:** what a council spends a year on street cleaning,
  which includes clearing fly-tips, per resident, in 2024/25 prices (councils'
  revenue outturn returns, adjusted with the consumer prices index).

## 1. Fly-tipping has risen, and most of the real rise is in bigger loads

We analysed the official counts of all 318 councils in England (296) and Wales
(22): 13.2 million incidents from 2012/13 to 2024/25. Recorded fly-tipping per
person in England rose 62%, from 13.2 to 21.5 incidents per 1,000 people a year.

Part of that rise is councils recording more, not people dumping more. We looked
for councils whose recorded numbers doubled or halved within a year or two, and
checked those years for signs of a recording change: a new reporting app, crews
logging everything they find, a change in how the council says it records. 73
councils had such a jump, 41 of them with signs of a recording change (for example
Camden doubled after launching a reporting app in 2018). In the other 223 councils,
whose numbers changed only gradually, recorded fly-tipping per person rose 43%.

| Size of load (223 councils with no sudden jump) | Per 1,000 people, 2012/13 | 2024/25 | Change |
|---|---|---|---|
| Small items (single bag, single item, car-boot load) | 7.7 | 9.4 | +22% |
| Van loads (small van or transit van) | 5.8 | 8.5 | +48% |
| Tipper-lorry load or larger | 0.32 | 0.80 | +149% |
| All fly-tipping | 13.5 | 19.4 | +43% |

The bigger the load, the faster it grew. Lorry-sized dumps are hard to miss and
were recorded before and after any change in recording, so their rise is the
clearest sign of a real increase. Wales rose 34%, almost all of it since 2019.
From 2019/20 Defra also asked councils to count the incidents their own crews
find, so figures from then on are not fully comparable with earlier years.

## 2. Closing recycling centres did not measurably raise fly-tipping

Between 2012 and 2024, 973 of 35,664 neighbourhoods (2.7%) ended up at least 3
minutes' drive further from their nearest recycling centre, mostly because a
centre closed. We tested whether that, or living far from a centre in general,
leads to more fly-tipping. Before testing we accounted for four things:

- **False closures.** Many "closures" in the Environment Agency's site records
  were not real. We checked all 256 sites that appear or disappear in those records
  against archived council websites, merged 35 duplicate records and checked the
  biggest cases by hand. Of 166 apparent closures, 83 remained.
- **Differences in recording between councils**, by comparing areas only within
  the same council and year.
- **Who lives there:** private renting, car ownership, density and whether an
  area is rural.
- **A few heavy-reporting places dominating**, by also giving every closure equal
  weight.

| Test | Change in fly-tipping (likely range) | Based on |
|---|---|---|
| Councils further from a centre, compared with similar councils (per 5 minutes) | +7% (−11% to +30%) | 950 council-years, 317 councils |
| A council's average drive gets 5 minutes longer, same council over time | −3% (−42% to +63%) | 3,814 council-years, 296 councils |
| Neighbourhoods further from a centre, same council and year (per 5 minutes) | −7% (−19% to +7%) | 183,799 neighbourhood-years, 212 councils |
| A neighbourhood's drive gets 5 minutes longer, same neighbourhood over time | +14% (−1% to +30%) | 1,692 neighbourhoods whose drive changed |
| Years 1 to 4 after a closure, each closure weighted equally | −5% (−27% to +23%) | 76 closures, 1,865 affected and 21,225 comparison neighbourhoods |
| The same, closures weighted by reports | +13% (−8% to +39%) | the same |
| Councils' own incident records, areas further from a centre (per 5 minutes) | +3% (−11% to +19%) | 11 councils, 182,072 incidents |
| The nearest centre opens 10 fewer hours a week | +1% (−4% to +7%) | 65,523 neighbourhood-years, 190 councils |
| England's January 2024 ban on charging for DIY waste, construction fly-tipping | +6% (−26% to +54%) | 100 councils that charged vs 184 that did not |

We also found no drive time beyond which fly-tipping jumps. Taken one by one, the
57 closures with enough reports for their own estimate show rises and falls about
equally often; the typical closure was followed by no change (+2%).

One result points the other way: where a closure added 3 minutes or more, reports
were 28% higher in the following years (+7% to +53%, 985 neighbourhoods). Each
correction to the closure records has made the estimated effect of closures
smaller, and this result has not yet been checked for dependence on a few closures.
Taken together, the data rule out large effects of access to recycling centres on
fly-tipping, but cannot rule out a small one where access gets much worse.

## 3. Who lives nearby matters more: private renting and car ownership

Two characteristics of residents explain more of the pattern than distance does,
and they go with different kinds of fly-tipping. Comparing councils with similar
deprivation, density and access, per 10 percentage points more households:

| Kind of fly-tipping | Private renting | No car |
|---|---|---|
| Household black bags | **+107%** (+17% to +265%) | −13% (−51% to +53%) |
| Bulky household and garden waste (furniture, white goods, electricals, green waste) | **+80%** (+24% to +162%) | +22% (−24% to +96%) |
| Van-sized loads | **+44%** (+6% to +97%) | +37% (−2% to +92%) |
| Small items (single bag or item, car-boot load) | −7% (−48% to +67%) | +27% (−17% to +93%) |
| Construction and demolition waste | +13% (−36% to +100%) | **+115%** (+16% to +297%) |
| Tipper-lorry load or larger | +54% (−34% to +258%) | **+105%** (+13% to +274%) |

Based on 950 council-years from 317 councils, 2022/23 to 2024/25. Bold: the likely
range excludes no change.

- **Private renting goes with household clear-outs:** black bags and bulky items,
  typically van-sized loads, not single small items. This fits waste left behind
  when tenants move out and rooms are cleared.
- **Households without a car go with the biggest loads:** builders' rubble and
  lorry-sized dumps. People without a car cannot take building waste or large
  items to a tip themselves.

Both links hold when we compare neighbourhoods inside the same council and year,
where the way councils record fly-tipping cancels out: per 10 percentage points,
+15% for private renting and +23% for no car (183,799 neighbourhood-years,
674,572 FixMyStreet reports, 212 councils). They also hold in twelve councils' own
records of where incidents were found (about 379,000 incidents, including those
crews find themselves): more fly-tipping with more car-less households in 10 of
the 12 councils, and with more private renting in most.

Within neighbourhoods, bags are left close to home: they rise with private renting
(+22%) and car-less households (+24%) in the neighbourhood itself, not in the
surrounding area. Bulky items and builders' waste also rise next to areas with a
lot of private renting (+59% to +123% per 10 points in the surrounding 8 km).

## 4. This is mostly kerbside fly-tipping, not countryside dumping

Recorded fly-tipping happens overwhelmingly in streets: 38% on highways, 18% on
footpaths, 17% on council land and 9% in back alleys, together 83% of incidents in
2022/23 to 2024/25. Private and residential land accounts for 1.3% and farmland
for 0.3%. In FixMyStreet, where a report says where the waste was, 64% describe a
doorstep, pavement or street and 36% an out-of-the-way place such as a layby, field
or verge. Bags (69%) and bulky items (70%) are mostly at the kerb; builders' waste
is split evenly (52%).

The drivers explain the kerbside dumping. Private renting goes with fly-tipping in
back alleys (+135% per 10 points) and on private and residential land (+128%);
car-less households go with back-alley fly-tipping (+118%), but not with dumping on
farmland (+9%, likely range −60% to +197%). Inside the same council, rural
neighbourhoods report about as much fly-tipping per resident as urban ones.

The limits: countryside dumping is badly under-recorded. Farmers usually clear
waste on their land themselves, so it rarely reaches council records (IECR
estimates about 108,000 such incidents a year in England), and few people report
rural dumping on FixMyStreet. Part of the growth in lorry-sized loads may be
dumped in the countryside. Our findings explain kerbside fly-tipping; they say
little about what drives countryside dumping.

## 5. Changes in renting and car ownership do not explain the rise, but more people moving home explains part of it

Between the 2011 and 2021 Censuses, the share of households renting privately
rose and the share without a car fell (318 councils on 2025 boundaries):

| Share of households | 2011 | 2021 | Change, points |
|---|---|---|---|
| Renting privately, England | 16.8% | 20.5% | +3.6 |
| No car or van, England | 25.8% | 23.5% | −2.3 |
| Renting privately, Wales | 14.1% | 17.0% | +2.8 |
| No car or van, Wales | 22.9% | 19.4% | −3.5 |

Using the council comparisons from part 3, more renting should have raised
fly-tipping by about 6% and fewer car-less households should have lowered it by
about 5%. The two roughly cancel out, so together they predict almost no change.

| Size of load (England, 296 councils) | Predicted from renting and car ownership | Actual change, 2012/13 to 2014/15 against 2022/23 to 2024/25 |
|---|---|---|
| All fly-tipping | 0% | +33% |
| Small items | −8% | +26% |
| Van loads | +6% | +32% |
| Tipper-lorry load or larger | −1% | +108% |

Councils where renting grew fastest, or where car ownership changed most, did not
see faster growth in fly-tipping (294 councils; 222 with no sudden jump in
recording). The rise happened almost everywhere, which points to causes that
changed for all councils at once. We looked at three:

- **More people moving home goes with more fly-tipping.** The share of residents
  moving into or out of their council area in a year rose from 12.8 to 15.7 in
  every 100 (England, 2012/13 to 2024/25). When a council's moving rate rises by 5
  in every 100, its fly-tipping rises 16% in councils with no sudden jump in
  recording (likely range +1% to +34%; 222 councils, 2,875 council-years) and 22%
  in all councils (0% to +48%; 295 councils, 3,814 council-years). The link is
  clearest for van-sized loads (+20%, +1% to +43%), which fits clear-outs at moving
  time. Applied to the national rise in moving, this accounts for about 8% to 11%
  more fly-tipping, roughly a quarter to a third of the rise. Because each council
  is compared with itself, fixed differences between councils cannot explain this,
  but other things that changed at the same time could. Between councils, places
  with more moving do not record more fly-tipping once renting is allowed for,
  because the two go together.
- **Spending on street cleaning did not fall.** Per person, in 2024/25 prices,
  councils spent £15.44 in 2017/18 and £15.57 in 2024/25 (£11.90 and £15.57 in
  prices of each year). Councils that cut spending saw slightly more of the largest
  loads: 8% more if spending halves (+4% to +13%; 212 councils, 1,694
  council-years), with no clear change for smaller loads. Because spending held
  steady nationally, it cannot explain the rise.
- **Prosecutions did not keep up.** Councils prosecuted 2,170 fly-tipping cases in
  2012/13 and 1,377 in 2024/25 while incidents nearly doubled: from 3.1 to 1.1
  prosecutions per 1,000 incidents. Fixed penalty notices roughly kept pace (50
  per 1,000 incidents in 2012/13, 55 in 2024/25, peaking at 84 in 2021/22). A
  falling chance of being prosecuted fits the growth in large, deliberate dumps,
  but we cannot test it as a cause, because more incidents on their own push the
  prosecution rate down.

**What remains unexplained.** Most of the rise, and especially the more than
doubling of lorry-sized loads, is not explained by anything we can measure council
by council. The likely candidates changed for the whole country at once: the cost
of getting rid of waste legally, unlicensed waste collectors advertising online,
and enforcement. One hint: lorry-sized dumps grew faster in councils with many
households without a car (48% more growth per decade per 10 percentage points,
+9% to +101%; 296 councils, 3,709 council-years), which would fit a growing trade
in illegal collection for people who cannot get to a tip themselves. In the 223
councils with no sudden jump in recording the estimate is similar (+51%) but too
uncertain to rule out no change (−10% to +154%), so it is suggestive only.

## 6. Methodology

**Data.**

| Source | What it records | Size |
|---|---|---|
| Official council counts (Defra, StatsWales) | Yearly totals per council, by waste type, size of load and type of land; no locations | 13.2 million incidents, 318 councils, 2012/13 to 2024/25 |
| FixMyStreet (mySociety) | Public reports with an exact location; waste type read from the report text | 904,027 reports, 2012 to 2025 |
| Councils' own incident records | Where each incident the council dealt with was found | about 379,000 incidents, 12 councils |
| Environment Agency and Natural Resources Wales site records | Recycling centre locations by year | 845 centres |
| Archived council websites (Internet Archive) | Which centres were really open, their opening hours, booking and DIY charges | 12,524 pages from 316 council websites |
| OS Open Roads, Census 2021 | Road network for drive times; renting, car ownership, deprivation | 35,672 neighbourhoods |
| Census 2011 (Nomis KS402EW, KS404EW) | Renting and car ownership ten years earlier | 318 councils on 2025 boundaries |
| ONS population estimates | Residents and moves into and out of each council area | 318 councils, 2012 to 2024 |
| Council revenue outturn (RO5), ONS consumer prices index | Street-cleaning spending, in 2024/25 prices | 296 councils, 2017/18 to 2024/25 |
| Enforcement actions in the official counts | Prosecutions and fixed penalty notices | 296 councils, 2012/13 to 2024/25 |

A neighbourhood is an ONS Lower Layer Super Output Area, home to about 1,500 to
1,700 people.

**Comparisons.** Each question was tested in more than one way:

1. *Council against council:* do councils with longer drives, more renting or
   fewer cars record more fly-tipping than otherwise similar councils?
2. *Neighbourhood against neighbourhood, inside a council and year:* this removes
   differences in how councils record incidents and how much residents use
   FixMyStreet.
3. *The same place over time:* when a council's or neighbourhood's drive time
   changes, does its fly-tipping change compared with places whose access did not?
4. *Closure by closure:* neighbourhoods that lost their nearest centre against
   nearby neighbourhoods that did not, from four years before to four years after.

**Models.** All estimates come from Poisson regressions of counts with a
population offset, so results are changes in fly-tipping per resident; likely
ranges are 95% confidence intervals with errors clustered by council or waste
authority.

**Recording changes.** A council's step change is a recorded rate that doubles or
halves within a year or two and stays there, by more than three times its usual
year-to-year variation. Signs that it is a recording change: small items becoming
a much larger share; total incidents jumping while large loads do not; FixMyStreet
reports in the council tripling; or a change in its recording basis. The largest
steps were checked against council papers and local news.

**Why it has risen (part 5).** Three tests:

1. *Did the places change?* The national change in each Census share times the
   council comparisons in part 3 gives the predicted change. For example, councils
   with 10 percentage points more private renting have about 18% more fly-tipping
   per resident; renting rose 3.6 points, so renting alone predicts about 6% more.
   This is compared with the actual change between 2012/13 to 2014/15 and 2022/23
   to 2024/25.
2. *Did fly-tipping grow faster where renting grew faster?* Each council's growth
   against its change in renting and car ownership, allowing for 2021 levels,
   deprivation and region, weighted by population. Also: whether the gap between
   high- and low-renting, car-owning and deprived councils widened year by year.
3. *Did anything else change in the same council at the same time?* Each council
   compared with itself over time, after removing the change common to all
   councils each year, for the moving rate and for street-cleaning spending.
   Prosecutions and fines are shown as a trend only, because more incidents on
   their own lower the number per incident.

Every test was run in all councils and in the councils with no sudden jump in
recording, and by size of load. Code: `src/composition_change.py`.

**What the data cannot do.** Official counts measure recording as well as
dumping. FixMyStreet captures the incidents members of the public choose to report
through one website, about 1 in 20 of those councils record. Countryside dumping is
under-recorded in both. Renting and car ownership come from the 2011 and 2021
Censuses, so changes are measured over one ten-year step. Comparing a council with
itself over time removes fixed differences between councils, but not other changes
that happened at the same time.
