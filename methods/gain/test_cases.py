#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""test_cases: known-answer test cases for the satellite-versus-gauge
confrontation.

A test case is a synthetic input tree in exactly the shape the sanctioned
executor reads
(hydrology/skills/swot-hydro/scripts/load_swot_confrontation.py), generated
from parameters whose true values are known, so a method can be asked the
one question real data never answers: did you recover what was put in?

A case comes in two parts, and they are kept apart. The data is what a
method is given: it carries no trace of what was put in. The answer (the
parameters, the gain among them) is returned and written separately, for
whoever scores the method. The code under test is never handed the answer.

Two ways to build one.

A synthetic river (the default): the river is invented too.
  river stage   h(t) = mean + seasonal + AR(1) flood pulses (daily)
  gauge reading h(t) + N(0, sigma_gauge), every 15 minutes near each pass

On the real sampling (`sampling=` a tree in the fixture shape): the pass
times, the quality flags, the processing identifiers and the gauge readings
are the real ones for a window, and only the satellite elevations are
synthetic. Pass times and flags cannot move the gain; gauge stage cannot
either once the screen, the pairing and the model are fixed, which is the
condition a study's plan states before it counts the gauge record as
observation metadata. On that condition they may be read before the lock,
and power computed on them is power for the experiment that will actually
run.

Either way the satellite is synthetic:
  satellite = offset + gain * h + bend * (h - mean h)^2 + drift * years
              + step (after a processing change) + e(t)
  e an AR(1) series across passes with sd sigma_sat, optionally growing
  with stage (`het`)

What is put in, the truth and the trouble:
  gain, drift_m_per_yr, offset_m (the uncited datum difference a correct
  method must ignore), bend_per_m (a relation that is not a line)
  outlier_frac, outlier_scale   zero-mean gross errors at any stage, not flagged
  lowstage_fault_frac, lowstage_fault_m, fault_flagged
                                one-signed errors on passes in the lowest
                                quarter of stage (the shape the 2024 record
                                shows), flagged as degraded (reach_q 2)
                                with probability fault_flagged
  crid_change_frac, step_m      a processing change part-way through the
                                window, with a new identifier and an offset

Defaults are calibrated to the committed 2024 Baton Rouge working-data
fixture after the plan's quality screen (gauge elevation sd about 3.0 m,
residual sd about 0.16 m with lag-1 correlation about 0.25, a pass every
nine to ten days), never to any held-out window.

Usage:
  test_cases.py --seed 7 --gain 0.9 --out case.json [--answer answer.json]
  test_cases.py --seed 7 --sampling fixture.json --out case.json
  test_cases.py --selftest
