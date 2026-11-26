# The stand-alone example

**Runs from a bare clone with nothing beside it, and makes its run fresh every time.**

```
uv run examples/stand-alone/run.py
```

It ends with `stand-alone example: PASS (37 of 37 steps)`, in two to three minutes after the first download of PyYAML (most of that is the known-answer tests of its last part). A warning the launcher prints on standard error does not disturb it: the run reads a tool's answer from what the tool prints, and one of its steps tests that.

**What you will see.** While it runs, nothing. At the end it prints the path of a scratch folder outside the repository (under the system's temporary folder), a short list of what is in it, and the line above. Nothing is written into the repository, and nothing it makes is kept by git. Open the folder to see what the two kinds of work look like on disk:

| In the scratch folder | What it is |
|---|---|
| `explorations/EXPLORATION-A/` | an exploration: `exploration-log.jsonl` (every step, chained by hash), `set-aside.json` (what was not looked at), `looks/` and `receipts/` (each look's script and its record), `figures/`, `notes/`, `lead.md` (what was found, with the order of looks and choices), `review/` and `verdicts/`, `hand-over/` (the request a study starts from) |
| `studies/STUDY-A/` | a study started from that hand-over, at the plan stage: `study-log.jsonl`, `request.md`, a plan |
| `studies/STUDY-B/` | a study taken through its tests: `analysis-plan.yaml`, `study-log.jsonl`, `receipts/` (the known-answer tests, the working data, the rehearsal), standing at the lock |
| `studies/openings.jsonl` | the record of what has been set aside and opened, beside the studies |
| `knowledge-queue/` | one drafted knowledge page waiting for a person, with the queue's index |
| `data/`, `request.md` | the synthetic record and the request the exploration began with |

Delete the folder when you have looked, or run with `--remove` to have the run delete it.

**What it has.**

- `record-2024.json`: a synthetic two-sensor record, one row a week, made by `make_record.py` from a fixed seed. The answer is known because it was put in by hand: a gain of 1.03, an offset of 0.40 m, noise of 0.05 m, two readings flagged degraded of which one is 2 m off.
- `openwiki/` at the top of the repository: the knowledge base, a wiki in OpenWiki's form (the Open Knowledge Format v0.2) with three pages and a quickstart. None is signed.
- `looks/gain.py`: the one look script.
- `skills/explore-a-record/scripts/plot_xy.py`, from the exploring skill: the script that draws the one figure.
- `system-trial/analysis-plan.yaml`: the plan of a system trial on a synthetic record, with this repository's own method. The run copies it into `STUDY-B`.
- `run.py`: the run.

**What the run does, in order.** It reads the wiki, and only the wiki, then sets the following year aside and records the page the boundary came from. It is refused a look before the knowledge is listed and again before a page is recorded as read, looks twice, is refused a look at the set-aside year (named as a file, through its folder, through a pattern and after an `=`), draws a figure of the residual and has it logged by checksum, records a choice and a note, is refused a lead until the coordinating name has named the reviewer, is refused a lead that quotes a number no look printed and one that calls flagged readings unflagged, records the lead with its figure and the order of looks and choices, corrects one phrase without a new version, is refused an end before the review and a resolved note before the end, is refused a review by the assistant that explored and one under a name nobody named, is refused an end after a correction made since the review until the corrected lead is reviewed, hands over, starts a study with the study tool, checks that the study keeps the fence and that one holding out the explored year is refused, drafts a page into a queue, is refused until the draft says how it relates to the wiki page it overlaps, is refused when the draft is marked as signed, and finds the draft again, as a draft, for a second question. Then the confirming loop as far as a tool can take it: a second study is started on the system trial's plan, its opening is refused before the lock, its known-answer tests, its working data and its rehearsal pass, and it stands at the stage `lock`. The lock is a person's act, and the run checks that the tool refuses it to an assistant.

**What it shows.** That the loops hold together and the refusals refuse; that the exploring comes within 0.02 of the gain that was put in once the degraded readings are left out (1.0281 against 1.03; 1.0502 with them in; `lead.md` in the scratch folder has both); and what a study looks like when everything a tool can do has been done.

**What it does not show.** Anything about assistants: no language model runs in it. And nothing past the lock: no person locks, opens or signs here. The blind test of the system (`system-trial/README.md`) takes the same plan through every stage in throwaway folders, with a script standing in for the person. `examples/baton-rouge` is the recipe for running the roles as separate assistants.
