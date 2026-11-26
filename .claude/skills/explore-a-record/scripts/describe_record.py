# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Describe the shape of a record before any statistic is computed on it.

For a JSON file: every key path, how many values sit under it, the range of
the numeric ones, the count at each value of a numeric key that takes only
a few whole values (a quality flag: say what each value is before screening
on it, and note when no observation is at the clean value), the distinct
values of the short text ones, and the span of anything that reads as a time. It prints no single observation in full.
It knows nothing about any dataset: it reports what the file holds.

Usage: uv run describe_record.py FILE.json [--max-distinct 8]
       uv run describe_record.py --selftest
"""
import argparse
import json
import re
import sys
from pathlib import Path

TIME = re.compile(r"^\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2})?")


def walk(obj, path, seen):
    if isinstance(obj, dict):
        for k, v in obj.items():
            walk(v, f"{path}.{k}" if path else str(k), seen)
    elif isinstance(obj, list):
        seen.setdefault(path + "[]", {"lists": 0, "items": 0})
        seen[path + "[]"]["lists"] = seen[path + "[]"].get("lists", 0) + 1
        seen[path + "[]"]["items"] = seen[path + "[]"].get("items", 0) + len(obj)
        for v in obj:
            walk(v, path + "[]", seen)
    else:
        s = seen.setdefault(path, {"n": 0, "null": 0, "numbers": [], "texts": {}, "times": []})
        s["n"] = s.get("n", 0) + 1
        if obj is None:
            s["null"] = s.get("null", 0) + 1
        elif isinstance(obj, bool):
            s.setdefault("texts", {})[str(obj)] = s.setdefault("texts", {}).get(str(obj), 0) + 1
        elif isinstance(obj, (int, float)):
            s.setdefault("numbers", []).append(obj)
        else:
            text = str(obj)
            if TIME.match(text):
                s.setdefault("times", []).append(text)
            else:
                t = s.setdefault("texts", {})
                t[text[:60]] = t.get(text[:60], 0) + 1


def describe(data, max_distinct: int = 8) -> list:
    seen = {}
    walk(data, "", seen)
    out = [f"{len(seen)} key paths"]
    for path, s in seen.items():
        if path.endswith("[]") and "lists" in s and "n" not in s:
            out.append(f"  {path}: {s['lists']} list(s), {s['items']} item(s) in all")
            continue
        parts = [f"n={s.get('n', 0)}"]
        if s.get("null"):
            parts.append(f"null={s['null']}")
        nums = s.get("numbers") or []
        if nums:
            parts.append(f"numbers {len(nums)}: min {min(nums):g}, max {max(nums):g}")
            whole = sorted({n for n in nums if float(n).is_integer()})
            if len(whole) == len(set(nums)) and len(whole) <= max_distinct and len(nums) > len(whole):
                # a key that takes a few whole values is most likely a flag or a class: count each value
                parts.append("count at each value: " + ", ".join(f"{int(v)} on {sum(1 for n in nums if n == v)}" for v in whole)
                             + (" (none at 0)" if 0 not in whole and min(whole) > 0 else ""))
        times = s.get("times") or []
        if times:
            parts.append(f"times {len(times)}: {min(times)} to {max(times)}")
        texts = s.get("texts") or {}
        if texts:
            if len(texts) <= max_distinct:
                parts.append("values " + ", ".join(f"{k!r} x{v}" for k, v in sorted(texts.items(), key=lambda kv: -kv[1])))
            else:
                parts.append(f"text, {len(texts)} distinct values")
        out.append(f"  {path}: " + "; ".join(parts))
    return out


def selftest() -> int:
    said = "\n".join(describe({"retrieved": "2026-01-01", "rows": [{"time": f"2024-01-{d:02d}T00:00:00Z", "h": d * 0.5, "q": 2 if d == 9 else 1} for d in range(1, 11)]}))
    results = [("a flag is counted value by value, and it says when none is at 0", "count at each value: 1 on 9, 2 on 1 (none at 0)" in said),
               ("a measured quantity is a range, not a list of values", "rows[].h: n=10; numbers 10: min 0.5, max 5" in said and "0.5 on" not in said),
               ("times are a span", "times 10: 2024-01-01T00:00:00Z to 2024-01-10T00:00:00Z" in said)]
    failed = [n for n, good in results if not good]
    for n in failed:
        print("FAIL:", n)
    print(f"selftest: {'PASS' if not failed else 'FAIL'} ({len(results) - len(failed)} of {len(results)})")
    return 0 if not failed else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", type=Path, nargs="?")
    ap.add_argument("--max-distinct", type=int, default=8)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.file:
        ap.error("FILE is required")
    try:
        data = json.loads(a.file.read_text())
    except (OSError, ValueError) as e:
        print(f"cannot read {a.file} as JSON: {e}", file=sys.stderr)
        return 2
    lines = describe(data, a.max_distinct)
    print(f"{a.file.name}: {a.file.stat().st_size} bytes, {lines[0]}")
    for line in lines[1:]:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
