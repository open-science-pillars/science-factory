# Review of the lead from EXPLORATION-0101 (version 1)

By `agent:review-0101`. I did none of this exploration and was given none of the analysis assistant's reasoning. I worked from the files: the request, the exploration log, the receipts, the look scripts, the lead and the knowledge. Verdict: **holes-found**. None of the holes is a wrong number. They are about what the headline says, what the screen is, and what the proposed test could show.

One thing to say about my own context: to judge the leak the lead declares, I read the first lines of `mvp/gain.py` and `mvp/confront.py` and grepped `examples/baton-rouge/README.md` for a few words. That showed me a short summary of an earlier run's lead. I did not open that run's folders.

## What I checked

1. **The record.** `explore.py check-log` passes (39 events, fingerprint 38:d67e2489...). `status`: stage review, 12 looks, 0 failed, 0 refused, 6 choices, 13 knowledge reads, 4 open notes.
2. **What is known, read independently.** `knowledge.py about` with the request's own words lists 8 pages; all 8 are among the 12 the work listed and read (log events 1 to 15). I read the signed recipe, the reach and node page, the river and lake dataset page and the flag paragraph of the lakes page myself. No page that bears on the question was missed. One draft (`gotchas/swot-gauge-datum-mismatch.md`) is leaned on only as support for a signed page, and the lead says it is a draft. The read events name the pages through `src/hydrology/knowledge` while the list events name `hydrology/knowledge`; the first is a symbolic link to the second and the hashes agree, so this is only a wording matter.
3. **Every number against a receipt.** Every number in "What looks true", in the four choices that would change it, in the two that would not, and in the pitfalls is in a receipt, at the receipt's precision (LOOK-003, 004, 005, 006, 007, 008, 009, 010, 011, 012). I found no number rounded to read better than its receipt, with one soft exception in hole 6. `explore.py recheck` on LOOK-003 to LOOK-012 gives output identical to what was logged in all ten cases.
4. **The fence.** Set aside: 2025-01-01 onward, recorded in log event 0 before any knowledge or data event. Every look script opens only the paths on its command line (`looks/*.py`, the `load(sys.argv[..])` lines), and those are the 2024 fixture and `work/confrontation-15.json`. LOOK-001 shows the latest time in the fixture is 2024-12-22T15:30Z. No look reads the Version C block (`satellite_other_version`). No network call in any script. Nothing set aside was touched, and nothing set aside is on disk in the files the looks name.
5. **It calls itself a lead** in the first line, the last line and the plan stub. Good.

## Holes

### 1. The screen is described as the product's own marking, and it is not (it would change the lead's headline)

The lead opens with "once passes the product itself marks are left out" (`lead.md`, What looks true). Three things in the record do not fit that sentence.

- LOOK-001 (`receipts/LOOK-001.out.txt`, line `satellite.rows[].reach_q`): reach_q is 1 on 49 passes and 2 on 3. There is no pass with reach_q 0 in 2024. So "reach_q below 2" means "reach_q equal to 1", and every pass in the year carries a non-zero flag. The lead never says this. The scientist asked where it breaks "by quality flag" and would want this first.
- No knowledge page says what reach_q values mean for a river reach (the lead says so, NOTE-002). The signed lakes page gives the lake flag as 0 good, 1 suspect, 2 degraded, 3 bad (`datasets/swot-lakes.md`, Quality paragraph), and the lead carried other lake field meanings over "as an assumption" (log event 7) but not this one. If the same ladder holds for reaches, the headline rests entirely on passes the product calls suspect. That is a question for the steward and the product description, not something I can settle from the knowledge.
- The wse_u limit of 0.2 m is the analyst's threshold, set after seeing the one pass it removes. The lead owns this in CHOICE-004, but the headline sentence calls it a product marking.

Also on the reach_q screen: of the three passes with reach_q 2, two sit on the line (residuals -0.036 m and -0.066 m, LOOK-010 part a). The flag removes three passes to catch one. The lead says "the flag is not enough" in the pitfalls; the record also shows it is not specific.

What would close it: state the flag census (49 at 1, 3 at 2, none at 0) in the headline, get the meaning of reach_q values for RiverSP reach Version D from the product description into the knowledge, and call the wse_u limit what it is.

### 2. Passes were left out for reasons stated after seeing them, and the leak is wider than the lead says (it limits the lead)

All six choices were recorded at 06:25:35Z (log events 28 to 33), after the last look (event 27, 06:25:03Z). The screen was already in the script of LOOK-005 (`looks/look_05_gain_by_screen.py`, the `screens` list, with the two dates written in as `BAD_Q1` and `BAD_Q2`), written after LOOK-004 had listed every pass against the gauge. So both parts of the screen, and the two passes by date, were chosen after seeing which passes depart. The lead says this for the wse_u limit; it should say it for reach_q as well.

