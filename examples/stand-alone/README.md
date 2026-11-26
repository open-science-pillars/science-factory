# The stand-alone example

**Runs from a fresh clone with nothing beside it.**

```
uv run examples/stand-alone/run.py
```

It ends with `stand-alone example: PASS (21 of 21 steps)`, in a few seconds after the first download of PyYAML.

What it has:

- `record-2024.json`: a synthetic two-sensor record, one row a week, made by `make_record.py` from a fixed seed. The answer is known because it was put in by hand: a gain of 1.03, an offset of 0.40 m, noise of 0.05 m, two readings flagged degraded of which one is 2 m off.
- `openwiki/` at the top of the repository: the knowledge base, a wiki in OpenWiki's form (the Open Knowledge Format v0.2) with three pages and a quickstart. None is signed.
- `looks/gain.py`: the one look script.
- `run.py`: the run. It reads the wiki, sets the following year aside, is refused a look before the knowledge is listed, looks twice, is refused a look at the set-aside year, records a choice and a note, is refused a lead that quotes a number no look printed, records the lead, is refused a review by the assistant that explored, hands over, starts a study with the study tool, checks that the study keeps the fence and that one holding out the explored year is refused, drafts a page into a queue, is refused until the draft says how it relates to the wiki page it overlaps, is refused when the draft is marked as signed, and finds the draft again, as a draft, for a second question.

What it shows: that the loops hold together and the refusals refuse, and that the exploring comes within 0.02 of the gain that was put in once the degraded readings are left out (1.0281 against 1.03; 1.0502 with them in).

What it does not show: anything about assistants. No language model runs in it. `examples/baton-rouge` is where the roles were played.
