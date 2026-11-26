"""REVIEW-001 hole 1: what values does the quality flag take in the working
year, on which passes, and what else in the file could mark a pass? A census,
no fitting beyond the reference line used to say which passes depart."""
import statistics
import sys
from collections import Counter
from common import load, pair

doc = load(sys.argv[1])
rows = doc["satellite"]["rows"]
print(f"passes delivered in the working year: {len(rows)}")
c = Counter(int(r["reach_q"]) for r in rows)
print("reach_q census over all delivered passes: " + ", ".join(f"value {v}: {c.get(v, 0)}" for v in (0, 1, 2, 3)))
print(f"   so no pass has reach_q 0, and 'reach_q below 2' is the same set as 'reach_q equal to 1' ({c.get(1, 0)} passes)")
print("ice_clim_f census: " + ", ".join(f"value {k}: {v}" for k, v in sorted(Counter(r['ice_clim_f'] for r in rows).items())))
have = sorted(rows[0].keys())
print("fields each pass carries in the working file: " + ", ".join(have))
want = ["reach_q_b", "xovr_cal_q", "n_good_nod", "obs_frac_n", "partial_f", "crid", "cycle_id", "pass_id", "wse_r_u", "slope_u", "node_dist"]
print("fields NOT in the working file (names from the signed pages datasets/swot-river-lake.md and datasets/swot-lakes.md where they give them, "
      "otherwise from the analyst's memory of the product and to be checked): " + ", ".join(w for w in want if w not in have))
pairs, unmatched = pair(doc, 60, True)
x = [p["gauge_m"] for p in pairs]
y = [p["wse_m"] for p in pairs]
sl = sorted((y[j] - y[i]) / (x[j] - x[i]) for i in range(len(x)) for j in range(i + 1, len(x)) if abs(x[j] - x[i]) > 0.25)
b = statistics.median(sl)
a = statistics.median(v - b * u for u, v in zip(x, y))
for p in pairs:
    p["dep"] = p["wse_m"] - (a + b * p["gauge_m"])
print(f"reference line that needs no screen (Theil-Sen over all {len(pairs)} passes, gauge interpolated inside 60 min): slope {b:.4f}")
for v in sorted(c):
    ps = [p for p in pairs if p["reach_q"] == v]
    d = sorted(abs(p["dep"]) for p in ps)
    print(f"reach_q {v}: n={len(ps)}; departing by more than 0.5 m: {sum(k > 0.5 for k in d)}; by more than 0.3 m: {sum(k > 0.3 for k in d)}; "
          f"median absolute departure {statistics.median(d):.4f} m; gauge elevation {min(p['gauge_m'] for p in ps):.3f} to {max(p['gauge_m'] for p in ps):.3f} m")
for p in pairs:
    if p["reach_q"] >= 2:
        print(f"   reach_q 2 pass {p['time'][:16]}: departure {p['dep']:+.3f} m, gauge {p['gauge_m']:.3f} m, wse_u {p['wse_u_m']:.3f} m, "
              f"dark_frac {p['dark_frac']:.3f}, slope {p['slope']*1e6:+.1f} ppm, width {p['width_m']:.0f} m")
n = len(pairs)
bad = [p for p in pairs if abs(p["dep"]) > 0.5]
fl = [p for p in pairs if p["reach_q"] >= 2]
hit = [p for p in fl if abs(p["dep"]) > 0.5]
print(f"the flag as a detector of departures beyond 0.5 m: flagged {len(fl)} of {n}, departing {len(bad)} of {n}, flagged and departing {len(hit)}; "
      f"share of flagged passes that depart {len(hit)}/{len(fl)}, share of departing passes that are flagged {len(hit)}/{len(bad)}")
g = sorted(pairs, key=lambda p: p["gauge_m"])
k = n // 3
for name, ps in (("lowest third of stage", g[:k]), ("middle third", g[k:n - k]), ("highest third", g[n - k:])):
    print(f"{name}: n={len(ps)}, gauge {ps[0]['gauge_m']:.2f} to {ps[-1]['gauge_m']:.2f} m, reach_q 2 on {sum(p['reach_q'] >= 2 for p in ps)}, "
          f"departing beyond 0.5 m: {[p['time'][:10] for p in ps if abs(p['dep']) > 0.5]}")
lo = g[0]
print(f"lowest gauge elevation at any pass: {lo['gauge_m']:.3f} m on {lo['time'][:10]}. The file keeps gauge readings only around passes "
      f"({doc['gauge']['readings']} readings), so this is the lowest stage at a pass, not the lowest stage of the year.")
for f, unit in (("wse_u_m", "m"), ("dark_frac", "")):
    v = sorted(r[f] for r in rows)
    print(f"{f} over all {len(v)} passes: min {v[0]:.4f}, median {statistics.median(v):.4f}, third largest {v[-3]:.4f}, second largest {v[-2]:.4f}, largest {v[-1]:.4f} {unit}")
