# Where jobs compute: the contract

The aim: run a study's commands wherever the data and capacity are, and make where a command ran part of the evidence. This folder holds the contract every runner keeps and its proof, `adapter.py`. Nothing sends a job to a runner yet; `sf.py` runs every command where it is called. The runners are in `factory/runners/`, one file each, with a table of the twelve keys `factory/factory.yaml` lists.

## A job

A known-answer test, a working-data run, a rehearsal or an opening would each be one job. A **job spec** has a name for people; an idempotency key (for an opening: the study, the test, the opening number and the lock's fingerprint); an argv in tokens the runner expands; its outputs; and optionally an inputs manifest (files that must match their checksums before it starts), a declared environment, resources, and the environment variable names it needs. A **runner** is anything that can submit, report status, collect and cancel a job.

One marker matters: `fetch.started`. The runner writes it before the job can reach data. A job that has it has used its opening up, however it ended; a job without it never started, and a person may void it.

A **run log** comes back with the outputs: what ran, where, with what inputs and variable names, when, the result, and a checksum of every output taken at the end. It is evidence, not proof: what the runner observed, naming what it only carried as declared.

## What the local runner holds today

Its conformance test covers each of these:

- The same key with the same spec is the same job, and nothing runs twice; the same key with a different spec is refused.
- Collect brings back the declared outputs and the run log and nothing else, is refused until the job can no longer change, and gives the same answer twice.
- A job killed by a signal, over its time limit or impossible to run is failed, never done.
- A job's environment is built from a short list, not inherited.

```
uv run compute/adapter.py conformance
uv run compute/adapter.py conformance --self-check
```

The first tests the local runner; the second tests the test: honest runners pass it, and every deliberately wrong runner fails it.

## What nothing holds yet

- **One opening across runners.** A runner knows only its own jobs, so the same key sent to a second runner runs there. The study log is what limits openings to one, and it does not record jobs yet.
- **Credentials.** A runner records the names a job asked for, and cannot tell a credential from any other name. On GitHub, an Actions environment with a required reviewer and an environment secret gives a data credential to one job alone.
- **What a job wrote, afterwards.** The contract has no verb to remove a job's files; they stay at the runner until a person removes them.
- **Size and number of outputs**, and any resource but a time limit.

## An opening sent through a runner

The simplest arrangement that keeps every check the tool makes: the job is the study tool itself, `sf.py open-held-out` on a fresh clone of the protected branch, returning the study log as an output. Each check runs where the data is, and the runner adds what the tool cannot: the manifest check before it starts, the marker, the run log. A clean interpreter needs a lockfile or image digest bound at the lock, with the tests run at the same runner and image.

## The runners

| Runner | Meant for | Status |
|---|---|---|
| `local` | cheap tests, working data, rehearsals; not an opening, since it runs as the same user on the same machine as whoever built the method | built |
| `batch-scheduler` | tests that cost a model run; data that lives on a cluster | written down |
| `cloud-batch` | openings, repeats across sites, scheduled re-tests, with an image pinned by digest | written down |
| `maap` | methods that run beside mission data on the MAAP platform | read in its documentation; sixteen open questions in its file, to be answered on one registered algorithm before an adapter is written |

A runner is built when `adapter.py conformance --runner REF` passes against it.
