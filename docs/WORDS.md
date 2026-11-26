# The words, and what was simplified

**Open Science Pillars (OSP), a personal project (personal hat) · 2026-11-25 · plain words and fewer moving parts, with nothing the system does taken away. Applied on 2026-11-25 in two passes: first to the documents, templates and messages, then to every name on disk, inside the files, in the study log and on the command line. A third review round then changed a few more names; they are in the last tables.**

The package grew by accretion: a concept, a design with thirteen sections, a build plan, two reviews, twenty commands, and a vocabulary invented along the way (spine, broker, ledger, look, rung). A scientist does not need any of those words. This review does two things. It replaces the invented vocabulary with plain words, and it finds what can be merged or dropped from view without changing behavior.

The first draft of the word list was then read cold by three readers in role (a hydrologist who has never met blind analysis, an agency scientist who writes for managers, an ocean modeler). They rejected a good part of it (no count was kept), mostly words that were plain to one field and wrong in another. The list below is the corrected one, and a later section says what they caught.

## What it is, in a scientist's words

You ask a question in your own words. With an assistant you write an **analysis plan**: what will be estimated, on which data, and what result would count for or against your idea. Some data is **held out**: by rule, nobody opens it yet. Before it is opened, the method has to pass **known-answer tests**: synthetic data built on your real sampling, with the truth put in by hand, including cases where your idea is false and cases right at the smallest difference you care about. It is the synthetic test you already run, aimed at the decision and not only at the estimate. Then a person, the steward (the person who holds a knowledge bundle and signs it), **locks** the plan and the code together. The tool opens the held-out data once and runs the locked analysis on it; it will not do so for an assistant that ran the tests. A separate **review assistant**, which did none of the study, reads the result, and the steward signs the finding or does not. Every step is written to a **study log**; once the log is committed and its fingerprints are posted outside the workspace, any later edit to it can be detected. What was learned about the data along the way goes back into the shared knowledge.

That paragraph is the design. README.md and DESIGN.md say what holds each sentence today.

## The words

The left column is what the package said before.

| Before | Now | Note |
|---|---|---|
| work order | **study** | |
| brief | **request** | |
| registration | **analysis plan** | |
| rung, tier, D0 to D5 | named, never numbered | the keys in the plan file are the names too |
| D0 validate | **plan check** | |
| D1 planted truth, planted world | **known-answer test** | a modeler's twin experiment; said once |
| nuisance world | **hard case** | the idea is true or false, and something else is also going on |
| limit world | **beyond-limits case** | where the method is known not to hold; reported, never required |
| margin | **the difference that matters** | a statistician's equivalence margin; said once |
| band edge | **right at that difference** | |
| D2 development data | **working data** | anything you or your group have already looked at |
| rehearsal | **rehearsal** | stays: it is required and recorded |
| G1, freeze | **the lock** | plan and code together, by a person, the steward; the design adds the scientist's approval |
| D3 confirmatory data | **held-out data** | |
| look | **opening the held-out data** | unblinding, to those who use the word; said once |
| broker | **access gate** | a step of the tool, not a person or an office |
| look budget | **openings allowed** | normally one |
| look registry | **record of what has been opened** | |
| void a look | **void an opening that read nothing** | only one whose fetch failed and left nothing behind; never one that read data |
| D4 | **repeat at an independent site** | |
| D5 standing look | **scheduled re-test** | |
| G2 | **the steward's signature** | |
| ledger | **study log** | |
| spine | **study tool** | keeps the log and enforces the procedure |
| blueprint, factory definition | **procedure** | the written procedure every study follows |
| anchor, anchored head | **log fingerprint**, posted outside the workspace | |
| attest, attestation | **log check** | |
| run record | **run log** | |
| design fields | **observation metadata** | values that cannot move the answer whatever the withheld values turn out to be, once every choice in the analysis is fixed: usually times, places and quality flags; an independent record only when its plan says so and why |
| outcome fields | **withheld values** | |
| estimand | **the quantity estimated** | |
| claim shape | **kind of question** | |
| decision map | **what I will do with each answer** | |
| flag | **note** | "flag" already means data quality to these readers |
| foreman, experimenter | **coordinating assistant** | "assistant" always means an AI agent; it walks the procedure and starts the opening, which the tool refuses to an actor that ran the tests |
| framer, builder | **analysis assistant** | one role, two tasks: it writes the plan, and it builds and tests the method |
| curator | **curating assistant** | |
| reviewer | **review assistant** | |
| scorers | **process scorecard** | |
| benchmark, sealed world | **blind test of the system** | |
| acceptance order | **system trial** | |
| exploratory order | **exploratory study** | |
| improvement memory | **change log with predictions** | |
| compute target | **where it runs** | |
| factory instance per product surface | **one factory per capability** | |
| bar, pass bar | **criterion**, plural criteria | a pass or fail threshold on a rate the known-answer tests measure; readers took "bar" for an error bar |
| "the result file", as the gloss of a receipt | **run receipt** at first mention on a page, glossed once; after that, receipt | the earlier gloss dropped the property that matters: see below |

