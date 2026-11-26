---
name: write-up-a-lead
description: "Write what an exploration found as a lead: what looks true, how it was found, how many things were tried, the choices that would change it, the pitfalls met, and a proposed plan for a confirming study. Use when an exploration has something worth testing."
---

# Write up a lead

A lead is something that looks true and is worth testing. It is right more often than chance and less often than it feels, because every choice behind it was made after looking. Writing it up honestly is what lets someone else test it. The tool counts what was tried and stamps the lead as exploring; this skill is the procedure for the part only you can write. It carries no facts about any dataset.

## Steps

1. **Check where you stand.** `uv run mvp/loops/explore.py status --exploration <x>`: looks, failures, refusals, choices, open notes.

2. **Write the lead file**, `<x>/lead.yaml`, from `lead-template.yaml` beside this skill. Every key is required.
   - `what_looks_true`: one or two sentences, with the numbers, their units, their counts, and the place and period they come from. Say "looks", not "is". Say where it does not hold as plainly as where it does.
   - `how_it_was_found`: the path you took, including what you tried first and dropped.
   - `evidence`: the looks it rests on, by id. Each must have run without failing. Every number in the lead is in the output of one of them.
   - `choices_that_would_change_it` and `choices_that_would_not`: every choice in the log goes in one list or the other, and the tool refuses a lead that leaves one out. For each one that would change it, say how, with the number from the look that tried the alternative if you ran one. If you did not run the alternative, say so: "not tried" is an answer, and it puts the choice in the first list.
   - `pitfalls`: each pitfall met, with the knowledge page that names it (and whether that page is signed or a draft) or the note you raised.
   - `proposed_plan`: the stub for a confirming study. `question` is one sentence ending in a question mark, about the data that was set aside. `quantity_estimated` is one quantity. `difference_that_matters` is the scientist's number if the request gives one; if it does not, write that nobody has stated one and what you would propose, as a proposal. `rule_sketch` says what result would support the idea, what would refute it, and that anything else is inconclusive. Add `hard_cases` (what the known-answer tests must include, from the pitfalls) and `what_this_could_not_show`.

3. **Record it.** `uv run mvp/loops/explore.py lead --exploration <x> --by <you> --file <x>/lead.yaml`. The tool adds what you cannot be trusted to remember: the count of looks, failures and refusals, the full record of each choice, what was read, what was set aside. It writes `lead.md` and `lead.json`.

4. **Hand it back for review.** Status now names the review assistant. Do not end the exploration yet.

5. **Answer the review.** For each hole: look again, revise the lead and record a new version, or keep the hole in the lead as a stated limit. Then `uv run mvp/loops/explore.py end --exploration <x> --by <you> --outcome lead --summary "<one sentence>"`. A revised lead is reviewed again before it can be handed over.

## What this skill refuses

- The words finding, result, confirmed, validated or shows for what a lead says. A lead looks true.
- A number that is in no look.
- A count of things tried written from memory.
- A proposed question about the data that was explored. The test is on what was set aside.
- Leaving out a choice because it is awkward.
