# Warp Factories and a science factory, compared

[Warp Factories](https://docs.warp.dev/factories/) is a software factory: configured AI agents take a request from an issue or a chat thread to a pull request a person merges, with the factory [defined as a tree of files](https://docs.warp.dev/factories/factory-as-code/). This page compares it with this repository, from Warp's public documentation and examples as of November 2026. Nothing of Warp's was run, and nothing here renders this repository's files for Warp. The layout of `factory/` follows Warp's where the meaning is the same; this page is the reasoning.

## Concept by concept

What became of each Warp concept: **kept**, **translated** (the same idea in another form), **changed** (because science differs), **dropped**, or **missing** (not built, worth building).

| In Warp | Here | Verdict |
|---|---|---|
| A root file with a schema version; schemas that refuse unknown keys | `factory/factory.yaml` with `schemaVersion`; `check_factory.py` refuses unknown keys | translated, built |
| An agent file with execution settings (model, runtime, compute) | those, plus permissions Warp has no place for: what it may call, must never see, may write | kept and extended |
| One coordinating agent, which also decides when a stage is done | one coordinator, which chooses who works next and never whether a stage is finished: a tool works that out from the log | changed |
| Stages and transitions as data, judged by a model | stages as data, each ended by named checks a tool evaluates; nothing returns across the opening | changed |
| Gates: a question a person answers in the conversation | two acts by people, each a pull request on a protected branch (the workflow has not run on GitHub) | changed |
| A run keeps the workflow it started with | the lock binds the whole definition, the declared models and the skills by checksum | translated, built |
| Automations with triggers, filters and schedules | two declared, not wired; they may start only stages agents do before the lock | missing, in part |
| A harness and a model per agent | the same, declared; every agent event records the model | translated, built |
| Runner files for compute | runner files with a job contract; only a local one is built | translated |
| Per-agent secrets and network policy | nothing yet | missing, and important |
| A dashboard of throughput, autonomy, cycle time and cost | a scorecard per study; no page across studies | missing; see below |
| Scorers: sampled model judges over finished runs | deterministic checks, and judges over pre-opening material only | changed |
| Benchmarks: fixed tasks under several configurations | sealed planted-truth cases under two definitions, in a design and an acceptance set | translated, built |
| Benchmark tasks made from past runs | never: a closed study's data has been opened | changed |
| Self-improvement: failures past a threshold become a pull request | the flag and the firewall only; no loop | missing, on purpose for now |
| A validator with three results; a summary of what a change does | the same | translated, built |

## What Warp has that this project had not thought about

**A barrier that is a field, not a sentence.** The only real answer to "an analysis agent could read the held-out data elsewhere" is an environment with no route to it, not built here. Warp has both halves as ordinary settings: which secrets an agent gets and which hosts it may reach, a denial winning. Declaring the same would cost little (the data host denied to the agent that builds methods, the data credential given to the opening's job alone, a validator rule that fails where they meet); enforcing it needs a platform or container runtime. The most valuable thing the reading found, and not built.

**Kept context, and its opposite.** A continuing conversation is good for exploring. For confirming, context is a channel: the review agent starts fresh, and whoever writes the finding must not carry hopes across the opening.

**Not validated is never a pass.** Warp's validator has a third result, treated as a failure. Taken outright.

**A different model for review**, "to reduce shared blind spots": cheap, and checkable now that models are recorded.

**The page that matters is what is waiting on a person**, not the dashboard: a steward's queue of locks, signatures and drafts is otherwise invisible. Built as `tools/waiting.py` (Warp's Home, "Waiting on you"), with a workflow that keeps a label in step on each tracking issue.

## Where a science factory must differ in kind

A software factory's sensor is its tests, and reading them more often makes the product better. Seven rules here have no such counterpart.

1. **Held-out data is opened once.** Reading it uses it up; a second reading after a change is fitting.
2. **Revision never crosses the opening.** A review may send back the write-up, never the analysis.
3. **Tests are on known answers**: the whole decision must say "no" when a planted truth is "no".
4. **Inconclusive is a final answer**, and a refuted claim is a product.
5. **There is a knowledge loop** that outlives the factory, and only a person signs.
6. **The two acts are not a merge.** A lock commits before the evidence exists; a signature asserts something about the world. Reverting a commit undoes neither, and neither becomes unnecessary as the factory matures.
7. **Exploring and confirming are two loops with a wall**; only a reviewed lead and the set-aside data cross it.

Two consequences for anything borrowed. A software factory assumes a work's outcome signals how well the factory worked; a confirming study's outcome does not (supporting nine claims in ten is not better than four, and may be worse). And it assumes looking at past work is harmless; here past work holds opened data.

**Self-improvement copied as it is would do the most damage.** A judge labelling "reached a clear verdict" would count inconclusive and refuted studies as failures; a proposal to make them rarer would follow; each step, a reviewed pull request with evidence, moves toward a procedure that agrees with its claims. It is the oldest error in science one level up, the openings of many studies serving as the training set. A judge that merely reads results does it more quietly, finding analyses that reached the expected answer sounder.

The defence is structural, and built here. Every scorer declares what it reads; a judge reads nothing written after an opening; only such a scorer may feed a proposal; a proposal is tested only on blind planted-truth cases, where "no" is as creditable as "yes", and the cases that accept a change are not those that shaped it; the prediction is written first.

## What is safe to take as it is

Almost everything about the definition as files: the layout, the schema version, refusing unknown keys, the three results, the summary of a change, a model per agent, runner files, skills in two scopes, schedules. The danger is one place: any path by which what an opening showed can reach what changes how the next opening runs.
