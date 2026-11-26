# Science Factory

**Open Science Pillars (OSP), a personal project (personal hat) · 2026-11-25 · concept, design, a tested study tool, and a build plan in two parts. Not a product of any employer or of any organization discussed in it.**

A science factory is an assisted study pipeline in which the plan is written down and locked before the data is opened (pre-registered, to those who use the word). It is designed to turn a question about archived observations into a signed finding or a recorded negative result, with assistants (always AI agents) doing the labor and an experiment they cannot argue with deciding what survives. No study has run to a finding yet. This package says what a science factory is, designs it, builds and tests the part that runs no language model, and records three rounds of attack on itself.

## Two ways of working

A scientist works in two ways. **Exploring** is most of the work: looking at data to find out what is there, trying, looking again, revising. **Confirming** is testing one claim, stated in advance, on data nobody has opened. This package builds both. The confirming way came first and is most of what follows. The exploring way now has a tool of its own (`mvp/loops/explore.py`), the assistants are defined as files, and what is learned goes back to a knowledge base through a queue of drafts; `TWO-WAYS-OF-WORKING.md` describes the two ways and the wall between them, and "The assistants and the two loops" below says what was added and what it does not yet do.

## What it is

You ask a question in your own words. With an assistant you write an **analysis plan**: what will be estimated, on which data, and what result would count for or against your idea. Some data is **held out**: by rule, nobody opens it yet. Before it is opened, the method has to pass **known-answer tests**: synthetic data built on your real sampling, with the truth put in by hand, including cases where your idea is false and cases right at the smallest difference you care about. It is the synthetic test you already run, aimed at the decision and not only at the estimate. Then a person, the steward (the person who holds a knowledge bundle and signs it), **locks** the plan and the code together. The tool opens the held-out data once and runs the locked analysis on it; it will not do so for an assistant that ran the tests. A separate **review assistant**, which did none of the study, reads the result, and the steward signs the finding or does not. Every step is written to a **study log**; once the log is committed and its fingerprints are posted outside the workspace, any later edit to it can be detected. What was learned about the data along the way goes back into the shared knowledge.

That paragraph is the design. What holds each sentence today (the tool, a control outside the tool, or nothing yet) is under "Status, plainly" at the end of this page and, stage by stage, in DESIGN.md.

## The five stages

| Stage | What happens |
|---|---|
| 1. Ask | You write a request in your own words. The analysis assistant asks four questions back, and the study is started with the request bound to it by checksum (`sf.py start --request`). |
| 2. Plan | The analysis plan is written, after a search of the shared knowledge for anything that already answers or limits the question, reading only observation metadata: values that cannot move the answer (times, places, quality flags; what else qualifies is decided for each plan). |
| 3. Test on known answers | The plan check, the known-answer tests, the working data (anything already looked at) and the rehearsals, repeated freely. Every attempt the tool runs is logged. |
| 4. Open the held-out data once | The access gate, a step of the tool, fetches the held-out data and runs the locked analysis, once. |
| 5. Review, sign and learn | The finding is written from run receipts and attached. A review assistant that did none of the study checks it. The steward signs the finding or records the decision not to. Notes go into the shared knowledge, and what should change goes into the procedure. |

A **run receipt** is the record a run writes, with its code and inputs by checksum and every number it produced, so anyone can re-check the result without trusting whoever ran it. After this it is called a receipt.

Two acts belong to people: **the lock**, between Test and Open, and **the steward's signature**. The design has the scientist approve the lock with the steward; the tool takes one person's name today, and the second approval is scheduled, not built. The procedure file counts nine steps where this page counts five stages, because it lists the two acts, the learning and the close as steps of their own, and `sf.py status` reports those nine names (`ask`, `plan`, `test`, `lock`, `open`, `review`, `signature`, `learn`, `close`). Under every stage sits the **study log**. Where the computing runs is a separate contract (`mvp/compute/`): it is built and tested with one local place, and the study tool does not call it yet.

## What to read

