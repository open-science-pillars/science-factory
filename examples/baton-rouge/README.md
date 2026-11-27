# Optional demo: one river gauge, with another repository's knowledge and data

**A recipe, not a record.** It points the factory at another repository's knowledge and data: the height and width the SWOT satellite mission reports for the Mississippi at Baton Rouge, against the gauge there. It needs that hydrology repository checked out beside this one, and a second for one check. Nothing here depends on it and no run of it is kept. The example that runs from a bare clone is `examples/stand-alone`.

**If you are an analysis agent starting fresh on one of these requests, stop reading here.** The second half states what an earlier run found: an answer, not knowledge, and reading it before you look ends your blindness to it. Take the request (`request-1.md` or `request-2.md`) and nothing else from this folder.

In this folder: `home.yaml`, the `home` block of `factory.yaml` for the hydrology repository; the two requests (`request-1.md`, how well the satellite height follows the gauge; `request-2.md`, whether the reported width says anything about stage); and `system-trial/analysis-plan.yaml`, the stand-alone trial's plan with the hydrology repository's pairing script in place of the built-in one.

## Run it yourself

**What you need.** `git`, `uv`, and three directories side by side in one folder, `<root>`, at the commits the November 2026 run used.

```
cd <root>
git clone https://github.com/open-science-pillars/hydrology
git -C hydrology checkout \
  f9850d08c526139407eedf13ee3f12effbe83594
git clone \
  https://github.com/open-science-pillars/nasa-daac-knowledge
git -C nasa-daac-knowledge checkout \
  c04ae2e156ca8672c7724254a2c738bd252e9de6
cd science-factory
```

**The part with no agent.** The four steps of the optional demo workflow (`.github/workflows/demo-with-hydrology.yml`), from the top of this repository; the blind test alone takes about five minutes.

```
uv run tools/sf.py check-plan \
  --study examples/baton-rouge/system-trial
uv run methods/gain/system_trial.py blind-test \
  --template examples/baton-rouge/system-trial --n 20
uv run methods/built-in-pairing/pair_records.py --selftest \
  --compare-with \
  ../hydrology/skills/swot-hydro/scripts/load_swot_confrontation.py
uv run tools/knowledge.py selftest \
  --checker ../nasa-daac-knowledge/tools/check_okf_v02.py
```

Expect `plan check: the analysis plan is complete`; `"wrong_verdicts": 0` and `"every_run_ready_for_signature": true`; `selftest: PASS` for the pairing step (on ten cases both pairing steps give the same pairs and scores); and `selftest: PASS` for the knowledge helpers with the pinned checker.

**The part with agents.** Each role is a separate agent started from `factory/agents/<name>/agent.md` with a task and no memory of the others. The work goes into folders git ignores (`explorations/`, `studies/`, `knowledge-queue/`, `record/`). The commands start each role through the Claude Code harness, which keeps task and answer in the role's own place; that harness has not run against Claude Code (the November run started roles another way, below), and any platform that starts an agent from a role file and a task will do.

Write each task as a short file. The first, `record/tasks/01.md`, says: take the request in `examples/baton-rouge/request-1.md`; explore as `agent:analysis-0101` in `explorations/EXPLORATION-0101`; the knowledge is the wiki `../hydrology/knowledge`; the working data is `../hydrology/verification/fixtures/confrontation/swot_gauge_baton_rouge_2024.json`, declared with `--working-data` at the start; open nothing else in `examples/baton-rouge`; hand back when `status` says a reviewer must be named.

```
X=explorations/EXPLORATION-0101
RUN="uv run factory/harnesses/claude-code/run_role.py"

# 1. the analysis agent: reads the knowledge, sets data
#    aside, looks, records choices and notes
$RUN --role analysis --task-file record/tasks/01.md \
  --record record/analysis/01

# 2. the coordinating step: name the reviewer, before any lead
uv run tools/explore.py reviewer --exploration $X \
  --by agent:coordinating-0101 --model claude-sonnet-5-5 \
  --reviewer agent:review-0101

# 3. the analysis agent, started again: writes the lead
$RUN --role analysis --task-file record/tasks/03.md \
  --record record/analysis/03

# 4. the review agent, which did none of the work
$RUN --role review --task-file record/tasks/04.md \
  --record record/review/04

# 5. see where it stands, and go round again or end
uv run tools/explore.py status --exploration $X
uv run tools/explore.py check-log --exploration $X
```

