"""Run one test case and compare results. Shared by the tests and by gen_cases.py.

PROVIDED: do not edit.
"""

from __future__ import annotations

import math

import numcomp

ERRORS = {
    "ValueError": ValueError,
    "ZeroDivisionError": ZeroDivisionError,
    "ExpressionError": numcomp.ExpressionError,
    "BracketError": numcomp.BracketError,
    "ZeroDerivativeError": numcomp.ZeroDerivativeError,
    "DivergenceError": numcomp.DivergenceError,
}

RESULT_FIELDS = ("root", "stop_reason")
ITERATION_FIELDS = ("iterations", "ea", "estimated_sig_figs", "true_sig_figs", "residual", "g_prime_x0")


def run(case: dict):
    kind, inp = case["kind"], case["input"]
    if kind == "round":
        return numcomp.round_sig(inp["value"], inp["n"], inp["mode"])
    if kind == "machine":
        m = numcomp.Machine(inp["sig_figs"], inp["mode"])
        return getattr(m, inp["op"])(*inp["args"])
    if kind == "eval":
        m = numcomp.Machine(inp["sig_figs"], inp["mode"])
        return numcomp.parse(inp["expr"]).evaluate(m, m.enter(inp["x"]))
    if kind == "root":
        return getattr(numcomp, inp["method"])(*inp["args"], **inp["kwargs"])
    raise ValueError(f"unknown case kind {kind!r}")


def to_expected(case: dict) -> dict:
    """Run the case on the reference implementation and record what it produced."""
    try:
        got = run(case)
    except tuple(ERRORS.values()) as exc:
        name = next(n for n, cls in ERRORS.items() if type(exc) is cls)
        return {"error": name, "message": str(exc)} | (
            {"steps_len": len(exc.steps)} if hasattr(exc, "steps") else {}
        )
    if case["kind"] != "root":
        return {"value": got}
    return {f: getattr(got, f) for f in RESULT_FIELDS + ITERATION_FIELDS} | {"steps": got.steps}


def same(got, want, *, abs_tol: float = 0.0) -> bool:
    if want is None or got is None:
        return got is want
    if isinstance(want, str):
        return got == want
    if isinstance(want, bool) or isinstance(got, bool):
        return False
    if not isinstance(got, (int, float)):
        return False
    if math.isnan(want):
        return math.isnan(got)
    if math.isinf(want):
        return got == want
    if want == 0:
        if got == 0:
            return math.copysign(1.0, got) == math.copysign(1.0, want)
        return abs_tol > 0 and abs(got) <= abs_tol
    return got == want or math.isclose(got, want, rel_tol=1e-13, abs_tol=abs_tol)


def float_abs_tol(field: str) -> float:
    """Near-zero libm noise must not become a relative-only trace mismatch."""
    if field == "ea":
        return 1e-9  # percent; cancellation in successive iterates amplifies ULPs
    if field == "residual" or field.startswith(("f_", "df_", "d2f_")):
        return 1e-12
    return 0.0


def mismatches(got, want: dict, level: str, *, float_mode: bool = False) -> list[str]:
    """Differences between a RootResult and the expected dict at one grading level."""
    out = []
    if level in ("result", "iterations"):
        for f in RESULT_FIELDS if level == "result" else ITERATION_FIELDS:
            g = getattr(got, f, "<missing>")
            if not same(g, want[f], abs_tol=float_abs_tol(f) if float_mode else 0.0):
                out.append(f"{f}: expected {want[f]!r}, got {g!r}")
        return out
    steps = getattr(got, "steps", None)
    if not isinstance(steps, list):
        return ["steps is not a list"]
    if len(steps) != len(want["steps"]):
        out.append(f"expected {len(want['steps'])} rows, got {len(steps)}")
    for r, (g_row, w_row) in enumerate(zip(steps, want["steps"]), start=1):
        if not isinstance(g_row, dict) or set(g_row) != set(w_row):
            out.append(f"row {r}: expected keys {sorted(w_row)}, got {sorted(g_row) if isinstance(g_row, dict) else g_row!r}")
            break
        bad = [k for k in w_row if not same(
            g_row[k], w_row[k], abs_tol=float_abs_tol(k) if float_mode else 0.0)]
        if bad:
            out.append(f"row {r}: " + ", ".join(f"{k} expected {w_row[k]!r} got {g_row[k]!r}" for k in bad))
            break
    return out
