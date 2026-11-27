#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""benchmark: the blind test of the system as suites, run under two versions
of the factory's definition and compared by a rule stated in advance.

A suite is a folder in the definition, `factory/benchmarks/<suite>/`, with a
`suite.yaml`. It names the cases (each a sealed case: a truth planted by
hand in synthetic data, never real held-out data), the configurations (two
or more versions of the definition, each a path or a git ref), how many
times each case is run, and the comparison: which rate decides, by how much
one configuration has to be better, and how noise is judged. The comparison
is in the file before anything is run; changing it after a run is choosing
the answer.

  run       run a suite: every case, every repetition, under every
            configuration, through every stage of the confirming way in
            scratch folders (the known-answer tests, the working data and
            the rehearsals, then for each case the lock, the opening on the
            sealed case, a finding, a review, the log check, and the seal
            opened); then report each configuration's wrong verdicts,
            inconclusives and power side by side, and the comparison
  cases     list a suite's cases. For an acceptance suite this needs the
            seed, and writes the generated cases into a folder named
            `acceptance-cases`, which no agent may read
  selftest  the arithmetic, the generation of acceptance cases, and the
            refusals; it runs no suite

WHAT A CONFIGURATION IS. A version of the definition. A `path` is a
definition folder, read from the suite's own definition; the plan and the
method scripts are then the ones in the repository that holds it. A `ref`
is a git commit: the whole repository at that commit is taken out into a
scratch folder, and the definition, the plan and the method scripts are the
ones found there. In both cases the study tool that runs the cases is the
one beside this file: a configuration is a version of the definition and of
the method, not of the tools. Each configuration's definition must be valid
(check_factory.py); one that is not, or cannot be validated, makes the
suite `not comparable`, which is never a pass.

THE TWO SETS. A design suite keeps its cases as files: anyone may read
them, and a change to the factory may be shaped against them. An acceptance
suite keeps none: its cases are generated when it is run, from a seed that
whoever keeps the acceptance set gives the run in an environment variable
(the suite names it). Without the seed this tool refuses, and it never
invents one. The generated cases and the result of an acceptance run are
written into a folder named `acceptance-cases`, which every agent's file
lists under `must_never_see`. What that is worth, plainly: the validator
checks that every agent lists it, and the Claude Code harness's per-call
check refuses a read of it when a platform calls that check. Nothing stops
a person, or an agent that runs arbitrary code, from reading a file. The
seed is the part that does not rest on instruction: it is not in the
repository.

HOW NOISE IS JUDGED. Every configuration runs the same cases on the same
draws, so the runs are paired. A pair on which two configurations agree
says nothing about which is better; only the discordant pairs count. With
d discordant pairs, in k of which the candidate was right where the
baseline was not, the two-sided exact sign test gives the chance of a split
at least that one-sided if the two were equally good. The candidate is
`better` only when the difference reaches the stated margin and that chance
is below the stated alpha; fewer than six discordant pairs can never reach
0.05. A rate the suite says must not be worse fails the candidate on any
excess at all: a guard is cautious on purpose. Each rate is printed with a
95 percent Wilson interval, so that how little a small suite can tell is in
view.

What this measures: the study tool and the method under a definition. The
lock is recorded by the harness in throwaway folders and labelled as such;
no person and no agent takes part, and no language model runs.

Usage:
  benchmark.py run --suite factory/benchmarks/built-in-gain [--out RESULT.json] [--work DIR]
  benchmark.py cases --suite DIR [--work DIR]
  benchmark.py selftest
