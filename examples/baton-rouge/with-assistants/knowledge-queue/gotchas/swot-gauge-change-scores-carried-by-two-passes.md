---
type: dataset-gotcha
spheres: [hydrosphere]
title: "In the 2024 Baton Rouge worked example two of the 50 paired passes carry nine tenths of the squared departure, so its change RMSD of 0.38 m describes those two passes and not the typical one"
description: "Seen while exploring the same reach, gauge, year and collection as the signed confrontation recipe's worked example. The recipe's scores reproduce exactly. Listed pass by pass, two passes (2024-10-30, 1.776 m low; 2024-03-26, 0.947 m high) carry 0.912 of the summed squared departure from the median difference, and the change RMSD is 0.3823 m with them and 0.1043 m without. Each pass enters two consecutive changes, so one gross pass spoils two. List every pass by name before reading a summary score. This page proposes no screen: the two passes were found by looking, on one year at one reach."
tags: [swot, riversp, confrontation, gauge, outliers, skill-scores, hydrology]
generated: { by: claude-code/fable-5-2, at: 2026-11-26T06:55:00Z }
status: draft
severity: medium
dataset: ../datasets/swot-river-lake.md
stale_after: 2027-03-08
seen_while: exploring
drafted_from: { exploration: EXPLORATION-0101, notes: [NOTE-002], lead: "lead.json version 3", log: "52:7a74732c0b1b4b84d61e933500dda18bb97ade880c8fca37db3c65177d31a7c4", curating: "agent:curating-0101" }
relates_to:
  - { concept: recipes/swot-gauge-confrontation.md, relation: narrows, why: "it does not dispute the recipe's numbers, which reproduce exactly. It narrows how the worked example is read: the recipe says the disagreement is not explained by the product's stated precision because the change RMSD is about four times it, and on this file that ratio is carried by two of 50 passes; with those two left out by date it is about 1.1. The recipe's method and refusals are untouched. Whether the worked example should say so is the steward's decision." }
  - { concept: gotchas/hydrocron-collection-default.md, relation: narrows, why: "that page gives the Version D range at this reach in 2024 as -0.534 to 10.201 m. The lower end is the single pass of 2024-10-30, which sits about 2 m below the gauge; the next lowest paired Version D height in the pass table is 1.295 m. Its point, that Versions C and D differ by metres, is not disputed." }
  - { concept: datasets/swot-river-lake.md, relation: beside, why: "same product; that page describes the collections and their attributes, this one a property of one year's comparison at one reach. No conflict." }
  - { concept: recipes/nwm-gauge-confrontation.md, relation: beside, why: "another gauge confrontation recipe, for modelled flow; shares only the form of the scores. No conflict." }
sources:
  - id: look-004
    resource: examples/baton-rouge/with-assistants/explorations/EXPLORATION-0101/receipts/LOOK-004.json
    title: "Receipt of LOOK-004 of EXPLORATION-0101 by agent:analysis-0101 (receipt sha256 d5dc0443...6ccd91; output receipts/LOOK-004.out.txt): every one of the 50 paired passes of calendar 2024 by date, with gauge elevation, satellite height, departure from the median difference, stated uncertainty and product fields, and the share of the summed squared departure carried by the largest passes. Read 2026-11-26. This repository is not under version control, so the receipt's own hash stands in for a commit"
  - id: look-003
    resource: examples/baton-rouge/with-assistants/explorations/EXPLORATION-0101/receipts/LOOK-003.json
    title: "Receipt of LOOK-003 of EXPLORATION-0101 (receipt sha256 d3416b1b...14ae7c; output receipts/LOOK-003.out.txt): the recipe's shipped executor run unmodified on the 2024 fixture, 50 of 52 passes paired at 15 minutes, change scores identical to the recipe's worked example, median stated per-pass uncertainty 0.0958 m, gauge approval Provisional. Read 2026-11-26"
  - id: look-017
    resource: examples/baton-rouge/with-assistants/explorations/EXPLORATION-0101/receipts/LOOK-017.json
    title: "Receipt of LOOK-017 of EXPLORATION-0101 (receipt sha256 6110376f...482d4f; output receipts/LOOK-017.out.txt): change RMSD, gauge change spread and their ratio for eight ways of leaving passes out, including all pairs and both departing passes left out by date. Read 2026-11-26"
  - id: look-005
    resource: examples/baton-rouge/with-assistants/explorations/EXPLORATION-0101/receipts/LOOK-005.json
    title: "Receipt of LOOK-005 of EXPLORATION-0101 (receipt sha256 f1f529d4...36949d; output receipts/LOOK-005.out.txt): change scores and their correlation for the same eight ways of leaving passes out. Read 2026-11-26"
  - id: look-012
    resource: examples/baton-rouge/with-assistants/explorations/EXPLORATION-0101/receipts/LOOK-012.json
    title: "Receipt of LOOK-012 of EXPLORATION-0101 (receipt sha256 6787cc5e...0f85af2; output receipts/LOOK-012.out.txt): the two departing passes beside the gauge readings around them and the two passes before and after each. Read 2026-11-26"
  - id: recipe
    resource: ../recipes/swot-gauge-confrontation.md
    title: "This bundle's signed recipe for confronting a satellite river elevation with a gauge, read 2026-11-26: scores are computed on the changes between consecutive pairs; the worked example at Baton Rouge for 2024 and its reading that the change RMSD is about four times the satellite's stated per-pass uncertainty; the level difference is not a bias"
  - id: collection-default
    resource: ../gotchas/hydrocron-collection-default.md
    title: "This bundle's signed gotcha on the Hydrocron collection default, Measured table, read 2026-11-26: Version D water surface elevation at reach 74210000331 in 2024 spans -0.534 to 10.201 m over 52 passes"
