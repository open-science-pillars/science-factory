#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""known_answer_tests: the known-answer tests for a satellite-versus-gauge
gain claim.

Runs synthetic test cases with the truth put in by hand (test_cases.py)
through the plan's handling and the SANCTIONED confrontation executor,
unmodified and end to end (confront.py), then through the candidate gain
estimate (gain.py), and measures what real data can never show: how often
the interval covers the value put in, and how often the plan's decision
rule gives the right answer in cases where the idea is true, where it is
false, and right at the difference that matters, with and without trouble
put in alongside. This is mutation testing moved from code to claims: a
decision rule that cannot fail when the idea is false is not a test, and a
false-confirmation rate measured only far from the difference that matters
is not a rate.

Three groups of test case, and what each is for:
  required        the hard cases the claim must survive (a kind case, a
                  drifting satellite, gross errors, flagged low-stage
                  faults, autocorrelated error), each at the true gain and
                  right at the difference that matters on both sides; cases
                  where the idea is far from true; and a processing change,
                  which the plan's guard must refuse. The criteria the lock
                  requires apply here.
  beyond-limits   cases the method is known not to survive, reported and
                  never required, so the finding can say so (unflagged
                  low-stage faults, very strong autocorrelation, a bending
                  relation, error that grows with stage, a noisier
                  satellite).
  curve           the rule's outcome against the gain put in: what the
                  opening can and cannot tell apart.

With --sampling the test cases are built on the real pass times, quality
flags and gauge record of a window, so the power reported is power for the
experiment that will run. Those are observation metadata on the condition
the study's plan states: the screen, the pairing and the model are fixed,
so none of them can move the gain without the satellite elevations.

The method is never given the answer, and it does not run in the process
that holds it. Each test case is made as two parts (test_cases.py), the
data the method reads and what was put in. This process keeps what was put
in and does the scoring. The method (confront.py) runs as a process of its
own, started fresh for each batch of cases with a short built environment
and no input: it is given the data of the batch, one case to a line, and
the planned handling, and it writes one line back for each case. It is not
given what was put in, the seed, a case's number, or which configuration a
case belongs to: every batch is a shuffle of all the configurations, drawn
from operating-system entropy, so a method cannot pool the cases that
share a truth. (A method that carried anything from one case to the next
would give numbers that change from run to run, and --check would fail.)

What that separation protects against: a method that looks for the answer
where it runs. Its own stack, every object in its memory, its arguments,
its environment and the file it is given hold no trace of what was put in
(--selftest searches all of them from inside). What it does not protect
against: a method written to recognise a known-answer test case and behave
differently on it. The seed and the configurations are published in this
file and the test cases say that they are synthetic, so such a method
could make the cases again for itself; and a process can ask the operating
system about another process of the same user. The answer to both is the
one the lock gives for all code: the method is read by the people locking
it, and it is bound by checksum, so the method that was read is the method
that ran here and the method that runs at the opening.

Deterministic for a given seed, case count and platform; no network; no
language model. The receipt (a run receipt: the record a run writes, with
its code and inputs by checksum and every number it produced) echoes the
rule it exercised, so the lock can refuse evidence that was produced for
some other rule.

Usage:
  known_answer_tests.py --executor PATH/load_swot_confrontation.py
      [--plan analysis-plan.yaml --rule ID] [--sampling TREE.json]
      [--cases 2000] [--seed 20261125] [--difference-that-matters 0.05]
      [--jobs N] --out known-answers.json
  known_answer_tests.py --executor PATH [--sampling TREE.json]
      --check known-answers.json
  known_answer_tests.py --selftest [--executor PATH]
