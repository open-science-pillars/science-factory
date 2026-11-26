"""Two things LOOK-010 part (c) could not tell (its split by pass minute was a
bad key: 22 groups). (1) Do the overpass tracks differ? The record carries no
pass number, so passes are grouped by phase in the repeat cycle: passes whose
times differ by a whole number of 20.86455-day cycles are the same track.
(2) Does a time term move the gain (a slow drift between the two records can
leak into the gain through the seasonal cycle)?"""
import math
import statistics
import sys
from common import load, pair, gain

CYCLE = 20.86455
doc = load(sys.argv[1])
pairs, _ = pair(doc, 60, True)   # all 52 passes, gauge interpolated, so no track loses a pass to the tolerance
t0 = pairs[0]["when"]
tracks = []
for p in pairs:
    ph = ((p["when"] - t0).total_seconds() / 86400) % CYCLE
    for tr in tracks:
        if min(abs(ph - tr["ph"]), CYCLE - abs(ph - tr["ph"])) < 0.05:
            tr["ps"].append(p)
            break
    else:
        tracks.append({"ph": ph, "ps": [p]})
scr = [p for p in pairs if p["reach_q"] < 2 and p["wse_u_m"] < 0.2]
g = gain(scr)
line = lambda p: g["intercept"] + g["gain"] * p["gauge_m"]
print(f"all 52 passes at 60 min interpolated; screened line n={g['n']}, gain {g['gain']:.4f}; tracks found by cycle phase: {len(tracks)}")
for tr in sorted(tracks, key=lambda tr: tr["ph"]):
    ps = tr["ps"]
    r = [p["wse_m"] - line(p) for p in ps]
    ok = [v for v, p in zip(r, ps) if p["reach_q"] < 2 and p["wse_u_m"] < 0.2]
    print(f"   track at phase {tr['ph']:6.2f} d: n={len(ps)}, first {ps[0]['time'][:16]}, median width {statistics.median([p['width_m'] for p in ps]):.0f} m, "
          f"median dark_frac {statistics.median([p['dark_frac'] for p in ps]):.3f}, flagged {sum(p['reach_q']>=2 for p in ps)}, "
          f"screened n={len(ok)} mean residual {statistics.fmean(ok):+.4f} m sd {statistics.stdev(ok) if len(ok)>1 else float('nan'):.4f} m; "
          f"departing passes: {[p['time'][:10] for p, v in zip(ps, r) if abs(v) > 0.5]}")

# (2) time term
def fit_time(ps):
    x1 = [p["gauge_m"] for p in ps]
    x2 = [(p["when"] - t0).total_seconds() / 86400 / 365.25 for p in ps]
    y = [p["wse_m"] for p in ps]
    n = len(ps)
    m1, m2, my = statistics.fmean(x1), statistics.fmean(x2), statistics.fmean(y)
    s11 = sum((a - m1) ** 2 for a in x1); s22 = sum((b - m2) ** 2 for b in x2)
    s12 = sum((a - m1) * (b - m2) for a, b in zip(x1, x2))
    s1y = sum((a - m1) * (c - my) for a, c in zip(x1, y)); s2y = sum((b - m2) * (c - my) for b, c in zip(x2, y))
    det = s11 * s22 - s12 * s12
    gn = (s1y * s22 - s2y * s12) / det; dr = (s2y * s11 - s1y * s12) / det
    res = [c - my - gn * (a - m1) - dr * (b - m2) for a, b, c in zip(x1, x2, y)]
    s2 = sum(r * r for r in res) / (n - 3)
    return gn, math.sqrt(s2 * s22 / det), dr, math.sqrt(s2 * s11 / det)

for name, ps in (("all", pairs), ("reach_q below 2", [p for p in pairs if p["reach_q"] < 2]), ("reach_q below 2 and wse_u below 0.2 m", scr)):
    g0 = gain(ps)
    gn, gse, dr, dse = fit_time(ps)
    print(f"{name}: n={len(ps)}, gain without a time term {g0['gain']:.4f}; with one {gn:.4f} (plain standard error {gse:.4f}), "
          f"drift {dr:+.4f} m per year (plain standard error {dse:.4f})")
