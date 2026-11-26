---
type: dataset-gotcha
spheres: [hydrosphere]
title: "At one Mississippi reach in 2024 reach_q read 1 on 49 of 52 passes, 2 on 3 and never 0, and this bundle does not say what any reach_q value means"
description: "Seen while exploring calendar 2024 at reach 74210000331 (SWOT_L2_HR_RiverSP_reach_D): the reach quality flag is 1 on 49 delivered passes and 2 on 3, with no pass at 0 or 3, so a rule 'reach_q below 2' keeps exactly the passes at 1. No page of the bundle and no source it cites gives the meaning of the values for a river reach. The lake flag's ladder is documented for lakes only and is not carried over here. Until the product description is read, do not write a screen on reach_q and do not call any value good."
tags: [swot, riversp, reach, reach_q, quality-flag, screening, hydrology]
generated: { by: claude-code/fable-5-2, at: 2026-11-26T06:55:00Z }
status: draft
severity: medium
dataset: ../datasets/swot-river-lake.md
stale_after: 2027-01-04
seen_while: exploring
drafted_from: { exploration: EXPLORATION-0101, notes: [NOTE-005, NOTE-002], lead: "lead.json version 3", log: "52:7a74732c0b1b4b84d61e933500dda18bb97ade880c8fca37db3c65177d31a7c4", curating: "agent:curating-0101" }
relates_to:
  - { concept: datasets/swot-river-lake.md, relation: extends, why: "that page names reach_q and calls the quality attributes categorical gates; it gives no values. This draft adds a census of the values at one reach in one year and states that their meaning is missing from the bundle. It conflicts with nothing there." }
  - { concept: datasets/swot-lakes.md, relation: beside, why: "that page gives the ladder of the lake flag quality_f (0 good, 1 suspect, 2 degraded, 3 bad) from the lake product description. This draft does not carry that ladder to reach_q, because no source read says the river flag shares it. No conflict." }
  - { concept: recipes/swot-gauge-confrontation.md, relation: beside, why: "the recipe's worked example is the same reach and year and says nothing about quality flags. This draft adds the census of the flag on those passes and changes none of the recipe's numbers." }
  - { concept: gotchas/swot-reach-node-scope.md, relation: beside, why: "same product and level; that page is about quoting statistics at the wrong aggregation level, this one about a flag whose values are undefined in the bundle. No conflict." }
sources:
  - id: look-013
    resource: examples/baton-rouge/with-assistants/explorations/EXPLORATION-0101/receipts/LOOK-013.json
    title: "Receipt of LOOK-013 of EXPLORATION-0101, run 2026-11-26T06:43:09Z by agent:analysis-0101 (receipt sha256 d10c3a33...71e7e5; output receipts/LOOK-013.out.txt): census of reach_q and of the fields each pass carries, over the 52 Version D passes of calendar 2024 in the fixture swot_gauge_baton_rouge_2024.json (sha256 b56b65d5...423f27), and the flag set beside departures from the gauge. Read 2026-11-26. This repository is not under version control, so the receipt's own hash stands in for a commit"
  - id: look-001
    resource: examples/baton-rouge/with-assistants/explorations/EXPLORATION-0101/receipts/LOOK-001.json
    title: "Receipt of LOOK-001 of EXPLORATION-0101 (receipt sha256 23811f82...b1a4b6; output receipts/LOOK-001.out.txt): every key path of the same fixture with counts of values, including reach_q for the Version D block (52 passes) and for the Version C block (47 passes), and the retrieval time 2026-09-08T05:12:04Z. Read 2026-11-26"
  - id: river-lake
    resource: ../datasets/swot-river-lake.md
    title: "This bundle's signed SWOT River and Lake Single-Pass concept, Structure and Uncertainty sections, read 2026-11-26: reach_q and xovr_cal_q are attributes of the reach granule; quality attributes are categorical gates, not quantitative uncertainty; no values are given"
  - id: lakes
    resource: ../datasets/swot-lakes.md
    title: "This bundle's signed SWOT lake products concept, Quality paragraph, read 2026-11-26: quality_f is 0 good, 1 suspect, 2 degraded, 3 bad; qual_f_b is the bitflag behind it; partial_f marks a lake at the swath edge; xovr_cal_q is 0 good, 1 suspect, 2 bad or missing. All stated for the lake product, from the lake product description"
  - id: pdd-lakesp
    resource: https://archive.podaac.earthdata.nasa.gov/podaac-ops-cumulus-docs/web-misc/swot_mission_docs/pdd/SWOT-TN-CDM-0673-CNES_Product_Description_L2_HR_LakeSP_20250307_RevC_signed.pdf
    title: "SWOT Product Description Document for L2_HR_LakeSP, Revision C, 2025-03-07: the document the signed lakes page cites for the lake flag ladder. Named here as the lineage of that ladder and as the kind of document that could settle the river flag. NOT read by the drafting assistant (no network on 2026-11-26); it describes the lake product, not the river product"
  - id: review
    resource: examples/baton-rouge/with-assistants/explorations/EXPLORATION-0101/verdicts/REVIEW-001.md
    title: "REVIEW-001 of EXPLORATION-0101 by agent:review-0101 (sha256 76cfae78...dcc72851), hole 1: version 1 of the lead called a reach_q below 2 screen 'passes the product itself marks', although no pass had reach_q 0. Read 2026-11-26"
