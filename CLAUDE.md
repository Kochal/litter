# Project notes

Research on what drives fly-tipping and littering in the UK. See README.md for the
pipeline, docs/research_brief.md for hypotheses, docs/results.md for results.

## Writing reports and results pages

Feedback from the project owner on the first results page; apply to every report:

- **Headline findings must read as complete, plain sentences.** No clipped or
  telegraphic phrasing; a reader with no statistics background should understand
  each finding on first read. Say what was compared, what happened, and how big.
- **Explain the methodology first, in clear terms, before any results.** Define
  every driver in everyday language: what it measures, where it comes from, and
  why it might matter (e.g. not "migration churn" but "how many people moved into
  or out of the council area in a year, as a share of residents"). Explain what a
  rate ratio means with a worked example.
- **Show the number of observations on every figure and table** (councils,
  council-years, reports, treated councils), so readers can judge how robust each
  result is. Where a pattern depends on a subgroup (e.g. rural councils recording
  less), show the data behind that claim rather than asserting it.
- No em dashes in any text (owner preference).

## Data handling

- Raw and intermediate data (data/raw, data/interim, data/analysis) are gitignored
  for size. Derived data may be committed or published as long as it contains no
  personally identifiable information (e.g. no operator names from EA files, no
  free text or reporter details from FixMyStreet reports).
- Never send the owner's personal details to external services (e.g. in user agents).
