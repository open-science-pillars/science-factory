"""LOOK-008 scored candidate periods badly (fewest groups rewards merging two tracks 1.45 d apart).
A grouping that uses no period at all: the gaps between consecutive passes. A pass that follows the
previous one by about 1.45 d is the second of a close pair; the pass before it is the first; the rest stand alone.
Then read the repeat period off the file, as the interval between passes of one group."""
import sys
from common import load, pairs, tracks, t, median

d = load(sys.argv[1])
P = sorted(pairs(d, 15.0), key=lambda p: p["time"])
lab0, _ = tracks(P)
days = [(t(p["time"]) - t(P[0]["time"])).total_seconds() / 86400.0 for p in P]
lab = ["alone"] * len(P)
for i in range(1, len(P)):
    if days[i] - days[i - 1] < 3.0:
        lab[i] = "second of pair"
        lab[i - 1] = "first of pair"
m = {}
for a, b in zip(lab, lab0):
    m.setdefault(a, {}).setdefault(b, 0)
    m[a][b] += 1
print("gap-rule groups against the phase groups used in the looks (counts):", m)
moved = [(p["date"], a, b) for p, a, b in zip(P, lab, lab0) if {"first of pair": "A", "second of pair": "B", "alone": "C"}[a] != b]
print("passes the two groupings place differently:", moved)
for L in "ABC":
    x = [dd for dd, l in zip(days, lab0) if l == L]
    iv = [b - a for a, b in zip(x[:-1], x[1:])]
    near = [v for v in iv if v < 30]
    print("track %s: intervals between its passes: %d of %d near one repeat, median %.5f d, min %.5f, max %.5f; longer intervals: %s" % (
        L, len(near), len(iv), median(near), min(near), max(near), [round(v, 4) for v in iv if v >= 30]))
