---
name: explore-a-record
description: "Explore a record freely without spending the data a later test will need: read what is known, set data aside, then look, with every look logged, figures kept and every choice recorded. Use when a request asks what is there, how well something works, or where it fails."
---

# Explore a record

Exploring is looking to find out what is there. It is most of the work and nothing in it is locked. The one rule is to say that it was exploring, and the tool (`tools/explore.py`) makes that easy: it keeps the log, counts what was tried, keeps the figures and holds the fence. This skill is the procedure. It carries no facts about any dataset.

Run every command from the repository root. `<x>` is the exploration's directory, by convention `<work>/explorations/<ID>`; the confirming studies and the record of what has been opened sit beside it in `<work>/studies/`.

A person can explore with the same tool: act as `--by human:<your name>` and follow the same steps. Nothing below needs an agent.

**The order.** Read what is known before you set anything aside, and read only knowledge: signed pages and drafted pages (`knowledge.py about`, then the pages themselves), never data, never the contents of a data file, never an earlier answer to the same question. Take from the knowledge where the boundary of the set-aside should fall. Then propose the fresh data from metadata only (`fresh_data.py propose`, the skill `propose-fresh-data`), and set it aside with `explore.py start --fresh-data`, before any look, naming the page the boundary came from with `--boundary-from`. Then run `explore.py known` and `explore.py read`, which write into the log what was listed and what each page changes; the first look is refused until they have. What is set aside is never narrowed afterwards; if the knowledge gives no boundary, set aside the widest honest window and say so.

## 1. Read what is known, from knowledge only

Use the `read-what-is-known` skill with `knowledge.py about`, and read the pages it lists. This is the only reading before data is set aside. Take from it where the boundary of the set-aside should fall: a change of processing, a release date, the end of a record. That is a fact about the data, so it comes from a page, not from a guess and not from opening the data.

## 2. Set data aside, before any look

Read the request for what has already been seen. Then propose the fresh data with the skill `propose-fresh-data`: from metadata only, one of the next release, a later period, another site or region, or a random set aside, with your reasons in words and the size of test it allows. The proposing tool prints the arguments that set it aside; use them, and add `--fresh-data <the proposal>`. Other ways the tool knows (a period of contrasting conditions, a different instrument or record, forecasts scored later) are set aside the same way without a proposal; say why in `--why`. Prefer what a later confirming study would most plausibly want: a question about whether a method travels wants other sites set aside, not only a later period at the same site.

```
uv run tools/explore.py start --exploration <x> --id <ID> --by <you> --model <your model> \
  --question "<one sentence ending in a question mark>" --request <the request file> \
  --subject <key=value,key=value: the thing the data is about> \
  --how "a later period" --set-aside-window <START:END, or START: to keep it open> \
  --why "<why this is the data to set aside>" --boundary-from <the page the boundary came from> \
  --working "<what will be explored, in words>" --working-window <START:END> \
  --working-data <the file or folder that holds the data to explore> --fresh-data <x>/fresh-data.yaml
```

- `--subject`: the keys are yours (for example `site=...,sensor=...`). A later plan's `pair` must carry the same keys and values; they are matched through case and spacing and through nothing else, so write them the way the plan will.
- If the knowledge gives no boundary, set aside the widest honest window and say so in `--why`. A set-aside is never narrowed afterwards.
- When the working window stops before the set-aside begins, the tool names the stretch that is in neither. Nothing protects it. Leave it alone unless the request needs it, and say in the lead what you did.

From here on you do not fetch, read, plot or ask about what was set aside, by any route. The tool refuses a look that names it: a path, a release, a date inside the window, a site in any of the ways people write one (with its agency in front, or the bare number). So keep dates inside the set-aside window out of your scripts and your lead altogether, and name a boundary by the page that gives it. The tool also refuses a look that names a folder, a pattern, a tilde path or a variable, because each reaches files it never read. On Linux the kernel keeps a look's script from opening anything but its own scratch folder and the system's folders, and the look's last line says whether that held. The tool cannot stop a script fetching the data over the network, and where there is no kernel fence it cannot stop a script opening a path it builds itself; that is on you.

## 3. Record what was read

```
uv run tools/explore.py known --exploration <x> --by <you> --model <your model> --wiki <the wiki> [--drafts <the queue>]
uv run tools/explore.py read --exploration <x> --by <you> --model <your model> --concept <the path as `known` printed it> \
  --takes "<what this page rules in, rules out or warns about here>" [--depth skimmed]
```

The first look is refused until `known` has run and at least one page is recorded as read. A page that came in on a stray word may be skimmed; say so with `--depth skimmed`, and the lead will.

## 4. Look

A look is one script, run through the tool, with a reason:

```
uv run tools/explore.py look --exploration <x> --by <you> --model <your model> --why "<what this look is trying to find out>" \
  -- uv run looks/<script>.py <arguments>
```

