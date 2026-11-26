---
type: dataset-gotcha
spheres: [hydrosphere]
title: "A reach height set beside a point gauge differs from it by the water surface slope times the distance between them, and where that slope rises with stage the distance reads as a gain: the recipe's 0.44 km does not say what it is measured to"
description: "Seen while exploring calendar 2024 at the Mississippi reach at Baton Rouge: the product's own reach slope rose by 3.179 parts per million per metre of stage on 46 pairs, so by geometry each kilometre between the gauge and the point the reach height refers to would add 0.0032 to the slope of satellite height on gauge height. The signed recipe gives the reach and gauge as 0.44 km apart without saying between which points or in which direction, and nothing in the bundle says where along its roughly 10 km the reach height refers to. Until that distance is known, a gain a little above or below one at a reach cannot be read as the instrument's."
tags: [swot, riversp, reach, gauge, slope, sword, confrontation, hydrology]
generated: { by: claude-code/fable-5-2, at: 2026-11-26T06:55:00Z }
status: draft
severity: medium
dataset: ../datasets/swot-river-lake.md
stale_after: 2027-03-08
seen_while: exploring
drafted_from: { exploration: EXPLORATION-0101, notes: [NOTE-006], lead: "lead.json version 3", log: "52:7a74732c0b1b4b84d61e933500dda18bb97ade880c8fca37db3c65177d31a7c4", curating: "agent:curating-0101" }
relates_to:
  - { concept: recipes/swot-gauge-confrontation.md, relation: extends, why: "the recipe states the pair is 0.44 km apart and scores changes. This draft does not say that figure is wrong; it says the recipe leaves unstated which two points it joins and in which direction, and adds why that matters for any fit of satellite height on gauge height. The recipe's change scores are untouched: a slope effect that grows with stage is not a constant offset, so it is not removed by differencing, which the recipe does not discuss." }
  - { concept: gotchas/swot-reach-node-scope.md, relation: extends, why: "that page says a reach value is the product's aggregate over roughly 10 km and that every statistic names its level. This draft adds one consequence when a reach value is set beside a point measurement. No conflict." }
  - { concept: datasets/swot-river-lake.md, relation: beside, why: "that page lists slope among the reach attributes and describes reaches as roughly 10 km aggregates; this draft uses the slope field and adds no fact about the product itself. No conflict." }
  - { concept: gotchas/nldi-unsnapped-point.md, relation: beside, why: "also about a point and a river line not being the same place, for another service. No conflict." }
sources:
  - id: look-015
    resource: examples/baton-rouge/with-assistants/explorations/EXPLORATION-0101/receipts/LOOK-015.json
    title: "Receipt of LOOK-015 of EXPLORATION-0101 by agent:analysis-0101 (receipt sha256 9a4f1e55...1f475a10; output receipts/LOOK-015.out.txt): on 46 and on 48 paired passes of calendar 2024, the rise of the product's reach slope with gauge elevation, the gain that geometry would give per kilometre, and fits with the gain held at one (an offset, a drift, a low stage step, slope times a distance). Read 2026-11-26. This repository is not under version control, so the receipt's own hash stands in for a commit"
  - id: look-008
    resource: examples/baton-rouge/with-assistants/explorations/EXPLORATION-0101/receipts/LOOK-008.json
    title: "Receipt of LOOK-008 of EXPLORATION-0101 (receipt sha256 df40a638...6005faab; output receipts/LOOK-008.out.txt): the span of the product's reach slope and its correlation with gauge elevation on two sets of passes, and fits with a slope term. Read 2026-11-26"
  - id: look-001
    resource: examples/baton-rouge/with-assistants/explorations/EXPLORATION-0101/receipts/LOOK-001.json
    title: "Receipt of LOOK-001 of EXPLORATION-0101 (receipt sha256 23811f82...b1a4b6; output receipts/LOOK-001.out.txt): every key path of the fixture swot_gauge_baton_rouge_2024.json, which carries the site's name, datum and drainage area and no coordinates or distance for the gauge or the reach. Read 2026-11-26"
  - id: review
    resource: examples/baton-rouge/with-assistants/explorations/EXPLORATION-0101/verdicts/REVIEW-001.md
    title: "REVIEW-001 of EXPLORATION-0101 by agent:review-0101 (sha256 76cfae78...dcc72851), hole 3: the reasoning that a reach aggregate and a point gauge differ by surface slope times an along-river distance, and that the recipe's 0.44 km is undefined. An assistant's reasoning, not a provider's statement. Read 2026-11-26"
  - id: recipe
    resource: ../recipes/swot-gauge-confrontation.md
    title: "This bundle's signed confrontation recipe, The worked example, read 2026-11-26: reach 74210000331 against gauge USGS-07374000, '0.44 km apart'; inputs include a steward-accepted reach and gauge pair"
  - id: scope
    resource: ../gotchas/swot-reach-node-scope.md
    title: "This bundle's signed reach and node gotcha, Mechanism, read 2026-11-26: reaches are aggregates of roughly 10 km, nodes are about 200 m apart, slope exists only at reach level"
