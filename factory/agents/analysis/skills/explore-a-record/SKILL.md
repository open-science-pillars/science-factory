---
name: explore-a-record
description: "Explore a record freely without spending the data a later test will need: read what is known, set data aside, then look, with every look logged, figures kept and every choice recorded. Use when a request asks what is there, how well something works, or where it fails."
---

# Explore a record

Exploring is looking to find out what is there: most of the work, and nothing in it is locked. The one rule is to say it was exploring; `tools/explore.py` keeps the log, counts what was tried, keeps the figures and holds the fence. This skill is the procedure and carries no facts about any dataset.

Run every command from the repository root. `<x>` is the exploration's directory, by convention `<work>/explorations/<ID>`; studies and the record of openings sit beside it in `<work>/studies/`. A person can follow the same steps as `--by human:<your name>`.

**The order.** Read what is known before you set anything aside, and read only knowledge: signed pages and drafted pages (`knowledge.py about`, then the pages themselves), never data, never the contents of a data file, never an earlier answer to the same question. Take from the knowledge where the boundary of the set-aside should fall. Then propose the fresh data from metadata only (`fresh_data.py propose`, the skill `propose-fresh-data`), and set it aside with `explore.py start --fresh-data`, before any look, naming the page the boundary came from with `--boundary-from`. Then run `explore.py known` and `explore.py read`, which write into the log what was listed and what each page changes; the first look is refused until they have. What is set aside is never narrowed afterwards; if the knowledge gives no boundary, set aside the widest honest window and say so.

## 1. Read what is known, from knowledge only

Use the `read-what-is-known` skill with `knowledge.py about`, and read the pages it lists: the only reading before data is set aside. The boundary of the set-aside (a change of processing, a release date, the end of a record) is a fact about the data, so it comes from a page, not a guess and not the data.

## 2. Set data aside, before any look

Read the request for what has already been seen. Propose the fresh data with the skill `propose-fresh-data`, from metadata only (the next release, a later period, another site or region, or a random set aside), with reasons in words and the test size; use the arguments it prints and add `--fresh-data <the proposal>`. Other ways the tool knows (contrasting conditions, another instrument or record, forecasts scored later) are set aside the same way without a proposal; say why in `--why`. Prefer what a later study would want: whether a method travels wants other sites, not only a later period.

```
uv run tools/explore.py start --exploration <x> --id <ID> --by <you> --model <your model> \
  --question "<one sentence ending in a question mark>" --request <the request file> \
  --subject <key=value,key=value: the thing the data is about> \
  --how "a later period" --set-aside-window <START:END, or START: to keep it open> \
  --why "<why this is the data to set aside>" --boundary-from <the page the boundary came from> \
  --working "<what will be explored, in words>" --working-window <START:END> \
  --working-data <the file or folder that holds the data to explore> --fresh-data <x>/fresh-data.yaml
```

- `--subject`: your own keys (such as `site=...,sensor=...`). A later plan's `pair` must carry the same keys and values, matched through case and spacing and nothing else, so write them as the plan will.
- If the knowledge gives no boundary, set aside the widest honest window and say so in `--why`. A set-aside is never narrowed afterwards.
- When the working window stops before the set-aside begins, the tool names the stretch in neither. Nothing protects it: leave it alone unless the request needs it, and say in the lead what you did.

From here on you never fetch, read, plot or ask about what was set aside, by any route. The tool refuses a look that names it: a path, a release, a date inside the window, a site in any way people write one (with its agency in front, or the bare number). So keep set-aside dates out of your scripts and lead altogether, and name a boundary by the page that gives it. A look that names a folder, a pattern, a tilde path or a variable is refused too. On Linux the kernel keeps a look's script from opening anything but its scratch folder and the system's folders, and the look's last line says whether that held. The tool cannot stop a script fetching the data over the network, nor, without the kernel fence, opening a path it builds itself: that is on you.

## 3. Record what was read

```
uv run tools/explore.py known --exploration <x> --by <you> --model <your model> --wiki <the wiki> [--drafts <the queue>]
uv run tools/explore.py read --exploration <x> --by <you> --model <your model> --concept <the path as `known` printed it> \
  --takes "<what this page rules in, rules out or warns about here>" [--depth skimmed]
```

The first look is refused until `known` has run and a page is recorded as read. A page that came in on a stray word may be skimmed: say so with `--depth skimmed`, and the lead will.

## 4. Look

A look is one script, run through the tool, with a reason:

```
uv run tools/explore.py look --exploration <x> --by <you> --model <your model> --why "<what this look is trying to find out>" \
  -- uv run looks/<script>.py <arguments>
```