"""
import sys

sys.dont_write_bytecode = True  # this package leaves no bytecode beside its sources
if __name__ == "__main__" and not sys.flags.safe_path and sys.path:
    del sys.path[0]  # the script's own folder must not shadow a module imported below

import argparse
import datetime as dt
import json
import math
import random
from pathlib import Path

FT_M = 0.3048
DEFAULTS = dict(n_passes=52, gain=1.0, drift_m_per_yr=0.0, offset_m=-0.25,
                sigma_sat=0.16, rho_sat=0.25, reported_u_m=0.096,
                sigma_gauge_m=0.01, h_mean=5.2, h_seasonal=3.3,
                h_pulse_sd=1.6, h_rho_daily=0.97, drop_frac=0.04,
                outlier_frac=0.0, outlier_scale=8.0,
                lowstage_fault_frac=0.0, lowstage_fault_m=-1.6, fault_flagged=1.0,
                het=0.0, bend_per_m=0.0, crid_change_frac=-1.0, step_m=0.0)


def _t(s: str) -> dt.datetime:
    return dt.datetime.fromisoformat(s.rstrip("Z"))


def _synthetic_sampling(p: dict, rng: random.Random) -> tuple:
    """Invent a river and a pass schedule: (pass datetimes, stage at each
    pass in metres, gauge readings per pass, window)."""
    start = dt.datetime(2031, 1, 1, 11, 0, 0)  # an obviously synthetic year
    innov = p["h_pulse_sd"] * math.sqrt(1 - p["h_rho_daily"] ** 2)
    pulse, stage = rng.gauss(0, p["h_pulse_sd"]), []
    phase = rng.uniform(0, 2 * math.pi)
    for day in range(366):
        pulse = p["h_rho_daily"] * pulse + rng.gauss(0, innov)
        stage.append(p["h_mean"] + p["h_seasonal"] * math.sin(2 * math.pi * day / 365 + phase) + pulse)

    def h(day_float: float) -> float:
        i = min(max(int(day_float), 0), 364)
        f = day_float - i
        return stage[i] * (1 - f) + stage[i + 1] * f

    days, d = [], rng.uniform(0, 3)
    while len(days) < p["n_passes"] and d < 364:
        days.append(d)
        d += rng.choice([1.5, 9.5, 9.5, 11.4, 20.9]) * rng.uniform(0.97, 1.03) * (364 / (p["n_passes"] * 10.4))
    times, truth, readings_by_pass = [], [], []
    for d in days:
        when = start + dt.timedelta(days=d)
        times.append(when)
        truth.append(h(d))
        if rng.random() < p["drop_frac"]:
            readings_by_pass.append([])  # a pass with no gauge reading in the window
            continue
        base = when.replace(minute=(when.minute // 15) * 15, second=0)
        readings = []
        for k in range(-4, 5):
            tg = base + dt.timedelta(minutes=15 * k)
            hg = h(d + (tg - when).total_seconds() / 86400.0) + rng.gauss(0, p["sigma_gauge_m"])
            readings.append({"t": tg.strftime("%Y-%m-%dT%H:%M:%SZ"),
                             "stage_ft": round(hg / FT_M, 2), "approval": "Synthetic"})
        readings_by_pass.append(readings)
    return times, truth, readings_by_pass, {"start": "2031-01-01", "end": "2031-12-31"}


def _real_sampling(sampling: dict) -> tuple:
    """Take pass times and gauge readings from a real tree; the stage at a
    pass is the reading nearest it (a pass with no reading borrows the
    previous stage: the executor will not pair it anyway)."""
    rows, rbp = sampling["satellite"]["rows"], sampling["gauge"]["readings_by_pass"]
    datum_ft = float(sampling["gauge"].get("gauge_datum_altitude_ft") or 0.0)
    times, truth, last = [], [], None
    for row, readings in zip(rows, rbp):
        when = _t(row["time"])
        times.append(when)
        if readings:
            near = min(readings, key=lambda r: abs((_t(r["t"]) - when).total_seconds()))
            last = (float(near["stage_ft"]) + datum_ft) * FT_M
        truth.append(last)
    known = [x for x in truth if x is not None]
    fill = sum(known) / len(known)
    return times, [fill if x is None else x for x in truth], rbp, sampling.get("window")


def make_case(seed: int, sampling: dict | None = None, **overrides) -> tuple:
    """(the data a method is given, the answer). The data holds nothing of what was put in; the answer is
    the full set of parameters, with the seed, for whoever scores the method."""
    p = {**DEFAULTS, **overrides}
    rng = random.Random(seed)
    trouble = random.Random(seed * 7919 + 13)  # its own stream, so putting in trouble never moves the river
    if sampling is None:
        times, truth, readings_by_pass, window = _synthetic_sampling(p, rng)
        flags, crids = ["1"] * len(times), ["SYNTHETIC_A"] * len(times)
        gauge = {"datum": "SYNTHETIC", "gauge_datum_altitude_ft": 0.0,
                 "approval_note": "a known-answer test case, not an observation"}
        pair = {"reach_id": "SYNTHETIC", "gauge": "SYNTHETIC"}
    else:
        times, truth, readings_by_pass, window = _real_sampling(sampling)
        rows = sampling["satellite"]["rows"]
        flags = [str(r.get("reach_q", "1")) for r in rows]
        crids = [r.get("crid") for r in rows]
        gauge = {k: v for k, v in sampling["gauge"].items() if k != "readings_by_pass"}
        pair = {**sampling.get("pair", {}), "built_on_real_sampling": True}
    n = len(times)
    order = sorted(range(n), key=lambda i: truth[i])
    rank = {i: k / max(n - 1, 1) for k, i in enumerate(order)}  # 0 at the lowest stage, 1 at the highest
    h_bar = sum(truth) / n
    t0 = times[0]
    innov_s = p["sigma_sat"] * math.sqrt(1 - p["rho_sat"] ** 2)
    e = rng.gauss(0, p["sigma_sat"])
    out_rows = []
    for i, when in enumerate(times):
        e = p["rho_sat"] * e + rng.gauss(0, innov_s)
        err = e * (1 + 2 * p["het"] * (rank[i] - 0.5))
        if rng.random() < p["outlier_frac"]:
            err = e * p["outlier_scale"]
        flag = flags[i]
        if rank[i] <= 0.25 and trouble.random() < p["lowstage_fault_frac"]:
            err += p["lowstage_fault_m"]
            if trouble.random() < p["fault_flagged"]:
                flag = "2"
        years = (when - t0).total_seconds() / 31557600.0
        crid = crids[i] or ("SYNTHETIC_A" if p["crid_change_frac"] >= 0 else None)
        step = 0.0
        if p["crid_change_frac"] >= 0 and i >= p["crid_change_frac"] * n:
            crid, step = "SYNTHETIC_B", p["step_m"]
        wse = (p["offset_m"] + p["gain"] * truth[i] + p["bend_per_m"] * (truth[i] - h_bar) ** 2
               + p["drift_m_per_yr"] * years + step + err)
        row = {"time": when.strftime("%Y-%m-%dT%H:%M:%SZ"), "wse_m": round(wse, 4),
               "wse_u_m": p["reported_u_m"], "reach_q": flag}
        if crid is not None:
            row["crid"] = crid
        out_rows.append(row)
    data = {
        "pair": pair, "window": window,
        "satellite": {"collection_named": "KNOWN_ANSWER_TEST_CASE", "rows": out_rows},
        "gauge": {**gauge, "readings_by_pass": readings_by_pass},
    }
    return data, {"seed": seed, "on_real_sampling": sampling is not None, **p}


def selftest() -> int:
    (a, a_in), (b, _) = make_case(11), make_case(11)
    c, c_in = make_case(11, gain=0.9)
    f, _ = make_case(11, lowstage_fault_frac=1.0)
    s, _ = make_case(11, crid_change_frac=0.3, step_m=0.5)
    ok = a == b and a != c and len(a["satellite"]["rows"]) >= 40
    ok = ok and a_in["gain"] == 1.0 and c_in["gain"] == 0.9
    # the data a method is given holds no trace of what was put in: no such block, no such key, at any depth
    ok = ok and "put_in" not in a and not any(k in json.dumps(c) for k in ('"put_in"', '"gain"', '"seed"', '"drift_m_per_yr"'))
    ok = ok and all("wse_m" in r and r["reach_q"] == "1" for r in a["satellite"]["rows"])
    ok = ok and a["gauge"]["readings_by_pass"] == f["gauge"]["readings_by_pass"]  # trouble never moves the river
    ok = ok and sum(r["reach_q"] == "2" for r in f["satellite"]["rows"]) >= 10
    ok = ok and {r["crid"] for r in s["satellite"]["rows"]} == {"SYNTHETIC_A", "SYNTHETIC_B"}
    d, d_in = make_case(5, sampling=a, gain=0.8)  # a case built on another case's sampling keeps its river
    ok = ok and d["gauge"]["readings_by_pass"] == a["gauge"]["readings_by_pass"] and d_in["on_real_sampling"]
    ok = ok and [r["time"] for r in d["satellite"]["rows"]] == [r["time"] for r in a["satellite"]["rows"]]
    print("selftest:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--sampling", type=Path, help="a tree in the fixture shape: build the case on its pass times and gauge readings")
    ap.add_argument("--out", type=Path, help="where the data goes (what a method is given)")
    ap.add_argument("--answer", type=Path, help="where what was put in goes; never pass this file to the method")
    ap.add_argument("--selftest", action="store_true")
    for k, v in DEFAULTS.items():
        ap.add_argument("--" + k.replace("_", "-"), type=type(v), default=None)
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    over = {k: getattr(a, k) for k in DEFAULTS if getattr(a, k) is not None}
    sampling = json.loads(a.sampling.read_text()) if a.sampling else None
    data, put_in = make_case(a.seed, sampling=sampling, **over)
    text = json.dumps(data, indent=1)
    if a.answer:
        a.answer.write_text(json.dumps({"put_in": put_in}, indent=1))
    if a.out:
        a.out.write_text(text)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
