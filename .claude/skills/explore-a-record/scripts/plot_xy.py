# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Draw one quantity of a record against another, as a figure a look can keep.

For a JSON file that holds a list of rows: plot `--y` against `--x`, one
point for each row, coloured by `--color` when given. With `--residual` the
vertical axis is what is left of y after the least-squares straight line of
y on x is taken out, which is the picture to look at before fitting anything
further: a pattern against x, or a colour that sorts the points, is a term
the line does not have. An x that reads as a time is plotted in days from
the first row.

It writes an SVG file (text, no plotting library, nothing fetched) and
prints what it drew as numbers, so the look's output says what the picture
holds. It knows nothing about any dataset: it draws the keys it is given.

Usage: uv run plot_xy.py FILE.json --x KEY --y KEY --out figures/NAME.svg
         [--rows KEY.PATH] [--color KEY] [--label KEY] [--residual] [--title TEXT]
       uv run plot_xy.py --selftest

Run it through `explore.py look` with `--out figures/<name>.svg`: a file a
look writes into the exploration's `figures/` folder is logged by checksum.
"""
import argparse
import datetime as dt
import json
import sys
import tempfile
from pathlib import Path

W, H, LEFT, RIGHT, TOP, BOTTOM = 720, 440, 76, 150, 44, 56
INK, GRID, AXIS = "#1f2933", "#e3e7eb", "#52606d"
RAMP = ("#cfe1f2", "#93c0e0", "#4f97c9", "#1f6aa8", "#0b3c6f")                 # light to dark, one hue: low to high
KINDS = ("#0072b2", "#d55e00", "#009e73", "#cc79a7", "#e69f00", "#56b4e9", "#000000", "#f0e442")


def rows_of(data, path: str | None) -> list:
    if path:
        for part in path.split("."):
            data = data[part]
        return [r for r in data if isinstance(r, dict)]
    if isinstance(data, list):
        return [r for r in data if isinstance(r, dict)]
    for v in data.values() if isinstance(data, dict) else []:
        if isinstance(v, list) and v and all(isinstance(r, dict) for r in v):
            return v
    return []


def number(v):
    """A value as a number, or None. Text that reads as a time is returned as a time."""
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return dt.datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    except ValueError:
        try:
            return float(v)
        except ValueError:
            return None


def ticks(lo: float, hi: float, n: int = 5) -> list:
    if hi <= lo:
        return [lo]
    raw = (hi - lo) / n
    mag = 10 ** len(str(int(raw))) / 10 if raw >= 1 else 10 ** -len(str(int(1 / raw)))
    step = next(s * mag for s in (1, 2, 5, 10) if s * mag >= raw)
    first = step * int(lo / step + (1 if lo > 0 else 0))
    out, t = [], first
    while t <= hi + 1e-12:
        if t >= lo - 1e-12:
            out.append(round(t, 10))
        t += step
    return out or [lo, hi]


def fit_line(xs: list, ys: list) -> tuple:
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx if sxx else 0.0
    return slope, my - slope * mx


def esc(text) -> str:
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def draw(rows: list, x_key: str, y_key: str, color_key: str | None, label_key: str | None, residual: bool, title: str | None) -> tuple:
    """(the SVG as text, the lines to print)."""
    pts, skipped = [], 0
    for i, r in enumerate(rows):
        x, y = number(r.get(x_key)), number(r.get(y_key))
        if x is None or y is None or isinstance(y, dt.datetime):
            skipped += 1
            continue
        pts.append({"x": x, "y": y, "c": r.get(color_key) if color_key else None, "label": str(r.get(label_key)) if label_key else f"row {i}"})
    if len(pts) < 2:
        raise SystemExit(f"fewer than two rows carry both `{x_key}` and `{y_key}` as numbers; nothing is drawn")
    x_unit = ""
    if any(isinstance(p["x"], dt.datetime) for p in pts):
        if not all(isinstance(p["x"], dt.datetime) for p in pts):
            raise SystemExit(f"`{x_key}` is a time in some rows and a number in others; nothing is drawn")
        first = min(p["x"] for p in pts)
        for p in pts:
            p["x"] = (p["x"] - first).total_seconds() / 86400.0
        x_unit = f" (days from {first.date().isoformat()})"
    said = [f"plotted {len(pts)} of {len(rows)} rows: {y_key} against {x_key}{x_unit}; {skipped} row(s) lacked one of them"]
    y_name = y_key
    if residual:
        slope, intercept = fit_line([p["x"] for p in pts], [p["y"] for p in pts])
        for p in pts:
            p["y"] = p["y"] - (intercept + slope * p["x"])
        y_name = f"{y_key} minus its straight line on {x_key}"
        spread = (sum(p["y"] ** 2 for p in pts) / max(1, len(pts) - 2)) ** 0.5
        said.append(f"straight line taken out: slope {slope:.4f}, intercept {intercept:.4f}; residual spread {spread:.4f} (n minus 2)")
        worst = sorted(pts, key=lambda p: -abs(p["y"]))[:3]
        said.append("largest residuals: " + "; ".join(f"{p['label']} {p['y']:+.4f}" for p in worst))
    xs, ys = [p["x"] for p in pts], [p["y"] for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    px, py = (x1 - x0) * 0.04 or 1.0, (y1 - y0) * 0.06 or 1.0
    x0, x1, y0, y1 = x0 - px, x1 + px, y0 - py, y1 + py
    said.append(f"{x_key}: {min(xs):.4f} to {max(xs):.4f}; vertical axis: {min(ys):.4f} to {max(ys):.4f}")

    def sx(v: float) -> float:
        return LEFT + (v - x0) / (x1 - x0) * (W - LEFT - RIGHT)

    def sy(v: float) -> float:
        return H - BOTTOM - (v - y0) / (y1 - y0) * (H - TOP - BOTTOM)

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" font-family="sans-serif" font-size="12">',
           f"<title>{esc(title or y_name + ' against ' + x_key)}</title>",
           f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
           f'<text x="{LEFT}" y="24" font-size="14" fill="{INK}">{esc(title or y_name + " against " + x_key)}</text>']
    for t in ticks(x0, x1):
        out.append(f'<line x1="{sx(t):.1f}" y1="{TOP}" x2="{sx(t):.1f}" y2="{H - BOTTOM}" stroke="{GRID}"/>'
                   f'<text x="{sx(t):.1f}" y="{H - BOTTOM + 18}" text-anchor="middle" fill="{AXIS}">{t:g}</text>')
    for t in ticks(y0, y1):
        out.append(f'<line x1="{LEFT}" y1="{sy(t):.1f}" x2="{W - RIGHT}" y2="{sy(t):.1f}" stroke="{GRID}"/>'
                   f'<text x="{LEFT - 8}" y="{sy(t) + 4:.1f}" text-anchor="end" fill="{AXIS}">{t:g}</text>')
    if residual and y0 < 0 < y1:
        out.append(f'<line x1="{LEFT}" y1="{sy(0):.1f}" x2="{W - RIGHT}" y2="{sy(0):.1f}" stroke="{AXIS}" stroke-dasharray="4 3"/>')
    out.append(f'<rect x="{LEFT}" y="{TOP}" width="{W - LEFT - RIGHT}" height="{H - TOP - BOTTOM}" fill="none" stroke="{AXIS}"/>')
    out.append(f'<text x="{(LEFT + W - RIGHT) / 2:.0f}" y="{H - 14}" text-anchor="middle" fill="{INK}">{esc(x_key + x_unit)}</text>')
    out.append(f'<text transform="translate(18 {(TOP + H - BOTTOM) / 2:.0f}) rotate(-90)" text-anchor="middle" fill="{INK}">{esc(y_name)}</text>')
    fill = {id(p): KINDS[0] for p in pts}
    lx, ly = W - RIGHT + 16, TOP + 10
    if color_key:
        values = [p["c"] for p in pts]
        nums = [number(v) for v in values]
        distinct = sorted({str(v) for v in values})
        if all(isinstance(n, float) for n in nums) and len(distinct) > len(KINDS):
            lo, hi = min(nums), max(nums)
            for p, n in zip(pts, nums):
                fill[id(p)] = RAMP[min(len(RAMP) - 1, int((n - lo) / (hi - lo) * len(RAMP)))] if hi > lo else RAMP[2]
            out.append(f'<text x="{lx}" y="{ly}" fill="{INK}">{esc(color_key)}</text>')
            for i, c in enumerate(RAMP):
                edge = lo + (hi - lo) * i / len(RAMP)
                out.append(f'<circle cx="{lx + 6}" cy="{ly + 18 + i * 18}" r="5" fill="{c}" stroke="{INK}" stroke-width="0.5"/>'
                           f'<text x="{lx + 18}" y="{ly + 22 + i * 18}" fill="{AXIS}">from {edge:.3g}</text>')
            said.append(f"coloured by {color_key}: {lo:.4f} to {hi:.4f}, light to dark in {len(RAMP)} equal steps")
        elif len(distinct) <= len(KINDS):
            counts = {d: sum(1 for v in values if str(v) == d) for d in distinct}
            for p in pts:
                fill[id(p)] = KINDS[distinct.index(str(p["c"]))]
            out.append(f'<text x="{lx}" y="{ly}" fill="{INK}">{esc(color_key)}</text>')
            for i, d in enumerate(distinct):
                out.append(f'<circle cx="{lx + 6}" cy="{ly + 18 + i * 18}" r="5" fill="{KINDS[i]}" stroke="{INK}" stroke-width="0.5"/>'
                           f'<text x="{lx + 18}" y="{ly + 22 + i * 18}" fill="{AXIS}">{esc(d)} ({counts[d]})</text>')
            said.append(f"coloured by {color_key}: " + ", ".join(f"{d} on {counts[d]}" for d in distinct))
        else:
            said.append(f"`{color_key}` has {len(distinct)} values that are not numbers; the points are not coloured")
    for p in pts:
        out.append(f'<circle cx="{sx(p["x"]):.1f}" cy="{sy(p["y"]):.1f}" r="4" fill="{fill[id(p)]}" stroke="{INK}" stroke-width="0.5">'
                   f'<title>{esc(p["label"])}</title></circle>')
    out.append("</svg>")
    return "\n".join(out) + "\n", said


def selftest() -> int:
    results = []
    tmp = Path(tempfile.mkdtemp(prefix="plot-xy-selftest-"))
    rows = [{"time": f"2024-{m:02d}-15T00:00:00Z", "a": float(m), "b": 2.0 * m + (5.0 if m == 7 else 0.0), "flag": 2 if m == 7 else 1, "slope": m / 10} for m in range(1, 13)]
    rows.append({"time": "2024-12-20T00:00:00Z", "a": None, "b": 1.0, "flag": 1, "slope": 0.1})
    svg, said = draw(rows, "a", "b", "flag", "time", True, None)
    results.append(("one point is drawn for each row that carries both quantities", svg.count("<circle") == 12 + 2 and "plotted 12 of 13 rows" in said[0]))
    results.append(("the residual plot names the row that stands out", "2024-07-15T00:00:00Z" in said[2] and said[2].index("2024-07-15") < said[2].index(";")))
    results.append(("a flag with few values is a legend with the count at each value", "1 on 11" in said[-1] and "2 on 1" in said[-1]))
    svg2, said2 = draw(rows, "time", "b", "slope", None, False, "b over the year")
    results.append(("an x that reads as a time is plotted in days from the first row", "days from 2024-01-15" in said2[0] and "b over the year" in svg2))
    results.append(("a quantity with many values is a ramp from light to dark", "light to dark" in said2[-1]))
    results.append(("the figure is text, so the fence of the exploring tool can read it", svg.startswith("<svg") and svg.isascii()))
    try:
        draw(rows[:1], "a", "b", None, None, False, None)
        results.append(("fewer than two usable rows draws nothing", False))
    except SystemExit:
        results.append(("fewer than two usable rows draws nothing", True))
    for f in tmp.iterdir():
        f.unlink()
    tmp.rmdir()
    failed = [n for n, good in results if not good]
    for n in failed:
        print("FAIL:", n)
    print(f"selftest: {'PASS' if not failed else 'FAIL'} ({len(results) - len(failed)} of {len(results)})")
    return 0 if not failed else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", type=Path, nargs="?")
    ap.add_argument("--rows", default=None, help="the key (dotted for a nested one) under which the list of rows sits; default: the first list of rows in the file")
    ap.add_argument("--x")
    ap.add_argument("--y")
    ap.add_argument("--color", default=None, help="a third quantity to colour the points by: a flag, a covariate")
    ap.add_argument("--label", default=None, help="the key that names a row (a time, an identifier), for the largest residuals")
    ap.add_argument("--residual", action="store_true", help="plot what is left of y after its straight line on x is taken out")
    ap.add_argument("--title", default=None)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not (a.file and a.x and a.y and a.out):
        ap.error("FILE, --x, --y and --out are required")
    try:
        rows = rows_of(json.loads(a.file.read_text()), a.rows)
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(f"cannot read rows from {a.file}: {e}", file=sys.stderr)
        return 2
    svg, said = draw(rows, a.x, a.y, a.color, a.label, a.residual, a.title)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(svg)
    for line in said:
        print(line)
    print(f"figure written: {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
