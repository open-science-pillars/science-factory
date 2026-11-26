# Request

*Written for this example by the assistant that built it, in the voice of a river scientist. No person asked this: it stands in for a request so that the assistants have something real to work on. The data and the knowledge it points at are real.*

**What I want to know.** How well does SWOT river height follow the Baton Rouge gauge, and where does it not? No hypothesis yet beyond "probably well at high water". I want to know what is there before I decide what is worth testing.

**The thing.** SWOT RiverSP reach water surface elevation for the Mississippi reach at Baton Rouge (reach 74210000331), Version D, against the USGS gauge there (USGS-07374000).

**Why it matters.** I am deciding whether the reach product can stand in for stage on reaches that have no gauge. If it follows a good gauge here, that is the first thing I would want to test properly.

**The difference that matters, and where it comes from.** Nobody has stated one. If I had to say: the satellite should rise and fall with the gauge to within about five percent before I would use it as a stage record. That is my judgment, not a requirement.

**What I have already looked at.** Calendar 2024 only: the fixture the hydrology capability keeps (swot_gauge_baton_rouge_2024.json). I have plotted it.

**What could be held out.** Everything after 2024. I have not downloaded or looked at any of it.

**What I will do with each answer.**
- If it holds: write it up as a lead and ask for a proper test on the later data.
- If it does not: I want to know where it breaks, by stage and by quality flag.
- If it cannot tell: say so and say what would tell.

**By when.** No date.

**How I expect it to be fooled.** The two are on different vertical references, so a level difference means little. And I suspect the bad passes are not random: low water, or whatever the quality flag catches.

**Who is on it.** Me. The capability's steward for anything that would be signed.

**What I want back.** A page: what looks true, where it does not hold, what you chose along the way, and what you would test.

**Anyone else's product involved?** Yes: SWOT RiverSP is a named mission product.

---

## From EXPLORATION-0001 (exploring, not a finding)

This request was first explored. The exploration ended in a lead, version 4, which is a lead, not a finding: found by exploring, tested on nothing, and it cannot be signed.

**The lead.** At the Mississippi reach at Baton Rouge (reach 74210000331 against gauge USGS-07374000, Version D, calendar 2024, 50 of 52 passes paired within 15 minutes), SWOT reach height looks as if it follows the gauge closely over the whole 1.47 to 10.33 m range of stage. With the three passes flagged reach_q 2 left out, the gain is 1.0121 with a 95 percent sampling interval of 0.9862 to 1.0381 (47 pairs), and changes between passes correlate at +0.9896 with an RMSD of 0.1859 m. A gain just above one shows in the departures too: the lowest third of stage sits about 0.09 m lower against the gauge than the other two thirds (medians -0.091, +0.027 and +0.023 m), which is the gain seen another way and not a second effect. Where it does not follow, in 2024, is two passes, named here and not a pattern: 2024-10-30, flagged reach_q 2, at the lowest stage of the year, 1.776 m low; and 2024-03-26, not flagged, 0.939 m high, with the year's highest dark fraction (0.692) and largest stated uncertainty (0.296 m). The other two flagged passes are 0.080 and 0.084 m from the rest, which is ordinary. With the three flagged passes and the 03-26 pass out, the residual spread about the gain line is 0.082 m, below the product's median stated uncertainty of 0.096 m. Low water by itself does not look like where it fails: the 15 unflagged pairs in the lowest third of stage have a sample spread of 0.081 m.

**How it was found.** Read the signed recipe first, which already gives the 2024 change scores for this pair and rules out scoring the level. Ran the recipe's own executor and reproduced its correlation (+0.9567), RMSD (0.3823 m) and, once my script used the sample spread as the recipe does, its gauge change spread (1.1959 m). Then looked at each pair's departure from the median level difference: by size, by quality flag, by third of stage, by third of dark fraction, by rising and falling limb, and against the product's stated uncertainty. That is six ways of cutting the same 50 pairs, so one pass standing out in a cut is not by itself remarkable. One pair carried 0.71 of the summed squared departure, and it was flagged. Tried the flag screen, then a gain by least squares with and without it, then the package's own gain method for an interval that allows for correlation in time. Tried pairing at 5 and at 60 minutes. Two looks failed on my own mistakes (a missing folder, a guessed key) and are in the count. A review then found nine holes; five more looks and two more readings answered them, and what could not be closed is written here as a limit. 29 looks were run, 2 failed, 0 were refused at the fence.

**The question proposed for the confirming study.** Over the first full year of forward processing (2025-04-28 to 2026-04-27), does SWOT reach water surface elevation at Baton Rouge rise and fall by the same amount as the gauge, to within five percent?

**The difference that matters, as proposed.** Five percent, from the request, where the scientist calls it their own judgment and not a requirement. It is the scientist's to confirm before any lock.

**Already looked at (working data from now on).** Calendar 2024, the committed fixture swot_gauge_baton_rouge_2024.json in the hydrology capability (52 Version D passes, the gauge readings around each, and 47 Version C passes kept for the version step)

**Held out.** Only what the exploration set aside: 2025-04-28 to onward. The hydrology bundle's signed SWOT lake dataset concept records that the Version D family changes from reprocessing (PGD0, through 2025-04-27) to forward processing (PID0) on 2025-04-28, and its signed river concept records the same two processing identifiers. Everything from that date on is one processing baseline, the request says none of it has been looked at, and it keeps growing, so it is what a later test would want. 2025-01-01 to 2025-04-27 is neither explored nor set aside.

**The review of the lead.** no-holes-found (verdicts/REVIEW-002.md in the exploration).

Lead checksum (lead.json): 01df056b42254bc39cd05ba2491bbfa541063eb5bb519007108c3796b83243b8. Exploration log fingerprint: 61:a200e935618310224744e078273f3ff9c2a50f6d518e09acf12643bf84ecd0db.
