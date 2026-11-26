---
type: dataset-gotcha
spheres: [hydrosphere]
title: "A SWOT reach height can be far from a gauge on a pass whose stated uncertainty is ordinary: apply reach_q before comparing, and look at dark_frac and wse_u as well"
description: "Seen while exploring one year at one reach (Mississippi at Baton Rouge, Version D, calendar 2024, 50 pairs within 15 minutes). One pass flagged reach_q 2 was 1.776 m from the rest with a stated uncertainty of 0.095 m, the year's median, so wse_u gave no warning and only the flag did. One pass that was not flagged was 0.939 m off, with the year's highest dark_frac (0.692) and largest wse_u (0.296 m), so the flag missed it and the other two fields marked it. Two passes in one year: a warning to apply the gate and read the other fields, not a threshold."
tags: [swot, riversp, reach_q, dark_frac, wse_u, quality, gauge, confrontation, hydrology]
generated: { by: claude-code/claude-fable-5-2, at: 2026-11-26T06:30:00Z }
severity: high
dataset: ../datasets/swot-river-lake.md
status: draft
stale_after: 2027-05-26
seen_while: exploring
drafted_from: { exploration: EXPLORATION-0001, notes: [NOTE-001, NOTE-002], log: "57:338aa756dc38f3358456f7b38f8f2b197210f6c231e04bb29cfea310b18f99f8" }
relates_to:
  - { concept: datasets/swot-river-lake.md, relation: extends, why: "that page says the quality attributes are categorical gates and wse_u is the total uncertainty; this adds what was seen at one reach when the gate is not applied, and that the gate and the stated uncertainty each missed a pass the other caught" }
  - { concept: recipes/swot-gauge-confrontation.md, relation: beside, why: "the recipe says how to score a reach against a gauge; this is about which passes to let into the scoring. The other draft in this queue takes up the recipe's worked example" }
  - { concept: gotchas/swot-gauge-datum-mismatch.md, relation: beside, why: "both are about a satellite height against a gauge; that page is about the datum in the level, this one about single passes that are off whatever the datum" }
  - { concept: gotchas/swot-reach-node-scope.md, relation: beside, why: "same product and level; that page is about naming the aggregation level, and everything here is at reach level" }
  - { concept: gotchas/hydrocron-collection-default.md, relation: beside, why: "same product at the same reach; that page is about the product version, and only Version D was used here" }
sources:
  - id: flagged
    resource: examples/baton-rouge/explorations/EXPLORATION-0001/receipts/LOOK-025.json
    title: "Look 25 of the exploration (science-factory repository; receipt sha256 a07420d40a06...): the three flagged pairs one by one and the spread of the 47 unflagged, run 2026-11-26 on the committed 2024 fixture"
  - id: worst
    resource: examples/baton-rouge/explorations/EXPLORATION-0001/receipts/LOOK-023.json
    title: "Look 23 (receipt sha256 6bb0b377a119...): with the flagged passes out, the pairs furthest from the rest, with dark_frac and wse_u for each"
  - id: uncertainty
    resource: examples/baton-rouge/explorations/EXPLORATION-0001/receipts/LOOK-009.json
    title: "Look 9 (receipt sha256 2a797f63e83e...): the median stated wse_u and how many departures fall within twice a pass's own stated uncertainty"
  - id: residual
    resource: examples/baton-rouge/explorations/EXPLORATION-0001/receipts/LOOK-018.json
    title: "Look 18 (receipt sha256 2b5801ef0e6e...): the residual spread about the gain line with the three flagged passes and the one high dark fraction pass left out"
  - id: lowstage
    resource: examples/baton-rouge/explorations/EXPLORATION-0001/receipts/LOOK-029.json
    title: "Look 29 (receipt sha256 fd0ac240ee9a...): departures by third of stage with the flagged passes out"
  - id: dataset
    resource: https://github.com/open-science-pillars/hydrology/blob/f9850d08c526139407eedf13ee3f12effbe83594/knowledge/datasets/swot-river-lake.md
    title: "The hydrology bundle's signed SWOT river and lake dataset concept, read 2026-11-26: quality attributes are categorical gates, wse_u is total height uncertainty"
  - id: fixture
    resource: https://github.com/open-science-pillars/hydrology/blob/f9850d08c526139407eedf13ee3f12effbe83594/verification/fixtures/confrontation/swot_gauge_baton_rouge_2024.json
    title: "The data every look read: reach 74210000331 against USGS-07374000, calendar 2024, Version D named, retrieved 2026-09-08"