"""
import sys

sys.dont_write_bytecode = True
if __name__ == "__main__" and not (sys.flags.isolated and sys.flags.no_site):
    # A clean start. This tool runs itself again in a Python that reads no PYTHON variable, no user site, no start-up
    # file (.pth, sitecustomize) and not the folder this file is in, so that none of those can change what it does.
    # What a hostile environment ran before this line has already run: a stated limit (docs/WHAT-IS-ENFORCED.md).
    import os
    _again = [sys.executable, "-I", "-S", "-B", os.path.abspath(__file__), *sys.argv[1:]]
    if os.name == "posix":
        os.execv(sys.executable, _again)
    import subprocess
    sys.exit(subprocess.call(_again))
if __name__ == "__main__":
    # The packages this tool declares, from the environment its interpreter belongs to, put on the import path by
    # hand and last: nothing in that folder is run at start-up.
    import os
    import sysconfig
    _env = os.path.dirname(os.path.dirname(os.path.abspath(sys.executable)))
    _lib = ([os.path.join(_env, "lib", f"python{sys.version_info.major}.{sys.version_info.minor}", "site-packages"),
             os.path.join(_env, "Lib", "site-packages")] if os.path.isfile(os.path.join(_env, "pyvenv.cfg"))
            else [sysconfig.get_paths()["purelib"], sysconfig.get_paths()["platlib"]])
    sys.path += [p for p in dict.fromkeys(_lib) if os.path.isdir(p) and p not in sys.path]
if __name__ == "__main__" and not sys.flags.safe_path and sys.path:
    _own = __file__.replace("\\", "/").rpartition("/")[0]
    del sys.path[0]
    sys.path[:] = [p for p in sys.path if p != _own]

import argparse  # noqa: E402
import hashlib  # noqa: E402
import hmac  # noqa: E402
import importlib.util  # noqa: E402
import io  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import os  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import tarfile  # noqa: E402
import tempfile  # noqa: E402
from pathlib import Path  # noqa: E402

import yaml  # noqa: E402

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
KEPT_OUT = "acceptance-cases"  # the folder an acceptance run writes into; every agent's file lists it under must_never_see
DIFFERENCE = 0.05  # the difference that matters for the built-in method: the idea is that the gain is within this of one


def load(name: str, path: Path):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


sf = load("sf", HERE / "sf.py")
fd = load("check_factory", HERE / "check_factory.py")
Refused = sf.Refused


class NotComparable(Exception):
    """The suite could not be run to a comparison. Never a pass."""


# ---------------------------------------------------------------- the arithmetic
def wilson(k: int, n: int, z: float = 1.959964) -> list | None:
    """The 95 percent Wilson interval for k out of n, as [low, high]; None when n is 0."""
    if n == 0:
        return None
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [round(max(0.0, centre - half), 4), round(min(1.0, centre + half), 4)]


def sign_test(k: int, d: int) -> float:
    """The two-sided exact sign test: the chance, if a discordant pair were as likely to fall either way, of a
    split at least as one-sided as k out of d. 1.0 when there are no discordant pairs."""
    if d == 0:
        return 1.0
    tail = sum(math.comb(d, i) for i in range(0, min(k, d - k) + 1)) / 2 ** d
    return min(1.0, 2 * tail)


def events(run: dict) -> dict:
    """What one run counts as, for each rate. None where the rate does not apply to the run."""
    true, said = run["the_idea_was_true"], run["the_factory_said"]
    return {"wrong_verdicts": run["verdict"] == "WRONG",
            "false_support_rate": (said == "supported") if not true else None,
            "missed_true_rate": (said != "supported") if true else None}


def rates(runs: list) -> dict:
    """One configuration's results, side by side: wrong verdicts, inconclusives and power, each with its count,
    what it is out of, and a 95 percent Wilson interval."""
    n = len(runs)
    true = [r for r in runs if r["the_idea_was_true"]]
    false = [r for r in runs if not r["the_idea_was_true"]]

    def rate(k: int, of: int) -> dict:
        return {"count": k, "of": of, "rate": round(k / of, 4) if of else None, "interval_95": wilson(k, of)}

    return {"runs": n, "true_cases": len(true), "false_cases": len(false),
            "wrong_verdicts": rate(sum(r["verdict"] == "WRONG" for r in runs), n),
            "inconclusive": rate(sum(r["the_factory_said"] == "inconclusive" for r in runs), n),
            "false_support_rate": rate(sum(r["the_factory_said"] == "supported" for r in false), len(false)),
            "missed_true_rate": rate(sum(r["the_factory_said"] != "supported" for r in true), len(true)),
            "power": {**rate(sum(r["the_factory_said"] == "refuted" for r in false), len(false)),
                      "means": "how often a false idea was refuted"},
            "ready_for_signature": rate(sum(bool(r["ready_for_signature"]) for r in runs), n),
            "process_checks_all_pass": rate(sum(set(r["process_checks"].values()) <= {"pass"} for r in runs), n),
            "process_checks_that_did_not_pass": sorted({k for r in runs for k, v in r["process_checks"].items() if v != "pass"})}


def compare(comparison: dict, baseline: list, candidate: list) -> dict:
    """The comparison the suite stated, applied to two configurations' paired runs."""
    if len(baseline) != len(candidate) or any(b["case"] != c["case"] or b["repetition"] != c["repetition"] for b, c in zip(baseline, candidate)):
        raise NotComparable("the two configurations did not run the same cases in the same order, so their runs are not pairs")
    primary = comparison["primary"]
    pairs = [(events(b)[primary], events(c)[primary]) for b, c in zip(baseline, candidate)]
    pairs = [(b, c) for b, c in pairs if b is not None and c is not None]
    bad_b, bad_c = sum(b for b, _ in pairs), sum(c for _, c in pairs)
    discordant = [(b, c) for b, c in pairs if b != c]
    k = sum(1 for b, c in discordant if b and not c)  # the candidate was right where the baseline was not
    p = sign_test(k, len(discordant))
    guards = {}
    for g in comparison["must_not_be_worse"]:
        gp = [(events(b)[g], events(c)[g]) for b, c in zip(baseline, candidate)]
        gb, gc = sum(1 for b, _ in gp if b), sum(1 for _, c in gp if c)
        guards[g] = {"baseline": gb, "candidate": gc, "holds": gc <= gb}
    margin, alpha = comparison["margin"], comparison["alpha"]
    if not all(g["holds"] for g in guards.values()):
        result = "worse"
        why = "the candidate is worse on a rate the suite says must not be worse: " + ", ".join(
            f"{g} ({v['candidate']} against {v['baseline']})" for g, v in guards.items() if not v["holds"])
    elif bad_b - bad_c >= margin and p < alpha:
        result, why = "better", (f"the candidate has {bad_b - bad_c} fewer on {primary}, which reaches the margin of {margin}, and "
                                 f"the {len(discordant)} discordant pairs are too one-sided to be chance (p = {p:.4f} < {alpha})")
    elif bad_c - bad_b >= margin and p < alpha:
        result, why = "worse", (f"the candidate has {bad_c - bad_b} more on {primary}, and the {len(discordant)} discordant pairs "
                                f"are too one-sided to be chance (p = {p:.4f} < {alpha})")
    else:
        result = "no difference beyond noise"
        why = (f"on {primary} the baseline has {bad_b} and the candidate {bad_c} over {len(pairs)} paired runs; "
               + ("the two gave the same answer on every pair" if not discordant else
                  f"{len(discordant)} pairs are discordant, {k} of them in the candidate's favour (p = {p:.4f}), which does not reach "
                  f"a margin of {margin} at alpha {alpha}"))
    return {"result": result, "why": why, "primary": primary, "baseline_count": bad_b, "candidate_count": bad_c, "paired_runs": len(pairs),
            "discordant_pairs": len(discordant), "in_the_candidates_favour": k, "sign_test_p": round(p, 6), "margin": margin, "alpha": alpha,
            "guards": guards,
            "smallest_number_of_discordant_pairs_that_could_reach_alpha": next((d for d in range(1, 200) if sign_test(0, d) < alpha), None)}


