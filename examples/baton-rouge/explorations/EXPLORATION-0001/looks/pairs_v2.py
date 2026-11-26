# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Looks at paired passes: one SWOT reach elevation beside the nearest gauge reading inside a tolerance.

Exploring. Each mode answers one question and prints numbers with counts.
The level difference printed here contains the uncited offset between the
two vertical references (the signed recipe says so), so only its spread and
how it varies are read, never its size as a bias.

Version 2, after the review: spreads are sample standard deviations (n - 1), as the recipe's receipt uses, and a
mode lists the flagged pairs one by one. pairs.py is kept as it was run.
"""
import argparse
import datetime as dt
import json
import statistics as st

FT = 0.3048


def when(s):
    return dt.datetime.fromisoformat(s.rstrip("Z"))


def pairs(d, tolerance, rows_key="satellite"):
    out, dropped = [], []
    alt = d["gauge"].get("gauge_datum_altitude_ft", 0.0)
    for row, readings in zip(d[rows_key]["rows"], d["gauge"]["readings_by_pass"]):
        t = when(row["time"])
        near = min(readings, key=lambda r: abs((when(r["t"]) - t).total_seconds()), default=None)
        if near is None or abs((when(near["t"]) - t).total_seconds()) > tolerance * 60 or row.get("wse_m") is None:
            dropped.append(row["time"])
            continue
        g = (near["stage_ft"] + alt) * FT
        out.append({"time": row["time"], "wse": row["wse_m"], "gauge": g, "diff": row["wse_m"] - g, "q": str(row.get("reach_q")),
                    "dark": row.get("dark_frac"), "u": row.get("wse_u_m"), "width": row.get("width_m"),
                    "offset_min": (when(near["t"]) - t).total_seconds() / 60})
    return out, dropped


def describe(name, xs):
    if not xs:
        return f"{name}: n=0"
    return (f"{name}: n={len(xs)}, median {st.median(xs):+.3f} m, mean {st.fmean(xs):+.3f} m, "
            f"sd {st.stdev(xs) if len(xs) > 1 else 0:.3f} m (sample), min {min(xs):+.3f}, max {max(xs):+.3f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("--mode", required=True, choices=["count", "by-flag", "by-stage", "worst", "by-dark", "changes", "limb", "uncertainty", "flagged"])
    ap.add_argument("--tolerance", type=int, default=15)
    ap.add_argument("--exclude-flag-at-or-above", type=int, default=None)
    a = ap.parse_args()
    d = json.load(open(a.data))
    ps, dropped = pairs(d, a.tolerance)
    if a.exclude_flag_at_or_above is not None:
        kept = [p for p in ps if int(p["q"]) < a.exclude_flag_at_or_above]
        print(f"screen: {len(ps) - len(kept)} of {len(ps)} pairs excluded (reach_q at or above {a.exclude_flag_at_or_above})")
        ps = kept
    med = st.median(p["diff"] for p in ps)
    print(f"tolerance {a.tolerance} min: {len(ps)} pairs, {len(dropped)} passes with no reading inside it {dropped}")
    if a.mode == "count":
        print(describe("level difference (satellite minus gauge, contains an uncited datum offset)", [p["diff"] for p in ps]))
        print("gauge stage range over the pairs: %.2f to %.2f m" % (min(p["gauge"] for p in ps), max(p["gauge"] for p in ps)))
        print("pairing offset: max %.1f min" % max(abs(p["offset_min"]) for p in ps))
    elif a.mode == "by-flag":
        for q in sorted({p["q"] for p in ps}):
            grp = [p for p in ps if p["q"] == q]
            print(describe(f"reach_q={q}", [p["diff"] - med for p in grp]) + "  (departure from the median level difference); gauge stage "
                  + "%.2f to %.2f m" % (min(p["gauge"] for p in grp), max(p["gauge"] for p in grp)))
    elif a.mode == "flagged":
        ordered = sorted(ps, key=lambda p: p["gauge"])
        for p in ps:
            if p["q"] not in ("0", "1"):
                rank = ordered.index(p) + 1
                print(f"  {p['time']}  reach_q {p['q']}  gauge {p['gauge']:.2f} m (rank {rank} of {len(ps)} from the lowest)  departure {p['diff'] - med:+.3f} m  "
                      f"dark_frac {p['dark']:.3f}  wse_u {p['u']:.3f} m")
        rest = [p["diff"] - med for p in ps if p["q"] in ("0", "1")]
        print(describe("unflagged pairs", rest))
    elif a.mode == "by-stage":
        ordered = sorted(ps, key=lambda p: p["gauge"])
        k = len(ordered) // 3
        for name, grp in (("lowest third of stage", ordered[:k]), ("middle third", ordered[k:2 * k]), ("highest third", ordered[2 * k:])):
            print(describe(name + " (%.2f to %.2f m)" % (grp[0]["gauge"], grp[-1]["gauge"]), [p["diff"] - med for p in grp])
                  + f"; flags {sorted(p['q'] for p in grp if p['q'] != '0' and p['q'] != '1')}")
    elif a.mode == "worst":
        print("the eight pairs furthest from the median level difference:")
        for p in sorted(ps, key=lambda p: -abs(p["diff"] - med))[:8]:
            print(f"  {p['time']}  departure {p['diff'] - med:+.3f} m  gauge {p['gauge']:.2f} m  reach_q {p['q']}  dark_frac {p['dark']:.3f}  "
                  f"wse_u {p['u']:.3f} m  width {p['width']:.0f} m")
        total = sum((p["diff"] - med) ** 2 for p in ps)
        top = sorted(((p["diff"] - med) ** 2 for p in ps), reverse=True)
        print(f"share of the summed squared departure carried by the worst one: {top[0] / total:.2f}; by the worst three: {sum(top[:3]) / total:.2f}")
    elif a.mode == "by-dark":
        ordered = sorted(ps, key=lambda p: p["dark"])
        k = len(ordered) // 3
        for name, grp in (("lowest third of dark_frac", ordered[:k]), ("middle third", ordered[k:2 * k]), ("highest third", ordered[2 * k:])):
            print(describe(name + " (%.3f to %.3f)" % (grp[0]["dark"], grp[-1]["dark"]), [p["diff"] - med for p in grp]))
    elif a.mode == "changes":
        ds = [(b["wse"] - c["wse"], b["gauge"] - c["gauge"]) for c, b in zip(ps, ps[1:])]
        err = [s - g for s, g in ds]
        ms, mg = st.fmean(s for s, _ in ds), st.fmean(g for _, g in ds)
        r = sum((s - ms) * (g - mg) for s, g in ds) / (sum((s - ms) ** 2 for s, _ in ds) * sum((g - mg) ** 2 for _, g in ds)) ** 0.5
        print(f"changes between consecutive pairs: n={len(ds)}, correlation {r:+.4f}, RMSD {(st.fmean(e * e for e in err)) ** 0.5:.4f} m, "
              f"mean error {st.fmean(err):+.4f} m, gauge change spread {st.stdev([g for _, g in ds]):.4f} m (sample)")
    elif a.mode == "limb":
        rising = [b["diff"] - med for c, b in zip(ps, ps[1:]) if b["gauge"] > c["gauge"]]
        falling = [b["diff"] - med for c, b in zip(ps, ps[1:]) if b["gauge"] <= c["gauge"]]
        print(describe("gauge rising since the pass before", rising))
        print(describe("gauge falling since the pass before", falling))
    elif a.mode == "uncertainty":
        dep = [abs(p["diff"] - med) for p in ps]
        inside = sum(1 for p in ps if abs(p["diff"] - med) <= 2 * p["u"])
        print(f"median stated wse_u {st.median(p['u'] for p in ps):.3f} m; median absolute departure {st.median(dep):.3f} m; "
              f"{inside} of {len(ps)} departures are within twice the pass's own stated uncertainty")
        big = sorted(ps, key=lambda p: -p["u"])[:3]
        print("largest stated uncertainties: " + "; ".join(f"{p['time']} u={p['u']:.3f} m q={p['q']} departure {p['diff'] - med:+.3f}" for p in big))


main()
