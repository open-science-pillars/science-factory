# Review of the lead, version 1 (exploring)

**Who reviewed, said plainly.** This review was made through the by-hand runner by the same model instance that did the exploring, in the same conversation, acting under the review role's name and limited to the review role's commands. It is not an independent review and it had no fresh context. The tool cannot tell: it checks the name. Read every "I checked" below as the author checking their own work against the record with the review checklist.

## What was checked

- `explore.py check-log`: passes, 44 events.
- The knowledge, listed again without looking at what the work read: the same eight pages. A second search by gauge words finds two signed pages the work did not read (hole 6).
- Every number in the lead against a look's output. All are there to the digit.
- `explore.py recheck` on LOOK-012, 014, 018, 020, 022 and 023: each reproduces identically.
- The look scripts, read line by line, for choices that were made and not recorded.
- The fence: the three scripts read only the file named on the command line, the only data file named in any look is the 2024 fixture, and no look was refused. Nothing reaches the set-aside window.

## Holes

**1. The lead explored one processing baseline and proposes to test on another, and never checked the first. It would change the lead.** The set-aside window starts where forward processing starts, so the proposed study differs from 2024 in two ways at once: the year and the processing. The lead's `what_this_could_not_show` does not say so. And "2024 is all reprocessed" comes only from the knowledge: the fixture carries no processing identifier for any pass (`confront-screened.json`, `processing_identifiers.passes_with_one: 0`), so no look could check it and none tried. To close: say in the lead that 2024 is taken to be one baseline on the knowledge's word, that the fixture cannot show it, and that a result on the later window cannot separate a change in the relation from a change in processing.

**2. "Where it does not follow: the three flagged passes" rests on one pass. It limits the lead.** LOOK-005 gives the three flagged departures as a minimum of -1.776 m and a median of -0.084 m with a maximum of -0.080 m: two of the three sit 0.08 m from the rest, which is ordinary (the unflagged spread is 0.162 m). The evidence that the flag marks bad passes is a single pass. The screen may still be the right choice (the signed dataset page says the flag is a gate), but the lead should say the 2024 evidence for it is one pass in three.

**3. "All at low stage" is not what the looks show. Wording, but it is in a note too.** LOOK-006 puts two flagged pairs in the lowest third of stage and one in the middle third (gauge 3.51 m, where the middle third runs 2.96 to 6.32 m). NOTE-001 repeats "all fall at low stage". To close: say "the lower half", or give the three stages.

**4. Every spread in the lead is a population standard deviation, and the lead does not say so. It limits the lead; it matters for the group of three.** `looks/pairs.py` uses `statistics.pstdev`. That is why LOOK-003 prints a level spread of 0.298 m where the recipe's own receipt has 0.3009, and LOOK-013 a gauge change spread of 1.1836 m where the recipe has 1.1959 m, so "reproduced its scores" is true of the correlation and the RMSD and not of the spread. For 47 or 50 pairs the difference is one percent. For the three flagged pairs it is not: 0.798 m becomes about 0.98 m. To close: say which it is, or print the sample value.

**5. The "where" results are single passes found after cutting the same 50 pairs six ways. It limits the lead.** By size, by flag, by stage, by dark fraction, by limb, by stated uncertainty: 24 looks. That one pass in each of two cuts stands out is what cutting 50 points six ways tends to produce. The lead's statement about the gain does not depend on them, but its two "where it does not" items are two observations, and CHOICE-005 is right not to build a threshold on one. The lead should call them two passes, by date, and not a pattern.

**6. Two signed pages on the gauge side were not read. It limits the lead.** `gotchas/nwis-provisional-data.md` and `gotchas/nwis-regulated-gauge.md`, both signed, did not come up for the question's words and do come up for "gauge provisional". The lead mentions provisional values from the recipe; the provisional page adds that such values can be revised or withdrawn, which bears on a test that would be run on a later, also provisional, window.

**7. The low-stage offset is in the looks and not in the lead. Wording.** LOOK-022: the lowest third of stage has a median departure of -0.091 m against +0.027 and +0.023 m for the other thirds. That is what a gain of 1.012 over a 8.9 m range gives (about 0.11 m end to end), so it is the gain seen another way and not a second effect, but "low water by itself does not look like the problem" reads as if nothing happens there.

**8. The gain model's time term comes out at -0.124 m per year (LOOK-020) and the lead is silent on it. Wording.** One year cannot tell a drift from the seasonal cycle. Say so, since the proposed quantity keeps the term.

**9. Unrecorded choices in the scripts. Minor.** Thirds as the bins (16, 16 and 18 pairs by integer division) and "nearest reading" as the pairing rule inside the tolerance are choices. The second is the recipe's; the first is harmless here but is a choice made after looking at where the flagged passes fell.

## What was looked for and not found

No number without a look. No look or script that reaches the set-aside window. No signed page contradicted. The proposed question is about the set-aside data, names one quantity and says what would refute the idea. The lead calls itself a lead throughout.

## Verdict

Holes found. None says the lead is wrong; 1 would change what it claims a test could show, and 2, 4 and 5 change how firmly the "where it does not" half can be said.