# ---------------------------------------------------------------- the suite
def read_suite(suite_dir: Path) -> tuple:
    """(suite, definition root, repository). Refuses a folder that is not a suite of a valid definition."""
    suite_dir = Path(suite_dir).resolve()
    root = suite_dir.parent.parent
    if suite_dir.parent.name != "benchmarks" or not (suite_dir / "suite.yaml").is_file() or not (root / "factory.yaml").is_file():
        raise Refused(f"{suite_dir} is not a suite: a suite is benchmarks/<suite>/ in a definition, with a suite.yaml")
    word, _, problems, nv = fd.result(root, root.parent)
    if word != "valid":
        raise NotComparable(f"the definition that holds this suite is {word} ({'; '.join((problems + nv)[:3])}); a suite is run from a valid definition")
    return fd.load_yaml((suite_dir / "suite.yaml").read_text()), root, root.parent


def design_cases(suite: dict, suite_dir: Path) -> list:
    out = []
    for name in suite["cases"]:
        c = fd.load_yaml((suite_dir / "cases" / f"{name}.yaml").read_text())
        out.append({"case": name, "seed": int(c["sampling"]["seed"]), "gain": float(c["truth"]["planted"]),
                    "the_idea_is_true": bool(c["truth"]["the_idea_is_true"]), "title": c["title"]})
    return out


def generated_cases(suite: dict, seed: str | None) -> list:
    """An acceptance suite's cases, from the keeper's seed. Each case's own seed and its planted truth are drawn by
    HMAC from the seed and the case's number, so the same seed gives the same cases and nothing else does."""
    g = suite["generated"]
    if not seed or len(seed.strip()) < 16:
        raise Refused(f"this is an acceptance suite: its cases are generated from a seed kept outside the definition, which the run is "
                      f"given in the environment variable {g['seed']['env']} (at least 16 characters). It is not set, and this tool "
                      "never invents one. Whoever keeps the acceptance set runs this suite; an agent proposing a change does not")
    out = []
    for i in range(int(g["count"])):
        h = hmac.new(seed.strip().encode(), f"{suite['name']}:{i}".encode(), hashlib.sha256).hexdigest()
        gain = float(g["truths"][int(h[12:20], 16) % len(g["truths"])])
        out.append({"case": f"generated-{i + 1:03d}", "seed": int(h[:11], 16), "gain": gain,
                    "the_idea_is_true": abs(gain - 1.0) <= DIFFERENCE + 1e-9, "title": f"generated case {i + 1}"})
    return out


