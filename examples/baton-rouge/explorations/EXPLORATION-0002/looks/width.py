# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Looks at SWOT reach width beside gauge stage. Exploring.

Width and stage are different quantities, so the only question is whether
they move together: a rank correlation, a straight-line slope in metres of
width per metre of stage, and how much of the width's spread the line takes
up. The pairing is the recipe's: nearest gauge reading within a tolerance.
"""
import argparse
import datetime as dt
import json
import statistics as st

FT = 0.3048


def when(s):
    return dt.datetime.fromisoformat(s.rstrip("Z"))


def ranks(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    for k, i in enumerate(order):
        r[i] = k + 1.0
    return r


def corr(a, b):
    ma, mb = st.fmean(a), st.fmean(b)
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)) ** 0.5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("--mode", required=True, choices=["relation", "named-passes", "by-stage"])
    ap.add_argument("--tolerance", type=int, default=15)
    ap.add_argument("--exclude-flag-at-or-above", type=int, default=None)
    ap.add_argument("--name", action="append", default=[], help="a pass date to print, as it appears at the start of its time")
    a = ap.parse_args()
    d = json.load(open(a.data))
    ps = []
    for row, readings in zip(d["satellite"]["rows"], d["gauge"]["readings_by_pass"]):
        t = when(row["time"])
        near = min(readings, key=lambda r: abs((when(r["t"]) - t).total_seconds()))
        if abs((when(near["t"]) - t).total_seconds()) <= a.tolerance * 60:
            ps.append({"time": row["time"], "width": row["width_m"], "stage": near["stage_ft"] * FT, "q": int(row["reach_q"]), "dark": row["dark_frac"]})
    n0 = len(ps)
    everyone = ps
    if a.exclude_flag_at_or_above is not None:
        ps = [p for p in ps if p["q"] < a.exclude_flag_at_or_above]
    print(f"tolerance {a.tolerance} min; reach_q screen {a.exclude_flag_at_or_above}: {len(ps)} of {n0} pairs kept")
    w, s = [p["width"] for p in ps], [p["stage"] for p in ps]
    if a.mode == "relation":
        slope = corr(w, s) * st.stdev(w) / st.stdev(s)
        res = [x - (st.fmean(w) + slope * (y - st.fmean(s))) for x, y in zip(w, s)]
        print(f"width: min {min(w):.1f} m, max {max(w):.1f} m, median {st.median(w):.1f} m, sample spread {st.stdev(w):.1f} m")
        print(f"rank correlation of width with stage {corr(ranks(w), ranks(s)):+.3f}; straight-line correlation {corr(w, s):+.3f}")
        print(f"straight line: {slope:+.2f} m of width per m of stage; spread of width about the line {st.stdev(res):.1f} m; "
              f"the line takes up {1 - (st.stdev(res) / st.stdev(w)) ** 2:.2f} of the width's variance")
    elif a.mode == "named-passes":
        med = st.median(p["width"] for p in everyone)
        for p in everyone:
            if any(p["time"].startswith(nm) for nm in a.name):
                rank = sorted(x["width"] for x in everyone).index(p["width"]) + 1
                print(f"  {p['time']}  width {p['width']:.1f} m ({p['width'] - med:+.1f} m from the median, rank {rank} of {len(everyone)} from the narrowest)  "
                      f"stage {p['stage']:.2f} m  reach_q {p['q']}  dark_frac {p['dark']:.3f}")
        far = sorted(everyone, key=lambda p: -abs(p["width"] - med))[:5]
        print("the five widths furthest from the median: " + "; ".join(f"{p['time'][:10]} {p['width'] - med:+.1f} m (q {p['q']}, dark {p['dark']:.3f}, stage {p['stage']:.2f})" for p in far))
    elif a.mode == "by-stage":
        ordered = sorted(ps, key=lambda p: p["stage"])
        k = len(ordered) // 3
        for name, grp in (("lowest third of stage", ordered[:k]), ("middle third", ordered[k:2 * k]), ("highest third", ordered[2 * k:])):
            ws = [p["width"] for p in grp]
            print(f"{name} ({grp[0]['stage']:.2f} to {grp[-1]['stage']:.2f} m): n={len(ws)}, median width {st.median(ws):.1f} m, sample spread {st.stdev(ws):.1f} m")


main()
