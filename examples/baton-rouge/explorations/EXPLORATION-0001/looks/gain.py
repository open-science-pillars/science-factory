# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""A look at the gain: how much the satellite elevation moves when the gauge moves by one.

Exploring. Ordinary least squares of satellite elevation on gauge elevation
and on time, over paired passes. The intercept takes up the uncited offset
between the vertical references and the time term takes up slow drift, so
neither touches the gain. The interval printed here is the plain least
squares one: it does not allow for passes being correlated in time, so it
is too narrow, and it is used only to compare one setting with another.
"""
import argparse
import datetime as dt
import json
import math

FT = 0.3048


def when(s):
    return dt.datetime.fromisoformat(s.rstrip("Z"))


def solve3(m, v):
    a = [row[:] + [x] for row, x in zip(m, v)]
    for i in range(3):
        piv = max(range(i, 3), key=lambda r: abs(a[r][i]))
        a[i], a[piv] = a[piv], a[i]
        for r in range(3):
            if r != i:
                f = a[r][i] / a[i][i]
                a[r] = [x - f * y for x, y in zip(a[r], a[i])]
    return [a[i][3] / a[i][i] for i in range(3)]


def fit(ps):
    t0 = when(ps[0]["time"])
    X = [[1.0, p["gauge"], (when(p["time"]) - t0).days / 365.25] for p in ps]
    y = [p["wse"] for p in ps]
    xtx = [[sum(r[i] * r[j] for r in X) for j in range(3)] for i in range(3)]
    xty = [sum(r[i] * v for r, v in zip(X, y)) for i in range(3)]
    b = solve3(xtx, xty)
    res = [v - sum(c * x for c, x in zip(b, r)) for r, v in zip(X, y)]
    s2 = sum(e * e for e in res) / (len(y) - 3)
    inv_col = solve3(xtx, [0.0, 1.0, 0.0])
    se = math.sqrt(s2 * inv_col[1])
    return b[1], se, math.sqrt(s2), res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("--tolerance", type=int, default=15)
    ap.add_argument("--exclude-flag-at-or-above", type=int, default=None)
    ap.add_argument("--exclude-dark-above", type=float, default=None)
    ap.add_argument("--leave-one-out", action="store_true")
    a = ap.parse_args()
    d = json.load(open(a.data))
    ps = []
    for row, readings in zip(d["satellite"]["rows"], d["gauge"]["readings_by_pass"]):
        t = when(row["time"])
        near = min(readings, key=lambda r: abs((when(r["t"]) - t).total_seconds()))
        if abs((when(near["t"]) - t).total_seconds()) <= a.tolerance * 60:
            ps.append({"time": row["time"], "wse": row["wse_m"], "gauge": near["stage_ft"] * FT, "q": int(row["reach_q"]), "dark": row["dark_frac"]})
    n0 = len(ps)
    if a.exclude_flag_at_or_above is not None:
        ps = [p for p in ps if p["q"] < a.exclude_flag_at_or_above]
    if a.exclude_dark_above is not None:
        ps = [p for p in ps if p["dark"] <= a.exclude_dark_above]
    g, se, sd, _ = fit(ps)
    print(f"tolerance {a.tolerance} min; reach_q screen {a.exclude_flag_at_or_above}; dark_frac screen {a.exclude_dark_above}: "
          f"{len(ps)} of {n0} pairs kept")
    print(f"gain {g:.4f}, plain least squares 95 percent interval {g - 1.96 * se:.4f} to {g + 1.96 * se:.4f} (too narrow: no allowance "
          f"for correlation in time), residual sd {sd:.3f} m")
    if a.leave_one_out:
        moves = []
        for i, p in enumerate(ps):
            gi, _, _, _ = fit(ps[:i] + ps[i + 1:])
            moves.append((gi - g, p))
        print("the five pairs whose removal moves the gain most:")
        for m, p in sorted(moves, key=lambda x: -abs(x[0]))[:5]:
            print(f"  without {p['time']} (gauge {p['gauge']:.2f} m, reach_q {p['q']}, dark_frac {p['dark']:.3f}): gain moves by {m:+.4f}")


main()