def configuration(c: dict, root: Path, scratch: Path) -> tuple:
    """(definition root, repository) for one configuration. A ref is taken out of git, whole, into scratch."""
    d = c["definition"]
    if "path" in d:
        target = (root / str(d["path"])).resolve()
        return target, target.parent
    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=root, capture_output=True, text=True)
    if top.returncode != 0:
        raise NotComparable(f"configuration `{c['name']}` names the git ref `{d['ref']}`, and {root} is not in a git work tree")
    top_dir = Path(top.stdout.strip()).resolve()
    done = subprocess.run(["git", "archive", "--format=tar", str(d["ref"])], cwd=top_dir, capture_output=True)
    if done.returncode != 0:
        raise NotComparable(f"configuration `{c['name']}`: git has no commit `{d['ref']}` here ({done.stderr.decode(errors='replace').strip()[:160]})")
    out = scratch / f"configuration-{c['name']}"
    with tarfile.open(fileobj=io.BytesIO(done.stdout)) as tar:
        tar.extractall(out, filter="data")
    target = out / root.relative_to(top_dir)
    if not (target / "factory.yaml").is_file():
        raise NotComparable(f"configuration `{c['name']}`: the commit `{d['ref']}` has no definition at {root.relative_to(top_dir)}/ "
                            "(a commit from before the definition was a tree cannot be a configuration)")
    return target, target.parent


def run_suite(suite_dir: Path, work: Path | None = None, runner=None, env: dict | None = None) -> dict:
    """Run a suite and return its report. `runner` stands in for the harness in the self-test."""
    suite, root, repository = read_suite(suite_dir)
    acceptance = suite["set"] == "acceptance"
    env = os.environ if env is None else env
    cases = generated_cases(suite, env.get(suite["generated"]["seed"]["env"])) if acceptance else design_cases(suite, Path(suite_dir).resolve())
    st = load("system_trial", REPO / "methods" / "gain" / "system_trial.py")
    own_work = work is None
    work = Path(tempfile.mkdtemp(prefix="benchmark-")).resolve() if own_work else Path(work).resolve()
    kept_out = work / KEPT_OUT
    if acceptance:
        kept_out.mkdir(parents=True, exist_ok=True)
        (kept_out / "cases.json").write_text(json.dumps(cases, indent=1) + "\n")
    plan_of = [(c["case"], rep, c["seed"] * 1000 + rep, c["gain"]) for c in cases for rep in range(1, int(suite["repetitions"]) + 1)]
    by_config, problems, prepared = {}, [], {}
    scratch = Path(tempfile.mkdtemp(prefix="benchmark-scratch-")).resolve()
    try:
        for c in suite["configurations"]:
            name = c["name"]
            try:
                definition, repo = configuration(c, root, scratch)
                word, _, bad, nv = fd.result(definition, repo)
                if word != "valid":
                    raise NotComparable(f"configuration `{name}`: its definition is {word} ({'; '.join((bad + nv)[:2])})")
                template = repo / suite["target"]["plan"]
                if not (template / "analysis-plan.yaml").is_file():
                    raise NotComparable(f"configuration `{name}`: its repository has no plan at {suite['target']['plan']}")
                if runner is not None:
                    got = runner(name, definition, template, [(s, g) for _, _, s, g in plan_of])
                else:
                    # configurations that share a plan and its code share one run of the known-answer tests: the tests
                    # are the same commands on the same files, and each run's lock still binds its own definition
                    key = str(template.resolve())
                    if key not in prepared:
                        prepared[key] = st.prepare(sf, template, suite.get("known_answer_cases"), scratch / f"base-{len(prepared)}")
                    got = st.run_prepared(sf, prepared[key], [(s, g) for _, _, s, g in plan_of], scratch / f"runs-{name}", definition)
            except (Refused, NotComparable) as e:
                problems.append(f"configuration `{name}` did not run: {e}")
                continue
            stamp = fd.stamp(definition)
            by_config[name] = {"definition": {"sha256": stamp["sha256"], "version": stamp["version"], "as": c["definition"]},
                               "runs": [{"case": case, "repetition": rep, **r} for (case, rep, _, _), r in zip(plan_of, got)]}
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    report = {"suite": suite["name"], "set": suite["set"], "target": suite["target"], "cases": len(cases), "repetitions": suite["repetitions"],
              "what_this_measures": "the study tool and the method under each definition; the lock is recorded by the harness in throwaway "
                                    "folders, and no person, no agent and no language model takes part",
              "configurations": {n: {"definition": v["definition"], **rates(v["runs"])} for n, v in by_config.items()},
              "comparison_as_stated": suite["comparison"]}
    base, cand = suite["comparison"]["baseline"], suite["comparison"]["candidate"]
    if problems or base not in by_config or cand not in by_config:
        report["comparison"] = {"result": "not comparable", "why": "; ".join(problems) or "a configuration the comparison names did not run"}
    else:
        try:
            report["comparison"] = compare(suite["comparison"], by_config[base]["runs"], by_config[cand]["runs"])
        except NotComparable as e:
            report["comparison"] = {"result": "not comparable", "why": str(e)}
    report["runs"] = {n: [{k: r[k] for k in ("case", "repetition", "the_idea_was_true", "the_factory_said", "verdict")} for r in v["runs"]]
                      for n, v in by_config.items()}
    if acceptance:  # the truths of the acceptance cases are in the runs: the result goes where no agent may read
        (kept_out / "result.json").write_text(json.dumps(report, indent=1) + "\n")
        report = {k: v for k, v in report.items() if k != "runs"}
        report["kept_out"] = f"the cases and the run-by-run result are in {kept_out}, which no agent may read; this summary carries no case's truth"
    elif own_work:
        shutil.rmtree(work, ignore_errors=True)
    return report


