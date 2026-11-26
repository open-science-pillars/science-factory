"""REVIEW-001 holes 3 and 4: can this year tell a gain above one from the
other things that would look the same? On the screened pairs, hold the gain
at exactly one and allow one other term at a time: a drift in time, a step at
low stage, the reach slope times a distance. Compare how well each fits with
the free gain. Then the size of gain that the river's own slope would give
for a gauge that is not at the point the reach height refers to: the reach
slope rises with stage, so each kilometre of offset adds (rise of slope per
metre of stage) times one kilometre to the gain. The distance on the command
line is the one the signed recipe states for this pair; whether it is the
along-river distance to the reach centre is not known."""
import statistics
import sys
from common import load, pair
from fits import fit, years, SETS

doc = load(sys.argv[1])
recipe_km = float(sys.argv[2])
pairs, _ = pair(doc, 15)
for name, keep in SETS[2:]:
    ps = [p for p in pairs if keep(p)]
    y = [p["wse_m"] for p in ps]
    g = [p["gauge_m"] for p in ps]
    tt = years(ps)
    s = [p["slope"] for p in ps]
    cut = sorted(g)[len(g) // 3 - 1]
    low = [1.0 if v <= cut else 0.0 for v in g]
    print(f"== {name}: n={len(ps)}")
    f = fit(y, [], fixed=g)
    print(f"   gain held at one, constant offset only: residual sd {f['sd']:.4f} m, residual lag-1 {f['lag1']:+.3f}")
    f = fit(y, [g])
    print(f"   free gain: {f['coef'][0]:.4f} (plain standard error {f['se'][0]:.4f}); residual sd {f['sd']:.4f} m, residual lag-1 {f['lag1']:+.3f}")
    f = fit(y, [tt], fixed=g)
    print(f"   gain held at one, drift in time: {f['coef'][0]:+.4f} m per year (plain standard error {f['se'][0]:.4f}); residual sd {f['sd']:.4f} m, residual lag-1 {f['lag1']:+.3f}")
    f = fit(y, [low], fixed=g)
    print(f"   gain held at one, step for the lowest third of stage (gauge at or below {cut:.2f} m, n={int(sum(low))}): {f['coef'][0]:+.4f} m (plain standard error {f['se'][0]:.4f}); "
          f"residual sd {f['sd']:.4f} m, residual lag-1 {f['lag1']:+.3f}")
    f = fit(y, [s], fixed=g)
    print(f"   gain held at one, reach slope times a distance: {f['coef'][0]:.0f} m (plain standard error {f['se'][0]:.0f} m); residual sd {f['sd']:.4f} m, residual lag-1 {f['lag1']:+.3f}")
    f = fit(y, [g, low])
    print(f"   free gain and the low-stage step together: gain {f['coef'][0]:.4f} (plain standard error {f['se'][0]:.4f}), step {f['coef'][1]:+.4f} m (plain standard error {f['se'][1]:.4f}); residual sd {f['sd']:.4f} m")
    fs = fit([v * 1e6 for v in s], [g])
    per_km = fs["coef"][0] * 1e-6 * 1000.0
    excess = fit(y, [g])["coef"][0] - 1.0
    print(f"   the product's reach slope rises by {fs['coef'][0]:.3f} ppm per metre of gauge elevation (plain standard error {fs['se'][0]:.3f}); "
          f"so one kilometre between the gauge and the point the reach height refers to adds {per_km:.4f} to the gain")
    print(f"   at the distance the signed recipe states ({recipe_km:.2f} km) geometry alone gives a gain excess of {per_km * recipe_km:.4f}, against {excess:.4f} seen; "
          f"the distance that would give all of what is seen is {excess / per_km:.2f} km")
    hi = sorted(ps, key=lambda p: p["gauge_m"])
    third = len(hi) // 3
    for label, grp in (("lowest third", hi[:third]), ("middle third", hi[third:len(hi) - third]), ("highest third", hi[len(hi) - third:])):
        r0 = fit(y, [], fixed=g)["res"]
        rr = [r0[ps.index(p)] for p in grp]
        print(f"   {label} (n={len(grp)}, gauge {grp[0]['gauge_m']:.2f} to {grp[-1]['gauge_m']:.2f} m): mean satellite minus gauge, less the set's mean, {statistics.fmean(rr):+.4f} m; sd {statistics.stdev(rr):.4f} m; "
              f"dates {grp[0]['time'][:10] if False else min(p['time'][:10] for p in grp)} to {max(p['time'][:10] for p in grp)}")
