# Demo: two questions about SWOT at Baton Rouge, run twice

**A demo of the factory using skills, knowledge and data from elsewhere in Open Science Pillars.** It needs the `hydrology` and `nasa-daac-knowledge` checkouts beside this repository, at the commits README.md names. Nothing in the core depends on it; the example that runs from a fresh clone is `examples/stand-alone`.

**If you are an analysis assistant starting fresh on one of these requests, stop reading here.** This page states what earlier runs found. It is an answer to the question, not knowledge, and reading it before you look means you are no longer blind to it. Take the request (`request-1.md` or `request-2.md`) and nothing else from this folder.

The same two requests were run twice, and the two runs are different kinds of evidence.

| | The run with separate assistants | The single-instance run |
|---|---|---|
| Where | `with-assistants/` | `explorations/`, `knowledge-queue/`, `record/`, `studies/` directly in this folder |
| Who | Separate assistants, each started from its role file with a task and no memory of the others | One model instance playing every role in one conversation |
| Reviews | By assistants that did none of the work and had not seen the author's account | The author checking its own work with the review checklist |
| How far | First lead reviewed twice and still with the analysis assistant; second lead recorded and not yet reviewed; four pages drafted; no hand-over | First lead handed over to a study that stops before the lock; second question ended as a note; two pages drafted |
| Read it for | What the loop does when the roles are really separate | The hand-over to the confirming way, and what self-review misses |

The run with separate assistants is the one to read. The single-instance run is kept as it was made, because it is the record of what happened and because the difference between the two is the main thing this example shows.

Everything below is a lead, a draft or a review. Nothing here is a finding. The requests were written for the example; no person asked them, and no person locked or signed anything.

## The run with separate assistants

`with-assistants/record/WHO-RAN-THIS.md` says exactly who ran what and what was not exercised. In short: each role was a separate subagent of one model, started by a coordinator from the role file with a task; the coordinating role itself was played by the person's session.

1. **An analysis assistant** (`agent:analysis-0101`) took the first request: how well does SWOT river height follow the Baton Rouge gauge, and where does it not? It set aside everything from 2025-01-01 onward before reading the knowledge or opening any data, read thirteen knowledge pages, ran 12 looks on calendar 2024, recorded six choices and four notes, and returned a lead. It said in its answer, and in the lead, that it had read an earlier version of this page and the head of a method script while orienting (the review found a second script that says as much), so it was not blind to the earlier run.
2. **A review assistant** (`agent:review-0101`), which did none of the work, returned six holes. No number was wrong. The holes were about what the headline said, what the screen was, and what the proposed test could show.
3. **The analysis assistant, started again with no memory of its first session,** answered every hole: two choices recorded before the looks that depend on them, five more looks, two choices after, two more notes, and a revised lead that claims less.
4. **A second review by a fresh assistant** (`agent:review-0103`). One reviewer before it stopped itself, as its role requires, after seeing the author's account by accident, and a fresh one was started. It found that all six earlier holes were answered and that smaller ones remained, and recorded holes-found again. The exploration stands there: with the analysis assistant, not ended.
5. **A curating assistant** (`agent:curating-0101`) drafted four pages from the six notes, linked one note and declined one. It ran before the second review, which the tool now refuses (see below).
6. **A second analysis assistant** (`agent:analysis-0102`) took the second request, whether reach width says anything about stage. It found the four drafts listed as drafts, read them, checked them against the file and used them. Its lead is recorded and has not been reviewed.

### What it found about the data, as a lead

From `with-assistants/explorations/EXPLORATION-0101/lead.md` (version 3) and the two reviews beside it. One reach, one gauge, calendar 2024, 52 passes of which 50 pair with a gauge reading within 15 minutes.

- **Most passes follow the gauge closely and two in fifty-two are grossly wrong.** Against a line that needs no screen, 2 of 52 passes depart by more than 0.5 m (1.699 m low on 2024-10-30, 0.907 m high on 2024-03-26) and no other pass departs by more than 0.217 m.
- **The quality flag is never zero in this record, and its meaning is not in the knowledge.** `reach_q` is 1 on 49 passes and 2 on 3. So "leave out flagged passes" only ever meant "keep the passes at 1", and no page of the bundle says what any value means for a river reach. The flag at 2 catches one of the two gross errors and removes two ordinary passes. The stated uncertainty does not mark them either: it was 0.095 m on the pass that was 1.699 m off.
- **The gain is not distinguishable from one once the product's own surface slope or a time term is in the fit.** On the same 46 pairs and one kind of interval: 1.0140 (1.0043 to 1.0236) with the gauge alone, 1.0101 (0.9987 to 1.0214) with a time term, 1.0048 (0.9846 to 1.0249) with the product's reach slope, 0.9983 (0.9771 to 1.0194) with both. The slope rises with stage, so a gauge that sits a few kilometres from the point the reach height refers to reads as a gain. A gain, a low-water offset, a drift and the gauge's place in the reach fit 2024 about equally, because in one year stage, time and slope move together.
- **The proposed test changed.** Version 1 proposed an interval on the gain inside 0.95 to 1.05, which the first review showed can hardly fail. Version 3 proposes the rate of gross errors: the share of kept passes more than 0.5 m off, against one in twenty, after a screen written down before opening from the product description. The second review found that this rule can still be met by discarding passes (one cut catches both gross errors by removing 34 of 52), that one in twenty was set after seeing 2 in 52, and that at that rate one reach probably cannot give enough passes for the rule to conclude. Those holes are open.
- **What must be in the knowledge before a plan can be written**, by the lead's own account: what the values of `reach_q` mean, where the gauge sits in the reach, and a working file that carries the processing identifier and the bitwise flag.

