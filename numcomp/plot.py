"""Plot f(x), or g(x) against y = x, to pick initial guesses.  YOU WRITE THIS FILE.

Use matplotlib (numpy is allowed here). Not autograded; the figures go in your report.
"""

from __future__ import annotations

from pathlib import Path


def plot(expr, a: float, b: float, path, *, fixed_point: bool = False, points: int = 400) -> Path:
    """Save a PNG of expr on [a, b] to ``path`` and return it as a Path.

    fixed_point=False: draw f(x) and the x-axis.
    fixed_point=True:  draw g(x) and the line y = x.
    Evaluate with Machine(None) (double precision); leave gaps where expr is undefined.
    """
    raise NotImplementedError