---

# A reach height can be far off on a pass whose stated uncertainty is ordinary

**Seen while exploring.** One reach, one gauge, one year: the Mississippi at Baton Rouge (reach 74210000331 against USGS-07374000), Version D, calendar 2024, 50 of 52 passes paired with a gauge reading within 15 minutes.[^fixture] This page is a draft from one exploration. Nothing in it was tested on data set aside for the purpose, and nobody has signed it. Every pass is read as its departure from the median satellite-minus-gauge difference, because the level itself contains an uncited datum offset.

**What happens.** The dataset concept already says the quality attributes are gates and not sizes of error, and that `wse_u` is the total height uncertainty.[^dataset] What it does not say is what was seen here: the gate and the stated uncertainty each failed, on different passes, to warn of a pass that the other marked. Why either pass was off is not known from this record. What `dark_frac` measures for a river reach is not described in the bundle's river concept, and the steward should cite the product's own documentation for it before this page is signed.

**Measured (calendar 2024, this reach only).**

| Pass | reach_q | Gauge stage | Departure from the rest | dark_frac | wse_u |
|---|---|---|---|---|---|
| 2024-10-30 | 2 | 1.47 m, the lowest of the year | -1.776 m | 0.020 | 0.095 m |
| 2024-01-01 | 2 | 1.61 m | -0.080 m | 0.247 | 0.098 m |
| 2024-11-30 | 2 | 3.51 m | -0.084 m | 0.020 | 0.096 m |
| 2024-03-26 | 1 | 7.68 m | +0.939 m | 0.692 | 0.296 m |

The first three rows are every flagged pass of the year.[^flagged] The fourth is the unflagged pass furthest from the rest.[^worst] The median stated `wse_u` over the year is 0.096 m, and 47 of 50 departures fall within twice their own pass's stated uncertainty.[^uncertainty] The 47 unflagged pairs have a sample spread of 0.164 m.[^flagged]

So in this year:

- The one pass that was metres off was flagged, and its stated uncertainty was the median. **`wse_u` did not warn of it; only `reach_q` did.**
- Two of the three flagged passes were ordinary. The evidence here that the flag marks bad passes is one pass in three.
- The one unflagged pass that was badly off had the highest `dark_frac` and the largest `wse_u` of the year. **`reach_q` did not warn of it; the other two fields did.**
- Low water by itself was not where it failed: with the flagged passes out, the 15 pairs in the lowest third of stage have a sample spread of 0.081 m.[^lowstage]

With the three flagged passes and the 03-26 pass left out, the residual spread about a fitted gain line is 0.082 m, below the median stated uncertainty.[^residual] That number rests on leaving out a pass chosen after seeing it.

**How it makes a wrong answer look right.** A comparison that lets every pass in reports a disagreement several times the product's stated precision and reads it as the instrument's skill. Here one pass carried most of it. A comparison that trusts `wse_u` to weight or screen passes would have kept the worst one at full weight.

**What to do.** Apply `reach_q` before pairing and report how many passes it removed. Then list the passes furthest from the rest with their `dark_frac` and `wse_u`, by date, and say what leaving each out does. Do not set a `dark_frac` or `wse_u` threshold from a single pass.

**How to check it.** Take any reach with a nearby gauge and a year of passes. Pair within a stated tolerance, take departures from the median difference, and list the largest with `reach_q`, `dark_frac` and `wse_u` beside them. See whether the passes that are far off are the flagged ones, and whether any flagged or far-off pass has an ordinary `wse_u`.

[^flagged]: look 25 of the exploration
[^worst]: look 23 of the exploration
[^uncertainty]: look 9 of the exploration
[^residual]: look 18 of the exploration
[^lowstage]: look 29 of the exploration
[^dataset]: the signed dataset concept
[^fixture]: the committed 2024 fixture