---

# Distance between a reach and a point gauge reads as gain

**Seen while exploring.** Reach 74210000331 (the Mississippi at Baton
Rouge) against gauge USGS-07374000, calendar 2024, collection
`SWOT_L2_HR_RiverSP_reach_D`. The numbers below come from 46 of the 50
paired passes, a set chosen by the analyst after seeing which passes
departed, and from 48 pairs with two passes left out by date.[^look-015]
This page is a draft from one exploration. It has not been tested and
no person has read or signed it.

**What happens.** A reach value is the product's aggregate over roughly
10 km of river; a gauge is one point.[^scope] If the height the reach
reports refers to a place some distance along the river from the gauge,
the two differ by the water surface slope times that distance. A
constant slope would only add a constant, which a datum offset already
hides. A slope that rises with stage adds more at high water than at
low, and a straight line fit of satellite height on gauge height then
has a slope other than one with no instrument effect at all. This is
geometry as reasoned by the exploration's reviewer and analyst; no
provider document read for this bundle states it, and which place
within the reach the reported height refers to is not stated in the
bundle.[^review][^scope]

**Measured, on this one year.** On the 46 pairs the product's own reach
slope spans -2.8 to 42.0 parts per million and its correlation with
gauge elevation is +0.876.[^look-008] It rises by 3.179 parts per
million per metre of gauge elevation (plain standard error 0.264), and
by 3.190 on the 48 pairs.[^look-015] By the geometry above, one
kilometre between the gauge and the point the reach height refers to
would therefore add 0.0032 to the fitted gain.[^look-015] At the 0.44 km
the recipe states that is 0.0014.[^look-015][^recipe]

For scale only: the exploration's untested lead has a fitted gain of
1.0140 on those 46 pairs, and a distance of 4.39 km would produce all
of that excess.[^look-015] That does not make the distance 4.39 km.
With the gain held at one, a slope times distance term, a step at low
stage, a drift in time and a free gain leave residual scatters of
0.0813, 0.0808, 0.0844 and 0.0824 m, so this year cannot tell them
apart.[^look-015]

**What is not known.**

- What the recipe's 0.44 km joins: the gauge and the nearest point of
  the reach centreline, the gauge and the reach centre measured along
  the river, or something else; and whether the gauge is upstream or
  downstream of it.[^recipe]
- Which place within the reach the reach height refers to.[^scope]
- The working file cannot help: it carries no coordinates or distance
  for either side.[^look-001]

**Who could say.** The SWORD database, which defines the reach and its
centreline, for the reach geometry; the USGS site file for the gauge's
position; the river product description for what the reach height
refers to; and the steward who accepted the pair, for how the 0.44 km
was computed.[^recipe][^scope]

**How it makes a wrong answer look right.** A gain of 1.01 or 0.99
against a good gauge looks like a small scale error of the satellite,
or, if it happens to be near one, like proof there is none. Either
could be the river's own slope and a few kilometres.

**What to do.** State the along-river distance and direction between
the gauge and the point the reach height refers to beside any fit of
satellite height on gauge height, and say what gain geometry alone
predicts from the product's slope field before comparing a fitted gain
with one. Where the distance is not known, say so and do not interpret
the excess.

**How to check it.** Regress the reach `slope` on gauge elevation over
the paired passes and multiply by a distance in metres: that is the
gain excess geometry predicts.[^look-015] Then obtain the distance
from SWORD and the site file and compare with the fitted gain on data
not used to choose the passes.

[^look-015]: receipt of LOOK-015, EXPLORATION-0101
[^look-008]: receipt of LOOK-008, EXPLORATION-0101
[^look-001]: receipt of LOOK-001, EXPLORATION-0101
[^review]: REVIEW-001 of EXPLORATION-0101, hole 3: reasoning, not a provider statement
[^recipe]: this bundle's signed confrontation recipe
[^scope]: this bundle's signed reach and node gotcha
