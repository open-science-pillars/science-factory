---
name: read-what-is-known
description: "Before any work on a question: find the knowledge that bears on it, read it, and say what it rules in, rules out and warns about, with who signed each page. Use at the start of an exploration, a plan, a review or a draft."
---

# Read what is known

Work starts from what is already known, pitfalls included. This skill carries no facts about any dataset: every fact is read from the knowledge at the time, so yesterday's page is found today.

The knowledge base is a wiki in the Open Knowledge Format v0.2: Markdown pages with small front matter (`type`, and where present `generated`, `sources`, `verified`, `status`, `stale_after`), an `index.md`, a `log.md` and a `quickstart.md`. Here it is `openwiki/`; any other in that form is read the same way, by naming its directory. Two ways to read it give the same pages:

- **When the tools `openwiki_search` and `openwiki_read` are available, use them.** Search with the question, then read every page the search returns. They are read-only.
- **Otherwise read the files**: start at `<wiki>/quickstart.md`, and use the command in step 1, which lists the pages that bear on a question.

Before an exploration starts, use `knowledge.py about` (step 1): it reads pages, never data, and is the only reading before data is set aside. Once it has started, run `explore.py known` either way: it writes the list into the log.

## Steps

1. **Ask the tool, not your memory.** From the repository root:

   ```
   uv run tools/knowledge.py about --question "<the question, in the scientist's words>" \
     --wiki <the wiki directory, such as openwiki> [--wiki <another>] \
     [--drafts <the queue of drafted pages>]
   ```

   Inside a started exploration use `uv run tools/explore.py known --exploration <dir> --by <you> --model <your model> --wiki ... [--drafts ...]`: it lists the same pages and writes what was listed into the exploration log. The first look is refused until this has run and a page is recorded as read.

   Add `--tag` for a product, quantity or place the question implies and does not say. Run it again with other words if the list looks thin. An empty list is a result: say so.

2. **Read every page listed**, whole, those that came in only by a link included, and the pages they point at that bear on the question: the search matches shared words, so it lists some that do not bear on it and can miss one a listed page leans on. A page that plainly came in on a stray word may be skimmed, and you say so.

3. **Say what each page is before you lean on it.** The list says, for each page, its status and who signed it.
   - **Signed** (the page's own signature lines name a person: a `verified` event by a person in its front matter, or a `Signed-by: human:...` line): established for this organization. Follow it. If the work would contradict it, stop and raise a note; do not quietly do otherwise.
   - **Not signed**, in the wiki: working memory, written down and not yet read by a steward. Use it, and say it is unsigned.
   - **A draft in the queue**: a colleague's note from earlier work. Use it to avoid rediscovering what was already seen, check it against your own data before relying on it, and say every time that it is a draft.

4. **Write down what each page changes**, in three kinds:
   - what it **rules in**: a method, a product version, a way of comparing that is the accepted one;
   - what it **rules out**: something the question as asked would have you do that the page refuses;
   - what it **warns about**: a pitfall that makes a wrong answer look right.

   Inside an exploration record each with `uv run tools/explore.py read --exploration <dir> --by <you> --model <your model> --concept <the path as the list printed it, or the file> --takes "<what it changes here>"`, adding `--depth skimmed` for a page not read whole (`whole` is the default). A page the list did not print is recorded by its file, and the lead says the search did not list it. The lead lists what was read, skimmed, and listed but not read.

5. **Say what is missing.** If the question needs something the knowledge does not have, that is a note (`explore.py note --kind missing`, or `sf.py note`), not something to fill in from memory.

6. **When nothing known applies**, because the list is empty or holds only stray-word pages (an example's record, for a question about another): `known` logs the list anyway; record each listed page as read, skimmed (`--takes "bears on nothing here"`); raise a `missing` note for the page that should exist. Then no page gives the fresh data's boundary: take it from the metadata, start without `--boundary-from`, and say in `--why` that no page gave it.

## What comes out

A short list, page by page: the path, signed by whom or not signed, and what it rules in, rules out or warns about for this question. Then what is missing. Cite each page by its path whenever you use it later.

## What this skill refuses

- A fact about a dataset stated from memory when a page could have been read.
- A draft or an unsigned page presented as established.
- Skipping a page because its title looked unrelated.
