"""Do the passes fall into overpass tracks, and does the reported width differ by track at like stage?"""
import sys
from common import load, pairs, tracks, mean, median, sd, t

d = load(sys.argv[1])
P = sorted(pairs(d, 15.0), key=lambda p: p["time"])
lab, ph = tracks(P)
for L in sorted(set(lab)):
    S = [p for p, l in zip(P, lab) if l == L]
    phs = [x for x, l in zip(ph, lab) if l == L]
    hrs = sorted(set(t(p["time"]).strftime("%H:%M")[:2] for p in S))
    w = [p["width_m"] for p in S]
    st = [p["stage_m"] for p in S if p["stage_m"] is not None]
    df = [p["dark_frac"] for p in S]
    print("track %s: %2d passes, phase %.3f to %.3f d, width mean %.1f median %.1f sd %.1f min %.1f max %.1f m; "
          "paired stage mean %.2f m (n=%d); dark_frac median %.3f" % (
              L, len(S), min(phs), max(phs), mean(w), median(w), sd(w), min(w), max(w), mean(st), len(st), median(df)))
    print("   dates:", " ".join(p["date"][5:] for p in S))
print()
print("Passes one or two days apart see nearly the same river. Width difference within such pairs:")
print("first_date  track stage_m width_m | next_date track stage_m width_m | d_stage  d_width")
dw = {}
for i in range(len(P) - 1):
    a, b = P[i], P[i + 1]
    gap = (t(b["time"]) - t(a["time"])).total_seconds() / 86400.0
    if gap <= 2.5 and a["stage_m"] is not None and b["stage_m"] is not None:
        key = lab[i] + lab[i + 1]
        dw.setdefault(key, []).append((b["width_m"] - a["width_m"], b["stage_m"] - a["stage_m"]))
        print("%s  %s  %6.3f %7.1f | %s  %s  %6.3f %7.1f | %+6.3f  %+7.1f" % (
            a["date"], lab[i], a["stage_m"], a["width_m"], b["date"], lab[i + 1], b["stage_m"], b["width_m"],
            b["stage_m"] - a["stage_m"], b["width_m"] - a["width_m"]))
for k, v in sorted(dw.items()):
    x = [a for a, _ in v]
    s = [abs(b) for _, b in v]
    print("pairs %s->%s: n=%d, width difference mean %+.1f m, median %+.1f m, sd %.1f m, all negative: %s; "
          "largest stage change inside a pair %.3f m" % (k[0], k[1], len(x), mean(x), median(x), sd(x) if len(x) > 1 else float('nan'),
                                                        all(a < 0 for a in x), max(s)))
