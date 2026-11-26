"""Shared loading and pairing for the looks of EXPLORATION-0102 (exploring).

Reads only the Version D block and the gauge block of the 2024 fixture.
Pairing follows the signed recipe: nearest gauge reading inside a stated
tolerance (15 minutes by default); an unpaired pass is dropped by name.
"""
import json
import math
from datetime import datetime, timezone

FT = 0.3048
HEIGHT_DEPARTED = ("2024-10-30", "2024-03-26")  # named by a DRAFT page in the queue, not signed


def t(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


def load(path):
    d = json.load(open(path))
    assert d["satellite"]["collection_named"] == "SWOT_L2_HR_RiverSP_reach_D"
    return d


def pairs(d, tol_min=15.0):
    """One dict per Version D pass: satellite fields, nearest gauge stage (m), minutes apart."""
    out = []
    allr = [r for g in d["gauge"]["readings_by_pass"] for r in g]  # pooled, so no order is assumed
    for row in d["satellite"]["rows"]:
        ts = t(row["time"])
        best = None
        for r in allr:
            dm = abs((t(r["t"]) - ts).total_seconds()) / 60.0
            if best is None or dm < best[0]:
                best = (dm, float(r["stage_ft"]) * FT)
        p = dict(row)
        p["date"] = row["time"][:10]
        p["gap_min"] = best[0] if best else None
        p["stage_m"] = best[1] if best and best[0] <= tol_min else None
        out.append(p)
    return out


def mean(x):
    return sum(x) / len(x)


def pearson(x, y):
    mx, my = mean(x), mean(y)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    return sxy / math.sqrt(sxx * syy) if sxx > 0 and syy > 0 else float("nan")


def ranks(x):
    o = sorted(range(len(x)), key=lambda i: x[i])
    r = [0.0] * len(x)
    i = 0
    while i < len(o):
        j = i
        while j + 1 < len(o) and x[o[j + 1]] == x[o[i]]:
            j += 1
        for k in range(i, j + 1):
            r[o[k]] = (i + j) / 2.0 + 1
        i = j + 1
    return r


def spearman(x, y):
    return pearson(ranks(x), ranks(y))


def fit(x, y):
    """Least squares y = a + b x; returns a, b, residual standard deviation (n-2)."""
    mx, my = mean(x), mean(y)
    b = sum((a - mx) * (c - my) for a, c in zip(x, y)) / sum((a - mx) ** 2 for a in x)
    a = my - b * mx
    res = [c - (a + b * v) for v, c in zip(x, y)]
    sd = math.sqrt(sum(r * r for r in res) / (len(x) - 2))
    return a, b, sd, res


def sd(x):
    m = mean(x)
    return math.sqrt(sum((a - m) ** 2 for a in x) / (len(x) - 1))


def median(x):
    s = sorted(x)
    n = len(s)
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


REPEAT_DAYS = 20.86455  # the science orbit repeat; used only to group passes into overpass tracks


def tracks(P):
    """Group passes into overpass tracks by phase of the repeat cycle (the file has no pass number).

    Returns a label per pass, 'A', 'B', ... in order of phase. Phases closer than 0.2 day are one track.
    """
    t0 = t(min(p["time"] for p in P))
    ph = [((t(p["time"]) - t0).total_seconds() / 86400.0) % REPEAT_DAYS for p in P]
    order = sorted(range(len(P)), key=lambda i: ph[i])
    lab = [None] * len(P)
    k = -1
    last = None
    for i in order:
        if last is None or ph[i] - last > 0.2:
            k += 1
        lab[i] = "ABCDEFGH"[k]
        last = ph[i]
    # wrap: a phase near REPEAT_DAYS belongs with the track near zero
    if ph[order[-1]] > REPEAT_DAYS - 0.2 and ph[order[0]] < 0.2:
        for i in range(len(P)):
            if lab[i] == "ABCDEFGH"[k]:
                lab[i] = "A"
    return lab, ph