---

# Two passes carry the worked example's change RMSD

**Seen while exploring.** Reach 74210000331 against gauge
USGS-07374000, calendar 2024, collection `SWOT_L2_HR_RiverSP_reach_D`,
52 passes of which 50 pair with a gauge reading inside 15 minutes: the
same pair, year, collection and pairing as the signed recipe's worked
example.[^look-003][^recipe] The gauge is provisional throughout.[^look-003]
This page is a draft from one exploration, on data that had already
been looked at. It has not been tested and no person has read or signed
it.

**What happens.** The recipe scores the changes between consecutive
paired passes.[^recipe] A pass that is grossly off therefore enters two
changes, once with each sign, and a root mean square over about fifty
changes is dominated by the few largest. Why the two passes below are
off is not known; the working file does not carry what would be needed
to say.[^look-012]

**Measured, on this one year.** The recipe's scores reproduce exactly:
49 changes, mean error +0.0019 m, RMSD 0.3823 m, correlation +0.9567,
gauge change spread 1.1959 m.[^look-003] Listed by name, the departures
from the median satellite minus gauge difference (which contains an
uncited datum offset and is not a bias) have a median absolute size of
0.0661 m, and two passes stand far outside: 2024-10-30 at -1.776 m and
2024-03-26 at +0.947 m. The third largest is +0.228 m.[^look-004] The
largest one, two and three passes carry 0.710, 0.912 and 0.923 of the
summed squared departure.[^look-004]

| Passes scored | Changes | Change RMSD | Over gauge change spread | Correlation |
|---|---|---|---|---|
| All 50 pairs (the worked example) | 49 | 0.3823 m | 0.3197 | +0.9567 |
| 2024-10-30 left out | 48 | 0.1828 m | 0.1517 | +0.9894 |
| 2024-03-26 left out | 48 | 0.3556 m | 0.3042 | +0.9575 |
| Both left out, by date | 47 | 0.1043 m | 0.0885 | +0.9960 |

The RMSD and ratio columns are from one look and the correlations from
another.[^look-017][^look-005] The median stated per-pass uncertainty
is 0.0958 m, so by this page's arithmetic the change RMSD is 4.0 times
it with every pair and 1.1 times it with the two passes left out.[^look-003][^look-017]

**What the two passes look like.** Around each, the gauge moves by at
most 0.024 m between consecutive readings, and the two satellite passes
before and after sit at their usual difference from the gauge.[^look-012]
The exploration read both as departures of the satellite and not of the
gauge. That is a reading, not a settled fact: the gauge record is
provisional, and nobody has looked at the node heights or the granules.[^look-012][^look-003]

**How it makes a wrong answer look right.** The all-pairs RMSD is a
true number and reads as a property of the product at this reach:
"disagreement four times the stated precision". A reader takes it as
the size of a typical miss. On this file the RMSD without the two passes is
between three and four times smaller, and the summary is mostly two
events.[^look-004][^look-017]
The opposite error is as easy: quoting 0.10 m as "the" agreement after
removing passes chosen by looking at them.

**What this page does not claim.** It gives no rule for leaving passes
out. The two passes were identified after every pass had been listed
against the gauge, and "left out by date" is a way to show what they
carry, not a screen.[^look-004] It does not say how often such passes
occur: 2 in 52 at one reach in one year fixes no rate. It does not say
the product's quality flag or stated uncertainty marks them or fails
to; that is in the exploration's lead, which is untested, and is a
matter for the steward.

**What to do.** Before reading a change RMSD, list every pass by name
with its departure, and report the share of the squared departure the
largest passes carry beside the score. If passes are left out, say by
what rule, written when, and report the score both ways.

**How to check it.** Run the recipe's executor on the fixture, then
print each paired pass with its satellite minus gauge difference less
the median difference, and recompute the change scores without the two
dates.[^look-003][^look-004][^look-017] The signed collection default
gotcha shows the same pass from another side: the lower end of the
Version D range it gives for this reach, -0.534 m, is the height of the
2024-10-30 pass, and the next lowest paired height in the table is
1.295 m.[^collection-default][^look-004]

[^look-004]: receipt of LOOK-004, EXPLORATION-0101
[^look-003]: receipt of LOOK-003, EXPLORATION-0101
[^look-017]: receipt of LOOK-017, EXPLORATION-0101
[^look-005]: receipt of LOOK-005, EXPLORATION-0101
[^look-012]: receipt of LOOK-012, EXPLORATION-0101
[^recipe]: this bundle's signed confrontation recipe
[^collection-default]: this bundle's signed Hydrocron collection default gotcha
