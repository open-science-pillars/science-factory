# Warp Factories and a science factory, compared

**Open Science Pillars (a personal open-source project) · 2026-11-26 · a shortened version of a longer study, for readers who know one of the two and want to place the other.**

[Warp Factories](https://docs.warp.dev/factories/) is a software factory: a product in which configured AI agents take a request from an issue or a chat thread to a pull request that a person merges, with the factory itself [defined as a tree of files](https://docs.warp.dev/factories/factory-as-code/). This page compares it with the science factory in this repository, from Warp's public documentation and examples as they stood in November 2026. Nothing of Warp's was run, and nothing here renders this repository's files for Warp. 

The layout of `factory/` follows Warp's wherever the meaning is the same, and `docs/CREATE-A-FACTORY.md` lists where it does not. This page is the reasoning behind both.

## Concept by concept

Each row says what became of a Warp concept here: **kept** as it is, **translated** (the same idea in another form), **changed** (the idea had to change because science differs), **dropped**, or **missing** (not built here, and worth building).

| In Warp | Here | Verdict |
|---|---|---|
| A root file with a schema version; schemas that refuse unknown keys | `factory/factory.yaml` with `schemaVersion`; `check_factory.py` refuses unknown keys | translated, built |
| An agent file with execution settings (model, runtime, compute) | an agent file with those, and with permissions Warp has no place for: what it may call, must never see, may write | kept and extended |
| Exactly one coordinating agent, which also decides when a stage is done | one coordinator, which chooses who works next and never whether a stage is finished: a tool works that out from the log | changed |
| Stages and transitions as data, judged by a model | stages as data, each ended by named checks a tool evaluates; nothing returns across the opening | changed |
| Gates: a question a person answers in the conversation | two acts by people, the lock and the signature, recorded with evidence and meant to be pull requests on a protected branch | changed |
| A run keeps the workflow it started with | the lock binds the whole definition, the declared models and the skills by checksum | translated, built |
| Automations with triggers, filters and schedules | two declared, not wired; they may start only stages agents do before the lock | missing, in part |
| A harness per agent; a model per agent | the same, declared; every event an agent writes records the model | translated, built |
| Runner files for compute | runner files, with a job contract each must pass; only a local one is built | translated |
| Per-agent secrets and network policy | nothing yet | missing, and important |
| A dashboard of throughput, autonomy, cycle time and cost | a scorecard for each study; no page across studies | missing; see below |
| Scorers: sampled model judges over finished runs | two kinds: deterministic checks, and judges over pre-opening material only | changed |
| Benchmarks: fixed tasks under several configurations | sealed cases with planted truths under two versions of the definition, in a design set and an acceptance set | translated, built |
| Benchmark tasks made from past runs | never: a closed study's data has been opened | changed |
| Self-improvement: failures past a threshold become a pull request | the flag and the firewall only; no loop | missing, on purpose for now |
| A validator with three results; a summary of what a change does | the same | translated, built |

## What Warp has that this project had not thought about

**A barrier that is a field, not a sentence.** This project's design says that the only real answer to "an analysis assistant could read the held-out data elsewhere" is an environment with no route to it, and that this is not built. Warp's definition has both halves of such a barrier as ordinary settings: which secrets an agent is given, and which hosts it may reach, with a denial winning. Declaring the same here would cost little: the data host denied to the agent that builds methods, the data credential given to the opening's job alone, and a validator rule that fails any definition where the two meet. Enforcing it needs a platform or a container runtime. It is the most valuable thing the reading found, and it is not built.

**Kept context, and its opposite.** Warp treats a continuing conversation as a pure good. For exploring it is. For confirming, context is a channel: the review assistant must start fresh, and whoever writes the finding must not carry hopes from before the lock across the opening.

**Not validated is never a pass.** Warp's validator has a third result for "could not tell", and its examples treat it as a failure. This project took that outright.

**A different model for review.** Warp's examples run the reviewer on another model family "to reduce shared blind spots". That is cheap, and checkable once models are recorded, which they now are.

**The page that matters is not the dashboard.** Warp's dashboard counts pull requests, autonomy and cost. The useful page for a science factory is the other one Warp has: what is waiting on a person. A steward's queue of locks, signatures and drafts is otherwise invisible.

## Where a science factory must differ in kind

A software factory's sensor is its tests, and reading them more often makes the product better. Seven rules here have no counterpart of that kind.

1. **Held-out data is opened once.** It is used up by being read. A second reading after a change is not a re-test; it is fitting.
2. **Revision never crosses the opening.** A review may send back the write-up, never the analysis.
3. **Tests are on known answers.** They check that the whole decision returns "no" when the truth is "no", against a planted truth and not against a specification.
4. **Inconclusive is a final answer.** A refuted claim is a product, and "cannot tell" is a result.
5. **There is a knowledge loop.** The factory also feeds a body of knowledge that outlives it, and only a person signs.
6. **The two acts by people are not a merge.** A lock is a commitment made before the evidence exists; a signature is an assertion about the world. Neither is undone by reverting a commit, and neither becomes unnecessary as the factory matures.
7. **Exploring and confirming are two loops with a wall.** Only a reviewed lead and the data that was set aside cross it.

Two consequences follow for anything borrowed. Everything a software factory optimizes assumes that the outcome of a piece of work is a fair signal of how well the factory worked: a merged pull request is good. In science the outcome of a confirming study carries no such signal: a factory that supports nine claims in ten is not better than one that supports four, and may be worse. And everything a software factory reuses assumes that looking at past work is harmless. Here past work contains opened data.

**The mechanism that would do the most damage if copied as it is, is self-improvement.** Suppose a judge labelled "the study reached a clear verdict", with its failures feeding proposals. Inconclusive and refuted studies would count as failures; after enough of them a proposal would arrive to make such failures rarer; and every such proposal is a step toward a procedure that agrees with the claims it is given. No single one would look wrong. Each would be a reviewed pull request with its evidence linked. It is the oldest error in science, one level up, with the openings of many studies serving as the training set. A judge that merely reads results does the same thing more quietly: asked whether an analysis was sound, it will tend to find the ones that reached the expected answer sounder.

The defence is structural, and it is what this repository built. Every scorer declares what it reads. A judge reads nothing written after an opening. Only a scorer that reads nothing written after an opening may feed a proposal. The only outcomes that may test a proposal are blind cases with a planted truth, where a "no" is as creditable as a "yes", and the cases that accept a change are not the cases that shaped it. The prediction is written before the change is tried.

## What is safe to take as it is

Almost everything about the definition as files: the layout, the schema version, the refusal of unknown keys, the three results, the summary of a change, a model for each agent, runner files, skills in two scopes, schedules. The danger is confined to one place: any path by which what an opening showed can reach something that changes how the next opening is run.
