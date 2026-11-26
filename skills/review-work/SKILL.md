---
name: review-work
description: "Check work you did not do: the record first, then every number against a receipt, then the reasoning, then what the knowledge says, and record a verdict with the tool. Use on an exploration's lead, a study's plan or finding, or a queue of drafts."
---

# Review work

A review is by someone who did none of the work and starts from the files. Its job is to pick holes, not to agree. This skill is the procedure. It carries no facts about any dataset.

If you did any part of this work, or were given the reasoning of the assistant that did, stop and say so.

## 1. The record

- An exploration: `uv run mvp/loops/explore.py check-log --exploration <x>` and `status`. A study: `uv run mvp/sf.py check-log --study <s>`, `status`, `scorecard`.
- If the record does not check out, that is the first hole. Do not review numbers that rest on it.

## 2. What is known, read independently

Use the `read-what-is-known` skill on the question before reading what the work says it read. Then compare with the log (`knowledge.read` events, or the plan's citations):

- a page that bears on the question and was not read;
- a pitfall a page warns about that the work walked into, or avoided without saying how;
- a draft or unsigned page leaned on as if it were established;
- a signed page the work contradicts without a note.

## 3. Every number against a receipt

For each number in the lead, the plan or the finding: find it in a look's output (`receipts/LOOK-00N.out.txt`) or a run receipt. A number that is in none is a hole. A number that is rounded so it reads better than the receipt is a hole. For an exploration, `uv run mvp/loops/explore.py recheck --exploration <x> --look LOOK-00N` runs a logged look again in a copy and says whether the output is identical; recheck the looks the lead rests on.

## 4. The reasoning

Ask of an exploration's lead:

- **What was set aside**, and does any look, script or data file reach into it? Read the look scripts, not only their names.
- **How many things were tried**, and does the lead's claim survive that count? Twenty looks and one striking number is one in twenty.
- **Choices**: read the scripts for choices that were made and never recorded (a filter, a tolerance, a dropped point). For each recorded choice that "would not change it": was the alternative run, or is that a belief?
- **Does a small part of the data carry it?** One point, one season, one flag value.
- **Where does it not hold?** Did the work look, and does the lead say?
- **Is the claim wider than the data**: one place, one period, one version, stated as general?
- **Does the proposed question** ask about the set-aside data, name one quantity, and say what would refute the idea?
- **Does it call itself a lead** throughout?

Ask of a study's plan: `check-plan` passes; the held-out data was never looked at (`explore.py check-study` when the study came from an exploration); the rule can fail; the known-answer tests include the pitfalls. Ask of a finding: every number is in a run receipt and the verdict is the one the locked rule gives.

Ask of a queue of drafts: `uv run mvp/loops/knowledge.py check-drafts --queue <q> --wiki <w>` passes; each statement is in its source; one case's numbers are not stated as general; nothing reads as signed; a disagreement with a signed page is declared as `contradicts`.

## 5. Write it and record it

Write the review file in the work's `review/` folder: what you checked, then each hole with where it shows (file and line or event), how much it matters (it would change the lead, it limits it, or it is a matter of wording), and what would close it. Then record the verdict with the tool:

```
uv run mvp/loops/explore.py review --exploration <x> --by <you> --verdict holes-found --file <x>/review/<name>.md
uv run mvp/sf.py review --study <s> --by <you> --verdict block --file <s>/review/<name>.md
```

`no-holes-found` and `approve` say that you looked and found none, and the file still says what you checked.

## What this skill refuses

- Fixing the work, running new looks, or rewriting the lead.
- A verdict with no file, or a file with no pointers into the record.
- Reviewing from the author's summary.