def in_words(report: dict) -> list:
    """The report as a few plain lines: the configurations side by side, then the comparison."""
    out = [f"{report['suite']} ({report['set']} set): {report['cases']} cases, each run {report['repetitions']} time(s), under "
           f"{len(report['configurations'])} configuration(s)."]

    def cell(r: dict) -> str:
        return "none apply" if not r["of"] else f"{r['count']} of {r['of']} (95 percent interval {r['interval_95'][0]} to {r['interval_95'][1]})"

    for name, c in report["configurations"].items():
        out.append(f"  {name} (definition {c['definition']['version']}, sha256 {c['definition']['sha256'][:12]}):")
        out.append(f"    wrong verdicts            {cell(c['wrong_verdicts'])}")
        out.append(f"    inconclusive              {cell(c['inconclusive'])}")
        out.append(f"    power (false, refuted)    {cell(c['power'])}")
        out.append(f"    false ideas supported     {cell(c['false_support_rate'])}")
        out.append(f"    true ideas not supported  {cell(c['missed_true_rate'])}")
        out.append(f"    every process check pass  {cell(c['process_checks_all_pass'])}")
    comp = report["comparison"]
    out.append(f"The comparison, as stated before the run ({report['comparison_as_stated']['candidate']} against "
               f"{report['comparison_as_stated']['baseline']}, on {report['comparison_as_stated']['primary']}): {comp['result'].upper()}.")
    out.append(f"  {comp['why']}.")
    if "smallest_number_of_discordant_pairs_that_could_reach_alpha" in comp:
        out.append(f"  With this alpha, fewer than {comp['smallest_number_of_discordant_pairs_that_could_reach_alpha']} discordant pairs can never "
                   "show a difference, however one-sided they are.")
    return out


# ---------------------------------------------------------------- commands
def cmd_run(a) -> int:
    try:
        report = run_suite(a.suite, a.work)
    except Refused as r:
        print(f"REFUSED: {r}", file=sys.stderr)
        return 2
    except NotComparable as e:
        print(f"NOT COMPARABLE: {e}. This is never a pass", file=sys.stderr)
        return 2
    except (OSError, KeyError, TypeError, ValueError) as e:  # a harness that fell over is not a result
        print(f"NOT COMPARABLE: the run did not finish ({type(e).__name__}: {e}). This is never a pass", file=sys.stderr)
        return 2
    text = json.dumps(report, indent=1)
    if a.out:
        a.out.write_text(text + "\n")
    print(text)
    for line in in_words(report):
        print(line, file=sys.stderr)
    return 0 if report["comparison"]["result"] != "not comparable" else 2


def cmd_cases(a) -> int:
    try:
        suite, _, _ = read_suite(a.suite)
        if suite["set"] == "acceptance":
            cases = generated_cases(suite, os.environ.get(suite["generated"]["seed"]["env"]))
            work = (a.work or Path(tempfile.mkdtemp(prefix="benchmark-"))).resolve() / KEPT_OUT
            work.mkdir(parents=True, exist_ok=True)
            (work / "cases.json").write_text(json.dumps(cases, indent=1) + "\n")
            print(f"{len(cases)} acceptance cases generated from the seed and written to {work / 'cases.json'}; they are not printed, and no agent may read that folder")
        else:
            for c in design_cases(suite, Path(a.suite).resolve()):
                print(f"{c['case']}: gain {c['gain']} planted, the idea is {'true' if c['the_idea_is_true'] else 'false'}; {c['title']}")
    except (Refused, NotComparable) as r:
        print(f"REFUSED: {r}", file=sys.stderr)
        return 2
    return 0


