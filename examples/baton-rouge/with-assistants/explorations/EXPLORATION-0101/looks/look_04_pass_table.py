"""Every paired pass by name: which passes depart from the typical
satellite-minus-gauge difference, and what the product says about them?
The level difference itself is not scored (two vertical references); what is
read here is each pass's departure from the median difference, which a constant
offset cannot touch."""
import statistics
import sys
from common import load, pair

doc = load(sys.argv[1])
pairs, _ = pair(doc, 15)
d = [p["wse_m"] - p["gauge_m"] for p in pairs]
med = statistics.median(d)
mad = statistics.median([abs(v - med) for v in d])
print(f"n={len(pairs)}; median satellite minus gauge {med:+.4f} m (contains an uncited datum offset, not a bias); "
      f"median absolute departure from it {mad:.4f} m; robust sd (1.4826 x MAD) {1.4826*mad:.4f} m")
print("date        time   gauge_m  sat_m   depart_m  wse_u_m  depart/u reach_q dark_frac width_m slope_e6 off_min")
for p, v in zip(pairs, d):
    dep = v - med
    mark = "  <-- beyond 3 robust sd" if abs(dep) > 3 * 1.4826 * mad else ""
    print(f"{p['time'][:10]}  {p['time'][11:16]}  {p['gauge_m']:6.3f}  {p['wse_m']:6.3f}  {dep:+7.3f}  "
          f"{p['wse_u_m']:6.3f}  {dep/p['wse_u_m']:+7.1f}   {p['reach_q']}      {p['dark_frac']:.3f}   "
          f"{p['width_m']:6.1f}  {p['slope']*1e6:7.1f}  {p['offset_min']:5.1f}{mark}")
order = sorted(zip(pairs, d), key=lambda z: -abs(z[1] - med))
print("five largest departures:")
for p, v in order[:5]:
    print(f"  {p['time']}  depart {v-med:+.3f} m, reach_q {p['reach_q']}, wse_u {p['wse_u_m']:.3f} m, "
          f"dark_frac {p['dark_frac']:.3f}, gauge {p['gauge_m']:.3f} m")
ss = sum((v - med) ** 2 for v in d)
print("share of the sum of squared departures carried by the largest 1, 2, 3 passes: " +
      ", ".join(f"{sum((v-med)**2 for _, v in order[:k])/ss:.3f}" for k in (1, 2, 3)))
