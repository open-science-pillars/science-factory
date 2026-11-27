# The stand-alone example

**Runs from a bare clone, with nothing beside it, and makes its run fresh every time.**

```
uv run examples/stand-alone/run.py
```

It ends with `stand-alone example: PASS (N of N steps)` in about three minutes and prints the path of a scratch folder outside the repository holding what it made; nothing is written into the repository. Look, then delete it, or run with `--remove`.

| In the scratch folder | What it is |
|---|---|
| `explorations/EXPLORATION-A/` | the exploration: `fresh-data.yaml` (the proposal of the fresh data), `exploration-log.jsonl`, `set-aside.json`, `looks/` and `receipts/`, `figures/`, `notes/`, `lead.md`, `review/` and `verdicts/`, `so-what/` (the question put to a person), `contribution.md` (who did what), and `hand-over/` (the request, a plan stub, a copy of the proposal, the figures) |
| `studies/STUDY-A/` | a study started from that hand-over, at the plan stage, holding the exploration's figures |
| `studies/STUDY-B/` | a system trial taken through its tests: its plan, log, receipts, a rehearsal figure, `lock-request/` (what a person would approve, the figure among it), a practice lock and `contribution.md` |
| `factory-copy/` | a scratch copy of the definition, with `methods/gain-with-intercept/` promoted from a look and recorded in its change log |
| `studies/openings.jsonl`, `studies/held-out.jsonl`, `studies/fresh-data.jsonl` | the records beside the studies: what was set aside and opened, every held-out block a study declared, every proposal of fresh data |
| `knowledge-queue/` | one drafted page waiting for a person, with the queue's index |
| `judging/` | two judging packets: what a model judge would be given for the review of the lead and for STUDY-B's plan. No model was asked |
| `data/`, `request.md`, `review.md` | the record, the request the exploration began with, and the review of its lead |

**What it has.** `record-2024.json`, a synthetic two-sensor record, a row a week, made by `make_record.py` from a fixed seed with a gain of 1.03 put in; `metadata.yaml`, what it and 2025 hold, as metadata only; `looks/gain.py`; `system-trial/analysis-plan.yaml`; and `run.py`. It reads the wiki `openwiki/`.

**What the run does, in order.**

1. Checks that the definition is valid, and that an agent that names no model is refused.
2. Reads the wiki, and only the wiki.
3. Proposes the fresh data from the metadata (the record's own data file, offered instead, is refused), starts the exploration setting aside exactly that, the year 2025, and writes a fit note.
4. Looks, and is refused each look that reaches for the set-aside year, by any of the routes the fence closes; draws a figure; records a choice and a note.
5. Writes the lead, and is refused a lead before a reviewer is named, a number no look printed, and words that mislead; corrects one phrase; is refused a review by the agent that explored, or under a name nobody named; a review that says "clearly" is flagged by the overclaiming check.
6. Asks a person so what: an agent drafts the question and is refused the answer; a practice so what says try instead, then worth confirming.
7. Hands over (the proposal and the figures go with it), starts a study, and checks that the study keeps the fence.
8. Promotes `looks/gain.py` to a method in a scratch copy of the definition: its tests reproduce both looks, and the validator refuses it until the change log records it.
9. Writes who did what, drafts a page into a queue for the wiki carrying it, and builds two judging packets.
10. Takes a system trial through its tests (with a figure) to a lock request that shows the fit note and the figure, shows the three standings an act can have, and records a practice lock.

Each step prints its refusals. **Practice at the end**, because a scratch folder has no pull request to merge; a practice study never closes as signed. The pull request route is tested in `tools/sf.py selftest` and `factory/harnesses/github/record_act.py --selftest`, in a throwaway git repository.

**It shows** that the loops hold together, the refusals refuse, and the exploring comes within 0.02 of the gain put in once degraded readings are left out (`lead.md` has both numbers). **It does not show** anything about agents (no language model runs) or past the lock.
