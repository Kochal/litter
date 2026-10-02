# Research brief: what drives fly-tipping and littering in the UK?

Prepared for the council-level panel study of fly-tipping and access to household
waste recycling centres (HWRCs) in England and Wales, 2012/13 to 2024/25.
Companion to `DATASETS.md`.

**Verification key used throughout.** Each reference carries a tag:
**[V]** full text read in this session; **[S]** existence, authors and venue
confirmed through search indexes and abstracts, but the full text could not be
opened (gov.uk, ResearchGate, Springer, WRAP and several other hosts were blocked
from this environment); **[U]** not verified in this session (from prior knowledge
or secondary reporting only), so check before citing.

---

## Executive summary

- **Scale.** English councils recorded 1.26 million fly-tipping incidents in
  2024/25, up 9% on 2023/24; 62% involved household waste and about 4% were
  "tipper lorry load" or larger. Wales recorded 48,367 incidents in 2024/25,
  a 14.7% rise. Official counts are council-recorded incidents, mostly on public
  land, and are strongly shaped by recording effort and reporting basis.
- **What the evidence says, in brief.**
  - *Cost and convenience of legal disposal* is the most consistently cited
    driver in surveys and qualitative work (Webb et al. 2006; Hodsman and
    Williams 2011; Purdy et al. 2022), and international econometrics finds that
    more disposal facilities reduce dumping (Ichinose and Yamamoto 2011) and that
    unit pricing can induce some dumping (Fullerton and Kinnaman 1996), though
    not always (Allers and Hoeben 2010).
  - *But the UK quasi-experimental evidence on specific HWRC restrictions is
    weak and mostly null*: WRAP (2021) found no significant association between
    HWRC DIY charging and fly-tipping; the Defra booking-systems study (Purdy,
    Borrion and Crocker 2022) found no evidence of a link. Neither used a
    credible causal design. This is the main gap our project can fill.
  - *Deprivation, density and rented/transient housing* are the most robust
    cross-sectional correlates (WRAP 2021; Hodsman and Williams 2011; Holmes and
    Perczel 2025).
  - *Organised and commercial waste crime* (rogue "man and van" carriers, skip
    firms, illegal sites) drives the large incidents and is linked to landfill
    tax and gate fees (Liu, Kong and Santibanez Gonzalez 2017; ESA/Eunomia 2021).
  - *Enforcement* has ambiguous signs in observational data because it raises
    recording as well as deterring offending.
  - *Covid-19*: the spring 2020 HWRC closures did not produce the expected
    national surge; fly-tipping fell about 20% in the first lockdown and then
    rebounded, with a net effect near zero, and with rural areas behaving
    differently (Dixon, Farrell and Tilley 2022).
- **Best natural experiments for us**: the England ban on HWRC DIY-waste charges
  (in force 31 December 2023, SI 2023/1243) with Wales and non-charging English
  authorities as controls; staggered HWRC booking-system introductions
  (2020 to 2023); HWRC closures and openings visible in the EA Waste Data
  Interrogator; Covid HWRC closures (late March to May 2020, needs sub-annual
  data); FPN reforms (May 2016, January 2019, 31 July 2023); Wales workplace
  recycling regulations (6 April 2024) for commercial fly-tipping.
- **Design recommendation**: Poisson/negative binomial panel with population
  offset and LA and year fixed effects, staggered event studies, and waste-type,
  size and land-type splits used as falsification and heterogeneity tests.
  Assign HWRC "treatments" at the waste disposal authority (WDA) level in
  two-tier areas, since counties run HWRCs while districts record fly-tips.

---

## 1. Definitions, scale and measurement

### 1.1 Definitions

- **Fly-tipping** is the illegal deposit of waste on land not licensed to receive
  it, an offence under section 33 of the Environmental Protection Act 1990
  (EPA 1990). It ranges from a single black bag to multiple lorry loads.
  **Littering** (EPA 1990 s.87) is dropping small items such as wrappers, cans
  and cigarette ends. In practice the boundary is blurred: Keep Britain Tidy's
  research finds that householders often do not regard leaving bags beside bins,
  boxes next to recycling banks or donations outside a closed charity shop as
  fly-tipping (KBT 2018; KBT "Beyond the Tipping Point").
- **Household vs commercial.** Defra's waste-type categories distinguish
  household black bags, "other household waste" (furniture, mattresses etc.),
  white goods, other electricals, green waste, construction/demolition/excavation,
  tyres, vehicle parts, asbestos, clinical, chemical drums, commercial black bags,
  "other commercial" and "other (unidentified)". Some "household" fly-tips are
  produced by traders working in homes (builders, gardeners, house clearers), so
  waste type is an imperfect marker of who dumped it.
- **Size categories** (Defra/WasteDataFlow): single black bag; single item; car
  boot load or less; small van load; transit van load; tipper lorry load;
  significant/multiple loads [V, Defra notes on datasets 2026]. Size is recorded
  only for incidents the council investigates and clears, so size totals can
  differ from waste-type and land-type totals [V].
- **Land types** include highway, footpath/bridleway, back alleyway, railway,
  council land, agricultural, private/residential, commercial/industrial,
  watercourse/bank and other.
- **Division of labour.** Councils handle most incidents; the Environment Agency
  (EA) deals with large-scale, hazardous or organised dumping, which is not in the
  council counts.

### 1.2 Scale and trend

- England: 711,000 incidents in 2012/13, rising to about 1.13 million in 2020/21
  (+16% on 2019/20, household-waste incidents +16% to 737,000), 1.08 million in
  2022/23, 1.15 million in 2023/24 and 1.26 million in 2024/25 (Defra, various
  years [S]). Household waste was 62% (777,000 incidents) in 2024/25; 52,000
  incidents were tipper-lorry size or larger, costing councils £19.3m to clear;
  investigations were 68% of 572,000 enforcement actions and about 69,000 FPNs
  were issued, with roughly 1,400 prosecutions [S].