The lead's last pitfall admits that the README and the docstring of `mvp/confront.py` had told the assistant about the two passes before any look. The files say more than that. `mvp/confront.py` (docstring, step 1) states the screen itself: passes with reach_q at or above a threshold are excluded before pairing, because of the 2024 low-stage pass. `mvp/gain.py` (docstring) names the gain of satellite on gauge as the quantity, with a time term and with lower and upper halves of stage. `examples/baton-rouge/README.md` (lines 12 and 55) gives an earlier gain near 1.01 with three flagged passes left out. CHOICE-003 says the gain reading "rests on the request's wording", and CHOICE-004 says the screen rests on LOOK-004. Both were on the page before the assistant looked. The record cannot show which came first in the assistant's reasoning, and the lead should not present them as found here.

What would close it: the leak statement names the quantity and the screen, not only the passes; and a test on the set-aside data fixes the screen from the product description, not from this year.

### 3. A gain of exactly one is not what a reach against a point gauge should give, and the lead does not use the one fact the knowledge has on it (it limits the lead and changes what the test means)

The reach value is an aggregate over roughly 10 km (`gotchas/swot-reach-node-scope.md`, Mechanism) and the gauge is a point. They differ by the water surface slope times the along-river distance between the gauge and the place the reach value refers to. The product's own slope on the screened passes runs from -2.8 to 42.0 parts per million and rises with stage (correlation +0.876, LOOK-008). So each kilometre of offset adds about 0.04 m across the year's range of stage, which is about 0.005 of gain per kilometre. The screened gain of 1.0140 is what about 3 km of offset would give with no instrument effect at all, and LOOK-008's fitted distance is 2887 m with a plain standard error of 2341 m.

The signed recipe states the pair is "0.44 km apart" (`recipes/swot-gauge-confrontation.md`, The worked example). The lead read that page and never cites the distance. If 0.44 km is the distance to the point the reach value refers to, geometry explains about 0.002 of the 0.014 and most of the excess needs another cause. If it is the distance to the nearest point of the centreline, the gauge could be kilometres from the reach centre and geometry could explain all of it. The knowledge does not say which. The lead's sentence "this year cannot say whether that is the instrument, the gauge's place in the reach, or a slow drift" is fair, but the headline before it gives an interval that excludes one, [1.0043, 1.0236], from a model with neither term.

LOOK-008 also has a line the lead leaves out: on the reach_q below 2 set, with the slope term, gain 0.9894 (plain standard error 0.0051) and distance 7820 m (761 m). That fit is carried by the single pass of 2024-03-26 (slope 135.8 ppm), so I do not read it as a distance. I read it as a hint about that pass: an error of about 0.9 m with a slope four times its neighbours and dark_frac 0.692 looks like a height carried to the reach centre from a partly observed reach along a wrong slope. That bears on CHOICE-006 and was not said.

What would close it: where in the reach the gauge sits (along-river distance to the reach centre, upstream or downstream), from SWORD and the site file; then the expected gain from geometry is a number, and the test is against that number, not against one.

### 4. Time terms: with either extra term the gain is no longer distinguishable from one, and the proposed quantity has neither (it would change the wording, and it limits the test)

In 2024 high water is February to June and low water is September to December, so stage and time are tangled. LOOK-011: screened gain with a time term 1.0094, plain standard error 0.0051, drift -0.0684 m per year (0.0526). Two plain standard errors either side is about 0.999 to 1.020. LOOK-008: with the slope term 1.0048 (0.0085). LOOK-007: lower half of stage 1.0133 [0.9675, 1.0591], upper half 0.9871 [0.9640, 1.0101]; residual against time -0.0478 m per year (0.0428). Both halves include one, and the upper half is on the other side of it. What the pooled fit calls a gain of 1.014 is, in these receipts, a low-water group sitting about 0.1 m lower than the rest (LOOK-007 thirds: -0.0594 against +0.0402 and +0.0287), late in the year. A gain, a step at low stage and a drift of 5 to 7 cm per year cannot be told apart on one year.

The lead reports all of these numbers in CHOICE-005, which is to its credit. The holes are that the headline still says "the gain also looks slightly above one" with the narrow interval; that the time and slope fits use plain standard errors on a different pairing (60 minutes interpolated, n=48) while the headline uses the lag-1 effective sample at 15 minutes (n=46), so the three are not on one footing; and that the plan stub's quantity has a free intercept per processing identifier and no time term, although the repository's own prototype says its known-answer tests demanded one (`mvp/gain.py`, docstring).

Not reported in the lead though looked at: rising against falling water. LOOK-007, screened: mean residual -0.0317 m rising (n=17) against +0.0222 m falling (n=25), slope -0.0585 m per (m/day) with plain standard error 0.0389. A river scientist would expect a loop here (steeper surface on the rise), and the sign is worth a sentence.