| File | What it is |
|---|---|
| `README.md` | this page: what it is, the five stages, how to try it, where it stands |
| `DESIGN.md` | the concept and the whole design in one document: knowledge factories, software factories, what a science factory borrows and refuses, experiments on data in the loop, then the five stages, the study log and where it runs, each with its parts, what goes in and out, what is held today and by what, and what is only designed; candidate platforms compared |
| `PLAN.md` | the build plan in two parts (the system trial, then the first real study): every component and what represents it, what was measured, prompts, commands, the steward's decisions |
| `WORDS.md` | the word list: each plain word beside the earlier word it replaced, with the old and new names of every file, key, log event, check and command |
| `reviews/RED-TEAM.md` | three rounds of attack: 33 findings from three reviewers, 15 from a second pass, and 62 from a third round of three reviewers (5 of them blockers) made after the revision and the renames; what each changed, and what is still open |
| `reviews/SCIENTISTS.md` | the factory from the chair of the people who would ask it questions: how they ask, kinds of question, other uses, bringing a workflow in |
| `TWO-WAYS-OF-WORKING.md` | how scientists work: exploring, which is most of it, and confirming; what the factory does for each and why they are kept apart |
| `CREATE-A-FACTORY.md` | how to define a factory of your own as files: a quickstart, the procedure file key by key, and how it compares with a software factory |
| `proposals/watching-studies.md` | proposed, not built: studies that keep watching as data arrives, and choices that expire |
| `roadmap-initiative.yaml` | the plan as one initiative and ten deliverables, in the organization's roadmap form |
| `mvp/` | the study tool, the exploring tool, the knowledge helpers, the procedure, the method prototypes, two studies not yet started, the practice runs |
| `assistants/`, `skills/`, `runners/`, `openwiki/`, `examples/` | the assistants as files, their skills, the runners, the wiki, and two examples; see "The assistants and the two loops" |
| `reviews/ASSISTANTS-AND-EXPLORING.md` | the review register for the assistants and the two loops: one round by the builder, two independent rounds owed |

## The assistants and the two loops

Added on 2026-11-26. Before it, the package was a rulebook and a referee with no players.

**Four layers, each resting on the one below.** The referee: `mvp/sf.py` and its checks, with no language model. Roles as files: `assistants/`, one Markdown file for each of the coordinating, analysis, review and curating assistants, in a form no agent platform owns. The knowledge: a wiki of Markdown pages, read before work and drafted for after it; a person signs. A runner: `runners/claude-code/` starts a role with its tools as a Claude Code subagent, and `runners/by-hand/` checks one command at a time. Two rules run through all four: an assistant never decides whether a step counts, a tool does; and nothing a role needs lives only in a platform's settings.

| Where | What it is |
|---|---|
| `assistants/` | the four roles as files (what each may call, must never see, reads, writes and hands on), and `check_roles.py`, which fails when they and the procedure's `assistants` block disagree |
| `skills/` | five skills, procedure only: `read-what-is-known`, `explore-a-record`, `write-up-a-lead`, `draft-a-knowledge-page`, `review-work` |
| `mvp/loops/explore.py` | the exploring tool: data is set aside first, every look is logged, choices are recorded, and it ends in a lead, a note, a method or a stop |
| `mvp/loops/knowledge.py` | the knowledge helpers: list the pages that bear on a question with who signed each; check a queue of drafts; import pages from another knowledge base |
| `mvp/loops/wiki_server.py` | a read-only server for a wiki directory with the two tool names OpenWiki uses, `openwiki_search` and `openwiki_read` |
| `openwiki/`, `AGENTS.md` | this repository's knowledge base, a wiki in OpenWiki's form, for the stand-alone example; and the pointer to it |
| `runners/` | the Claude Code runner (rendered roles and skills with a drift check, a check on every tool call, a launcher that keeps the record) and the by-hand runner |
| `.claude/`, `.mcp.json` | the rendered files Claude Code reads; never edited by hand |
| `examples/stand-alone/` | the two loops end to end on a synthetic record with a known answer; runs from a fresh clone |
| `examples/baton-rouge/` | a demo on real data and knowledge from the hydrology capability, with the whole record kept |
| `reviews/ASSISTANTS-AND-EXPLORING.md` | what was attacked in this part, what changed, what remains |

**Why `mvp/loops/`.** The study tool counts every Python file beside a plan's code as part of that code. A new file in `mvp/` would therefore change the code identity of the practice runs and of both studies, so the two new tools sit one folder down, where the study tool does not look.

**Try this part.** From the repository, with nothing beside it:

