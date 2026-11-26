"""Does the pairing choice move anything? Tolerances of 5, 15, 30 and 60
minutes with the nearest reading, and linear interpolation of the gauge to the
pass time. Reported for all paired passes and for reach_q below 2 with wse_u
below 0.2 m. Also: what are the passes that 15 minutes leaves unpaired?"""
import sys
from common import load, pair, gain, change_scores

doc = load(sys.argv[1])
for tol, interp in ((5, False), (15, False), (30, False), (60, False), (60, True)):
    pairs, un = pair(doc, tol, interp)
    how = "interpolated to the pass time" if interp else "nearest reading"
    line = f"tolerance {tol} min, {how}: paired {len(pairs)} of {len(pairs)+len(un)}"
    for name, ps in (("all", pairs), ("screened", [p for p in pairs if p["reach_q"] < 2 and p["wse_u_m"] < 0.2])):
        g = gain(ps)
        s = change_scores(ps)
        line += f"; {name}: n={g['n']}, gain {g['gain']:.4f} [{g['lo']:.4f}, {g['hi']:.4f}], change RMSD {s['rmsd']:.4f} m, r {s['r']:+.4f}"
    print(line)
p15, un15 = pair(doc, 15)
p60, _ = pair(doc, 60, True)
names = {u[0] for u in un15}
g = gain([p for p in p60 if p["reach_q"] < 2 and p["wse_u_m"] < 0.2])
for p in p60:
    if p["time"] in names:
        print(f"unpaired at 15 min: {p['time']}, nearest reading {p['offset_min']:.1f} min away, {p['n_readings']} readings kept around it, "
              f"reach_q {p['reach_q']}, wse_u {p['wse_u_m']:.3f} m, dark_frac {p['dark_frac']:.3f}, gauge (interpolated) {p['gauge_m']:.3f} m, "
              f"satellite {p['wse_m']:.3f} m, residual from the screened line {p['wse_m'] - (g['intercept'] + g['gain']*p['gauge_m']):+.3f} m, "
              f"gauge rate {p['gauge_rate_m_per_day']:+.3f} m/day")
import statistics
gaps = [p["n_readings"] for p in p60]
print(f"gauge readings kept around each pass: min {min(gaps)}, median {statistics.median(gaps)}, max {max(gaps)}")
