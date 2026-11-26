---
name: review-work
description: "Check work you did not do: the record first, then every number against a receipt, then the reasoning, then what the knowledge says, and record a verdict with the tool. Use on an exploration's lead, a study's plan or finding, or a queue of drafts."
---

# Review work

A review is by someone who did none of the work and starts from the files. Its job is to pick holes, not to agree. This skill is the procedure. It carries no facts about any dataset.

If you did any part of this work, or were given the reasoning of the assistant that did, stop and say so.

**Where you write.** Write the review file in the work's `review/` folder (the exploring tool makes one at the start). `explore.py review` copies it to `verdicts/REVIEW-00N.md` and logs the copy by checksum: the copy is the record, and your file stays as you wrote it. Your account for the coordinating assistant goes in `record/review/`, your own place. You never read `record/analysis/`, or any file in `record/` with `analysis` in its name, where the analysis assistant's own account is: the harness refuses it, and if you see it by accident you say so and stop, so that a fresh review assistant can be started.

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

For each number in the lead, the plan or the finding: find it in a look's output (`receipts/LOOK-00N.out.txt`) or a run receipt. A number that is in none is a hole. A number that is rounded so it reads better than the receipt is a hole. For an exploration, `uv run tools/explore.py recheck --exploration <x> --look LOOK-00N` runs a logged look again and says whether the output is identical, and what was pinned: for a look that ran in a scratch folder, every file it was given, by checksum; for a look logged before that, only its script and the files its command names. Recheck the looks the lead rests on.

## 4. The reasoning

Ask of an exploration's lead:

- **What was set aside**, and does any look, script or data file reach into it? Read the look scripts, not only their names.
- **How many things were tried**, and does the lead's claim survive that count? Twenty looks and one striking number is one in twenty.
- **Choices**: read the scripts for choices that were made and never recorded (a filter, a tolerance, a dropped point, a term in a fit: the form of the model is a choice). For each recorded choice that "would not change it": was the alternative run, or is that a belief?
- **The order.** The lead has a section, written by the tool from the log, on the order of looks and choices. A choice written down after the looks it governs was made knowing what they showed; does the lead treat it so? Were the scripts of a battery of looks all there before the first ran?
- **How many comparisons**, not only how many looks: one look can hold many fits. The lead gives the number the looks declared; read the scripts for the rest.
- **The pictures.** Open the figures in `figures/`, the ones the lead shows and the ones it does not. A pattern in a residual plot that the lead does not mention is a hole. No figure at all, on a question about how one record follows another, is a hole.
- **The physical question.** What would someone who works with this kind of record ask first (where the instrument sits, what a flag value means, what the product is a measurement of)? Did any look ask it?
- **Does a small part of the data carry it?** One point, one season, one flag value.
- **Where does it not hold?** Did the work look, and does the lead say?
- **Is the claim wider than the data**: one place, one period, one version, stated as general?
- **Does the proposed question** ask about the set-aside data, name one quantity, and say what would refute the idea? Can the rule fail at all, at the sizes the lead itself reports? Can it be met by throwing observations away?
- **Words.** Does it call observations "unflagged" when their flag has a value, or an interval anything but a confidence interval with its model named? Would a scientist in the field misread a word?
- **Does it call itself a lead** throughout?

Ask of the fresh data, in an exploration and in a study: was it chosen fairly, and before any look? Follow the section "When you review" of the skill `propose-fresh-data`: `uv run tools/fresh_data.py check --proposal <the proposal> --studies <the folder of studies> --log <the log>` passes; the kind suits the question; what would make it unfair is named and is not the case as far as the knowledge says; the size is stated and the claim does not outrun it; the plan holds out exactly what was proposed; and the record holds one proposal for the subject, or the others are explained. A plan that names no proposal is a hole: nothing records who chose its fresh data or why.

Ask of a study's plan: `check-plan` passes; the held-out data was never looked at (`explore.py check-study` when the study came from an exploration); the rule can fail; the known-answer tests include the pitfalls. Ask of a finding: every number is in a run receipt and the verdict is the one the locked rule gives; and when `sf.py status` gives the lock a standing other than `verified`, the finding's first line says so.

Ask of a queue of drafts: `uv run tools/knowledge.py check-drafts --queue <q> --wiki <w>` passes; each statement is in its source; one case's numbers are not stated as general; nothing reads as signed; a disagreement with a signed page is declared as `contradicts`.

## 5. Write it and record it

Write the review file in the work's `review/` folder: what you checked, then each hole with where it shows (file and line or event), how much it matters (it would change the lead, it limits it, or it is a matter of wording), and what would close it. Put gaps in the knowledge itself, as against holes in the work, under a heading "For the steward". Then record the verdict with the tool:

```
uv run tools/explore.py review --exploration <x> --by <you> --model <your model> --verdict holes-found --file <x>/review/<name>.md \
  --read-lead <lead_json_sha256, as `explore.py status` printed it when you began>
uv run tools/sf.py review --study <s> --by <you> --model <your model> --verdict block --file <s>/review/<name>.md
```

`no-holes-found` and `approve` say that you looked and found none, and the file still says what you checked. For an exploration, `<you>` is the name the coordinating assistant named as reviewer before the lead was recorded; the tool refuses any other. Your verdict covers the lead as it stands: if its wording is corrected afterwards, it comes back to you.

## What this skill refuses

- Fixing the work, running new looks, or rewriting the lead.
- A verdict with no file, or a file with no pointers into the record.
- Reviewing from the author's summary, or reading the author's account of the work at all.
