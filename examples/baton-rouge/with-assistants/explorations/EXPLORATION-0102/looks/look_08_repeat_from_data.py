"""The track grouping used a repeat period I supplied (20.86455 d), which no knowledge page states.
Does the file itself give the same grouping? Scan candidate periods and group by phase."""
import sys
from common import load, pairs, tracks, t

d = load(sys.argv[1])
P = sorted(pairs(d, 15.0), key=lambda p: p["time"])
lab0, _ = tracks(P)
t0 = t(P[0]["time"])
days = [(t(p["time"]) - t0).total_seconds() / 86400.0 for p in P]
gaps = sorted(set(round(b - a, 2) for a, b in zip(days[:-1], days[1:])))
print("distinct gaps between consecutive passes (days, rounded):", gaps)
best = None
for k in range(190000, 230001):
    T = k / 10000.0
    ph = sorted(x % T for x in days)
    # group phases closer than 0.2 d, with wrap
    groups = [[ph[0]]]
    for x in ph[1:]:
        if x - groups[-1][-1] > 0.2:
            groups.append([x])
        else:
            groups[-1].append(x)
    if len(groups) > 1 and ph[-1] - T + 0.2 > ph[0]:
        groups[0] = groups.pop() + groups[0]
    spread = max((max(g) - min(g)) if max(g) - min(g) < T / 2 else 0 for g in groups)
    score = (len(groups), spread)
    if best is None or score < best[0]:
        best = (score, T)
(ng, spread), T = best
print("period that gives the fewest, tightest phase groups in 19 to 23 d: %.4f d -> %d groups, widest group %.4f d" % (T, ng, spread))
ph = [x % T for x in days]
order = sorted(range(len(P)), key=lambda i: ph[i])
lab = [None] * len(P); g = -1; last = None
for i in order:
    if last is None or ph[i] - last > 0.2:
        g += 1
    lab[i] = g; last = ph[i]
m = {}
for a, b in zip(lab, lab0):
    m.setdefault(a, set()).add(b)
print("data-derived groups against the groups used in the looks:", {k: sorted(v) for k, v in m.items()},
      "| identical partition:", all(len(v) == 1 for v in m.values()) and len(m) == len(set(lab0)))
import collections
print("group sizes:", sorted(collections.Counter(lab).values()))
print("time of day (UTC hour) drifts through the year within a group, so hour of day alone does not group them:",
      {L: sorted(set(t(p['time']).hour for p, l in zip(P, lab0) if l == L)) for L in "ABC"})