Words that stay because they are already the organization's or already science's: finding, steward, run receipt, interval, coverage, power, capability, validity domain. Three of them are glossed once on each page that uses them. A *run receipt* is the record a run writes, with its code and inputs by checksum and every number it produced, so anyone can re-check the result without trusting whoever ran it; after its first mention on a page it is called a receipt. *Power* is how often a test reaches the right firm answer when there is one to reach. A *validity domain* is a signed statement of the scope in which a class of claim may be made. "Science factory" stays as the name and is described on first use as an assisted study pipeline in which the plan is written down and locked before the data is opened. People are always called people (the scientist who asked, the steward); anything called an assistant is an AI agent.

## Words with more than one sense

These could not all be given one sense each, so each sense is named here.

| Word | Its senses in this package |
|---|---|
| lock | **the lock** is the act by a person that binds the plan and the code. A *lockfile* is the file that pins every library version, and the organization's *release lock* is the file of checksums written for a release; neither has anything to do with the lock |
| open | **opening** the held-out data; an *open note* is one not yet resolved. For anything not yet decided the documents say "undecided"; the worked request of the first real study that was planned marked such lines OPEN (historical; `records-2026-11`) |
| gate | the **access gate** is a step of the tool. The organization also calls a repository's required checks before a merge its gate (hence the deliverable `findings-checker-in-gate`), and the roadmap file has a field `gate:` for a decision a person takes before work starts. The documents say "required check" for the second |
| confirmatory | in every status that begins "confirmatory study": the study tests a claim written down beforehand on data nobody had opened. Its opposite is exploratory |
| the method builder | in the two files under `compute/`: whoever built the method, which is the analysis assistant or the person running it |

Five kinds of trial run have near names. *Known-answer tests*: the method on synthetic data with the truth put in, before the lock, repeated freely. A *rehearsal*: what the opening depends on (its fetch, the form of the finding) run once on working data, before the lock. A *practice run*: what the build environment did with a study, stopping before any act by a person; none is kept in this repository, the stand-alone example makes one fresh on every run, and those made in November 2026 are at the branch `records-2026-11`. The *system trial*: one whole study on a blind test case sealed at its opening, with a person's lock and signature (its plan is `examples/stand-alone/system-trial`). The *blind test of the system*: many such cases run unattended by a harness (the script that drives it), with no person, to count wrong verdicts.

## What can be simpler without changing what it does

**Five stages, not thirteen subsystems.** Ask. Plan. Test on known answers. Open the held-out data once. Review, sign and learn. Two things sit under all five and are named once: the study log, and where the computing happens (a contract the study tool does not call yet). The thirteen design sections collapse onto those seven headings with nothing removed; improving the procedure and "one factory per capability" become two short closing sections. The procedure file and `sf.py status` count nine steps, because the two acts by people, the learning and the close are steps of their own there.

**The ladder loses its numbers.** In prose: plan check, known-answer tests, working data, held-out data, a repeat at an independent site, a scheduled re-test.

**Two acts by people, by name.** The lock and the steward's signature. Same acts, same people, same evidence.

