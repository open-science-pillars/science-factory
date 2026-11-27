---
name: review-work
description: "Check work you did not do: the record first, then every number against a receipt, then the reasoning, then what the knowledge says, and record a verdict with the tool. Use on an exploration's lead, a study's plan or finding, or a queue of drafts."
---

# Review work

A review is by someone who did none of the work, starting from the files, to pick holes, not to agree. This skill carries no facts about any dataset. If you did any part of this work, or were given the reasoning of the agent that did, stop and say so.

**Where you write.** Write the review file in the work's `review/` folder (the exploring tool makes one at the start). `explore.py review` copies it to `verdicts/REVIEW-00N.md` and logs the copy by checksum: the copy is the record, and your file stays as you wrote it. Your account for the coordinating agent goes in `record/review/`, your own place, when the launcher keeps one; in a plain exploration, with no `record/` folder, it goes in the exploration's `review/` folder beside your review file. You never read `record/analysis/`, or any file in `record/` with `analysis` in its name, where the analysis agent's own account is: the harness refuses it, and if you see it by accident you say so and stop, so that a fresh review agent can be started.

## 1. The record

- An exploration: `uv run tools/explore.py check-log --exploration <x>` and `status`. A study: `uv run tools/sf.py check-log --study <s>`, `status`, `scorecard`.
- If the record does not check out, that is the first hole. Do not review numbers that rest on it.

## 2. What is known, read independently

Use the `read-what-is-known` skill on the question before reading what the work says it read. Then compare with the log (`knowledge.read` events, or the plan's citations):

- a page that bears on the question and was not read;
- a pitfall a page warns about that the work walked into, or avoided without saying how;
- a draft or unsigned page leaned on as if it were established;
- a signed page the work contradicts without a note.

## 3. Every number against a receipt

Find each number of the lead, plan or finding in a look's output (`receipts/LOOK-00N.out.txt`) or a run receipt. One in none is a hole; so is one rounded to read better than the receipt. `uv run tools/explore.py recheck --exploration <x> --look LOOK-00N` runs a logged look again, says whether the output is identical, and what was pinned (every file a scratch-folder look was given, by checksum; for an older look, only its script and the files its command names): recheck the looks the lead rests on. To check what a script does, write a variant in `review/` and run it in the look's place with `uv run tools/explore.py recheck --exploration <x> --look LOOK-00N --variant review/<name>.py` (same files, same fence, logged nowhere), and list each variant in your review with what it showed.

## 4. The reasoning

Ask of an exploration's lead:

- **What was set aside**, and does any look, script or data file reach into it? Read the scripts, not only their names.
- **How many things were tried**, and does the claim survive the count? Twenty looks and one striking number is one in twenty.
- **Choices** made in the scripts and never recorded (a filter, a tolerance, a dropped point, a term in a fit: a model's form is a choice). For each recorded choice that "would not change it": was the alternative run, or is that a belief?
- **The order.** The tool's section of the lead on the order of looks and choices: a choice written down after the looks it governs was made knowing what they showed; does the lead treat it so? Were a battery's scripts all there before the first ran?
- **How many comparisons**, not only looks: one look can hold many fits. The lead gives the number declared; read the scripts for the rest.
- **The pictures.** Open the figures in `figures/`, shown or not. A residual pattern the lead does not mention is a hole; so is no figure at all on how one record follows another.
- **The physical question** someone who works with this record would ask first (where the instrument sits, what a flag value means, what the product measures). Did any look ask it?
- **Does a small part of the data carry it?** One point, one season, one flag value.
- **Where does it not hold?** Did the work look, and does the lead say?
- **Is the claim wider than the data**: one place, one period, one version, stated as general?
- **Does the proposed question** ask about the set-aside data, name one quantity, and say what would refute the idea? Can the rule fail at all, at the sizes the lead itself reports? Can it be met by throwing observations away?
- **Words.** Does it call observations "unflagged" when their flag has a value, or an interval anything but a confidence interval with its model named? Would a scientist in the field misread a word?
- **Claims larger than the work.** Read the overclaiming flags (`explore.py status` for a lead, `sf.py scorecard` for a finding) and look for more: "good agreement", "excellent", "clearly", "definitive", "proves", "confirms" when no locked rule gave `supported`, "remarkable", "breakthrough", a dramatic timescale, "significant" with no test, a number finer than its uncertainty. Each that stands is a hole: ask for the number, what it is compared with, and by how much. Your own review is checked the same way.
- **Does it call itself a lead** throughout?

Ask of the fresh data, in an exploration or a study, whether it was chosen fairly and before any look, by the section "When you review" of the skill `propose-fresh-data`: `uv run tools/fresh_data.py check --proposal <the proposal> --studies <the folder of studies> --log <the log>` passes; the kind suits the question; what would make it unfair is named and, as far as the knowledge says, not the case; the size is stated and the claim does not outrun it; the plan holds out exactly what was proposed; the record holds one proposal for the subject, or the others are explained. A plan naming no proposal is a hole: nothing records who chose its fresh data or why.

Ask of a study's plan: `check-plan` passes; the held-out data was never looked at (`explore.py check-study` when the study came from an exploration); the rule can fail; the known-answer tests include the pitfalls. Ask of a finding: every number is in a run receipt and the verdict is the one the locked rule gives; and when `sf.py status` gives the lock a standing other than `verified`, the finding's first line says so.

Ask of a queue of drafts: `uv run tools/knowledge.py check-drafts --queue <q> --wiki <w>` passes; each statement is in its source; one case's numbers are not stated as general; nothing reads as signed; a disagreement with a signed page is declared as `contradicts`.

## 5. Write it and record it

Write the review file in the work's `review/` folder: what you checked, then each hole with where it shows (file and line or event), how much it matters (it would change the lead, limits it, or is wording), and what would close it. Gaps in the knowledge itself go under a heading "For the steward". Then record the verdict:

```
uv run tools/explore.py review --exploration <x> --by <you> --model <your model> --verdict holes-found --file <x>/review/<name>.md \
  --read-lead <lead_json_sha256, as `explore.py status` printed it when you began>
uv run tools/sf.py review --study <s> --by <you> --model <your model> --verdict block --file <s>/review/<name>.md
```

`no-holes-found` and `approve` say you looked and found none; the file still says what you checked. For an exploration `<you>` is the name the coordinating agent named as reviewer before the lead; the tool refuses any other. Your verdict covers the lead as it stands, and a later correction brings it back to you.

## What this skill refuses

- Fixing the work, running new looks in the exploration (a variant run with `recheck --variant` is a check, listed in the review), or rewriting the lead.
- A verdict with no file, or a file with no pointers into the record.
- Reviewing from the author's summary, or reading the author's account of the work at all.
