#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""system_trial: the system trial of the factory, and the blind test of the
system.

A science factory can be checked the way a testbed is checked out before
the flight article arrives: run the whole thing on a test case whose answer
is known, with the answer sealed from everyone until the opening is over.

  working-data  the system trial's working data: a known-answer test case
                with a published seed (seed 2, a gain of 1.00), run through
                the same handling, so the study touches no real record at
                all. Only the data is written; the method is never given
                what was put in.
  seal          the access gate's fetch for a system trial: generate a
                known-answer test case from operating-system entropy and
                write it as two files. The data (--out) is what the locked
                analysis is given, and it holds no trace of what was put
                in. The answer (--answer) is a file the analysis is never
                passed; the data carries the answer file's checksum, and
                the study log carries the data's, so neither can be changed
                afterwards without `verdict` refusing. The gain put in is
                1.00 with probability one half and 0.90 or 1.10 otherwise,
                so nobody, person or assistant, knows whether the idea is
                true in it. It is a seal by procedure, and that is a
                stated limit: the answer file sits inside the study. The
                study tool passes it to no command, but nothing in the tool
                stops the locked analysis from opening a file in its own
                study, and reading it before the verdict is cheating that
                the study log cannot see. What stands against it is that
                the code is read at the lock by the people who lock it,
                and bound by checksum: an analysis that opened the answer
                would have to say so in code they read.
                --harness  the blind test harness names the seed and the
                gain (in BLIND_TEST_SEAL, as seed:gain). The flag has to
                stand in the plan's fetch line, and the variable's name
                under that test's `passes_environment` (the study tool
                gives a command no variable the plan does not name), where
                the people locking read both; without the flag the variable
                is ignored. A case sealed this way is never a system trial:
                `verdict` calls it void.
  verdict       after the steward has decided: check the study log, check
                that the data is the data the opening read and the answer
                is the answer the seal wrote, open the seal, compare what
                the factory concluded with what was put in, and write the
                verdict into the study log: right, not wrong
                (inconclusive), or WRONG. `sf.py close --outcome
                system-trial-accepted` needs that event to say right.
  blind-test    the same thing many times, unattended: blind test cases
                through the whole procedure (known-answer tests, working
                data, rehearsal, lock, opening, finding, review, log
                check), counting how often a false idea is supported and a
                true one missed. The lock is recorded by the harness, in
                throwaway directories, and labelled as such: this measures
                the study tool and the method, never people or assistants.

Usage:
  system_trial.py working-data --executor PATH --case CASE.json --out RECEIPT.json
  system_trial.py seal --out DATA.json --answer ANSWER.json [--rehearsal | --harness]
  system_trial.py verdict --study STUDY_DIR --by human:<id> [--anchor SEQ:HASH ...]
  system_trial.py blind-test --template studies/STUDY-0000 --n 200 [--seed 7] [--cases 2000] --out blind-test.json
