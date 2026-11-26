# The assistants, the exploring loop and the knowledge loop: review register

**Open Science Pillars (OSP), a personal project (personal hat) · 2026-11-26 · what was attacked, what it found, what changed, what remains. One round, by the builder, and two rounds still owed.**

**Said first, because it decides how to read the rest.** The build asked for two independent reviewers who had not seen the work: one to attack it, one a working hydrologist reading the example cold. Neither review happened. The assistant that built this could not start another assistant (it had no tool to start one, and the Claude Code program in its environment could not authenticate). What is recorded here is the builder attacking its own work, with the code in front of it. That finds real holes, and it found eleven; it is not a substitute for a reviewer who does not know where the builder looked. The two owed reviews are set out at the end, ready to run.

## The attack on the tools (the builder, playing the tester)

Four aims, as the brief gave them: get held-out data into an exploration, get a lead signed as a finding, get a draft marked as signed, get a role to do another role's job. Every finding was shown by running the tool.

| # | Severity | Finding | Disposition |
|---|---|---|---|
| A1 | blocker | **A look could run the study tool.** `explore.py look -- {python} mvp/sf.py lock ... --by human:x` was accepted, because a look may run any script. Under the Claude Code runner the analysis role's one open door was the look, and through it every command of every tool, under any name. | Fixed. A look whose script is `sf.py`, `explore.py`, `knowledge.py` or `system_trial.py` of this package is refused; self-test added. A script that calls one of them from inside is not seen: stated below. |
| A2 | blocker | **A second exploration could explore what the first set aside.** `start` checked the new set-aside against what was already explored, and never the new working window against what another exploration had set aside for the same subject. | Fixed. `start` refuses a working window that reaches into another exploration's set-aside for the same subject, and takes those windows into its own fence; two self-tests added. |
| A3 | major | **Data with its times under an undeclared key crossed the fence.** The fence read dates only under the declared time keys, so a file with `"when": "2025-06-01..."` in its rows was let through. | Fixed. A date under any key inside a list of rows counts as a time of the data; a single date at the top of a file (when it was retrieved) still does not; self-test added. Times kept as numbers (seconds since an epoch) are not seen: stated below. |
| A4 | major | **A lead could quote any number.** Nothing tied a number in the lead to a look. The example's own lead showed it: version 3 quoted 0.798 from a look it no longer cited. | Fixed. `explore.py lead` refuses a decimal number in the lead's own words that is in the output of none of the looks it cites; self-test added. Whole numbers and the proposed plan's numbers are not checked. |
| A5 | major | **A draft could carry a signature under another spelling.** `Verified_by:` in the front matter, or a `Signed-by:` line in the body, passed the queue, which looked only for the key `verified`. | Fixed. Any front matter key containing "verif" or "sign", and any `Signed-by:` line, is refused; two self-tests added. |
| A6 | major | **The knowledge search drowned the pages that mattered.** One shared common word ("gauge") listed precipitation and basin pages for a river height question, 13 pages of which 5 were noise. | Fixed. A page needs two shared words and a score near the best match, a word most of the wiki uses counts for little, and a pitfall filed against a listed dataset is listed whatever its words. The same question now lists 8 pages, all on the product. |
| A7 | minor | **In a wiki of three pages every word was "generic"**, so the overlap check found no overlap and a draft repeating a page passed. Found by the stand-alone example failing. | Fixed. A word is generic only when more than two pages and a quarter of the wiki carry it. |
| A8 | minor | **The role check blocked brackets in a quoted reason**, so `--why "pairs (15 min)"` was refused as if it were a subshell. | Fixed. Quoting is read as a shell reads it; `$`, backticks, backslashes and newlines are refused anywhere. Four self-tests added. |
| A9 | limit, stated | **A lead can be attached to a study as its finding after a real opening.** The study tool takes any file. `explore.py check-study` refuses a study whose attached finding is the lead or carries its banner, and the study tool is not edited here, so nothing stops it at the attach. | Stated. Held by `check-study` when it is run, by the review assistant, and by the steward reading what they sign. |
| A10 | limit, stated | **A reviewer is a name.** `explore.py review --by agent:someone-new`, typed by the assistant that explored, is accepted: the tool refuses only names that appear in the work. The Claude Code runner's check holds `--by` to the role; the by-hand runner does too; a bare command line holds nothing. | Stated, as the same limit the study tool states for itself. |
| A11 | limit, stated | **The subject is matched by its text.** An exploration of the same reach under another spelling of the subject shares no fence with the first. The study tool has the same limit and prints the record at the lock for a person to read. | Stated. |

