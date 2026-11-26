"""Where, by stage, does the satellite not follow the gauge? Uses passes with
reach_q below 2 and, separately, also without the one unflagged departing pass,
so the reader can see both. Reports the departure from the median difference by
stage third, the gain in the lower and upper half of stage, and whether the
departure goes with a rising or falling river."""
import statistics
import sys
from common import load, pair, gain, ols

doc = load(sys.argv[1])
pairs, _ = pair(doc, 15)
sets = (("reach_q below 2", [p for p in pairs if p["reach_q"] < 2]),
        ("reach_q below 2, without 2024-03-26", [p for p in pairs if p["reach_q"] < 2 and not p["time"].startswith("2024-03-26")]),
        ("all paired", pairs))
for name, ps in sets:
    d = [p["wse_m"] - p["gauge_m"] for p in ps]
    med = statistics.median(d)
    order = sorted(range(len(ps)), key=lambda i: ps[i]["gauge_m"])
    k = len(ps) // 3
    print(f"{name}: n={len(ps)}, median difference {med:+.4f} m (uncited datum offset inside it)")
    for label, idx in (("lowest third", order[:k]), ("middle third", order[k:len(ps) - k]), ("highest third", order[len(ps) - k:])):
        dep = [d[i] - med for i in idx]
        g = [ps[i]["gauge_m"] for i in idx]
        print(f"   {label}: n={len(idx)}, gauge {min(g):.2f} to {max(g):.2f} m, mean departure {statistics.fmean(dep):+.4f} m, "
              f"sd {statistics.stdev(dep):.4f} m, largest {max(dep, key=abs):+.3f} m")
    half = len(ps) // 2
    lo = [ps[i] for i in order[:half]]
    hi = [ps[i] for i in order[half:]]
    for label, sub in (("lower half of stage", lo), ("upper half of stage", hi)):
        sub = sorted(sub, key=lambda p: p["when"])
        g = gain(sub)
        print(f"   gain in the {label}: n={g['n']}, {g['gain']:.4f} [{g['lo']:.4f}, {g['hi']:.4f}], residual sd {g['resid_sd']:.4f} m")
    g = gain(ps)
    rate = [p["gauge_rate_m_per_day"] for p in ps]
    b, a0, _, se = ols(rate, g["res"])
    rising = [r for r, q in zip(g["res"], rate) if q > 0.02]
    falling = [r for r, q in zip(g["res"], rate) if q < -0.02]
    print(f"   residual from the straight line against the gauge's rate of change around the pass: slope {b:+.4f} m per (m/day), "
          f"plain standard error {se:.4f}; rate spans {min(rate):+.3f} to {max(rate):+.3f} m/day")
    print(f"   mean residual when rising faster than 0.02 m/day: {statistics.fmean(rising):+.4f} m (n={len(rising)}); "
          f"falling faster than 0.02 m/day: {statistics.fmean(falling):+.4f} m (n={len(falling)})")
    yrs = [(p["when"] - ps[0]["when"]).total_seconds() / 86400 / 365.25 for p in ps]
    b, a0, _, se = ols(yrs, g["res"])
    print(f"   residual against time: {b:+.4f} m per year, plain standard error {se:.4f}")
