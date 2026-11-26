# Demo: two questions about SWOT at Baton Rouge

**A demo of the factory using skills, knowledge and data from elsewhere in Open Science Pillars.** It needs the `hydrology` and `nasa-daac-knowledge` checkouts beside this repository, at the commits README.md names. Nothing in the core depends on it; the example that runs from a fresh clone is `examples/stand-alone`.

**Read this first: every role here was played by one model instance in one conversation**, held to each role's commands by the by-hand runner and not by separate assistants. The reviews are therefore not independent. `record/WHO-RAN-THIS.md` says exactly what was real and what was not, and `record/RUN-WITH-ASSISTANTS.md` says how to make the record with real assistants. The requests were written for the example; no person asked them, and no person locked or signed anything.

## What happened

1. **A request arrived** (`request-1.md`): how well does SWOT river height follow the Baton Rouge gauge, and where does it not? The coordinating role read it as exploring and handed it to the analysis role.
2. **The analysis role read what is known, then set data aside.** `knowledge.py about` listed eight pages of the hydrology bundle, seven signed and one not. From one of them it took the date on which forward processing starts, and it set aside everything from 2025-04-28 onward before looking at anything. That data was never fetched or read.
3. **It explored calendar 2024**: 24 looks, 2 of which failed, each logged with its script and data by checksum. It recorded five choices as it made them and raised four notes.
4. **It returned a lead**: on 2024 the reach height looks as if it follows the gauge with a gain of 1.0121 (0.9862 to 1.0381 on 47 pairs) once three flagged passes are left out.
5. **The review role picked holes in it**: nine. The one that mattered most: the proposed test would change the year and the processing baseline at once, and the fixture cannot show which baseline 2024 is on.
6. **The analysis role answered**: two more pages read, five more looks, one more choice, and a revised lead that names what could not be closed as a limit. Along the way the tool was changed to refuse a lead that quotes a decimal number found in none of the looks it cites, and it at once refused the lead for one such number.
7. **The curating role drafted two knowledge pages** from the notes into `knowledge-queue/`, at status draft, with sources. One says it contradicts a signed recipe's reading of its own worked example, so the queue lists it first for the steward. One note was linked to the recipe. `knowledge.py check-drafts` passes them, with the organization's own checker.
8. **A second, different question** (`request-2.md`): does the reach width say anything about stage? The analysis role listed the knowledge again with the queue, found the two drafts marked as drafts, read them as drafts, checked the first in one look and then used it: the flag screen from the start and the two bad passes by date, without looking for them again. Four looks. It ended as a dead-end note: width follows stage too coarsely to check a height at this leveed reach.
9. **The first lead was handed to the confirming way** as far as an assistant may take it: a study started from the hand-over (`studies/STUDY-0002`), its plan written and passing the plan check, `explore.py check-study` confirming that its held-out window is inside what was set aside and touches nothing explored, and the known-answer and working-data tests passing. It stops there. The rehearsals need the provider's network, and the lock is a person's. The coordinating role's one attempt to call the lock was blocked by its role file.

## Where everything is

| What | Where |
|---|---|
| The requests | `request-1.md`, `request-2.md` |
| What each role was given and handed back, and who ran it | `record/` |
| Every command a role ran or was refused | `record/commands.jsonl` |
| The first exploration: log, set-aside, look scripts, receipts and outputs, notes, the four lead versions, the two reviews, the hand-over | `explorations/EXPLORATION-0001/` |
| The lead | `explorations/EXPLORATION-0001/lead.md` |
| The second exploration | `explorations/EXPLORATION-0002/` |
| The record of what is set aside, explored and opened | `studies/openings.jsonl` |
| The drafted knowledge and its queue index | `knowledge-queue/` |
| The study started from the lead | `studies/STUDY-0002/` |

To check it yourself, from the repository root with the two checkouts beside it:

```
uv run mvp/loops/explore.py check-log --exploration examples/baton-rouge/explorations/EXPLORATION-0001
uv run mvp/loops/explore.py recheck --exploration examples/baton-rouge/explorations/EXPLORATION-0001 --look LOOK-012
uv run mvp/loops/explore.py check-study --exploration examples/baton-rouge/explorations/EXPLORATION-0001 \
  --study examples/baton-rouge/studies/STUDY-0002
uv run mvp/loops/knowledge.py check-drafts --queue examples/baton-rouge/knowledge-queue \
  --wiki ../hydrology/knowledge --checker ../nasa-daac-knowledge/tools/check_okf_v02.py
```

## What it shows

- **Setting data aside first costs one command and nothing afterwards.** The fence refused nothing because nothing reached for the later data, and the study that came out of the lead has a year of data nobody has looked at.
- **The count of things tried is kept for you.** The lead says 29 looks, 2 failed, because the log does, and the review used that count against the lead's own "where it does not follow".
- **Reading what is known first changed the work.** The signed recipe ruled out scoring the level and already held the 2024 change scores, so the exploring started from them.
- **Drafted knowledge was found and used by the next question, as a draft.** The second exploration spent one look checking what the first spent nine finding. Because one instance played both, this shows the mechanism and not that a fresh assistant would do the same.
- **The tools refused what they should**: a lead quoting a number no cited look printed, a study checked before it had a plan, a role calling the lock, a reviewer acting under the analysis role's name.
- **What it did not show.** Independent review, because there was no second mind. Any person's part: the requests are stand-ins, and nothing was locked or signed. The fence under attack, because no look tried to cross it here; the self-tests and `reviews/ASSISTANTS-AND-EXPLORING.md` cover that.

## What it found about the data, as leads and drafts only

On calendar 2024, with three flagged passes left out, the reach height looks as if it follows the gauge with a gain near 1.01. Two passes do not follow: one flagged, at the year's lowest stage, 1.776 m low with an ordinary stated uncertainty; one not flagged, 0.939 m high, with the year's highest dark fraction. The signed recipe's worked example scores every pass, and its change RMSD of 0.3823 m becomes 0.1859 m with the flagged passes out. None of this is a finding. It was seen on data that had already been looked at, and the test is the study that is waiting for people.
