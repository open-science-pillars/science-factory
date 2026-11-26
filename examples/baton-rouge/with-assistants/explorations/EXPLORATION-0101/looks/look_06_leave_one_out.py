"""Do a few passes carry the gain? Leave each pass out in turn, from all paired
passes and from the passes with reach_q below 2."""
import sys
from common import load, pair, gain

doc = load(sys.argv[1])
pairs, _ = pair(doc, 15)
for name, ps in (("all paired", pairs), ("reach_q below 2", [p for p in pairs if p["reach_q"] < 2])):
    base = gain(ps)["gain"]
    moves = []
    for i in range(len(ps)):
        g = gain(ps[:i] + ps[i + 1:])["gain"]
        moves.append((g - base, ps[i]["time"][:10], g))
    moves.sort(key=lambda m: -abs(m[0]))
    print(f"{name}: n={len(ps)}, gain {base:.4f}; leave-one-out gains span {min(m[2] for m in moves):.4f} to {max(m[2] for m in moves):.4f}")
    for dv, d, g in moves[:4]:
        print(f"   leaving out {d} moves the gain by {dv:+.4f} to {g:.4f}")