Step 2 is typed by whoever coordinates, a person or the coordinating agent; the tool refuses a lead until it is made and takes a review only from the name it names, never one who explored. A review task names the exploration and nothing the analysis agent said; the launcher refuses a task pointing at `record/analysis/`. When the review finds holes, start the analysis agent on them, name a fresh reviewer (`agent:review-0102`) and repeat steps 3 to 5. Once the lead is reviewed and the exploration ended, the curating agent drafts pages into `knowledge-queue/`:

```
$RUN --role curating --task-file record/tasks/06.md \
  --record record/curating/06
uv run tools/knowledge.py check-drafts \
  --queue knowledge-queue --wiki ../hydrology/knowledge \
  --checker ../nasa-daac-knowledge/tools/check_okf_v02.py
```

The second request is the same loop in `explorations/EXPLORATION-0102`, with `--drafts knowledge-queue` given to `explore.py known` so the drafted pages are found as drafts. Nothing here locks or signs.

## What was found when it was run in November 2026

History: a summary of a run on 2026-11-26 whose numbers no check here reproduces. Its full record is at the branch `records-2026-11`, under `examples/baton-rouge/`. Nothing below is a finding; the requests were written for the example, and nobody locked or signed anything.

One reach, one gauge, calendar 2024, 52 passes, 50 paired with a gauge reading within 15 minutes. The analysis agent set aside everything from 2025-01-01 before reading the knowledge or opening data.

- **Most passes follow the gauge closely, and two in fifty-two are grossly wrong.** Against a line that needs no screen, 2 of 52 passes depart by more than 0.5 m (1.699 m low on 2024-10-30, 0.907 m high on 2024-03-26), and no other pass departs by more than 0.217 m.
- **The quality flag is never zero here, and the knowledge does not say what it means.** `reach_q` is 1 on 49 passes and 2 on 3, so "leave out flagged passes" meant "keep the passes at 1". The flag at 2 catches one gross error and removes two ordinary passes.
- **The gain is not distinguishable from one once the product's own surface slope or a time term is in the fit.** On the same 46 pairs and one kind of interval: 1.0140 (1.0043 to 1.0236) with the gauge alone, 1.0101 (0.9987 to 1.0214) with a time term, 1.0048 (0.9846 to 1.0249) with the product's reach slope, 0.9983 (0.9771 to 1.0194) with both. The slope rises with stage, so a gauge that sits a few kilometres from the point the reach height refers to reads as a gain.
- **The proposed test changed, and can still be met by discarding passes.** The first lead's interval on the gain inside 0.95 to 1.05 could hardly fail (first review). The revised lead proposes the share of kept passes more than 0.5 m off, against one in twenty, after a screen fixed before the opening. The second review found it can still be met by discarding passes (one cut catches both gross errors by removing 34 of 52), and that one in twenty was set after seeing 2 in 52. Those holes were left open.
- **The second question, on river width.** The reported width depends on the overpass track by about as much as on the season, so with tracks mixed, width says little about stage; inside one track it rises about 7 m per metre of stage. That lead was recorded and not reviewed.

Four pages were drafted from the notes; none was signed. A working hydrologist had earlier reviewed a run of the same requests by one instance playing every role. Four of that reviewer's most serious findings on the science were found independently by the review agent in the run with separate agents, and by nobody in the run where one instance reviewed itself. One run, one question, one model behind every role: separation can matter, not how often. The hydrologist's findings are HY in [the register](../../docs/reviews/README.md); the review in full is [history](../../docs/history/reviews/AGENTS-AND-EXPLORING.md).

## Who ran what, and what was instruction

Each role was a separate subagent of one model, given its role file's path and a task by a coordinating session played by a person: an analysis agent, a review agent (six holes), the analysis agent again with no memory, a second fresh reviewer, a curating agent, and a second analysis agent on the second request. No agent was started from the coordinating role file.

Enforced by a tool: every look, choice, note, lead and review went through `tools/explore.py`, which held the fence and kept the log. Instruction only: which commands each role called, where it wrote, what it read. With no harness, nothing stopped a call a role file does not allow, and the answers record small departures. One reviewer saw the author's account by accident and stopped itself; a fresh one was started. The curating agent ran before the second review, which the tool now refuses. The first analysis agent had read an earlier version of this page, so was not blind to the earlier run. There was no hand-over to a study.
