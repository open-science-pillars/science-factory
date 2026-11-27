#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""confront: apply the plan's quality screen, run the pairing step the
plan names, then the gain estimate, and write one receipt that binds all
three.

PROTOTYPE, like gain.py, and part of the same built-in method. The pairing
step is a parameter (--executor): the system trial that ships here names
this repository's own (methods/built-in-pairing/pair_records.py), and a
study of a real record names the script its own discipline keeps for the
purpose. The same function serves the known-answer tests, the working data
and the one opening of the held-out data, which is this procedure's
version of test-as-you-fly: the code the lock covers is the code that
reads the held-out data.

The input tree keeps the names of the method's first use, a satellite
record of river height against a river gauge (`satellite.rows`, `gauge`,
`reach_q` for the quality flag, `crid` for the processing identifier).
They are names only; any two records written in that shape are read.

What happens to an input tree, in order:
  1. the quality screen: passes flagged degraded or worse (reach_q at or
     above the plan's threshold) are excluded before pairing, and the
     count is reported. One degraded pass at the lowest stage of a year
     can carry most of the residual sum of squares.
  2. the processing guard: a window that mixes processing identifiers is
     refused, because an offset between them leaks into the gain.
  3. the pairing step, unmodified, pairs the passes of the first record
     with the readings of the second.
  4. the gain estimate (gain.py), plus two descriptive gains for the lower
     and upper half of stage, which no rule uses.

A refusal (too few pairs, mixed identifiers, the executor declining) is
written into the receipt as `refused`. For an opening of held-out data a
refusal is a result, planned as inconclusive, so the command still exits 0
when asked to treat it that way.

The method is never given the answer. A known-answer test case is two
parts (test_cases.py): the data, which is what arrives here, and what was
put in, which stays with whoever scores the method. An input that carries
a `put_in` block is refused outright.

The known-answer tests run this file as a process of its own (--batch): it
is started with the data of many test cases, one to a line, the planned
handling, and nothing else, and it writes one line back for each. What was
put in, and the seed the cases were made from, are in another process. The
same function, confront_tree, serves a batch and a single input tree.

The receipt this writes is a run receipt: the record a run writes, with its
code and inputs by checksum and every number it produced.

Usage:
  confront.py --executor PATH/pair_records.py --inputs TREE.json --out receipt.json
              [--screen-reach-q 2] [--require-crid] [--refusal-is-a-result]
  confront.py --executor PATH/pair_records.py --batch CASES.jsonl --out RESULTS.jsonl
              [--screen-reach-q 2] [--require-crid]
"""
import sys

sys.dont_write_bytecode = True  # this package leaves no bytecode beside its sources
if __name__ == "__main__" and not sys.flags.safe_path and sys.path:
    del sys.path[0]  # the script's own folder must not shadow a module imported below

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import secrets
import tempfile
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


MIN_PAIRS, gain_block = neighbour("gain").MIN_PAIRS, neighbour("gain").gain_block

_EXECUTORS: dict = {}


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load_executor(path: Path):
    """The pairing step the plan names, as a module: the file is the one on disk,
    unmodified, and it is run through its own command line entry point."""
    key = str(Path(path).resolve())
    if key not in _EXECUTORS:
        spec = importlib.util.spec_from_file_location("pairing_step", key)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _EXECUTORS[key] = mod
    return _EXECUTORS[key]


def run_executor(mod, tree: dict, tolerance: int, scratch: Path) -> tuple:
    """Call the executor's main() exactly as its command line would."""
    inp, out = scratch / "inputs.json", scratch / "executor-receipt.json"
    inp.write_text(json.dumps(tree))
    out.unlink(missing_ok=True)
    argv, err = sys.argv, io.StringIO()
    sys.argv = [str(mod.__file__), "--inputs", str(inp), "--tolerance-minutes", str(tolerance), "--out", str(out)]
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            code = mod.main()
    except SystemExit as e:
        code = e.code
    finally:
        sys.argv = argv
    if code not in (0, None) or not out.is_file():
        return None, (err.getvalue().strip() or f"exit {code}")[-300:]
    return json.loads(out.read_text()), ""


def _flag(row: dict) -> int | None:
    try:
        return int(str(row["reach_q"]))
    except (KeyError, ValueError):
        return None


def confront_tree(tree: dict, mod, scratch: Path, tolerance: int = 15, screen_q: int = 2,
                  require_crid: bool = False) -> dict:
    if "put_in" in tree:
        raise ValueError("this input carries what was put in (`put_in`); the method is never given the answer")
    rows, rbp = tree["satellite"]["rows"], tree["gauge"]["readings_by_pass"]
    keep = [i for i, r in enumerate(rows) if _flag(r) is None or _flag(r) < screen_q]
    out = {"screen": {"rule": f"passes with reach_q at or above {screen_q} are excluded before pairing",
                      "passes_offered": len(rows), "passes_excluded": len(rows) - len(keep),
                      "passes_without_a_flag": sum(1 for r in rows if _flag(r) is None)}}
    crids = sorted({rows[i]["crid"] for i in keep if rows[i].get("crid")})
    captured = sum(1 for i in keep if rows[i].get("crid"))
    out["processing_identifiers"] = {"values": crids, "passes_with_one": captured, "passes_kept": len(keep)}
    if len(crids) > 1:
        out["refused"] = "the window mixes processing identifiers: " + ", ".join(crids)
        return out
    if require_crid and captured < len(keep):
        out["refused"] = "the processing identifier was not captured for every pass"
        return out
    screened = dict(tree)
    screened["satellite"] = {**tree["satellite"], "rows": [rows[i] for i in keep]}
    screened["gauge"] = {**tree["gauge"], "readings_by_pass": [rbp[i] for i in keep]}
    r, why = run_executor(mod, screened, tolerance, scratch)
    if r is None:
        out["refused"] = "the executor declined: " + why
        return out
    out["_executor"] = r
    out["gain"] = gain_block(r["pairs"])
    if "refused" in out["gain"]:
        out["refused"] = "the estimator declined: " + out["gain"]["refused"]
    pairs = sorted(r["pairs"], key=lambda p: p["gauge_elevation_m"])
    half = len(pairs) // 2
    desc = {}
    for name, part in (("lower_half_of_stage", pairs[:half]), ("upper_half_of_stage", pairs[half:])):
        part = sorted(part, key=lambda p: p["time"])
        g = gain_block(part) if len(part) >= MIN_PAIRS else {"refused": "too few pairs"}
        desc[name] = {k: g[k] for k in ("gain", "ci_low", "ci_high", "n")} if "refused" not in g else g
    out["gain_by_stage_half"] = desc
    return out


def run_batch(a) -> int:
    """The known-answer tests' way in. Each line of the batch is the data of one test case; each line written
    back is what confront_tree made of it, with the executor's own receipt cut down to the one block the
    known-answer tests compare against. This process is told nothing about the cases but their data."""
    mod = load_executor(a.executor)
    with tempfile.TemporaryDirectory() as tmp, a.batch.open() as given, a.out.open("w") as back:
        for line in given:
            tree = json.loads(line)
            if "put_in" in tree:
                print(f"{a.batch}: refused. A case in this batch carries what was put in (`put_in`); the method is never "
                      "given the answer", file=sys.stderr)
                return 4
            c = confront_tree(tree, mod, Path(tmp), a.tolerance_minutes, a.screen_reach_q, a.require_crid)
            r = c.pop("_executor", None)
            if r is not None:
                c["_executor"] = {"confrontation_on_changes": r["confrontation_on_changes"]}
            back.write(json.dumps(c) + "\n")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, allow_abbrev=False)
    ap.add_argument("--executor", type=Path, required=True)
    ap.add_argument("--inputs", type=Path, help="one input tree; the receipt goes to --out")
    ap.add_argument("--batch", type=Path, help="many input trees, one to a line (the known-answer tests); one line each goes to --out")
    ap.add_argument("--tolerance-minutes", type=int, default=15)
    ap.add_argument("--screen-reach-q", type=int, default=2)
    ap.add_argument("--require-crid", action="store_true")
    ap.add_argument("--refusal-is-a-result", action="store_true")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    if (a.inputs is None) == (a.batch is None):
        ap.error("give --inputs TREE.json, or --batch CASES.jsonl, and not both")
    if not a.executor.is_file():
        print(f"confront: refused. The executor {a.executor} is not there; it ships with the repository it belongs to, so "
              "check that repository out where the plan's roots point. Nothing was run", file=sys.stderr)
        return 2
    if a.batch:
        return run_batch(a)
    tree = json.loads(a.inputs.read_text())
    if "put_in" in tree:
        print(f"{a.inputs}: refused. This input carries what was put in (`put_in`); the method is never given the "
              "answer. Pass the data file alone", file=sys.stderr)
        return 4
    with tempfile.TemporaryDirectory() as tmp:
        c = confront_tree(tree, load_executor(a.executor), Path(tmp), a.tolerance_minutes, a.screen_reach_q, a.require_crid)
    r = c.pop("_executor", None)
    receipt = {
        "computation": "gain of one record against another, after pairing (prototype)",
        "sanctioned": False,
        "code": {"executor_sha256": sha(a.executor), "gain_sha256": sha(HERE / "gain.py"),
                 "wrapper_sha256": sha(Path(__file__))},
        "data": {"path": a.inputs.name, "sha256": sha(a.inputs)},
        "planned_handling": {"tolerance_minutes": a.tolerance_minutes, "screen_reach_q": a.screen_reach_q,
                             "require_crid": a.require_crid},
        **c,
    }
    if r is not None:
        receipt.update({
            "pair": r["pair"], "window": r["window"], "collection_named": r["collection_named"],
            "matching": {k: r["matching"][k] for k in ("tolerance_minutes", "passes_offered", "pairs")},
            "approval_values": r["approval"]["values_used"],
            "descriptive": {  # reported, never used by a rule in the plan
                "change_rmsd_m": r["confrontation_on_changes"]["rmsd_m"],
                "change_correlation": r["confrontation_on_changes"]["correlation"],
                "reported_uncertainty_median_m": r["satellite_reported_uncertainty_m"]["median"],
                "residual_sd_over_reported_uncertainty": (
                    round(receipt["gain"]["residual_sd_m"] / r["satellite_reported_uncertainty_m"]["median"], 2)
                    if "refused" not in receipt.get("gain", {"refused": 1}) else None)},
        })
    a.out.write_text(json.dumps(receipt, indent=1))
    if "refused" in receipt:
        print(f"{a.out}: refused ({receipt['refused']})", file=sys.stderr)
        return 0 if a.refusal_is_a_result else 3
    print(f"{a.out}: {receipt['matching']['pairs']} pairs after excluding "
          f"{receipt['screen']['passes_excluded']} flagged passes, gain {receipt['gain']['gain']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