```
uv run mvp/loops/explore.py selftest
uv run mvp/loops/knowledge.py selftest
uv run mvp/loops/wiki_server.py --selftest
uv run assistants/check_roles.py
uv run assistants/check_roles.py --selftest
uv run runners/claude-code/render.py --check
uv run runners/claude-code/render.py --selftest
uv run runners/claude-code/allow.py --selftest
uv run runners/claude-code/run_role.py --selftest
uv run examples/stand-alone/run.py
```

They end with `PASS (109 of 109)`, `PASS (44 of 44)`, `PASS (12 of 12)`, `check-roles: PASS (4 roles; ...)`, `PASS (20 of 20)`, `render --check: PASS (13 rendered files)`, `PASS (11 of 11)`, `PASS (57 of 57)`, `PASS (6 of 6)` and `stand-alone example: PASS (21 of 21 steps)`.

**The knowledge base is a wiki, in OpenWiki's form.** A repository's wiki lives in `openwiki/`: Markdown pages in the Open Knowledge Format v0.2 (front matter with a non-empty `type`, and where present `generated`, `sources`, `verified`, `status`, `stale_after`), with `index.md` and `log.md` reserved, `quickstart.md` as the place to start, and `INSTRUCTIONS.md` as the owner's brief. That is the same format the Open Science Pillars bundles use, so a bundle is read through the same door by naming its directory (or copied in with `knowledge.py import`, which keeps where each page came from, its status and who signed it). `AGENTS.md` at the top of the repository carries the pointer to the wiki between `OPENWIKI:START` and `OPENWIKI:END` markers, and each role file repeats it.

Assistants read the wiki in two ways, and the `read-what-is-known` skill says which: through the read-only tools `openwiki_search` and `openwiki_read` when they have them, otherwise as files, starting at `openwiki/quickstart.md`. `mvp/loops/wiki_server.py` is a small read-only server of this project's own that offers exactly those two tool names over the Model Context Protocol and nothing that writes, so the OpenWiki tool's server or this one can be used without changing a role's instructions; `.mcp.json` names it. `knowledge.py about` is the search behind it.

Assistants do not write into `openwiki/`. The curating assistant drafts into a queue outside the wiki, in the same format, and a page enters the wiki only when a person accepts it. The factory's own rule sits on top: a wiki page is working memory and may be a draft, and what counts as signed is decided by the page's own `verified` lines, which only a person adds.

This follows the OpenWiki repository's README as it was read on 2026-11-25 and relayed to the assistant that built this part, which had no network and did not read it itself. It was not run against the OpenWiki tool, which is an npm package that could not be installed here. Where this project guessed: the exact form of the marker lines in `AGENTS.md`, the arguments and result shape of the two tools, and whether `quickstart.md` carries front matter (here it does). The organization's own checker passes every page of `openwiki/` and stops only at `INSTRUCTIONS.md`, a reserved file it does not know.

**Where this part stands, plainly.**

- *Built and tested here:* the exploring tool, the knowledge helpers, the wiki server, the role check, the renderer, the per-call check and the launcher, by their own self-tests, and the two loops end to end on the stand-alone example.
- *Run once, by one assistant playing every role:* the demo in `examples/baton-rouge`. The roles were held to their commands by the by-hand runner. There was no second assistant, so the reviews in it are not independent and no role had a fresh context. Its page says so first.
- *Not exercised:* anything against the OpenWiki tool; and the Claude Code runner against Claude Code. The build environment could not start an assistant. The rendered files, the hook and the launcher are tested as scripts only.
- *Not done:* the two independent reviews this part was meant to have (an attacker and a working hydrologist). The builder attacked its own tools and closed eleven findings; `reviews/ASSISTANTS-AND-EXPLORING.md` records that and sets out the two reviews still owed.
- *Still instruction and not enforcement:* that a script run as a look reads nothing its command does not name (the network, a path built while running); that a role started outside its rendered file keeps to its role; that the coordinating role passes the review role nothing the analysis role said; who is behind a typed name.
- *Left as it was:* `mvp/procedure.yaml` still calls the exploratory kind of study designed and not built. It was not edited, because `sf.py status` prints the procedure's checksum and the practice runs must report what they reported. The exploring loop is the tool described here, beside the procedure and not a kind of study inside it.

## What is in `mvp/`

