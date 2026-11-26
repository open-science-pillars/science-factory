# Science Factory

*Part of Open Science Pillars, a personal open-source project.*

A science factory is a procedure and a set of tools for testing a scientific claim honestly: the plan is written down and locked before the data is opened (pre-registered, to those who use the word), with assistants (always AI agents) doing the labor of exploring, review and drafting knowledge, and an experiment they cannot argue with deciding what survives. This repository is the factory and nothing else. It says what a science factory is, designs it, builds and tests the parts that run no language model, defines the assistants as files, and keeps the reviews made of all of it. It stands on its own: nothing in it needs another repository, and it keeps no runs. No study has run to a finding yet.

## The layout

| Folder | What is in it |
|---|---|
| `tools/` | the programs a person or an assistant runs: `sf.py` (the study tool: one study, one study log, no language model in any check), `explore.py` (the exploring tool), `knowledge.py` and `wiki_server.py` (reading and drafting knowledge), and `check_roles.py` |
| `factory/` | the definition of this factory, as files: `procedure.yaml` (the stages and who acts in each), `change-log.jsonl` (its own changes, each with a prediction), `templates/` (a request, a commented analysis plan, the kinds of question, the checklist for bringing a pipeline in), and `checkers.yaml` (the checkers the knowledge helpers will run, each pinned by checksum) |
| `methods/` | the built-in method, used by the system trial and the examples: `gain/` is the gain of one record against another, with its known-answer tests and the system trial's script; `built-in-pairing/` is the small step that pairs two records by time |
| `compute/` | the contract for where a job runs (`adapter.py`) and the table of places (`places.yaml`); one local place is built |
| `assistants/`, `skills/`, `runners/` | the four roles as files, their five skills, and the two runners that start a role |
| `openwiki/` | this repository's own knowledge base, a wiki of Markdown pages |
| `examples/` | inputs and recipes, never runs: `stand-alone/`, which runs from a bare clone and makes its run fresh; `baton-rouge/`, an optional demo that needs another repository |
| `docs/` | the design, the build plan, the word list, the two ways of working, how to define a factory of your own, proposals, reviews |

![The layout of the repository: tools (the programs you run), factory (this factory as files), methods (the built-in method), compute (where a job runs), assistants, skills and runners (the roles, their skills and what starts a role), openwiki (the knowledge base), examples (inputs and recipes), and docs. Beside them, drawn apart: a run is made fresh in a scratch folder, and your own studies live in the repository where the science is; neither is kept here.](docs/diagrams/repository-layout.svg)

## See it work

