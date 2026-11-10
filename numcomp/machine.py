"""Simulated n-significant-figure decimal machine.  YOU WRITE THIS FILE.

Read README.md, section 2 "The machine", before starting.
Rules: no `decimal`, no built-in `round()`, no `Fraction.__round__`.
`fractions.Fraction` and `math` are allowed.
"""

from __future__ import annotations

from fractions import Fraction

from .errors import DivergenceError  # noqa: F401  (you will raise it)

MODES = ("round", "chop")
MAX_SIG_FIGS = 12


def round_sig(value: float, n: int | None, mode: str = "round") -> float:
    """Round ``value`` to ``n`` significant figures.

    mode "round": half away from zero (2.675 -> 2.68, -2.5 -> -3 at n=1).
    mode "chop":  toward zero (3.1415926535 -> 3.141592 at n=7).
    n None: no decimal rounding, just convert to float (inputs are still
    validated and the result is never -0.0). Raise ValueError for bad n / mode,
    DivergenceError for inf / nan or a result too large for a float.
    """
    raise NotImplementedError


class Machine:
    """Every method returns a float holding an exact n-digit decimal."""

    def __init__(self, sig_figs: int | None = None, mode: str = "round"):
        raise NotImplementedError

    def enter(self, value: int | float | Fraction) -> float:
        """Store an input number (literal, constant, initial guess): one rounding."""
        raise NotImplementedError

    def add(self, a: float, b: float) -> float:
        raise NotImplementedError

    def sub(self, a: float, b: float) -> float:
        raise NotImplementedError

    def mul(self, a: float, b: float) -> float:
        raise NotImplementedError

    def div(self, a: float, b: float) -> float:
        """Raise ZeroDivisionError when b == 0."""
        raise NotImplementedError

    def pow_int(self, a: float, k: int) -> float:
        """a**k by repeated multiplication from the left, rounding each product.
        k == 0 -> 1; k < 0 -> one rounded reciprocal of a**(-k)."""
        raise NotImplementedError

    def call(self, name: str, a: float) -> float:
        """exp, sin, cos, tan, ln, sqrt: computed with `math` in double, then
        rounded once. Let math's ValueError (domain error) propagate; turn
        overflow into DivergenceError."""
        raise NotImplementedError