"""
import sys

sys.dont_write_bytecode = True  # this package leaves no bytecode beside its sources
if __name__ == "__main__" and not sys.flags.safe_path and sys.path:
    del sys.path[0]  # the script's own folder must not shadow a module imported below

import argparse
import hashlib
import importlib.util
import json
import math
import operator
import os
import random
import secrets
import statistics
import subprocess
import tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

# Whatever sits in a __pycache__ folder beside the files loaded below is never read in their place: Python is
# pointed at a cache folder that does not exist. (Run by the study tool, it already is.)
sys.pycache_prefix = os.path.join(tempfile.gettempdir(), "sf-no-bytecode-" + secrets.token_hex(16))
HERE = Path(__file__).resolve().parent


def neighbour(name: str):
    """Load a file of this folder by its path, so what runs is the file the lock hashed and nothing that
    shares its name somewhere else on the import path."""
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


make_case = neighbour("test_cases").make_case
METHOD = HERE / "confront.py"  # the method under test: run as a process of its own, never loaded into this one
BATCH = 1000  # the most cases one method process is given

OPS = {">=": operator.ge, "<=": operator.le, ">": operator.gt, "<": operator.lt, "==": operator.eq}
DIFFERENCES = (0.03, 0.05, 0.08, 0.10)
# the criteria the lock requires of the plan's rule
CRITERIA = {"coverage_low": 0.90, "coverage_high": 0.985, "max_false_at_edge": 0.05, "min_power": 0.80,
            "max_false_confirm_far": 0.01, "processing_change_refused": 1.0}
HARD_CASES = {  # the idea is true or false, and something else is also going on
    "kind": {},
    "drift": {"drift_m_per_yr": 0.5},
    "gross": {"outlier_frac": 0.05},
    "lowstage-flagged": {"lowstage_fault_frac": 0.25},
    "autocorrelated": {"rho_sat": 0.6},
}
BEYOND_LIMITS = {
    "lowstage-unflagged": {"lowstage_fault_frac": 0.25, "fault_flagged": 0.0},
    "strong-autocorrelation": {"rho_sat": 0.9},
    "bend": {"bend_per_m": -0.013},
    "error-grows-with-stage": {"het": 0.5},
    "noisier": {"sigma_sat": 0.24},
}


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def default_rule(m: float) -> dict:
    lo, hi = round(1 - m, 6), round(1 + m, 6)
    return {"supported_if": [{"field": "gain.ci_low", "op": ">=", "value": lo},
                             {"field": "gain.ci_high", "op": "<=", "value": hi}],
            "refuted_if": [[{"field": "gain.ci_high", "op": "<", "value": lo}],
                           [{"field": "gain.ci_low", "op": ">", "value": hi}]]}


def holds(conds: list, receipt: dict) -> bool:
    try:
        for c in conds:
            v = receipt
            for part in c["field"].split("."):
                v = v[part]
            if not isinstance(v, (int, float)) or not math.isfinite(v) or not OPS[c["op"]](float(v), float(c["value"])):
                return False
        return True
    except (KeyError, TypeError, ValueError):
        return False


def outcome(rule: dict, receipt: dict) -> str:
    """The plan's three-valued rule; a refusal is inconclusive."""
    if "refused" in receipt:
        return "inconclusive"
    if holds(rule["supported_if"], receipt):
        return "supported"
    if any(holds(g, receipt) for g in rule["refuted_if"]):
        return "refuted"
    return "inconclusive"