"""
import sys

sys.dont_write_bytecode = True  # this package leaves no bytecode beside its sources
if __name__ == "__main__" and not sys.flags.safe_path and sys.path:
    del sys.path[0]  # the script's own folder must not shadow a module imported below

import argparse
import hashlib
import importlib.util
import json
import os
import secrets
import shutil
import tempfile
from pathlib import Path

# Whatever sits in a __pycache__ folder beside the files loaded below is never read in their place: Python is
# pointed at a cache folder that does not exist. (Run by the study tool, it already is.)
sys.pycache_prefix = os.path.join(tempfile.gettempdir(), "sf-no-bytecode-" + secrets.token_hex(16))
HERE = Path(__file__).resolve().parent


STUDY_TOOL = HERE.parent.parent / "tools" / "sf.py"  # the study tool; the files of the gain method sit in this folder


def neighbour(name: str):
    """Load a file of this folder by its path (the study tool by its own), so what runs is the file the lock
    hashed and nothing that shares its name somewhere else on the import path."""
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, STUDY_TOOL if name == "sf" else HERE / f"{name}.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


make_case = neighbour("test_cases").make_case

GAINS = (1.00, 1.00, 0.90, 1.10)  # drawn uniformly: true half the time
ENTROPY = "operating-system entropy at the opening"
HARNESS = "the blind test harness"
REHEARSAL = "a rehearsal case with a published seed; never the sealed one"
DIFFERENCE = 0.05  # the difference that matters
HOOK = "BLIND_TEST_SEAL"  # read only when the fetch line carries --harness: "seed:gain", so a blind test is reproducible


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def cmd_seal(a) -> int:
    if a.rehearsal and a.harness:
        print("seal: --rehearsal and --harness do not go together", file=sys.stderr)
        return 2
    if a.rehearsal:
        seed, gain, how = 1, 1.0, REHEARSAL
    elif a.harness:
        try:
            s, g = os.environ[HOOK].split(":")
            seed, gain, how = int(s), float(g), HARNESS
        except (KeyError, ValueError):
            print(f"seal: --harness was given and {HOOK} does not hold seed:gain; only the blind test harness seals "
                  "this way, and nothing was sealed", file=sys.stderr)
            return 2
    else:  # the real thing: nothing in the environment can choose the case
        seed, gain, how = secrets.randbits(48), secrets.choice(GAINS), ENTROPY
    case, put_in = make_case(seed, gain=gain)
    for f in (a.out, a.answer):
        f.parent.mkdir(parents=True, exist_ok=True)
    # the answer first, then the data that names it by checksum; the nonce keeps the checksum from giving the gain away
    a.answer.write_text(json.dumps({"answers": a.out.name, "sealed": {"by": how}, "put_in": put_in,
                                    "nonce": secrets.token_hex(32)}))
    case["sealed"] = {"by": how, "answer_sha256": sha(a.answer),
                      "note": "what was put in is in a separate file that the analysis is never given; this checksum ties the two"}
    a.out.write_text(json.dumps(case))
    print(f"sealed a blind test case at {a.out} (the answer is in a separate file and is not printed)", file=sys.stderr)
    return 0


def judge(gain_put_in: float, outcome: str) -> str:
    true = abs(gain_put_in - 1.0) <= DIFFERENCE + 1e-9
    if outcome == "inconclusive":
        return "not wrong (inconclusive)"
    if outcome not in ("supported", "refuted"):
        return "no result (the run failed)"
    if (outcome == "supported") == true and outcome in ("supported", "refuted"):
        return "right"
    return "WRONG"


def answer_path(sf, study, plan: dict) -> Path:
    """Where the seal put the answer: the word after --answer in the plan's fetch line."""
    fetch = [str(w) for w in plan["tests"]["held-out"]["fetch"]]
    if "--answer" not in fetch or fetch.index("--answer") + 1 >= len(fetch):
        raise sf.Refused("the plan's fetch line names no --answer file, so this study was not sealed by `system_trial.py seal`")
    return study.word(fetch[fetch.index("--answer") + 1], plan)


def read_verdict(sf, study) -> dict:
    """Open the seal of one study and compare. Refuses unless the data on disk is what the opening read and
    the answer on disk is the one the data names by checksum."""
    plan = study.plan()
    finished = sf.last_live_opening(study.events())
    if finished is None:
        raise sf.Refused("no opening has finished in this study")
    data = study.path(finished["data"]["data"])
    if not data.is_file() or sha(data) != finished["data"].get("data_sha"):
        raise sf.Refused("the data file on disk is not what the opening read (its checksum is not the one in the study log); "
                         "no verdict is given on it")
    case = json.loads(data.read_text())
    answer = answer_path(sf, study, plan)
    sealed = case.get("sealed") if isinstance(case.get("sealed"), dict) else {}
    if not answer.is_file() or sha(answer) != sealed.get("answer_sha256"):
        raise sf.Refused("the answer file on disk is not the one the seal wrote (the data file names another checksum); "
                         "no verdict is given on it")
    put_in = json.loads(answer.read_text())["put_in"]
    rid = next(r["id"] for r in plan["rules"] if r.get("role") == "primary")
    outcome = finished["data"]["outcomes"][rid]
    gain = put_in["gain"]
    return {"study": study.d.name, "sealed_by": sealed.get("by"), "gain_put_in": gain,
            "the_idea_was_true": abs(gain - 1.0) <= DIFFERENCE + 1e-9, "the_factory_said": outcome,
            "verdict": judge(gain, outcome), "data_sha": finished["data"]["data_sha"], "answer_sha": sha(answer)}


