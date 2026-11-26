# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Describe the shape of a record before any statistic is computed on it.

For a JSON file: every key path, how many values sit under it, the range of
the numeric ones, the distinct values of the short text ones, and the span
of anything that reads as a time. It prints no single observation in full.
It knows nothing about any dataset: it reports what the file holds.

Usage: uv run describe_record.py FILE.json [--max-distinct 8]
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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", type=Path)
    ap.add_argument("--max-distinct", type=int, default=8)
    a = ap.parse_args()
    try:
        data = json.loads(a.file.read_text())
    except (OSError, ValueError) as e:
        print(f"cannot read {a.file} as JSON: {e}", file=sys.stderr)
        return 2
    seen = {}
    walk(data, "", seen)
    print(f"{a.file.name}: {a.file.stat().st_size} bytes, {len(seen)} key paths")
    for path, s in seen.items():
        if path.endswith("[]") and "lists" in s and "n" not in s:
            print(f"  {path}: {s['lists']} list(s), {s['items']} item(s) in all")
            continue
        parts = [f"n={s.get('n', 0)}"]
        if s.get("null"):
            parts.append(f"null={s['null']}")
        nums = s.get("numbers") or []
        if nums:
            parts.append(f"numbers {len(nums)}: min {min(nums):g}, max {max(nums):g}")
        times = s.get("times") or []
        if times:
            parts.append(f"times {len(times)}: {min(times)} to {max(times)}")
        texts = s.get("texts") or {}
        if texts:
            if len(texts) <= a.max_distinct:
                parts.append("values " + ", ".join(f"{k!r} x{v}" for k, v in sorted(texts.items(), key=lambda kv: -kv[1])))
            else:
                parts.append(f"text, {len(texts)} distinct values")
        print(f"  {path}: " + "; ".join(parts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
