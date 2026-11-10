"""numcomp: root finding on a simulated n-significant-figure machine."""

from .errors import BracketError, DivergenceError, ExpressionError, NumCompError, ZeroDerivativeError
from .expr import Expression, parse
from .machine import Machine, round_sig
from .plot import plot
from .result import RootResult
from .roots import bisection, false_position, fixed_point, modified_newton, newton, secant

__all__ = [
    "BracketError", "DivergenceError", "ExpressionError", "NumCompError", "ZeroDerivativeError",
    "Expression", "parse", "Machine", "round_sig", "plot", "RootResult",
    "bisection", "false_position", "fixed_point", "modified_newton", "newton", "secant",
]
