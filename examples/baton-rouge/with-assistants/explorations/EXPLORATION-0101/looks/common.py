"""Shared helpers for the looks of this exploration (exploring, not a method).

Pairing follows the shipped executor (hydrology skills/swot-hydro/scripts/
load_swot_confrontation.py): nearest gauge reading inside a tolerance, stage in
feet times 0.3048 plus the gauge datum altitude. LOOK-003 checks that this
module reproduces the executor's receipt.
"""
import datetime as dt
import json
import math
import statistics

FT_M = 0.3048


def t(s):
    return dt.datetime.fromisoformat(s.rstrip("Z"))


def load(path):
    with open(path) as f:
        return json.load(f)


def pair(doc, tol_min=15, interpolate=False):
    """Return (pairs, unmatched). Each pair carries every satellite field."""
    sat, gauge = doc["satellite"], doc["gauge"]
    alt = gauge.get("gauge_datum_altitude_ft") or 0.0
    tol = dt.timedelta(minutes=tol_min)
    pairs, unmatched = [], []
    for p, readings in zip(sat["rows"], gauge["readings_by_pass"]):
        when = t(p["time"])
        if p["wse_m"] is None:
            unmatched.append((p["time"], "no elevation"))
            continue
        near = [r for r in readings if abs(t(r["t"]) - when) <= tol]
        if not near:
            gaps = sorted(abs((t(r["t"]) - when).total_seconds()) / 60 for r in readings)
            unmatched.append((p["time"], f"no reading within {tol_min} min; nearest {gaps[0]:.1f} min"
                              if gaps else "no readings at all"))
            continue
        best = min(near, key=lambda r: abs(t(r["t"]) - when))
        stage_ft = best["stage_ft"]
        if interpolate:
            before = [r for r in readings if t(r["t"]) <= when]
            after = [r for r in readings if t(r["t"]) >= when]
            if before and after:
                b, a = max(before, key=lambda r: t(r["t"])), min(after, key=lambda r: t(r["t"]))
                span = (t(a["t"]) - t(b["t"])).total_seconds()
                w = 0.0 if span == 0 else (when - t(b["t"])).total_seconds() / span
                stage_ft = b["stage_ft"] + w * (a["stage_ft"] - b["stage_ft"])
        # rate of gauge change over the readings kept around this pass, m per day
        rs = sorted(readings, key=lambda r: t(r["t"]))
        rate = None
        if len(rs) >= 2:
            hours = (t(rs[-1]["t"]) - t(rs[0]["t"])).total_seconds() / 3600
            if hours > 0:
                rate = (rs[-1]["stage_ft"] - rs[0]["stage_ft"]) * FT_M / hours * 24
        q = dict(p)
        q.update({"when": when, "gauge_m": (stage_ft + alt) * FT_M,
                  "offset_min": abs((t(best["t"]) - when).total_seconds()) / 60,
                  "gauge_rate_m_per_day": rate, "n_readings": len(readings),
                  "reach_q": int(p["reach_q"])})
        pairs.append(q)
    pairs.sort(key=lambda x: x["when"])
    return pairs, unmatched


def ols(x, y):
    """Slope, intercept, residuals, slope standard error (plain, n-2)."""
    n = len(x)
    mx, my = statistics.fmean(x), statistics.fmean(y)
    sxx = sum((a - mx) ** 2 for a in x)
    b = sum((a - mx) * (c - my) for a, c in zip(x, y)) / sxx
    a0 = my - b * mx
    res = [c - (a0 + b * a) for a, c in zip(x, y)]
    s2 = sum(r * r for r in res) / (n - 2)
    return b, a0, res, math.sqrt(s2 / sxx)


def lag1(x):
    m = statistics.fmean(x)
    den = sum((v - m) ** 2 for v in x)
    if den <= 0 or len(x) < 3:
        return 0.0
    return sum((x[i] - m) * (x[i - 1] - m) for i in range(1, len(x))) / den


def neff(x):
    n = len(x)
    r = max(-0.99, min(0.99, lag1(x)))
    return max(2.0, min(float(n), n * (1 - r) / (1 + r)))


# two-sided 97.5 per cent Student-t quantiles, by degrees of freedom
_T = {3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
      12: 2.179, 15: 2.131, 20: 2.086, 25: 2.060, 30: 2.042, 40: 2.021, 60: 2.000, 120: 1.980}


def tq(df):
    df = max(3, int(df))
    keys = sorted(_T)
    lo = max(k for k in keys if k <= df)
    return _T[lo]  # the next lower tabulated value: slightly wide, never narrow


def gain(pairs):
    """Gain of satellite on gauge with an interval that uses the effective
    sample size of the residuals (lag-1, capped at n). Returns a dict."""
    x = [p["gauge_m"] for p in pairs]
    y = [p["wse_m"] for p in pairs]
    b, a0, res, se = ols(x, y)
    n = len(x)
    ne = neff(res)
    se_eff = se * math.sqrt((n - 2) / max(ne - 2, 1.0))
    q = tq(ne - 2)
    return {"n": n, "gain": b, "intercept": a0, "lo": b - q * se_eff, "hi": b + q * se_eff,
            "resid_sd": statistics.stdev(res), "resid_lag1": lag1(res), "n_eff": ne, "res": res}


def change_scores(pairs):
    cs = [pairs[i]["wse_m"] - pairs[i - 1]["wse_m"] for i in range(1, len(pairs))]
    cg = [pairs[i]["gauge_m"] - pairs[i - 1]["gauge_m"] for i in range(1, len(pairs))]
    err = [s - g for s, g in zip(cs, cg)]
    ms, mg = statistics.fmean(cs), statistics.fmean(cg)
    r = (sum((a - ms) * (b - mg) for a, b in zip(cs, cg))
         / math.sqrt(sum((a - ms) ** 2 for a in cs) * sum((b - mg) ** 2 for b in cg)))
    ne = neff(err)
    m = statistics.fmean(err)
    se = statistics.stdev(err) / math.sqrt(ne)
    return {"n": len(err), "mean": m, "lo": m - 1.96 * se, "hi": m + 1.96 * se,
            "rmsd": math.sqrt(sum(e * e for e in err) / len(err)), "r": r,
            "spread": statistics.stdev(cg), "err": err, "cg": cg, "cs": cs}
