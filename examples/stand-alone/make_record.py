# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Make the synthetic two-sensor record of the stand-alone example, with a known answer.

The truth, put in by hand: sensor = OFFSET + GAIN * reference + noise, one
row a week. Two readings in each year are flagged degraded (flag 2), and one
of those is far off. The seed is fixed, so the same file is made every time.

  uv run make_record.py --year 2024 --out record-2024.json     the working year (committed)
  uv run make_record.py --year 2025 --out record-2025.json     the following year: the example sets it
                                                               aside and never makes it, except in a
                                                               scratch folder to show the fence refuse it
"""
import argparse
import datetime as dt
import json
import math
import random

GAIN, OFFSET, NOISE_SD, SEED = 1.03, 0.40, 0.05, 20261125


def make(year: int) -> dict:
    rng = random.Random(SEED + year)
    rows, day = [], dt.date(year, 1, 3)
    for week in range(52):
        reference = 5.0 + 4.0 * math.sin(2 * math.pi * week / 52) + rng.gauss(0, 0.3)
        sensor = OFFSET + GAIN * reference + rng.gauss(0, NOISE_SD)
        flag = 1
        if week == 38:
            flag, sensor = 2, sensor - 2.0      # degraded and far off, near the low end of the range
        if week == 12:
            flag = 2                            # degraded and fine
        rows.append({"time": f"{day.isoformat()}T12:00:00Z", "reference": round(reference, 4), "sensor": round(sensor, 4), "flag": flag})
        day += dt.timedelta(days=7)
    return {"what": "a synthetic two-sensor record with a known answer; see openwiki/the-two-sensor-record.md",
            "window": {"start": f"{year}-01-01", "end": f"{year}-12-31"}, "units": "metres", "rows": rows}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    with open(a.out, "w") as f:
        json.dump(make(a.year), f, indent=1)
        f.write("\n")
    print(f"wrote {a.out}: 52 rows for {a.year}")


if __name__ == "__main__":
    main()
