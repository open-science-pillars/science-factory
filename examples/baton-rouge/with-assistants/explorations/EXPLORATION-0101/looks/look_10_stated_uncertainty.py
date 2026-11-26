"""Does the product say which passes are bad? (a) the flag as a detector of the
two departing passes; (b) whether the stated uncertainty wse_u accounts for the
scatter of the rest; (c) whether the two alternating overpass geometries differ
(told apart here only by the minute offset pattern of the pass time of day)."""
import statistics
import sys
from common import load, pair, gain

doc = load(sys.argv[1])
pairs, _ = pair(doc, 15)
scr = [p for p in pairs if p["reach_q"] < 2 and p["wse_u_m"] < 0.2]
g = gain(scr)
line = lambda p: g["intercept"] + g["gain"] * p["gauge_m"]
print(f"reference line from the screened passes (n={g['n']}): gain {g['gain']:.4f}, residual sd {g['resid_sd']:.4f} m")
print("(a) all paired passes against that line, by reach_q:")
for q in (1, 2):
    ps = [p for p in pairs if p["reach_q"] == q]
    r = [p["wse_m"] - line(p) for p in ps]
    big = [(p["time"][:10], round(v, 3)) for p, v in zip(ps, r) if abs(v) > 0.5]
    print(f"   reach_q {q}: n={len(ps)}, residual beyond 0.5 m: {len(big)} {big}; median absolute residual {statistics.median([abs(v) for v in r]):.4f} m")
for q in (2,):
    for p in pairs:
        if p["reach_q"] == q:
            print(f"   flagged pass {p['time'][:10]}: residual {p['wse_m']-line(p):+.3f} m, wse_u {p['wse_u_m']:.3f} m, dark_frac {p['dark_frac']:.3f}, "
                  f"gauge {p['gauge_m']:.3f} m, slope {p['slope']*1e6:.1f} ppm")
print("(b) screened passes: residual over stated uncertainty")
z = [r / p["wse_u_m"] for r, p in zip(g["res"], scr)]
u = [p["wse_u_m"] for p in scr]
print(f"   wse_u spans {min(u):.4f} to {max(u):.4f} m, median {statistics.median(u):.4f} m; residual sd {g['resid_sd']:.4f} m; "
      f"sd of residual/wse_u {statistics.stdev(z):.3f}; share within 1: {sum(abs(v)<=1 for v in z)/len(z):.3f}, within 2: {sum(abs(v)<=2 for v in z)/len(z):.3f}")
allu = sorted((p["wse_u_m"], p["time"][:10]) for p in pairs)
print(f"   over all paired passes the three largest wse_u: {[(d, round(v,3)) for v, d in allu[-3:]]}")
dk = sorted((p["dark_frac"], p["time"][:10]) for p in pairs)
print(f"   the five largest dark_frac: {[(d, round(v,3)) for v, d in dk[-5:]]}")
hi = [abs(r) for r, p in zip(g["res"], scr) if p["dark_frac"] >= 0.1]
lo = [abs(r) for r, p in zip(g["res"], scr) if p["dark_frac"] < 0.1]
print(f"   screened passes, median absolute residual with dark_frac at or above 0.1: {statistics.median(hi):.4f} m (n={len(hi)}); below 0.1: {statistics.median(lo):.4f} m (n={len(lo)})")
print("(c) by overpass geometry, split on the gauge reading offset pattern (pass minute):")
groups = {}
for r, p in zip(g["res"], scr):
    key = p["time"][14:16]
    groups.setdefault(key, []).append(r)
for k in sorted(groups, key=lambda k: -len(groups[k]))[:6]:
    v = groups[k]
    if len(v) >= 3:
        print(f"   passes at minute :{k} n={len(v)}, mean residual {statistics.fmean(v):+.4f} m, sd {statistics.stdev(v):.4f} m")
print(f"   distinct pass minutes: {len(groups)}")
