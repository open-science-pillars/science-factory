---
name: write-up-a-lead
description: "Write what an exploration found as a lead: what looks true, how it was found, how many things were tried, the choices that would change it, the pitfalls met, and a proposed plan for a confirming study. Use when an exploration has something worth testing."
---

# Write up a lead

A lead is something that looks true and is worth testing. It is right more often than chance and less often than it feels, because every choice behind it was made after looking. Writing it up honestly is what lets someone else test it. The tool counts what was tried and stamps the lead as exploring; this skill is the procedure for the part only you can write. It carries no facts about any dataset.

## Steps

1. **Check where you stand.** `uv run mvp/loops/explore.py status --exploration <x>`: looks, failures, refusals, choices, open notes.

2. **Write the lead file**, `<x>/lead.yaml`, from `lead-template.yaml` beside this skill. Seven keys are required and three more may be added.
   - `what_looks_true`: a short paragraph, with the numbers, their units, their counts, and the place and period they come from. Say "looks", not "is".
   - `what_does_not_hold` (optional): what a reader might expect that the looks do not bear out, and what an earlier version claimed that this one withdraws. Give it its own key so that a cut-back is easy to find and hard to skip.
   - `open_explanations` (optional): what could explain what was seen and was not settled. An explanation is not a thing seen; keep it out of `what_looks_true`.
   - `figures` (optional): `{file: figures/<name>.svg, shows: "<what the picture shows>"}` for each picture the lead should show. The file must be one a look you cite drew.
   - `how_it_was_found`: the path you took, including what you tried first and dropped.
   - `evidence`: the looks it rests on, by id. Each must have run without failing. Every decimal number in the lead's own words was printed by one of them, whole and digit for digit, or stands in a knowledge page you recorded as read. Quote numbers as they were printed: a rounded number is refused, and so is one that is only part of a longer printed number. Whole numbers, ratios in words and the numbers of the proposed plan are not checked by the tool, which is a reason to take more care with them, not less.
   - `choices_that_would_change_it` and `choices_that_would_not`: every choice in the log goes in one list or the other, and the tool refuses a lead that leaves one out. For each one that would change it, say how, with the number from the look that tried the alternative if you ran one. If you did not run the alternative, say so: "not tried" is an answer, and it puts the choice in the first list. A choice about the write-up or the proposed test, made after looking, belongs in the log and in the first list too. The tool adds to each choice how many looks had run when it was written down; do not argue with that in words.
   - `pitfalls`: each pitfall met, with the knowledge page that names it (and whether that page is signed or a draft) or the note you raised.
   - `proposed_plan`: the stub for a confirming study. `question` is one sentence ending in a question mark, about the data that was set aside. `quantity_estimated` is one quantity. `difference_that_matters` is the scientist's number if the request gives one; if it does not, write that nobody has stated one and what you would propose, as a proposal. `rule_sketch` says what result would support the idea, what would refute it, and that anything else is inconclusive. Add `hard_cases` (what the known-answer tests must include, from the pitfalls) and `what_this_could_not_show`. Other keys of your own are allowed in the stub (`prerequisites`, for what must be in the knowledge before a plan can be written) and are rendered as they are. Ask of the rule: can it fail, and can it be met by throwing observations away? A rule on a share of kept observations needs a floor on how many are kept.

3. **Record it.** `uv run mvp/loops/explore.py lead --exploration <x> --by <you> --file <x>/lead.yaml`. The tool adds what you cannot be trusted to remember: the count of looks, failures and refusals, the comparisons the looks declared, the full record of each choice and when it was written down, the order of looks and choices, what was read and what was listed and not read, what was set aside and what is in neither. It writes `lead.md` and `lead.json`.

4. **Hand it back for review, and answer the review.** For each hole: look again, revise the lead and record a new version, or keep the hole in the lead as a stated limit.

   **When to end.** After `explore.py lead`, do not call `end`: status names the review assistant, and you stop. When the review comes back, answer it; a revised lead is a new version and is reviewed again. Call `end --outcome lead` only when the latest lead has been reviewed and you will not revise it further; the tool refuses it earlier. An exploration with no lead ends when you choose, as a note, a method or a stop.

   The command, when its time comes: `uv run mvp/loops/explore.py end --exploration <x> --by <you> --outcome lead --summary "<one sentence>"`.

5. **Put a slip of wording right without a new version.** `uv run mvp/loops/explore.py correct --exploration <x> --by <you> --old "<the words as they stand>" --new "<the words to put there>" --why "<why>"`. The old words must stand in the lead exactly once, no number may change, and the lead then shows the old and the new words under "Corrections of wording". Bring `lead.yaml` in line by hand so a later version starts from the corrected words. Anything that changes a number or what the lead claims is a new version.

## What this skill refuses

- The words finding, result, confirmed, validated or shows for what a lead says. A lead looks true.
- Words that mislead the person the lead is for. The tool refuses "sampling interval" for a confidence interval (to a hydrologist a sampling interval is the time between samples) and "unflagged" or "not flagged" for observations whose flag has a value (say the value, and say so when nothing in the record is at the clean value). Define once any word a field scientist would not use your way: gain is the rise of one record per unit rise of the other.
- A number that is in no look.
- A count of things tried written from memory.
- A proposed question about the data that was explored. The test is on what was set aside.
- Leaving out a choice because it is awkward.
