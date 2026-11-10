"""Root-finding methods on the simulated machine.  YOU WRITE THIS FILE.

Read README.md, sections 4 "Methods" and 5 "Result and errors", before starting.
Every method takes ``f`` (or ``g``) as a string or a parsed Expression and
returns a RootResult. Use Machine operations for every arithmetic step of the
method's formula, in exactly the order given in the README.
"""

from __future__ import annotations

from .result import RootResult


def bisection(f, xl, xu, *, sig_figs=None, mode="round", eps=None, max_iter=50, true_root=None) -> RootResult:
    """xr = (xl + xu) / 2."""
    raise NotImplementedError


def false_position(f, xl, xu, *, sig_figs=None, mode="round", eps=None, max_iter=50, true_root=None) -> RootResult:
    """xr = xu - (f(xu) * (xl - xu)) / (f(xl) - f(xu))."""
    raise NotImplementedError


def fixed_point(g, x0, *, sig_figs=None, mode="round", eps=None, max_iter=50, true_root=None) -> RootResult:
    """x_{i+1} = g(x_i)."""
    raise NotImplementedError


def newton(f, x0, *, sig_figs=None, mode="round", eps=None, max_iter=50, true_root=None) -> RootResult:
    """x_{i+1} = x_i - f(x_i) / f'(x_i)."""
    raise NotImplementedError


def modified_newton(f, x0, *, sig_figs=None, mode="round", eps=None, max_iter=50, true_root=None) -> RootResult:
    """x_{i+1} = x_i - (f f') / (f' f' - f f'')."""
    raise NotImplementedError


def secant(f, x0, x1, *, sig_figs=None, mode="round", eps=None, max_iter=50, true_root=None) -> RootResult:
    """x_{i+1} = x_i - (f(x_i) * (x_{i-1} - x_i)) / (f(x_{i-1}) - f(x_i))."""
    raise NotImplementedError
