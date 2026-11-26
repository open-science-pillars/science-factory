"""REVIEW-001 hole 5: lead version 1 said the other reading of 'five per cent'
(the recipe's change RMSD over the gauge change spread) stays above five per
cent under any screen tried, and no look printed it. Print it for every
screen of LOOK-005."""
import sys
from common import load, pair, change_scores

doc = load(sys.argv[1])
pairs, _ = pair(doc, 15)
B1, B2 = "2024-03-26", "2024-10-30"
screens = [
    ("all paired passes", lambda p: True),
    ("reach_q below 2", lambda p: p["reach_q"] < 2),
    ("leave out only the flagged pass that departs", lambda p: not p["time"].startswith(B2)),
    ("leave out only the unflagged pass that departs", lambda p: not p["time"].startswith(B1)),
    ("leave out both departing passes by date", lambda p: not p["time"].startswith((B1, B2))),
    ("reach_q below 2 and wse_u below 0.2 m", lambda p: p["reach_q"] < 2 and p["wse_u_m"] < 0.2),
    ("reach_q below 2 and dark_frac below 0.5", lambda p: p["reach_q"] < 2 and p["dark_frac"] < 0.5),
    ("wse_u below 0.2 m only", lambda p: p["wse_u_m"] < 0.2),
]
lowest = 9.9
for name, keep in screens:
    s = change_scores([p for p in pairs if keep(p)])
    ratio = s["rmsd"] / s["spread"]
    lowest = min(lowest, ratio)
    print(f"- {name}: changes n={s['n']}, RMSD {s['rmsd']:.4f} m, gauge change spread {s['spread']:.4f} m, RMSD over spread {ratio:.4f}, below 0.05: {ratio < 0.05}")
print(f"lowest RMSD over spread under any of these screens: {lowest:.4f}")
