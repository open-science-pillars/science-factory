# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""Run the exploring loop and the knowledge loop end to end on the stand-alone example, and check each step.

Nothing here needs another repository or the network: the record is
examples/stand-alone/record-2024.json (synthetic, with a known answer) and
the knowledge base is the wiki in openwiki/. The work is done in a scratch
folder that is removed afterwards.

What this is and is not. It is the tools, driven from the command line the
way a role would drive them, with each step checked. No assistant runs in
it and no language model: it shows that the loops hold together and that
the refusals refuse, and the checks workflow runs it. What assistants do
with the same tools is the demo in examples/baton-rouge.

  uv run examples/stand-alone/run.py            run and check
  uv run examples/stand-alone/run.py --keep     keep the scratch folder and print where it is
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
GAIN_PUT_IN, CLOSE_ENOUGH = 1.03, 0.02   # the answer the record was made with (make_record.py), and how near counts


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()
    work = Path(tempfile.mkdtemp(prefix="stand-alone-")).resolve()
    steps = []

    def ran(command: list, expect: int = 0, answer: bool = False) -> str:
        """Run one command. What it prints and what it says on standard error are both returned, for reading a refusal;
        with `answer` only what it prints is returned, because that alone is the tool's answer: the launcher may add a
        warning of its own on standard error (uv does, for a deprecated setting), and a warning is not part of the answer."""
        done = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if done.returncode != expect:
            raise AssertionError(f"`{' '.join(str(x) for x in command[:6])} ...` ended {done.returncode}, expected {expect}:\n{(done.stdout + done.stderr)[-800:]}")
        return done.stdout if answer else done.stdout + done.stderr

    def tool(name: str, *args, expect: int = 0, answer: bool = False) -> str:
        return ran(["uv", "run", str(ROOT / "tools" / name), *[str(x) for x in args]], expect, answer)

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

        # before work: what is known, from the wiki in openwiki/, and only that
        out = tool("knowledge.py", "about", "--question", "How closely does the second sensor follow the reference?", "--wiki", wiki)
        step("the wiki answers with the pages that bear on the question, none of them signed",
             "compare-changes-not-levels.md" in out and "flagged-readings.md" in out and "NOT SIGNED" in out and "SIGNED by" not in out)

        # data is set aside first
        step("a start that sets nothing aside is refused",
             "REFUSED" in tool("explore.py", "start", *E, "--id", "EXPLORATION-A", "--by", me, "--question", "How closely does the second sensor follow the reference?",
                               "--request", request, "--subject", "record=two-sensor,sensor=second", "--how", "a later period", "--why", "x", expect=2))
        tool("explore.py", "start", *E, "--id", "EXPLORATION-A", "--by", me, "--question", "How closely does the second sensor follow the reference?",
             "--request", request, "--subject", "record=two-sensor,sensor=second", "--how", "a later period", "--set-aside-window", "2025-01-01:2025-12-31",
             "--why", "the following year: the request says only 2024 has been looked at", "--working", "the 2024 record", "--working-window", "2024-01-01:2024-12-31",
             "--boundary-from", wiki / "the-two-sensor-record.md")
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

        # looks, the fence, choices, a note
        out_all = tool("explore.py", *look, "the gain with every reading", "--", "uv", "run", gain_script, data)
        out_screened = tool("explore.py", *look, "the gain with degraded readings left out", "--", "uv", "run", gain_script, data, "--exclude-flag-at-or-above", "2")
        gain_all = float(re.search(r"gain (\d+\.\d+)", out_all).group(1))
        gain = float(re.search(r"gain (\d+\.\d+)", out_screened).group(1))
        step(f"the exploring comes close to the answer the record was made with (found {gain}, put in {GAIN_PUT_IN})", abs(gain - GAIN_PUT_IN) <= CLOSE_ENOUGH)
        step("without the screen the gain is further from it, as the wiki page warns", abs(gain_all - GAIN_PUT_IN) > abs(gain - GAIN_PUT_IN))
        later = work / "scratch" / "record-2025.json"
        later.parent.mkdir()
        subprocess.run(["uv", "run", str(HERE / "make_record.py"), "--year", "2025", "--out", str(later)], check=True, capture_output=True)
        step("a look that names the set-aside year is refused, and the refusal is logged",
             "set aside" in tool("explore.py", *look, "peek at the next year", "--", "uv", "run", gain_script, later, expect=2)
             and json.loads(x.joinpath("exploration-log.jsonl").read_text().splitlines()[-1])["kind"] == "look.refused")
        shutil.rmtree(later.parent)
        plot = str(ROOT / "skills" / "explore-a-record" / "scripts" / "plot_xy.py")
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
        lead = {"what_looks_true": f"With degraded readings left out, the second sensor looks as if it follows the reference with a gain of {gain:.4f} over 2024.",
                "how_it_was_found": "Read the wiki pages, fitted the gain with an intercept with and without the flag screen.",
                "evidence": ["LOOK-001", "LOOK-002", "LOOK-003"],
                "figures": [{"file": "figures/residual.svg", "shows": "what is left of the second sensor after its straight line on the reference, coloured by flag"}],
                "choices_that_would_change_it": [{"choice": "CHOICE-001", "how": f"keeping every reading gives {gain_all:.4f}"}],
                "choices_that_would_not": [], "pitfalls": ["a level difference is mostly the mounting offset (wiki page, not signed)"],
                "proposed_plan": {"question": "Over 2025, is the gain of the second sensor on the reference within five percent of one?",
                                  "quantity_estimated": "the gain, with an interval", "difference_that_matters": "five percent, proposed; nobody has stated one",
                                  "rule_sketch": "supported if the interval lies inside 0.95 to 1.05, refuted if wholly outside, otherwise inconclusive"}}
        lead_file = x / "lead.yaml"
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
        step("the assistant that explored cannot review its own lead",
             "did part of this exploration" in tool("explore.py", "review", *E, "--by", me, "--verdict", "no-holes-found", "--file", review, expect=2))
        step("a logged look reproduces", "identical" in tool("explore.py", "recheck", *E, "--look", "LOOK-002"))
        tool("explore.py", "review", *E, "--by", reviewer, "--verdict", "holes-found", "--file", review)
        tool("explore.py", "end", *E, "--by", me, "--outcome", "lead", "--summary", "the gain looks close to one with degraded readings out")
        step("the assistant that explored cannot make the hand-over",
             "did the exploring" in tool("explore.py", "hand-over", *E, "--by", me, "--study-id", "STUDY-A", expect=2))
        tool("explore.py", "hand-over", *E, "--by", coordinator, "--study-id", "STUDY-A")
        hand = json.loads((x / "hand-over" / "hand-over.json").read_text())
        study = studies / "STUDY-A"
        tool("sf.py", "start", "--study", study, "--id", "STUDY-A", "--question", hand["question"], "--request", x / "hand-over" / "request.md", "--by", coordinator)

        def plan(window: dict) -> None:
            (study / "analysis-plan.yaml").write_text(yaml.safe_dump({
                "study": "STUDY-A", "question": hand["question"],
                "data": {"working": "the 2024 record", "held_out": {"window": window, "pair": {"record": "two-sensor", "sensor": "second"}, "path": "data/record-2025.json"}},
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

        # after work: a draft for the queue, checked, and found again as a draft
        tool("explore.py", "curation-list", *E)
        (queue / "pages").mkdir(parents=True)
        draft = queue / "pages" / "one-degraded-reading-steers-the-gain.md"
        head = {"type": "pitfall", "title": "One degraded reading at the low end steers the gain of the two-sensor record",
                "description": "Seen while exploring the 2024 record.", "tags": ["flagged", "readings", "sensor", "gain", "degraded"],
                "generated": {"by": "stand-alone-run/no-model", "at": "2026-11-26T00:00:00Z"}, "status": "draft", "seen_while": "exploring",
                "drafted_from": {"exploration": "EXPLORATION-A", "notes": ["NOTE-001"], "by": curator},
                "sources": [{"id": "look", "resource": "explorations/EXPLORATION-A/receipts/LOOK-002.json", "title": "the look with the screen"}]}
        body = f"\n# One degraded reading steers the gain\n\nSeen while exploring one year. With every reading the gain is {gain_all}; with degraded readings out it is {gain}.[^look]\n\n[^look]: the look\n"
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
    except AssertionError as err:
        print(f"FAIL at step {len(steps) + (0 if steps and not steps[-1][1] else 1)}: {err}")
        print(f"stand-alone example: FAIL ({sum(1 for _, good in steps if good)} steps passed)")
        return 1
    finally:
        if a.keep:
            print(f"kept: {work}")
        else:
            shutil.rmtree(work, ignore_errors=True)
    print(f"stand-alone example: PASS ({len(steps)} of {len(steps)} steps)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