**Four assistants, not six roles.** What the tool separates, by typed name, is the assistant that ran the tests from the opening (the access gate refuses it) and from the review (the review assistant must have done none of the study). Nothing in it separates the framer from the builder. So: coordinating, analysis, review and curating assistants, and two people.

**Three documents to read, not six.** A front door in plain words (the paragraph above, the five stages, how to try it). One design document (the concept and the architecture merged under the seven headings). One build plan. The red-team register and the scientist review move to a `reviews/` folder as the evidence behind the design.

**Twenty commands under the five stages.** The commands do what they did; the help groups them by stage, and each has one plain name. The earlier names are gone.

| Stage | Before | Now |
|---|---|---|
| Ask | `open`, `status`, `close` | `start`, `status`, `close` |
| Plan | `validate` | `check-plan` |
| Test | `run --tier D1`, `run --tier D2`, `rehearse` | `test known-answers`, `test working-data`, `rehearse` |
| Open | `freeze`, `look`, `void` | `lock`, `open-held-out`, `void-unread` |
| Review, sign, learn | `attach`, `review`, `g2`, `flag`, `curate`, `resolve`, `improve`, `score` | `attach`, `review`, `signature`, `note`, `curation-list`, `resolve`, `log-change`, `scorecard` |
| The log | `head`, `attest`, `selftest` | `fingerprint`, `check-log`, `selftest` |

**Statuses that keep their meaning.** "Confirmatory, ready for the steward" becomes "confirmatory study, ready for the steward's signature". "Confirmatory, anchored heads owed" becomes "confirmatory study, log fingerprints missing". The word confirmatory and the steward stay in the string, because dropping either changes what it says. The plain string is the status; there is no second spelling. The log check gives exactly one of these: `in progress`; `closed before any opening (OUTCOME)`; `exploratory study`; `the study log or its files do not check out`; and, each beginning `confirmatory study,`: `held-out data opened without a result (TEST)`, `a planned opening remains (TEST)`, `waiting for the finding to be attached`, `waiting for the review assistant`, `blocked by review`, `log fingerprints missing (...)`, `ready for the steward's signature`, `signed by the steward`, `the steward declined to sign`. The last two end with `; closed as OUTCOME` once the study is closed.

## The architecture, before and after

The same system, drawn twice. Nothing in the first picture is missing from the second; the table under them says where each box went. The first picture is in the earlier words on purpose.

**Before** (21 boxes, 28 arrows):

