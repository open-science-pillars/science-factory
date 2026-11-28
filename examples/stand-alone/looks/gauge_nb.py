# /// script
# requires-python = ">=3.11"
# dependencies = ["marimo==0.26.0", "duckdb"]
# ///
# A notebook look at the gauge record: the slope of the stage on the day, by least squares, with DuckDB over Parquet.
# Exploring. It runs as a script (`uv run gauge_nb.py FILE`), its cells in the order they depend on each other, and only
# what it prints is the look's output.
import marimo

app = marimo.App()


@app.cell
def _():
    import os
    import sys

    import duckdb

    path = os.path.abspath(sys.argv[1])  # a path the fence allowed: the look's own folder
    con = duckdb.connect()
    return con, path


@app.cell
def _(con, path):
    slope, n = con.execute(f"SELECT regr_slope(stage, epoch(day) / 86400), count(*) FROM read_parquet('{path}')").fetchone()
    print(f"slope of the stage per day: {slope:.4f} from {n} days")
    return


if __name__ == "__main__":
    app.run()
