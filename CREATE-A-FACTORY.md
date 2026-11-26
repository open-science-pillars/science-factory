# Create a science factory

**Open Science Pillars (personal hat) · 2026-11-25 · for the maintainer and the steward of a capability who want a factory of their own.**

A software factory is defined as code: files in a repository say which agents exist, which stages a piece of work passes through, what runs each stage and how the result is scored, and a change to the factory is a pull request. A science factory is defined the same way. This page says which files, how to start, what each key means, and what you can change by editing a file as against what still needs code.

Status, plainly. The files and the tool described here exist and are tested. There is no command yet that sets a factory up for you, so the quickstart is done by hand. Everything under "Not built yet" at the end is designed or planned, not working.

## A factory, as files

| File | What it is | Read by |
|---|---|---|
| `procedure.yaml` | the factory as code: stages, who does each, the check that ends each, the scorecard | the study tool (stages and scorecard); people (the rest) |
| `studies/STUDY-0001/analysis-plan.yaml` | one study's plan: the question, the data held out, the code, the decision rules | the study tool, key by key |
| `studies/STUDY-0001/request.md` | what the scientist asked, in their own words | people; bound by checksum at the start and at the lock |
| `studies/STUDY-0001/study-log.jsonl` | everything that happened, in order, each line chained to the last | the study tool |
| `studies/openings.jsonl` | the record of what has been opened, across this factory's studies | the study tool |
| `change-log.jsonl` | every change to the factory, with what it was predicted to do and what it did | people; written by the study tool |
| `sf.py`, `system_trial.py`, `compute/` | the machinery, shared by every factory | you run them |
| `templates/` | the request, the analysis plan, the kinds of question, bringing a workflow in | you copy them |
| `assistants/<role>.md` | one file for each role: what it may call, must never see, reads, writes and hands on, then its instructions | a runner; `assistants/check_roles.py` against the procedure |
| `skills/<name>/SKILL.md` | a procedure a role follows, with any script beside it; no facts about a dataset | the assistants |
| `explorations/EXPLORATION-0001/` | one exploration: its log, what it set aside, its looks and receipts, its notes, its lead | the exploring tool (`explore.py`) |
| a wiki (`openwiki/`, or a knowledge bundle's directory) | the knowledge base: Markdown pages in the Open Knowledge Format, read as files or through `openwiki_search` and `openwiki_read`; `AGENTS.md` points to it | the assistants; `knowledge.py about` |
| `knowledge-queue/` | drafted pages waiting for the steward; none signed | `knowledge.py check-drafts`; the steward |
| `explore.py`, `knowledge.py`, `runners/` | more machinery, shared by every factory | you run them |

One factory per capability. The machinery lives in this repository. Each capability keeps its own procedure, studies, record of openings and change log in its own repository, under its own stewards, because the method under test and the knowledge it rests on are the capability's.

## Quickstart

1. **Put the machinery beside your capability.** Clone this repository next to your capability's repository at a commit you write down. The study tool is part of what a study locks, so the commit matters.
2. **Make the factory.** In your capability's repository create `factory/`. Copy `mvp/procedure.yaml` into it and fill in the `capability` block: the repositories it covers, what it borrows, who its stewards are, and where its studies, record of openings and change log are kept. Copy `mvp/templates/` beside it.
3. **Protect the branch.** The two acts by people, the lock and the steward's signature, are pull requests that a person approves and merges. The tool checks that the lock is in a commit; only your repository's rules can check who merged it.
4. **Accept the factory before you trust it.** Run the system trial (PLAN.md, Part A) in your repository: the whole procedure on a blind test case whose answer nobody in the workspace knows until after the opening. Accept the factory only on a right verdict. An inconclusive trial is closed and another is run.
5. **Run a first study.** A scientist fills in `templates/request.md`. The analysis assistant asks the four questions in `templates/kinds-of-question.yaml` and writes the plan from `templates/analysis-plan.yaml`. What is yours to write for a new method: the method's script, test cases with known answers for it, and a runner that reports the required criteria. Then, in order: `sf.py start`, `check-plan`, `test known-answers`, `test working-data`, `rehearse`, the lock by people, `open-held-out`, `attach`, `review`, the steward's `signature`, `resolve` for each note, `close`.
6. **Put the checks in your pipeline.** On every pull request: `sf.py selftest`, `sf.py check-plan` on each study, and a short `system_trial.py blind-test`.
7. **Give it players.** Copy `assistants/` and `skills/` and change the instructions to suit your capability; keep the front matter true, because the runner enforces it and `assistants/check_roles.py` compares it with your procedure. Render them for your platform (`runners/claude-code/render.py` for Claude Code) and commit what it writes. Point the role files at your knowledge base: a directory of Markdown pages. Add to your pipeline `explore.py selftest`, `knowledge.py selftest`, `check_roles.py` and `render.py --check`.
8. **Explore before you confirm.** Most requests are not yet claims. The coordinating assistant sends those to an exploration (`explore.py start`, which sets data aside first), and only a lead that survives a review is handed to a study (`explore.py hand-over`, then `sf.py start`).

## The procedure file, key by key

**Read by the study tool.** Changing these changes what the tool does.

| Key | Meaning |
|---|---|
| `stages[].id` | the stage's name, shown by `sf.py status` |
| `stages[].done_by` | who does it: an assistant by role, or `people` |
| `stages[].done_when` | the checks that end the stage, from the list below; a name the tool cannot check is refused |
| `stages[].does` | one sentence shown to whoever is at that stage |
| `measure.checks[].id`, `kind`, `why` | the scorecard: each check has a kind from the list below |

Checks a stage may name: `started`, `plan-complete`, `tests-pass`, `rehearsals-pass`, `locked`, `openings-complete`, `finding-attached`, `reviewed`, `steward-decided`, `notes-resolved`, `closed`.

Kinds a scorecard check may have: `log-checks-out`, `not-exploratory`, `openings-within-allowed`, `no-failed-opening`, `lock-committed-before-opening`, `review-recorded`, `acts-recorded-by-people`, `notes-on-curation-list`.

The lock records the procedure file's checksum, and `status` and `scorecard` say so when the file they read is not the one that was locked.

**The roles, as files.** The procedure's `assistants` block says in a sentence what each assistant does, may not do and never sees. The role files in `assistants/` say the same thing in a form a runner can enforce, and quote the block word for word; `assistants/check_roles.py` fails when either changes without the other, when a role may call the lock or the signature, when the review role may call anything that does the work, or when a stage's command is missing from the role the procedure gives the stage to.

**Read by people.** These blocks state the factory's design. The tool does not read or enforce them, and each says in its own words what does hold it: `factory`, `version`, `product`, `capability`, `study_kinds`, `request`, `where_it_runs`, `people`, `assistants`, `separations`, `rules_for_people`, and under `measure` the blind test and how the procedure is improved.

## What a file can change, and what needs code

By editing `procedure.yaml` you can add, remove or reorder stages built from the checks above, change who does a stage, change what a person is told at a stage, and choose which scorecard checks apply. By editing a plan you set everything about one study.

A new kind of check, a new kind of study or a new kind of decision rule needs a change to the study tool, which is a pull request to this repository with a self-test that fails without it.

## Measure and change

Three things say how a factory is doing. The **scorecard** (`sf.py scorecard`) is worked out from one study's log. The **blind test of the system** (`system_trial.py blind-test`) runs many blind test cases through the whole procedure and counts how often a false idea is supported and a true one missed. **Notes** raised during studies say what was missing or wrong.

A change to the factory is a pull request. Before it is tried, `sf.py log-change` records the problem, the change and what it is predicted to do; afterwards a second record says what it did. Nothing is adopted automatically.

## Compared with a software factory

| In a software factory | Here | |
|---|---|---|
| work sources | a scientist's request; also a new data release, a reprocessing, a finding that expires | translated |
| automations | triggers that start a study or run tests; they never lock, open or sign | translated; not built |
| a foreman, one conversation per work item | the coordinating assistant, one log per study or exploration | kept; defined in `assistants/coordinating.md` |
| agent definitions in the platform's settings | role files in `assistants/`, rendered for a platform and checked for drift | changed: the platform's files are output, never the source |
| triage | Ask: the four questions back, and a search for what already answers it | translated |
| a spec that a person approves | the analysis plan | changed, see below |
| implement, with evidence a person can look at | build the method and test it on known answers; the evidence is run receipts | translated |
| review, with revision back to implement | the review assistant, then the steward | changed, see below |
| "agents never merge; your repository policy applies" | the same sentence, twice: the lock and the signature | kept |
| the factory definition, under version control | `procedure.yaml` and the templates, per capability | kept |
| execution on hosted or your own compute | where it runs; a fresh clone at recorded commits | translated |
| a dashboard | studies by stage, and openings spent against openings allowed | translated; not built |
| measure and improve | the scorecard, the blind test, the change log, fixes as pull requests | kept |

The one change in kind. In software a person approves the spec, the work is then implemented, and review can send it back as often as needed. Here the method is built and revised freely first, then people lock the plan and the code together, then the held-out data is opened once. Revision never crosses that opening: afterwards a review can send back the write-up, never the analysis.

What a software factory has no place for, and this one keeps: held-out data and the access gate, tests on known answers, the record of what has been opened, inconclusive as a final answer, and a second loop that feeds shared knowledge as well as the procedure.

## Not built yet

A command that sets a factory up in a capability's repository. The request as an issue form that the factory reports back to. Triggers for a data release and for an expiring finding. The lock and the signature as pull requests that carry a generated summary of the evidence. A page of studies by stage. The blind test used to compare two versions of a procedure. The model behind each stage recorded in the study log (the Claude Code launcher records it beside each role's answer, not in the log). A run of the roles by a platform: the roles, the skills and one runner exist, and the runner has not been run against its platform. A schedule for the curating assistant. Studies that keep watching as data arrives (see `proposals/watching-studies.md`). Places to run other than this machine.