---

# reach_q was never 0 at one reach in 2024, and the bundle does not say what its values mean

**Seen while exploring.** One reach (74210000331, the Mississippi at
Baton Rouge), one year (calendar 2024), one collection
(`SWOT_L2_HR_RiverSP_reach_D`), 52 delivered passes, in a working file
retrieved on 2026-09-08.[^look-001][^look-013] This page is a draft
from one exploration. Nothing on it has been tested on other data, and
no person has read or signed it.

**What was counted.** Over the 52 passes, `reach_q` is 1 on 49 and 2
on 3. No pass has 0 and no pass has 3.[^look-013] So in this year, at
this reach, the rule "`reach_q` below 2" selects the same 49 passes as
"`reach_q` equal to 1", and every delivered pass carries a non-zero
flag.[^look-013] The Version C block the same file keeps (47 passes,
not otherwise used by the exploration) reads 1 on 35 and 2 on 12, again
with no 0.[^look-001]

**What the bundle says about the flag.** The signed river and lake page
lists `reach_q` among the reach attributes and says the quality
attributes are categorical gates, not quantitative
uncertainty.[^river-lake] It gives no value ladder for `reach_q` and
names no bitwise flag behind it.[^river-lake]

**What is not known.** These are gaps, not findings:

- What 0, 1, 2 and 3 mean for a river reach. The signed lakes page
  gives a ladder for the lake flag `quality_f` (0 good, 1 suspect, 2
  degraded, 3 bad), taken from the lake product
  description.[^lakes][^pdd-lakesp] No source read here says the reach
  flag uses the same ladder, so this page does not say that a pass at
  1 is suspect, or that it is good. If the ladders were the same, every
  pass of 2024 at this reach would be marked at least suspect; that is
  a conditional, and its premise is unverified.[^look-013][^lakes]
- Whether a bitwise flag stands behind `reach_q` for reaches, as
  `qual_f_b` does for lakes, and what its bits are.[^lakes] The working
  file carries none.[^look-013]
- Which reach fields, if any, say that a reach was only partly
  observed. The lakes page names `partial_f` for lakes; nothing in the
  bundle names the river counterpart.[^lakes][^river-lake]
- Why no pass over this wide reach read 0 in a year. The file cannot
  say.[^look-013]

**Who could say.** The product description document for the RiverSP
product, the river counterpart of the lake document the lakes page
cites; no page of this bundle cites it.[^lakes][^pdd-lakesp] Failing
that, PO.DAAC, the archive of the product.[^river-lake] The steward of
this bundle is the one to bring the answer into the river and lake
page, with its source.

**What this page does not claim.** It does not say how well the flag
tells a usable pass from an unusable one. In this year the counts are
too small to say anything: against a line that needs no screen, 2 of
52 passes depart by more than 0.5 m; 1 of the 3 passes at `reach_q` 2
is one of them, and the other departing pass has `reach_q` 1; the two
other passes at 2 sit within 0.05 m of the line.[^look-013] Those
are four passes at one reach. They are an example for a steward to
weigh, not a statement about the product, and the lead they come from
is untested.

**How it makes a wrong answer look right.** A reader who knows the lake
ladder, or who assumes a flag starts at "good", writes "flagged passes
were left out" for a `reach_q` below 2 screen. Here that sentence would
describe a set in which every kept pass carries a non-zero flag whose
meaning nobody has cited.[^look-013] An earlier version of the lead
did write it that way and its reviewer caught it.[^review]

**What to do.** Print the census of `reach_q` values beside any result
that screens on it. Do not describe a value as good, suspect or
degraded for a river reach until the product description has been read
and cited. Do not write a screen for a confirming study from this page
or by analogy with the lake flag: it is the steward's and the
scientist's to write, from the product description.

**How to check it.** Count the values of `reach_q` in the Version D
rows of the fixture named above, or ask Hydrocron for the reach and
year with the collection named and count them there.[^look-013] Then
read the river product description and compare.

[^look-013]: receipt of LOOK-013, EXPLORATION-0101
[^look-001]: receipt of LOOK-001, EXPLORATION-0101
[^river-lake]: this bundle's signed river and lake concept
[^lakes]: this bundle's signed lakes concept, Quality paragraph
[^review]: REVIEW-001 of EXPLORATION-0101, hole 1
[^pdd-lakesp]: the lake product description the lakes page cites; not read by the drafting assistant
