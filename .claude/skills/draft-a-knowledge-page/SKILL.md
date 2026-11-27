---
name: draft-a-knowledge-page
description: "Turn notes and leads from explorations and studies into draft knowledge pages in the Open Knowledge Format, with sources, at status draft, for the steward's queue. Use when notes are open. Never signs."
---

# Draft a knowledge page

What work learned about the data goes back into the shared knowledge as pages a steward reads and signs. This skill drafts them, and carries no facts about any dataset: a page's words come from the notes, receipts and sources.

**When you start.** Start on an exploration only when `explore.py status` says it has ended (stage `learn`, `hand-over` or `ended`). Before that its notes can still change and its lead can still be revised after a review, and `explore.py resolve` refuses. On a study, start when `sf.py status` says `learn`.

## Before drafting

1. **List what is open**: `uv run tools/explore.py curation-list --exploration <x>` writes `<x>/curation-list.json`; `uv run tools/sf.py curation-list --study <s>` does the same for a study.
2. **For each note, read what is known**: `uv run tools/knowledge.py about --question "<the note's subject as a question>" --wiki <wiki> --drafts <queue>`. Read the pages it lists.
3. **Decide where the note belongs.**
   - The knowledge already says it: **link**. `resolve --disposition linked --ref <the page's path below the wiki>`. No page.
   - A signed page is stale or wrong: **link** it to that page and say in `--comment` what the steward should do. List it first in your account: a link prompts nobody.
   - The knowledge says something close and the note adds to it, narrows it, corrects it or disagrees with it: **draft**, and say which.
   - Nothing covers it and it would save the next person time or a wrong answer: **draft**.
   - It is about this one piece of work and nobody else would need it: **decline**, with the reason.
   Several notes on one subject make one page.

## Drafting

Write each page into the queue in a folder named for its type, as the wiki is laid out (`<queue>/pitfalls/`, `<queue>/datasets/`, `<queue>/recipes/`), from `page-template.md` beside this skill, following the shape of two or three real pages of that type.

Front matter the queue requires (the tool refuses a draft without them):

- `type`, `spheres`, `title`, `description`, `tags`: as the wiki's pages have them. The title states the thing, not the topic.
- `generated: {by: <platform>/<model>, at: <now, UTC, from the clock>}`: the platform and model (such as `claude-code/<model>`), not the name you act under, which the format's checker refuses. A time later than the clock is refused: the stamp is a clock reading.
- `status: draft`. Never anything else.
- No `verified` key at all. A steward's signing tool adds it after the merge.
- `sources`: per source an `id`, a `resource` (the provider's page, the record's address, or the receipt's path at a commit) and a `title` saying what was read there and when. Every statement in the body footnotes a source id. The tool checks that every cited footnote is a header source and every source is cited, not that each statement has one or that the source says it, so reread each against its source first. With no commit to point at, give the receipt's path and put its checksum in the title.
- `drafted_from`: the exploration or study, the notes or the lead, and you (`{exploration: <ID>, notes: [NOTE-001], log: <the log fingerprint from the curation list>, by: <the name you act under, agent:curating-...>}`); `by` is the name you give `resolve --by`, so page and log name one actor.
- `seen_while: exploring` for a page from an exploration, whose first paragraph says where, when, on which data, how many observations.
- `relates_to`: an entry per wiki page it bears on, `{concept: <the page's path below the wiki>, relation: extends | narrows | corrects | contradicts | beside, why: <words>}` (`beside`: the same subject, another point, no conflict). A page that would only repeat a concept is not drafted: link the note.
- `stale_after`: a date, when it can go out of date.

The body: what happens (the mechanism if known, and say when it is not), what was measured (numbers with units, counts and their receipt), how it makes a wrong answer look right, what to do, how someone else could check it. One case's numbers stay that case's. End with a paragraph beginning **Who did what.**: run `uv run tools/explore.py contribution --exploration <x>` (or `uv run tools/sf.py contribution --study <s>`) and take its paragraph and its sentence on what the log cannot show, adding no credit the log does not show; a draft from an exploration or study without it is refused.

## After drafting

```
uv run tools/knowledge.py check-drafts --queue <queue> --wiki <wiki> [--checker <the format's checker>]
```

It applies the queue's rules, runs the format's checker when `--checker` names it (only a checker whose checksum is pinned in `factory/checkers.yaml`; any other is refused, not run), and writes the queue's index when all passes. A `resource` that is a path names an existing file, read from the top of the repository, the draft's folder or its place in the wiki; an address (`https:`, `doi:`) is not fetched. Fix what it refuses, then record what became of each note:

```
uv run tools/explore.py resolve --exploration <x> --by <you> --model <your model> --note NOTE-001 --disposition drafted --ref <queue path of the page>
```

## What this skill refuses

- A `verified` event, a status other than `draft`, or any wording that says a page is established.
- Writing into a wiki. Drafts go to the queue; a steward merges.
- A page of type `finding`, or a lead restated as fact.
- A statement with no source.
- Settling a disagreement with a signed page by picking a side quietly. Say `contradicts` and why.
