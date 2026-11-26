#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""pair_records: this repository's own pairing step, so the system trial
and the blind test of the system run with nothing beside the repository.

The gain method (methods/gain/) does not pair the two records itself. It
hands the screened input to a pairing script, named on its command line as
the executor, and estimates the gain from the pairs that come back. For the
first real study that script belongs to the hydrology capability, and the
checks that use it need that capability checked out beside this
repository. This file stands in the same place for studies that touch no
real record: a system trial, whose data is a synthetic record with a known
answer, made by methods/gain/test_cases.py.

NOT A SANCTIONED COMPUTATION of any capability. It is small on purpose, it
was written here, and nothing about a real record should rest on it.

What it does, in order:
  1. For each pass of the first record, take the reading of the second
     record nearest in time, if one lies within the tolerance. A pass with
     no elevation, or with no reading inside the tolerance, is left out and
     named. It is never matched to a reading farther away.
  2. Refuse when fewer than ten pairs remain.
  3. Report the pairs, and three plain scores on the changes between
     consecutive pairs (the mean difference with a 95 percent interval, the
     root mean square difference, the correlation). The known-answer tests
     show that the first of those cannot see a gain; the gain method is
     what estimates one.

It reads the input tree in the shape test_cases.py writes, which is the
shape the hydrology script reads: `satellite.rows` (each with `time`,
`wse_m`, `wse_u_m`) and `gauge.readings_by_pass` (for each pass, readings
with `t`, `stage_ft`, `approval`), with `gauge.gauge_datum_altitude_ft`.
It writes the keys the gain method reads from a pairing receipt. It is
deterministic: the same input gives the same bytes, with no clock, no
random number and no network in it.

Usage:
  pair_records.py --inputs TREE.json [--tolerance-minutes 15] --out receipt.json
  pair_records.py --selftest [--compare-with PATH/load_swot_confrontation.py]