def cmd_verdict(a) -> int:
    sf = neighbour("sf")
    try:
        sf.refuse_dirty_environment()
        study = sf.Study(a.study)
        study.check_actor(a.by)
        rep = sf.check_log(study, a.anchor)
        if rep["status"] == sf.INVALID:
            raise sf.Refused("the study log or its files do not check out, so no verdict is given: " + "; ".join(rep["problems"]))
        v = read_verdict(sf, study)
        if v["sealed_by"] != ENTROPY:  # a case chosen by the harness, or a rehearsal case, was never sealed from anyone
            v["verdict"] = f"void: this case was sealed by {v['sealed_by']}, not by entropy at the opening"
        study.append(a.by, "trial.verdict", {k: v[k] for k in ("verdict", "sealed_by", "gain_put_in", "the_idea_was_true",
                                                                "the_factory_said", "data_sha", "answer_sha")})
    except sf.Refused as r:
        print(f"REFUSED: {r}", file=sys.stderr)
        return 2
    print(json.dumps(v, indent=1))
    print("the verdict is written to the study log" + ("" if v["verdict"] == "right" else
                                                         "; `close --outcome system-trial-accepted` needs a verdict of right"), file=sys.stderr)
    return 0 if v["verdict"] in ("right", "not wrong (inconclusive)") else 1


def cmd_working_data(a) -> int:
    """The system trial's working data: a known-answer test case with a
    published seed, so the study touches no real record at all."""
    import subprocess
    case, _ = make_case(2, gain=1.0)  # published: seed 2, a gain of 1.00; the method is given the data alone
    case["sealed"] = {"by": "a working-data case with a published seed; never the sealed one"}
    a.case.parent.mkdir(parents=True, exist_ok=True)
    a.case.write_text(json.dumps(case))
    return subprocess.run([sys.executable, str(HERE / "confront.py"), "--executor", str(a.executor), "--inputs", str(a.case),
                           "--screen-reach-q", "2", "--out", str(a.out)]).returncode