- Wales: 48,367 incidents in 2024/25 (+14.7%), 71% involving household waste;
  enforcement actions at a six-year high (Welsh Government and Fly-tipping
  Action Wales 2026 [S]).
- Costs: ESA/Eunomia estimated the cost of fly-tipping in England at £392m in
  2018/19 within a total waste-crime cost of £924m (up from £604m in 2015)
  [S]. The EA's National Waste Crime Survey 2023 estimated that about 18% of all
  waste is illegally managed, and 52% of landowners/farmers reported being
  affected by waste crime [S].

### 1.3 Measurement problems that matter for our design

All points below are confirmed in Defra's *Fly-tipping incidents and actions
2024/25 update: notes on datasets* [V], unless otherwise flagged.

1. **Recording basis.** Since 2019/20 each English LA declares whether it reports
   "all incidents" (including those proactively found and cleared by staff or
   contractors) or "customer/public reported only". About 10% were not on an
   all-incidents basis in 2019/20; in 2023/24, 270 (91%) reported all incidents
   and 24 (8%) public-reported only [S]. Several LAs switch basis mid-year
   (e.g. Pendle 2019/20, Nuneaton and Bedworth and Southend 2020/21, Solihull and
   North Devon 2021/22, Hillingdon and East Lindsey 2022/23, Blackburn with
   Darwen 2022/23 and 2023/24, Gravesham 2024/25). These are measurement shocks
   that must be coded as a time-varying control or used to drop LA-years.
2. **Methodological break in 2019/20.** Before 2019/20 Defra imputed
   "all incidents" for LAs reporting public-only counts in the national totals
   (but not the LA-level file); from 2019/20 it stopped doing so, and 2018/19
   totals were restated. LA-level series are not imputed, so the LA panel is
   less affected than the national series, but a 2019/20 indicator is prudent.
3. **Private land is largely missing.** Councils usually do not clear private
   land, so incidents there (notably farmland) are under-recorded; this is why
   size totals do not match land-type totals. Surveys of farmers (EA 2023; NFU)
   suggest substantial unrecorded dumping.
4. **Recording effort.** Councils with proactive cleansing and in-cab recording
   technology record more: Newham's note in the 2014/15 data explicitly
   attributes its high count to "state-of-the-art in-cab technology" and multiple
   daily cleansing rounds [V]. Effort is LA-specific and time-varying.
5. **Imputation and missing data.** Some LA-years are partly estimated or
   withheld (e.g. Hackney after its October 2020 cyber-attack, Thurrock 2016/17,
   Isle of Wight 2023/24, Fylde 2024/25, Birmingham actions 2024/25). Estimated
   values appear in national totals but not in the LA file.
6. **Boundary changes.** LA reorganisations on 1 April 2019 (Bournemouth,
   Christchurch and Poole; Dorset; East Suffolk; West Suffolk; Somerset West and
   Taunton), 1 April 2020 (Buckinghamshire), 1 April 2021 (North and West
   Northamptonshire) and 1 April 2023 (Cumberland; Westmorland and Furness;
   North Yorkshire; Somerset) require harmonising to a stable geography [V].
7. **FPN data.** Fly-tipping FPN powers began May 2016; household duty of care
   FPNs January 2019 (2018/19 covers January to March only) [V]. From 2023/24,
   WasteDataFlow asked voluntarily for each LA's FPN level and early-payment
   discount (47% responded in 2023/24, 50% in 2024/25) [V].
8. **Cost data.** Standard unit costs (2003 to 2006 vintage) were dropped after
   2016/17, so only tipper-lorry and multi-load clearance costs and prosecution
   costs are reported thereafter [V].
9. **Litter** has no administrative count comparable to fly-tipping; available
   measures are survey-based (KBT LEQSE in England, Keep Wales Tidy LEAMS) or
   crowd-sourced (OpenLitterMap), all listed in `DATASETS.md`.

---

## 2. Drivers: direction and strength of evidence

Strength scale: **Strong** = consistent causal or quasi-experimental evidence;
**Moderate** = consistent correlational evidence from several sources;
**Weak** = mixed, anecdotal or survey-perception only.

