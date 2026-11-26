"""How much do my choices move the answer: pairing tolerance, half of the year, and which passes are left out."""
import sys
from common import load, pairs, tracks, pearson, spearman, fit, sd, mean

d = load(sys.argv[1])


def setup(tol):
    P = sorted(pairs(d, tol), key=lambda p: p["time"])
    lab, _ = tracks(P)
    for p, l in zip(P, lab):
        p["track"] = l
    return [p for p in P if p["stage_m"] is not None]


def line(name, S):
    x = [p["stage_m"] for p in S]; y = [p["width_m"] for p in S]
    a, b, s, _ = fit(x, y)
    print("  %-34s n=%2d r=%+.3f rho=%+.3f slope %+5.2f m/m resid sd %5.1f m width at 5 m stage %.1f m" % (name, len(x), pearson(x, y), spearman(x, y), b, s, a + 5 * b))


for tol in (15.0, 60.0, 7.0):
    Q = setup(tol)
    print("pairing tolerance %g min: %d pairs" % (tol, len(Q)))
    line("all tracks, one line", Q)
    for L in "ABC":
        line("track " + L, [p for p in Q if p["track"] == L])
Q = setup(15.0)
print("\nhalves of the year (15 min pairing): is each track's line the same in both halves?")
for half, S in (("January to June", [p for p in Q if p["date"] < "2024-07-01"]), ("July to December", [p for p in Q if p["date"] >= "2024-07-01"])):
    x = [p["stage_m"] for p in S]
    print(" %s: stage %.2f to %.2f m" % (half, min(x), max(x)))
    line("all tracks, one line", S)
    for L in "ABC":
        line("track " + L, [p for p in S if p["track"] == L])
print("\nfit on January to June, per track, then predict July to December widths:")
for L in "ABC":
    S1 = [p for p in Q if p["track"] == L and p["date"] < "2024-07-01"]
    S2 = [p for p in Q if p["track"] == L and p["date"] >= "2024-07-01"]
    a, b, s, _ = fit([p["stage_m"] for p in S1], [p["width_m"] for p in S1])
    e = [p["width_m"] - (a + b * p["stage_m"]) for p in S2]
    print("  track %s: n=%d later passes, mean miss %+.1f m, sd %.1f m, worst %+.1f m (first-half scatter %.1f m)" % (L, len(e), mean(e), sd(e), max(e, key=abs), s))
