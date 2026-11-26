---
type: dataset-gotcha
spheres: [hydrosphere]
title: "The Baton Rouge 2024 confrontation fixture keeps eight fields per pass and no processing identifier, cycle, pass number or crossover calibration quality, so which processing a pass came from cannot be read from it"
description: "Seen while exploring: the working file swot_gauge_baton_rouge_2024.json carries, for each of its 52 Version D passes, the time, height, stated uncertainty, width, slope, reach_q, dark_frac and ice_clim_f, and nothing else. The signed pages say the reach granule also has xovr_cal_q and the random uncertainty components, and that the processing identifier varies inside the Version D collection. A file of this shape extended past 2025-04-27 would mix reprocessed and forward processed passes with no way to tell them apart. It also keeps gauge readings only within 60 minutes of each pass, as few as two for some."
tags: [swot, riversp, fixture, crid, provenance, confrontation, hydrology]
generated: { by: claude-code/fable-5-2, at: 2026-11-26T06:55:00Z }
status: draft
severity: low
dataset: ../datasets/swot-river-lake.md
stale_after: 2027-03-08
seen_while: exploring
drafted_from: { exploration: EXPLORATION-0101, notes: [NOTE-001], lead: "lead.json version 3", log: "52:7a74732c0b1b4b84d61e933500dda18bb97ade880c8fca37db3c65177d31a7c4", curating: "agent:curating-0101" }
relates_to:
  - { concept: recipes/swot-gauge-confrontation.md, relation: extends, why: "the recipe's worked example runs on this file and its inputs ask for passes with the collection named. This draft adds what the file does not carry beyond the collection name. It changes none of the recipe's numbers or rules." }
  - { concept: datasets/swot-river-lake.md, relation: beside, why: "that page says the reach granule has 127 attributes and that the processing identifier varies within a collection; this draft only records that a working file keeps eight of them. No conflict." }
  - { concept: datasets/swot-lakes.md, relation: beside, why: "that page dates the two Version D processing identifiers; this draft uses those dates and adds nothing about lakes. No conflict." }
  - { concept: gotchas/hydrocron-collection-default.md, relation: beside, why: "that page is why the file names its collection; this draft is about the level below the collection, the processing identifier, which the file does not keep. No conflict." }
sources:
  - id: look-001
    resource: examples/baton-rouge/with-assistants/explorations/EXPLORATION-0101/receipts/LOOK-001.json
    title: "Receipt of LOOK-001 of EXPLORATION-0101 by agent:analysis-0101 (receipt sha256 23811f82...b1a4b6; output receipts/LOOK-001.out.txt): all 60 key paths of the fixture verification/fixtures/confrontation/swot_gauge_baton_rouge_2024.json in the hydrology capability (73145 bytes, sha256 b56b65d5...423f27, retrieved 2026-09-08T05:12:04Z by verification/fixtures/fetch_confrontation_fixtures.py), with counts and ranges. Read 2026-11-26. This repository is not under version control, so the receipt's own hash stands in for a commit"
  - id: look-013
    resource: examples/baton-rouge/with-assistants/explorations/EXPLORATION-0101/receipts/LOOK-013.json
    title: "Receipt of LOOK-013 of EXPLORATION-0101 (receipt sha256 d10c3a33...71e7e5; output receipts/LOOK-013.out.txt): the fields each pass carries in the working file. Read 2026-11-26"
  - id: look-009
    resource: examples/baton-rouge/with-assistants/explorations/EXPLORATION-0101/receipts/LOOK-009.json
    title: "Receipt of LOOK-009 of EXPLORATION-0101 (receipt sha256 47063c05...043e8772; output receipts/LOOK-009.out.txt): pairing under five rules, the two passes left unpaired at 15 minutes and the count of gauge readings kept around each pass. Read 2026-11-26"
  - id: look-011
    resource: examples/baton-rouge/with-assistants/explorations/EXPLORATION-0101/receipts/LOOK-011.json
    title: "Receipt of LOOK-011 of EXPLORATION-0101 (receipt sha256 be3a5673...b1b7b95ee5; output receipts/LOOK-011.out.txt): three overpass tracks found by the phase of the repeat cycle, since the file has no pass number. Read 2026-11-26"
  - id: river-lake
    resource: ../datasets/swot-river-lake.md
    title: "This bundle's signed SWOT River and Lake Single-Pass concept, read 2026-11-26: the reach granule's attributes (among them wse_r_u, slope_u, slope_r_u, reach_q, xovr_cal_q), the granule naming with cycle, pass and CRID, and that the CRID varies within collections"
  - id: lakes
    resource: ../datasets/swot-lakes.md
    title: "This bundle's signed SWOT lake products concept, version line, read 2026-11-26: Version D is CRID PGD0 reprocessing for 2023-03-30 to 2025-04-27 and PID0 forward processing from 2025-04-28, from the Version D release note"
  - id: hydrocron-lakes
    resource: ../connectors/hydrocron-lakes.md
    title: "This bundle's signed Hydrocron lakes connector concept, field acceptance probe of 2026-09-15, read 2026-11-26: for the prior lake Version D collection the service accepts crid, cycle_id, pass_id and xovr_cal_q among fifty-four field names. Nothing is recorded for the reach collection"
