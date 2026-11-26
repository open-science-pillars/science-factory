"""Does width rise and fall with stage? Levels and changes, all pairs and by track, with and without named passes."""
import sys
from common import load, pairs, tracks, pearson, spearman, fit, sd, HEIGHT_DEPARTED

d = load(sys.argv[1])
P = sorted(pairs(d, 15.0), key=lambda p: p["time"])
lab, _ = tracks(P)
for p, l in zip(P, lab):
    p["track"] = l
Q = [p for p in P if p["stage_m"] is not None]
print("paired at 15 min: %d of %d (gauge provisional throughout)" % (len(Q), len(P)))


def row(name, S):
    x = [p["stage_m"] for p in S]
    y = [p["width_m"] for p in S]
    a, b, s, _ = fit(x, y)
    se = s / (sd(x) * (len(x) - 1) ** 0.5)
    eq = s / abs(b) if b else float("nan")
    print("%-44s n=%2d  r=%+.3f  rho=%+.3f  slope %+6.2f (se %.2f) m width per m stage  resid sd %5.1f m  "
          "stage-equivalent scatter %5.2f m  stage sd %.2f m" % (name, len(x), pearson(x, y), spearman(x, y), b, se, s, eq, sd(x)))


print("\nLEVELS: width_m against stage_m (stage span %.2f to %.2f m)" % (min(p["stage_m"] for p in Q), max(p["stage_m"] for p in Q)))
row("all pairs", Q)
row("without 2024-02-12 (widest, 937.3 m)", [p for p in Q if p["date"] != "2024-02-12"])
row("without the two height-departed passes", [p for p in Q if p["date"] not in HEIGHT_DEPARTED])
row("without all three", [p for p in Q if p["date"] not in HEIGHT_DEPARTED + ("2024-02-12",)])
for L in "ABC":
    row("track %s" % L, [p for p in Q if p["track"] == L])
row("track A without 2024-02-12", [p for p in Q if p["track"] == "A" and p["date"] != "2024-02-12"])
row("track B without 2024-03-26", [p for p in Q if p["track"] == "B" and p["date"] != "2024-03-26"])
row("track C without 2024-10-30", [p for p in Q if p["track"] == "C" and p["date"] != "2024-10-30"])

# track means removed (one constant per track), then pooled
print("\nLEVELS with one constant per track removed (three constants fitted after seeing the tracks):")
import statistics
R = []
for L in "ABC":
    S = [p for p in Q if p["track"] == L]
    mw = statistics.mean(p["width_m"] for p in S)
    ms = statistics.mean(p["stage_m"] for p in S)
    for p in S:
        R.append(dict(p, width_m=p["width_m"] - mw, stage_m=p["stage_m"] - ms))
row("pooled, track constants removed", R)
row("same, without 2024-02-12", [p for p in R if p["date"] != "2024-02-12"])

print("\nSame scores for the HEIGHT, for scale (wse_m against stage_m; a level across datums, shown only as a correlation):")
x = [p["stage_m"] for p in Q]; y = [p["wse_m"] for p in Q]
print("height all pairs: n=%d r=%+.4f rho=%+.4f" % (len(x), pearson(x, y), spearman(x, y)))


def changes(S, key):
    return [b[key] - a[key] for a, b in zip(S[:-1], S[1:])]


print("\nCHANGES between consecutive paired passes (the signed recipe's form):")
for name, S in [("all pairs, consecutive", Q)] + [("track %s, consecutive within track" % L, [p for p in Q if p["track"] == L]) for L in "ABC"]:
    ds, dw, dh = changes(S, "stage_m"), changes(S, "width_m"), changes(S, "wse_m")
    print("%-40s n=%2d  width change vs stage change r=%+.3f rho=%+.3f | height change vs stage change r=%+.4f | "
          "sd of width change %.1f m, of stage change %.3f m" % (name, len(ds), pearson(ds, dw), spearman(ds, dw), pearson(ds, dh), sd(dw), sd(ds)))
big = [(a, b) for a, b in zip(changes(Q, "stage_m"), changes(Q, "width_m")) if abs(a) >= 1.0]
print("consecutive changes with |stage change| >= 1 m: n=%d, width change has the same sign as stage change in %d" % (
    len(big), sum((a > 0) == (b > 0) for a, b in big)))
