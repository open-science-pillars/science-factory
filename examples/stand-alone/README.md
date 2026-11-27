# The stand-alone example

**Runs from a bare clone, with nothing beside it, and makes its run fresh every time.**

```
uv run examples/stand-alone/run.py
```

It ends with `stand-alone example: PASS (N of N steps)` in about three minutes, most of it the known-answer tests of its last part. At the end it prints the path of a scratch folder outside the repository and what is in it. Nothing is written into the repository. Open the folder to see what the work looks like on disk, then delete it, or run with `--remove` to have the run delete it.

| In the scratch folder | What it is |
|---|---|
| `explorations/EXPLORATION-A/` | the exploration: `fresh-data.yaml` (the proposal of the fresh data), `exploration-log.jsonl`, `set-aside.json`, `looks/` and `receipts/`, `figures/`, `notes/`, `lead.md`, `review/` and `verdicts/`, and `hand-over/` (the request, a plan stub and a copy of the proposal) |
| `studies/STUDY-A/` | a study started from that hand-over, at the plan stage |
| `studies/STUDY-B/` | a system trial taken through its tests: its plan, log, receipts, `lock-request/` (what a person would approve), and a practice lock |
| `studies/openings.jsonl`, `studies/held-out.jsonl`, `studies/fresh-data.jsonl` | the records beside the studies: what was set aside and opened, every held-out block a study declared, every proposal of fresh data |
| `knowledge-queue/` | one drafted page waiting for a person, with the queue's index |
| `judging/` | two judging packets: what a model judge would be given for the review of the lead and for STUDY-B's plan. No model was asked |
| `data/`, `request.md`, `review.md` | the record, the request the exploration began with, and the review of its lead |

**What it has.** `record-2024.json`, a synthetic two-sensor record, one row a week, made by `make_record.py` from a fixed seed, with a gain of 1.03 put in by hand; `metadata.yaml`, what that record holds and what 2025 will hold, as metadata only; `looks/gain.py`, the one look script; `system-trial/analysis-plan.yaml`, a system trial's plan; and `run.py`, the run. The wiki it reads is `openwiki/` at the top of the repository.

**What the run does, in order.**

1. Checks that the definition is valid, and that an agent that names no model is refused.
2. Reads the wiki, and only the wiki.
3. Proposes the fresh data from the metadata (the record's own data file, offered instead, is refused), and starts the exploration setting aside exactly that: the year 2025.
4. Looks, and is refused each look that reaches for the set-aside year, by any of the routes the fence closes; draws a figure; records a choice and a note.
5. Writes the lead, and is refused a lead before a reviewer is named, a number no look printed, and words that mislead; corrects one phrase; is refused a review by the agent that explored, or under a name nobody named.
6. Hands over (the proposal goes with it), starts a study, and checks that the study keeps the fence.
7. Drafts a page into a queue for the wiki, and builds two judging packets.
8. Takes a system trial through its tests to a lock request, shows the three standings an act can have, and records a practice lock.

Each step's refusals are printed in the run's own output.

**Why practice mode at the end.** The scratch folder is no repository, so there is no pull request to merge. A practice lock says of itself that it is practice, and its study can never close as a signed finding. The pull request route is tested in `tools/sf.py selftest` and `factory/harnesses/github/record_act.py --selftest`, in a throwaway git repository.

**What it shows.** That the loops hold together and the refusals refuse; and that the exploring comes within 0.02 of the gain that was put in once the degraded readings are left out (`lead.md` has both numbers). **What it does not show.** Anything about agents (no language model runs in it), and nothing past the lock.