# ---------------------------------------------------------------- the self-test
def selftest() -> int:
    results = []

    def ok(name: str, cond) -> None:
        results.append((name, bool(cond)))

    def refusal(fn, *args, **kw) -> str:
        try:
            fn(*args, **kw)
        except (Refused, NotComparable) as r:
            return str(r) or "refused"
        return ""

    tmp = Path(tempfile.mkdtemp(prefix="benchmark-selftest-")).resolve()
    try:
        ok("the sign test: no discordant pairs is no evidence; 5 of 5 cannot reach 0.05 and 6 of 6 does",
           sign_test(0, 0) == 1.0 and sign_test(5, 5) == 0.0625 and sign_test(6, 6) == 0.03125 and sign_test(3, 6) == 1.0
           and abs(sign_test(1, 8) - 0.0703125) < 1e-12)
        ok("the Wilson interval: none of 12 still leaves room up to about a quarter, and nothing out of nothing has no interval",
           wilson(0, 12) == [0.0, 0.2425] and wilson(12, 12)[0] > 0.75 and wilson(0, 0) is None and wilson(6, 12)[0] < 0.5 < wilson(6, 12)[1])

        def run(case, rep, true, said) -> dict:
            verdict = "not wrong (inconclusive)" if said == "inconclusive" else ("right" if (said == "supported") == true else "WRONG")
            return {"case": case, "repetition": rep, "the_idea_was_true": true, "the_factory_said": said, "verdict": verdict,
                    "ready_for_signature": True, "process_checks": {"a": "pass"}}

        base = [run(f"c{i}", 1, i % 2 == 0, "supported") for i in range(12)]      # every false idea supported: six wrong verdicts
        same = [dict(r) for r in base]
        good = [run(f"c{i}", 1, i % 2 == 0, "supported" if i % 2 == 0 else "refuted") for i in range(12)]
        stated = {"primary": "wrong_verdicts", "margin": 1, "alpha": 0.05, "must_not_be_worse": ["false_support_rate"]}
        r = rates(base)
        ok("a configuration's report puts wrong verdicts, inconclusives and power side by side, each out of what it applies to",
           r["wrong_verdicts"]["count"] == 6 and r["wrong_verdicts"]["of"] == 12 and r["false_support_rate"] == {"count": 6, "of": 6, "rate": 1.0, "interval_95": wilson(6, 6)}
           and r["power"]["count"] == 0 and r["inconclusive"]["count"] == 0 and r["missed_true_rate"]["of"] == 6 and rates(good)["power"]["rate"] == 1.0)
        ok("a definition compared with itself: no difference beyond noise, with no discordant pair",
           compare(stated, base, same)["result"] == "no difference beyond noise" and compare(stated, base, same)["discordant_pairs"] == 0)
        better = compare(stated, base, good)
        ok("a candidate that is right on six runs where the baseline was wrong is better: the margin is reached and six one-sided pairs are not chance",
           better["result"] == "better" and better["discordant_pairs"] == 6 and better["in_the_candidates_favour"] == 6 and better["sign_test_p"] == 0.03125)
        ok("the same difference the other way round is worse", compare(stated, good, base)["result"] == "worse")
        five = good[:10] + base[10:]
        ok("five one-sided pairs are not enough at 0.05, whatever the margin: no difference beyond noise",
           compare({**stated, "must_not_be_worse": []}, base, five)["result"] == "no difference beyond noise"
           and compare(stated, base, five)["smallest_number_of_discordant_pairs_that_could_reach_alpha"] == 6)
        hedging = [run(f"c{i}", 1, i % 2 == 0, "inconclusive") for i in range(12)]
        ok("a candidate that answers inconclusive every time has no wrong verdict and no power, and the report shows both",
           rates(hedging)["wrong_verdicts"]["count"] == 0 and rates(hedging)["power"]["count"] == 0 and rates(hedging)["inconclusive"]["count"] == 12
           and rates(hedging)["missed_true_rate"]["count"] == 6)
        guard = {**stated, "primary": "missed_true_rate", "must_not_be_worse": ["false_support_rate"]}
        trade = [run(f"c{i}", 1, i % 2 == 0, "supported") for i in range(12)]
        careful = [run(f"c{i}", 1, i % 2 == 0, "inconclusive" if i % 2 == 0 else "refuted") for i in range(12)]
        ok("a candidate that buys fewer missed true ideas with more false ideas supported is worse, whatever the primary rate says",
           compare(guard, careful, trade)["result"] == "worse" and "must not be worse" in compare(guard, careful, trade)["why"])
        ok("runs that are not the same cases in the same order are not pairs", "are not pairs" in refusal(compare, stated, base, good[1:] + good[:1]))

        # the shipped suites, read
        design, root, repo = read_suite(REPO / "factory" / "benchmarks" / "built-in-gain")
        dc = design_cases(design, REPO / "factory" / "benchmarks" / "built-in-gain")
        ok("the design suite lists its cases as files, with true and false ideas among them",
           len(dc) == len(design["cases"]) >= 4 and {c["the_idea_is_true"] for c in dc} == {True, False}
           and all(c["the_idea_is_true"] == (abs(c["gain"] - 1.0) <= DIFFERENCE + 1e-9) for c in dc))
        acc, _, _ = read_suite(REPO / "factory" / "benchmarks" / "acceptance")
        ok("the acceptance suite refuses to give its cases without the seed, and never invents one",
           "never invents one" in refusal(generated_cases, acc, None) and "never invents one" in refusal(generated_cases, acc, "short"))
        g1, g2, g3 = generated_cases(acc, "a-seed-kept-somewhere-else-0001"), generated_cases(acc, "a-seed-kept-somewhere-else-0001"), generated_cases(acc, "a-seed-kept-somewhere-else-0002")
        ok("the same seed gives the same acceptance cases and another seed gives others",
           g1 == g2 and g1 != g3 and len(g1) == acc["generated"]["count"] and all(c["gain"] in acc["generated"]["truths"] for c in g1))
        ok("no acceptance case is in the definition, and the design cases are not the acceptance cases",
           not (REPO / "factory" / "benchmarks" / "acceptance" / "cases").exists() and not {c["seed"] for c in dc} & {c["seed"] for c in g1})
        ok("a folder that is not a suite is refused", "is not a suite" in refusal(read_suite, REPO / "factory" / "scorers"))

        # a suite run with a stand-in for the harness: the report, the pairing, where an acceptance result goes
        def stand_in(wrong_under: str):
            def runner(name, definition, template, plan):
                out = []
                for seed, gain in plan:
                    true = abs(gain - 1.0) <= DIFFERENCE + 1e-9
                    said = "supported" if (true or name == wrong_under) else "refuted"
                    out.append({"seed": seed, "gain_put_in": gain, "the_idea_was_true": true, "the_factory_said": said,
                                "verdict": "right" if (said == "supported") == true else "WRONG", "ready_for_signature": True,
                                "definition_sha256": "x", "process_checks": {"chain-of-custody": "pass"}})
                return out
            return runner

        rep = run_suite(REPO / "factory" / "benchmarks" / "built-in-gain", runner=stand_in("nobody"))
        ok("a suite run reports each configuration with its definition's checksum, and the comparison as it was stated",
           set(rep["configurations"]) == {"current", "same-again"} and rep["comparison"]["result"] == "no difference beyond noise"
           and rep["configurations"]["current"]["definition"]["sha256"] == fd.tree_checksum(REPO / "factory")["sha256"]
           and rep["configurations"]["current"]["runs"] == len(dc) * design["repetitions"] and rep["comparison_as_stated"] == design["comparison"])
        ok("each repetition of a case is its own draw, and both configurations run the same draws",
           len({(r["case"], r["repetition"]) for r in rep["runs"]["current"]}) == len(rep["runs"]["current"])
           and [(r["case"], r["repetition"]) for r in rep["runs"]["current"]] == [(r["case"], r["repetition"]) for r in rep["runs"]["same-again"]])
        worse = run_suite(REPO / "factory" / "benchmarks" / "built-in-gain", runner=stand_in("same-again"))
        ok("a candidate that supports false ideas the baseline refuted is worse, by the guard",
           worse["comparison"]["result"] == "worse" and worse["configurations"]["same-again"]["false_support_rate"]["count"] > 0
           and any("WRONG" in ln or "worse" in ln.lower() for ln in in_words(worse)))
        ok("the report in words names wrong verdicts, inconclusives and power for each configuration",
           all(any(w in ln for ln in in_words(rep)) for w in ("wrong verdicts", "inconclusive", "power", "NO DIFFERENCE BEYOND NOISE")))
        ok("an acceptance run with no seed is refused", "never invents one" in refusal(run_suite, REPO / "factory" / "benchmarks" / "acceptance", tmp / "w0", stand_in("nobody"), {}))
        arep = run_suite(REPO / "factory" / "benchmarks" / "acceptance", tmp / "w1", stand_in("nobody"), {"SF_ACCEPTANCE_SEED": "a-seed-kept-somewhere-else-0001"})
        ok("an acceptance run writes its cases and its run-by-run result into the folder no agent may read, and its summary carries no case's truth",
           (tmp / "w1" / KEPT_OUT / "cases.json").is_file() and (tmp / "w1" / KEPT_OUT / "result.json").is_file() and "runs" not in arep
           and "gain" not in json.dumps(arep["configurations"]) and arep["comparison"]["result"] == "no difference beyond noise")
        allow = load("allow", REPO / "factory" / "harnesses" / "claude-code" / "allow.py")
        ok("the per-call check refuses every agent a read of that folder",
           all(allow.decide(role, {"tool_name": "Read", "tool_input": {"file_path": str(tmp / "w1" / KEPT_OUT / "cases.json")}, "cwd": str(tmp)})
               for role in ("analysis", "coordinating", "curating", "review")))

        # a configuration by git ref, and one whose definition is not valid
        have_git = shutil.which("git") is not None
        if have_git:
            repo2 = tmp / "repo"
            shutil.copytree(REPO / "factory", repo2 / "factory", ignore=shutil.ignore_patterns("__pycache__"))
            shutil.copytree(REPO / "tools", repo2 / "tools", ignore=shutil.ignore_patterns("__pycache__"))
            (repo2 / "examples" / "stand-alone" / "system-trial").mkdir(parents=True)
            shutil.copyfile(REPO / "examples" / "stand-alone" / "system-trial" / "analysis-plan.yaml", repo2 / "examples" / "stand-alone" / "system-trial" / "analysis-plan.yaml")

            def git(*args) -> None:
                subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args], cwd=repo2, check=True, capture_output=True)

            git("init", "-q")
            git("add", "-A")
            git("commit", "-q", "-m", "first")
            git("tag", "before")
            fy = repo2 / "factory" / "factory.yaml"
            was = str(yaml.safe_load(fy.read_text())["version"])  # whatever this definition's version is today
            fy.write_text(fy.read_text().replace(f"version: {was}", f"version: {was}-candidate"))
            suite_file = repo2 / "factory" / "benchmarks" / "built-in-gain" / "suite.yaml"
            suite_file.write_text(suite_file.read_text().replace('  - name: current\n    definition: {path: "."}', '  - name: current\n    definition: {ref: before}'))
            seen = {}

            def spy(name, definition, template, plan):
                seen[name] = (definition, template)
                return stand_in("nobody")(name, definition, template, plan)

            byref = run_suite(repo2 / "factory" / "benchmarks" / "built-in-gain", runner=spy)
            ok("a configuration named by a git ref is that commit's definition, plan and all, taken out into scratch",
               byref["configurations"]["current"]["definition"]["version"] == was and byref["configurations"]["same-again"]["definition"]["version"] == f"{was}-candidate"
               and byref["configurations"]["current"]["definition"]["sha256"] != byref["configurations"]["same-again"]["definition"]["sha256"]
               and repo2 not in seen["current"][0].parents and seen["current"][1].name == "system-trial" and repo2 in seen["same-again"][0].parents)
            suite_file.write_text(suite_file.read_text().replace("definition: {ref: before}", "definition: {ref: no-such-commit}"))
            ok("a ref git does not have makes the suite not comparable, which is not a pass",
               "not validated" in refusal(read_suite, repo2 / "factory" / "benchmarks" / "built-in-gain") or
               "not comparable" == run_suite(repo2 / "factory" / "benchmarks" / "built-in-gain", runner=spy)["comparison"]["result"])
        else:
            ok("a configuration named by a git ref (not checked: git is not here)", True)
            ok("a ref git does not have (not checked: git is not here)", True)
        broken = tmp / "broken"
        shutil.copytree(REPO / "factory", broken / "factory", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(REPO / "tools", broken / "tools", ignore=shutil.ignore_patterns("__pycache__"))
        (broken / "examples" / "stand-alone" / "system-trial").mkdir(parents=True)
        shutil.copyfile(REPO / "examples" / "stand-alone" / "system-trial" / "analysis-plan.yaml", broken / "examples" / "stand-alone" / "system-trial" / "analysis-plan.yaml")
        s = broken / "factory" / "scorers" / "plan-is-clear" / "scorer.md"
        s.write_text(s.read_text().replace("reads: [request, plan, known-answer-tests]", "reads: [request, plan, finding]"))
        ok("a suite in a definition that is not valid is not run", "a suite is run from a valid definition" in refusal(read_suite, broken / "factory" / "benchmarks" / "built-in-gain"))
        ok("the self-test leaves no bytecode folder beside the tools", not (HERE / "__pycache__").exists())
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [n for n, good in results if not good]
    for n in failed:
        print("FAIL:", n)
    print(f"selftest: {'PASS' if not failed else 'FAIL'} ({len(results) - len(failed)} of {len(results)})")
    return 0 if not failed else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, allow_abbrev=False)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", allow_abbrev=False)
    r.add_argument("--suite", type=Path, required=True, help="a suite folder: factory/benchmarks/<suite>")
    r.add_argument("--out", type=Path, default=None, help="also write the report here (outside the repository)")
    r.add_argument("--work", type=Path, default=None, help="where an acceptance run writes its `acceptance-cases` folder (default: a new scratch folder)")
    c = sub.add_parser("cases", allow_abbrev=False)
    c.add_argument("--suite", type=Path, required=True)
    c.add_argument("--work", type=Path, default=None)
    sub.add_parser("selftest", allow_abbrev=False)
    a = ap.parse_args()
    try:
        sf.refuse_dirty_environment()
    except Refused as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2
    return {"run": cmd_run, "cases": cmd_cases, "selftest": lambda _: selftest()}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