"""
import sys

sys.dont_write_bytecode = True  # this package leaves no bytecode beside its sources
if __name__ == "__main__" and not sys.flags.safe_path and sys.path:
    del sys.path[0]  # the script's own folder must not shadow a module imported below

import argparse
import datetime as dt
import hashlib
import json
import math
import statistics
from pathlib import Path

FEET_TO_METRES = 0.3048
FEWEST_PAIRS = 10


def when(text: str) -> dt.datetime:
    return dt.datetime.fromisoformat(text.rstrip("Z"))


def effective_count(series: list) -> float:
    """How many independent values a series is worth under a lag-1 model: n(1 - r)/(1 + r), never more than
    the count and never fewer than two."""
    n = len(series)
    if n < 3:
        return float(n)
    mean = statistics.fmean(series)
    spread = sum((v - mean) ** 2 for v in series)
    if spread <= 0:
        return float(n)
    r = sum((series[i] - mean) * (series[i - 1] - mean) for i in range(1, n)) / spread
    r = max(-0.99, min(0.99, r))
    return max(2.0, min(float(n), n * (1 - r) / (1 + r)))


def mean_with_interval(series: list) -> tuple:
    """(mean, low, high, effective count): a 95 percent sampling interval on the mean."""
    count = effective_count(series)
    mean = statistics.fmean(series)
    if len(series) < 2:
        return mean, None, None, count
    half = 1.96 * statistics.stdev(series) / math.sqrt(count)
    return mean, mean - half, mean + half, count


def correlation(a: list, b: list) -> float | None:
    ma, mb = statistics.fmean(a), statistics.fmean(b)
    sa = math.sqrt(sum((x - ma) ** 2 for x in a))
    sb = math.sqrt(sum((y - mb) ** 2 for y in b))
    if not sa or not sb:
        return None
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (sa * sb)


def pair(tree: dict, tolerance_minutes: int) -> tuple:
    """(pairs in time order, the passes left out with the reason for each)."""
    datum_ft = tree["gauge"].get("gauge_datum_altitude_ft") or 0.0
    tolerance = dt.timedelta(minutes=tolerance_minutes)
    pairs, left_out = [], []
    for row, readings in zip(tree["satellite"]["rows"], tree["gauge"]["readings_by_pass"]):
        if row["wse_m"] is None:
            left_out.append({"time": row["time"], "why": "the pass carries no elevation"})
            continue
        at = when(row["time"])
        inside = [r for r in readings if abs(when(r["t"]) - at) <= tolerance]
        if not inside:
            left_out.append({"time": row["time"], "why": f"no gauge reading within {tolerance_minutes} minutes"})
            continue
        nearest = min(inside, key=lambda r: abs(when(r["t"]) - at))
        pairs.append({"time": row["time"], "gauge_time": nearest["t"],
                      "offset_s": abs((when(nearest["t"]) - at).total_seconds()),
                      "satellite_m": row["wse_m"], "satellite_u_m": row["wse_u_m"],
                      "gauge_stage_ft": nearest["stage_ft"],
                      "gauge_elevation_m": (nearest["stage_ft"] + datum_ft) * FEET_TO_METRES,
                      "approval": nearest["approval"]})
    pairs.sort(key=lambda p: p["time"])
    return pairs, left_out


def receipt_for(tree: dict, tolerance_minutes: int, source: Path | None = None) -> dict:
    pairs, left_out = pair(tree, tolerance_minutes)
    if len(pairs) < FEWEST_PAIRS:
        raise ValueError(f"{len(pairs)} pairs; at least {FEWEST_PAIRS} are needed before a score means anything")
    first = [pairs[i]["satellite_m"] - pairs[i - 1]["satellite_m"] for i in range(1, len(pairs))]
    second = [pairs[i]["gauge_elevation_m"] - pairs[i - 1]["gauge_elevation_m"] for i in range(1, len(pairs))]
    apart = [a - b for a, b in zip(first, second)]
    mean, low, high, count = mean_with_interval(apart)
    rmsd = math.sqrt(sum(d * d for d in apart) / len(apart))
    r = correlation(first, second)
    spread = statistics.stdev(second)
    reported = [p["satellite_u_m"] for p in pairs if p["satellite_u_m"] is not None]
    out = {
        "computation": "pairing of two records (this repository's own; not a sanctioned computation of any capability)",
        "pair": tree["pair"], "window": tree["window"], "collection_named": tree["satellite"]["collection_named"],
        "matching": {"tolerance_minutes": tolerance_minutes, "passes_offered": len(tree["satellite"]["rows"]),
                     "pairs": len(pairs), "unmatched": left_out, "max_offset_s": max(p["offset_s"] for p in pairs)},
        "approval": {"values_used": sorted({p["approval"] for p in pairs}), "note": tree["gauge"].get("approval_note")},
        "confrontation_on_changes": {
            "n": len(apart), "mean_error_m": round(mean, 4),
            "mean_error_95pct": [round(low, 4), round(high, 4)] if low is not None else None,
            "effective_sample_size": round(count, 1), "rmsd_m": round(rmsd, 4),
            "correlation": round(r, 4) if r is not None else None,
            "gauge_change_spread_m": round(spread, 4),
            "rmsd_over_spread": round(rmsd / spread, 4) if spread else None},
        "satellite_reported_uncertainty_m": {"median": round(statistics.median(reported), 4) if reported else None},
        "intervals_are": "sampling intervals under a lag-1 model; they carry neither record's own stated uncertainty",
        "pairs": pairs,
    }
    if source is not None:
        out["source"] = {"path": source.name, "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--inputs", type=Path)
    ap.add_argument("--tolerance-minutes", type=int, default=15)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--compare-with", type=Path, help="with --selftest: another pairing script to compare pairs with, case for case")
    a = ap.parse_args()
    if a.selftest:
        return selftest(a.compare_with)
    if a.inputs is None:
        ap.error("--inputs is required")
    try:
        receipt = receipt_for(json.loads(a.inputs.read_text()), a.tolerance_minutes, a.inputs)
    except ValueError as refusal:
        print(f"REFUSED: {refusal}", file=sys.stderr)
        return 2
    text = json.dumps(receipt, indent=1)
    if a.out:
        a.out.write_text(text)
        print(f"{a.out}: {receipt['matching']['pairs']} pairs", file=sys.stderr)
    else:
        print(text)
    return 0


def selftest(other: Path | None) -> int:
    import importlib.util
    import subprocess
    import tempfile
    results = []

    def check(name: str, ok: bool) -> None:
        results.append(bool(ok))
        print(("PASS  " if ok else "FAIL  ") + name)

    spec = importlib.util.spec_from_file_location("test_cases", Path(__file__).resolve().parent.parent / "gain" / "test_cases.py")
    cases = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cases)
    tree, put_in = cases.make_case(11, gain=0.9)
    receipt = receipt_for(tree, 15)
    by_time = {row["time"]: (row, readings) for row, readings in zip(tree["satellite"]["rows"], tree["gauge"]["readings_by_pass"])}
    check("every pair is a pass with the reading nearest to it in time, and none is farther than the tolerance",
          all(p["offset_s"] <= 900 and p["offset_s"] == min(abs((when(r["t"]) - when(p["time"])).total_seconds())
                                                             for r in by_time[p["time"]][1]) for p in receipt["pairs"]))
    check("a pass with no reading is left out and named, never matched farther away",
          receipt["matching"]["pairs"] + len(receipt["matching"]["unmatched"]) == receipt["matching"]["passes_offered"]
          and all(not by_time[u["time"]][1] for u in receipt["matching"]["unmatched"]))
    check("the same input gives the same bytes", json.dumps(receipt_for(tree, 15)) == json.dumps(receipt))
    few = {**tree, "satellite": {**tree["satellite"], "rows": tree["satellite"]["rows"][:6]},
           "gauge": {**tree["gauge"], "readings_by_pass": tree["gauge"]["readings_by_pass"][:6]}}
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "few.json").write_text(json.dumps(few))
        ran = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--inputs", str(Path(tmp) / "few.json"),
                              "--out", str(Path(tmp) / "out.json")], capture_output=True, text=True)
        check("fewer than ten pairs is refused, and nothing is written",
              ran.returncode == 2 and "REFUSED" in ran.stderr and not (Path(tmp) / "out.json").exists())
        check("the receipt carries no key that names what was put in (the gain, the seed)",
              put_in["gain"] == 0.9 and not any(key in json.dumps(receipt) for key in ('"put_in"', '"seed"', '"gain"')))
        if other is not None:
            same = True
            for seed in range(20, 30):
                tree, _ = cases.make_case(seed, gain=1.0 + (seed % 3 - 1) * 0.1)
                (Path(tmp) / "case.json").write_text(json.dumps(tree))
                subprocess.run([sys.executable, str(other), "--inputs", str(Path(tmp) / "case.json"), "--tolerance-minutes", "15",
                                "--out", str(Path(tmp) / "theirs.json")], capture_output=True, text=True)
                theirs = json.loads((Path(tmp) / "theirs.json").read_text())
                ours = receipt_for(tree, 15)
                same = same and theirs["pairs"] == ours["pairs"] and all(
                    theirs["confrontation_on_changes"][k] == ours["confrontation_on_changes"][k]
                    for k in ("n", "mean_error_m", "mean_error_95pct", "rmsd_m", "correlation"))
            check(f"on ten test cases this step and {other.name} give the same pairs and the same scores on the changes", same)
    good = all(results)
    print(f"selftest: {'PASS' if good else 'FAIL'} ({sum(results)} of {len(results)})")
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
