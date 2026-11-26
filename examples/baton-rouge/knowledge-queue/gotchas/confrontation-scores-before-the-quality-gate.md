---
type: dataset-gotcha
spheres: [hydrosphere]
title: "Change scores computed before the product's quality gate can be mostly one flagged pass: at Baton Rouge in 2024 the change RMSD halves when three flagged passes are left out"
description: "Seen while exploring. The confrontation recipe's worked example scores all 50 pairs at Baton Rouge for 2024 and reads the change RMSD of 0.3823 m as about four times the product's stated precision. With the three passes flagged reach_q 2 left out, the same scores on 46 changes are a correlation of +0.9896 and an RMSD of 0.1859 m. The recipe's numbers are right for the pairs it scored; its reading of them as the instrument's disagreement does not survive the product's own gate. The recipe has no step that applies the gate."
tags: [swot, confrontation, gauge, reach_q, skill-scores, quality, riversp, hydrology]
generated: { by: claude-code/claude-fable-5-2, at: 2026-11-26T06:35:00Z }
severity: medium
dataset: ../datasets/swot-river-lake.md
status: draft
stale_after: 2027-05-26
seen_while: exploring
drafted_from: { exploration: EXPLORATION-0001, notes: [NOTE-003], log: "57:338aa756dc38f3358456f7b38f8f2b197210f6c231e04bb29cfea310b18f99f8" }
relates_to:
  - { concept: recipes/swot-gauge-confrontation.md, relation: contradicts, why: "the recipe says of its worked example that the disagreement is not explained by the product's stated precision, the RMSD being about four times it. With the product's own quality gate applied the change RMSD is 0.1859 m, and most of the gap was one flagged pass. The recipe's scores are reproduced exactly; it is the reading, and the missing gate step, that this disagrees with. For the steward to settle: neither page is edited here" }
  - { concept: datasets/swot-river-lake.md, relation: extends, why: "that page says quality attributes are gates; this shows what a score looks like when the gate is not applied" }
  - { concept: gotchas/swot-gauge-datum-mismatch.md, relation: beside, why: "both concern a satellite height against a gauge; that page is about the level, this one about the change scores" }
  - { concept: gotchas/hydrocron-collection-default.md, relation: beside, why: "same reach and year; that page is about the product version, and only Version D was scored here" }
sources:
  - id: all
    resource: examples/baton-rouge/explorations/EXPLORATION-0001/receipts/LOOK-027.json
    title: "Look 27 of the exploration (science-factory repository; receipt sha256 9061151a67d3...): change scores on all 50 pairs, identical to the recipe's worked example, run 2026-11-26"
  - id: gated
    resource: examples/baton-rouge/explorations/EXPLORATION-0001/receipts/LOOK-014.json
    title: "Look 14 (receipt sha256 7cd6096f8ead...): the same change scores with passes flagged reach_q 2 left out"
  - id: flagged
    resource: examples/baton-rouge/explorations/EXPLORATION-0001/receipts/LOOK-025.json
    title: "Look 25 (receipt sha256 a07420d40a06...): the three flagged pairs one by one"
  - id: recipe
    resource: https://github.com/open-science-pillars/hydrology/blob/f9850d08c526139407eedf13ee3f12effbe83594/knowledge/recipes/swot-gauge-confrontation.md
    title: "The hydrology bundle's signed confrontation recipe, read 2026-11-26: the worked example and its reading against the stated precision"
---

# Change scores before the quality gate can be mostly one flagged pass

**Seen while exploring.** The Mississippi at Baton Rouge (reach 74210000331 against USGS-07374000), Version D, calendar 2024: the same pairs as the confrontation recipe's worked example. This page is a draft from one exploration, on data that had already been looked at. It is not tested and not signed, and it disagrees with a signed page, which is for a steward to settle.

**What the recipe says.** Its worked example scores 50 pairs: change correlation +0.9567, change RMSD 0.3823 m, against a per-pass stated uncertainty with a median of 0.096 m, and it reads the result as a disagreement the product's stated precision does not explain, the RMSD being about four times it.[^recipe] The recipe lists what to do before scoring (name the collection, read the datum, check approval, state the tolerance) and has no step for the product's quality flag.[^recipe]

**Measured.**

| Pairs scored | Changes | Correlation of changes | RMSD of changes |
|---|---|---|---|
| all 50 | 49 | +0.9567 | 0.3823 m |
| the 47 with reach_q 1 | 46 | +0.9896 | 0.1859 m |

The first row reproduces the recipe to the digit.[^all] The second leaves out the three passes flagged `reach_q` 2.[^gated] One of those three is 1.776 m from the rest and the other two are within 0.09 m of it, so nearly all of the change between the rows is one pass.[^flagged]

**How it makes a wrong answer look right.** The scores for all pairs are correct arithmetic, and "the satellite disagrees with the gauge by four times its own stated precision" is a natural sentence to write from them. It describes one flagged pass at the year's lowest stage more than it describes the instrument.

**What to do.** Apply the product's quality gate before pairing, report how many passes it removed, and give the scores both ways when they differ this much. Whether the recipe should gain a step, and whether its worked example should be rescored, is the steward's decision.

**How to check it.** Run the recipe's executor on the committed 2024 fixture as it stands, then again on a copy with the three `reach_q` 2 passes removed, and compare the two receipts.

[^all]: look 27 of the exploration
[^gated]: look 14 of the exploration
[^flagged]: look 25 of the exploration
[^recipe]: the signed confrontation recipe
