"""REVIEW-001 hole 4, under CHOICE-007: the gain on one footing. The same
pairing (15 minutes, nearest reading), the same pass set across a row, and
both kinds of interval for every fit: gauge alone; with a time term; with the
product's reach slope; with both; and by halves of stage. Then each pass of
the screened set left out in turn, and rising against falling water."""
import statistics
import sys
from common import load, pair
from fits import fit, show, years, SETS

doc = load(sys.argv[1])
pairs, _ = pair(doc, 15)
print("footing: 15 minutes nearest reading; plain interval = Student t on n minus the number of fitted terms; "
      "effective-sample interval = the same widened by the lag-1 effective sample of that fit's residuals, capped at n")


def within(c, h):
    return "includes one" if c - h <= 1.0 <= c + h else "excludes one"


for name, keep in SETS:
    ps = [p for p in pairs if keep(p)]
    y = [p["wse_m"] for p in ps]
    g = [p["gauge_m"] for p in ps]
    tt = years(ps)
    s = [p["slope"] for p in ps]
    print(f"== {name}: n={len(ps)}")
    for label, cols in (("gauge alone", [g]), ("gauge and time", [g, tt]), ("gauge and reach slope", [g, s]), ("gauge, time and reach slope", [g, tt, s])):
        f = fit(y, cols)
        line = f"   {label}: " + show("gain", f) + f"; plain interval {within(f['coef'][0], f['half_plain'][0])}, effective-sample interval {within(f['coef'][0], f['half_eff'][0])}"
        line += f"; residual sd {f['sd']:.4f} m, residual lag-1 {f['lag1']:+.3f}, n_eff {f['n_eff']:.1f}"
        print(line)
        if "time" in label:
            i = 1
            print(f"      drift {f['coef'][i]:+.4f} m per year (plain standard error {f['se'][i]:.4f}; effective-sample 95 pct [{f['coef'][i]-f['half_eff'][i]:+.4f}, {f['coef'][i]+f['half_eff'][i]:+.4f}])")
        if "slope" in label:
            i = len(cols) - 1
            print(f"      distance term {f['coef'][i]:.0f} m (plain standard error {f['se'][i]:.0f} m)")
    med = statistics.median(g)
    for label, half in (("lower half of stage", [p for p in ps if p["gauge_m"] < med]), ("upper half of stage", [p for p in ps if p["gauge_m"] >= med])):
        f = fit([p["wse_m"] for p in half], [[p["gauge_m"] for p in half]])
        print(f"   {label} (split at the median gauge elevation {med:.3f} m), n={len(half)}: " + show("gain", f)
              + f"; effective-sample interval {within(f['coef'][0], f['half_eff'][0])}; residual sd {f['sd']:.4f} m")
    f0 = fit(y, [g])
    r = f0["res"]
    cor = lambda a, b: (sum((u - statistics.fmean(a)) * (v - statistics.fmean(b)) for u, v in zip(a, b))
                        / (sum((u - statistics.fmean(a)) ** 2 for u in a) * sum((v - statistics.fmean(b)) ** 2 for v in b)) ** 0.5)
    print(f"   how tangled the regressors are on this set: correlation of gauge with time {cor(g, tt):+.3f}, gauge with reach slope {cor(g, s):+.3f}, time with reach slope {cor(tt, s):+.3f}")
    up = [v for v, p in zip(r, ps) if p["gauge_rate_m_per_day"] is not None and p["gauge_rate_m_per_day"] > 0.02]
    dn = [v for v, p in zip(r, ps) if p["gauge_rate_m_per_day"] is not None and p["gauge_rate_m_per_day"] < -0.02]
    se = (statistics.variance(up) / len(up) + statistics.variance(dn) / len(dn)) ** 0.5
    print(f"   residual from the gauge-alone line: rising faster than 0.02 m/day mean {statistics.fmean(up):+.4f} m (n={len(up)}), "
          f"falling faster than 0.02 m/day mean {statistics.fmean(dn):+.4f} m (n={len(dn)}), difference {statistics.fmean(up)-statistics.fmean(dn):+.4f} m, plain standard error {se:.4f} m")

name, keep = SETS[2]
ps = [p for p in pairs if keep(p)]
base = fit([p["wse_m"] for p in ps], [[p["gauge_m"] for p in ps]])["coef"][0]
moves = []
for i, p in enumerate(ps):
    rest = ps[:i] + ps[i + 1:]
    moves.append((fit([q["wse_m"] for q in rest], [[q["gauge_m"] for q in rest]])["coef"][0], p["time"][:10]))
moves.sort()
print(f"== leave one out on the {len(ps)} pairs of '{name}': gain {base:.4f}; leave-one-out gains span {moves[0][0]:.4f} (without {moves[0][1]}) to {moves[-1][0]:.4f} (without {moves[-1][1]})")