def cmd_blind_test(a) -> int:
    import yaml
    sf = neighbour("sf")
    try:
        sf.refuse_dirty_environment()
    except sf.Refused as r:
        print(f"REFUSED: {r}", file=sys.stderr)
        return 2
    ns = argparse.Namespace
    quiet = open(os.devnull, "w")
    url = "https://example.invalid/blind-test-harness-not-a-person"
    template = a.template.resolve()
    plan = sf.load_plan_text((template / "analysis-plan.yaml").read_text())
    plan["roots"] = {k: str((template / v).resolve()) for k, v in plan["roots"].items()}  # absolute: the copies move
    for name, folder in plan["roots"].items():  # say in words which checkout is missing, before anything is run
        if not Path(folder).is_dir():
            print(f"REFUSED: the blind test runs the plan in {template}, and that plan's root `{name}` points at {folder}, "
                  f"which is not there. Check out {Path(folder).name} at that place (beside this repository) and run again. "
                  "Nothing was run", file=sys.stderr)
            return 2
    fetch = plan["tests"]["held-out"]["fetch"]
    if "--harness" not in fetch:  # the harness chooses each case, and says so where the plan is read
        fetch.insert(fetch.index("seal") + 1, "--harness")
    passes = plan["tests"]["held-out"].setdefault("passes_environment", [])
    if HOOK not in passes:  # and the study tool gives the seal no variable the plan does not name
        passes.append(HOOK)
    if a.cases:
        cmd = plan["tests"]["known-answers"]["command"]
        cmd[cmd.index("--cases") + 1] = str(a.cases)
    tally = {}
    stdout = sys.stdout
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp).resolve()
        base = tmp / "base" / "STUDY-BLIND-TEST"
        sys.stdout = quiet
        try:
            sf.cmd_start(sf.Study(base), ns(id="STUDY-BLIND-TEST", question=plan["question"], by="agent:blind-test-harness"))
            (base / "analysis-plan.yaml").write_text(yaml.safe_dump(plan, sort_keys=False))
            study = sf.Study(base)
            sf.cmd_test(study, ns(what="known-answers", by="agent:blind-test-harness"))
            sf.cmd_test(study, ns(what="working-data", by="agent:blind-test-harness"))
            for reh in plan.get("rehearsals") or []:
                sf.cmd_rehearse(study, ns(id=reh["id"], by="agent:blind-test-harness"))
            (tmp / "verdict.md").write_text("blind test harness: approve, automatically; not a review")
            (tmp / "finding.md").write_text("blind test harness: no finding is written; this file stands where one would be attached")
            for i in range(a.n):
                gain = GAINS[i % len(GAINS)]
                one = tmp / f"run-{i:04d}" / "STUDY-BLIND-TEST"
                shutil.copytree(base, one)
                study = sf.Study(one)
                sf.cmd_lock(study, ns(by=sf.HARNESS_PERSON, evidence=url))
                os.environ[HOOK] = f"{a.seed * 100003 + i}:{gain}"
                try:
                    sf.cmd_open_held_out(study, ns(test="held-out", by="agent:blind-test-access-gate"))
                finally:
                    os.environ.pop(HOOK, None)
                sf.cmd_attach(study, ns(by="agent:blind-test-harness", file=str(tmp / "finding.md")))
                sf.cmd_review(study, ns(by="agent:blind-test-review", verdict="approve", file=str(tmp / "verdict.md")))
                posted = [f"{e['seq']}:{e['hash']}" for e in study.events() if e["kind"] in ("lock.recorded", "opening.finished")]
                status = sf.check_log(study, posted)["status"]
                v = read_verdict(sf, study)
                t = tally.setdefault(str(gain), {"cases": 0, "supported": 0, "refuted": 0, "inconclusive": 0,
                                                 "ready_for_signature": 0, "wrong": 0})
                t["cases"] += 1
                t[v["the_factory_said"]] += 1
                t["ready_for_signature"] += status == sf.READY
                t["wrong"] += v["verdict"] == "WRONG"
        except sf.Refused as r:  # a refusal by the study tool ends the blind test in its words, never in a traceback
            print(f"REFUSED: the blind test stopped because the study tool refused a step: {r}", file=sys.stderr)
            return 2
        finally:
            sys.stdout = stdout
            quiet.close()
    true = tally.get("1.0", {"cases": 0, "supported": 0})
    false = [t for g, t in tally.items() if g != "1.0"]
    n_false = sum(t["cases"] for t in false)
    out = {"blind_test": "blind test cases through the whole procedure", "cases": a.n, "seed": a.seed,
           "difference_that_matters": DIFFERENCE,
           "acts_by_people": ("recorded by the harness in throwaway directories; this measures the study tool and the "
                              "method, not people or assistants"),
           "by_gain_put_in": tally,
           "false_support_rate": round(sum(t["supported"] for t in false) / n_false, 4) if n_false else None,
           "missed_true_rate": round(1 - true["supported"] / true["cases"], 4) if true["cases"] else None,
           "wrong_verdicts": sum(t["wrong"] for t in tally.values()),
           "every_run_ready_for_signature": all(t["ready_for_signature"] == t["cases"] for t in tally.values())}
    text = json.dumps(out, indent=1)
    if a.out:
        a.out.write_text(text)
    print(text)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("seal")
    s.add_argument("--out", type=Path, required=True, help="the data: what the locked analysis is given")
    s.add_argument("--answer", type=Path, required=True, help="what was put in: a file the analysis is never passed")
    s.add_argument("--rehearsal", action="store_true", help="a published case (seed 1, a gain of 1.00), for the rehearsal")
    s.add_argument("--harness", action="store_true", help=f"take the seed and the gain from {HOOK}; the blind test harness only")
    v = sub.add_parser("verdict")
    v.add_argument("--study", type=Path, required=True)
    v.add_argument("--by", required=True, help="who reveals the answer: human:<id> or agent:<id>")
    v.add_argument("--anchor", action="append", default=None, help="SEQ:HASH, a log fingerprint posted outside the workspace; repeatable")
    d = sub.add_parser("working-data")
    d.add_argument("--executor", type=Path, required=True)
    d.add_argument("--case", type=Path, required=True)
    d.add_argument("--out", type=Path, required=True)
    b = sub.add_parser("blind-test")
    b.add_argument("--template", type=Path, required=True)
    b.add_argument("--n", type=int, default=200)
    b.add_argument("--seed", type=int, default=7)
    b.add_argument("--cases", type=int, help="override the known-answer case count (smaller is faster and noisier)")
    b.add_argument("--out", type=Path)
    a = ap.parse_args()
    return {"seal": cmd_seal, "verdict": cmd_verdict, "working-data": cmd_working_data, "blind-test": cmd_blind_test}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
