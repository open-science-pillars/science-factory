# /// script
# requires-python = ">=3.11"
# dependencies = ["duckdb"]
# ///
"""A look at the gauge record with DuckDB over Parquet: the slope of the stage on the day, by least squares.

Exploring. Inside the fence DuckDB reads only the files the look was given: it cannot load or install an extension, or read
a remote file, and this look shows that too.
"""
import os
import sys

import duckdb

f = os.path.abspath(sys.argv[1])  # a path the fence allowed: the look's own folder
con = duckdb.connect()
slope, n = con.execute(f"SELECT regr_slope(stage, epoch(day) / 86400), count(*) FROM read_parquet('{f}')").fetchone()
print(f"slope of the stage per day: {slope:.4f} from {n} days")
try:
    con.execute("SELECT * FROM read_parquet('https://example.invalid/fresh.parquet')")
    print("a remote file: read")
except Exception:
    print("a remote file: refused")
