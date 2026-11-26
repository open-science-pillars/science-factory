---
name: draft-a-knowledge-page
description: "Turn notes and leads from explorations and studies into draft knowledge pages in the organization's Open Knowledge Format, with sources, at status draft, for the steward's queue. Use when notes are open. Never signs."
---

# Draft a knowledge page

What a piece of work learned about the data goes back into the shared knowledge as pages a steward reads and signs. This skill is the procedure for drafting them. It carries no facts about any dataset: what a page says comes from the notes, the receipts and the sources.

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

Write each page into the queue, in a folder named for its type the way the bundle is laid out (`<queue>/gotchas/`, `<queue>/datasets/`, `<queue>/recipes/`). Start from `page-template.md` beside this skill. Read two or three real pages of the same type in the bundle first and follow their shape.

Front matter the queue requires (the tool refuses a draft without them):

- `type`, `spheres`, `title`, `description`, `tags`: as the bundle's pages have them. The title states the thing, not the topic.
- `generated: {by: <platform>/<model>, at: <now, UTC, from the clock>}`. The knowledge format takes the platform and the model here (for example `claude-code/<model>`), not the name you act under, and the organization's checker refuses anything else. A time later than the clock is refused: the stamp is read as a clock reading.
- `status: draft`. Never anything else.
- No `verified` key at all. A steward's signing tool adds it after the merge.
- `sources`: one entry per source, each with an `id`, a `resource` (an address: the provider's page, the record's address, or the receipt's path in the repository at a commit) and a `title` saying what was read there and when. Every statement in the body carries a footnote to a source id. The tool checks that every footnote the body cites is a source in the header and that every source is cited; it cannot check that a statement has a footnote or that the source says what the statement says, so reread each one against its source before you run the check. When the repository has no commit to point at, give the receipt's path and put its checksum in the title.
- `drafted_from`: the exploration or study, the notes or the lead, and you (`{exploration: <ID>, notes: [NOTE-001], log: <the log fingerprint from the curation list>, by: <the name you act under, agent:curating-...>}`). `by` is the same name you give `resolve --by`, so the page and the log name one actor.
- `seen_while: exploring` when it comes from an exploration, and the body says so in its first paragraph: where, when, on which data, how many observations.
- `relates_to`: one entry for every concept in the bundle the page bears on: `{concept: <path below the bundle>, relation: extends | narrows | corrects | contradicts | beside, why: <words>}`. `beside` is for a page on the same subject that makes another point and conflicts with nothing. If the page would only repeat a concept, do not draft it: link the note.
- `stale_after`: a date, when what it says can go out of date.

The body: what happens (the mechanism, if known, and say when it is not), what was measured (numbers with units, counts and the receipt they come from), how it makes a wrong answer look right, what to do, and how someone else could check it. Keep one case's numbers as that case's numbers.

## After drafting

```
uv run tools/knowledge.py check-drafts --queue <queue> --wiki <wiki> [--checker <the organization's checker>]
```

It applies the rules of the queue, runs the organization's own checker for its knowledge format when `--checker` names it, and writes the queue's index when everything passes. The checker is run only when the checksum of the file is pinned in `factory/checkers.yaml`; any other file is refused and not run. A source whose `resource` is a path must name a file that exists, read from the top of the repository, from the draft's own folder or from its place in the wiki; an address (`https:`, `doi:`) is not fetched. Fix what it refuses. Then record what became of each note:

```
uv run tools/explore.py resolve --exploration <x> --by <you> --model <your model> --note NOTE-001 --disposition drafted --ref <queue path of the page>
```

## What this skill refuses

- A `verified` event, a status other than `draft`, or any wording that says a page is established.
- Writing into a bundle. Drafts go to the queue; a steward merges.
- A page of type `finding`, or a lead restated as fact.
- A statement with no source.
- Settling a disagreement with a signed concept by picking a side quietly. Say `contradicts` and why.