- Write each script in `<x>/looks/`. A path in the command is read from the exploration directory: give the data file and a skill's script by their full paths.
- The script runs in a scratch folder of its own, which holds the script and the files the command names and nothing else. A file from outside the exploration is handed to it under `outside/`, and the word that named it is rewritten to say so. Name every file the script reads, as a word of its own or after an `=`. A helper the script imports, or a settings file it opens by itself, is declared with `--also-reads <file>` before the `--`. A folder, a pattern (`*`, `?`, brackets, braces), a tilde path, a variable and several paths joined into one word are refused.
- What the script writes in its folder comes back into the exploration, except into the places the tool or a reviewer keeps (`receipts/`, `verdicts/`, `review/`, `notes/`, `leads/`, `hand-over/`, the log, the lead). A link it leaves is not followed.
- Print nothing that carries a date inside the set-aside window, a set-aside site or a set-aside release, a retrieval stamp included. What a look prints is read by the fence like a file: output that crosses it spoils the exploration and is withheld.
- A look calls no tool of this package and leaves no process running: `explore.py`, `sf.py` and `knowledge.py` refuse a command started from inside a look, and whatever a look leaves running is ended with it.
- Under the Claude Code harness a command is one plain line with every option spelled out. Write `--why` and every other value in plain words: no brackets, braces, semicolons, `#`, `$`, `!`, `&`, `|`, `<`, `>`, backslashes or backticks, even inside quotes.
- Every look goes through the tool. A quick print of a file in a shell is a look nobody counted.
- Start with the shape of the record before any statistic: `uv run <repository>/skills/explore-a-record/scripts/describe_record.py <data file>` prints keys, counts, ranges and time span.
- **Draw it.** `uv run <repository>/skills/explore-a-record/scripts/plot_xy.py <data file> --rows <key> --x <key> --y <key> [--color <key>] [--residual] --out figures/<name>.svg` draws one quantity against another, coloured by a third, or the residual from a straight line. A file a look writes into `figures/` (.svg, .png, .pdf, .jpg) is a figure of that look: the receipt lists it by checksum and the lead can show it. Plot the residual against each thing the record carries before you fit anything to it: a slope, a flag, a time. A picture finds in a minute what a table of fits does not.
- Use the method the knowledge rules in (a script the capability ships) before writing your own, and say when you depart from it.
- Ask why, not only how much. When a number is off, write down a physical guess for it and look for what would show the guess wrong.
- Print what you found as numbers with units and counts; the output is kept by checksum and is what a reviewer will read. When one look holds several fits, cuts or groups, print a line `comparisons: N`: the lead adds them up beside the count of looks. Where a group has nothing (a source with no months in a window), print `none` for it, and catch the warning a mean of nothing raises: `None`, `nan` and a warning reach the receipt and read as results.
- Say what a flag value is. Print the count of observations at each value of a quality flag before you screen on it, and never call an observation "unflagged" unless it is at the flag's clean value. Call an interval a confidence interval and say which model it comes from.
- A failed look is still a look and is still counted. Do not delete scripts to tidy the record.
- Look for where it does not hold as hard as for where it does: split by the conditions the question cares about, look at the worst cases by name, and check whether a few points carry the result.

## 5. Record choices when you make them

Every time you pick one way over another (which observations to drop, which tolerance, which model form, which terms in a fit, which period to show), record it then:

```
uv run tools/explore.py choice --exploration <x> --by <you> --model <your model> --choice "<what you chose>" \
  --alternative "<another way>" --alternative "<another>" --rests-on "<what it rests on>" --look LOOK-00N
```

The log keeps how many looks had run when the choice was written down, and the lead shows the order. A choice recorded after the looks it governs reads as a choice made after looking, whatever you intended. So record a choice before the look that depends on it when you can, and when you cannot, say in `--rests-on` what you had already seen. The form of a model is a choice: a term for time, a term for a covariate, a straight line. So is what a write-up says and what a proposed test asks, when they were settled after looking.

When you can, run the alternative as a look too, so the lead can say how much the choice moves the answer.

## 6. Raise notes

Anything missing, wrong or stale in the data or the knowledge, and any dead end:

```
uv run tools/explore.py note --exploration <x> --by <you> --model <your model> --kind <missing|wrong|stale|contradiction|method|dead-end> \
  --about "<the product, field or page>" --text "<what, with numbers>" --evidence receipts/LOOK-00N.json
```

Check first whether the knowledge already says it; a pitfall the knowledge names and you met is worth one line in the lead, not a note.

## 7. End

**When to end.** After `explore.py lead`, do not call `end`: status names the review agent, and you stop. When the review comes back, answer it; a revised lead is a new version and is reviewed again, and so is a lead whose wording was corrected after its review. Call `end --outcome lead` only when the lead as it stands has been reviewed, a person has said it is worth confirming (`status` shows their so what), and you will not revise it further; the tool refuses it earlier. If the person says try instead, their direction is your next question: explore it and write a new version. You never record a so what. An exploration with no lead ends when you choose, as a note, a method or a stop.

A lead needs a reviewer named first. `explore.py lead` is refused until the coordinating agent has named the reviewer of this exploration (`explore.py reviewer`); `status` shows `before_a_lead` until then. If you reach the lead before that, write `lead.yaml`, stop and hand back. A person exploring by hand asks a colleague who did none of the exploring to name the reviewer.

An exploration ends in a lead (use the `write-up-a-lead` skill), a note, a method (`end --outcome method --file <script>`), or a stop. All four are honest outcomes. `uv run tools/explore.py status --exploration <x>` says where it stands and who is next.

## What this skill refuses

- Reading data, or an earlier answer to the same question, before data is set aside.
- Looking at what was set aside, or looking outside the tool.
- Calling a tool of this package from inside a look, or naming your own reviewer.
- A number in a write-up that is not in a look's output as it was printed.
- A choice made after looking and left unrecorded, the form of the model included.
- Calling what was found a finding, a result or a validation. It is a lead.
