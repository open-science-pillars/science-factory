# /// script
# requires-python = ">=3.11"
# dependencies = ["duckdb"]
# ///
"""Make the stand-alone example's synthetic gauge record as two Parquet files, one for each year: a day, a position and a
stage that rises by a known 0.01 a day from 1.0. Exploring 2024 should find that slope; 2025 is the fresh data.

  uv run examples/stand-alone/make_parquet.py YEAR OUT.parquet
"""
import sys

import duckdb

year, out = int(sys.argv[1]), sys.argv[2]
con = duckdb.connect()
con.execute(f"""COPY (SELECT DATE '{year}-01-01' + i::INTEGER AS day, 30.45 AS lat, -91.19 AS lon,
                      round(1.0 + 0.01 * i + 0.002 * sin(i), 4) AS stage FROM range(365) t(i))
                TO '{out.replace("'", "''")}' (FORMAT parquet)""")
print(f"wrote {out}: 365 days of {year}")
