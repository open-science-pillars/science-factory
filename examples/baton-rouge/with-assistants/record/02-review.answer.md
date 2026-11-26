# Review of EXPLORATION-0101: answer from `agent:review-0101`

**Verdict: holes-found**, recorded with `explore.py review` as review 1 (log event 39, `explorations/EXPLORATION-0101/verdicts/REVIEW-001.md`; my source file is `explorations/EXPLORATION-0101/review/review-0101.md`). The exploration is now at stage `revise-or-end`, with the analysis assistant. I did none of the work and was given none of its reasoning. I did not read `record/01-analysis.answer.md`, since it is the author's account.

No number is wrong. The holes are about what the headline says, what the screen is, and what the proposed test could show.

## What checked out

- `check-log` passes before and after my verdict (40 events now). Status before: 12 looks, 0 failed, 0 refused, 6 choices, 13 knowledge reads, 4 open notes.
- `knowledge.py about` with the request's words lists 8 pages, all among the 12 the work listed and read (log events 1 to 15). No page bearing on the question was missed. The one draft is used only as support for a signed page and is called a draft.
- Every number in the lead is in a receipt at the receipt's precision, with one exception (hole 5). `explore.py recheck` on LOOK-003 to LOOK-012 reproduces all ten outputs identically.
- The fence held. The set-aside (2025-01-01 onward) is in log event 0, before any knowledge or data event. Every look script opens only the paths on its command line: the 2024 fixture and `work/confrontation-15.json`. The latest time in the fixture is 2024-12-22T15:30Z (LOOK-001). No script touches the network or the Version C block.
- The lead calls itself a lead throughout.

## Holes, each with its evidence

1. **The screen is called the product's own marking, and it is not** (would change the headline). `lead.md`, What looks true: "once passes the product itself marks are left out". LOOK-001 shows reach_q is 1 on 49 passes and 2 on 3, with none at 0, so "reach_q below 2" means "reach_q equal to 1" and every 2024 pass carries a non-zero flag. The lead never says so, although the request asks where it breaks by quality flag. No knowledge page defines reach_q values for a river reach (NOTE-002 says this). The signed lakes page gives the lake flag as 0 good, 1 suspect, 2 degraded, 3 bad (`datasets/swot-lakes.md`, Quality paragraph); if that ladder carries over, the headline rests wholly on passes the product calls suspect. The wse_u limit of 0.2 m is the analyst's threshold, not a product mark. The flag is also not specific: of three passes at reach_q 2, two sit on the line (residuals -0.036 m and -0.066 m, LOOK-010 part a).

2. **Passes were left out for reasons stated after seeing them, and the leak is wider than declared** (limits the lead). All six choices are logged at 06:25:35Z (events 28 to 33), after the last look (event 27, 06:25:03Z). The screen and the two dates (`BAD_Q1`, `BAD_Q2`) are already in `looks/look_05_gain_by_screen.py`, written after LOOK-004 listed every pass against the gauge. The lead admits this for the wse_u limit only. Its leak statement names only the two passes, but the `mvp/confront.py` docstring states the reach_q screen itself, the `mvp/gain.py` docstring names the gain as the quantity (with a time term and stage halves), and `examples/baton-rouge/README.md` lines 12 and 55 give an earlier gain near 1.01 with three flagged passes left out. CHOICE-003 and CHOICE-004 present the quantity and the screen as arising from the request's wording and LOOK-004.

3. **A gain of exactly one is not the expectation for a reach against a point gauge** (limits the lead, changes what the test means). The reach value is an aggregate over roughly 10 km (`gotchas/swot-reach-node-scope.md`). The two differ by surface slope times along-river offset, and the product slope rises with stage from -2.8 to 42.0 ppm (correlation +0.876, LOOK-008). By my arithmetic from those receipts, that is about 0.005 of gain per kilometre of offset, so the screened 1.0140 is what about 3 km would give with no instrument effect; LOOK-008 fits 2887 m (plain standard error 2341 m). The signed recipe says the pair is "0.44 km apart" (`recipes/swot-gauge-confrontation.md`, worked example). The lead read that page and never cites the distance, and the knowledge does not say whether it is measured to the reach centre or to the nearest point of the centreline. The lead also omits LOOK-008's other line (reach_q below 2 set: gain 0.9894, distance 7820 m), which is carried by the 2024-03-26 pass alone. I read that as a hint that the pass was a partly seen reach extrapolated along a wrong slope, which bears on CHOICE-006.