`sf.py` is the study tool: one study, one study log, no language model in any check it makes. `procedure.yaml` is the procedure it reads. `test_cases.py`, `gain.py`, `confront.py` and `known_answer_tests.py` are the known-answer tests and the method prototypes for the first claim. `system_trial.py` seals a blind test case for the system trial, reveals the sealed answer afterwards and writes the verdict into the study log, and runs the blind test of the system. `studies/STUDY-0000` is the system trial and `studies/STUDY-0001` is the first real study; both are drafts and not started. `exhibits/` holds what the build environment ran: the practice runs and the blind test of the system. `change-log.jsonl` is the change log with predictions, the factory's record of its own changes; it holds two records. `templates/` holds the request a scientist fills in (`request.md`), a commented analysis plan with every key the tool reads (`analysis-plan.yaml`), the catalog of kinds of question an analysis assistant reads (`kinds-of-question.yaml`), and the checklist for bringing an existing pipeline in (`workflow-adapter.md`). `compute/` holds the contract for where it runs (`adapter.py`: a job spec, four verbs, a run log), one local reference place, the conformance test any place must pass and a test of that test, and the table of places (`places.yaml`: local is built; a cluster scheduler, a cloud job and MAAP, NASA's Multi-Mission Algorithm and Analysis Platform, are written down and not built).

## Try it

