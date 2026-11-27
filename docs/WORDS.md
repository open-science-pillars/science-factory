# The words

Today's words, one line each, in groups. What a word used to be is in [history/RENAMES.md](history/RENAMES.md).

## People and agents

- **scientist**: the person who asks, approves the plan and the fresh data at the lock, and receives the result first.
- **steward**: the person who approves the lock with the scientist, signs or declines the finding, and signs knowledge pages.
- **maintainer**: a person who reviews and merges changes to the methods and the definition.
- **agent**: an AI agent. Four are defined, in `factory/agents/`: coordinating, analysis, review, curating.
- **role**: the job an agent's file defines; "the analysis role" is what the analysis agent may and may not do.
- **harness**: what starts an agent and holds it to its file (Claude Code, by hand), or carries the two acts (GitHub).
- **platform**: what runs an agent, such as Claude Code. GitHub is called GitHub.
- **code owners**: the GitHub accounts a repository's `CODEOWNERS` file says must approve a change to a path.

## The two ways

- **exploring**: looking at data to find out what is there; it ends in a lead, a note, a method or a stop.
- **confirming**: testing one claim, stated in advance, once, on fresh data.
- **lead**: what an exploration found that looks true and is worth testing; never a finding.
- **so what**: a person's answer to a reviewed lead: `worth-confirming`, `try-instead`, `not-interesting` or `needs-an-expert`; no agent records it.
- **lead noted**: how an exploration ends when a person says its lead is not interesting; not a failure.
- **finding**: the signed result of a confirming study, and nothing else.
- **the wall**: data used to explore is never used to confirm what the exploring found.

## Data

- **fresh data**: data nobody working on the question has looked at; what checks the idea.
- **held-out data**: the tools' name for fresh data in a study; nobody opens it before the lock.
- **set aside**: the exploring tool's word for the same, while exploring.
- **working data**: anything you or your group have already looked at.
- **metadata**: what may be read before the lock because it cannot move the answer: dates, places, versions, counts, flags.
- **proposal of the fresh data**: what `tools/fresh_data.py propose` writes: the kind, exactly what, why, what would make it unfair, the test size.
- **random set aside**: fresh data the tool draws from the items the metadata lists, at the opening, from the lock's merge commit; nobody chooses the members.
- **withheld values**: what nobody reads before the opening.
- **subject** (`pair` in a plan): what the data is about, as key and value; the records match on it.
- **window**: the period a study holds out, from one date to another.

## A study

- **study**: one question taken from request to signed finding or recorded no; one folder.
- **request**: what the scientist asks, in their own words (`factory/templates/request.md`, or the issue form).
- **fit note**: the coordinating agent's advice at intake: how well the question suits agents, a verdict (`good-fit`, `fit-with-a-person-steering`, `poor-fit`), and what it needs from a person; it blocks nothing.
- **tracking issue**: the GitHub issue a study's request became; fingerprints are posted there.
- **analysis plan**: `analysis-plan.yaml`: what is estimated, on which data, and what counts for and against.
- **the difference that matters**: the smallest difference that would change what you do.
- **decision rule**: what supports the idea, what refutes it; anything else is inconclusive.
- **criterion**: a pass or fail threshold on a rate the known-answer tests measure.
- **known-answer test**: synthetic data with the truth put in, including cases where the idea is false.
- **hard case**: a known-answer case where the idea is true or false and something else is also going on.
- **rehearsal**: a run of what the opening depends on, on working data, before the lock.
- **the lock**: people approve the plan, the code and the fresh data together, by merging a pull request.
- **lock request**: what `sf.py request-lock` writes: an evidence summary in plain words and a manifest of checksums.
- **opening**: the one run of the locked analysis on the fresh data.
- **access gate**: the step of the study tool that fetches the fresh data at the opening, and nothing else does.
- **signature**: the steward's decision on the finding, by merging a second pull request.
- **standing**: how an act stands: `practice`, `merge found, people not verified`, or `verified`.
- **verification**: GitHub asked, wherever a standing is used or by `sf.py verify-acts`, whether an act is a merge people approved; a verification kept in the log is a note.
- **awaiting verification**: a study whose signature is recorded and whose acts are not both verified; not signed.
- **practice**: an act typed at a command line, for trying the tools; a practice study never closes as a signed finding.
- **system trial**: a study of the factory itself, on a blind test case sealed at the opening.
- **study log**: `study-log.jsonl`, only ever added to, each event chained to the one before by hash.
- **log fingerprint**: an event's sequence number and hash, posted outside the workspace.
- **run receipt**: the record a run writes, with its code and inputs by checksum and every number it produced.
- **record of what has been opened**: `studies/openings.jsonl`, beside the studies.
- **openings allowed**: how many times a test on fresh data may be opened: one.
- **inconclusive**: a result, and final for that data.
- **note**: something missing or wrong, raised during work, with evidence; never deleted.
- **contribution statement**: who did each kind of work (person, or agent and declared model), drawn from the logs; the finding and every draft carry it.

