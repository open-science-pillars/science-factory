# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""A look at the two-sensor record: the gain of the second sensor on the reference, by least squares with an intercept.

Exploring. The intercept takes up the unsurveyed mounting offset, as the wiki page on comparing changes says.
"""
import argparse
import json


def main() -> None:
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("data")
    ap.add_argument("--exclude-flag-at-or-above", type=int, default=None)
    a = ap.parse_args()
    rows = json.load(open(a.data))["rows"]
    n0 = len(rows)
    if a.exclude_flag_at_or_above is not None:
        rows = [r for r in rows if r["flag"] < a.exclude_flag_at_or_above]
    x, y = [r["reference"] for r in rows], [r["sensor"] for r in rows]
    mx, my = sum(x) / len(x), sum(y) / len(y)
    gain = sum((a_ - mx) * (b_ - my) for a_, b_ in zip(x, y)) / sum((a_ - mx) ** 2 for a_ in x)
    res = [b_ - (my + gain * (a_ - mx)) for a_, b_ in zip(x, y)]
    worst = max(zip(res, rows), key=lambda t: abs(t[0]))
    print(f"flag screen {a.exclude_flag_at_or_above}: {len(rows)} of {n0} readings kept")
    print(f"gain {gain:.4f}; intercept {my - gain * mx:.4f} m; residual spread {(sum(e * e for e in res) / (len(res) - 2)) ** 0.5:.4f} m")
    print(f"the reading furthest from the line: {worst[1]['time']} (flag {worst[1]['flag']}), {worst[0]:+.4f} m")


if __name__ == "__main__":
    main()