| Driver | Expected direction | Strength | Key evidence |
|---|---|---|---|
| Distance/time to HWRC, number of disposal facilities | Fewer/further sites, more dumping | Moderate (international); untested in UK panel | Ichinose and Yamamoto 2011; Hodsman and Williams 2011 (survey); Liu et al. 2017 |
| HWRC opening hours, closures | Fewer hours/closures, more dumping | Weak | Council reports; Senedd Research briefing; Purdy et al. 2022 (perceptions) |
| HWRC booking systems (mostly post-2020) | Hypothesised increase | Weak, mostly null | Purdy, Borrion and Crocker 2022; LGA 2022 |
| DIY/rubble/tyre charges at HWRCs | Hypothesised increase in C&D fly-tips | Weak, null in cross-section | WRAP 2021 (p = 0.29) |
| Van/trailer permits, residency checks | Hypothesised increase, esp. near borders | Weak (no studies found) | Practitioner reports only |
| Bulky waste collection charges | Higher charge, more furniture/white goods dumping | Weak, mixed | Hodsman and Williams 2011; secondary analyses show weak correlation |
| Residual collection frequency (fortnightly, three/four-weekly) and side-waste rules | Lower frequency, more black-bag dumping | Weak | Conwy trial reported no significant rise; KBT 2018 links side-waste rules to dumping near litter bins |
| Garden waste charges | More green-waste dumping | Weak, council monitoring finds no rise | Warwick, Haringey, Huntingdonshire committee reports |
| Landfill tax, gate fees, skip hire costs | Higher costs, more (commercial, large) dumping | Moderate | Liu et al. 2017 (but see sign issue below); Matsumoto and Takeuchi 2011; Webb et al. 2006 |
| Pay-as-you-throw / unit pricing (international) | Some dumping response | Moderate, mixed | Fullerton and Kinnaman 1996 (yes); Allers and Hoeben 2010 (no) |
| Deprivation | Higher | Moderate to strong (cross-section) | WRAP 2021; Hodsman and Williams 2011 |
| Private renting, HMOs, tenant turnover, students | Higher | Moderate (qualitative and cross-section) | Hodsman and Williams 2011; Holmes and Perczel 2025 |
| Flats, communal bins, density | Higher | Moderate | Hodsman and Williams 2011; KBT 2018 (London) |
| Low car ownership | Higher (cannot reach HWRC) | Weak (plausible, little direct evidence) | Implied by surveys; interaction with HWRC distance is testable |
| Rogue waste carriers, organised waste crime | Higher, esp. large incidents | Moderate | Purdy et al. 2022 (86% of "man and van" firms apparently unregistered); EA 2023; ESA/Eunomia 2021 |
| Enforcement (FPNs, prosecutions, CCTV, fine levels) | Deterrence lowers; recording raises | Weak for net effect | Matsumoto and Takeuchi 2011; Liu et al. 2017; CCTV case studies only |
| Social norms and disorder cues | Existing litter/dumping, more dumping | Strong (experimental, littering) | Keizer, Lindenberg and Steg 2008; Cialdini, Reno and Kallgren 1990; Schultz et al. 2013 |
| Covid-19 HWRC closures | Expected increase; observed fall then rebound | Moderate (one quasi-experimental study) | Dixon, Farrell and Tilley 2022 |
| Seasonality | Spring/summer and end of tenancy peaks | Weak (practitioner knowledge) | Not documented in sources reviewed |

### 2.1 Access to legal disposal

- **Distance and facility supply.** Ichinose and Yamamoto (2011), using Japanese
  municipal data, find that the number of illegal dump sites falls as the number
  of intermediate waste management facilities rises [S]. Liu, Kong and Santibanez
  Gonzalez (2017), a 2008 to 2014 English panel with count models, report that more
  landfill facilities, higher income and stronger penalties reduce illegal dumping
  [S]. In a survey of 219 English householders, Hodsman and Williams (2011) found
  the main stated reasons for bulky-item fly-tipping were lack of a nearby HWRC,
  the cost of legal disposal and weak deterrence [S]. **No study we found
  estimates the effect of HWRC drive time on fly-tipping in a UK panel with
  site-level changes.** This is the core contribution available to us.