What would close it: one model, one pairing and one kind of interval for the gain with and without the time term, stated side by side in the headline; a time term or a stated reason for none in the proposed quantity.

### 5. The proposed test asks the least doubtful question and can hardly fail (it would change the proposed question)

The stub's rule: supported if the interval of the gain lies inside 0.95 to 1.05; refuted only if it lies wholly outside. With a gain near 1.01, refutation is close to impossible. The way this product fails in the record is not a wrong scale. It is two passes in fifty wrong by 0.9 m and 1.8 m (LOOK-004), one flagged and one not, and a screen that drops three flagged passes to catch one and catches the other only with a threshold tuned on it. In later data a third kind of gross error would widen the interval and give "inconclusive", not "refuted". So the rule as sketched cannot say "this is not usable as a stage record", which is the scientist's decision.

The reading of "five per cent" was also chosen knowing the alternative fails (CHOICE-003: change RMSD over spread 0.3197 with all passes, "so that reading would have failed outright"). The lead is open about this. But its claim that the other reading "would stay above five per cent under any screen tried" (CHOICE-003, how it would change the answer) is in no receipt: LOOK-005 prints the change RMSD for each screen and not the gauge change spread for that screen. It is very likely true (0.1051 m over a spread near 1.2 m), and it is still a number with no receipt.

What would close it: a question on the set-aside data about the rate and size of departures after a screen fixed in advance from the product description (for example, the share of screened passes more than a stated distance from the line), with the gain reported beside it; and the missing ratio printed in a look.

### 6. Wording wider than the data (wording)

- "to within about two per cent": the point estimate is 1.4 per cent and the interval reaches 2.4 per cent (LOOK-005). "About two" is defensible for the interval and reads a little better than "up to 2.4".
- "the year's lowest stage" for 2024-10-30: the fixture keeps gauge readings only around passes (386 readings, LOOK-001), so this is the lowest stage at any pass, not the lowest of the year.
- "residual scatter is 0.0815 m against a median stated uncertainty of 0.0957 m" is offered as agreement. wse_u is nearly constant on the screened passes (0.0930 to 0.1101 m, LOOK-010 part b), it is the total and not the random part (`datasets/swot-river-lake.md`, Uncertainty), and the 0.0815 m is what is left after fitting two numbers to a set from which the two largest departures were removed. It shows the stated uncertainty is not exceeded on that set; it does not show the stated uncertainty tells a good pass from a bad one. On 2024-10-30 it was 0.095 m on a pass 1.8 m off.
- "How many things were tried: 12 looks". True of the log. Inside those looks there are 8 screens and a robust slope (LOOK-005), 5 pairing rules on two sets (LOOK-009), three sets by thirds, halves, rate and time (LOOK-007), 22 groups by minute (LOOK-010) and 3 tracks (LOOK-011). The lead lists them in "How it was found", so the count is owned in words; the number 12 alone understates it. Leave-one-out (LOOK-006) was run on the unscreened and the reach_q sets and not on the 46 headline pairs.

## What a sceptical river scientist would ask

1. What does reach_q 1 mean, and why is there no pass at 0 over this reach in a whole year? What is in the bitwise flag behind it?
2. Where is the gauge in the reach: how far along the river from the point the reach height refers to, and on which side? What gain should I expect from the river's own slope before I blame the satellite?
3. Baton Rouge is on the leveed lower river and the slope goes to zero and below at low water (LOOK-004: -2.8 and -9.1 ppm). Is the low-water offset of about 0.1 m the river (backwater, tide at low flow, a loop between rise and fall) or the instrument or a drift? One year cannot say; which later data would?
4. The pass of 2024-10-30 is 1.8 m low with an ordinary stated uncertainty and a clear surface (dark_frac 0.020). What went wrong, and would the node heights or the crossover calibration quality have shown it? The fixture has neither (NOTE-001).
5. The pass of 2024-03-26: was the reach only partly seen? The product has fields for that which this file lacks. A threshold on wse_u is a stand-in for them. (This is from my general knowledge of the product, not from the knowledge base, and needs checking there.)
6. I said "probably well at high water". The one unflagged gross error is at high water. On the screened passes the scatter is 0.0619 m in the highest third and 0.0807 m in the lowest (LOOK-007). Say that plainly.
7. I want to use this where there is no gauge. There, I cannot tune a threshold on a departure. Which screen would you have written down before seeing this year?
8. The gauge is provisional for the whole year. When was it retrieved (2026-09-08, LOOK-001) and has it been revised since?

## What I did not find

No broken record, no number without a receipt in the headline, no look into the set-aside period, no unsigned page presented as signed, no claim to be a finding. The choices that move the answer are mostly listed as such by the lead itself. The holes above are where the headline says more than those choices allow.
