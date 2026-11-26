# Review of the revised lead from EXPLORATION-0101 (version 3)

By `agent:review-0103`. I did none of this exploration, I am not the reviewer of version 1, and I was given none of the analysis assistant's reasoning. I worked from the files: the request, the exploration log, the receipts, the look scripts, the three lead versions, the earlier review (`verdicts/REVIEW-001.md`, identical to `review/review-0101.md`) and the knowledge. I did not open the record folder, the knowledge queue or any other run.

Verdict: **holes-found**. The six holes of REVIEW-001 are answered as far as one year and this knowledge allow, and no number in the lead is wrong. What is left is smaller than last time: two holes in the sketched rule of the proposed test, one clause of the headline that a receipt contradicts, and wording. None of them changes what the lead says looks true.

## What I checked

1. **The record.** `explore.py check-log` passes (59 events, fingerprint 58:178bc656...). `status`: stage review, 17 looks, 0 failed, 0 refused, 10 choices, 13 knowledge reads, no open notes. `lead.md` and `lead.json` are byte for byte `leads/lead-v3.md` and `leads/lead-v3.json`. Version 3 (log event 52) differs from version 2 (event 51) in one phrase ("17.9 times too small" became "its departure is 17.9 times that") and the fingerprint line; nothing else moved.
2. **What is known, read independently.** `knowledge.py about` with the request's words: the first ten pages it ranks that bear on SWOT, the gauge or the confrontation are all among the thirteen the work read (log events 3 to 15). I checked two claims the lead makes about the knowledge: no page gives the meaning of `reach_q` values (true: the only mentions are two lists of field names in `datasets/swot-river-lake.md`, lines 35 and 110), and the signed recipe gives "0.44 km apart" without saying to what (true: `recipes/swot-gauge-confrontation.md`, line 96). The one draft (`gotchas/swot-gauge-datum-mismatch.md`) is named as a draft and used only beside the signed recipe.
3. **Every number against a receipt.** I traced every number in "What looks true", in all ten choices, in the pitfalls and in the plan stub to LOOK-004, 005, 007, 008, 009, 010, 011, 012, 013, 014, 015, 016 or 017, at the receipt's precision. All are there. `explore.py recheck` on LOOK-003 to LOOK-017 gives "the output is identical to what was logged" in all fifteen cases.
4. **The fence.** Set aside: 2025-01-01 onward, log event 0. The five new scripts (`looks/look_13` to `look_17`) open only the path on their command line through `common.load`, which is the 2024 fixture; LOOK-015 also takes the number 0.44 as an argument. No network call, no use of the Version C block, no date after 2024-12-22 in any receipt.
5. **Order of choices.** CHOICE-007 and CHOICE-008 are logged at events 40 and 41, before LOOK-013 (event 42); CHOICE-009 and CHOICE-010 at events 47 and 48, after LOOK-017. The lead says exactly this.
6. **It calls itself a lead** in the first paragraph, the stub heading and the last line.

## Are the earlier holes answered

