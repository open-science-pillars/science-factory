# The stand-alone example

**Runs from a fresh clone with nothing beside it.**

```
uv run examples/stand-alone/run.py
```

It ends with `stand-alone example: PASS (33 of 33 steps)`, in about a minute after the first download of PyYAML. A warning the launcher prints on standard error does not disturb it: the run reads a tool's answer from what the tool prints, and one of its steps tests that.

What it has:

- `record-2024.json`: a synthetic two-sensor record, one row a week, made by `make_record.py` from a fixed seed. The answer is known because it was put in by hand: a gain of 1.03, an offset of 0.40 m, noise of 0.05 m, two readings flagged degraded of which one is 2 m off.
- `openwiki/` at the top of the repository: the knowledge base, a wiki in OpenWiki's form (the Open Knowledge Format v0.2) with three pages and a quickstart. None is signed.
- `looks/gain.py`: the one look script.
- `skills/explore-a-record/scripts/plot_xy.py`, from the exploring skill: the script that draws the one figure.
- `run.py`: the run. It reads the wiki, and only the wiki, then sets the following year aside and records the page the boundary came from. It is refused a look before the knowledge is listed and again before a page is recorded as read, looks twice, is refused a look at the set-aside year (named as a file, through its folder, through a pattern and after an `=`), draws a figure of the residual and has it logged by checksum, records a choice and a note, is refused a lead until the coordinating name has named the reviewer, is refused a lead that quotes a number no look printed and one that calls flagged readings unflagged, records the lead with its figure and the order of looks and choices, corrects one phrase without a new version, is refused an end before the review and a resolved note before the end, is refused a review by the assistant that explored and one under a name nobody named, is refused an end after a correction made since the review until the corrected lead is reviewed, hands over, starts a study with the study tool, checks that the study keeps the fence and that one holding out the explored year is refused, drafts a page into a queue, is refused until the draft says how it relates to the wiki page it overlaps, is refused when the draft is marked as signed, and finds the draft again, as a draft, for a second question.

What it shows: that the loops hold together and the refusals refuse, and that the exploring comes within 0.02 of the gain that was put in once the degraded readings are left out (1.0281 against 1.03; 1.0502 with them in).

What it does not show: anything about assistants. No language model runs in it. `examples/baton-rouge` is where the roles were run, once by separate assistants and once by one instance playing them all.
