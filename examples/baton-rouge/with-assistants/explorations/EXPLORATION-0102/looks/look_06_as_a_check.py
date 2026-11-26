"""Would width, used with no gauge, single out the passes whose height is off?

Satellite fields only: inside each overpass track, fit height on width leaving one pass out, and ask how far
that pass's height sits from what its width implies. All 52 passes (no gauge needed). Then the same with one
line for all tracks, which is what a user who did not know about tracks would do.
"""
import sys
from common import load, pairs, tracks, fit, median, HEIGHT_DEPARTED

d = load(sys.argv[1])
P = sorted(pairs(d, 15.0), key=lambda p: p["time"])
lab, _ = tracks(P)
for p, l in zip(P, lab):
    p["track"] = l
med = median([p["wse_m"] - p["stage_m"] for p in P if p["stage_m"] is not None])


def loo(S, tag):
    out = []
    for i, p in enumerate(S):
        R = S[:i] + S[i + 1:]
        a, b, s, _ = fit([q["width_m"] for q in R], [q["wse_m"] for q in R])
        miss = p["wse_m"] - (a + b * p["width_m"])
        out.append((p, miss, s, tag))
    return out


def report(res, title):
    print(title)
    res = sorted(res, key=lambda r: -abs(r[1] / r[2]))
    print("  rank date       track width_m  wse_m  height minus width-implied (m)  in units of the fit scatter  | height departure from gauge (m)")
    for k, (p, miss, s, tag) in enumerate(res[:8], 1):
        dep = "n/a (unpaired)" if p["stage_m"] is None else "%+.3f" % (p["wse_m"] - p["stage_m"] - med)
        print("  %2d   %s  %s  %7.1f %6.3f   %+6.2f   %+5.2f  | %s" % (k, p["date"], p["track"], p["width_m"], p["wse_m"], miss, miss / s, dep))
    for dte in HEIGHT_DEPARTED:
        k = [r[0]["date"] for r in res].index(dte) + 1
        r = res[k - 1]
        print("  the pass of %s (height known to depart): rank %d of %d, %+.2f m, %+.2f scatters" % (dte, k, len(res), r[1], r[1] / r[2]))
    n2 = sum(abs(r[1] / r[2]) > 2 for r in res)
    n3 = sum(abs(r[1] / r[2]) > 3 for r in res)
    print("  passes beyond 2 scatters: %d; beyond 3: %d (of %d)" % (n2, n3, len(res)))
    print("  median leave-one-out scatter of height about the width line: %.2f m" % median([r[2] for r in res]))
    print()


print("median satellite minus gauge height over paired passes: %+.3f m (contains an uncited datum offset; not a bias)\n" % med)
res = []
for L in "ABC":
    res += loo([p for p in P if p["track"] == L], L)
report(res, "A line per track (three lines, tracks known):")
report(loo(P, "all"), "One line for all passes (tracks ignored):")
