#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""gain: the candidate quantity estimated for a satellite-versus-gauge gain
claim, as a PROTOTYPE.

NOT A SANCTIONED COMPUTATION. This is the analysis assistant's starting
point, kept here so the known-answer tests can be run before any capability
is touched. The method work lands it in hydrology as an attested
computation with an attester and a golden, under the specification's rule
that a computation is a skill.

The quantity estimated. Regress satellite elevation on gauge elevation and
on time across the paired passes of a confrontation receipt:
    satellite = intercept + gain * gauge + drift * years + residual
The gain says whether the satellite sees the same size of rise and fall as
the gauge (1.0 means yes), as an average over the stage the window visited.
The intercept absorbs any constant offset between the two vertical
references, so the uncited datum difference that forbids scoring the level
cannot touch the gain. The time term is there because the known-answer
tests demanded it: without it, a slow drift between the two records leaks
into the gain through the seasonal cycle and the interval covered the gain
that was put in only 81 percent of the time (measured in an early run whose
receipt was not kept). With it the gain is estimated at fixed time.

The interval follows the organization's trend method: lag-1 autocorrelation
of the residuals, an effective sample size n(1-r1)/(1+r1) capped at n, the
residual variance on n_eff - 3 degrees of freedom, and a two-sided
Student-t interval on those degrees of freedom. It declines below ten pairs
and below four effective degrees of freedom.

Where the interval holds and where it does not, as the known-answer tests
measured it (known_answer_tests.py): it covers at about 93 percent in a
kind case, under drift, under zero-mean gross errors, under flagged
low-stage faults (once the plan's quality screen removes them) and with
residual autocorrelation up to about 0.6. It does not survive low-stage
errors the product leaves unflagged, autocorrelation near 0.9, a relation
that bends with stage, or an offset step inside the window (which the
plan's processing guard declines instead).

Input: a receipt written by the sanctioned confrontation executor (its
`pairs` list). Output: a gain block as JSON.

Usage:
  gain.py --receipt confrontation-receipt.json [--out gain.json]
  gain.py --selftest
"""
import sys

sys.dont_write_bytecode = True  # this package leaves no bytecode beside its sources
if __name__ == "__main__" and not sys.flags.safe_path and sys.path:
    del sys.path[0]  # the script's own folder must not shadow a module imported below

import argparse
import hashlib
import json
import math
import statistics
from pathlib import Path

MIN_PAIRS, MIN_DOF = 10, 4.0


def t_quantile_975(dof: float) -> float:
    """Two-sided 95 percent Student-t quantile by Cornish-Fisher expansion
    (accurate to about 1e-3 for dof >= 4, which the refusal guarantees)."""
    z = 1.959963985
    g1 = (z ** 3 + z) / 4
    g2 = (5 * z ** 5 + 16 * z ** 3 + 3 * z) / 96
    g3 = (3 * z ** 7 + 19 * z ** 5 + 17 * z ** 3 - 15 * z) / 384
    return z + g1 / dof + g2 / dof ** 2 + g3 / dof ** 3


def gain_block(pairs: list) -> dict:
    import datetime as dt
    x = [p["gauge_elevation_m"] for p in pairs]
    y = [p["satellite_m"] for p in pairs]
    n = len(x)
    if n < MIN_PAIRS:
        return {"refused": f"{n} pairs; at least {MIN_PAIRS} are needed"}
    if all("time" in p for p in pairs):
        t0 = dt.datetime.fromisoformat(pairs[0]["time"].rstrip("Z"))
        yrs = [(dt.datetime.fromisoformat(p["time"].rstrip("Z")) - t0).total_seconds() / 31557600.0 for p in pairs]
    else:
        yrs = [i / n for i in range(n)]
    mx, my, mt = statistics.fmean(x), statistics.fmean(y), statistics.fmean(yrs)
    sxx = sum((a - mx) ** 2 for a in x)
    stt = sum((c - mt) ** 2 for c in yrs)
    sxt = sum((a - mx) * (c - mt) for a, c in zip(x, yrs))
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sty = sum((c - mt) * (b - my) for c, b in zip(yrs, y))
    det = sxx * stt - sxt * sxt
    if sxx <= 0 or det <= 1e-12 * max(sxx * stt, 1e-30):
        return {"refused": "the gauge did not move over the window, or moved only as a line in time"}
    g = (sxy * stt - sty * sxt) / det
    drift = (sty * sxx - sxy * sxt) / det
    icpt = my - g * mx - drift * mt
    res = [b - (icpt + g * a + drift * c) for a, b, c in zip(x, y, yrs)]
    sse = sum(r * r for r in res)
    num = sum(res[i] * res[i - 1] for i in range(1, n))
    r1 = max(-0.99, min(0.99, num / sse)) if sse > 0 else 0.0
    n_eff = max(4.0, min(float(n), n * (1 - r1) / (1 + r1)))
    dof = n_eff - 3
    if dof < MIN_DOF:
        return {"refused": f"{dof:.1f} effective degrees of freedom; at least {MIN_DOF} are needed"}
    se = math.sqrt(sse / dof * stt / det)
    half = t_quantile_975(dof) * se
    return {"gain": round(g, 4), "ci_low": round(g - half, 4), "ci_high": round(g + half, 4),
            "confidence": 0.95, "drift_m_per_yr": round(drift, 4), "intercept_m": round(icpt, 4),
            "n": n, "effective_sample_size": round(n_eff, 1), "residual_lag1": round(r1, 3),
            "residual_sd_m": round(math.sqrt(sse / (n - 3)), 4),
            "gauge_sd_m": round(statistics.stdev(x), 4),
            "intervals_are": ("sampling intervals under a lag-1 autocorrelation model of the "
                              "regression residuals; they carry neither instrument's published "
                              "uncertainty")}


def selftest() -> int:
    import random
    rng = random.Random(3)
    pairs = []
    for _ in range(60):
        h = rng.uniform(1, 10)
        pairs.append({"gauge_elevation_m": h, "satellite_m": -0.4 + 0.9 * h + rng.gauss(0, 0.05)})
    b = gain_block(pairs)
    ok = abs(b["gain"] - 0.9) < 0.02 and b["ci_low"] < 0.9 < b["ci_high"] and b["ci_high"] < 1.0
    ok = ok and "refused" in gain_block(pairs[:5])
    ok = ok and abs(t_quantile_975(10) - 2.2281) < 2e-3 and abs(t_quantile_975(47) - 2.0117) < 1e-3
    print("selftest:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--receipt", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    src = json.loads(a.receipt.read_text())
    block = {"computation": "gain-prototype", "sanctioned": False,
             "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             "source_receipt_sha256": hashlib.sha256(a.receipt.read_bytes()).hexdigest(),
             "gain": gain_block(src["pairs"])}
    text = json.dumps(block, indent=1)
    if a.out:
        a.out.write_text(text)
    else:
        print(text)
    return 3 if "refused" in block["gain"] else 0


if __name__ == "__main__":
    sys.exit(main())