![The architecture as first drawn, in the earlier words, with 21 boxes and 28 arrows: a chain of thirteen boxes from the scientist's brief to scorers and a benchmark, with the signed knowledge, the factory definition and the improver on the left, and the development tiers, the compute targets, the flag queue, the curator and the steward on the right.](diagrams/architecture-before.svg)

**Simplified** (13 boxes: five numbered stages, two acts by people, and the held-out data drawn once):

![The confirming loop. A scientist's request passes down through five stages inside the study log (1 Ask, 2 Plan, 3 Test on known answers, 4 Open the held-out data once, 5 Review, sign and learn) and ends in a finding or a recorded no. Two acts by people are marked: the lock, between Test and Open, and the steward's signature, after Review. Beside the stages: the procedure, read at Ask and changed after Review; shared knowledge, read at Plan and fed by notes; and where the computing runs, which the stages do not call yet.](diagrams/confirming-loop.svg)

| Boxes before | Simplified |
|---|---|
| brief, interview, intake | 1 Ask |
| frame, signed knowledge consulted | 2 Plan, reading shared knowledge |
| build, development tiers D0 to D2, rehearsals | 3 Test, repeated freely |
| G1 readiness | the lock |
| experiment, broker, confirmatory tiers D3 and D4 | 4 Open the held-out data once, and the held-out data it opens |
| review, assemble | 5 Review, sign and learn |
| G2 signature | the steward's signature |
| flags, flag queue, curator, steward signs knowledge | notes into shared knowledge (the curating assistant drafts, the steward signs) |
| scorers, benchmark, improver, factory definition | what to change, into the procedure |
| compute targets | where it runs |
| the ledger (in every box, never drawn) | the study log, drawn once around all five stages |

What the second picture leaves to the text, on purpose: that the review assistant did none of the study, that notes come from every stage and not only the last, and that a change to the procedure is a reviewed proposal with a prediction attached. Each is one sentence under its stage in the design document.

## What must not be simplified away

Plain words must not blur what makes this more than a pipeline. These are the rules, whatever they are called; DESIGN.md says which of them the tool holds, which a control outside the tool holds, and which are convention:

- The plan and the code are locked together, by a person, before any held-out data is opened, and the locked code is the code that runs.
- A decision rule is shown, on known-answer tests, to fail when the idea is false and to behave right at the difference that matters, before the lock.
- Held-out data is opened once per subject and window, by the access gate. A second study on the same data is exploratory. An opening can be voided only when its fetch failed and left nothing behind.
- The tool only ever adds to the study log, and the log is checked against fingerprints posted where the workspace cannot rewrite them.
- The review assistant did none of the study. Its block stands until it lifts it.
- Notes are never deleted. A signature is a person's.
- Inconclusive is a result. The limits the tests measured are stated in the finding.

## What the three readers caught

Words that are native to one field and wrong in another were the main failure of the first draft. "Unblinding" was clear only to those who already do it. "Twin experiment" was clear only to the modeler. "Tolerance" read as a solver or instrument setting. "Data custodian" names an accountable office in data governance. "Audit" implies auditors. "Checkpoint" is a restart file. "Dry run" in software does nothing, and this one is required. "Flag" is a data quality flag. "Analyst" and "reviewer" read as people. "Protocol" is, in trials, the pre-registered plan itself. And three simplifications had quietly dropped meaning: an alias that suggested any opening could be cancelled, a status that lost the word confirmatory, and a "plan lock" that hid that the code is locked too. All of these are corrected above. The readers were language models in role; the first real scientist who trips on a word outranks them.

## Names on disk, in the files and on the command line

The first pass changed what the documents and the tool's messages say and left these names alone, on the reasoning that the practice runs are hash-chained to them. That was the wrong line to draw: they are the first things a scientist meets. Nothing had landed and no real lock existed, so the second pass renamed them as a clean break, with one name per thing and no aliases.

| Files and directories, before | Now |
|---|---|
| `work-orders/WO-0000`, `WO-0001` | `studies/STUDY-0000`, `STUDY-0001` (since taken out; see the last section) |
| `registration.yaml` | `analysis-plan.yaml` |
| `order.md` | `study.md` |
| `ledger.jsonl` | `study-log.jsonl` |
| `looks.jsonl` | `openings.jsonl` |
| `improvement-memory.jsonl` | `change-log.jsonl` |
| `curator-queue.json` | `curation-list.json` |
| `flags/FLAG-001.json` | `notes/NOTE-001.json` |
| `factory.yaml` | `procedure.yaml` |
| `d1_experiments.py` | `known_answer_tests.py` |
| `worlds.py` | `test_cases.py` |
| `acceptance.py` | `system_trial.py` |
| `compute/targets.yaml` | `compute/places.yaml` |
| `receipts/d1.json`, `d2.json`, `d3.json` | `receipts/known-answers.json`, `working-data.json`, `held-out.json` |

| Keys in the analysis plan, before | Now |
|---|---|
| `work_order` | `study` |
| `estimand` | `quantity_estimated` |
| `data.development`, `data.confirmatory` | `data.working`, `data.held_out` |
| `outcome_fields` | `withheld_values` |
| `design_fields` | `observation_metadata` |
| `tiers` with `D1`, `D2`, `D3` | `tests` with `known-answers`, `working-data`, `held-out` |
| `look_budget` | `openings_allowed` |
| `registered_handling` | `planned_handling` |
| `standing`, `next_look` | `scheduled_retest`, `next_window` |

| Events in the study log, before | Now |
|---|---|
| `order.opened`, `order.closed` | `study.started`, `study.closed` |
| `tier.run` | `test.run` |
| `gate.G1.approved` | `lock.recorded` |
| `look.opened`, `look.closed`, `look.voided` | `opening.started`, `opening.finished`, `opening.voided` |
| `gate.G2.recorded` | `signature.recorded` |
| `flag.raised`, `flag.resolved` | `note.raised`, `note.resolved` |
| `improvement.recorded` | `change.recorded` |

| Checks named in the procedure, before | Now |
|---|---|
| `opened` | `started` |
| `registration-valid` | `plan-complete` |
| `development-tiers-green`, `rehearsals-green` | `tests-pass`, `rehearsals-pass` |
| `frozen` | `locked` |
| `looks-complete` | `openings-complete` |
| `flags-resolved` | `notes-resolved` |
| `registration-adherence` | `plan-adherence` |
| `look-discipline`, `clean-look` | `opening-discipline`, `no-failed-opening` (called `clean-opening` until the third review round) |
| `human-gates` | `acts-by-people` |
| `flags-curated` | `notes-curated` |

| Options on the command line, before | Now |
|---|---|
| `--wo` | `--study` |
| `run --tier D1`, `run --tier D2` | `test known-answers`, `test working-data` |
| `look --tier D3` | `open-held-out` |
| `--factory` | `--procedure` |
| `flag --note "..."` | `note --text "..."` |
| `resolve --flag FLAG-001` | `resolve --note NOTE-001` |
| `improve --memory` | `log-change --log` |
| `d1_experiments.py --registration`, `--worlds`, `--margin`, `--design` | `known_answer_tests.py --plan`, `--cases`, `--difference-that-matters`, `--sampling` |
| `acceptance.py develop`, `bench` | `system_trial.py working-data`, `blind-test` |

Names that stay: `rehearsal.run`, `review.verdict`, `finding.attached`; `claim_class`, which is the organization's closed vocabulary; `sf.py`, `gain.py` and `confront.py`; the option `--anchor`, which passes a posted log fingerprint to `check-log`, `signature`, `scorecard`, `close` and `system_trial.py verdict` and kept its earlier word on the command line; and the stage names `ask`, `plan`, `test`, `lock`, `open`, `review`, `signature`, `learn`, `close`.

| On the compute side (`compute/`), before | Now |
|---|---|
| `Target`, `LocalTarget` | `Place`, `LocalPlace` |
| `targets:`, `rules_for_every_target:` in the YAML file | `places:`, `rules_for_every_place:` |
| "run record", `run-record.json`, the key `target` | "run log", `run-log.json`, the key `place` |

| Renamed or changed in the third review round | Now |
|---|---|
| the scorecard check `clean-opening` | `no-failed-opening` ("clean" also describes a clean environment) |
| the key `bars` in the known-answers receipt; `BARS` in `known_answer_tests.py` | `criteria`; `CRITERIA` |
| the key `unseen` in `kinds-of-question.yaml` | `held_out_data` |
| `exhibits/practice-run-3-STUDY-0001` | `exhibits/practice-run-STUDY-0001` (since taken out; see the last section) |
| the variable `SF_SYSTEM_TRIAL_SEAL` | `BLIND_TEST_SEAL`, read only when the seal's command carries `--harness` |
| job spec: no key for what a job is | `key` (required), and `env` for the variable names a job needs |
| run log: `environment`, `inputs_manifest`, `markers` | `declared_environment`, `inputs` (declared and observed), `markers` (the place's own) and `job_markers` (the job's); new `argv_started`, `interpreter`, `program` |
| job status: phases `queued`, `running`, `done`, `cancelled`, `lost` | the same, with `failed` and a `reason` |
| the job's own marker `marker.fetch.done` deciding a void | `fetch.started`, written by the place |
| local place: `<root>/<job id>/` | `<root>/state/<job id>/` and `<root>/work/<job id>/` |
| in `places.yaml`: `identity`, `status_from`, `register`, `limits`, `note`, `reads_held-out_data`, `clean_for_an_opening`, `fits_the_factory_because` | one table for every place: `basis`, `status`, `for`, `table`, `open_questions`, with `clean_interpreter` and `blinds_the_method_builder` among the table's twelve keys, and a top-level `keys` |

New in the third review round, with no earlier name: the event `trial.verdict`; the scorecard check `lock-committed`; the plan keys `study_kind`, `writes` and `power_evidence.waived`; the options `start --request` and `--asked-by`, `lock --procedure`, `check-log --change-log`, `close --anchor`, `system_trial.py seal --answer` and `--harness`, `system_trial.py verdict --by`, and `adapter.py conformance --place`; the file `factory/templates/analysis-plan.yaml`.

## Words added with the assistants and the two loops

Added on 2026-11-26, with no earlier form. One line each.

| Word | What it means here |
|---|---|
| **exploration** | one question looked into freely: a directory with its own log, like a study, kept by the exploring tool (`explore.py`); it ends in a lead, a note, a method or a stop |
| **set aside** | named as not to be looked at, before anything is looked at; what an exploration sets aside is what a later study may hold out |
| **look** | one script run on working data through the exploring tool, logged with its data by checksum and what came out; the earlier vocabulary's "look" (opening the held-out data) is not this |
| **lead** | something that looks true and is worth testing: what, how it was found, how many looks, which choices would change it, and a proposed plan; never a finding |
| **choice** | a decision made while exploring, recorded with its alternatives and what it rests on |
| **fence** | what keeps set-aside data out of an exploration: the checks the exploring tool makes on a look's command, the scratch folder its script runs in, the reading of what it prints and leaves, and the record a later study respects. It is a fence around a look, not around a person or an assistant with a shell |
| **spoiled** | said of an exploration that set-aside data reached; it can end only as a stop |
| **hand-over** | what an exploration writes so that the study tool can start a confirming study from its lead |
| **recheck** | running a logged look again, in a copy, to see that it gives the same output |
| **role** | one assistant's job as a file in `assistants/`: what it may call, must never see, reads, writes and hands on |
| **skill** | a written procedure a role follows, with any script beside it; it carries no facts about a dataset |
| **runner** | what starts a role with its tools on some platform; the role does not depend on it |
| **rendered** | written out from the role and skill files into the files a platform reads; never edited by hand |
| **wiki** | a knowledge base as a directory of Markdown pages in the Open Knowledge Format (`openwiki/` in a repository), read as files or through the two read-only tools `openwiki_search` and `openwiki_read` |
| **working memory** | what a wiki page is until a person signs it |
| **signed** (of a page) | its own signature lines name a person; only a person adds them |
| **draft** | a page an assistant wrote for the queue; at status draft, with sources, never signed |
| **queue** | the folder of drafts waiting for the steward, beside the work and outside the wiki |
| **beside** (of a draft) | on the same subject as a page, making another point, in conflict with nothing |

Added later on 2026-11-26, after separate assistants were run and a hydrologist reviewed the result. One line each.

| Word | What it means here |
|---|---|
| **figure** | a picture a look wrote into the exploration's `figures/` folder; the receipt lists it by checksum and a lead may show it |
| **the order** (of looks and choices) | what the lead shows from the log: which looks had already run when each choice was written down |
| **written down** (of a choice) | when the log received it, which is all the log knows; a choice written down after a look is read as made after it |
| **correction** | one phrase of a recorded lead replaced without a new version; no number may change, and the lead shows the old and the new words |
| **comparisons** | the fits, cuts and groups inside one look, declared by the look's own output and added up in the lead beside the count of looks |
| **account** | what a role tells the coordinating assistant about what it did, as against the work itself; the review assistant never reads the author's |
| **own place** | `record/<role>/`, where a role's account and its task are kept, apart from every other role's |
| **remark** (of `check-log`) | where a log that checks out departs from the order the tool now holds; the log was written before the tool refused that and is kept as it is |
| **in neither** | data that is neither explored nor set aside; the start names it, and nothing protects it |
| **skimmed** | said of a knowledge page recorded as read but not read whole; the lead says so |
| **drafted by** | the name the drafting assistant acts under in the logs (`drafted_from.by`), beside `generated.by`, which is the platform and the model |
| **the run with separate assistants** | the second run of the optional demo (one river gauge, `examples/baton-rouge`): each role a separate assistant started from its role file, with no memory of the others; historical, its record is at `records-2026-11` |
| **the single-instance run** | the first run of that demo: one model instance playing every role, so its reviews are the author's own |

Words this package no longer uses for these things, because a field scientist reads them another way:

| Not this | This | Why |
|---|---|---|
| unflagged, not flagged | the flag's value: "`reach_q` equal to 1" | a quality flag can have a value on every observation; in the record the optional demo explored none is at the clean value, so "unflagged" described passes the product marks |
| sampling interval (for an interval around an estimate) | confidence interval, with the model it comes from | to a hydrologist a sampling interval is the time between samples |

The method scripts under `methods/gain/` and the kept records of both demo runs still carry the two older words, because neither may be edited; the exploring tool refuses them in a new lead.

These words beside the ones a hydrologist would use, for a first reading:

| Here | A hydrologist might say |
|---|---|
| set aside (exploring), held out (confirming) | withheld for validation; the same thing in two tools |
| look | one analysis run, with its script and output kept |
| lead | a hypothesis worth testing, with how it was arrived at |
| fence | the check that keeps withheld data out of the analysis |
| known-answer tests | synthetic recovery tests |
| gain | regression slope or scale factor: metres of rise in one record per metre of rise in the other ("slope" is kept for the water surface) |
| departure | residual from the median difference |
| spread | standard deviation |
| level difference | the offset between two records, datum included; not called a bias, because most of it is not error |
| confrontation | comparison of a product with in situ data |
| wiki, bundle | where knowledge lives: a directory of pages; a page is also called a concept |
| steward | the person who holds a knowledge bundle and signs what enters it |

## What was applied

Applied everywhere a reader or a user can meet a word: the front door (README.md), the design (DESIGN.md, which replaces the separate concept and architecture documents), the build plan (PLAN.md), the templates, both studies and their analysis plans, the procedure file, the method scripts, and the study tool, inside and out (commands, options, messages, statuses, the names of its self-test checks and its own code).

Run again, not renamed: a study log is hash-chained to its names, and each test event carries the tool's own checksum. So the earlier practice runs were discarded, and `practice-run-STUDY-0001`, `system-trial-ready-STUDY-0000` and the blind test of the system were run from the start, the last time on the tool as it stands after the third review round. The known-answer numbers and the blind test result are the same as before. The two records in `factory/change-log.jsonl` are new ones, written by the tool from that practice run: a prediction, and its observed outcome. (All of this paragraph is historical: those runs are at `records-2026-11`.)

The first two rounds in `reviews/RED-TEAM.md` and the whole of `reviews/SCIENTISTS.md` were written in the earlier words and put into the present words later the same day; each says so at its head, and their originals are not kept in this package. The third round was written in the present words. Outside this file the earlier words survive in one place, the option `--anchor`. So the tables above matter mostly for comparing with older material.

Added after the third review round, new names with no earlier form: the plan keys `passes_environment` (environment variables a step may be given, by name), `needs` (files a rehearsal requires before it runs) and `writes` (files a step writes for itself); and in the study log `env_names` (the names passed to a step) and `uv_environments` (the settings and environments `uv` would read from the study's folders, bound at the lock).

## Where the files are, since 2026-11-26

The file names in the tables above are the names; the folders changed once more. Everything that sat in `mvp/` moved to a folder named for what it is: `tools/`, `factory/`, `methods/`, `compute/`, `studies/`, and these documents moved to `docs/`. README.md has the layout in a table.

## Where the runs are, since the repository became the factory only

Later in November 2026 every run was taken out of this repository: `studies/` (the two draft studies and the practice runs), and the explorations, drafted pages and records of the demo under `examples/baton-rouge/`. With them went the table of moved files and the tool that replayed old records, which existed only to keep those records checkable. The last commit that holds them is kept as the branch `records-2026-11`. A new term follows from it. A number in these documents is *historical* when it came from one of those records and no command here makes it again; it then carries a pointer to that branch. Every other number is given with the command that reproduces it today from this repository alone.
