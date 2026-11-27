# Define your own factory

A factory is defined as code: `factory/`, rooted at `factory.yaml`, says which agents exist, the stages a study passes and what ends each, what starts an agent, how the factory is measured, and what may never feed a change to it. A change is a pull request to that folder, which a tool validates. Five steps to start, then the reference; what a tool enforces is in [WHAT-IS-ENFORCED.md](WHAT-IS-ENFORCED.md).

## Start in five steps

**The repository where your science lives holds its own copy of `tools/`, `factory/` and, with the built-in method, `methods/` and `examples/stand-alone/system-trial/`** (the shipped benchmarks name that plan; drop both if you drop it). The workflow runs the tools from there, the lock binds them there, and the verification reads the repository name there.

1. **Get the tools.** Clone this repository, run the README's three commands, and note the commit.
2. **Copy and name the definition.** Copy those four folders into your repository. In `factory/factory.yaml` set `name`, `alias`, a new `version`, the `home` block, and `repository:` under both acts to your owner/name on GitHub. That changes the acts by people, so record it with `sf.py log-change`, which names them by checksum ([FIRST-STUDY.md](FIRST-STUDY.md) shows the commands). Then pin the copy (`tools/factory_update.py pin`), so it can receive fixes (below).
3. **Validate it**, from your repository: `uv run tools/check_factory.py`. Copy `factory/harnesses/github/factory-check.workflow.yml` to `.github/workflows/`: on every pull request touching `factory/` it validates and posts the summary of the change, failing on invalid and on not validated.
4. **Protect the branch** and install the two acts, once, by the checklist in [factory/harnesses/github/README.md](../factory/harnesses/github/README.md), which also makes the labels and the Project board.
5. **Run the system trial** ([FIRST-STUDY.md](FIRST-STUDY.md)). One right verdict on a kind case is a first sign, not proof; the blind test (below) is the wider measure.

## The definition tree

![The definition tree: factory.yaml at the root, and beside it the agents with their own skills, the shared skills, harnesses, runners, scorers, benchmarks, automations, templates, the pinned checkers and the change log.](diagrams/definition-tree.svg)

The path is the name: an agent is called what its folder is called, a runner what its file is called.

| Path | What it is | Read by |
|---|---|---|
| `factory.yaml` | the root: schema version, identity, agent defaults, the stages and who does each, the two acts, the runner contract | `sf.py` (stages, acts); `check_factory.py` (all); people (blocks marked for people) |
| `agents/<name>/agent.md` | one agent: harness, model, runner and permissions in front matter; instructions in the body | a harness; the validator; the lock (declared models) |
| `agents/<name>/skills/<skill>/` | a skill that agent alone uses | that agent; the lock, by checksum |
| `skills/<skill>/SKILL.md` | a skill several agents use (`read-what-is-known`, `propose-fresh-data`) | those agents; the lock, by checksum |
| `harnesses/<name>/` | what starts an agent (`claude-code`, `by-hand`), or carries the acts as pull requests (`github`) | you or a workflow; the validator |
| `runners/<name>.yaml` | where a job computes, and how it keeps the job contract; `local` is built | people; the validator |
| `scorers/<name>/scorer.md` | one check (worked out by a tool) or judge (a rubric for a model); an overclaiming check names its `phrases.yaml` | `sf.py scorecard`; `explore.py`; `scorers.py` |
| `benchmarks/<suite>/` | a blind test suite | `benchmark.py` |
| `automations/<name>/automation.md` | what would start work without a person; declared, not wired | the validator |
| `templates/` | the request, a commented analysis plan, the kinds of question, the checklist for bringing a pipeline in | you copy them |
| `checkers.yaml` | the checkers `knowledge.py check-drafts` runs, pinned by checksum | `knowledge.py` |
| `change-log.jsonl` | every change, with its prediction and what it did | people; `sf.py log-change` writes it |

The work (`studies/`, `explorations/`, `record/`, `knowledge-queue/`) lives in your repository, made by the tools; the definition is one folder so it can be copied, reviewed and bound by one checksum.

## `factory.yaml`, key by key

**Read by the study tool**, so changing them changes what it does:

| Key | Meaning |
|---|---|
| `schemaVersion` | the form of the files; today `science-factory/v1alpha1` |
| `version` | this definition's content; bump it with every change and record it with `sf.py log-change` |
| `procedure.stages[].id`, `done_by`, `done_when`, `does` | each stage's name; who does it (agents, or `people`); the checks that end it; one sentence shown at it |
| `procedure.acts_by_people.lock.opening_without_verification` | `refused` (default) or `allowed-with-a-reason`: may a person open fresh data on a lock GitHub could not be asked about; changing it needs a change-log record under a new version |

