---
name: read-what-is-known
description: "Before any work on a question: find the knowledge that bears on it, read it, and say what it rules in, rules out and warns about, with who signed each page. Use at the start of an exploration, a plan, a review or a draft."
---

# Read what is known

Work starts from what is already known, pitfalls included. This skill is the procedure for that. It carries no facts about any dataset: every fact is read from the knowledge at the time, so a page added or corrected yesterday is found today.

## Steps

1. **Ask the tool, not your memory.** From the repository root:

   ```
   uv run mvp/knowledge.py about --question "<the question, in the scientist's words>" \
     --bundle <the capability's knowledge folder> [--bundle <a provider's>] \
     [--drafts <the queue of drafted pages>]
   ```

   Inside an exploration use `uv run mvp/explore.py known --exploration <dir> --by <you> --bundle ... [--drafts ...]`: it lists the same pages and writes what was listed into the exploration log. The first look is refused until this has run.

   Add `--tag` for a product, a quantity or a place the question implies and does not say. Run it again with other words if the list looks thin. An empty list is a result: say so.

2. **Read every page listed**, whole, including the ones that came in only by a link. Read the pages a page points at when they bear on the question.

3. **Say what each page is before you lean on it.** The list says, for each page, its status and who signed it.
   - **Signed** (a `verified` event by a person): established for this organization. Follow it. If the work would contradict it, stop and raise a note; do not quietly do otherwise.
   - **Not signed**, in the bundle: written down and not yet read by a steward. Use it, and say it is unsigned.
   - **A draft in the queue**: a colleague's note from earlier work. Use it to avoid rediscovering what was already seen, check it against your own data before relying on it, and say every time that it is a draft.

4. **Write down what each page changes**, in three kinds:
   - what it **rules in**: a method, a product version, a way of comparing that is the accepted one;
   - what it **rules out**: something the question as asked would have you do that the page refuses;
   - what it **warns about**: a pitfall that makes a wrong answer look right.

   Inside an exploration record each with `uv run mvp/explore.py read --exploration <dir> --by <you> --concept <file> --takes "<what it changes here>"`.

5. **Say what is missing.** If the question needs something the knowledge does not have, that is a note (`explore.py note --kind missing`, or `sf.py note`), not something to fill in from memory.

## What comes out

A short list, page by page: the path, signed by whom or not signed, and what it rules in, rules out or warns about for this question. Then what is missing. Cite each page by its path whenever you use it later.

## What this skill refuses

- A fact about a dataset stated from memory when a page could have been read.
- A draft or an unsigned page presented as established.
- Skipping a page because its title looked unrelated.
