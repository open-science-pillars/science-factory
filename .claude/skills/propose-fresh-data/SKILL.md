---
name: propose-fresh-data
description: "Propose the fresh data that will check an idea, from metadata only: the next release, a later period, another site or region, or a random set aside, with the reasons in words and the size of test it allows. Use before an exploration starts or a study is planned; use when reviewing, to judge whether the choice is fair."
---

# Propose the fresh data

Fresh data is data nobody working on the question has looked at. It is what can check an idea found by looking at other data. The tools call it held-out data. Most scientists do not arrive with any, and they should not have to: you propose it, with your reasons, and the scientist approves the choice when people lock the plan.

You propose from metadata only. Metadata says what data exists: identifiers, sites or regions, dates, releases, versions, positions, and how many observations each item holds. It never holds a measured value. You do not open a data file to choose, not even to see how it is laid out, because whatever you see there you have seen.

## 1. Read what is known, and what the scientist has already seen

Use `read-what-is-known` first. The request says what the scientist has already looked at: everything there is working data and cannot be fresh. A wiki page may say where a record changes (a new sensor, reprocessing, a dam), which decides where a later period can begin.

## 2. Get the metadata, as a file

The proposing tool reads one file in this form, JSON or YAML, and refuses any other key:

```
subject: {record: two-sensor}           # what the data is about: the keys a later plan's `pair` carries
what: "what this list describes"        # optional
items:                                  # one entry for each item: a site, a granule, a month of passes
  - {id: S01-2024, site: S01, region: north, start: 2024-01-01, end: 2024-12-31, count: 52, release: v1}
releases:                               # optional: releases that are announced and not out
  - {name: v2, date: 2027-03-01, expected_items: 20, expected_count: 900}
```

An item may carry `id` (required), `site`, `region`, `start`, `end`, `time`, `date`, `release`, `version`, `count`, `lat`, `lon`, `name` and `note`. Take it from a catalogue, a granule listing, a site list or release notes. If the only description of the data is inside the data files, stop and ask the coordinating agent for a metadata file made by a person or a script you do not read the output of.

## 3. Choose the kind, and say why

| Kind | `--kind` | Suits | Unfair when |
|---|---|---|---|
| The next release | `next-release` | a question about a product, when a release is coming and can be waited for | the release reprocesses the working data too |
| A later period | `later-period` | a question about how something behaves over time, at the same places | something else changed between the periods: a sensor, processing, a regime shift |
| Another site or region | `another-site` | a question about whether a method or a relation travels | the site differs in a way the idea does not cover |
| A random set aside | `random` | many similar items, none special, and no later data to wait for | items are close in time or space to the working data, so they are not independent |

Prefer what a later study would most plausibly want: a question about whether a method travels wants other sites, not only a later period. A random set aside is the weakest of the four, because neighbouring sites and times share their errors; say so when you choose it.

## 4. Propose it with the tool

```
uv run tools/fresh_data.py propose --metadata <the metadata file> --kind later-period --from <YYYY-MM-DD> \
  --what "<exactly what data is kept for the check>" --why "<why it suits the question>" \
  --unfair "<what would make it unfair as a check>" --by <you> --model <your model> \
  --out <the exploration>/fresh-data.yaml --studies <the folder of studies>
```

For the other kinds use `--release <name>`, `--sites <a,b>` or `--regions <r>`, or `--fraction <share>` for a random set aside. The tool counts the size of the test from the metadata (items and observations, fresh and working), adds a caution for the kind, says what it does not compute, and prints the arguments that set the data aside. For a random set aside the tool draws the members itself, from a seed it makes; you do not choose them, and you cannot. Every proposal goes on a record beside the studies, and the lock shows how many proposals that record holds for the subject, so run the tool once and keep what it gives.

The tool does not compute the power of the plan's rules at that size. Say in `--why` whether the size is enough, as far as the knowledge tells you, and leave the measuring to the known-answer tests of the plan (for the built-in gain method, `methods/gain/known_answer_tests.py --passes <N>`).

## 5. Set it aside, and say it in the scientist's words

Start the exploration with the arguments the tool printed and `--fresh-data <the proposal>`: `explore.py start` refuses a start that sets aside something other than the proposal, and refuses a random set aside without one. For a study started without an exploration, name the proposal in the plan as `data.held_out.fresh_data`. Then tell the scientist, through the coordinating agent, in their words: which data is being kept for the check, why that data, what would make it unfair, and how large a test it allows. They may change it; a change is a new proposal. They approve it when people lock the plan: the lock request shows the proposal in words and, for a random set aside, reveals the seed so anybody can draw again.

## When you review

Ask of every proposal, and write each failure as a hole:

- `uv run tools/fresh_data.py check --proposal <the proposal> --studies <the folder of studies> --log <the exploration or study log>` passes: it is on the record byte for byte, its words are written, a random draw comes from its seed, and it was written before the work it serves started.
- Nothing in the proposal was in what the scientist says they have seen, or in the working data.
- The reason holds for this question: the kind suits it (step 3), and what would make it unfair is named and is not the case, as far as the knowledge says. A later period across a known change, or a site chosen because it looked good, is a hole that would change the result.
- The size is stated, and the lead or plan does not claim more than that size can show.
- The plan's held-out block is the proposal (the same period, sites or release).
- The record holds one proposal for this subject, or the extra ones are explained.