The checks a stage may name: `started`, `plan-complete`, `tests-pass`, `rehearsals-pass`, `locked`, `openings-complete`, `finding-attached`, `reviewed`, `steward-decided`, `notes-resolved`, `closed`.

**Read by the validator:**

| Key | Meaning |
|---|---|
| `agentDefaults` | the harness, model and runner an agent gets when its file names none |
| `procedure.coordinator` | the agent that follows `sf.py status` and starts the others |
| `procedure.agents` | what each agent does, in a sentence its file quotes word for word |
| `procedure.acts_by_people` | the lock and the signature: `who`, the `command` no agent may call, the `route` (`pull-request` or `practice`), and for a pull request the `harness`, `protected_branch`, `approvals`, `repository` (owner/name), `merge_methods` (`merge`, `squash`; never a rebase), `opening_needs` and `shows` |
| `procedure.so_what` | a person's answer to a reviewed lead: `who`, the `command` no agent may call, the `route` (`comment` through a `harness` for a `repository`, or `practice`) and the four `answers` |
| `where_it_runs`, `runner_contract.keys` | runner files, and the twelve keys every runner fills in |

The acts must be exactly the stages `done_by: people`, both declared the same way; a factory whose acts are `practice` is valid, and every study under it is practice.

**Read by people**, stating the design and what holds it: `product`, `home`, `procedure.study_kinds`, `procedure.request` (with `fit_note`), `procedure.people`, `procedure.separations`, `procedure.rules_for_people`, `measure`. Unknown and repeated keys are refused everywhere.

## Agents, skills and harnesses

**An agent file** is front matter, then instructions; `description` is one sentence; `harness`, `model` and `runner` fall back to `agentDefaults`, and the model is a concrete name the harness lists, never `auto`. The permissions: `may_call` (`tools/<tool>.py <command>`, `skill:<name>`, agents it may start as `role:<name>`), `must_never_see` (in words, and as `path:<pattern>` where a harness can refuse it), `reads`, `writes` (patterns; every agent that writes has `record/<name>/*.md`) and `hands_on`.

**What holds an agent to its file.** The validator holds the files to each other (commands exist, no agent calls an act, the review agent does no work, shared paragraphs match, every command shown parses); a harness holds the agent while it works; without one the file is instruction.

**Skills** are procedures, with any script beside them, and no facts about a dataset. Methods for a kind of data belong where that science lives; the factory ships one built-in method to exercise its stages.

**Promoted methods.** `explore.py promote` turns a look's script into `methods/<name>/` with the exploration's runs as known-answer cases, a README (what it computes, on what inputs, known limits), a generated `known_answer_tests.py` and `method.json` with every checksum. The validator refuses it until a change-log record names `methods/<name>` with a prediction; a plan binding it runs `known_answer_tests.py` as a rehearsal before its tests and lock.

**Harnesses.** In `claude-code/`, `render.py` writes the files Claude Code reads and fails on drift (`--check`), `allow.py` is the per-call check, and `run_role.py` starts one agent in a fresh context, keeping its task and answer in `record/<role>/`. `by-hand/as_role.py` asks the same check for one command. `github/` carries the two acts. None has run under its platform. **The model is declared, not proven:** an agent's event without `--model` is refused, and the lock records the declared models and those the log recorded.

## Runners

A runner is where a job computes (this machine, a cluster, a cloud batch service, a platform beside the data): a file in `runners/` with a status, a `contract` table of the twelve keys, and open questions. Only `local` is built; the study tool runs every command where it is called. The contract and its proof: [compute/README.md](../compute/README.md), `compute/adapter.py`.

## Checks, judges, and the outcome firewall

A scorer is one file in `scorers/`. A **check** is worked out by a tool from the log (`sf.py scorecard`), `pending` until it can be. Nine ship for studies (`chain-of-custody`, `plan-adherence`, `opening-discipline`, `no-failed-opening`, `lock-committed`, `independent-review`, `acts-by-people`, `notes-curated`, `overclaiming-in-findings`) and one for explorations (`overclaiming-in-leads`); the overclaiming checks read `scorers/overclaiming-in-leads/phrases.yaml` (a pattern, why, optionally `when: not-supported` or `unless`) and only warn. A **judge** is a rubric for a model, with `labels`, `passingScore`, `samplingRate`, `model` and the `agents` it scores; three ship (`exploration-owns-its-count`, `review-finds-holes`, `plan-is-clear`). In a first trial agents judged six packets by hand, twice each, matched the key on five and found a fault in the sixth case; the Claude Code path (`scorers.py judge`) has not run. `JUDGE.md` asks for `verdict.yaml`; `scorers.py record` writes the verdict beside the packet and moves the answer out.