## An exploration

- **exploration**: one folder with its own log, made by `tools/explore.py`.
- **look**: one script run through the exploring tool, logged with its inputs and output.
- **choice**: a decision recorded with its alternatives and what it rests on.
- **fence**: what keeps set-aside data out of a look (`tools/fence.py`): the scratch folder, the reading of what goes in and out, the kernel fence.
- **kernel fence**: Landlock on Linux, which keeps a script from opening anything outside its scratch folder.
- **keeper**: the small process that puts the kernel fence up and ends what a script leaves running.
- **hand-over**: what an ended exploration gives a confirming study: the request, a plan stub, the proposal of the fresh data, the figures.
- **promoted method**: a look script made a method by `explore.py promote`, its runs becoming known-answer cases; a change to the factory.

## The definition

- **definition**: the `factory/` tree, rooted at `factory.yaml`.
- **procedure**: the list of stages in `factory.yaml`.
- **stage**: ask, plan, test, the lock, check once on fresh data, review, the signature, learn, close.
- **skill**: a procedure an agent follows, with any script beside it, and no facts about a dataset.
- **runner**: where a job computes (`factory/runners/`); only `local` is built.
- **driver**: the script that drives the blind test (`methods/gain/system_trial.py blind-test`, `tools/benchmark.py`).
- **validator**: `tools/check_factory.py`: valid, invalid, or not validated, which is never a pass.
- **change log**: `factory/change-log.jsonl`, every change to the definition with its prediction and what it did.
- **factory pin**: `factory-pin.yaml` in a study repository: where its factory came from, by version, commit and checksum; `tools/factory_update.py` moves it.
- **waiting on a person**: what `tools/waiting.py` lists: everything in a workspace that wants a person, or is stuck, with its next step.

## Measuring

- **check**: one item of a study's scorecard, worked out by the tool from the log (the files are in `scorers/`).
- **judge**: a rubric for a model, reading only what was written before any opening.
- **scorer**: a file in `scorers/`, of either kind.
- **scorecard**: the nine checks for one study (`sf.py scorecard`).
- **report**: `tools/report.py`, what a workspace's studies and explorations did, counted by stage, outcome and time; it scores no factory by findings supported.
- **overclaiming check**: flags words that claim more than the work shows ("good agreement", "clearly", "proves", a number finer than its uncertainty) in leads, reviews and findings; it warns, never blocks.
- **firewall**: what an opening showed never reaches a judge or a proposal to change the factory.
- **benchmark**: a suite of sealed cases run under two versions of the definition and compared.
- **design set** and **acceptance set**: cases anyone may read, and cases made from a seed nobody proposing a change may read.
- **self-test**: a tool's test of itself, attacks included.
- **hole**: an item a review or an attack raised.

## Knowledge

- **wiki**: a knowledge base of Markdown pages in the Open Knowledge Format v0.2, read as files; here `openwiki/`.
- **page**: one file of the wiki; signed only when its own `verified` line names a person.
- **pitfall**: a trap in the data, written down as a page.
- **queue of drafts**: where the curating agent drafts pages, for a person to accept into the wiki.
- **checker**: a program that checks the knowledge format, run only when pinned by checksum in `factory/checkers.yaml`.