4. **Time terms** (changes the wording, limits the test). Stage and time are tangled in 2024: high water February to June, low water September to December.
   - With a time term the screened gain is 1.0094, plain standard error 0.0051, drift -0.0684 m per year (LOOK-011). Two standard errors reach about 0.999.
   - With the slope term it is 1.0048 (0.0085) (LOOK-008).
   - By stage halves it is 1.0133 [0.9675, 1.0591] and 0.9871 [0.9640, 1.0101] (LOOK-007). Both include one.
   - The pooled 1.014 is, in the receipts, a low-water group about 0.1 m lower than the rest, late in the year (LOOK-007 thirds).

   The lead reports these in CHOICE-005, yet the headline keeps "slightly above one" with [1.0043, 1.0236]. The fits are on different footings: plain standard errors at 60 minutes interpolated (n=48) against the lag-1 interval at 15 minutes (n=46). The plan stub's quantity has no time term, though the `mvp/gain.py` docstring says its known-answer tests demanded one. The rising against falling result in LOOK-007 (-0.0317 m against +0.0222 m) is not in the lead.

5. **The proposed test asks the least doubtful question and can hardly fail** (would change the proposed question). Refutation needs the whole interval outside 0.95 to 1.05, which is near impossible at a gain near 1.01. The failure the record shows is 2 passes in 50 off by 0.9 m and 1.8 m (LOOK-004), with a screen that drops three flagged passes to catch one. A new kind of gross error in later data would give "inconclusive", never "refuted". The reading of five per cent as a gain was chosen knowing the other reading fails (CHOICE-003 says so). The claim that the other reading "would stay above five per cent under any screen tried" is in no receipt: LOOK-005 prints no gauge change spread for the screened sets.

6. **Wording.**
   - "About two per cent": the estimate is 1.4 and the interval reaches 2.4.
   - "The year's lowest stage" is the lowest at any pass; the fixture keeps readings only around passes.
   - The residual scatter under the stated uncertainty (0.0815 m against 0.0957 m) does not show that wse_u tells good from bad. wse_u is nearly constant (0.0930 to 0.1101 m) and was 0.095 m on the pass that was 1.8 m off.
   - "12 looks" understates the comparisons inside them, though the lead lists them in words.
   - Leave-one-out was not run on the 46 headline pairs.

## What a sceptical river scientist would ask

- What does reach_q 1 mean, and why is no pass at 0 in a year?
- Where does the gauge sit in the reach, and what gain does the river's own slope predict?
- Is the 0.1 m low-water offset the river (backwater, tide at low flow, a loop between rise and fall), the instrument, or a drift?
- What went wrong on 2024-10-30, a clear surface with an ordinary stated uncertainty? Would node heights or the crossover quality have shown it?
- Was the reach only partly seen on 2024-03-26?
- I said "probably well at high water", so why is the one unflagged gross error at high water?
- Which screen would you have written down before seeing this year, for a reach with no gauge?
- Has the provisional gauge record been revised since its retrieval on 2026-09-08?

## What was unclear or got in my way

- **Role file against skill, on where to write.** `assistants/review.md` lists `explorations/*/review/*.md` under writes; the tool then copies the file to `verdicts/REVIEW-001.md` and logs that copy. The exploration had a `verdicts/` folder and no `review/` folder, so I had to create one. Neither file says the tool copies, or which of the two is the record.
- **This answer file is outside my role's `writes` list.** I wrote it because the coordinating assistant asked.
- **`must_never_see` is ambiguous on the author's answer file.** "The working context of the assistant whose work it checks": I took `record/01-analysis.answer.md` to be covered and did not read it, but the role does not say whether an author's hand-off note counts. The `notes/` and `work/` folders inside the exploration are in the same position; I read notes only as they appear in the log.
- **Judging a declared leak needs the leaking files.** I read the heads of `mvp/gain.py` and `mvp/confront.py` and grepped the example README, which showed me a summary of the earlier run I was told not to read. The role gives no guidance on this.
- **`may_call` lists `sf.py note`** but nothing says when a reviewer should raise a note in place of writing a hole. I raised none. Hole 1 (reach_q meanings) and hole 3 (what "0.44 km apart" measures) are really gaps in the knowledge for the steward.
- **Review step 2 points at `openwiki/` and the `openwiki_*` tools**, which do not apply here. `knowledge.py about --wiki ../hydrology/knowledge` worked. Its ranking is by shared words: a second query on flags, slope and distance returned IMERG and NLDI pages and nothing on flags.
- **Two spellings of one knowledge path.** `../hydrology` is a symbolic link to `../src/hydrology`, so the log's list events and read events name the same pages differently. The hashes match; it cost a check.
- **`recheck` cannot see runs made outside the log.** Each look script's modification time is within a second of its logged run and all ran first time. That fits a write-and-run in one command, and I did not count it as a hole. The skill's "how many things were tried" rests on trust here.
- **The skill counts looks, not comparisons inside a look.** One look here holds nine fits.
- `uv run` needed `--offline` in this sandbox and prints a `UV_NATIVE_TLS` deprecation warning into every receipt's first line.
