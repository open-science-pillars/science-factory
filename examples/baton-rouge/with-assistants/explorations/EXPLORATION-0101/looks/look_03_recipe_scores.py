"""Does the shipped executor's receipt on the working data give the scores the
signed recipe states, and does this exploration's pairing helper reproduce it?"""
import json
import sys
from common import load, pair, change_scores

rec = json.load(open(sys.argv[1]))
doc = load(sys.argv[2])
c = rec["confrontation_on_changes"]
m = rec["matching"]
print("shipped executor receipt, tolerance", m["tolerance_minutes"], "min, collection", rec["collection_named"])
print(f"  passes offered {m['passes_offered']}, paired {m['pairs']}, max offset {m['max_offset_s']:.0f} s")
for u in m["unmatched"]:
    print("  unmatched:", u["time"], "|", u["why"])
print(f"  changes n={c['n']}: mean error {c['mean_error_m']:+.4f} m, 95 pct {c['mean_error_95pct']}, "
      f"RMSD {c['rmsd_m']:.4f} m, correlation {c['correlation']:+.4f}, gauge change spread "
      f"{c['gauge_change_spread_m']:.4f} m, RMSD over spread {c['rmsd_over_spread']:.4f}")
lv = rec["level_difference_not_a_bias"]
print(f"  level difference (not a bias, not scored): mean {lv['mean_m']:+.4f} m, sd {lv['sd_m']:.4f} m, "
      f"min {lv['min_m']:+.4f}, max {lv['max_m']:+.4f}")
print(f"  satellite stated per-pass uncertainty, median {rec['satellite_reported_uncertainty_m']['median']:.4f} m")
print("  gauge approval values used:", rec["approval"]["values_used"])
print("recipe states: 50 of 52 paired; changes n=49 mean +0.0019 m, RMSD 0.3823 m, r +0.9567, spread 1.1959 m")
pairs, un = pair(doc, 15)
s = change_scores(pairs)
print(f"this exploration's helper: paired {len(pairs)}, changes n={s['n']}, mean {s['mean']:+.4f} m, "
      f"RMSD {s['rmsd']:.4f} m, r {s['r']:+.4f}, spread {s['spread']:.4f} m")
for u in un:
    print("  helper unmatched:", u[0], "|", u[1])
