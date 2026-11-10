"""Result type shared by every root-finding method. PROVIDED: do not edit."""

from dataclasses import dataclass, field
from typing import Literal

StopReason = Literal["computed_zero", "stagnated", "tolerance", "max_iter"]


@dataclass
class RootResult:
    method: str
    root: float
    iterations: int  # == len(steps)
    ea: float | None  # approximate relative error of the last row, in percent
    estimated_sig_figs: int | None
    true_sig_figs: int | None  # only when true_root was given (and is nonzero)
    stop_reason: StopReason
    residual: float  # f(root); for fixed point g(root) - root
    steps: list[dict] = field(default_factory=list)
    time_s: float = 0.0
    g_prime_x0: float | None = None  # fixed point only; None if g' is unavailable
