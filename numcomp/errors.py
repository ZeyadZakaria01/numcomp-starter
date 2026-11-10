"""Exception types raised by numcomp. PROVIDED: do not edit (the grader overwrites it)."""


class NumCompError(Exception):
    """Base class. ``steps`` holds the trace rows completed before the failure."""

    def __init__(self, message: str, steps: list[dict] | None = None):
        super().__init__(message)
        self.steps: list[dict] = steps if steps is not None else []


class ExpressionError(NumCompError):
    """Bad syntax, unknown name, unsupported construct, or a math domain error
    (division by zero, ln of a non-positive number, ...) while evaluating f."""


class BracketError(NumCompError):
    """f(xl) and f(xu) have the same sign: [xl, xu] does not bracket a root."""


class ZeroDerivativeError(NumCompError):
    """A method's own denominator is zero: f'(x) = 0 in Newton, f'^2 - f f'' = 0
    in modified Newton, f(x0) - f(x1) = 0 in secant."""


class DivergenceError(NumCompError):
    """A computed value overflowed or became non-finite (inf / nan)."""
