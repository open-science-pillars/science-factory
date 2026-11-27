---
name: write-up-a-lead
description: "Write what an exploration found as a lead: what looks true, how it was found, how many things were tried, the choices that would change it, the pitfalls met, and a proposed plan for a confirming study. Use when an exploration has something worth testing."
---

# Write up a lead

A lead is something that looks true and is worth testing: right more often than chance and less often than it feels, because every choice behind it was made after looking. Writing it up honestly lets someone else test it. The tool counts what was tried and stamps the lead as exploring; this skill is the part only you can write, and carries no facts about any dataset.

## Steps

1. **Check where you stand.** `uv run tools/explore.py status --exploration <x>`: looks, failures, refusals, choices, open notes.

2. **Write the lead file**, `<x>/lead.yaml`, from `lead-template.yaml` beside this skill. Eight keys are required and three more may be added.
   - `summary`: the lead in a minute, for whoever says so what: `looks_true`, `how_strong` and `cannot_settle`, a sentence or two each, under 150 words in all. The tool puts it atop `lead.md` and checks its numbers. Write it last, claiming no more than the lead.
   - `what_looks_true`: a short paragraph with the numbers, units, counts, and the place and period. Say "looks", not "is".
   - `what_does_not_hold` (optional): what a reader might expect that the looks do not bear out, and what an earlier version claimed that this one withdraws, under its own key so a cut-back is easy to find and hard to skip.
   - `open_explanations` (optional): what could explain what was seen and was not settled; an explanation is not a thing seen, so keep it out of `what_looks_true`.
   - `figures` (optional): `{file: figures/<name>.svg, shows: "<what the picture shows>"}` per picture, drawn by a look you cite.
   - `how_it_was_found`: the path you took, including what you tried first and dropped.
   - `evidence`: the looks it rests on, by id, each run without failing. Every decimal number in the lead's own words was printed by one of them, whole and digit for digit, or stands in a page of a listed wiki you recorded as read; your own page, a queued draft or a file outside every listed wiki backs nothing. Quote numbers as printed: a rounded number is refused, and so is one that is part of a longer printed number or written another way (a decimal comma, an exponent, a missing zero, a unit glued on). A whole number given as a share (`5 percent`, `5%`) must have been printed too. In the method's words (`how_it_was_found`, the choices, the pitfalls) a listed constant (1.645, 1.96, 2.576, 0.05, 0.01, 0.95, 0.99, and 90, 95 or 99 percent) and a count with a thousands comma (5,000 draws) need no receipt; where the lead says what looks true they do. A sentence of the proposed plan that names a look (LOOK-007) quotes it, and its every number must be one that look printed, so put a proposed number in a sentence of its own. Other whole numbers, numbers and ratios in words, and the plan's proposed numbers are not checked, which is a reason for more care, not less.
   - `choices_that_would_change_it` and `choices_that_would_not`: every logged choice goes in one list, and a lead that leaves one out is refused. For each that would change it, say how, with the number from the look that tried the alternative if one ran; "not tried" is an answer and puts the choice in the first list. A choice about the write-up or proposed test made after looking belongs in the log and the first list too. The tool adds how many looks had run when each was written down; do not argue with that in words.
   - `pitfalls`: each pitfall met, with the page that names it (signed or a draft) or the note you raised.
   - `proposed_plan`: the stub for a confirming study. `question`: one sentence ending in a question mark, about the set-aside data. `quantity_estimated`: one quantity. `difference_that_matters`: the scientist's number if the request gives one, otherwise that nobody has stated one and what you propose, as a proposal. `rule_sketch`: what would support the idea, what would refute it, and that anything else is inconclusive. Add `hard_cases` (what the known-answer tests must include, from the pitfalls) and `what_this_could_not_show`. Keys of your own are allowed and rendered as they are (`prerequisites`, for what the knowledge must hold before a plan can be written). Ask of the rule: can it fail, and can it be met by throwing observations away? A rule on a share of kept observations needs a floor on how many are kept.

   **Say no more than the looks show.** Not "good agreement", "excellent", "clearly", "definitive", "proves", "confirms" (a lead is tested on nothing), "remarkable", "breakthrough", a dramatic timescale ("years of work"), "significant" without its test, or a number to more decimals than its uncertainty supports. Give the number, what it is compared with, and by how much. The overclaiming check (`factory/scorers/overclaiming-in-leads/phrases.yaml`) flags these by line when you record the lead; it warns, does not refuse, and a reviewer and a person read the flags.

3. **Record it.** `uv run tools/explore.py lead --exploration <x> --by <you> --model <your model> --file <x>/lead.yaml`, refused until the coordinating agent has named the reviewer (`status` shows `before_a_lead`): hand back for that, you do not name one. The tool adds what you cannot be trusted to remember (the counts of looks, failures, refusals and declared comparisons, each choice and when it was written down, the order of looks and choices, what was read and what listed and not read, what was set aside and what is in neither) and writes `lead.md` and `lead.json`.

4. **Hand it back for review, and answer the review.** For each hole: look again, revise the lead and record a new version, or keep the hole in the lead as a stated limit.

   **When to end.** After `explore.py lead`, do not call `end`: status names the review agent, and you stop. When the review comes back, answer it; a revised lead is a new version and is reviewed again, and so is a lead whose wording was corrected after its review. Call `end --outcome lead` only when the lead as it stands has been reviewed, a person has said it is worth confirming (`status` shows their so what), and you will not revise it further; the tool refuses it earlier. If the person says try instead, their direction is your next question: explore it and write a new version. You never record a so what. An exploration with no lead ends when you choose, as a note, a method or a stop.

   The command, when its time comes: `uv run tools/explore.py end --exploration <x> --by <you> --model <your model> --outcome lead --summary "<one sentence>"`.

5. **Put a slip of wording right without a new version.** `uv run tools/explore.py correct --exploration <x> --by <you> --model <your model> --old "<the words as they stand>" --new "<the words to put there>" --why "<why>"`. The old words must stand exactly once, no number may change, and the lead shows old and new under "Corrections of wording"; bring `lead.yaml` in line by hand. Anything that changes a number or the claim is a new version. A correction after a review undoes it, whatever it changes (the tool cannot tell a slip from a stronger claim), so the lead goes back to the reviewer before the exploration can end on it or be handed over.

## What this skill refuses

- The words finding, result, confirmed, validated or shows for what a lead says. A lead looks true.
- Words that mislead the person the lead is for. The tool refuses "sampling interval" for a confidence interval (to a hydrologist a sampling interval is the time between samples) and "unflagged" or "not flagged" for observations whose flag has a value (say the value, and say so when nothing in the record is at the clean value). Define once any word a field scientist would not use your way: gain is the rise of one record per unit rise of the other.
- A number that is in no look.
- A count of things tried written from memory.
- A proposed question about the data that was explored. The test is on what was set aside.
- Leaving out a choice because it is awkward.
