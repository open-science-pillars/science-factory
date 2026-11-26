"""For the two departing passes: is it the satellite or the gauge that jumps?
Print the gauge readings kept around each, and the passes either side."""
import sys
from common import load, pair, t, FT_M

doc = load(sys.argv[1])
pairs, _ = pair(doc, 60, True)
rows = doc["satellite"]["rows"]
for day in ("2024-03-26", "2024-10-30"):
    i = next(k for k, p in enumerate(pairs) if p["time"].startswith(day))
    j = next(k for k, r in enumerate(rows) if r["time"].startswith(day))
    rd = doc["gauge"]["readings_by_pass"][j]
    st = [r["stage_ft"] * FT_M for r in rd]
    print(f"{day}: {len(rd)} gauge readings from {rd[0]['t']} to {rd[-1]['t']}, {min(st):.3f} to {max(st):.3f} m, "
          f"largest step between consecutive readings {max(abs(a-b) for a, b in zip(st, st[1:])):.3f} m")
    for k in range(i - 2, i + 3):
        p = pairs[k]
        print(f"   {p['time'][:16]}  gauge {p['gauge_m']:6.3f} m  satellite {p['wse_m']:6.3f} m  difference {p['wse_m']-p['gauge_m']:+.3f} m  "
              f"reach_q {p['reach_q']}  wse_u {p['wse_u_m']:.3f}  dark_frac {p['dark_frac']:.3f}  width {p['width_m']:.0f} m  slope {p['slope']*1e6:.1f} ppm")