The four drafted pages are in `with-assistants/knowledge-queue/`: the flag census and the missing meaning of its values; two passes carrying nine tenths of the squared departure in the signed recipe's worked example; a reach height against a point gauge reading as a gain; and what the working file does not carry. None says `contradicts`; two say `narrows`. None gives a meaning for a flag value, a screen, a threshold or a gain as fact, on purpose.

The second question's lead (`with-assistants/explorations/EXPLORATION-0102/lead.md`, not reviewed): the reported width depends on the overpass track by about as much as the seasonal signal, so with tracks mixed width says little about stage, and inside one track it rises about 7 m per metre of stage. Nothing in the signed or drafted knowledge had warned of that.

## What an independent hydrologist said

A working hydrologist (altimetry and gauges) read the single-instance run cold, recomputed it with their own code, and did not open `with-assistants/`. The review is recorded finding by finding in `docs/reviews/ASSISTANTS-AND-EXPLORING.md`. Its substance:

- **Every central number reproduced to the digit.** "The arithmetic is honest. My objections are about what was not looked at and what the numbers are taken to mean."
- **The gain above one is probably geometry, and nobody looked.** The file carries the product's water surface slope for every pass; no look used it. With slope in the model the gain falls to about 1.005.
- **The time term was a choice nobody recorded**, and it moves the gain as much as the flag screen does.
- **"Unflagged" passes are all flagged.** No pass is at 0, and the lead never says what the values mean.
- **A regression gain with a five percent band is a weak summary and a weak test.** The measures the field uses (the 68th percentile of absolute error, the fraction beyond a stated error, a robust fit) answer the request better, and in their judgment the proposed study would very likely come back supported and teach almost nothing about using the product where there is no gauge.
- **The drafted page that corrects the signed recipe credits the flag for what one pass did**, and compares a change between two passes with a per-pass uncertainty.
- **On the tools:** the fence let a set-aside site through when it was written as a bare number; exploring had no pictures; the record read as "an audit trail of a prepared battery, not of a mind changing"; and the stand-alone example crashed on a launcher warning.
- **Would they sign the two drafted pages?** No, not as written.
- **Would they use it?** "I came expecting ceremony and found something more useful and more limited than that." They would use it if looks kept figures, the fence matched identifiers the way people type them, and a person could drive it; the list of choices sorted by whether they move the answer is "the one artefact I would steal".

## What the comparison shows

The single-instance run's science was naive in the ways the hydrologist names, and it is not rewritten here. Its headline (a gain of 1.0121 with "three flagged passes left out"), its proposed test and its two drafted pages stand in the folders as they were made, and they should be read as what one instance checking itself produced.

| What a referee would ask | Single-instance run | Independent hydrologist | Review assistant in the run with separate assistants |
|---|---|---|---|
| Is a gain of one even the expectation for a reach against a point gauge? Was the product's slope used? | Not asked in 29 looks or two reviews | Finding 1 | Hole 3 of the first review; the answer is LOOK-015 |
| Is the time term a choice, and does the answer depend on it? | Kept in every fit and never recorded as a choice; the self-review asked only that the drift be called meaningless | Finding 2 | Hole 4; the answer puts every fit on one footing |
| What does the flag screen mean when no pass is at zero? | Passes at 1 called "not flagged" | Finding 3 | Hole 1; the answer is the flag census |
| Can the proposed test fail? | The self-review passed a rule that needs the whole interval outside 0.95 to 1.05 to refute | Finding 10 | Hole 5; the question was changed, and the second review pressed on the new one |
| Were choices recorded when they were made? | This page used to say "it recorded five choices as it made them"; the log shows every one was written down after a batch of looks | Finding 8 | Hole 2; the revised lead says all six were logged after the last look |

