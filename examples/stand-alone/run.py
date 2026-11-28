# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""Run the exploring loop and the knowledge loop end to end on the stand-alone example, and check each step.

Nothing here needs another repository or the network: the record is
examples/stand-alone/record-2024.json (synthetic, with a known answer) and
the knowledge base is the wiki in openwiki/. The work is done in a scratch
folder outside the repository, made fresh on every run. It is left in
place and its path is printed, with a short list of what is in it, so
that a newcomer can open an exploration and a study and see what each
looks like on disk. Nothing is written into the repository.

What this is and is not. It is the tools, driven from the command line the
way a role would drive them, with each step checked. No agent runs in
it and no language model: it shows that the loops hold together and that
the refusals refuse, and the checks workflow runs it. Its last part takes
a study of its own (a system trial on a synthetic record, with this
repository's own method) through every stage a tool can take, and stops
where the next step is a person's: the lock. What agents do with the
same tools is the optional demo in examples/baton-rouge.

  uv run examples/stand-alone/run.py            run, check, and print where the output is
  uv run examples/stand-alone/run.py --remove   run, check, and remove the output
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
# uv refuses a setting of its own that is set and empty (UV_NATIVE_TLS=, for one) before it runs anything: the commands
# below are given the environment without such a setting, as the tools give the scripts they run
QUIET_ENV = {k: v for k, v in os.environ.items() if not (k.startswith("UV_") and not v.strip())}
GAIN_PUT_IN, CLOSE_ENOUGH = 1.03, 0.02   # the answer the record was made with (make_record.py), and how near counts
MODEL = "stand-alone-run/no-model"       # what this script's events carry where a model's name would stand: no model runs in it


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, allow_abbrev=False)
    ap.add_argument("--keep", action="store_true", help="the output is kept by default; this option is still taken and changes nothing")
    ap.add_argument("--remove", action="store_true", help="remove the scratch folder when the run is over")
    a = ap.parse_args()
    work = Path(tempfile.mkdtemp(prefix="stand-alone-")).resolve()
    steps = []

    def ran(command: list, expect: int = 0, answer: bool = False) -> str:
        """Run one command. What it prints and what it says on standard error are both returned, for reading a refusal;
        with `answer` only what it prints is returned, because that alone is the tool's answer: the launcher may add a
        warning of its own on standard error (uv does, for a deprecated setting), and a warning is not part of the answer."""
        done = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, env=QUIET_ENV)
        if done.returncode != expect:
            raise AssertionError(f"`{' '.join(str(x) for x in command[:6])} ...` ended {done.returncode}, expected {expect}:\n{(done.stdout + done.stderr)[-800:]}")
        return done.stdout if answer else done.stdout + done.stderr

    def tool(name: str, *args, expect: int = 0, answer: bool = False, model: str | None = MODEL) -> str:
        """One command of a tool. Every event an agent writes names the model that wrote it, so a command that acts
        as an agent is given `--model`; here it says that no model ran."""
        args = [str(x) for x in args]
        if model and "--by" in args and args[args.index("--by") + 1].startswith("agent:"):
            at = args.index("--by") + 2  # beside --by, and so before any `--` that begins a look's own command
            args[at:at] = ["--model", model]
        return ran(["uv", "run", str(ROOT / "tools" / name), *args], expect, answer)

    def step(name: str, cond) -> None:
        steps.append((name, bool(cond)))
        if not cond:
            raise AssertionError(name)

    try:
        x = work / "explorations" / "EXPLORATION-A"
        studies, queue, wiki = work / "studies", work / "knowledge-queue", ROOT / "openwiki"
        data = work / "data" / "record-2024.json"
        data.parent.mkdir(parents=True)
        shutil.copyfile(HERE / "record-2024.json", data)
        request = work / "request.md"
        request.write_text("# Request\n\nHow closely does the second sensor follow the reference, and where does it not? Only 2024 has been looked at.\n")
        me, reviewer, coordinator, curator = "agent:analysis-a", "agent:review-a", "agent:coordinating-a", "agent:curating-a"
        E = ("--exploration", x)

        step("a warning on standard error beside a tool's answer does not break reading the answer",
             json.loads(ran([sys.executable, "-c", "import sys; print('{\"stage\": \"set-aside\"}'); print('warning: a launcher grumbles', file=sys.stderr)"],
                            answer=True))["stage"] == "set-aside")

        # the factory itself: its definition is a tree of files, and a tool says whether the tree is valid
        said = tool("check_factory.py")
        step("the factory's definition (factory/) is valid, and the validator says what it cannot check",
             "check-factory: VALID" in said and "what this tool cannot check" in said)

        # before work: what is known, from the wiki in openwiki/, and only that
        out = tool("knowledge.py", "about", "--question", "How closely does the second sensor follow the reference?", "--wiki", wiki)
        step("the wiki answers with the pages that bear on the question, none of them signed",
             "compare-changes-not-levels.md" in out and "flagged-readings.md" in out and "NOT SIGNED" in out and "SIGNED by" not in out)

        # data is set aside first
        step("a start that sets nothing aside is refused",
             "REFUSED" in tool("explore.py", "start", *E, "--id", "EXPLORATION-A", "--by", me, "--question", "How closely does the second sensor follow the reference?",
                               "--request", request, "--subject", "record=two-sensor,sensor=second", "--how", "a later period", "--why", "x", expect=2))
        # the fresh data is proposed by the analysis agent from metadata only, before the exploration starts
        proposal = x / "fresh-data.yaml"
        propose = ("fresh_data.py", "propose", "--kind", "later-period", "--from", "2025-01-01", "--until", "2025-12-31",
                   "--what", "the whole of 2025, every pass of the second sensor and the reference",
                   "--why", "the request says only 2024 has been looked at, and the same two sensors keep running in 2025",
                   "--unfair", "a change of either sensor or of its processing at the turn of the year; the wiki page names none",
                   "--by", me, "--studies", studies)
        step("the fresh data is proposed from metadata only: the record's own data file, offered as metadata, is refused",
             "this looks like data" in tool(*propose, "--metadata", data, "--out", work / "refused.yaml", expect=2))
        said = tool(*propose, "--metadata", HERE / "metadata.yaml", "--out", proposal)
        step("the proposal says in words which data, why, what would make it unfair and how large a test it allows, from the metadata",
             all(w in said for w in ("A later period.", "**Why it suits the question.**", "**What would make it unfair.**",
                                     "Fresh: 12 items, 52 observations", "Not computed here")))
        tool("explore.py", "start", *E, "--id", "EXPLORATION-A", "--by", me, "--question", "How closely does the second sensor follow the reference?",
             "--request", request, "--subject", "record=two-sensor,sensor=second", "--how", "a later period", "--set-aside-window", "2025-01-01:2025-12-31",
             "--why", "the following year: the request says only 2024 has been looked at", "--working", "the 2024 record", "--working-window", "2024-01-01:2024-12-31",
             "--working-data", data.parent, "--boundary-from", wiki / "the-two-sensor-record.md", "--fresh-data", proposal)
        fit = work / "fit.yaml"
        fit.write_text(yaml.safe_dump({"answer_is": "checkable", "data_at_hand": "yes", "mostly": "computation",
                                       "person_must_supply": "what the scientist has already looked at, and the difference that matters",
                                       "verdict": "fit-with-a-person-steering", "why": "the gain is a number a rule can test; which readings to trust needs someone who knows the gauge",
                                       "taste_needed": "someone who knows what a degraded flag means at low stage, and which result would be unremarkable"}))
        tool("explore.py", "fit", *E, "--by", coordinator, "--file", fit)
        step("before any look the coordinating agent writes a fit note: a verdict and what the work needs from a person, shown in status as advice",
             "fit-with-a-person-steering" in json.loads(tool("explore.py", "status", *E, answer=True))["fit"])
        step("the exploration sets aside exactly what was proposed, and its log binds the proposal by checksum",
             json.loads(x.joinpath("exploration-log.jsonl").read_text().splitlines()[0])["data"]["set_aside"]["fresh_data"]["sha256"]
             == hashlib.sha256(proposal.read_bytes()).hexdigest())
        step("before data is set aside only knowledge was read, and the page the boundary came from is in the log by checksum",
             json.loads(x.joinpath("exploration-log.jsonl").read_text().splitlines()[0])["data"]["set_aside"]["boundary_read_from"][0]["path"].endswith("the-two-sensor-record.md"))
        record = [json.loads(ln) for ln in (studies / "openings.jsonl").read_text().splitlines()]
        step("what is set aside and what is explored are both in the record beside the studies",
             {ln["kind"] for ln in record} == {"set-aside", "explored"})
        look = ("look", *E, "--by", me, "--why")
        gain_script = str(HERE / "looks" / "gain.py")
        step("a look before the knowledge is listed is refused", "run `known` first" in tool("explore.py", *look, "the gain", "--", "uv", "run", gain_script, data, expect=2))
        tool("explore.py", "known", *E, "--by", me, "--wiki", wiki)
        step("listing is not reading: a look is refused until a page is recorded as read",
             "none is recorded as read" in tool("explore.py", *look, "the gain", "--", "uv", "run", gain_script, data, expect=2))
        # one page is named the way `known` prints it (repository/wiki/page), the other by its file
        tool("explore.py", "read", *E, "--by", me, "--concept", f"{ROOT.name}/openwiki/compare-changes-not-levels.md",
             "--takes", "rules out a level difference; rules in a gain with an intercept")
        tool("explore.py", "read", *E, "--by", me, "--concept", wiki / "flagged-readings.md",
             "--takes", "warns that a degraded reading can steer the gain; leave them out and give it both ways")

        step("an agent that does not say which model it is cannot write to the log",
             "names the model that wrote it" in tool("explore.py", "note", *E, "--by", me, "--kind", "missing", "--about", "x", "--text", "y", expect=2, model=None))

        # looks, the fence, choices, a note
        out_all = tool("explore.py", *look, "the gain with every reading", "--", "uv", "run", gain_script, data)
        out_screened = tool("explore.py", *look, "the gain with degraded readings left out", "--", "uv", "run", gain_script, data, "--exclude-flag-at-or-above", "2")
        gain_all = float(re.search(r"gain (\d+\.\d+)", out_all).group(1))
        gain = float(re.search(r"gain (\d+\.\d+)", out_screened).group(1))
        step(f"the exploring comes close to the answer the record was made with (found {gain}, put in {GAIN_PUT_IN})", abs(gain - GAIN_PUT_IN) <= CLOSE_ENOUGH)
        step("without the screen the gain is further from it, as the wiki page warns", abs(gain_all - GAIN_PUT_IN) > abs(gain - GAIN_PUT_IN))
        later = work / "scratch" / "record-2025.json"
        later.parent.mkdir()
        subprocess.run(["uv", "run", str(HERE / "make_record.py"), "--year", "2025", "--out", str(later)], check=True, capture_output=True, env=QUIET_ENV)
        step("a look that names the set-aside year is refused, and the refusal is logged",
             "set aside" in tool("explore.py", *look, "peek at the next year", "--", "uv", "run", gain_script, later, expect=2)
             and json.loads(x.joinpath("exploration-log.jsonl").read_text().splitlines()[-1])["kind"] == "look.refused")
        step("a look that reaches the set-aside year through its folder, a pattern or a word after `=` is refused too",
             "names a folder" in tool("explore.py", *look, "peek through the folder", "--", "uv", "run", gain_script, later.parent, expect=2)
             and "holds a pattern" in tool("explore.py", *look, "peek through a pattern", "--", "uv", "run", gain_script, later.parent / "record-*.json", expect=2)
             and "set aside" in tool("explore.py", *look, "peek after an equals sign", "--", "uv", "run", gain_script, f"--data={later}", expect=2))
        shutil.rmtree(later.parent)
        plot = str(ROOT / "factory" / "agents" / "analysis" / "skills" / "explore-a-record" / "scripts" / "plot_xy.py")
        tool("explore.py", *look, "a picture: what is left of the second sensor after its straight line on the reference, coloured by flag",
             "--", "uv", "run", plot, data, "--x", "reference", "--y", "sensor", "--color", "flag", "--label", "time", "--residual", "--out", "figures/residual.svg")
        receipt = json.loads((x / "receipts" / "LOOK-003.json").read_text())
        step("a look that draws a figure has it in its receipt by checksum, and the launcher's warnings are not in its output",
             [f["file"] for f in receipt["figures"]] == ["figures/residual.svg"] and (x / "figures" / "residual.svg").read_text().startswith("<svg")
             and "warning:" not in (x / "receipts" / "LOOK-003.out.txt").read_text())
        tool("explore.py", "choice", *E, "--by", me, "--choice", "leave out readings flagged 2", "--alternative", "keep every reading",
             "--rests-on", "the wiki page on flagged readings (not signed) and LOOK-001 against LOOK-002", "--look", "LOOK-002")
        tool("explore.py", "note", *E, "--by", me, "--kind", "missing", "--about", "the flagged-readings page",
             "--text", f"Seen while exploring: with every reading the gain is {gain_all}, with degraded readings out it is {gain}; one degraded reading is far off.",
             "--evidence", "receipts/LOOK-002.json")

        # the lead, the review, the end, the hand-over
        lead = {"summary": {"looks_true": f"In 2024 the second sensor seems to track the reference, with a gain of {gain:.4f} once degraded readings are left out.",
                            "how_strong": "Three looks at one year of one pair of sensors, with the flag screen chosen after the first look.",
                            "cannot_settle": "Whether the gain holds in 2025, which was set aside, or for any other pair of sensors."},
                "what_looks_true": f"With degraded readings left out, the second sensor looks as if it follows the reference with a gain of {gain:.4f} over 2024.",
                "how_it_was_found": "Read the wiki pages, fitted the gain with an intercept with and without the flag screen.",
                "evidence": ["LOOK-001", "LOOK-002", "LOOK-003"],
                "figures": [{"file": "figures/residual.svg", "shows": "what is left of the second sensor after its straight line on the reference, coloured by flag"}],
                "choices_that_would_change_it": [{"choice": "CHOICE-001", "how": f"keeping every reading gives {gain_all:.4f}"}],
                "choices_that_would_not": [], "pitfalls": ["a level difference is mostly the mounting offset (wiki page, not signed)"],
                "proposed_plan": {"question": "Over 2025, is the gain of the second sensor on the reference within five percent of one?",
                                  "quantity_estimated": "the gain, with an interval", "difference_that_matters": "five percent, proposed; nobody has stated one",
                                  "rule_sketch": "supported if the interval lies inside 0.95 to 1.05, refuted if wholly outside, otherwise inconclusive"}}
        lead_file = x / "lead.yaml"
        lead_file.write_text(yaml.safe_dump(lead, sort_keys=False))
        step("a lead is refused until whoever coordinates has named the reviewer, and the explorer cannot name one",
             "no reviewer is named" in tool("explore.py", "lead", *E, "--by", me, "--file", lead_file, expect=2)
             and "did part of this exploration" in tool("explore.py", "reviewer", *E, "--by", me, "--reviewer", reviewer, expect=2))
        tool("explore.py", "reviewer", *E, "--by", coordinator, "--reviewer", reviewer)
        bad = dict(lead, what_looks_true=lead["what_looks_true"].replace(f"{gain:.4f}", "1.2345"))
        lead_file.write_text(yaml.safe_dump(bad, sort_keys=False))
        step("a lead that quotes a number no look printed is refused", "1.2345" in tool("explore.py", "lead", *E, "--by", me, "--file", lead_file, expect=2))
        bad = dict(lead, what_looks_true=lead["what_looks_true"].replace("With degraded readings left out", "On the unflagged readings"))
        lead_file.write_text(yaml.safe_dump(bad, sort_keys=False))
        step("a lead that calls readings unflagged when their flag has a value is refused, with the words to use",
             "flag's value" in tool("explore.py", "lead", *E, "--by", me, "--file", lead_file, expect=2))
        lead_file.write_text(yaml.safe_dump(lead, sort_keys=False))
        tool("explore.py", "lead", *E, "--by", me, "--file", lead_file)
        recorded = json.loads((x / "lead.json").read_text())
        step("the lead says it is exploring and is not a finding", "not a finding" in (x / "lead.md").read_text() and recorded["tried"]["looks"] == 3)
        step("the lead shows the figure and the order of looks and choices: the one choice was written down after three looks",
             "](figures/residual.svg)" in (x / "lead.md").read_text() and recorded["order"]["choices"]["CHOICE-001"]["after_looks"] == 3
             and "Written down after LOOK-003" in (x / "lead.md").read_text())
        tool("explore.py", "correct", *E, "--by", me, "--old", "looks as if it follows the reference", "--new", "looks as if it rises and falls with the reference",
             "--why", "follows was too loose a word")
        step("a slip of wording is put right without a new version of the lead, and a correction that changes a number is refused",
             json.loads((x / "lead.json").read_text())["version"] == 1 and "Corrections of wording" in (x / "lead.md").read_text()
             and "never numbers" in tool("explore.py", "correct", *E, "--by", me, "--old", "over 2024", "--new", "over 2025", "--why", "x", expect=2))
        step("the exploration cannot end as a lead before the lead is reviewed, and its note cannot be resolved before it ends",
             "has not been reviewed" in tool("explore.py", "end", *E, "--by", me, "--outcome", "lead", "--summary", "x", expect=2)
             and "has not ended" in tool("explore.py", "resolve", *E, "--by", curator, "--note", "NOTE-001", "--disposition", "declined", "--comment", "x", expect=2))
        review = work / "review.md"
        review.write_text("# Review (exploring)\n\nChecked the log and both looks. One hole: one year only.\n")
        step("the agent that explored cannot review its own lead",
             "did part of this exploration" in tool("explore.py", "review", *E, "--by", me, "--verdict", "no-holes-found", "--file", review, expect=2))
        step("a review under a name nobody named as a reviewer before the lead existed is refused",
             "was not named as a reviewer" in tool("explore.py", "review", *E, "--by", "agent:review-fresh", "--verdict", "no-holes-found", "--file", review, expect=2))
        step("a logged look reproduces", "identical" in tool("explore.py", "recheck", *E, "--look", "LOOK-002"))
        lead_read = lambda: hashlib.sha256((x / "lead.json").read_bytes()).hexdigest()  # noqa: E731  (the lead the reviewer read)
        step("a review that does not say which lead the reviewer read is refused",
             "--read-lead" in tool("explore.py", "review", *E, "--by", reviewer, "--verdict", "holes-found", "--file", review, expect=2))
        loose = work / "review-loose.md"
        loose.write_text("# Review (exploring)\n\nThe gain clearly holds, in good agreement with the wiki. One hole: one year only.\n")
        said = tool("explore.py", "review", *E, "--by", reviewer, "--verdict", "holes-found", "--file", loose, "--read-lead", lead_read())
        step("a review that claims more than an exploration can show is recorded, and the overclaiming check names each phrase and its line",
             "overclaiming check (a warning, not a refusal): verdicts/REVIEW-001.md, line 3: `clearly`" in said and "`good agreement`" in said)
        tool("explore.py", "correct", *E, "--by", me, "--old", "over 2024", "--new", "over the whole of 2024", "--why", "to say the year was read whole")
        step("a correction made after the review undoes the review: the exploration does not end as a lead until the corrected lead is reviewed",
             "corrected after it was reviewed" in tool("explore.py", "end", *E, "--by", me, "--outcome", "lead", "--summary", "x", expect=2))
        tool("explore.py", "review", *E, "--by", reviewer, "--verdict", "holes-found", "--file", review, "--read-lead", lead_read())

        def waiting_now() -> dict:
            return json.loads(tool("waiting.py", "--workspace", work, "--json", answer=True))

        def waiting_for(what: str, path: str) -> list:
            return [i for g in waiting_now()["groups"] if g["path"] == path for i in g["items"] if i["what"] == what]

        asked = waiting_for("so-what-wanted", "explorations/EXPLORATION-A")
        step("what waits on a person (tools/waiting.py) lists the reviewed lead once, for a person's so what, with the lines of the "
             "comment on the tracking issue", len(asked) == 1 and asked[0]["who"] == "people" and f"lead: {lead_read()[:16]}" in asked[0]["next_step"]["do"])
        # the person's so what: is the reviewed lead worth confirming? An agent drafts the question; only a person answers
        step("the exploration cannot end as a lead before a person has said the reviewed lead is worth confirming",
             "worth confirming" in tool("explore.py", "end", *E, "--by", me, "--outcome", "lead", "--summary", "x", expect=2))
        question = work / "so-what-question.yaml"
        question.write_text(yaml.safe_dump({
            "what_the_lead_shows": f"Over 2024 the second sensor rises and falls with the reference with a gain of {gain:.4f} once degraded readings are left out.",
            "why_it_might_matter": "A gain this close to one would let the second sensor stand in for the reference where the reference is down.",
            "what_would_make_it_unremarkable": "If the two sensors are calibrated against each other, a gain near one is what calibration gives and says nothing new."}))
        tool("explore.py", "ask-so-what", *E, "--by", coordinator, "--file", question, "--read-lead", lead_read())
        step("an agent drafts the question a person is asked, and cannot record the answer under any name",
             "What would make it unremarkable" in (x / "so-what" / "QUESTION-001.md").read_text()
             and "a person's answer" in tool("explore.py", "so-what", *E, "--by", coordinator, "--answer", "worth-confirming", "--read-lead", lead_read(),
                                              "--local-practice", expect=2))
        person = "human:throwaway-placeholder"  # nobody: a name for a scratch folder, typed here and nowhere that is kept
        step("typed at a command line, a person's so what is refused unless it says it is practice: on GitHub it is a comment on the tracking issue",
             "--local-practice" in tool("explore.py", "so-what", *E, "--by", person, "--answer", "worth-confirming", "--read-lead", lead_read(), expect=2))
        tool("explore.py", "so-what", *E, "--by", person, "--answer", "try-instead", "--direction", "look at the low end of the record, where the degraded readings sit",
             "--read-lead", lead_read(), "--local-practice")
        step("try-instead sends the exploration back to exploring, with the person's direction as its next question",
             json.loads(tool("explore.py", "status", *E, answer=True))["next_question"].startswith("look at the low end"))
        step("the so what leaves the waiting list, and the direction waits there for an agent to pick it up",
             not waiting_for("so-what-wanted", "explorations/EXPLORATION-A")
             and len(waiting_for("try-instead-not-picked-up", "explorations/EXPLORATION-A")) == 1)
        tool("explore.py", "so-what", *E, "--by", person, "--answer", "worth-confirming", "--read-lead", lead_read(), "--local-practice")
        tool("explore.py", "end", *E, "--by", me, "--outcome", "lead", "--summary", "the gain looks close to one with degraded readings out")
        step("the agent that explored cannot make the hand-over",
             "did the exploring" in tool("explore.py", "hand-over", *E, "--by", me, "--study-id", "STUDY-A", expect=2))
        tool("explore.py", "hand-over", *E, "--by", coordinator, "--study-id", "STUDY-A", "--local-practice")
        step("the hand-over carries the person's so what and its standing",
             "**The so what.** worth-confirming, by human:throwaway-placeholder" in (x / "hand-over" / "request.md").read_text())
        hand = json.loads((x / "hand-over" / "hand-over.json").read_text())
        stub = yaml.safe_load((x / "hand-over" / "analysis-plan.stub.yaml").read_text())
        step("the hand-over carries the proposal of the fresh data byte for byte, and the plan stub names it",
             (x / "hand-over" / "fresh-data.yaml").read_bytes() == proposal.read_bytes()
             and stub["data"]["held_out"]["fresh_data"].endswith("hand-over/fresh-data.yaml"))
        study = studies / "STUDY-A"
        tool("sf.py", "start", "--study", study, "--id", "STUDY-A", "--question", hand["question"], "--request", x / "hand-over" / "request.md", "--by", coordinator)
        step("a study started from the hand-over keeps the exploration's figures, each bound by checksum, for the lock to show",
             (study / "exploration-figures" / "LOOK-003-residual.svg").read_bytes() == (x / "figures" / "residual.svg").read_bytes()
             and json.loads((study / "study-log.jsonl").read_text().splitlines()[0])["data"]["exploration_figures"][0]["caption"].startswith("a picture"))

        def plan(window: dict) -> None:
            (study / "analysis-plan.yaml").write_text(yaml.safe_dump({
                "study": "STUDY-A", "question": hand["question"],
                "data": {"working": "the 2024 record", "held_out": {"window": window, "pair": {"record": "two-sensor", "sensor": "second"}, "path": "data/record-2025.json",
                                                                 "fresh_data": stub["data"]["held_out"]["fresh_data"]}},
                "tests": {"held-out": {"fetch": ["{python}", "fetch.py"], "command": ["{python}", "confront.py"], "receipt": "receipts/held-out.json"}}}))

        plan({"start": "2025-01-01", "end": "2025-12-31"})
        step("a study started from the hand-over that holds out the set-aside year keeps the fence",
             "PASS" in tool("explore.py", "check-study", *E, "--study", study))
        plan({"start": "2024-01-01", "end": "2024-12-31"})
        step("a study that holds out the explored year is refused",
             "cannot be used to confirm" in tool("explore.py", "check-study", *E, "--study", study, expect=2))
        plan({"start": "2025-01-01", "end": "2025-12-31"})
        step("no role's commands include the lock or the signature, and the tool has no command that signs",
             "invalid choice" in tool("explore.py", "signature", *E, expect=2))

        # a look that proved useful becomes a method of the factory: here in a scratch copy of the definition, because the
        # repository keeps no runs. The promotion is a change to the factory, recorded with a prediction and validated.
        repo_copy = work / "factory-copy"
        for part in ("factory", "tools"):
            shutil.copytree(ROOT / part, repo_copy / part, ignore=shutil.ignore_patterns("__pycache__"))
        (repo_copy / "examples" / "stand-alone").mkdir(parents=True)
        shutil.copytree(HERE / "system-trial", repo_copy / "examples" / "stand-alone" / "system-trial")
        readme = work / "method-readme.md"
        readme.write_text("# gain-with-intercept\n\n**What it computes.** The gain of the second sensor on the reference by least squares with an "
                          "intercept, the intercept and the residual spread, with an optional screen on the flag.\n\n**On what inputs.** One JSON record "
                          "with `rows`, each holding `reference`, `sensor`, `flag` and `time`.\n\n**Known limits.** No uncertainty on the gain, "
                          "no handling of a step in the offset, and readings are taken as independent.\n")
        tool("explore.py", "promote", *E, "--by", me, "--look", "LOOK-002", "--name", "gain-with-intercept", "--readme", readme, "--methods", repo_copy / "methods")
        method = repo_copy / "methods" / "gain-with-intercept"
        kat = ran(["uv", "run", str(method / "known_answer_tests.py")])
        step("a look's script is promoted to a method, with the exploration's runs of it as known-answer cases, and its tests reproduce them",
             sorted(json.loads((method / "method.json").read_text())["cases"]) == ["LOOK-001", "LOOK-002"] and "PASS (2 of 2)" in kat)
        step("the promotion is a change to the factory: the validator refuses it until the change log records it with a prediction",
             "no record of the change log names" in tool("check_factory.py", repo_copy / "factory", expect=1))
        change = work / "studies" / "CHANGE-PROMOTE"
        tool("sf.py", "start", "--study", change, "--id", "CHANGE-PROMOTE", "--by", coordinator, "--question", "Does the promoted gain method reproduce its looks?")
        tool("sf.py", "log-change", "--study", change, "--by", coordinator, "--log", repo_copy / "factory" / "change-log.jsonl",
             "--factory", repo_copy / "factory", "--problem", "a look that proved useful is rewritten by hand in every study",
             "--change", "Promote methods/gain-with-intercept from EXPLORATION-A, LOOK-002", "--rationale", "tools grow as they are used",
             "--predicted", "its two known-answer cases reproduce, and a study that uses it runs them first")
        step("recorded with a prediction, the promoted method is valid", "check-factory: VALID" in tool("check_factory.py", repo_copy / "factory"))

        # after work: a draft for the queue, checked, and found again as a draft
        tool("explore.py", "curation-list", *E)
        (queue / "pages").mkdir(parents=True)
        draft = queue / "pages" / "one-degraded-reading-steers-the-gain.md"
        head = {"type": "pitfall", "title": "One degraded reading at the low end steers the gain of the two-sensor record",
                "description": "Seen while exploring the 2024 record.", "tags": ["flagged", "readings", "sensor", "gain", "degraded"],
                "generated": {"by": "stand-alone-run/no-model", "at": "2026-11-26T00:00:00Z"}, "status": "draft", "seen_while": "exploring",
                "drafted_from": {"exploration": "EXPLORATION-A", "notes": ["NOTE-001"], "by": curator},
                "sources": [{"id": "look", "resource": "explorations/EXPLORATION-A/receipts/LOOK-002.json", "title": "the look with the screen"}]}
        said = tool("explore.py", "contribution", *E)
        step("the contribution statement of the lead says who did each kind of work, the agents with the model they declared, and what the log cannot show",
             "| the so what | human:throwaway-placeholder (a person, by the name typed) | 2 |" in said and "| exploring | agent:analysis-a (an AI agent, the analysis role" in said
             and "What the logs cannot show" in said)
        who = json.loads((x / "contribution.json").read_text())["paragraph"]
        body = (f"\n# One degraded reading steers the gain\n\nSeen while exploring one year. With every reading the gain is {gain_all}; with degraded readings out it is {gain}.[^look]\n\n"
                f"**Who did what.** {who} The log cannot show thinking that left no event, and a model is declared, not proven.\n\n[^look]: the look\n")
        draft.write_text("---\n" + yaml.safe_dump(head, sort_keys=False) + "---\n" + body)
        step("a draft that bears on a wiki page without saying how is refused",
             "does not say how it relates" in tool("knowledge.py", "check-drafts", "--queue", queue, "--wiki", wiki, expect=2))
        head["relates_to"] = [{"concept": "flagged-readings.md", "relation": "extends", "why": "adds what one degraded reading did to the gain in 2024"}]
        draft.write_text("---\n" + yaml.safe_dump(head, sort_keys=False) + "---\n" + body)
        step("the draft passes the rules of the queue", "PASS" in tool("knowledge.py", "check-drafts", "--queue", queue, "--wiki", wiki))
        signed = dict(head, verified={"by": "human:someone", "at": "2026-11-26T00:00:00Z"})
        draft.write_text("---\n" + yaml.safe_dump(signed, sort_keys=False) + "---\n" + body)
        step("a draft marked as signed is refused", "carries a signature" in tool("knowledge.py", "check-drafts", "--queue", queue, "--wiki", wiki, expect=2))
        draft.write_text("---\n" + yaml.safe_dump(head, sort_keys=False) + "---\n" + body)
        tool("knowledge.py", "check-drafts", "--queue", queue, "--wiki", wiki)
        tool("explore.py", "resolve", *E, "--by", curator, "--note", "NOTE-001", "--disposition", "drafted", "--ref", "knowledge-queue/pages/" + draft.name)
        out = tool("knowledge.py", "about", "--question", "Does a degraded reading steer the gain of the two-sensor record?", "--wiki", wiki, "--drafts", queue)
        step("a second question finds the drafted page, marked as a draft and not signed", draft.name in out and "DRAFT IN THE QUEUE, NOT SIGNED" in out)
        status = json.loads(tool("explore.py", "status", *E, answer=True))
        step("the exploration is ended, handed over, and everything it wrote checks out",
             status["stage"] == "ended" and status["handed_over_to"] == "STUDY-A" and "PASS" in tool("explore.py", "check-log", *E))
        step("the study started from it stands at the plan stage, waiting for a real plan, with nothing locked or signed",
             json.loads(tool("sf.py", "status", "--study", study, answer=True))["stage"] in ("plan", "test")
             and not any(json.loads(ln)["kind"] in ("lock.recorded", "signature.recorded") for ln in (study / "study-log.jsonl").read_text().splitlines()))

        # measuring the work: a judge reads a packet of exactly what its scorer declares, and no model is asked here
        packet = work / "judging" / "review-finds-holes"
        said = tool("scorers.py", "packet", "--scorer", "review-finds-holes", "--exploration", x, "--out", packet)
        listed = json.loads((packet / "packet.json").read_text())
        step("a judging packet for the review of the lead holds the exploration's log up to the hand-over, the lead and the review, and says what it left out",
             {m["kind"] for m in listed["material"]} == {"exploration-log", "lead", "review-before-opening"} and (packet / "JUDGE.md").is_file()
             and any("after the hand-over" in q["why"] for q in listed["left_out"]) and "note.resolved" not in (packet / "material" / "exploration-log" / "exploration-log.jsonl").read_text())
        verdict = work / "judging" / "verdict.yaml"
        verdict.write_text("label: checked\nreasoning: Written by the example's script to show the refusal; no judge read the packet.\n")
        step("a verdict under a model the scorer does not declare is refused, so nothing is recorded: no judge has judged this run",
             "is not this scorer's" in tool("scorers.py", "record", "--packet", packet, "--verdict", verdict, "--by", "agent:judge-a", expect=2)
             and not (x / "judgements.jsonl").exists() and not (packet.parent / "judgements.jsonl").exists()
             and "`verdict.yaml`" in (packet / "JUDGE.md").read_text())

        # the confirming loop, as far as a tool can take it: a study through its tests, stopping before the lock
        trial = studies / "STUDY-B"
        trial.mkdir()
        template = HERE / "system-trial"
        trial_plan = yaml.safe_load((template / "analysis-plan.yaml").read_text())
        trial_plan["study"] = "STUDY-B"
        trial_plan["roots"] = {k: str((template / v).resolve()) for k, v in trial_plan["roots"].items()}  # the copy stands elsewhere
        # a figure for the people at the lock to look at: the rehearsal case drawn by the skill's own plotting script
        trial_plan["rehearsals"][0]["steps"].append(["{python}", plot, "{study}/rehearsal/rehearsal_case.json", "--rows", "satellite.rows", "--x", "time",
                                                     "--y", "wse_m", "--color", "reach_q", "--out", "{study}/figures/rehearsal-case.svg"])
        trial_plan["rehearsals"][0]["figures"] = [{"file": "figures/rehearsal-case.svg",
                                                   "shows": "the rehearsal case's satellite elevations through its year, coloured by quality flag"}]
        (trial / "analysis-plan.yaml").write_text(yaml.safe_dump(trial_plan, sort_keys=False))
        S = ("--study", trial)
        tool("sf.py", "start", *S, "--id", "STUDY-B", "--question", trial_plan["question"], "--by", coordinator)
        fit.write_text(yaml.safe_dump({"answer_is": "exact", "data_at_hand": "yes", "mostly": "computation",
                                       "person_must_supply": "nothing but the lock and the reading of the sealed answer",
                                       "verdict": "good-fit", "why": "a system trial on a synthetic case: the answer is a number the sealed truth settles",
                                       "taste_needed": "a person who looks at the rehearsal's figure before the lock"}))
        tool("sf.py", "fit", *S, "--by", coordinator, "--file", fit)
        step("a second study, a system trial on a synthetic record, is started and its plan is complete",
             "the analysis plan is complete" in tool("sf.py", "check-plan", *S))
        step("its opening is refused before the lock",
             "REFUSED" in tool("sf.py", "open-held-out", *S, "--by", coordinator, expect=2))
        step("the known-answer tests pass: the method meets every criterion the plan sets, on synthetic records with the truth put in",
             "pass" in tool("sf.py", "test", "known-answers", *S, "--by", me) and (trial / "receipts" / "known-answers.json").is_file())
        tool("sf.py", "test", "working-data", *S, "--by", me)
        tool("sf.py", "rehearse", *S, "--id", "opening-path", "--by", me)
        trial_status = json.loads(tool("sf.py", "status", *S, answer=True))
        step("status says which factory this is (the definition's checksum and version) and shows the models: declared by the definition, and recorded in the log",
             len(trial_status["definition"]["sha256"]) == 64 and trial_status["definition"]["this_factorys_own"]
             and set(trial_status["models"]["declared_by_the_definition"]) == {"analysis", "coordinating", "curating", "review"}
             and trial_status["models"]["recorded_in_the_log"] == {coordinator: [MODEL], me: [MODEL]}
             and len(trial_status["models"]["remarks"]) == 2)
        plan_packet = work / "judging" / "plan-is-clear"
        tool("scorers.py", "packet", "--scorer", "plan-is-clear", "--study", trial, "--out", plan_packet)
        step("a judging packet for the plan holds the plan, the receipts of its tests and the method's code, names no place outside itself, "
             "and nothing was opened to make it",
             {m["kind"] for m in json.loads((plan_packet / "packet.json").read_text())["material"]} == {"plan", "known-answer-tests", "code"}
             and str(work) not in (plan_packet / "packet.json").read_text() and str(ROOT) not in (plan_packet / "packet.json").read_text()
             and not json.loads((plan_packet / "packet.json").read_text())["run"]["held_out_data_opened"])
        step("the design set of blind cases can be listed, and the acceptance set gives nothing without its keeper's seed",
             "the idea is false" in tool("benchmark.py", "cases", "--suite", ROOT / "factory" / "benchmarks" / "built-in-gain")
             and "never invents one" in tool("benchmark.py", "cases", "--suite", ROOT / "factory" / "benchmarks" / "acceptance", expect=2))
        step("with its tests and its rehearsal passed the study stands at the lock, which is a person's act: no tool and no agent takes it further",
             trial_status["stage"] == "lock" and "PASS" not in tool("sf.py", "lock", *S, "--by", me, "--evidence", "https://example.invalid/not-a-person", expect=2)
             and not any(json.loads(ln)["kind"] in ("lock.recorded", "held-out.opened", "signature.recorded") for ln in (trial / "study-log.jsonl").read_text().splitlines()))

        # The lock itself. In a real study it is a pull request: an agent writes the request, and people approve and
        # merge it on the protected branch of the repository where the study lives (factory/harnesses/github). This
        # example runs in a scratch folder that is no repository and has no branch to merge into, and this repository
        # keeps no runs, so it shows the request and then uses practice mode, which says of itself that it is practice.
        tool("sf.py", "request-lock", *S, "--by", coordinator)
        asked = (trial / "lock-request" / "EVIDENCE.md").read_text()
        step("the lock request shows the fit note from intake", "**good-fit**, noted by agent:coordinating-a" in asked)
        step("the lock request shows the rehearsal's figure as a picture with its caption, asks the person to look at it, and binds it",
             "## The figures: look at each one yourself" in asked and "](../figures/rehearsal-case.svg)" in asked and "Look at each figure yourself" in asked
             and "figures/rehearsal-case.svg" in json.loads((trial / "lock-request" / "manifest.json").read_text())["figures"])
        step("an agent can write the lock request: an evidence summary in plain words and a manifest of checksums, with nothing locked",
             "## The question" in asked and "## The fresh data that will check the idea, and why it was chosen" in asked
             and "a blind test case that the tool makes and seals at the opening" in asked
             and json.loads((trial / "lock-request" / "manifest.json").read_text())["definition"]["sha256"] == trial_status["definition"]["sha256"]
             and "requested" in str(json.loads(tool("sf.py", "status", *S, answer=True))["acts"]["lock"])
             and not any(json.loads(ln)["kind"] == "lock.recorded" for ln in (trial / "study-log.jsonl").read_text().splitlines()))
        waits = waiting_now()
        step("the lock request waits on people, and the drafted page waits on the steward, each once, oldest first, in plain words too",
             len(waiting_for("lock-request-not-merged", "studies/STUDY-B")) == 1
             and len(waiting_for("draft-awaiting-the-steward", "explorations/EXPLORATION-A")) == 1
             and "lock-request/EVIDENCE.md" in tool("waiting.py", "--workspace", work, answer=True)
             and [g["path"] for g in waits["groups"]][0] == "explorations/EXPLORATION-A")
        (work / "waiting.md").write_text(tool("waiting.py", "--workspace", work, answer=True))
        step("a lock typed at a command line, under a person's name and with a link, is refused unless it says it is practice",
             "the lock is a pull request" in tool("sf.py", "lock", *S, "--by", person, "--evidence", "https://example.invalid/not-a-review", expect=2))
        tool("sf.py", "lock", *S, "--by", person, "--evidence", "https://example.invalid/not-a-review", "--local-practice")
        step("once the lock is recorded the request leaves the waiting list", not waiting_for("lock-request-not-merged", "studies/STUDY-B"))
        credit = tool("sf.py", "contribution", *S)
        step("the study's contribution statement credits the practice lock to the name typed, the tests to the analysis agent with its declared model, "
             "and lists the steps with no event yet",
             "| the lock | human:throwaway-placeholder (a person, by the name typed) | 1 |" in credit
             and f"| planning and testing the method | agent:analysis-a (an AI agent, the analysis role, model {MODEL} as declared) | 3 |" in credit
             and "Steps with no event yet:" in credit and "the signature" in credit.split("Steps with no event yet:")[1].split("\n")[0])
        practice = json.loads(tool("sf.py", "status", *S, answer=True))
        step("a practice lock says so in the study's status, and the held-out data is not opened unless the caller says practice too",
             practice["acts"]["practice"] is True and "cannot close as a signed finding" in practice["acts"]["lock"]["note"]
             and "practice lock" in tool("sf.py", "open-held-out", *S, "--by", coordinator, expect=2)
             and not any(json.loads(ln)["kind"] == "opening.started" for ln in (trial / "study-log.jsonl").read_text().splitlines()))
        # The three standings of an act. This example can show the first only: `merge found, people not verified` needs a
        # merge in a repository, and `verified` needs the platform to be asked, and a scratch folder has neither.
        checked = json.loads(tool("sf.py", "verify-acts", *S, "--by", coordinator, answer=True))
        step("the status names the three standings an act can have and gives this lock the first, practice; asked to verify it, the tool "
             "says a typed lock has nothing to verify and stays practice",
             practice["acts"]["standings"].startswith("each act has one of three standings: practice; merge found, people not verified; verified.")
             and practice["acts"]["lock"]["standing"] == "practice" and checked["acts"]["lock"]["standing"] == "practice"
             and "nothing to verify" in checked["acts"]["lock"]["said"] and checked["acts"]["signature"]["standing"] is None)
        standings_shown = f"{practice['acts']['standings'].split('.')[0]}. The lock of STUDY-B: {practice['acts']['lock']['standing']}."

        # The factory updated: a throwaway pair of git repositories, the science factory and a study repository copied from
        # it, as docs/FIRST-STUDY.md sets one up. Upstream then changes an agent's file; the update keeps the study
        # repository's own edits, moves the pin, and writes the pull request's description.
        pair = work / "update-pair"
        upstream, mine = pair / "science-factory", pair / "my-science"

        def git_in(repo: Path, *words) -> str:
            return ran(["git", "-C", str(repo), "-c", "user.name=stand-alone", "-c", "user.email=stand-alone@example.invalid",
                        "-c", "commit.gpgsign=false", *words], answer=True)
        for repo in (upstream, mine):
            for part in ("factory", "tools", "methods"):
                shutil.copytree(ROOT / part, repo / part, ignore=shutil.ignore_patterns("__pycache__"))
            shutil.copytree(HERE / "system-trial", repo / "examples" / "stand-alone" / "system-trial")
            git_in(repo, "init", "-q", "-b", "main")
        git_in(upstream, "add", "-A")
        git_in(upstream, "commit", "-q", "-m", "the science factory")
        version = yaml.safe_load((ROOT / "factory" / "factory.yaml").read_text())["version"]
        fy = mine / "factory" / "factory.yaml"
        fy.write_text(fy.read_text().replace("example-org/example-studies", "owner/my-science").replace(f"version: {version} ", f"version: {version}+local.1 ", 1))
        here_tools = mine / "tools"
        ran(["uv", "run", str(here_tools / "sf.py"), "log-change", "--study", str(mine / "studies" / "SETUP"), "--by", person,
             "--log", str(mine / "factory" / "change-log.jsonl"), "--factory", str(mine / "factory"), "--problem", "the definition names the example repository",
             "--change", f"repository: under both acts names owner/my-science, as version {version}+local.1",
             "--rationale", "the acts are verified on the repository where the studies live", "--predicted", "check_factory.py says VALID"])
        ran(["uv", "run", str(here_tools / "factory_update.py"), "pin", "--repo", str(mine), "--source", str(upstream)])
        git_in(mine, "add", "-A")
        git_in(mine, "commit", "-q", "-m", "the factory, copied, named and pinned")
        review_file = upstream / "factory" / "agents" / "review" / "agent.md"
        review_file.write_text(review_file.read_text() + "\nRead the request before the plan.\n")
        ufy = upstream / "factory" / "factory.yaml"
        ufy.write_text(ufy.read_text().replace(f"version: {version} ", "version: 99.0.0 ", 1))
        ran(["uv", "run", str(upstream / "tools" / "sf.py"), "log-change", "--study", str(pair / "CHANGE-99"), "--by", coordinator, "--model", MODEL,
             "--log", str(upstream / "factory" / "change-log.jsonl"), "--factory", str(upstream / "factory"),
             "--problem", "the review agent reads the plan before the request", "--change", "Definition 99.0.0: the review agent reads the request first.",
             "--rationale", "a review starts from what was asked", "--predicted", "check_factory.py says VALID"])
        git_in(upstream, "add", "-A")
        git_in(upstream, "commit", "-q", "-m", "upstream 99.0.0")
        status = json.loads(ran(["uv", "run", str(here_tools / "factory_update.py"), "status", "--repo", str(mine), "--source", str(upstream), "--json"], answer=True))
        step("the study repository's pin sees that the science factory has moved, and that the update keeps the repository's own name",
             status["moved"] and status["update_needed"] and not status["refused"]
             and {"field": "procedure.acts_by_people.lock.repository", "value": '"owner/my-science"'} in status["factory"]["fields_kept_here"])
        body = pair / "PULL_REQUEST.md"
        ran(["uv", "run", str(here_tools / "factory_update.py"), "update", "--repo", str(mine), "--source", str(upstream), "--by", person,
             "--body-out", str(body), "--git-identity", "stand-alone <stand-alone@example.invalid>"])
        merged = yaml.safe_load(fy.read_text())
        step("the update is written on a branch: upstream's change in, the repository's name kept, a local version, the pin moved, and a "
             "pull request description with the summary of the change and the change-log record between the two versions",
             git_in(mine, "rev-parse", "--abbrev-ref", "HEAD").strip() == "factory-update/99.0.0"
             and "Read the request before the plan." in (mine / "factory" / "agents" / "review" / "agent.md").read_text()
             and merged["procedure"]["acts_by_people"]["lock"]["repository"] == "owner/my-science" and merged["version"] == "99.0.0+local.1"
             and yaml.safe_load((mine / "factory-pin.yaml").read_text())["version"] == "99.0.0"
             and "Definition 99.0.0: the review agent reads the request first." in body.read_text() and "**valid**" in body.read_text()
             and "check-factory: VALID" in ran(["uv", "run", str(here_tools / "check_factory.py")], answer=True))

        # Data described as STAC, a Parquet look inside the fence, and the shared registry of openings: a synthetic gauge
        # record in two Parquet files, 2024 to explore and 2025 kept unopened, in a folder the exploration is not given
        gauge, held = work / "gauge-data", work / "gauge-held"
        gauge.mkdir()
        held.mkdir()
        ran(["uv", "run", str(HERE / "make_parquet.py"), "2024", str(gauge / "2024.parquet")])
        ran(["uv", "run", str(HERE / "make_parquet.py"), "2025", str(held / "2025.parquet")])
        said = tool("fresh_data.py", "describe", "--files", gauge / "2024.parquet", held / "2025.parquet", "--date-column", "day",
                    "--lat-column", "lat", "--lon-column", "lon", "--subject", "record=gauge", "--what", "a synthetic river gauge, one file a year",
                    "--stac", work / "gauge-stac")
        item = json.loads((work / "gauge-stac" / "items" / "2025.json").read_text())
        step("the data is described as STAC from its date and position columns only: a Collection, one Item for each file with its start "
             "and end, its place, and its file by checksum and size, validated against the schemas shipped with pystac",
             "STAC description written" in said and "no schema was fetched" in said and item["geometry"]["type"] == "Point"
             and item["properties"]["start_datetime"] == "2025-01-01T00:00:00Z"
             and item["assets"]["data"]["file:checksum"] == "1220" + hashlib.sha256((held / "2025.parquet").read_bytes()).hexdigest()
             and "stage" not in (work / "gauge-stac" / "items" / "2025.json").read_text())
        tool("openings.py", "init", "--registry", work / "registry")
        xg = work / "explorations" / "EXPLORATION-G"
        said = tool("fresh_data.py", "propose", "--metadata", work / "gauge-stac" / "collection.json", "--kind", "later-period", "--from", "2025-01-01",
                    "--what", "the whole of 2025 at the gauge", "--why", "only 2024 has been looked at", "--unfair", "a new gauge datum in 2025",
                    "--by", me, "--studies", studies, "--registry", work / "registry", "--out", xg / "fresh-data.yaml")
        step("the fresh data is proposed as a STAC query, its Item bound by ID and checksum, after asking the shared registry of openings",
             "As a STAC query" in said and "2025 (" in said and "records no opening" in (xg / "fresh-data.yaml").read_text())
        tool("explore.py", "start", "--exploration", xg, "--id", "EXPLORATION-G", "--by", me, "--question", "How fast does the gauge rise?",
             "--request", request, "--subject", "record=gauge", "--how", "a later period", "--set-aside-window", "2025-01-01:",
             "--why", "the year after the one explored", "--working", "2024 at the gauge", "--working-data", gauge,
             "--fresh-data", xg / "fresh-data.yaml")
        tool("explore.py", "known", "--exploration", xg, "--by", me, "--wiki", wiki)
        shutil.copyfile(HERE / "looks" / "duck_slope.py", xg / "looks" / "duck_slope.py")
        said = tool("explore.py", "look", "--exploration", xg, "--by", me, "--why", "the slope of the stage on the day",
                    "--", "uv", "run", "looks/duck_slope.py", gauge / "2024.parquet")
        receipt = json.loads((xg / "receipts" / "LOOK-001.json").read_text())
        step("a look uses DuckDB over Parquet working data inside the fence: the fence read every row's date first, and DuckDB in the "
             "look could not read a remote file", "slope of the stage per day: 0.0100" in said and "a remote file: refused" in said
             and receipt["ran_in"]["parquet_read_by_the_fence"] and list(receipt["ran_in"]["parquet_read_by_the_fence"].values())[0]["rows"] == 365)
        shutil.copyfile(held / "2025.parquet", xg / "looks" / "copy.parquet")
        step("a copy of the set-aside Item's file is refused, by its checksum and by its dates",
             "the file of the set-aside Item 2025" in tool("explore.py", "look", "--exploration", xg, "--by", me, "--why", "2025",
                                                           "--", "uv", "run", "looks/duck_slope.py", "looks/copy.parquet", expect=2))
        (xg / "looks" / "copy.parquet").unlink()
        # A marimo notebook as a look; then a short session on it, ended as a person would end it. (Its page is not exported here:
        # marimo runs an export's cells in a child process, where DuckDB cannot start inside the kernel fence. The self-test
        # of tools/explore.py exports the page of a notebook that does not use DuckDB.)
        shutil.copyfile(HERE / "looks" / "gauge_nb.py", xg / "looks" / "gauge_nb.py")
        said = tool("explore.py", "look", "--exploration", xg, "--by", me, "--why", "the slope of the stage on the day, in a notebook",
                    "--", "uv", "run", "looks/gauge_nb.py", gauge / "2024.parquet")
        receipt = json.loads((xg / "receipts" / "LOOK-002.json").read_text())
        step("a marimo notebook is a look: it runs in the fence top to bottom as a script, with DuckDB over the Parquet working data, and "
             "prints the slope", "slope of the stage per day: 0.0100" in said and receipt["ran_in"]["notebook"]["kind"] == "marimo")
        session = subprocess.Popen(["uv", "run", str(ROOT / "tools" / "explore.py"), "session", "--exploration", str(xg), "--by", person,
                                    "--notebook", "looks/gauge_nb.py", "--data", str(gauge / "2024.parquet"), "--idle-minutes", "5"],
                                   cwd=ROOT, env=QUIET_ENV, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        told = []
        threading.Thread(target=lambda: [told.append(line) for line in session.stdout], daemon=True).start()
        try:
            for _ in range(600):
                folder = re.search(r"Its folder is (\S+)\.\n", "".join(told))
                if folder or session.poll() is not None:
                    break
                time.sleep(0.25)
            if folder:  # an editor saves the notebook once, as a person working in the browser would
                nb = Path(folder.group(1)) / "looks" / "gauge_nb.py"
                nb.write_text(nb.read_text().replace('print(f"slope of the stage per day: {slope:.4f} from {n} days")',
                                                      'print(f"slope of the stage per day: {slope:.4f} from {n} days, in metres")'))
                for _ in range(80):
                    if '"session.saved"' in (xg / "exploration-log.jsonl").read_text():
                        break
                    time.sleep(0.25)
            session.send_signal(signal.SIGTERM)  # Ctrl-C, for a script
            session.wait(90)
        finally:
            if session.poll() is None:
                session.kill()
        kinds = [json.loads(line)["kind"] for line in (xg / "exploration-log.jsonl").read_text().splitlines()]
        step("a notebook session opens marimo's editor inside the fence on the declared Parquet file, and the log holds its start, the "
             "one saved version and its end", session.returncode == 0 and kinds[-3:] == ["session.started", "session.saved", "session.ended"]
             and (xg / "sessions" / "SESSION-001" / "v001.py").is_file() and "in metres" in (xg / "looks" / "gauge_nb.py").read_text())
        said = tool("explore.py", "look", "--exploration", xg, "--by", me, "--why", "the session's final notebook, run once as a look",
                    "--", "uv", "run", "looks/gauge_nb.py", gauge / "2024.parquet")
        status = json.loads(tool("explore.py", "status", "--exploration", xg, answer=True))
        step("nothing a session showed is quotable until its final notebook runs as a look; status says which look did",
             "from 365 days, in metres" in said and status["sessions"][0]["run_as_a_look"] == "LOOK-003" and "never a cell run" in status["sessions_say"])
        step("the registry answers in plain words, as the lock request and the opening will ask it",
             "records no opening of these Items" in tool("openings.py", "check", "--registry", work / "registry", "--proposal", xg / "fresh-data.yaml"))

        # What the workspace did, counted: a report in Markdown and as one page of HTML
        tool("report.py", "--workspace", work, "--out", work / "report.md", "--html", work / "report.html")
        said = (work / "report.md").read_text()
        counted = json.loads(tool("report.py", "--workspace", work, "--json", answer=True))
        step("the report counts the studies and the exploration by stage and outcome, the time at each stage and waiting on a person, "
             "the models recorded, says no cost was recorded, and first says why it scores nothing",
             said.splitlines()[2] == counted["why_no_score"] and "## Time at each stage" in said and "## Waiting on a person" in said
             and "none was recorded" in said and counted["totals"]["by_outcome"]["lead"] == 1
             and {x["id"] for x in counted["studies"]} >= {"STUDY-A", "STUDY-B"} and MODEL in json.dumps(counted["totals"]["models_by_stage"])
             and (work / "report.html").read_text().startswith("<!DOCTYPE html>") and "<script" not in (work / "report.html").read_text())
    except AssertionError as err:
        print(f"FAIL at step {len(steps) + (0 if steps and not steps[-1][1] else 1)}: {err}")
        print(f"stand-alone example: FAIL ({sum(1 for _, good in steps if good)} steps passed)")
        return 1
    finally:
        if a.remove:
            shutil.rmtree(work, ignore_errors=True)
    if not a.remove:
        print(f"""What this run made is in {work}, outside the repository. Nothing in it is kept by the repository; delete it when you have looked.
  explorations/EXPLORATION-A/   an exploration: exploration-log.jsonl (every step, chained by hash), set-aside.json (what
                                was not looked at), looks/ and receipts/ (each look's script and its record), figures/,
                                notes/, lead.md (what was found, with the order of looks and choices), review/ and
                                verdicts/, hand-over/ (the request a study starts from)
  studies/STUDY-A/              a study started from that hand-over: study-log.jsonl and a plan, at the plan stage
  studies/STUDY-B/              a study taken through its tests: analysis-plan.yaml, study-log.jsonl, receipts/ (the
                                known-answer tests, the working data, the rehearsal), lock-request/ (what a person
                                would be asked to approve), and a practice lock, typed here because a scratch folder
                                has no protected branch
                                {standings_shown}
                                The second standing is what git on a clone can show of a merged request; the third is
                                what the platform answers when `sf.py verify-acts` asks it. Neither can be shown here.
  studies/openings.jsonl        the record of what has been set aside and opened, beside the studies
  knowledge-queue/              a drafted knowledge page waiting for a person, with the queue's index
  waiting.md                    what waited on a person before the practice lock (tools/waiting.py), in plain words
  judging/                      two judging packets (JUDGE.md, packet.json, material/): what a model judge would be given
                                to judge the review of the lead and the clarity of the plan; no model was asked
  report.md, report.html        what the workspace did, counted by tools/report.py: by stage and outcome, time, models
  update-pair/                  a throwaway science factory and a study repository copied from it, pinned, then updated on
                                a branch by tools/factory_update.py; PULL_REQUEST.md is the description it wrote
  gauge-stac/, registry/        a STAC description of a synthetic gauge record (Parquet), and a shared registry of openings
  explorations/EXPLORATION-G/   an exploration set aside from that description, with a DuckDB look over Parquet, a marimo
                                notebook look with its page in figures/, and a notebook session's saved version in sessions/
  data/, request.md             the synthetic record and the request the exploration began with""")
    print(f"stand-alone example: PASS ({len(steps)} of {len(steps)} steps)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