---

# The Baton Rouge fixture does not say which processing a pass came from

**Seen while exploring.** One working file, the hydrology capability's
fixture for the Mississippi at Baton Rouge, calendar 2024, retrieved
2026-09-08: 52 passes of `SWOT_L2_HR_RiverSP_reach_D` and 386 gauge
readings.[^look-001] This page is a draft from one exploration. It
describes one file as it was on the day it was read, and no person has
read or signed it.

**What the file carries.** For each pass: `time`, `wse_m`, `wse_u_m`,
`width_m`, `slope`, `reach_q`, `dark_frac` and `ice_clim_f`.[^look-001][^look-013]
The collection is named once for the whole block.[^look-001]

**What it does not carry.** No processing identifier (CRID), no cycle
and no pass number, although the signed river and lake page says each
granule name holds all three and that the CRID varies within a
collection.[^look-001][^river-lake] No `xovr_cal_q`, no `wse_r_u` and
no slope uncertainty, which the same page lists among the reach
attributes.[^look-013][^river-lake] No bitwise quality flag; whether
the reach product has one is not stated anywhere in the bundle.[^look-013][^river-lake]

**Why it matters.** The signed lakes page dates Version D processing:
PGD0 for 2023-03-30 to 2025-04-27, PID0 from 2025-04-28.[^lakes] By
those dates calendar 2024 should be all PGD0, but that is an inference
from another page, not something the file shows.[^lakes][^look-001] A
file of this shape for a window that crosses 2025-04-28 would hold two
kinds of processing with nothing to tell them apart, and any step
between them would look like the river or the instrument. Without
cycle and pass, the exploration had to infer which of three overpass
tracks each pass belonged to from the phase of the repeat cycle.[^look-011]
Without the fields behind the flag, it could not see why three passes
read `reach_q` 2.[^look-013]

**The gauge side.** The file keeps gauge readings only inside 60
minutes of each pass: between 2 and 8 around a pass, median 8.[^look-001][^look-009]
Two passes (2024-02-23 and 2024-03-15) have only two readings kept, the
nearest 17.0 and 28.1 minutes away, and are the two left unpaired at
the recipe's 15 minutes.[^look-009] So a statement such as "the lowest
stage of the year" cannot be made from it, only the lowest stage at a
pass.[^look-013] Why the kept readings are an hour apart around those
passes is not known.

**What is not known, and who could say.** Whether Hydrocron serves
`crid`, `cycle_id`, `pass_id` and `xovr_cal_q` for the reach
collection: the signed lakes connector page records that it accepts
those names for the prior lake collection and records nothing for
reaches.[^hydrocron-lakes] The Hydrocron documentation or one probe
would say. Whether the fixture should be refetched with those fields
is for the maintainer of the fetch script and the steward.[^look-001]

**How it makes a wrong answer look right.** Everything in the file is
labelled Version D, so a series built from a longer file of the same
shape looks homogeneous. The label is the collection, and the
processing changes inside it.[^river-lake][^lakes]

**What to do.** For any window that reaches 2025-04-28 or later, keep
the processing identifier, cycle and pass with every pass, and report
results for each identifier. Do not assert the processing of a pass
from this file; cite the page the dates come from.

**How to check it.** List the keys of one row of `satellite.rows` in
the fixture.[^look-001]

[^look-001]: receipt of LOOK-001, EXPLORATION-0101
[^look-013]: receipt of LOOK-013, EXPLORATION-0101
[^look-009]: receipt of LOOK-009, EXPLORATION-0101
[^look-011]: receipt of LOOK-011, EXPLORATION-0101
[^river-lake]: this bundle's signed river and lake concept
[^lakes]: this bundle's signed lakes concept
[^hydrocron-lakes]: this bundle's signed Hydrocron lakes connector concept