Four of the hydrologist's most serious findings about the science were found independently by the review assistant in the run with separate assistants, which had not seen the hydrologist's review, and none of them was found by the instance that reviewed itself. That is the case for separate roles, made by the example itself. It is one run, on one question, with one model behind every role, so it shows that separation can matter, not how often it does.

What neither run did, and the hydrologist asked for: a figure of any kind, the error measures the field uses, a second reach, and sites set aside as well as a later period. The tools now keep figures and the skill tells the analysis assistant to draw them; the rest is for the next run.

## What changed in the tools because of this

The six answer files in `with-assistants/record/` each end with what was unclear, wrong or in the way. Together with the hydrologist's review they led to these changes, each with a self-test (the full list is in `docs/reviews/ASSISTANTS-AND-EXPLORING.md`):

- The fence reads a site the ways people write it, the bare number included.
- The role file and the skill now say the same thing about order, in the same words, and a check fails when they differ: knowledge is read first and only knowledge, then data is set aside, then looks; an exploration ends as a lead only after its latest lead is reviewed.
- The review assistant has no route to the author's account: each role has its own place to write, and the runner refuses the reviewer the author's place.
- The curating assistant waits for the end: a note cannot be resolved while the lead can still be revised.
- The lead shows the order of looks and choices from the log; a look can keep a figure; one phrase of a lead can be corrected without a new version; a number in a lead must match a whole printed number.

Because of the fourth change, `check-log` on `EXPLORATION-0101` passes with a remark: its notes were resolved before it ended, which the tool now refuses. The log is kept as it was written.

## To check it yourself

From the repository root with the two checkouts beside it:

```
uv run tools/explore.py check-log --exploration examples/baton-rouge/with-assistants/explorations/EXPLORATION-0101
uv run tools/explore.py check-log --exploration examples/baton-rouge/with-assistants/explorations/EXPLORATION-0102
uv run tools/explore.py status --exploration examples/baton-rouge/with-assistants/explorations/EXPLORATION-0101
uv run tools/knowledge.py check-drafts --queue examples/baton-rouge/with-assistants/knowledge-queue \
  --wiki ../hydrology/knowledge --checker ../nasa-daac-knowledge/tools/check_okf_v02.py
```

The looks of this run named the data file by the full path it had on the machine that ran them, so `explore.py recheck` reproduces them only where the hydrology checkout sits at that same path; `check-log` verifies every receipt and output by checksum anywhere. For the single-instance run, whose looks used paths from the exploration directory:

```
uv run tools/explore.py check-log --exploration examples/baton-rouge/explorations/EXPLORATION-0001
uv run tools/explore.py recheck --exploration examples/baton-rouge/explorations/EXPLORATION-0001 --look LOOK-012
uv run tools/explore.py check-study --exploration examples/baton-rouge/explorations/EXPLORATION-0001 \
  --study examples/baton-rouge/studies/STUDY-0002
```

## Where everything is

| What | Where |
|---|---|
| The requests | `request-1.md`, `request-2.md` |
| **The run with separate assistants** | `with-assistants/` |
| Who ran each role, and what was not exercised | `with-assistants/record/WHO-RAN-THIS.md` |
| What each assistant handed back, ending with what got in its way | `with-assistants/record/01` to `06` |
| The first exploration: log, looks, receipts, notes, three lead versions, two reviews | `with-assistants/explorations/EXPLORATION-0101/` |
| The second exploration | `with-assistants/explorations/EXPLORATION-0102/` |
| The four drafted pages and the queue's index | `with-assistants/knowledge-queue/` |
| **The single-instance run** | everything else in this folder |
| What each role was given and handed back, and every command | `record/` |
| The first exploration, with its hand-over | `explorations/EXPLORATION-0001/` |
| The second exploration, a dead-end note | `explorations/EXPLORATION-0002/` |
| The two drafted pages | `knowledge-queue/` |
| The study started from the first lead, stopped before the lock | `studies/STUDY-0002/` |

## The single-instance run, for the record

One instance read the first request as exploring; set aside everything from 2025-04-28 onward (a narrower window than the request offered, which left the first four months of 2025 in no category, as the hydrologist pointed out); ran 29 looks of which 2 failed; recorded six choices, every one written into the log after a batch of looks had run; returned a lead through four versions; drafted two pages; answered the second request in four looks using those drafts; and took the first lead to a study (`studies/STUDY-0002`) whose plan passes the plan check and `explore.py check-study`, stopping before the lock. Every command it ran went through the by-hand runner, which holds a role to its commands and gives no fresh context. `record/WHO-RAN-THIS.md` there says what was real and what was not. The hand-over is the part of the loop only this run shows; it was not repeated with separate assistants.
