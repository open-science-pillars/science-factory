---
name: explore-a-record
description: "Explore a record freely without spending the data a later test will need: set data aside first, then look, with every look logged and every choice recorded. Use when a request asks what is there, how well something works, or where it fails."
---

# Explore a record

Exploring is looking to find out what is there. It is most of the work and nothing in it is locked. The one rule is to say that it was exploring, and the tool (`mvp/loops/explore.py`) makes that easy: it keeps the log, counts what was tried and holds the fence. This skill is the procedure. It carries no facts about any dataset.

Run every command from the repository root. `<x>` is the exploration's directory, by convention `<work>/explorations/<ID>`; the confirming studies and the record of what has been opened sit beside it in `<work>/studies/`.

## 1. Set data aside first

Before anything is looked at, decide what will not be looked at. Read the request for what has already been seen and what could be held out, and choose one of the ways TWO-WAYS-OF-WORKING.md lists: a later period, a period of contrasting conditions, sites never opened, a new release, a different instrument or record, forecasts scored later. Prefer the one that a later confirming study would most plausibly want.

```
uv run mvp/loops/explore.py start --exploration <x> --id <ID> --by <you> \
  --question "<one sentence ending in a question mark>" --request <the request file> \
  --subject <key=value,key=value: the thing the data is about, as a plan's `pair` will say it> \
  --how "a later period" --set-aside-window <START:END, or START: to keep it open> \
  --why "<why this is the data to set aside>" \
  --working "<what will be explored, in words>" --working-window <START:END>
```

Where the boundary should fall is a fact about the data (a change of processing, a release date): read it from the knowledge, do not guess it. If you cannot read the knowledge before starting, start with the widest honest set-aside and say why.

From here on you do not fetch, read, plot or ask about what was set aside, by any route. The tool refuses a look that names it. It cannot see a script that reads it from somewhere the command does not name; that is on you.

## 2. Read what is known

Use the `read-what-is-known` skill with `explore.py known` and `explore.py read`. The first look is refused until `known` has run.

## 3. Look

A look is one script, run through the tool, with a reason:

```
uv run mvp/loops/explore.py look --exploration <x> --by <you> --why "<what this look is trying to find out>" \
  -- uv run looks/<script>.py <arguments>
```

- Write each script in `<x>/looks/`. Paths in the command are read from the exploration directory.
- Start with the shape of the record before any statistic: `uv run <path to>/skills/explore-a-record/scripts/describe_record.py <data file>` prints keys, counts, ranges and time span.
- Use the method the knowledge rules in (a script the capability ships) before writing your own, and say when you depart from it.
- One question per look. Print what you found as numbers with units and counts; the output is kept by checksum and is what a reviewer will read.
- A failed look is still a look and is still counted. Do not delete scripts to tidy the record.
- Look for where it does not hold as hard as for where it does: split by the conditions the question cares about, look at the worst cases by name, and check whether a few points carry the result.

## 4. Record choices as you make them

Every time you pick one way over another after looking (which passes to drop, which tolerance, which model, which period to show), record it then, not at the end:

```
uv run mvp/loops/explore.py choice --exploration <x> --by <you> --choice "<what you chose>" \
  --alternative "<another way>" --alternative "<another>" --rests-on "<what it rests on>" --look LOOK-00N
```

When you can, run the alternative as a look too, so the lead can say how much the choice moves the answer.

## 5. Raise notes

Anything missing, wrong or stale in the data or the knowledge, and any dead end:

```
uv run mvp/loops/explore.py note --exploration <x> --by <you> --kind <missing|wrong|stale|contradiction|method|dead-end> \
  --about "<the product, field or page>" --text "<what, with numbers>" --evidence receipts/LOOK-00N.json
```

Check first whether the knowledge already says it; a pitfall the knowledge names and you met is worth one line in the lead, not a note.

## 6. End

An exploration ends in a lead (use the `write-up-a-lead` skill), a note, a method (`end --outcome method --file <script>`), or a stop. All four are honest outcomes. `uv run mvp/loops/explore.py status --exploration <x>` says where it stands and who is next.

## What this skill refuses

- Looking before data is set aside, or at what was set aside.
- A number in a write-up that is not in a look's output.
- A choice made after looking and left unrecorded.
- Calling what was found a finding, a result or a validation. It is a lead.
