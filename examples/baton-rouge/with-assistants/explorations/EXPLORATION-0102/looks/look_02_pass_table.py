"""Every Version D pass by date: width, stage at the pass, height, flags. Fills and gaps counted."""
import sys
from common import load, pairs, median, sd

d = load(sys.argv[1])
P = pairs(d, 15.0)
print("collection:", d["satellite"]["collection_named"], "| passes:", len(P))
print("keys per pass:", sorted(d["satellite"]["rows"][0].keys()))
print("gauge approval present:", d["gauge"]["approval_present"], "| readings kept within", d["gauge"]["window_minutes"], "min")
w = [p["width_m"] for p in P]
print("width_m: none=%d, <=0 or < -1e6 fills=%d" % (sum(v is None for v in w), sum(v is not None and v <= 0 for v in w)))
ok = [v for v in w if v is not None and v > 0]
print("width_m over %d passes: min %.1f  median %.1f  max %.1f  sd %.1f m" % (len(ok), min(ok), median(ok), max(ok), sd(ok)))
print("unpaired at 15 min:", [(p["date"], round(p["gap_min"], 1)) for p in P if p["stage_m"] is None])
print()
print("date        stage_m  wse_m   width_m  wse_u  slope_ppm reach_q dark_frac ice gap_min")
for p in sorted(P, key=lambda p: p["time"]):
    st = "   n/a " if p["stage_m"] is None else "%7.3f" % p["stage_m"]
    print("%s %s %7.3f %8.1f %6.3f %9.1f %7s %9.3f %3s %6.1f" % (
        p["date"], st, p["wse_m"], p["width_m"], p["wse_u_m"], p["slope"] * 1e6,
        p["reach_q"], p["dark_frac"], p["ice_clim_f"], p["gap_min"]))
