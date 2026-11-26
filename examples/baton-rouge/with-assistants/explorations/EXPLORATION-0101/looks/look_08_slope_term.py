"""Is the gain above one a matter of where the gauge sits in the reach? The
reach elevation is an average over about 10 km and the gauge is a point; if the
gauge is not at the reach's centre, the two differ by the reach slope times a
distance, and the product's own slope grows with stage. Fit
    satellite = a + gain * gauge + L * slope
and see whether the gain goes to one and what distance L comes out."""
import math
import statistics
import sys
from common import load, pair, gain, ols

doc = load(sys.argv[1])
pairs, _ = pair(doc, 15)


def fit2(ps):
    # two-regressor least squares by normal equations
    x1 = [p["gauge_m"] for p in ps]
    x2 = [p["slope"] for p in ps]
    y = [p["wse_m"] for p in ps]
    n = len(ps)
    m1, m2, my = statistics.fmean(x1), statistics.fmean(x2), statistics.fmean(y)
    s11 = sum((a - m1) ** 2 for a in x1)
    s22 = sum((b - m2) ** 2 for b in x2)
    s12 = sum((a - m1) * (b - m2) for a, b in zip(x1, x2))
    s1y = sum((a - m1) * (c - my) for a, c in zip(x1, y))
    s2y = sum((b - m2) * (c - my) for b, c in zip(x2, y))
    det = s11 * s22 - s12 * s12
    g = (s1y * s22 - s2y * s12) / det
    L = (s2y * s11 - s1y * s12) / det
    res = [c - my - g * (a - m1) - L * (b - m2) for a, b, c in zip(x1, x2, y)]
    s2 = sum(r * r for r in res) / (n - 3)
    return g, math.sqrt(s2 * s22 / det), L, math.sqrt(s2 * s11 / det), s12 / math.sqrt(s11 * s22), math.sqrt(s2)


for name, ps in (("reach_q below 2", [p for p in pairs if p["reach_q"] < 2]),
                 ("reach_q below 2 and wse_u below 0.2 m", [p for p in pairs if p["reach_q"] < 2 and p["wse_u_m"] < 0.2])):
    g0 = gain(ps)
    g, gse, L, Lse, r, s = fit2(ps)
    sl = [p["slope"] * 1e6 for p in ps]
    print(f"{name}: n={len(ps)}; product slope spans {min(sl):.1f} to {max(sl):.1f} parts per million; "
          f"correlation of slope with gauge elevation {r:+.3f}")
    print(f"   without the slope term: gain {g0['gain']:.4f}, residual sd {g0['resid_sd']:.4f} m")
    print(f"   with the slope term: gain {g:.4f} (plain standard error {gse:.4f}), L {L:.0f} m (plain standard error {Lse:.0f} m), "
          f"residual sd {s:.4f} m")