- **HWRC network contraction.** Austerity led to closures, reduced hours and
  consolidation; one source reports England's HWRC count falling from 734
  (2010/11) to 697 (2013/14) [U: figure seen only in a search snippet, possibly
  from Jaidee et al. on Hampshire's network, not confirmed]. The EA Waste Data
  Interrogator lets us build our own site panel.
- **Booking systems.** Introduced widely during Covid and retained by roughly
  half of English councils [U: "around 50%" is a commonly repeated figure in
  industry sources]. Purdy, Borrion and Crocker (2022, Defra EV04102) combined a
  literature review, LA survey and interviews: no peer-reviewed literature, and no
  evidence of a link; in six councils studied in depth, fly-tipping fell after
  introduction [S]. Their design is descriptive, not causal, and the authors note
  that poorly designed systems might matter where better ones do not.
- **DIY waste charges.** About a third of English councils charged for DIY waste
  (rubble, plasterboard, bathroom units) before the ban [S]. WRAP (2021) compared
  charging and non-charging LAs: charging LAs had *lower* rates (13.3 vs 15.3
  incidents per 1,000 people); in a model, charging was not significant
  (p = 0.29) and deprivation was the only significant variable [S]. This is a
  cross-sectional comparison, so selection (affluent counties charge) could mask a
  true effect. The England ban, in force 31 December 2023 (Controlled Waste
  (England and Wales) (Amendment) (England) Regulations 2023, SI 2023/1243),
  requires free acceptance of small DIY quantities (reported as up to 100 litres,
  i.e. two 50-litre rubble bags, or one item no larger than 2m x 0.75m x 0.7m,
  subject to a limit on visit frequency) [S; check the exact frequency rule in
  the SI].
- **Permits and residency checks.** Commonly blamed by residents and councillors,
  but no evaluation was found. Testable via cross-border spillovers.

### 2.2 Council collection services

- **Bulky waste charges** vary widely and rose in recent years. Evidence linking
  them to fly-tipping is weak; one secondary analysis reports only a weak
  correlation (r = -0.26) between price and fly-tipping rates, with free-service
  councils recording more incidents on average, almost certainly because urban,
  deprived councils both offer free collection and have more fly-tipping [U: from
  a commercial waste firm's blog, not a primary source].
- **Collection frequency and side waste.** Conwy's three- and four-weekly residual
  collections (2017 onwards) were reported by the council to cause no significant
  increase in side waste or fly-tipping, with black-bag waste at 22% of incidents
  in 2017 and 25% in 2018 [S, council-reported]. KBT's London research (2018)
  identifies strict side-waste rules as an unintended driver, leading residents to
  leave bags by public litter bins [S].
- **Garden waste charges.** Several English councils monitored green-waste
  fly-tipping after introducing charges and reported no significant change [S,
  committee papers].

### 2.3 Cost of legal disposal for traders

- **Landfill tax** rose by £8/tonne a year from £24 (2007/08) to £80 (2014/15),
  then with RPI; £64 in 2012/13 and £126.15 in 2025/26 [S]. Wales replaced it with
  Landfill Disposals Tax from April 2018, including an **unauthorised disposals
  rate at 150% of the standard rate** (£133.45/tonne in 2018/19) [S].
- Liu et al. (2017) report that higher landfill cost (tax plus gate fee) is
  associated with *less* illegal dumping in England, which contradicts the usual
  incentive story; treat this cautiously, since national tax rates are collinear
  with time trends [S]. Matsumoto and Takeuchi (2011), on Japanese appliance
  dumping, find higher disposal costs and weaker enforcement increase dumping,
  and that dumping is higher where unemployment is higher [S].
- **Pay-as-you-throw.** Fullerton and Kinnaman (1996, Charlottesville) estimate that
  a sizeable share (reported as roughly 28% to 43% by different summaries) of the
  measured fall in kerbside waste after a per-bag fee was illegal dumping or other
  diversion [S]. Allers and Hoeben (2010), a difference-in-differences study of
  all 458 Dutch municipalities over ten years, found no evidence of waste tourism
  or illegal dumping [S]. Korean volume-based fee studies (Hong 2001; Kim 2002)
  suggest some dumping response, but these are short-panel studies [U, seen only
  as cited in later work].
- **Skip hire costs**: no systematic UK evidence found.

### 2.4 Housing and demographics

- Fly-tipping concentrates in deprived, dense areas with high renting
  (Hodsman and Williams 2011 [S]; WRAP 2021 [S]). Holmes and Perczel (2025),
  interviewing 14 LA waste officers and councillors, describe fly-tipping as
  occurring in "transitional zones" and associate it with rented, sometimes
  illegally sublet housing occupied by transient groups such as students,
  refugees and asylum seekers [S].
- Tenancy turnover and **student move-out** (June) are widely reported by councils
  and landlord groups as spikes [U, practitioner and press only].
- KBT's London study (2018) finds a lack of awareness of what counts as
  fly-tipping, including among some recent European migrants, and a belief that
  leaving reusable items out is "helping someone out" [S].
- **Car ownership**: rarely tested directly, but it plausibly moderates the effect
  of HWRC distance (households without a car cannot use most HWRCs, and many sites
  ban pedestrians).

### 2.5 Rogue carriers and organised waste crime

- Purdy et al. (2022) found 86% of "man and van" operators and 68% of skip firms
  advertising online appeared to lack waste carrier registration [S]. Householders
  have a duty of care to use registered carriers (FPN up to £600 since 31 July 2023;
  household duty of care FPNs began January 2019).
- Large incidents (tipper lorry and above) are the signature of commercial or
  organised dumping. The EA survey (2023) reports perceived increases in
  large-scale fly-tipping on farmland [S].
- Policy pipeline: mandatory digital waste tracking (phased from 2026), carrier,
  broker and dealer reform, and in 2025 the government's Waste Crime Action Plan
  proposals including driving-licence penalty points for fly-tippers and vehicle
  seizure [S, press and legal commentary; check final dates].

### 2.6 Enforcement and deterrence

- FPNs: introduced for fly-tipping in England from 9 May 2016 (£150 to £400,
  default £200; Unauthorised Deposit of Waste (Fixed Penalties) Regulations 2016,
  SI 2016/334) [S]; maximum raised to £1,000 from 31 July 2023 (Environmental
  Offences (Fixed Penalties) (Amendment) (England) Regulations 2023, SI 2023/770),
  with littering raised from £150 to £500 and household duty of care from £400 to
  £600 [S]. The littering maximum had earlier risen from £80 to £150 from 1 April
  2018 under SI 2017/1050 [U for the £80 to £150 detail]. Councils adopted the
  new levels on different dates in 2023 to 2024.
- Observational evidence: Liu et al. (2017) find stronger penalties reduce
  dumping [S]; Matsumoto and Takeuchi (2011) similarly, plus a role for resident
  surveillance [S]. Deterrence research generally finds certainty matters more
  than severity. CCTV evidence is mostly vendor case studies (e.g. an 83% fall at
  one Birmingham hotspot) with no control for displacement [U].
- **Identification problem**: enforcement effort raises recorded incidents
  (investigations generate records, proactive teams find more) while deterring
  offending. In LA panels, enforcement and incidents will be positively
  correlated for reasons unrelated to deterrence.

### 2.7 Social norms and environmental cues

- Keizer, Lindenberg and Steg (2008), six field experiments in Groningen: visible
  disorder (graffiti, litter) roughly doubled littering (e.g. 69% vs 33% littered
  a flyer) and increased theft [S].
- Cialdini, Reno and Kallgren (1990): making descriptive norms (a littered
  setting) or injunctive norms salient changes littering in the direction of the
  salient norm; litter begets litter [S].
- Schultz et al. (2013): 9,757 observed disposals at 130 US sites; 17% littered;
  existing litter increased littering, more bins and shorter distance to a bin
  reduced it, and younger people littered more [S].
- Implication for fly-tipping: hotspots self-reinforce (a reason for fast
  clearance), and spatial and temporal autocorrelation is expected. A 2026 Lancaster
  study models this "broken windows" spillover with a graph neural network on
  2019 to 2025 incident data [S].

### 2.8 Litter-specific drivers

- **Smoking**: smoking-related litter was found on 77% of surveyed English sites in
  2019/20 (KBT LEQSE) [S].
- **Fast food**: present on 27% of sites in 2019/20 [S]; earlier KBT data reported
  a 59% rise in fast-food litter 2004 to 2015 [U]; Keep Wales Tidy found fast-food
  packaging on 67% of Welsh main roads [S]. Takeaway density is higher, and rising
  faster, in deprived areas (Norfolk study), a key confounder [S].
- **Bins**: availability and proximity reduce littering (Schultz et al. 2013) [S].
- **Roads and verges**: KBT reports 23% of people say they are likely to litter
  from a car, especially when anonymous [S]; keeper civil penalties for vehicle
  littering outside London started 1 April 2018 (SI 2018/171) [S].
- **Events**: no systematic UK evidence found.
- **Packaging policy**: 5p carrier bag charges (Wales October 2011, England October
  2015) cut bag use sharply (Wales -76% distribution in the first year, England
  -89% over time) [S]; marine litter effects are documented in beach-clean data.

### 2.9 Covid-19

- HWRCs in England closed in late March 2020 under stay-at-home rules; government
  guidance allowed reopening from early May, with most reopening between about
  5 and 12 May (e.g. Shropshire and Telford 5 May, London boroughs from 11 May,
  Cumbria 12 May) [S]. In Wales, the Welsh Government confirmed reopening on
  8 May 2020, and councils reopened from about 15 May (Wrexham) to 26 May
  (Flintshire) [S]. Many councils also suspended bulky and garden collections.
- Dixon, Farrell and Tilley (2022): FOI monthly data from 216 of 394 UK LAs,
  January 2017 to July 2020. Fly-tipping fell about 20% in the first lockdown,
  then rebounded as restrictions eased, net effect near zero ("temporal
  displacement"); urban areas drove the fall while some rural areas rose; the
  authors attribute the fall to higher perceived risk with people at home [S].
- Annual Defra data show a 16% rise in 2020/21, so the annual figure blends the
  dip, the rebound and later lockdowns. **Sub-annual data are essential** for
  using Covid as a natural experiment.

### 2.10 Seasonality

Practitioner sources describe spring and summer peaks (garden and DIY activity,
clear-outs) and end-of-tenancy spikes; we found no peer-reviewed quantification
for the UK. WasteDataFlow is quarterly and Dixon et al. show monthly data can be
obtained by FOI.

---

## 3. Key studies and grey literature

The core evidence base, all detailed in section 2 and the reference list:

- **Official and Defra-commissioned**: Defra annual statistics and dataset notes;
  Webb et al. (2006) for the Jill Dando Institute; Purdy et al. (2022) *Drivers,
  Deterrents and Impacts* (EV04101); Purdy, Borrion and Crocker (2022) on booking
  systems (EV04102); Defra's 2022 consultation and June 2023 response on DIY
  charges and booking systems; EA National Waste Crime Survey 2023.
- **Charity, industry, local and devolved government**: WRAP (2021) on HWRC
  charging; Keep Britain Tidy (London 2018 study, *Beyond the Tipping Point*,
  LEQSE); National Fly-Tipping Prevention Group partnership framework;
  ESA/Eunomia (2021) waste crime costs; LGA (2022) booking-systems response;
  Senedd Research and Welsh Government / Fly-tipping Action Wales; Zero Waste
  Scotland (*Flytipping: Costs, Impacts and Behaviours*, plus a COM-B mapping of
  191 influences on litter and flytipping); Defra/WRAP Fly-tipping Intervention
  Grants (11 councils in 2022, 21 in 2023, 26 in 2024).
- **Academic**: Hodsman and Williams (2011); Ichinose and Yamamoto (2011);
  Matsumoto and Takeuchi (2011); Liu et al. (2017); Sahramäki and Kankaanranta
  (2017, situational prevention, Finland); Dixon, Farrell and Tilley (2022);
  Holmes and Perczel (2025); Lu et al. (2025, Hong Kong spatial model);
  Fullerton and Kinnaman (1996) and Allers and Hoeben (2010) on unit pricing;
  Keizer et al. (2008), Cialdini et al. (1990) and Schultz et al. (2013) on norms.

**Gap**: no study found uses a UK panel with site-level HWRC changes or the
2023 DIY-charge ban to estimate causal effects on fly-tipping.

---

## 4. Natural experiments and policy changes for identification

| Event | Date(s) | Variation | Data needed | Where |
|---|---|---|---|---|
| Covid HWRC closures | Closed about 23 March 2020; reopened about 5 to 26 May 2020 (England from early May; Wales from 8 May announcement) | Closure length and bulky/garden suspensions vary by WDA; urban/rural | Monthly or quarterly incidents; reopening dates per WDA | FOI (Dixon et al. method); WasteDataFlow quarterly returns; council news archives |
| England DIY-waste charge ban | In force 31 December 2023 (SI 2023/1243) | Treated: about one third of English LAs that charged; controls: non-charging English LAs and all Welsh LAs | Pre-ban charging status and tariffs per WDA | WRAP 2021 dataset; Defra 2022 consultation; Wayback Machine snapshots of council pages; FOI |
| HWRC booking systems | Mostly spring 2020 onwards; some removed or made permanent 2021 to 2025 | Staggered adoption and removal across WDAs | Start/end dates, slot capacity, walk-in exceptions | Purdy et al. 2022 survey; council minutes; Wayback; FOI |
| HWRC closures, openings, hour cuts | Throughout 2012 to 2025 | Site-level, changes drive time for specific LSOAs | Site panel with years active, tonnage | EA Waste Data Interrogator (civic amenity sites, annual); NRW returns; council minutes |
| FPN powers and levels | 9 May 2016 (fly-tipping FPN, £150 to £400); January 2019 (household duty of care FPN); 1 April 2018 (vehicle-keeper littering penalties); 31 July 2023 (max £1,000 fly-tipping, £500 litter, £600 duty of care) | National dates but staggered local adoption and chosen levels | LA adoption dates and FPN levels | Defra LA dataset (FPN levels voluntary from 2023/24); council cabinet decisions |
| Fly-tipping Intervention Grants | 2022 (11 LAs), 2023 (21), 2024 (26) | Selected LAs, likely hotspot-selected | Recipient lists and project types (mostly CCTV) | WRAP/Defra announcements |
| Collection frequency changes | Various (e.g. Conwy three/four-weekly from 2017); England Simpler Recycling 31 March 2026 (outside panel) | Staggered by WCA | Residual frequency by LA-year | WRAP LA Portal scheme data [U]; council records; FOI |
| Wales workplace recycling regulations | 6 April 2024 | Wales vs England, commercial waste types only | Commercial black bags and other commercial fly-tips | Defra and StatsWales waste-type splits |
| Landfill tax divergence | Wales LDT from 1 April 2018, unauthorised rate 150% | Wales vs England, mostly level shift | Rate series | HMRC; Welsh Revenue Authority |
| LA reorganisations | 1 April 2019, 2020, 2021, 2023 (England); none in Wales in the panel | Policy harmonisation inside new unitaries (e.g. HWRC rules) | Harmonised geography; pre/post policies | Defra notes; ONS lookups |
| Recording-basis switches | Various, listed in Defra notes | LA-specific measurement shocks | Basis per LA-year | Defra notes on datasets (2019/20 onwards) |

---

## 5. Implications for our analysis

### 5.1 Ranked hypotheses

**H1. Poorer HWRC access raises household fly-tipping.** Within-LA increases in
population-weighted drive time to the nearest HWRC (from site closures) raise
incidents of HWRC-type waste (other household, white goods, electricals, green,
small construction), with effects concentrated in car-boot to transit-van sizes,
and stronger where car ownership is low.
- Variables: drive time (and 2SFCA accessibility weighted by tonnage) per LA-year;
  site open/close years; car availability.
- Data: EA Waste Data Interrogator, NRW, OS Open Roads, ONS centroids, Census
  2021 TS045 (all **in DATASETS.md**); HWRC opening hours and closure dates
  (**new: scraping/FOI/council minutes**).

**H2. HWRC restrictions raise targeted waste types; removing them lowers them.**
DIY charges raise construction/demolition fly-tips, and the 31 December 2023 ban
lowers them in previously charging authorities; booking systems raise
HWRC-type household fly-tips at introduction.
- Variables: charging status/tariffs and booking start/end dates per WDA-year.
- Data: **new** (WRAP 2021 list, Defra consultation, Wayback Machine, FOI).

**H3. Housing churn and density drive black-bag and bulky household fly-tipping.**
Higher private renting, HMOs, flats and student populations raise black bags and
"other household" on highways and back alleys.
- Data: Census 2021 tenure TS054 and IMD/WIMD (**in DATASETS.md**); accommodation
  type and student counts from Census 2021 (**new tables**); HMO licensing
  registers (**new: scraping/FOI**). Mostly cross-sectional, so these are absorbed
  by LA fixed effects; estimate in between-LA models or as interactions with H1/H2.

**H4. Council collection services matter for specific streams.** Higher bulky
charges raise furniture and white-goods dumping; lower residual frequency and
strict side-waste rules raise black-bag dumping; garden charges raise green-waste
dumping.
- Data: bulky charges, frequency, garden charges by LA-year (**partly in
  DATASETS.md** as "council waste service data"; in practice **new collection**
  via WRAP LA Portal, FOI and archived web pages).

**H5. Trade disposal costs and rogue carriers drive large and commercial
incidents.** Large (tipper lorry and above) and commercial/C&D incidents respond
to landfill tax and gate fees and are higher where permitted transfer stations
and landfills are far away.
- Data: landfill and transfer site locations (**in DATASETS.md**); landfill tax and
  LDT rates, WRAP Gate Fees reports [U], EA waste crime data (**new**).

Lower priority: **H6** enforcement deterrence (FPN levels and adoption dates;
intervention grants), which is hard to separate from recording effort; **H7**
Covid dip and rebound, which needs monthly data (FOI).

### 5.2 Expected confounders and threats

- **Recording effort and basis**: LA fixed effects; time-varying recording-basis
  dummy; exclude switching LA-years; consider investigations or staff-reported
  share as an effort proxy (but endogenous; use lags and robustness only).
- **Deprivation, urbanity, tenure, density**: slow-moving, largely absorbed by LA
  fixed effects; include time-varying population, IMD rank changes (2015, 2019,
  2025 vintages), and region-by-year effects.
- **Council finances**: cuts drive both HWRC closures and reduced cleansing or
  enforcement. Control with revenue outturn spending on waste and street
  cleansing (MHCLG RO5 [U], **new**).
- **Policy bundling**: booking systems often arrived with residency checks or van
  restrictions; DIY charges with tyre/plasterboard charges. Code bundles.
- **Two-tier structure**: districts record fly-tips; counties run HWRCs. Treat
  county-level treatments at WDA level and cluster standard errors by WDA.
- **Spillovers**: residency checks and closures displace users across boundaries;
  include neighbour-exposure terms or drop border LAs as a robustness check.
- **Reverse causality**: councils may close HWRCs where use is low, or add booking
  because of congestion; test pre-trends.
- **Boundary changes**: aggregate to the 2023 geography (or the coarsest stable
  units) for the whole panel.

### 5.3 Recommended model designs

1. **Baseline panel.** Poisson pseudo-maximum likelihood (preferred for fixed
   effects consistency) and negative binomial, with log population offset, LA and
   year fixed effects, region-by-year effects, and WDA-clustered errors.
   Outcome: incidents by waste type, size and land type.
2. **Continuous treatment.** Drive time or accessibility index, identified from
   site openings and closures within LA; also a dose-response by distance band.
3. **Staggered event studies** for booking systems, DIY charges and closures:
   use heterogeneity-robust estimators (Callaway and Sant'Anna; Sun and Abraham;
   or Wooldridge's Poisson extended two-way fixed effects) with leads to test
   pre-trends.
4. **DIY-ban difference-in-differences** (2024/25 vs prior years): previously
   charging English WDAs vs non-charging English WDAs and Welsh LAs, outcome
   construction/demolition incidents; triple difference against other waste types
   within the same LA.
5. **Falsification outcomes.** HWRC treatments should move household HWRC-type
   streams but not commercial black bags, animal carcasses, clinical waste,
   asbestos or vehicle parts; size effects should appear in car-boot to
   transit-van categories, not tipper lorry and above.
6. **Land-type heterogeneity.** Expect effects on highways, footpaths and back
   alleys (where household dumping is recorded) and weaker effects on
   agricultural land (under-recorded); a large effect on agricultural land would
   signal recording artefacts.
7. **Sub-annual extension.** WasteDataFlow quarterly returns or FOI monthly data
   for Covid (March to May 2020) and seasonality.
8. **Point-level extension.** FixMyStreet or council incident data at LSOA level
   with distance to the nearest HWRC, for within-LA designs.

### 5.4 Data sources found that are not in DATASETS.md

- Defra *notes on datasets* (recording basis per LA, imputations, reorganisations):
  <https://s3.eu-west-1.amazonaws.com/data.defra.gov.uk/statistics_2024/Flytipping+notes+on+datasets.pdf>
- WasteDataFlow quarterly fly-tipping module (sub-annual counts).
- WRAP (2021) HWRC charging analysis (list of charging LAs):
  <https://www.wrap.ngo/resources/report/relationship-between-fly-tipping-rates-and-hwrc-charging>
- Defra 2022 consultation on DIY charges and booking systems and the 2023
  response: <https://www.gov.uk/government/consultations/household-waste-recycling-centres-diy-waste-disposal-charges-and-booking-systems>
- Purdy, Borrion and Crocker (2022) booking-system survey of LAs.
- Fly-tipping Intervention Grant recipient lists (WRAP/Defra).
- Landfill tax (HMRC) and Landfill Disposals Tax (Welsh Revenue Authority) rates:
  <https://www.gov.wales/landfill-disposals-tax-rates>
- WRAP Gate Fees reports [U].
- EA National Waste Crime Survey 2023 and ESA/Eunomia waste crime cost estimates.
- FOI monthly fly-tipping data (Dixon et al. 2022 approach).
- MHCLG revenue outturn (waste and street cleansing spend) [U].
- HMO licensing registers; Census 2021 accommodation-type and student tables.
- Food Standards Agency hygiene ratings (takeaway locations, for litter) [U].
- Legislation dates: SI 2016/334, SI 2017/1050, SI 2018/171, SI 2023/770,
  SI 2023/1243 (legislation.gov.uk).

---

## References

- Allers, M.A. and Hoeben, C. (2010). Effects of unit-based garbage pricing: a
  differences-in-differences approach. *Environmental and Resource Economics*
  45(3), 405 to 428. <https://doi.org/10.1007/s10640-009-9320-6> [S]
- Cialdini, R.B., Reno, R.R. and Kallgren, C.A. (1990). A focus theory of
  normative conduct: recycling the concept of norms to reduce littering in public
  places. *Journal of Personality and Social Psychology* 58(6), 1015 to 1026.
  <https://www.semanticscholar.org/paper/4c7df37dcc52cb5087bf9b0a1e7dbd781a7122f1> [S]
- Defra (2026). Fly-tipping incidents and actions 2024/25 update: notes on
  datasets. <https://s3.eu-west-1.amazonaws.com/data.defra.gov.uk/statistics_2024/Flytipping+notes+on+datasets.pdf> [V]
- Defra (annual). Fly-tipping statistics for England.
  <https://www.gov.uk/government/statistics/fly-tipping-in-england> [S]
- Defra (2022 to 2023). Household waste recycling centres: DIY waste disposal
  charges and booking systems (consultation and government response).
  <https://www.gov.uk/government/consultations/household-waste-recycling-centres-diy-waste-disposal-charges-and-booking-systems> [S]
- Dixon, A.C., Farrell, G. and Tilley, N. (2022). Illegal waste fly-tipping in the
  Covid-19 pandemic: enhanced compliance, temporal displacement, and urban to rural
  variation. *Crime Science* 11, 8.
  <https://doi.org/10.1186/s40163-022-00170-3> [S]
- Environment Agency (2023). National waste crime survey 2023: results and
  findings. <https://assets.publishing.service.gov.uk/media/67e1629d70323a45fe6a7003/National_waste_crime_survey_2023_-_report.pdf> [S]
- Environmental Services Association / Eunomia (2021). Counting the Cost of UK
  Waste Crime. <https://eunomia.eco/reports/counting-the-cost-of-uk-waste-crime/> [S]
- Fullerton, D. and Kinnaman, T.C. (1996). Household responses to pricing garbage
  by the bag. *American Economic Review* 86(4), 971 to 984. NBER working paper
  version: <https://www.nber.org/system/files/working_papers/w4670/w4670.pdf>
  [S for the study and findings; U for the exact journal pagination]
- Hodsman, C. and Williams, I.D. (2011). Drivers for the fly-tipping of household
  bulky waste in England. *Proceedings of the ICE: Municipal Engineer* 164(ME1),
  33 to 44. <https://eprints.soton.ac.uk/73800> [S]
- Holmes, H. and Perczel, J. (2025). Fly-tipping and the sociology of abandonment.
  *The Sociological Review* 73(3), 607 to 625.
  <https://doi.org/10.1177/00380261241285183> [S]
- Ichinose, D. and Yamamoto, M. (2011). On the relationship between the provision
  of waste management service and illegal dumping. *Resource and Energy
  Economics* 33(1), 79 to 93. <https://doi.org/10.1016/j.reseneeco.2010.01.002> [S]
- Keep Britain Tidy (2018). Understanding and Tackling Fly-Tipping in London
  (with ADEPT and partners).
  <https://www.keepbritaintidy.org/sites/default/files/resources/Understanding-and-Tackling-Fly-Tipping-in-London-Final-Report.pdf> [S]
- Keep Britain Tidy (n.d.). Beyond the Tipping Point: insights to tackle
  householder fly-tipping. <https://www.keepbritaintidy.org/beyond-tipping-point>
  [S; publication year not confirmed]
- Keep Britain Tidy (2020). The Local Environmental Quality Survey of England
  2019/20 (How clean is England?).
  <https://www.keepbritaintidy.org/sites/default/files/resources/National%20Litter%20Survey%20How%20Clean%20is%20England%20Leaflet%20201920.pdf> [S]
- Keizer, K., Lindenberg, S. and Steg, L. (2008). The spreading of disorder.
  *Science* 322(5908), 1681 to 1685. <https://doi.org/10.1126/science.1161405> [S]
- Local Government Association (2022). Response to Defra call for evidence on
  booking systems at HWRCs and DIY waste charges.
  <https://www.local.gov.uk/parliament/briefings-and-responses/lga-response-defra-call-evidence-booking-systems-household-waste> [S]
- Liu, Y., Kong, F. and Santibanez Gonzalez, E.D.R. (2017). Dumping, waste
  management and ecological security: evidence from England. *Journal of Cleaner
  Production* 167, 1425 to 1437.
  <https://www.sciencedirect.com/science/article/abs/pii/S0959652616321618>
  [S; volume and pages U]
- Lu, W., Yang, B., Yuan, L. and Peng, Z. (2025). Understanding fly-tipping in
  urban areas: a social-economic-spatial combinatorial approach enabled by
  geographically weighted random forest. *Environmental Impact Assessment Review*.
  <https://www.sciencedirect.com/science/article/pii/S0195925525000551> [S]
- Matsumoto, S. and Takeuchi, K. (2011). The effect of community characteristics
  on the frequency of illegal dumping. *Environmental Economics and Policy
  Studies* 13(3), 177 to 193. <https://doi.org/10.1007/s10018-011-0011-5> [S]
- National Fly-Tipping Prevention Group. Fly-tipping Partnership Framework.
  <https://www.keepbritaintidy.org/national-fly-tipping-prevention-group> [S]
- Purdy, R., Borrion, H., Ekblom, P., Tompson, L. et al. (2022). Fly-tipping:
  Drivers, Deterrents and Impacts. Technical report for Defra (EV04101).
  <https://www.researchgate.net/publication/361261033> ; summary:
  <https://naturalengland.contentdm.oclc.org/digital/api/collection/p21006coll3/id/4854/download> [S]
- Purdy, R., Borrion, H. and Crocker, M. (2022). HWRC booking systems and
  incidents of fly-tipping: research into possible links. Technical report for
  Defra (EV04102). <https://www.researchgate.net/publication/367254616> [S]
- Sahramäki, I. and Kankaanranta, T. (2017). Waste no money: reducing
  opportunities for illicit waste dumping. *Crime, Law and Social Change* 68,
  217 to 232. <https://doi.org/10.1007/s10611-016-9674-y> [S]
- Schultz, P.W., Bator, R.J., Large, L.B., Bruni, C.M. and Tabanico, J.J. (2013).
  Littering in context: personal and environmental predictors of littering
  behavior. *Environment and Behavior* 45(1), 35 to 59.
  <https://scholarworks.calstate.edu/concern/publications/jm214p840> [S]
- Senedd Research (n.d.). Fly-tipping in Wales.
  <https://research.senedd.wales/research-articles/fly-tipping-in-wales/> [S]
- Webb, B., Marshall, B., Czarnomski, S. and Tilley, N. (2006). Fly-tipping:
  causes, incentives and solutions. Jill Dando Institute of Crime Science, UCL,
  for Defra. <https://www.semanticscholar.org/paper/fcbf0afab85b3e7a48643fa739231c2e2a84edbf> [S]
- Welsh Government (annual). Local authority recorded fly-tipping.
  <https://www.gov.wales/local-authority-recorded-fly-tipping-april-2024-march-2025> [S]
- WRAP (2021). The relationship between fly-tipping rates and HWRC charging.
  <https://www.wrap.ngo/resources/report/relationship-between-fly-tipping-rates-and-hwrc-charging> [S]
- Zero Waste Scotland. Flytipping: Costs, Impacts and Behaviours.
  <https://www.zerowastescotland.org.uk/resources/flytipping-costs-impacts-and-behaviours> [S]

**Legislation** (legislation.gov.uk) [S]: Unauthorised Deposit of Waste (Fixed
Penalties) Regulations 2016, SI 2016/334; Environmental Offences (Fixed
Penalties) (England) Regulations 2017, SI 2017/1050; Littering From Vehicles
Outside London (Keepers: Civil Penalties) Regulations 2018, SI 2018/171;
Environmental Offences (Fixed Penalties) (Amendment) (England) Regulations 2023,
SI 2023/770; Controlled Waste (England and Wales) (Amendment) (England)
Regulations 2023, SI 2023/1243; Landfill Disposals Tax (Tax Rates) (Wales)
Regulations 2018, WSI 2018/131.

**Not verified / to check**: England HWRC count 734 (2010/11) to 697 (2013/14);
"about 50% of councils use booking systems"; bulky-charge correlation of -0.26;
Korean VWF studies (Hong 2001; Kim 2002); CCTV 83% Birmingham figure; littering
FPN £80 to £150 change in 2018; WRAP LA Portal scheme data, WRAP Gate Fees
reports, MHCLG RO5 and FSA ratings as data sources; exact pagination of
Fullerton and Kinnaman (1996) and Liu et al. (2017).