Every scorer declares what it `reads`, from a list split at the first opening:

| Written before any opening | Written from the first opening on |
|---|---|
| `request`, `plan`, `known-answer-tests`, `code`, `pre-lock-log`, `exploration-log`, `lead`, `review-before-opening`, `transcript-before-opening` | `opening-outcome`, `finding`, `post-opening-log`, `review-after-opening`, `transcript-after-opening` |

**The firewall.** What an opening showed must never reach what changes how the next opening runs, or the factory would drift toward agreeing with its claims. The validator refuses a judge reading the right-hand column, `selfImprovement: true` on any scorer that does, and a benchmark case that is real fresh data. Outcomes may still be counted, shown to people and fed to the knowledge loop.

![Measure and improve: what is written before any opening feeds the judges and may feed a proposal; what an opening produced is counted and shown to people, behind a wall.](diagrams/measure-and-improve.svg)

## Benchmarks: the blind test, as suites

A suite (`benchmarks/<suite>/suite.yaml`) has sealed planted-truth cases (never real fresh data), configurations (definitions by path or git ref), repetitions, and a comparison stated first. `uv run tools/benchmark.py run --suite factory/benchmarks/built-in-gain` runs six cases twice under two configurations (the definition against itself) and should say `NO DIFFERENCE BEYOND NOISE`; only paired runs that differ count, by an exact sign test. The **design set** keeps its cases as files. The **acceptance set** makes them at run time from `SF_ACCEPTANCE_SEED` and refuses without it; on GitHub the seed is an environment secret with a required reviewer. `methods/gain/system_trial.py blind-test` is the same driver on one definition.

## Automations

An automation says what would start work without a person: `triggers`, the `stage` (one agents do before the lock), instructions. Two are declared (a new data release, a signed page past its date), neither wired; on GitHub each would be an Actions trigger opening a request from the issue form.

## Validate a definition

```
uv run tools/check_factory.py
uv run tools/check_factory.py --summary git:HEAD^:factory factory
uv run tools/check_factory.py --checksum
uv run tools/check_factory.py --selftest
```

`valid` (exit 0), `invalid` (exit 1, each broken rule by name: form, references, roles, acts, skills, firewall, acceptance, automations, methods) or `not validated` (exit 2, never a pass). `--summary OLD NEW` says in plain words what a change does, acts and permissions first.

## What the lock binds

The plan, the code, the request, the test receipts, the fresh-data proposal, and the definition: the checksum of the whole tree (but the change log), its version, the checksum of `tools/`, each agent's declared model and harness, and each skill by checksum. A definition changed between lock and opening blocks the opening; the remedy is a new lock.

## What a file can change, and how a change is made

Editing `factory.yaml` can add, remove or reorder stages built from the checks above, change who does a stage, and allow or refuse an opening without verification (under a new version with a change-log record; the lock request then says so in capitals); scorers choose the checks and add judges; an agent's file changes what it may do, which the summary makes hard to miss. A new kind of check, study, decision rule or material needs code, with a self-test that fails without it. A change is a pull request: `sf.py log-change` records the problem, the change and its prediction before it is tried, and what it did after. Nothing is adopted automatically; the intended rule, which no tool enforces yet, is a pass on the acceptance set. Tag and release each definition version beside the change log.

## Receiving fixes: the pin and the update

`factory-pin.yaml`, at the top of your repository, names the source, the version and commit your copy came from, and the checksums of its definition and tools. `uv run tools/factory_update.py status --repo . --source ../science-factory` says whether the source has moved and what an update would do; `update` writes it on a branch: your own edits kept (the repository's name, your settings), a field or lines changed on both sides refused by name, `tools/` taken from upstream, the version `<upstream>+local.<n>`, the pin moved, a change-log record added, and the pull request's description written (`--body-out`): the summary of the change and upstream's change-log records between the two versions. It refuses while a study is locked and not closed, because a locked study is bound to its definition, unless you carry it on its old version (`--carry-on-old-version studies/NAME`; it is then opened from a checkout of the commit before the update). `update.workflow.yml` does this weekly and opens the pull request; it has never run on GitHub. `methods/` and `examples/` are not touched.

## Compared with Warp Factories

The layout follows [Warp Factories](https://docs.warp.dev/factories/) where the meaning is the same; it is our own schema, differing where science differs from software. [WARP-COMPARISON.md](WARP-COMPARISON.md) has the reasoning.