def build_configs(m: float, cases: int, passes: int | None) -> list:
    lo, hi, far_lo, far_hi = round(1 - m, 4), round(1 + m, 4), round(1 - 2 * m, 4), round(1 + 2 * m, 4)
    base = {"n_passes": passes} if passes else {}
    small = max(cases // 4, 50)
    out = []
    for name, over in HARD_CASES.items():
        for label, g in (("true", 1.0), ("edge-low", lo), ("edge-high", hi)):
            out.append((f"required/{name}/{label}", {**base, **over, "gain": g}, cases))
    out.append(("required/kind/far-low", {**base, "gain": far_lo}, cases))
    out.append(("required/kind/far-high", {**base, "gain": far_hi}, cases))
    out.append(("required/processing-change", {**base, "gain": 1.0, "crid_change_frac": 0.32, "step_m": 0.5}, small))
    for name, over in BEYOND_LIMITS.items():
        for label, g in (("true", 1.0), ("edge-low", lo)):
            out.append((f"beyond-limits/{name}/{label}", {**base, **over, "gain": g}, small))
    for k in range(-6, 7):
        out.append((f"curve/{round(1 + k * m / 2, 4):.4f}", {**base, "gain": round(1 + k * m / 2, 4)}, small))
    return out


_SAMPLING: dict = {}


def method_environment(scratch: Path) -> dict:
    """What the method's process is given of this one's environment: where programs, the home folder and
    temporary files are, the language and the time zone, and the three Python settings the study tool gives
    every command. Nothing else arrives, so nothing this process was told can arrive that way."""
    env = {k: os.environ[k] for k in ("PATH", "HOME", "LANG", "LC_ALL", "LC_CTYPE", "TZ", "TMPDIR") if k in os.environ}
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1", PYTHONPYCACHEPREFIX=str(scratch / "no-bytecode"))
    return env


def deal(configs: list, jobs: int = 1) -> list:
    """Every case of every configuration as (configuration, case number), shuffled together by
    operating-system entropy and cut into batches: at most BATCH cases each, and several batches for each
    job that runs at once. The shuffle decides only which process works on which case: results are put back
    by configuration and case number, so the numbers do not depend on it."""
    cards = [(i, w) for i, (_, _, n) in enumerate(configs) for w in range(n)]
    random.SystemRandom().shuffle(cards)
    size = min(BATCH, max(50, -(-len(cards) // (4 * max(jobs, 1)))))
    return [cards[k:k + size] for k in range(0, len(cards), size)]


def method_batch(job: tuple) -> list:
    """Make one batch of cases, hand their data to a method process, and return what it wrote back, case by
    case. What was put in stays in this process: the method's process is started fresh (never forked from
    this one, which would copy its memory), with a built environment, no input, an empty working folder, and
    arguments that name the executor, the planned handling and two files with random names."""
    cards, overs, seed, executor, sampling_path, handling, method, rule = job
    if sampling_path and sampling_path not in _SAMPLING:
        _SAMPLING[sampling_path] = json.loads(Path(sampling_path).read_text())
    sampling = _SAMPLING.get(sampling_path)
    with tempfile.TemporaryDirectory(prefix="known-answer-cases-") as tmp:
        tmp = Path(tmp)
        given, back, work = tmp / f"{secrets.token_hex(8)}.jsonl", tmp / f"{secrets.token_hex(8)}.jsonl", tmp / "work"
        work.mkdir()
        with given.open("w") as f:
            for index, w in cards:
                case, _ = make_case(seed + 100003 * index + w, sampling=sampling, **overs[index])  # the data, never what was put in
                f.write(json.dumps(case) + "\n")
        argv = [sys.executable, str(method), "--executor", str(executor), "--batch", str(given), "--out", str(back),
                "--tolerance-minutes", str(handling["tolerance"]), "--screen-reach-q", str(handling["screen_q"])]
        argv += ["--require-crid"] if handling["require_crid"] else []
        ran = subprocess.run(argv, cwd=work, env=method_environment(tmp), stdin=subprocess.DEVNULL, capture_output=True, text=True)
        lines = back.read_text().splitlines() if ran.returncode == 0 and back.is_file() else []
        if len(lines) != len(cards):
            raise RuntimeError(f"the method's process did not report on every case it was given (exit {ran.returncode}, "
                               f"{len(lines)} of {len(cards)} cases): " + ran.stderr.strip()[-400:])
    return [(index, w, summary(json.loads(line), rule)) for (index, w), line in zip(cards, lines)]


def summary(c: dict, rule: dict) -> dict:
    """What scoring needs of one case's result: the rule's outcome on it and a few numbers. A result this
    process cannot read that way is passed on whole (the --selftest's stand-in method writes such lines)."""
    if not isinstance(c.get("screen"), dict):
        return c
    s = {"outcome": outcome(rule, c), "excluded": c["screen"]["passes_excluded"], "refused": c.get("refused")}
    if "refused" not in c:
        ch = c["_executor"]["confrontation_on_changes"]
        s.update(gain={k: c["gain"][k] for k in ("gain", "ci_low", "ci_high", "n")},
                 mean_error_m=ch["mean_error_m"], mean_error_95pct=ch["mean_error_95pct"])
    return s


def run_method(configs: list, seed: int, executor: Path, sampling: Path | None, handling: dict, jobs: int,
               rule: dict, method: Path = METHOD) -> dict:
    """What the method reported for every case, summed up for scoring, by (configuration, case number)."""
    overs = [over for _, over, _ in configs]
    executor, method = Path(executor).resolve(), Path(method).resolve()  # the method's process starts in a folder of its own
    todo = [(cards, overs, seed, str(executor), str(sampling) if sampling else None, handling, str(method), rule)
            for cards in deal(configs, jobs)]
    reported = {}
    try:
        if jobs > 1:
            with ProcessPoolExecutor(max_workers=jobs) as pool:
                parts = list(pool.map(method_batch, todo))
        else:
            parts = [method_batch(j) for j in todo]
    except RuntimeError as e:
        raise SystemExit(f"known-answer tests: {e}")
    for part in parts:
        for index, w, c in part:
            reported[(index, w)] = c
    return reported


def score(over: dict, n: int, reported: list) -> dict:
    """Score one configuration: what the method reported for its cases, in case order, against what was put in."""
    counts = {"supported": 0, "refuted": 0, "inconclusive": 0}
    gains, halves, pairs, excluded, cover, refused, mixed = [], [], [], [], 0, 0, 0
    by_difference = {str(m): 0 for m in DIFFERENCES}
    me, me_zero, me_half = [], 0, []
    for c in reported:
        counts[c["outcome"]] += 1
        excluded.append(c["excluded"])
        if c["refused"] is not None:
            refused += 1
            mixed += c["refused"].startswith("the window mixes processing identifiers")
            continue
        g = c["gain"]
        gains.append(g["gain"])
        halves.append((g["ci_high"] - g["ci_low"]) / 2)
        pairs.append(g["n"])
        cover += g["ci_low"] <= over["gain"] <= g["ci_high"]
        for m in DIFFERENCES:
            by_difference[str(m)] += g["ci_low"] >= 1 - m and g["ci_high"] <= 1 + m
        me.append(c["mean_error_m"])
        lo, hi = c["mean_error_95pct"]
        me_zero += lo <= 0.0 <= hi
        me_half.append((hi - lo) / 2)
    k = len(gains)
    res = {"put_in": over, "cases": n, "refused": refused, "refused_for_mixed_identifiers": mixed,
           "rule_outcomes": {o: round(v / n, 4) for o, v in counts.items()},
           "passes_excluded_by_screen_mean": round(statistics.fmean(excluded), 2)}
    if k >= 2:
        res.update({
            "gain_mean": round(statistics.fmean(gains), 4), "gain_sd": round(statistics.stdev(gains), 4),
            "interval_halfwidth_mean": round(statistics.fmean(halves), 4), "pairs_mean": round(statistics.fmean(pairs), 1),
            "interval_covers_value_put_in_rate": round(cover / k, 4),
            "supported_at_difference": {m: round(v / n, 4) for m, v in by_difference.items()},
            "existing_mean_change_error": {
                "interval_contains_zero_rate": round(me_zero / k, 4),
                "statistic_sd_across_cases_m": round(statistics.stdev(me), 4),
                "reported_halfwidth_over_1.96_m": round(statistics.fmean(me_half) / 1.96, 4)}})
    return res


def run(executor: Path, cases: int, seed: int, difference: float, rule: dict, rule_id: str,
        sampling: Path | None, passes: int | None, jobs: int, handling: dict) -> dict:
    probe = {"gain": {"ci_low": 1 - difference, "ci_high": 1 + difference}}
    wide = {"gain": {"ci_low": 1 - difference - 0.01, "ci_high": 1 + difference}}
    if outcome(rule, probe) != "supported" or outcome(rule, wide) == "supported":
        raise SystemExit("the plan's rule is not the equivalence band these test cases are built around: "
                         f"an interval of exactly 1 +/- {difference} must be supported and a wider one must not")
    configs = build_configs(difference, cases, passes)
    reported = run_method(configs, seed, executor, sampling, handling, jobs, rule)
    cfg = {name: score(over, n, [reported[(i, w)] for w in range(n)]) for i, (name, over, n) in enumerate(configs)}
    out = {"experiment": "known-answer tests", "cases_per_required_config": cases, "seed": seed,
           "difference_that_matters": difference,
           "passes": passes, "criteria": CRITERIA, "planned_handling": handling,
           "cases_built_on": ({"sampling": sampling.name, "sha256": sha(sampling)} if sampling else "a synthetic river"),
           "code": {"executor": {"path": executor.name, "sha256": sha(executor)},
                    "gain_prototype": {"sha256": sha(HERE / "gain.py")},
                    "confront_prototype": {"sha256": sha(HERE / "confront.py")},
                    "test_case_generator": {"sha256": sha(HERE / "test_cases.py")},
                    "this_experiment": {"sha256": sha(Path(__file__))}},
           "configs": cfg}

    def rate(name: str, what: str) -> float:
        return cfg[name]["rule_outcomes"][what]

    hard = list(HARD_CASES)
    kind = cfg["required/kind/true"]
    r = {
        "tested_rule": json.loads(json.dumps(rule)),
        "coverage_when_true": kind["interval_covers_value_put_in_rate"],
        "coverage_min_over_hard_cases": min(cfg[f"required/{n}/true"]["interval_covers_value_put_in_rate"] for n in hard),
        "false_confirm_at_edge_max": max(rate(f"required/{n}/{e}", "supported") for n in hard for e in ("edge-low", "edge-high")),
        "false_refute_at_edge_max": max(rate(f"required/{n}/{e}", "refuted") for n in hard for e in ("edge-low", "edge-high")),
        "power_to_support_when_true": rate("required/kind/true", "supported"),
        "power_to_support_min_over_hard_cases": min(rate(f"required/{n}/true", "supported") for n in hard),
        "power_to_refute_when_false": min(rate("required/kind/far-low", "refuted"), rate("required/kind/far-high", "refuted")),
        "false_confirm_when_false": max(rate("required/kind/far-low", "supported"), rate("required/kind/far-high", "supported")),
        "processing_change_refused_rate": round(cfg["required/processing-change"]["refused_for_mixed_identifiers"]
                                                / cfg["required/processing-change"]["cases"], 4),
    }
    far, drift = cfg["required/kind/far-low"], cfg["required/drift/true"]
    old = kind["existing_mean_change_error"]
    out["rules"] = {
        rule_id: r,
        "existing mean-change-error interval contains zero (for comparison, never required)": {
            "when_the_gain_is_1.00": old["interval_contains_zero_rate"],
            f"when_the_gain_is_{far['put_in']['gain']}": far["existing_mean_change_error"]["interval_contains_zero_rate"],
            "when_drifting_0.5_m_per_yr": drift["existing_mean_change_error"]["interval_contains_zero_rate"],
            "reported_sd_over_actual_sd": round(old["reported_halfwidth_over_1.96_m"] / old["statistic_sd_across_cases_m"], 1)}}
    out["power_curve"] = [{"gain_put_in": cfg[n]["put_in"]["gain"], **cfg[n]["rule_outcomes"]}
                          for n in cfg if n.startswith("curve/")]
    out["what_the_sample_resolves"] = {
        "supported_when_the_gain_is_1.00_by_difference_that_matters": kind["supported_at_difference"],
        "interval_halfwidth_mean": kind["interval_halfwidth_mean"], "pairs_mean": kind["pairs_mean"]}
    out["beyond_limits_cases"] = {n.split("/", 1)[1]: {"coverage": cfg[n].get("interval_covers_value_put_in_rate"),
                                                       **cfg[n]["rule_outcomes"]} for n in cfg if n.startswith("beyond-limits/")}
    checks = {
        "the interval covers the gain put in for the kind case, neither too rarely nor too often":
            CRITERIA["coverage_low"] <= r["coverage_when_true"] <= CRITERIA["coverage_high"],
        "coverage holds in every hard case": r["coverage_min_over_hard_cases"] >= CRITERIA["coverage_low"],
        "the rule rarely confirms right at the difference that matters, in any hard case":
            r["false_confirm_at_edge_max"] <= CRITERIA["max_false_at_edge"],
        "the rule rarely refutes right at the difference that matters, in any hard case":
            r["false_refute_at_edge_max"] <= CRITERIA["max_false_at_edge"],
        "the rule can pass: a case where the idea is true is supported": r["power_to_support_when_true"] >= CRITERIA["min_power"],
        "the rule can fail: a case where the idea is false is refuted": r["power_to_refute_when_false"] >= CRITERIA["min_power"],
        "a case where the idea is false is almost never confirmed": r["false_confirm_when_false"] <= CRITERIA["max_false_confirm_far"],
        "a processing change inside the window is refused":
            r["processing_change_refused_rate"] >= CRITERIA["processing_change_refused"]}
    out["readiness"] = {"checks": checks, "verdict": "PASS" if all(checks.values()) else "FAIL"}
    return out


def planned_rule(plan_path: Path, rule_id: str | None) -> tuple:
    import yaml

    class NoDuplicateKeys(yaml.SafeLoader):  # YAML would keep the last of two `rules:` blocks and say nothing
        pass

    def mapping(loader, node):
        keys = [loader.construct_object(k, deep=True) for k, _ in node.value]
        twice = sorted({str(k) for k in keys if keys.count(k) > 1})
        if twice:
            raise SystemExit(f"{plan_path} gives the key `{twice[0]}` twice; say it once")
        return loader.construct_mapping(node, deep=True)

    NoDuplicateKeys.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)
    plan = yaml.load(plan_path.read_text(), Loader=NoDuplicateKeys)
    rules = plan["rules"]
    r = next((x for x in rules if x["id"] == rule_id), None) if rule_id else next(x for x in rules if x.get("role") == "primary")
    if r is None:
        raise SystemExit(f"no rule `{rule_id}` in {plan_path}")
    return {"supported_if": r["supported_if"], "refuted_if": r["refuted_if"]}, r["id"]


# A stand-in method for this file's own check. It is started exactly as the method is, and it looks everywhere a
# method could look without asking the operating system about another process: its arguments, its environment,
# every frame of its stack, every object its interpreter holds, and the file it is given. It carries only the
# digests of what the harness knows, so it can recognise a secret without holding one.
SEARCHER = '''import gc, hashlib, json, os, re, sys

NEEDLES = __NEEDLES__  # label: sha256 of the text of something the harness knows and the method must not


def digest(x) -> str:
    return hashlib.sha256((repr(x) if isinstance(x, float) else str(x)).encode()).hexdigest()


def search(*texts) -> list:
    wanted, found, seen = {v: k for k, v in NEEDLES.items()}, set(), set()

    def number(x):
        if digest(x) in wanted:
            found.add(wanted[digest(x)])

    def text(s):
        for token in set(re.findall(r"[0-9][0-9.]*", s)):
            number(token)

    def walk(x, depth=0):
        if isinstance(x, bool) or x is None:
            return
        if isinstance(x, (int, float)):
            return number(x)
        if isinstance(x, str):
            return text(x) if len(x) < 20000 else None
        if depth > 12 or id(x) in seen:
            return
        seen.add(id(x))
        if isinstance(x, dict):
            for k, v in list(x.items()):
                walk(k, depth + 1), walk(v, depth + 1)
        elif isinstance(x, (list, tuple, set, frozenset)):
            for v in list(x):
                walk(v, depth + 1)
        elif isinstance(getattr(x, "__dict__", None), dict):
            walk(x.__dict__, depth + 1)

    walk(list(sys.argv))
    walk(dict(os.environ))
    for frame in list(sys._current_frames().values()):
        while frame is not None:
            walk(dict(frame.f_locals)), walk(frame.f_globals)
            frame = frame.f_back
    for obj in gc.get_objects():
        walk(obj)
    for s in texts:
        text(s)
    return sorted(found)


if __name__ == "__main__":
    args = dict(zip(sys.argv[1::2], sys.argv[2::2]))
    given = open(args["--batch"]).read()
    report = {"found": search(given), "carries_put_in": "put_in" in given, "environment": sorted(os.environ),
              "arguments": [a for a in sys.argv[1:] if a.startswith("--")], "input_is_empty": sys.stdin.read() == "",
              "folder_is_empty": os.listdir(".") == []}
    with open(args["--out"], "w") as back:
        for _ in given.splitlines():
            back.write(json.dumps(report) + "\\n")
'''


def selftest(executor: Path | None) -> int:
    """This file's own checks. The first two need nothing but this folder; the third needs the executor."""
    results = []

    def check(name: str, ok: bool) -> None:
        results.append((name, bool(ok)))
        print(("PASS  " if ok else "FAIL  ") + name)

    # what the harness knows and the method must not: values no test case's data could hold by chance
    seed, over = 918273645546372, {"gain": 0.91370001, "drift_m_per_yr": 0.42420001}
    configs = [("probe/one", over, 3), ("probe/two", {"gain": 1.08130001}, 3)]
    needles = {"the gain put in": over["gain"], "the drift put in": over["drift_m_per_yr"], "the seed": seed,
               "a case's own seed": seed + 100003 * 0 + 1, "another gain put in": 1.08130001}
    digests = {k: hashlib.sha256((repr(v) if isinstance(v, float) else str(v)).encode()).hexdigest() for k, v in needles.items()}
    handling = {"tolerance": 15, "screen_q": 2, "require_crid": False}
    with tempfile.TemporaryDirectory() as tmp:
        searcher = Path(tmp) / "searcher.py"
        searcher.write_text(SEARCHER.replace("__NEEDLES__", json.dumps(digests)))
        os.environ["KNOWN_ANSWER_SEED"] = str(seed)  # as if a careless caller had left the seed in the environment
        try:
            reported = run_method(configs, seed, Path(tmp) / "no-executor", None, handling, 1, default_rule(0.05), method=searcher)
        finally:
            del os.environ["KNOWN_ANSWER_SEED"]
        saw = list(reported.values())
        check("a method that looks for the answer in its own process finds nothing: not in its arguments, its environment, "
              "its stack, any object in its memory, or the file it is given",
              len(saw) == 6 and all(r["found"] == [] and r["carries_put_in"] is False for r in saw))
        check("the method's process is started with the executor, two files, the planned handling and nothing else: a built "
              "environment, no input, an empty folder",
              all(r["arguments"] == ["--executor", "--batch", "--out", "--tolerance-minutes", "--screen-reach-q"]
                  and set(r["environment"]) - {"LC_CTYPE"} <= {"PATH", "HOME", "LANG", "LC_ALL", "TZ", "TMPDIR", "PYTHONDONTWRITEBYTECODE",
                                                                 "PYTHONNOUSERSITE", "PYTHONPYCACHEPREFIX"}
                  and r["input_is_empty"] and r["folder_is_empty"] for r in saw))
        spec = importlib.util.spec_from_file_location("searcher", searcher)
        here = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(here)

        def where_the_truth_is(put_in: dict, the_seed: int) -> list:  # the same search, in the process that holds the truth
            return here.search()
        check("the same search, run in this process where the truth is kept, finds the gain, the drift and the seed",
              {"the gain put in", "the drift put in", "the seed"} <= set(where_the_truth_is(over, seed)))
    with tempfile.TemporaryDirectory() as tmp:  # the method's own refusal of an input that carries the answer
        tmp = Path(tmp)
        case, put_in = make_case(3, gain=0.9)
        (tmp / "stub.py").write_text("def main():\n    return 0\n")  # stands where the executor would: never reached
        (tmp / "told.json").write_text(json.dumps({**case, "put_in": put_in}))
        (tmp / "told.jsonl").write_text(json.dumps(case) + "\n" + json.dumps({**case, "put_in": put_in}) + "\n")
        runs = [subprocess.run([sys.executable, str(METHOD), "--executor", str(tmp / "stub.py"), how, str(tmp / given), "--out", str(tmp / out)],
                               env=method_environment(tmp), stdin=subprocess.DEVNULL, capture_output=True, text=True)
                for how, given, out in (("--inputs", "told.json", "one.json"), ("--batch", "told.jsonl", "many.jsonl"))]
        confront = neighbour("confront")  # loaded into this process to call its function directly; nothing is run through it
        try:
            confront.confront_tree({**case, "put_in": put_in}, None, tmp)
            as_function = False
        except ValueError as e:
            as_function = "put_in" in str(e)
        check("the method refuses an input that carries what was put in: as a single input, as a line of a batch, and when "
              "its function is called directly",
              [r.returncode for r in runs] == [4, 4] and all("never given the answer" in r.stderr for r in runs)
              and not (tmp / "one.json").exists() and as_function)
    many = build_configs(0.05, 200, None)
    batches = deal(many, 4)
    cards = sorted(c for b in batches for c in b)
    check("every case is dealt once, and every batch mixes the configurations",
          cards == [(i, w) for i, (_, _, n) in enumerate(many) for w in range(n)]
          and all(len({i for i, _ in b}) >= 10 for b in batches) and all(len(b) <= BATCH for b in batches))
    if executor:
        few = [(name, o, 12) for name, o, _ in build_configs(0.05, 200, None)[:4]]
        rule = default_rule(0.05)
        apart = run_method(few, 7, executor, None, handling, 1, rule)
        confront = neighbour("confront")  # loaded into this process for the comparison only
        mod, same = confront.load_executor(executor), True
        with tempfile.TemporaryDirectory() as tmp:
            for i, (_, o, n) in enumerate(few):
                for w in range(n):
                    case, _ = make_case(7 + 100003 * i + w, **o)
                    c = confront.confront_tree(case, mod, Path(tmp), **handling)
                    same = same and apart[(i, w)] == json.loads(json.dumps(summary(c, rule)))
        check("the method run as a process of its own reports, case for case, what it reports when run in this process",
              same and len(apart) == 48)
    good = all(ok for _, ok in results)
    print(f"selftest: {'PASS' if good else 'FAIL'} ({sum(ok for _, ok in results)} of {len(results)})")
    return 0 if good else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--executor", type=Path)
    ap.add_argument("--selftest", action="store_true", help="this file's own checks; with --executor, one more")
    ap.add_argument("--plan", type=Path, help="read the rule to exercise from this analysis plan")
    ap.add_argument("--rule", help="rule id (default: the primary rule)")
    ap.add_argument("--sampling", type=Path, help="build the test cases on the pass times and gauge record of this tree")
    ap.add_argument("--passes", type=int, help="passes per synthetic test case (default: the generator's)")
    ap.add_argument("--cases", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20261125)
    ap.add_argument("--difference-that-matters", type=float, default=0.05)
    ap.add_argument("--tolerance-minutes", type=int, default=15, help="the plan's handling, as in the opening's command")
    ap.add_argument("--screen-reach-q", type=int, default=2, help="the plan's handling, as in the opening's command")
    ap.add_argument("--require-crid", action="store_true", help="the plan's handling, as in the opening's command")
    ap.add_argument("--jobs", type=int, default=min(8, os.cpu_count() or 1))
    ap.add_argument("--out", type=Path)
    ap.add_argument("--check", type=Path, help="run again and require agreement with a stored receipt")
    a = ap.parse_args()
    if a.selftest:
        return selftest(a.executor)
    if not a.executor:
        ap.error("--executor is required: the sanctioned executor the method wraps")
    if not a.executor.is_file():
        print(f"known-answer tests: refused. The executor {a.executor} is not there; it ships with the capability it belongs "
              "to, so check that capability out where the plan's roots point. Nothing was run", file=sys.stderr)
        return 2
    if a.check:
        old = json.loads(a.check.read_text())
        rid = next(iter(old["rules"]))
        built_on = old["cases_built_on"]
        if isinstance(built_on, dict) and (not a.sampling or sha(a.sampling) != built_on["sha256"]):
            print(f"check: FAIL (the receipt's test cases were built on {built_on['sampling']}; pass that file with --sampling)")
            return 1
        new = run(a.executor, old["cases_per_required_config"], old["seed"], old["difference_that_matters"],
                  old["rules"][rid]["tested_rule"],
                  rid, a.sampling if isinstance(built_on, dict) else None, old.get("passes"), a.jobs,
                  old["planned_handling"])
        same = json.dumps(new, sort_keys=True) == json.dumps(old, sort_keys=True)
        print("check:", "PASS (recomputed identically)" if same else "FAIL (the receipt does not reproduce)")
        return 0 if same and new["readiness"]["verdict"] == "PASS" else 1
    rule, rid = (planned_rule(a.plan, a.rule) if a.plan
                 else (default_rule(a.difference_that_matters), a.rule or "gain-equivalence"))
    handling = {"tolerance": a.tolerance_minutes, "screen_q": a.screen_reach_q, "require_crid": a.require_crid}
    rep = run(a.executor, a.cases, a.seed, a.difference_that_matters, rule, rid, a.sampling, a.passes, a.jobs, handling)
    if a.out:
        a.out.write_text(json.dumps(rep, indent=1))
    show = {k: v for k, v in rep["rules"][rid].items() if k != "tested_rule"}
    print(json.dumps({"rule": rid, **show, "readiness": rep["readiness"]}, indent=1))
    return 0 if rep["readiness"]["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