- **Hole 1 (the screen is not the product's marking): answered.** The census (1 on 49, 2 on 3, none at 0) is in the headline, the wse_u limit is called the analyst's, and the specificity of the flag is stated (LOOK-013, LOOK-016). The meaning of the flag values is still unknown; that cannot be settled here and is a named prerequisite (NOTE-005).
- **Hole 2 (choices after seeing, and the leak): answered.** "How it was found" owns that both parts of the screen were chosen after LOOK-004, and the last pitfall names the quantity, the screen and the two passes as on the page before any look. The 2024 screen is not carried into the test.
- **Hole 3 (reach against a point): answered as far as it can be.** LOOK-015 turns it into numbers (3.179 ppm per metre, 0.0032 of gain per kilometre, 0.0014 at 0.44 km, 4.39 km for all of it) and the line of LOOK-008 that version 1 left out is now in CHOICE-006. Where the gauge sits in the reach is still unknown (NOTE-006), a named prerequisite.
- **Hole 4 (time terms and footing): answered.** LOOK-014 puts every fit on one pairing with one kind of interval; the headline no longer says the gain is above one; the stub's gain model has a time term; rising against falling is reported.
- **Hole 5 (a test that can hardly fail): answered in kind, with new holes in the rule** (holes 1 and 2 below). The missing ratio is now in a receipt (LOOK-017: 0.3197, 0.1501, 0.0867 at best).
- **Hole 6 (wording): answered.** "About two per cent" is gone, "lowest stage at any pass" is used, the scatter is no longer set beside the stated uncertainty as agreement, the count of things tried is owned ("well over a hundred comparisons"), and leave-one-out was run on the 46 headline pairs (1.0127 to 1.0155).

## Holes

### 1. The sketched rule can be met by throwing passes away (it limits the proposed test)

The tested quantity is the share of **kept** passes beyond 0.5 m (`lead.md`, Proposed plan, Quantity estimated), and the screen is not written yet. How many passes the screen removes is "reported beside it and used by no rule". So a severe screen supports the idea by discarding. The record shows how cheap that is: with every pass at `reach_q` 1 or 2, any rule fitted to this product will be built from cuts like those of LOOK-016, where a cut on wse_u that catches both gross errors removes 34 of 52 passes. The only guard in the rule is "fewer than ten pairs in a processing group". The lead lists "a screen that removes mostly ordinary passes" as a hard case and then gives the rule nothing to say about it. For the scientist's purpose (a stage record where there is no gauge) a product that is clean on a third of its passes is a different answer from one that is clean on nearly all.

What would close it: a floor in the rule, stated before opening, on the share of delivered passes the screen must keep (or make the share with no screen the tested quantity and the screened share the one reported beside).

### 2. One in twenty was set after seeing 2 in 52, is in no choice, and at the rate seen the rule most likely cannot conclude (it limits the proposed test)

- The limit of one in twenty appears only in the stub ("Proposed here, for the scientist to decide"). CHOICE-008 records the 0.5 m line and CHOICE-010 the change of question; neither records 0.05. It was chosen knowing the working year's share with no screen is 0.038 (LOOK-016), which sits just under it. The lead is open that the scientist must decide, so this is a gap in the record, not a hidden one.
- The lead gives 2 of 52 as 0.038 with no interval, while its own rule would use an exact binomial interval. By my arithmetic (not in any receipt, and I ran no look for it): the exact 95 per cent interval of 2 in 52 is about 0.005 to 0.132, so the working year itself would be "inconclusive" under the rule. Support needs at least 72 kept passes with no gross error, or about 110 with one. Refutation needs about 7 gross errors in 50 kept passes or 11 in 100, roughly three times the rate of 2024. At a rate near 4 in 100 the interval is about 0.011 to 0.099.
- So the rule can now fail in both directions, which version 1's could not, and that answers REVIEW-001. But the outcome to expect if later data look like 2024 is "inconclusive". The stub says this in words ("this may be more than the later data at one reach can give"); it does not give the counts, and a reader deciding whether to spend the set-aside data needs them.

What would close it: record the one in twenty as a choice with what was known when it was made; put the interval beside 0.038; and have the plan stage state the counts above (from its own receipt) before the held-out data is opened, with the lead's own fallback (further gauged reaches never opened) if they cannot be reached.

### 3. One clause of the headline is contradicted by a receipt (wording, in the headline)

"(3) The size of rise and fall looks within five per cent of the gauge's under every way of leaving passes out, but only as a point estimate when nothing is left out" (`lead.md`, What looks true). LOOK-005 has two other ways of leaving passes out whose interval is also not inside 0.95 to 1.05: leaving out only the unflagged departing pass, and wse_u below 0.2 m only, both 1.0294 [1.0036, 1.0553] ("inside 0.95 to 1.05: False"). So the interval reading fails under three of the eight screens, each one that keeps the pass of 2024-10-30. In the same vein CHOICE-009 says the gain sits within five per cent of one "however passes are left out or terms are added", while LOOK-014 has 1.1149 for the lower half of stage with no screen (and LOOK-009 has 1.0399 at 5 minutes, inside, but only as a point). The point estimates under the eight screens do all sit within five per cent, so the sentence is nearly right; it should say "whenever the pass of 2024-10-30 is kept".

### 4. Rising against falling is quoted in its strongest form (wording)

The lead gives the split at 0.02 m per day: -0.0539 m with a plain standard error of 0.0244 (LOOK-014, screened), about 2.2 standard errors. The same receipt family has the same residuals against the rate itself at -0.0585 m per (m/day) with standard error 0.0389 (LOOK-007, screened), about 1.5, and with no screen the split is -0.0281 (0.0736) and the slope +0.0068 (0.1335). The 0.02 m per day cut is in the script (`looks/look_14_gain_one_footing.py`, lines 49 and 50) and in no choice. The lead does file this under "open explanations, not things seen", which is the right place; among well over a hundred comparisons a 2.2 is not worth more, and the weaker form belongs beside it.

### 5. Small matters of wording and record

- The page is titled version 3 and its first claim paragraph begins "Version 2, written after REVIEW-001".
- "Six two-part rules" (How it was found): two of the six in LOOK-016 are single rules.
- The two gross departures have three sizes in the record depending on the line they are measured from (2024-10-30: 1.699 m in LOOK-016, 1.730 m in LOOK-010, 2.007 m as a level difference in LOOK-012; 2024-03-26: 0.907, 0.947 in LOOK-004, 0.715). The lead uses the LOOK-016 values throughout and says which line; a reader comparing with version 1 or REVIEW-001 ("0.9 m and 1.8 m") should be told once.
- The step "for the lowest third of stage" (2.96 m) and the thirds themselves were cut after LOOK-007 had shown the low-water group sitting low. The lead presents the step as one of four explanations that cannot be told apart, so nothing rests on it.
- Order in the log: the six notes were resolved by `agent:curating-0101` (events 53 to 58) after version 3 was recorded and before any review of it. That is for the coordinating assistant; I did not open the queue and say nothing about the drafts.

## Does the lead now claim only what the looks support

Yes, with the one clause in hole 3. The three things it says look true are counts and fits that are in receipts on all 52 passes or on stated subsets; the gain is no longer claimed to differ from one; four explanations are given as open with their fits side by side; the two gross errors are called satellite departures "which is itself a reading"; the claim is held to one reach, one gauge, one year, one version, and "What this could not show" says it tells nothing about ungauged reaches. Three prerequisites stay open and the lead names them itself: the meaning of the flag (NOTE-005), the gauge's place in the reach (NOTE-006), and a working file with the processing identifier and the bitwise flag (NOTE-001). Until the first is in the knowledge no screen can be written, and so no plan.

## What I did not find

No broken record, no number without a receipt, no number rounded to read better, no look into the set-aside period, no unsigned page presented as signed, no claim to be a finding, and no hole of REVIEW-001 left unaddressed.