- Write each script in `<x>/looks/`. Paths in the command are read from the exploration directory: give the data file and a skill's script by full path.
- The script runs in a scratch folder holding only itself and the files the command names; a file from outside the exploration is handed in under `outside/`, and the word naming it rewritten to say so. Name every file it reads, as its own word or after an `=`; declare a helper it imports, or a settings file it opens itself, with `--also-reads <file>` before the `--`. A folder, a pattern (`*`, `?`, brackets, braces), a tilde path, a variable and several paths in one word are refused.
- What the script writes in its folder comes back into the exploration, except into the tool's and reviewer's places (`receipts/`, `verdicts/`, `review/`, `notes/`, `leads/`, `hand-over/`, the log, the lead). A link it leaves is not followed.
- Print nothing carrying a set-aside date, site or release, a retrieval stamp included: the fence reads output like a file, and output that crosses it spoils the exploration and is withheld.
- A look calls no tool of this package (`explore.py`, `sf.py` and `knowledge.py` refuse a command started inside one) and leaves no process running (whatever it leaves is ended with it).
- Under the Claude Code harness a command is one plain line, every option spelled out, every value in plain words: no brackets, braces, semicolons, `#`, `$`, `!`, `&`, `|`, `<`, `>`, backslashes or backticks, even inside quotes.
- Every look goes through the tool; a quick print of a file in a shell is a look nobody counted.
- Start with the shape of the record before any statistic: `uv run <repository>/skills/explore-a-record/scripts/describe_record.py <data file>` prints keys, counts, ranges and time span.
- **Draw it.** `uv run <repository>/skills/explore-a-record/scripts/plot_xy.py <data file> --rows <key> --x <key> --y <key> [--color <key>] [--residual] --out figures/<name>.svg` draws one quantity against another, coloured by a third, or the residual from a straight line. A file a look writes into `figures/` (.svg, .png, .pdf, .jpg) is that look's figure, listed in the receipt by checksum, for the lead to show. Before fitting anything, plot the residual against each thing the record carries (a slope, a flag, a time): a picture finds in a minute what a table of fits does not.
- Use the method the knowledge rules in (a script the capability ships) before your own, and say when you depart from it.
- Ask why, not only how much: when a number is off, write down a physical guess and look for what would show it wrong.
- Print findings as numbers with units and counts; the output is kept by checksum and is what a reviewer reads. When one look holds several fits, cuts or groups, print `comparisons: N`, which the lead adds up beside the count of looks. Print `none` for an empty group (a source with no months in a window) and catch the warning a mean of nothing raises: `None`, `nan` and a warning reach the receipt and read as results.
- Say what a flag value is: print the count at each value of a quality flag before screening on it, and never call an observation "unflagged" unless it is at the clean value. Call an interval a confidence interval and name its model.
- A failed look is still a look and still counted; do not delete scripts to tidy the record.
- Look as hard for where it does not hold: split by the conditions the question cares about, look at the worst cases by name, and check whether a few points carry the result.

**Notebooks.** A look may be a script or a marimo notebook (a `.py` file whose `# /// script` header names marimo), run the same way, with `uv run`. Use a notebook when the work is a chain of steps a person will want to read or change cell by cell, and add `--export html` to keep its page as a figure the person opens at the so what and the lock; use a script for one computation. Only what a notebook prints is its output, so print each number you will quote. A Jupyter notebook is given as `uv run looks/NAME.ipynb`: the tool strips its outputs, converts it beside itself to `looks/NAME.py` and runs that; from then on run the `.py`. A notebook session (`explore.py session`) is a person's, never an agent's: marimo's editor inside the fence, logged by each saved version and never by a cell run. A number seen in a session, or in a person's account of one, is quoted only once the session's final notebook has run as a look and printed it, and the lead cites that look.

## 5. Record choices when you make them

Every time you pick one way over another (which observations to drop, which tolerance, which model form, which terms in a fit, which period to show), record it then:

```
uv run tools/explore.py choice --exploration <x> --by <you> --model <your model> --choice "<what you chose>" \
  --alternative "<another way>" --alternative "<another>" --rests-on "<what it rests on>" --look LOOK-00N
```

The lead shows how many looks had run when each choice was written down; one recorded after the looks it governs reads as made after looking, whatever you intended. Record it before the look that depends on it when you can, and otherwise say in `--rests-on` what you had already seen. The form of a model is a choice (a term for time or a covariate, a straight line), and so are what a write-up says and what a proposed test asks, when settled after looking. Run the alternative as a look too when you can, so the lead can say how much the choice moves the answer.

## 6. Raise notes

Anything missing, wrong or stale in the data or the knowledge, and any dead end:

```
uv run tools/explore.py note --exploration <x> --by <you> --model <your model> --kind <missing|wrong|stale|contradiction|method|dead-end> \
  --about "<the product, field or page>" --text "<what, with numbers>" --evidence receipts/LOOK-00N.json
```

Check first whether the knowledge already says it: a pitfall it names and you met is one line in the lead, not a note.

## 7. End

**When to end.** After `explore.py lead`, do not call `end`: status names the review agent, and you stop. When the review comes back, answer it; a revised lead is a new version and is reviewed again, and so is a lead whose wording was corrected after its review. Call `end --outcome lead` only when the lead as it stands has been reviewed, a person has said it is worth confirming (`status` shows their so what), and you will not revise it further; the tool refuses it earlier. If the person says try instead, their direction is your next question: explore it and write a new version. You never record a so what. An exploration with no lead ends when you choose, as a note, a method or a stop.

A lead needs a reviewer named first: `explore.py lead` is refused, and `status` shows `before_a_lead`, until the coordinating agent has named one (`explore.py reviewer`). If you get there first, write `lead.yaml`, stop and hand back. A person exploring by hand asks a colleague who did none of the exploring to name the reviewer.

An exploration ends in a lead (the `write-up-a-lead` skill), a note, a method (`end --outcome method --file <script>`) or a stop, all honest. `uv run tools/explore.py status --exploration <x>` says where it stands and who is next.

## What this skill refuses

- Reading data, or an earlier answer to the same question, before data is set aside.
- Looking at what was set aside, or looking outside the tool.
- Calling a tool of this package from inside a look, or naming your own reviewer.
- A number in a write-up that is not in a look's output as it was printed.
- A choice made after looking and left unrecorded, the form of the model included.
- Calling what was found a finding, a result or a validation. It is a lead.
