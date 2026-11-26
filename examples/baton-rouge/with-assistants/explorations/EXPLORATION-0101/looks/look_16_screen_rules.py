"""REVIEW-001 holes 1 and 5, under CHOICE-008: what would a rule have to be
to catch the gross errors, using only what the product says about a pass?
A gross error is a pass more than 0.5 m (also shown: 0.3 m) from a line that
needs no screen. For each product field, every possible cut is tried in both
directions, and the look reports the cuts that remove every gross error they
can, what else they remove, and how wide the range of equally good cuts is."""
import statistics
import sys
from common import load, pair

doc = load(sys.argv[1])
pairs, _ = pair(doc, 60, True)
x = [p["gauge_m"] for p in pairs]
y = [p["wse_m"] for p in pairs]
sl = sorted((y[j] - y[i]) / (x[j] - x[i]) for i in range(len(x)) for j in range(i + 1, len(x)) if abs(x[j] - x[i]) > 0.25)
b = statistics.median(sl)
a = statistics.median(v - b * u for u, v in zip(x, y))
for p in pairs:
    p["dep"] = p["wse_m"] - (a + b * p["gauge_m"])
    p["slope_ppm"] = p["slope"] * 1e6
n = len(pairs)
d = sorted((abs(p["dep"]), p["time"][:10]) for p in pairs)
print(f"all {n} passes, gauge interpolated inside 60 min; line with no screen: slope {b:.4f}")
print("six largest absolute departures: " + ", ".join(f"{t} {v:.3f} m" for v, t in reversed(d[-6:])))
for lim in (0.5, 0.3):
    print(f"gross errors beyond {lim} m: {sum(v > lim for v, _ in d)} of {n} passes ({sum(v > lim for v, _ in d) / n:.3f}): {[t for v, t in d if v > lim]}")
gross = [p for p in pairs if abs(p["dep"]) > 0.5]
gd = {p["time"][:10] for p in gross}
print("for each gross error, its rank in each field (1 = largest of the 52):")
for p in gross:
    parts = []
    for f in ("wse_u_m", "dark_frac", "slope_ppm", "width_m"):
        v = sorted((q[f] for q in pairs), reverse=True)
        parts.append(f"{f} {p[f]:.4g} rank {v.index(p[f]) + 1} from the top, {n - v.index(p[f])} from the bottom")
    print(f"   {p['time'][:10]} (departure {p['dep']:+.3f} m, reach_q {p['reach_q']}): " + "; ".join(parts))
print("single-field rules, every cut tried; a rule removes passes on one side of a cut:")
for f in ("reach_q", "wse_u_m", "dark_frac", "slope_ppm", "width_m"):
    vals = sorted(set(p[f] for p in pairs))
    for side, rm in (("above", lambda p, c: p[f] > c), ("below", lambda p, c: p[f] < c)):
        best = None
        cuts = [(vals[i] + vals[i + 1]) / 2 for i in range(len(vals) - 1)]
        rows = []
        for c in cuts:
            out = [p for p in pairs if rm(p, c)]
            caught = {p["time"][:10] for p in out} & gd
            rows.append((c, len(out), caught))
        most = max(len(r[2]) for r in rows)
        if most == 0:
            print(f"   {f}, remove {side} a cut: no cut removes a gross error without first removing every pass on that side; best catches 0")
            continue
        good = [r for r in rows if len(r[2]) == most]
        fewest = min(r[1] for r in good)
        tight = [r for r in good if r[1] == fewest]
        lo_c, hi_c = min(r[0] for r in tight), max(r[0] for r in tight)
        # the neighbouring values that bound the range of equally good cuts
        lo_v = max(v for v in vals if v <= lo_c)
        hi_v = min(v for v in vals if v >= hi_c)
        print(f"   {f}, remove {side} a cut: catches at most {most} of {len(gd)} gross errors ({sorted(tight[0][2])}); the cheapest such cut removes {fewest} passes "
              f"({fewest - most} of them ordinary); any cut between {lo_v:.4g} and {hi_v:.4g} does the same")
print("two-part rules built from the above:")
rules = [
    ("reach_q at or above 2", lambda p: p["reach_q"] >= 2),
    ("wse_u at or above 0.2 m", lambda p: p["wse_u_m"] >= 0.2),
    ("reach_q at or above 2, or wse_u at or above 0.2 m (lead version 1)", lambda p: p["reach_q"] >= 2 or p["wse_u_m"] >= 0.2),
    ("reach_q at or above 2, or dark_frac at or above 0.5", lambda p: p["reach_q"] >= 2 or p["dark_frac"] >= 0.5),
    ("reach slope below zero, or wse_u at or above 0.2 m", lambda p: p["slope"] < 0 or p["wse_u_m"] >= 0.2),
    ("reach slope below zero, or reach slope above 100 ppm", lambda p: p["slope"] < 0 or p["slope_ppm"] > 100),
]
for name, rm in rules:
    out = [p for p in pairs if rm(p)]
    caught = sorted({p["time"][:10] for p in out} & gd)
    kept = [p for p in pairs if not rm(p)]
    worst = max(abs(p["dep"]) for p in kept)
    print(f"   {name}: removes {len(out)} of {n}, gross errors caught {len(caught)} of {len(gd)} {caught}, ordinary passes removed {len(out) - len(caught)}; "
          f"largest departure left {worst:.3f} m; share of kept passes beyond 0.3 m: {sum(abs(p['dep']) > 0.3 for p in kept)}/{len(kept)}")
print("what the stated uncertainty says on the two gross errors: "
      + "; ".join(f"{p['time'][:10]} departure {abs(p['dep']):.3f} m is {abs(p['dep']) / p['wse_u_m']:.1f} times its wse_u of {p['wse_u_m']:.3f} m" for p in gross))