With `git` and `uv` (https://docs.astral.sh/uv/) and nothing else, from a bare clone:

```
uv run tools/sf.py selftest
uv run methods/gain/system_trial.py blind-test \
  --template examples/stand-alone/system-trial --n 20
uv run examples/stand-alone/run.py
```

The first ends with `selftest: PASS (175 of 175)` in about half a minute: the study tool takes studies through every stage in throwaway folders and makes every attack on itself that a tool can refuse. The second takes two to three minutes and ends with `"wrong_verdicts": 0`: twenty synthetic records, each with a gain put in by hand and sealed, go through the whole confirming procedure, and each seal is opened afterwards to see whether the factory was right. The third takes two to three minutes and ends with `stand-alone example: PASS (37 of 37 steps)`: the exploring loop and the knowledge loop on a synthetic record whose answer is known, then a study taken through its tests to the lock. It prints the path of a scratch folder where you can open the exploration and the two studies it made and see what each looks like on disk. None of the three needs the network after `uv` has fetched PyYAML once, none starts a language model, and none leaves anything in the repository. "Try it" below has the rest.

## Why no runs are kept here

This repository is the factory, not what the factory makes. A study log names the code it ran by checksum, so a record kept beside tools that go on changing stops matching them, and keeping old records checkable had started to shape the tools. So every run is made fresh: the examples ship their inputs and their recipes, and each number these documents cite either comes with the command that reproduces it today from this repository alone, or is marked as historical. The records that were here until November 2026 (two practice runs, a blind test, and a demo on real data run twice) are at the branch `records-2026-11` of this repository (commit `ad0c459`, which is also in the history of `main`, so the records stay reachable whatever becomes of the branch), with the tools as they stood then, and a historical number points there.

**Where your own studies go.** A real study belongs in the repository where the science lives, beside its data and its methods, where its lock can be committed, reviewed and merged on a protected branch. The study tool creates a study wherever `--study` points, by convention in a folder called `studies/`, with the record of what has been opened beside it (`studies/openings.jsonl`); the exploring tool does the same in `explorations/`. In this repository those folders, and `knowledge-queue/` and `record/`, are ignored by git, so that a run made here to try the tools is never committed by accident.

## Two ways of working

A scientist works in two ways. **Exploring** is most of the work: looking at data to find out what is there, trying, looking again, revising. **Confirming** is testing one claim, stated in advance, on data nobody has opened. This package builds both. The confirming way came first and is most of what follows. The exploring way now has a tool of its own (`tools/explore.py`), the assistants are defined as files, and what is learned goes back to a knowledge base through a queue of drafts. Separate assistants have been run from those files once, on real data, and a working hydrologist has reviewed an earlier run (both historical; the records are at `records-2026-11`); `docs/TWO-WAYS-OF-WORKING.md` describes the two ways and the wall between them, and "The assistants and the two loops" below says what is built, what a tool enforces, what is still only instruction, and what is still owed.

![The two ways of working with the wall between them. Exploring, on the left: read what is known, set data aside before any look, look as often as wanted with every look logged, record choices, write up a lead that is reviewed. Confirming, on the right: plan, test on known answers, the lock by a person, open the held-out data once, review, the steward's signature. Only two things cross the wall: a lead, handed over to start a plan, and the data that was set aside, which becomes the held-out data.](docs/diagrams/two-ways-of-working.svg)

## What it is

You ask a question in your own words. With an assistant you write an **analysis plan**: what will be estimated, on which data, and what result would count for or against your idea. Some data is **held out**: by rule, nobody opens it yet. Before it is opened, the method has to pass **known-answer tests**: synthetic data built on your real sampling, with the truth put in by hand, including cases where your idea is false and cases right at the smallest difference you care about. It is the synthetic test you already run, aimed at the decision and not only at the estimate. Then a person, the steward (the person who holds a knowledge bundle and signs it), **locks** the plan and the code together. The tool opens the held-out data once and runs the locked analysis on it; it will not do so for an assistant that ran the tests. A separate **review assistant**, which did none of the study, reads the result, and the steward signs the finding or does not. Every step is written to a **study log**; once the log is committed and its fingerprints are posted outside the workspace, any later edit to it can be detected. What was learned about the data along the way goes back into the shared knowledge.

That paragraph is the design. What holds each sentence today (the tool, a control outside the tool, or nothing yet) is under "Status, plainly" at the end of this page and, stage by stage, in docs/DESIGN.md.

## The five stages

| Stage | What happens |
|---|---|
| 1. Ask | You write a request in your own words. The analysis assistant asks four questions back, and the study is started with the request bound to it by checksum (`sf.py start --request`). |
| 2. Plan | The analysis plan is written, after a search of the shared knowledge for anything that already answers or limits the question, reading only observation metadata: values that cannot move the answer (times, places, quality flags; what else qualifies is decided for each plan). |
| 3. Test on known answers | The plan check, the known-answer tests, the working data (anything already looked at) and the rehearsals, repeated freely. Every attempt the tool runs is logged. |
| 4. Open the held-out data once | The access gate, a step of the tool, fetches the held-out data and runs the locked analysis, once. |
| 5. Review, sign and learn | The finding is written from run receipts and attached. A review assistant that did none of the study checks it. The steward signs the finding or records the decision not to. Notes go into the shared knowledge, and what should change goes into the procedure. |

![The confirming loop. A scientist's request passes down through five stages inside the study log (1 Ask, 2 Plan, 3 Test on known answers, 4 Open the held-out data once, 5 Review, sign and learn) and ends in a finding or a recorded no. Two acts by people are marked: the lock, between Test and Open, and the steward's signature, after Review. Beside the stages: the procedure, read at Ask and changed after Review; shared knowledge, read at Plan and fed by notes; and where the computing runs, which the stages do not call yet.](docs/diagrams/confirming-loop.svg)

A **run receipt** is the record a run writes, with its code and inputs by checksum and every number it produced, so anyone can re-check the result without trusting whoever ran it. After this it is called a receipt.

Two acts belong to people: **the lock**, between Test and Open, and **the steward's signature**. The design has the scientist approve the lock with the steward; the tool takes one person's name today, and the second approval is scheduled, not built. The procedure file counts nine steps where this page counts five stages, because it lists the two acts, the learning and the close as steps of their own, and `sf.py status` reports those nine names (`ask`, `plan`, `test`, `lock`, `open`, `review`, `signature`, `learn`, `close`). Under every stage sits the **study log**. Where the computing runs is a separate contract (`compute/`): it is built and tested with one local place, and the study tool does not call it yet.

## What to read

| File | What it is |
|---|---|
| `README.md` | this page: what it is, the layout, the five stages, how to try it, where it stands |
| `docs/DESIGN.md` | the concept and the whole design in one document: knowledge factories, software factories, what a science factory borrows and refuses, experiments on data in the loop, then the five stages, the study log and where it runs, each with its parts, what goes in and out, what is held today and by what, and what is only designed; candidate platforms compared |
| `docs/PLAN.md` | the build plan in two parts (the system trial, then the first real study): every component and what represents it, what was measured, prompts, commands, the steward's decisions |
| `docs/WORDS.md` | the word list: each plain word beside the earlier word it replaced, with the old and new names of every file, key, log event, check and command |
| `examples/README.md` | the two examples: the one that runs from a bare clone, and the optional demo |
| `docs/reviews/RED-TEAM.md` | three rounds of attack: 33 findings from three reviewers, 15 from a second pass, and 62 from a third round of three reviewers (5 of them blockers) made after the revision and the renames; what each changed, and what is still open |
| `docs/reviews/SCIENTISTS.md` | the factory from the chair of the people who would ask it questions: how they ask, kinds of question, other uses, bringing a workflow in |
| `docs/TWO-WAYS-OF-WORKING.md` | how scientists work: exploring, which is most of it, and confirming; what the factory does for each and why they are kept apart |
| `docs/CREATE-A-FACTORY.md` | how to define a factory of your own as files: a quickstart, the procedure file key by key, and how it compares with a software factory |
| `docs/proposals/watching-studies.md` | proposed, not built: studies that keep watching as data arrives, and choices that expire |
| `docs/diagrams/` | the pictures used on this page and in the documents, as plain SVG files kept by hand, in one style throughout |
| `docs/roadmap-initiative.yaml` | the plan as one initiative and ten deliverables, in the organization's roadmap form |
| `docs/reviews/README.md` | a note on reading the reviews: they are history, they name files by the paths of the day they were written, and the records they cite are at `records-2026-11` |
| `docs/reviews/ASSISTANTS-AND-EXPLORING.md` | the review register for the assistants and the two loops: the builder's self-review, a working hydrologist's review, what separate assistants found in the role files and tools, an independent attack on the tools (2 blockers, 5 serious and 5 minor findings) with what became of each, and the second independent attack that is now owed |

## The assistants and the two loops

Added on 2026-11-26, and revised the same day after separate assistants were run from the role files and a working hydrologist reviewed the result. Before it, the package was a rulebook and a referee with no players.

**The AI side, in four layers, each resting on the one below.** The referee: `tools/sf.py` and its checks, with no language model. Roles as files: `assistants/`, one Markdown file for each of the coordinating, analysis, review and curating assistants, in a form no agent platform owns. The knowledge: a wiki of Markdown pages, read before work and drafted for after it; a person signs. A runner: `factory/harnesses/claude-code/` starts a role with its tools as a Claude Code subagent, and `factory/harnesses/by-hand/` checks one command at a time. Two rules run through all four: an assistant never decides whether a step counts, a tool does; and nothing a role needs lives only in a platform's settings.

![The assistant side in four layers, each resting on the one below: 1 the referee (tools/sf.py and its checks, no language model), 2 roles as files (assistants/), 3 the knowledge (a wiki read before work and drafted for after it, signed by a person), 4 a runner that starts a role with its tools. Two rules run through all four: a tool, never an assistant, decides whether a step counts, and nothing a role needs lives only in a platform's settings.](docs/diagrams/assistant-layers.svg)

**Two loops.** The exploring loop: read what is known, set data aside, look as often as wanted, record choices, write up a lead, have it reviewed, revise, end. The knowledge loop: before work, list the pages that bear on the question and say who signed each; after work, turn notes into drafted pages in a queue for the steward, where the next question finds them marked as drafts. Neither loop signs anything.

| Where | What it is |
|---|---|
| `assistants/` | the four roles as files (what each may call, must never see, reads, writes and hands on), and `check_roles.py`, which fails when they and the procedure's `assistants` block disagree, when a role file and a skill give different orders, or when a role could write in another role's place |
| `skills/` | five skills, procedure only: `read-what-is-known`, `explore-a-record` (with a script that describes a record and one that draws a figure), `write-up-a-lead`, `draft-a-knowledge-page`, `review-work` |
| `tools/explore.py` | the exploring tool: data is set aside before any look, every look runs in a scratch folder holding only what its command names and is logged with its figures, choices are recorded and the lead shows when, and it ends in a lead, a note, a method or a stop |
| `tools/knowledge.py` | the knowledge helpers: list the pages that bear on a question with who signed each; check a queue of drafts, running the organization's checker only when its checksum is pinned in `factory/checkers.yaml`; import pages from another knowledge base, never over a signed page |
| `tools/wiki_server.py` | a read-only server for a wiki directory with the two tool names OpenWiki uses, `openwiki_search` and `openwiki_read` |
| `openwiki/`, `AGENTS.md` | this repository's own knowledge base, a wiki in OpenWiki's form, which the stand-alone example reads; and the pointer to it |
| `runners/` | the Claude Code runner (rendered roles and skills with a drift check, a check on every tool call, a launcher that keeps each role's record in the role's own place) and the by-hand runner |
| `.claude/`, `.mcp.json` | the rendered files Claude Code reads; never edited by hand |
| `examples/stand-alone/` | the two loops end to end on a synthetic record with a known answer, then a study taken to the lock; runs from a bare clone and keeps nothing |
| `examples/baton-rouge/` | an optional demo, as a recipe: the roles run as separate assistants on another repository's knowledge and data for one river gauge, with what was found when it was run in November 2026 |
| `docs/reviews/ASSISTANTS-AND-EXPLORING.md` | the builder's self-review, the hydrologist's review finding by finding, what the assistants found, the independent attack finding by finding, and what is still owed |

**The order the exploring loop holds.** Knowledge is read first, and only knowledge: signed pages and drafted pages, never data. Then data is set aside, before any look. Then the tool writes into the log what was listed and read, and the first look waits for that. The coordinating assistant names the reviewer before a lead exists, and a lead is refused until it has. A lead is reviewed by that reviewer, an assistant that did none of the work and is told to keep away from the author's account of it (the Claude Code runner's check refuses it the read, when a platform calls that check); a revised lead is reviewed again, and so is a lead whose wording was corrected after its review; the exploration ends as a lead only after its latest lead has been reviewed; and the curating assistant resolves no note until the exploration has ended. The role files and the skills say this in the same words, and a check fails when they differ.

**Where the tools sit, and why the system trial's script does not sit with them.** The study tool counts every Python file beside a script that a plan runs as part of that plan's code, because Python could import it. The system trial's script is run by a plan, so it sits with the method it exercises, in `methods/gain/`, and not in `tools/`: there, every tool would be bound into every lock, and an edit to the exploring tool would undo a locked study.

**Run the stand-alone example.** From a bare clone, with nothing beside it and only `uv` installed:

```
uv run examples/stand-alone/run.py
```

It ends with `stand-alone example: PASS (37 of 37 steps)`, in two to three minutes after the first download of PyYAML. It drives both loops from the command line on a synthetic record whose answer is known, and checks every step: the refusals refuse, a look keeps a figure, the lead shows the order of looks and choices, and a draft is found again as a draft. Then it takes a study through its tests to the lock. It leaves what it made in a scratch folder outside the repository and prints where. No assistant runs in it. A warning the launcher prints on standard error does not disturb it; it once did, and one of its steps now tests that.

**Try the rest of this part.** From the repository, with nothing beside it:

```
uv run tools/explore.py selftest
uv run tools/knowledge.py selftest
uv run tools/wiki_server.py --selftest
uv run tools/check_roles.py
uv run tools/check_roles.py --selftest
uv run factory/harnesses/claude-code/render.py --check
uv run factory/harnesses/claude-code/render.py --selftest
uv run factory/harnesses/claude-code/allow.py --selftest
uv run factory/harnesses/claude-code/run_role.py --selftest
uv run factory/harnesses/by-hand/as_role.py --selftest
uv run factory/agents/analysis/skills/explore-a-record/scripts/describe_record.py --selftest
uv run factory/agents/analysis/skills/explore-a-record/scripts/plot_xy.py --selftest
```

They end with `PASS (198 of 198)`, `PASS (64 of 64)`, `PASS (13 of 13)`, `check-roles: PASS (4 roles; ...)`, `PASS (32 of 32)`, `render --check: PASS (14 rendered files)`, `PASS (11 of 11)`, `PASS (77 of 77)`, `PASS (10 of 10)`, `PASS (9 of 9)`, `PASS (3 of 3)` and `PASS (7 of 7)`.

**A person can explore with the same tool.** Nothing in `explore.py` needs an assistant: act as `--by human:<your name>` and follow `factory/agents/analysis/skills/explore-a-record/SKILL.md`. The hydrologist who reviewed this part started an exploration of their own from the documents in about five minutes (historical; `docs/reviews/ASSISTANTS-AND-EXPLORING.md`).

**The knowledge base is a wiki, in OpenWiki's form.** A repository's wiki lives in `openwiki/`: Markdown pages in the Open Knowledge Format v0.2 (front matter with a non-empty `type`, and where present `generated`, `sources`, `verified`, `status`, `stale_after`), with `index.md` and `log.md` reserved, `quickstart.md` as the place to start, and `INSTRUCTIONS.md` as the owner's brief. Any other knowledge base kept in that format is read through the same door by naming its directory (or copied in with `knowledge.py import`, which keeps where each page came from, its status and who signed it). `AGENTS.md` at the top of the repository carries the pointer to the wiki between `OPENWIKI:START` and `OPENWIKI:END` markers, and each role file repeats it.

Assistants read the wiki in two ways, and the `read-what-is-known` skill says which: through the read-only tools `openwiki_search` and `openwiki_read` when they have them, otherwise as files, starting at `openwiki/quickstart.md`. `tools/wiki_server.py` is a small read-only server of this project's own that offers exactly those two tool names over the Model Context Protocol and nothing that writes, so the OpenWiki tool's server or this one can be used without changing a role's instructions; `.mcp.json` names it. `knowledge.py about` is the search behind it.

Assistants do not write into `openwiki/`. The curating assistant drafts into a queue outside the wiki, in the same format, and a page enters the wiki only when a person accepts it. The factory's own rule sits on top: a wiki page is working memory and may be a draft, and what counts as signed is decided by the page's own `verified` lines, which only a person adds.

This follows the OpenWiki repository's README as it was read on 2026-11-25 and relayed to the assistant that built this part, which had no network and did not read it itself. It was not run against the OpenWiki tool, which is an npm package that could not be installed here. Where this project guessed: the exact form of the marker lines in `AGENTS.md`, the arguments and result shape of the two tools, and whether `quickstart.md` carries front matter (here it does). The format's checker kept in another repository of this project (the one pinned in `factory/checkers.yaml`, as an example) passed every page of `openwiki/` and stopped only at `INSTRUCTIONS.md`, a reserved file it does not know; that was checked by hand in November 2026 and no check here repeats it.

**Where this part stands, plainly.**

- *Built and tested here, by commands that run from a bare clone:* the exploring tool, the knowledge helpers, the wiki server, the role check, the renderer, the per-call check, the launcher and the two scripts the exploring skill ships, by their own self-tests; and the two loops end to end on the stand-alone example.
- *Run by separate assistants, once (historical):* the demo whose recipe is in `examples/baton-rouge`. Each role was a separate subagent of one model, started from its role file with a task and no memory of the others: an analysis assistant, a review assistant that returned holes, the analysis assistant answering, a second review by a fresh assistant, a curating assistant, and a second analysis assistant on a new question that used the drafted knowledge. Their tool restrictions were by instruction and the role file, not by a runner, and the coordinating role was played by the person's session. The demo's page says what it found; the record of that run, and of an earlier run by one instance playing every role, is at `records-2026-11`.
- *Reviewed by a working hydrologist, once (historical):* the single-instance run and the tools, read cold. Every central number reproduced; the science was found naive in ways the separate review assistant also found, independently; the tools were found wanting in ways that are now fixed, each with a self-test. `docs/reviews/ASSISTANTS-AND-EXPLORING.md` has every finding and what became of it.
- *Attacked independently, once:* a reviewer who did not build the tools attacked them on 2026-11-26 and found 2 blockers, 5 serious and 5 minor holes, each shown by running the tool. Set-aside data could be reached through a folder, a pattern, a tilde path or a word after `=`. The per-call check read a command differently from the shell that would run it, so a second command could ride behind a `#`. A shortened `--by` got past the name check. A look's script could record a review of its own lead under a fresh name. The reviewer could read the author's account where the example of that day kept it. `check-drafts --checker` ran any file. A lead could be reworded after its review and handed over with the old verdict. All twelve are fixed or restated, each with a self-test that reproduces the attack; `docs/reviews/ASSISTANTS-AND-EXPLORING.md` has every finding and what became of it.
- *Still owed:* a second independent attack. The fixes for the first were made and tested by one author, the same one for all of them, and nobody else has attacked them. Until someone does, read every line under "Enforced by a tool" below as "enforced as far as its author could break it".
- *Not exercised:* the Claude Code runner against Claude Code (the rendered files, the hook and the launcher are tested as scripts only, and the run by separate assistants did not go through them); an assistant started from `factory/agents/coordinating/agent.md`; a hand-over made by separate assistants; the naming of a reviewer by a coordinating assistant; anything against the OpenWiki tool; the kernel fence on any machine but the Linux one this was built on.
- *Enforced by a tool, on any machine:* that data is set aside before any look; that a look whose command names set-aside data is refused, with a site read the ways people write it, whether the file is named as a word or after an `=`; that a look whose command names a folder, a pattern, a tilde path, a variable or several paths in one word is refused outright; that a look's script runs in a scratch folder holding only the script and the files the command names, each read by the fence first; that what a look prints or leaves is read by the fence, and output that crosses it spoils the exploration and is withheld; that nothing a look writes in its folder is brought into the log, the receipts, the lead, the verdicts or the reviewer's folder, and that a script which writes into the exploration directly (possible only where there is no kernel fence) spoils it, with the log put back and the files it added taken out; that the study tool, the exploring tool and the knowledge tool refuse a command started from inside a look (they read their own ancestry; tested on Linux), and that the exploration log is held while a look runs; that every look, its inputs, its output and its figures are logged by checksum; that a recheck of a look made since refuses to run when any file the look was given has changed; that a number with a fraction in a lead, in any form it can be written, and a whole number given as a share, was printed whole by a look the lead cites or stands in a page of a listed wiki that was read; that a lead shows the order of looks and choices from the log; that a lead is refused until a reviewer has been named, and that a review is taken only from a name that was named before the lead it reviews was recorded, by a name that did none of the work; that the name that explored cannot review, name the reviewer or hand over; that an exploration does not end as a lead, and is not handed over, unless the lead as it stands (a correction of wording included) has been reviewed; that no note is resolved before the end; that a draft carries no signature, has sources its body cites, names as a source no path where there is no file, and says how it relates to what it overlaps; that `check-drafts` runs no checker whose checksum is not pinned in `factory/checkers.yaml`; that an import never writes over a signed page; that no tool a role calls takes a shortened option (the method scripts under `methods/gain/` take none either, since no kept record binds their bytes any longer). In a git work tree, that an exploration log rewritten or cut short since its last commit fails `check-log`.
- *Enforced by the kernel, on Linux 5.13 or later with Landlock, and nowhere else:* that a look's script, and every process it starts, can open nothing but its scratch folder, the system's own folders, the interpreter, and the launcher's program, cache and settings; and that a process a look detaches is ended with the look. Each look's receipt and its last printed line say whether the kernel fence held (`kernel`) or the machine has none (`scratch-only`). It was built and tested on one Linux machine.
- *Enforced by the Claude Code runner's per-call check, when a platform calls it, which has not been exercised:* a role's commands, taken only when the command is one plain line of one known shape with nothing in it a shell acts on and every option spelled out as the tool's own parser has it; its name in `--by`; where it writes; that the review role cannot read, search over, or hand to a tool the author's account, in `record/analysis/` or as a flat file in `record/` with `analysis` in its name; that only the coordinating role names a reviewer.
- *Not enforceable by one user on one machine, and not claimed:* that set-aside data is out of reach. A person, or an assistant with a shell, who can read a file can read it outside the tool. Where there is no kernel fence, a look's script can open any path it builds itself, and the tool catches it only if a date inside the window or a set-aside name comes back in what the look prints or leaves; a script that prints a mean and no date is not caught. With the kernel fence, a script can still use the network, read what is kept in the system's folders or the launcher's cache, and ask a service already running on the machine to act for it later. That a log was not rewritten before its first commit or posted fingerprint: the hash chain has no secret, so a log rewritten from its first line with every hash right, together with the record beside the studies, passes `check-log` on its own. Who is behind a typed name: the reviewer rule stops a name invented at the review, not a person or a process that types two names in the right order.
- *Still instruction and not enforcement:* that only knowledge is read before data is set aside (the tool records the page a boundary came from and refuses a data file there; it cannot see what else was read); that nothing is looked at outside the tool; that a choice is written down when it is made (the tool shows when it was written down, which is not the same); that every comparison inside a look is declared; that a number written out in words, or a whole number that is not a share, is true; that a role started outside its rendered file keeps to its role and its own place; that the coordinating role passes the review role nothing the analysis role said (the launcher refuses a task that names the author's place, and reads no further); that the reviewer is a separate assistant with a fresh context and not the author under the name the coordinator named; that an analysis assistant has not already read an answer to its question.
- *Left as it was:* `factory/factory.yaml` still calls the exploratory kind of study designed and not built, and one of its comments still speaks of the procedure file "beside the tool". It was not edited when the layout changed or when the records were taken out: its content is the owner's to change, and no path it names moved. The exploring loop is the tool described here, beside the procedure and not a kind of study inside it.

## What is in each folder

`tools/sf.py` is the study tool: one study, one study log, no language model in any check it makes. `factory/factory.yaml` is the procedure it reads; its `capability` block is filled in for the built-in example, so it names nothing outside this repository; a copy filled in for a real capability is `examples/baton-rouge/capability.yaml`, and a factory of your own fills in its own. `methods/gain/` is the built-in method, the gain of one record against another (`gain.py`, `confront.py`), with its known-answer tests (`test_cases.py`, `known_answer_tests.py`) and `system_trial.py`, which seals a blind test case for the system trial, reveals the sealed answer afterwards and writes the verdict into the study log, and runs the blind test of the system. `methods/built-in-pairing/pair_records.py` pairs two records by time; the gain method takes its pairing step as a parameter, and this is the one that ships. Both are prototypes for exercising the procedure, not the checked computation of any discipline; the method for a kind of data belongs to the repository where that science lives. `factory/change-log.jsonl` is the change log with predictions, the factory's record of its own changes; it holds two records, written from a practice run that is no longer kept here (historical; `records-2026-11`). `factory/templates/` holds the request a scientist fills in (`request.md`), a commented analysis plan with every key the tool reads (`analysis-plan.yaml`), the catalog of kinds of question an analysis assistant reads (`kinds-of-question.yaml`), and the checklist for bringing an existing pipeline in (`workflow-adapter.md`). `compute/` holds the contract for where it runs (`adapter.py`: a job spec, four verbs, a run log), one local reference place, the conformance test any place must pass and a test of that test, and the table of places (`places.yaml`: local is built; a cluster scheduler, a cloud job and MAAP, NASA's Multi-Mission Algorithm and Analysis Platform, are written down and not built).

## Try it

**What you need.** `git`; `uv` (https://docs.astral.sh/uv/), which runs every script here and on first use downloads what a script declares (Python 3.11 or later, and PyYAML); a shell (bash or zsh). After that first download nothing below uses the network. The numbers on this page were made on Linux with Python 3.13, from a bare copy of this repository with nothing beside it.

**From this repository alone.** The three commands under "See it work", and these, all from the top of a bare clone. The checks workflow (`.github/workflows/checks.yml`) runs every one of them on each pull request, in one job, with no other repository checked out.

```
uv run tools/sf.py check-plan --study examples/stand-alone/system-trial
uv run methods/built-in-pairing/pair_records.py --selftest
uv run compute/adapter.py conformance
uv run compute/adapter.py conformance --self-check
```

The plan check prints `plan check: the analysis plan is complete`. The pairing step's self-test ends with `selftest: PASS (5 of 5)`. The conformance test ends with `conformance (local): PASS (34 of 34)`, in about six seconds, and its self-check ends with `self-check: PASS (2 of 2 honest places pass all 34 checks; 30 of 30 wrong places fail; 8 of 8 local checks pass)`. The self-tests of the exploring tool, the knowledge helpers, the role check and the runners are listed under "The assistants and the two loops"; they too run from a bare clone.

**The numbers these documents cite, and how to get each today.** Both commands use the built-in method and nothing else.

```
uv run methods/gain/system_trial.py blind-test \
  --template examples/stand-alone/system-trial --n 200
uv run methods/gain/known_answer_tests.py \
  --executor methods/built-in-pairing/pair_records.py \
  --plan examples/stand-alone/system-trial/analysis-plan.yaml \
  --out /tmp/known-answers.json
```

The first is the blind test of the system on 200 cases, about six minutes here. Its last lines read `"false_support_rate": 0.0`, `"missed_true_rate": 0.18`, `"wrong_verdicts": 0`, and the block above them gives the counts: of the 100 cases where the idea was true, 82 supported and 18 inconclusive; of the 100 where it was false (50 at a gain of 0.90, 50 at 1.10), 94 refuted and 6 inconclusive. The second is the known-answer tests of the system trial's plan, 2000 synthetic records in each required setting, about a minute and a half. It prints the rates the lock would read: coverage 0.93 in the kind case and 0.93 in the worst hard case, false confirmation and false refutation right at the difference that matters at most 0.0405 each, a true idea supported 0.8405 of the time, a false one refuted 0.9175 of the time, and `"verdict": "PASS"`. Both are deterministic for a given platform; on another platform the last digit of a rate may differ.

**The optional demo.** `examples/baton-rouge` is the factory used with the knowledge, the data and one script of another repository of this project. Its page has the commands, and a workflow of its own (`.github/workflows/demo-with-hydrology.yml`) runs its steps when asked and once a week, never on a push. It is a demo, not a check of this repository.

Then docs/PLAN.md, Part A.

## Status, plainly

**Built and tested, each by a command above.** The study tool (175 of 175 self-tests). The built-in method and its known-answer tests. The system trial's plan through its plan check, known-answer tests, working data and rehearsal (the stand-alone example takes it to the lock on every run). The job contract and its local place (34 of 34 conformance checks, and a test of that test: 30 deliberately wrong places each fail it). The blind test of the system, on the built-in pairing step: 200 blind test cases, no wrong verdict; of the 100 cases where the idea was false none was supported (94 refuted, 6 inconclusive), and of the 100 where it was true 82 were supported and 18 inconclusive.

**Historical, and not reproduced here.** A first real study was planned on a real river gauge, and a practice run of it reached its known-answer tests and working data; the blind test of 200 was first made with that discipline's own pairing script and gave the same counts; a demo on real data was run twice. Those records, the draft plans of both studies and the tools of that day are at `records-2026-11`.

**What the blind test result is, and is not.** Its false cases sit at gains of 0.90 and 1.10, twice the five percent difference that matters. Every case is a kind one, with no trouble put in. The cases were chosen by the test harness (the script that drives the test), not sealed from it. Zero false supports in 100 cases still allows a true rate of up to about 3.6 percent. The evidence right at the difference that matters, and on hard cases, is carried by the known-answer tests, not by the blind test.

**Held by a control outside the tool, when that control is in place.** That a named person made the lock and the signature: the lock cites an approving review, and its commit is merged on a protected branch with its own approval before the opening. That a study log was not rewritten: its fingerprints are posted on the tracking issue. docs/PLAN.md Part A says who does each. Neither control has been exercised. The package lives in its own repository, where its checks run on every pull request; branch protection and required approvals are the repository owner's to switch on, here and in any repository where a study is run.

**Found when the fixes of the third review round were checked, and since closed.** A script named inside a shell string was not bound by the lock: a command must now be a launcher the tool knows followed by a script file, and anything else fails the plan check. The known-answer runner called the method in its own process, where the answer was in memory: the method now runs in a separate process that is given the data and nothing else. The power to refute when the idea is false can no longer be waived. **Still open from that check:** the other three required criteria can be waived with a stated reason, and no criterion has a floor under its value, so the values and the waivers are the person's to read in what the lock prints; and a system trial's sealed answer sits inside the study, where locked code could look for it by its path.

**Not done, by design.** Neither the lock nor the steward's signature was recorded, and no held-out data was fetched, opened or requested; those are a person's acts.

**Not done, by environment.** Anything that needs a data provider's network: no real record has been fetched by any tool here.

**Not built.** A schedule for the curating assistant, and any run of the assistants through the Claude Code runner (the roles are files, one runner is rendered, and separate assistants have been run from the role files by instruction; see "The assistants and the two loops"). The exploratory kind of study inside the procedure (the exploring loop is a tool beside it). The checks on the request's fields, and the answer to "can this be answered by the date?" before a method exists. The scientist's own approval at the lock (the tool records one person). The record of what has been opened across factories (the record is one file beside one set of studies). Every place to run but the local one, and any call from the study tool to the job contract: the tool runs its own commands on the machine it is on. A place where the analysis assistant has no route to the withheld values. An assistant that proposes changes to the procedure, and the adoption rule for such changes. The automation of the scheduled re-test. The blind test of the system with assistants in the loop.

**The four limits the study tool states at the top of its file, and what answers each.**

1. It cannot stop anyone reading public data outside the access gate. Nothing built answers this, and where the opening runs does not either. Only an analysis assistant working where it has no route to the withheld values would; that is not built and not planned for the first two studies. Until it is, the barrier for public data is instruction and evidence.
2. The names of who did what are typed, not proven, and the tool takes any local commit as the lock being committed. The answer is the protected branch and the approving reviews described above.
3. A study log that is rewritten from its first line, cut short, or added to by hand with the right hashes checks out on its own. A later edit is detectable only against a commit or a log fingerprint posted outside the workspace. Before the first of those nothing protects a log.
4. It cannot defend itself against a hostile interpreter. The answer is where the opening runs: somewhere clean that is not the workspace where the method was built. No such place is built yet, and the system trial's opening runs in the workspace.
