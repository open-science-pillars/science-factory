# Optional demo: one river gauge, with another repository's knowledge and data

**An optional demo, and a recipe, not a record.** It is the factory pointed at the knowledge and the data of another repository of this project, the hydrology capability, for one river gauge: the height and width the SWOT satellite mission reports for the Mississippi at Baton Rouge, against the gauge there. It needs that repository checked out beside this one, and for one check a second repository. Nothing in the tools, the roles, the skills or the checks of this repository depends on it, and no run of it is kept here. The example that runs from a bare clone is `examples/stand-alone`.

**If you are an analysis assistant starting fresh on one of these requests, stop reading here.** The second half of this page states what an earlier run found. That is an answer to the question, not knowledge, and reading it before you look means you are no longer blind to it. Take the request (`request-1.md` or `request-2.md`) and nothing else from this folder.

What is in this folder: `capability.yaml`, the `capability` block of the procedure filled in for the hydrology capability (the factory's own copy names only the built-in example); the two requests, as inputs (`request-1.md`, how well the satellite height follows the gauge; `request-2.md`, whether the reported river width says anything about stage), and `system-trial/analysis-plan.yaml`, the plan of the stand-alone system trial with the pairing step exchanged for the script the hydrology capability ships.

## Run it yourself

**What you need.** `git`, `uv`, and three directories side by side in one folder, called `<root>` here. The addresses and commits are those the November 2026 run used.

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

**The part with no assistant in it.** These four commands are the steps of the optional demo workflow (`.github/workflows/demo-with-hydrology.yml`), typed from the top of this repository. They take about three minutes together.

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

They end with `plan check: the analysis plan is complete`; `"wrong_verdicts": 0` and `"every_run_ready_for_signature": true`; `selftest: PASS (6 of 6)` (on ten test cases this repository's pairing step and the hydrology script give the same pairs and scores); and `selftest: PASS (64 of 64)`.

**The part with assistants.** Each role is a separate assistant started from its role file (`factory/agents/<name>/agent.md`), with a task and no memory of the others. The work goes into folders at the top of this repository that git ignores (`explorations/`, `studies/`, `knowledge-queue/`, `record/`), so nothing you make is committed here. The commands below start each role through the Claude Code harness, which keeps the task and the answer in the role's own place. That harness has not been run against Claude Code; the November run started each role another way, described under "Who ran what". Any platform that starts an assistant from a role file and a task will do.

Write each task as a short file first. The first one, `record/tasks/01.md`, says: take the request in `examples/baton-rouge/request-1.md`; explore as `agent:analysis-0101` in `explorations/EXPLORATION-0101`; the knowledge is the wiki `../hydrology/knowledge`; the working data is `../hydrology/verification/fixtures/confrontation/swot_gauge_baton_rouge_2024.json`; open nothing else in `examples/baton-rouge`; stop and hand back when `status` says a reviewer must be named.

```
X=explorations/EXPLORATION-0101
RUN="uv run factory/harnesses/claude-code/run_role.py"

# 1. the analysis assistant: reads the knowledge, sets data
#    aside, looks, records choices and notes
$RUN --role analysis --task-file record/tasks/01.md \
  --record record/analysis/01

# 2. the coordinating step: name the reviewer, before any lead
uv run tools/explore.py reviewer --exploration $X \
  --by agent:coordinating-0101 --model claude-sonnet-5-5 \
  --reviewer agent:review-0101

# 3. the analysis assistant, started again: writes the lead
$RUN --role analysis --task-file record/tasks/03.md \
  --record record/analysis/03

# 4. the review assistant, which did none of the work
$RUN --role review --task-file record/tasks/04.md \
  --record record/review/04

# 5. see where it stands, and go round again or end
uv run tools/explore.py status --exploration $X
uv run tools/explore.py check-log --exploration $X
```

The coordinating step is the one command typed by whoever coordinates, a person or a coordinating assistant started from `factory/agents/coordinating/agent.md`. The tool refuses a lead until it has been made, takes a review only from the name it names, and refuses that name to anyone who explored. A review task names the exploration and nothing the analysis assistant said about it; the launcher refuses a task that points at `record/analysis/`. When the review finds holes, start the analysis assistant again on them, name a fresh reviewer (`agent:review-0102`) and repeat steps 3 to 5. When the lead has been reviewed and the exploration has ended, the curating assistant drafts pages into `knowledge-queue/`:

```
$RUN --role curating --task-file record/tasks/06.md \
  --record record/curating/06
uv run tools/knowledge.py check-drafts \
  --queue knowledge-queue --wiki ../hydrology/knowledge \
  --checker ../nasa-daac-knowledge/tools/check_okf_v02.py
```

The second request is the same loop in `explorations/EXPLORATION-0102`, with `--drafts knowledge-queue` given to `explore.py known` so that the drafted pages are found, marked as drafts. No step here locks or signs anything, and no role's commands include either.

## What was found when it was run in November 2026

Everything in this section is historical. It is a summary of a run made on 2026-11-26, and the numbers in it are not reproduced by any check in this repository: the full record of that run (the exploration logs, every look and receipt, the three versions of the lead, the two reviews, the drafted pages, each assistant's answer and a page saying who ran what) is at the branch `records-2026-11` of this repository, under `examples/baton-rouge/`. Nothing below is a finding. The requests were written for the example; no person asked them, and no person locked or signed anything.

One reach, one gauge, calendar 2024, 52 passes of which 50 pair with a gauge reading within 15 minutes. The analysis assistant set aside everything from 2025-01-01 onward before reading the knowledge or opening any data.

- **Most passes follow the gauge closely, and two in fifty-two are grossly wrong.** Against a line that needs no screen, 2 of 52 passes depart by more than 0.5 m (1.699 m low on 2024-10-30, 0.907 m high on 2024-03-26), and no other pass departs by more than 0.217 m.
- **The quality flag is never zero in this record, and its meaning is not written in the knowledge.** `reach_q` is 1 on 49 passes and 2 on 3. So "leave out flagged passes" only ever meant "keep the passes at 1", and no page of the bundle says what any value means for a river reach. The flag at 2 catches one of the two gross errors and removes two ordinary passes.
- **The gain is not distinguishable from one once the product's own surface slope or a time term is in the fit.** On the same 46 pairs and one kind of interval: 1.0140 (1.0043 to 1.0236) with the gauge alone, 1.0101 (0.9987 to 1.0214) with a time term, 1.0048 (0.9846 to 1.0249) with the product's reach slope, 0.9983 (0.9771 to 1.0194) with both. The slope rises with stage, so a gauge that sits a few kilometres from the point the reach height refers to reads as a gain.
- **The proposed test changed, and can still be met by discarding passes.** The first lead proposed an interval on the gain inside 0.95 to 1.05, which the first review showed can hardly fail. The revised lead proposes a rate of gross errors: the share of kept passes more than 0.5 m off, against one in twenty, after a screen written down before the opening. The second review found that this rule can still be met by discarding passes (one cut catches both gross errors by removing 34 of 52), and that one in twenty was set after seeing 2 in 52. Those holes were left open.
- **The second question, on river width.** The reported width depends on the overpass track by about as much as on the season, so with tracks mixed, width says little about stage; inside one track it rises about 7 m per metre of stage. That lead was recorded and not reviewed.

Four pages were drafted for the hydrology knowledge from the notes; none was signed. A working hydrologist had earlier reviewed a run of the same requests by a single instance playing every role, and four of that reviewer's most serious findings about the science were found independently by the review assistant in the run with separate assistants, and by nobody in the run where one instance reviewed itself. That is one run, on one question, with one model behind every role: it shows that separation can matter, not how often it does. `docs/reviews/ASSISTANTS-AND-EXPLORING.md` has the hydrologist's review, finding by finding.

## Who ran what, and what was instruction

Each role was a separate subagent of one model, started by a coordinating session that gave it the path of its role file and a task: an analysis assistant, a review assistant that returned six holes, the analysis assistant started again with no memory of its first session, a second review by a fresh assistant, a curating assistant, and a second analysis assistant on the second request. The coordinating role was played by a person's session; no assistant was started from `factory/agents/coordinating/agent.md`.

What was enforced by a tool: every look, choice, note, lead and review went through `tools/explore.py`, which held the fence around the set-aside data and kept the log. What was instruction and not enforcement: which commands each role might call, where it wrote, and what it might read. The Claude Code harness was not used, so nothing outside a role stopped a call its role file does not allow, and the answers record small departures an enforcing harness would have stopped. One reviewer saw the author's account by accident and stopped itself, as its role file requires; a fresh one was started. The curating assistant ran before the second review, which the tool now refuses. The first analysis assistant had read an earlier version of this page, so it was not blind to the earlier run. There was no hand-over to a study in that run.