What was tried and held: a look through a shell, `python -c`, a link with an innocent name pointing at set-aside data, a file whose declared window overlaps, a date passed as an argument, a script naming a set-aside date, a look that writes set-aside data into the exploration (the exploration is spoiled and can end only as a stop), a hand-over without a review, a review by the explorer under another case of its name, a hand-over by the explorer, a study holding out the explored year (refused by `check-study`, and the unedited study tool's own record names the exploration), a study started from another request, a draft at status stable, a draft of type finding, a draft with no sources, a draft that overlaps a signed page without saying so, a role file that allows the lock (the role check fails), a rendered role edited by hand (the drift check fails), a role defined only in `.claude/` (the drift check fails).

## The example, read by its own author with the review checklist

Not the hydrologist's cold reading that was asked for. What the two reviews inside the example found is in `examples/baton-rouge/explorations/EXPLORATION-0001/verdicts/`. The points a hydrologist would most want checked, and which the builder cannot judge:

- Whether a gain from a regression on gauge elevation and time is what a river scientist would call "following", or whether they would want the stage-dependent slope between the gauge and the reach centre treated first.
- Whether the two drafted pages are true beyond this reach and year, and whether the first is worth having without a cited account of what `dark_frac` measures on a river reach (the draft says the bundle does not give one).
- Whether the second draft is right to say it contradicts the signed recipe, or whether "narrows" is the fair word.
- Whether the knowledge listing (eight pages, two of them about lakes) would help or annoy at the start of a day's work.

## What still stands

- **Independent review has not happened.** Neither of the two reviewers the build asked for, and no review inside the example by an assistant with a fresh context.
- **The Claude Code runner has not been run against Claude Code.** Its three scripts test themselves; that the platform calls the hook and applies the tools was not exercised.
- **A script can read what its command does not name.** The network, a path built at run time, a tool of this package called from inside the script. The fence reads the command, the files it names and what the look leaves behind. This is the study tool's first limit and it is not answered here.
- **Times kept as numbers, and data that is not text, are outside the fence's reading.** Data that is not text is refused; numeric times are not seen.
- **Nothing was run against the OpenWiki tool.** The wiki's layout, the pointer block in `AGENTS.md` and the two tool names follow its README as relayed; the marker syntax and the tools' arguments are guesses.
- **A9, A10 and A11 above.**
- **The overlap check cannot read meaning.** It makes a draft say how it relates to what it overlaps; whether "extends" should have been "contradicts" is for the review assistant and the steward.

## The two reviews that are owed

Each is to be given to an assistant that has not seen this work, with the repository and nothing else.

**The tester.** "You are testing a research tool. In this repository, `mvp/loops/explore.py` lets an assistant explore data after setting some aside, `mvp/loops/knowledge.py` checks drafted knowledge pages, `assistants/` defines four roles and `runners/claude-code/allow.py` decides what each role may do. Try to do each of these and prove every success by running the tool: get data that an exploration set aside into one of its looks; get a lead recorded, attached or signed as a finding; get a drafted page through `check-drafts` marked as signed or verified; get one role to do another role's job under the Claude Code runner's check. Read `reviews/ASSISTANTS-AND-EXPLORING.md` only after you have tried, then say which of your attacks it does not list."

**The hydrologist.** "You are a working river hydrologist. Read `examples/baton-rouge/README.md` cold, then the request, the lead (`explorations/EXPLORATION-0001/lead.md`), the two reviews beside it, and the two drafted pages in `knowledge-queue/`. Judge two things and say why: would exploring this way, with data set aside first and every look logged, actually help you in your own work, and where would it get in your way; and is each drafted page true, is it worth having, and what would you need before you would sign it."

Their findings go in this file as a second and third table, with what each changed.
