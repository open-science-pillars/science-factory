"""Helpers for the looks that answer REVIEW-001 (exploring, not a method).
Least squares with any number of regressors, with two kinds of interval for
each coefficient: plain, and widened by the lag-1 effective sample of the
fit's own residuals (capped at the count), as common.gain does for one."""
import math
import statistics
from common import lag1, neff, tq


def solve(A, b):
    n = len(A)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for i in range(n):
        p = max(range(i, n), key=lambda r: abs(M[r][i]))
        M[i], M[p] = M[p], M[i]
        for r in range(n):
            if r != i:
                f = M[r][i] / M[i][i]
                M[r] = [a - f * c for a, c in zip(M[r], M[i])]
    return [M[i][n] / M[i][i] for i in range(n)]


def inverse(A):
    n = len(A)
    cols = [solve(A, [1.0 if i == j else 0.0 for i in range(n)]) for j in range(n)]
    return [[cols[j][i] for j in range(n)] for i in range(n)]


def fit(y, cols, fixed=None):
    """y = c0 + sum(c_k * cols[k]). `fixed` is a column whose coefficient is
    held at one (subtracted from y first). Returns coefficients (after the
    constant), plain standard errors, effective-sample half widths, residuals."""
    if fixed is not None:
        y = [a - f for a, f in zip(y, fixed)]
    n, k = len(y), len(cols) + 1
    X = [[1.0] + [c[i] for c in cols] for i in range(n)]
    # centre for conditioning
    means = [0.0] + [statistics.fmean(c) for c in cols]
    X = [[1.0] + [row[j] - means[j] for j in range(1, k)] for row in X]
    XtX = [[sum(r[i] * r[j] for r in X) for j in range(k)] for i in range(k)]
    Xty = [sum(r[i] * v for r, v in zip(X, y)) for i in range(k)]
    inv = inverse(XtX)
    beta = [sum(inv[i][j] * Xty[j] for j in range(k)) for i in range(k)]
    res = [v - sum(b * x for b, x in zip(beta, r)) for r, v in zip(X, y)]
    s2 = sum(r * r for r in res) / (n - k)
    se = [math.sqrt(s2 * inv[i][i]) for i in range(k)]
    ne = neff(res)
    widen = math.sqrt((n - k) / max(ne - k, 1.0))
    q_plain, q_eff = tq(n - k), tq(ne - k)
    return {"coef": beta[1:], "se": se[1:], "half_plain": [q_plain * s for s in se[1:]],
            "half_eff": [q_eff * s * widen for s in se[1:]], "res": res, "sd": math.sqrt(s2),
            "n": n, "n_eff": ne, "lag1": lag1(res)}


def show(name, f, i=0, unit=""):
    c, hp, he = f["coef"][i], f["half_plain"][i], f["half_eff"][i]
    return (f"{name} {c:.4f}{unit} (plain standard error {f['se'][i]:.4f}; plain 95 pct [{c-hp:.4f}, {c+hp:.4f}]; "
            f"effective-sample 95 pct [{c-he:.4f}, {c+he:.4f}])")


def years(ps):
    t0 = min(p["when"] for p in ps)
    return [(p["when"] - t0).total_seconds() / 86400 / 365.25 for p in ps]


SETS = [
    ("all paired passes, no screen", lambda p: True),
    ("reach_q equal to 1 (the three passes with reach_q 2 left out)", lambda p: p["reach_q"] < 2),
    ("reach_q equal to 1 and wse_u below 0.2 m (the analyst's limit)", lambda p: p["reach_q"] < 2 and p["wse_u_m"] < 0.2),
    ("the two departing passes left out by date", lambda p: not p["time"].startswith(("2024-03-26", "2024-10-30"))),
]