**What you need.** `git`; `uv` (https://docs.astral.sh/uv/), which runs every script here and on first use downloads what a script declares (Python 3.11 or later, and PyYAML); a shell (bash or zsh). After that first download nothing below uses the network. The numbers on this page were made on Linux with Python 3.13.

**The layout.** Three directories side by side in one folder, called `<root>` here:

| Directory | What it is | Address and commit |
|---|---|---|
| `<root>/science-factory` | this package | https://github.com/open-science-pillars/science-factory |
| `<root>/hydrology` | the hydrology capability: the method under test is its sanctioned executor (the script that capability ships for comparing a satellite record with a gauge) | https://github.com/open-science-pillars/hydrology at commit `f9850d08c526139407eedf13ee3f12effbe83594` |
| `<root>/nasa-daac-knowledge` | the provider knowledge and its tools; only the first real study (STUDY-0001) uses it, for the findings checker | https://github.com/open-science-pillars/nasa-daac-knowledge at commit `c04ae2e156ca8672c7724254a2c738bd252e9de6` |

Those are the addresses and commits recorded in the checkouts the practice runs used (both commits are dated 2026-09-20); the addresses were not fetched again when this page was written. To get them:

```
cd <root>
git clone https://github.com/open-science-pillars/hydrology
git -C hydrology checkout \
  f9850d08c526139407eedf13ee3f12effbe83594
git clone \
  https://github.com/open-science-pillars/nasa-daac-knowledge
git -C nasa-daac-knowledge checkout \
  c04ae2e156ca8672c7724254a2c738bd252e9de6
```

Then, from `<root>`:

```
cd <root>
uv run science-factory/mvp/sf.py selftest
uv run science-factory/mvp/system_trial.py blind-test \
  --template science-factory/mvp/studies/STUDY-0000 \
  --n 40
uv run science-factory/mvp/sf.py status \
  --study science-factory/mvp/exhibits/system-trial-ready-STUDY-0000
uv run science-factory/mvp/compute/adapter.py conformance
```

What each prints, and how long it took here:

1. The self-test ends with `selftest: PASS (173 of 173)`, in about 25 seconds.
2. The blind test of the system on 40 cases takes two to three minutes. It prints a summary of the known-answer tests, two lines for each case as it goes, and then its result, which ends with `"wrong_verdicts": 0` and `"every_run_ready_for_signature": true`.
3. `status` prints `"stage": "lock"` and `"who": "people"`: the exhibit is waiting for a person. That is what it prints when the hydrology checkout is at the commit above. On any other commit it prints `"stage": "test"` with a `why` that names the file that differs, which is the study tool doing its job: the code that would read the data is not the code that was tried.
4. The conformance test ends with `conformance (local): PASS (34 of 34)`, in about six seconds.

Without the hydrology checkout only the first and the last run; the second ends in a refusal that names the missing checkout, and the third reports `"stage": "test"`.

To re-derive the known-answer test evidence in the practice run (about a minute; the comparison is byte for byte on the same platform):

```
H=hydrology
E=$H/skills/swot-hydro/scripts
F=$H/verification/fixtures/confrontation
X=science-factory/mvp/exhibits/practice-run-STUDY-0001
uv run science-factory/mvp/known_answer_tests.py \
  --executor $E/load_swot_confrontation.py \
  --sampling $F/swot_gauge_baton_rouge_2024.json \
  --check $X/receipts/known-answers.json
```

It ends with `check: PASS (recomputed identically)`.

Then PLAN.md, Part A.

## Status, plainly

**Built and tested in the build environment.** The study tool (173 of 173 self-tests). The known-answer tests for the first claim. Both analysis plans through their plan check, known-answer tests and working data. The job contract and its local place (34 of 34 conformance checks, and a test of that test: 30 deliberately wrong places each fail it). The blind test of the system: 200 blind test cases, no wrong verdict; of the 100 cases where the idea was false none was supported (94 refuted, 6 inconclusive), and of the 100 where it was true 82 were supported and 18 inconclusive.

**What the blind test result is, and is not.** Its false cases sit at gains of 0.90 and 1.10, twice the five percent difference that matters. Every case is a kind one, with no trouble put in. The cases were chosen by the test harness (the script that drives the test), not sealed from it. Zero false supports in 100 cases still allows a true rate of up to about 3.6 percent. The evidence right at the difference that matters, and on hard cases, is carried by the known-answer tests, not by the blind test.

**Held by a control outside the tool, when that control is in place.** That a named person made the lock and the signature: the lock cites an approving review, and its commit is merged on a protected branch with its own approval before the opening. That a study log was not rewritten: its fingerprints are posted on the tracking issue. PLAN.md Part A says who does each. Neither control has been exercised. The package now lives in its own repository (open-science-pillars/science-factory), where its checks run on every pull request; branch protection and required approvals are the repository owner's to switch on.

**Found when the fixes of the third review round were checked, and since closed.** A script named inside a shell string was not bound by the lock: a command must now be a launcher the tool knows followed by a script file, and anything else fails the plan check. The known-answer runner called the method in its own process, where the answer was in memory: the method now runs in a separate process that is given the data and nothing else. The power to refute when the idea is false can no longer be waived. **Still open from that check:** the other three required criteria can be waived with a stated reason, and no criterion has a floor under its value, so the values and the waivers are the person's to read in what the lock prints; and a system trial's sealed answer sits inside the study, where locked code could look for it by its path.

**Not done, by design.** Neither the lock nor the steward's signature was recorded, and no held-out data was fetched, opened or requested; those are a person's acts.

**Not done, by environment.** Anything that needs the provider's network: the rehearsal of the opening path and the fetch of observation metadata for the first real study.

**Not built.** A schedule for the curating assistant, and any run of the assistants by a platform (the roles are files and one runner is rendered, see "The assistants and the two loops"). The exploratory kind of study inside the procedure (the exploring loop is a tool beside it). The checks on the request's fields, and the answer to "can this be answered by the date?" before a method exists. The scientist's own approval at the lock (the tool records one person). The record of what has been opened across factories (the record is one file beside one set of studies). Every place to run but the local one, and any call from the study tool to the job contract: the tool runs its own commands on the machine it is on. A place where the analysis assistant has no route to the withheld values. An assistant that proposes changes to the procedure, and the adoption rule for such changes. The automation of the scheduled re-test. The blind test of the system with assistants in the loop.

**The four limits the study tool states at the top of its file, and what answers each.**

1. It cannot stop anyone reading public data outside the access gate. Nothing built answers this, and where the opening runs does not either. Only an analysis assistant working where it has no route to the withheld values would; that is not built and not planned for the first two studies. Until it is, the barrier for public data is instruction and evidence.
2. The names of who did what are typed, not proven, and the tool takes any local commit as the lock being committed. The answer is the protected branch and the approving reviews described above.
3. A study log that is rewritten from its first line, cut short, or added to by hand with the right hashes checks out on its own. A later edit is detectable only against a commit or a log fingerprint posted outside the workspace. Before the first of those nothing protects a log, and the logs in `mvp/exhibits/` have neither.
4. It cannot defend itself against a hostile interpreter. The answer is where the opening runs: somewhere clean that is not the workspace where the method was built. No such place is built yet, and the system trial's opening runs in the workspace.
