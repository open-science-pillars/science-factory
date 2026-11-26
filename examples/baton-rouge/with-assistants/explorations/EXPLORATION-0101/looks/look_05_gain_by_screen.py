"""How large is the gain of satellite on gauge (the size of rise and fall the
satellite sees per metre at the gauge), and how much does it move with which
passes are left out? The intercept absorbs the constant datum offset.
Screens tried, each a candidate and none chosen here."""
import statistics
import sys
from common import load, pair, gain, change_scores

doc = load(sys.argv[1])
pairs, _ = pair(doc, 15)
BAD_Q1 = "2024-03-26"
BAD_Q2 = "2024-10-30"
screens = [
    ("all paired passes (the recipe's worked example)", lambda p: True),
    ("reach_q below 2 (leave out flagged)", lambda p: p["reach_q"] < 2),
    ("leave out only the one flagged pass that departs", lambda p: not p["time"].startswith(BAD_Q2)),
    ("leave out only the one unflagged pass that departs", lambda p: not p["time"].startswith(BAD_Q1)),
    ("leave out both departing passes by date", lambda p: not p["time"].startswith((BAD_Q1, BAD_Q2))),
    ("reach_q below 2 and wse_u below 0.2 m", lambda p: p["reach_q"] < 2 and p["wse_u_m"] < 0.2),
    ("reach_q below 2 and dark_frac below 0.5", lambda p: p["reach_q"] < 2 and p["dark_frac"] < 0.5),
    ("wse_u below 0.2 m only", lambda p: p["wse_u_m"] < 0.2),
]
print("gain = slope of satellite wse on gauge elevation; interval uses the lag-1 effective sample of the residuals, capped at n")
print("the requester's stated judgment: within about five per cent, read here as the interval inside 0.95 to 1.05")
for name, keep in screens:
    ps = [p for p in pairs if keep(p)]
    g = gain(ps)
    s = change_scores(ps)
    inside = 0.95 <= g["lo"] and g["hi"] <= 1.05
    print(f"- {name}: n={g['n']}, gain {g['gain']:.4f} [{g['lo']:.4f}, {g['hi']:.4f}], inside 0.95 to 1.05: {inside}; "
          f"residual sd {g['resid_sd']:.4f} m, residual lag-1 {g['resid_lag1']:+.3f}, n_eff {g['n_eff']:.1f}; "
          f"change scores n={s['n']} RMSD {s['rmsd']:.4f} m, r {s['r']:+.4f}, mean {s['mean']:+.4f} m")
# Theil-Sen, which needs no screen
x = [p["gauge_m"] for p in pairs]
y = [p["wse_m"] for p in pairs]
sl = sorted((y[j] - y[i]) / (x[j] - x[i]) for i in range(len(x)) for j in range(i + 1, len(x)) if abs(x[j] - x[i]) > 0.25)
print(f"- Theil-Sen median slope over all {len(pairs)} paired passes, pairs of passes at least 0.25 m apart in stage "
      f"(n slopes {len(sl)}): {statistics.median(sl):.4f}")
