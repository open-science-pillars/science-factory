"""What goes with a width that is off its track's line: dark_frac, reach_q, stated height uncertainty, slope?"""
import sys
from common import load, pairs, tracks, fit, pearson, spearman, mean

d = load(sys.argv[1])
P = sorted(pairs(d, 15.0), key=lambda p: p["time"])
lab, _ = tracks(P)
for p, l in zip(P, lab):
    p["track"] = l
Q = [p for p in P if p["stage_m"] is not None]
rows = []
for L in "ABC":
    S = [p for p in Q if p["track"] == L]
    a, b, s, res = fit([p["stage_m"] for p in S], [p["width_m"] for p in S])
    for p, r in zip(S, res):
        rows.append((p, r))
print("Width residual about each track's own line on stage (lines fitted on all paired passes of the track), largest first:")
print("date       track stage_m width_m resid_m dark_frac reach_q wse_u_m")
for p, r in sorted(rows, key=lambda x: -abs(x[1]))[:10]:
    print("%s  %s  %6.3f %7.1f %+7.1f   %.3f    %s    %.3f" % (p["date"], p["track"], p["stage_m"], p["width_m"], r, p["dark_frac"], p["reach_q"], p["wse_u_m"]))
res = [r for _, r in rows]
dk = [p["dark_frac"] for p, _ in rows]
print("\nresidual against dark_frac, %d pairs: r=%+.3f rho=%+.3f" % (len(res), pearson(dk, res), spearman(dk, res)))
hi = [r for (p, r) in rows if p["dark_frac"] >= 0.10]
lo = [r for (p, r) in rows if p["dark_frac"] < 0.10]
print("dark_frac >= 0.10: n=%d, mean residual %+.1f m; dark_frac < 0.10: n=%d, mean residual %+.1f m" % (len(hi), mean(hi), len(lo), mean(lo)))
print("\ndark_frac by track (all 52 passes): " + "; ".join(
    "%s: n>=0.10 is %d of %d" % (L, sum(p["dark_frac"] >= 0.10 for p in P if p["track"] == L), sum(p["track"] == L for p in P)) for L in "ABC"))
print("reach_q 2 passes:", [(p["date"], p["track"], round(r, 1)) for p, r in rows if str(p["reach_q"]) == "2"])
print("\nRaw width against dark_frac ignoring track and stage, 52 passes: r=%+.3f rho=%+.3f" % (
    pearson([p["dark_frac"] for p in P], [p["width_m"] for p in P]), spearman([p["dark_frac"] for p in P], [p["width_m"] for p in P])))
# is the A to B drop explained by dark_frac?
A = [p for p in Q if p["track"] == "A"]; B = [p for p in Q if p["track"] == "B"]
print("track A dark_frac mean %.3f, track B %.3f, track C %.3f" % (mean([p["dark_frac"] for p in A]), mean([p["dark_frac"] for p in B]),
      mean([p["dark_frac"] for p in Q if p["track"] == "C"])))
Blo = [p for p in B if p["dark_frac"] < 0.05]
Alo = [p for p in A if p["dark_frac"] < 0.05]
a1, b1, s1, _ = fit([p["stage_m"] for p in Alo if p["date"] != "2024-02-12"], [p["width_m"] for p in Alo if p["date"] != "2024-02-12"])
a2, b2, s2, _ = fit([p["stage_m"] for p in Blo], [p["width_m"] for p in Blo])
print("low dark_frac only (<0.05): width at 5 m stage on track A line %.1f m (n=%d, without 2024-02-12), on track B line %.1f m (n=%d); difference %.1f m" % (
    a1 + 5 * b1, len(Alo) - 1, a2 + 5 * b2, len(Blo), (a1 + 5 * b1) - (a2 + 5 * b2)))
for L in "ABC":
    S = [p for p in Q if p["track"] == L]
    a, b, s, _ = fit([p["stage_m"] for p in S], [p["width_m"] for p in S])
    print("track %s line: width at 2 m stage %.1f m, at 5 m %.1f m, at 9 m %.1f m" % (L, a + 2 * b, a + 5 * b, a + 9 * b))
