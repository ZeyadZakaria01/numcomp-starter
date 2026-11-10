"""Expression parsing, evaluation on a simulated machine, and symbolic derivatives.

PROVIDED: do not edit (the grader overwrites it).

The evaluator walks the expression exactly as typed (Python precedence and
associativity, left operand before right) and sends every arithmetic operation
to a ``Machine`` (see ``machine.py``), which rounds each result. Nothing is
simplified, expanded or reordered, so ``x**3 - 5*x**2`` and ``(x - 5)*x**2``
can give different answers at low precision, exactly as in Tutorial 2.

Derivatives are built with SymPy and converted back into the same tree form;
their printed form is shown by ``str(expr.derivative())``.
"""

from __future__ import annotations

import ast
import math
import re
from fractions import Fraction
from typing import Protocol

import sympy

from .errors import DivergenceError, ExpressionError

FUNCTIONS = ("exp", "sin", "cos", "tan", "ln", "sqrt", "abs")
ALIASES = {"log": "ln"}
CONSTANTS = {"pi": math.pi, "e": math.e}
MAX_EXPONENT = 64


class MachineLike(Protocol):
    def enter(self, value: int | float | Fraction) -> float: ...
    def add(self, a: float, b: float) -> float: ...
    def sub(self, a: float, b: float) -> float: ...
    def mul(self, a: float, b: float) -> float: ...
    def div(self, a: float, b: float) -> float: ...
    def pow_int(self, a: float, k: int) -> float: ...
    def call(self, name: str, a: float) -> float: ...


# Tree nodes are tuples:
#   ("var",)  ("num", int | float | Fraction)  ("const", "pi" | "e")
#   ("neg", a)  ("add" | "sub" | "mul" | "div", a, b)  ("pow", a, k)  ("call", name, a)
Node = tuple

_BINOPS = {ast.Add: "add", ast.Sub: "sub", ast.Mult: "mul", ast.Div: "div"}
_IMPLICIT = re.compile(r"(\d|\))\s*([A-Za-z_(])")


class Expression:
    """A parsed f(x). Create with ``parse(text)``."""

    def __init__(self, text: str, node: Node, sym: sympy.Expr | None = None):
        self.text = text
        self._node = node
        self._sym = sym
        self._derivatives: dict[int, Expression] = {}

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        return f"Expression({self.text!r})"

    def evaluate(self, machine: MachineLike, x: float) -> float:
        """Value at ``x`` (which must already be a machine number)."""
        try:
            return _eval(self._node, machine, x)
        except ZeroDivisionError:
            raise ExpressionError(f"division by zero evaluating {self} at x = {x!r}") from None
        except ValueError as exc:
            raise ExpressionError(f"math domain error evaluating {self} at x = {x!r} ({exc})") from None
        except OverflowError:
            raise DivergenceError(f"overflow evaluating {self} at x = {x!r}") from None

    def derivative(self, order: int = 1) -> Expression:
        """d^order f / dx^order. Raises ExpressionError if it cannot be represented
        (e.g. the derivative of abs(x) is sign(x), which is not supported)."""
        if order < 1:
            raise ValueError("order must be >= 1")
        if order not in self._derivatives:
            sym = sympy.diff(self._sympy(), _X, order)
            node = _from_sympy(sym)
            self._derivatives[order] = Expression(_format(node)[0], node, sym)
        return self._derivatives[order]

    def _sympy(self) -> sympy.Expr:
        if self._sym is None:
            self._sym = _to_sympy(self._node)
        return self._sym


def parse(text: str) -> Expression:
    """Parse ``text`` into an Expression; raises ExpressionError with a hint."""
    if not isinstance(text, str):
        raise ExpressionError("the expression must be a string")
    src = text.strip()
    if not src:
        raise ExpressionError("empty expression")
    try:
        tree = ast.parse(src.replace("^", "**"), mode="eval")
    except SyntaxError:
        raise ExpressionError(f"invalid syntax in {text!r}{_hint(src)}") from None
    return Expression(src, _convert(tree.body, src))


def _hint(src: str) -> str:
    m = _IMPLICIT.search(src)
    if m is None:
        return ""
    return f": implicit multiplication is not allowed, write '{m.group(1)}*{m.group(2)}'"


# ---------------------------------------------------------------- parsing


def _convert(node: ast.AST, src: str) -> Node:
    if isinstance(node, ast.Constant):
        v = node.value
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise ExpressionError(f"unsupported literal {v!r}")
        if isinstance(v, float) and not math.isfinite(v):
            raise ExpressionError("numeric literal is too large")
        return ("num", v)
    if isinstance(node, ast.Name):
        if node.id == "x":
            return ("var",)
        if node.id in CONSTANTS:
            return ("const", node.id)
        if node.id in FUNCTIONS or node.id in ALIASES:
            raise ExpressionError(f"'{node.id}' is a function, write {node.id}(...)")
        raise ExpressionError(f"unknown name '{node.id}': the variable is x; constants are pi and e")
    if isinstance(node, ast.UnaryOp):
        if isinstance(node.op, ast.USub):
            return ("neg", _convert(node.operand, src))
        if isinstance(node.op, ast.UAdd):
            return _convert(node.operand, src)
        raise ExpressionError("unsupported unary operator")
    if isinstance(node, ast.BinOp):
        if isinstance(node.op, ast.Pow):
            return ("pow", _convert(node.left, src), _exponent(node.right))
        op = _BINOPS.get(type(node.op))
        if op is None:
            raise ExpressionError("unsupported operator: use + - * / and ** (or ^)")
        return (op, _convert(node.left, src), _convert(node.right, src))
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id == "x":
            raise ExpressionError(f"cannot call a value in {src!r}{_hint(src) or ': missing *'}")
        name = ALIASES.get(node.func.id, node.func.id)
        if name not in FUNCTIONS:
            raise ExpressionError(f"unknown function '{node.func.id}'; allowed: {', '.join(FUNCTIONS)}, log")
        if len(node.args) != 1 or node.keywords:
            raise ExpressionError(f"{node.func.id}() takes exactly one argument")
        return ("call", name, _convert(node.args[0], src))
    raise ExpressionError(f"unsupported syntax ({type(node).__name__}) in {src!r}")


def _exponent(node: ast.AST) -> int:
    sign = 1
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        sign = -1 if isinstance(node.op, ast.USub) else 1
        node = node.operand
    if not (isinstance(node, ast.Constant) and type(node.value) is int):
        raise ExpressionError(
            "exponent must be an integer literal such as x**3 or x**(-2); "
            "use sqrt(...) for square roots and exp(...) for e**(...)"
        )
    k = sign * node.value
    if abs(k) > MAX_EXPONENT:
        raise ExpressionError(f"exponent {k} is outside [-{MAX_EXPONENT}, {MAX_EXPONENT}]")
    return k


# ------------------------------------------------------------- evaluation


def _eval(node: Node, m: MachineLike, x: float) -> float:
    kind = node[0]
    if kind == "var":
        return x
    if kind == "num":
        return m.enter(node[1])
    if kind == "const":
        return m.enter(CONSTANTS[node[1]])
    if kind == "neg":
        return -_eval(node[1], m, x) + 0.0  # exact; + 0.0 turns -0.0 into 0.0
    if kind == "pow":
        return m.pow_int(_eval(node[1], m, x), node[2])
    if kind == "call":
        a = _eval(node[2], m, x)
        return abs(a) if node[1] == "abs" else m.call(node[1], a)
    a = _eval(node[1], m, x)
    b = _eval(node[2], m, x)
    return getattr(m, kind)(a, b)


# ------------------------------------------------------------ derivatives

_X = sympy.Symbol("x", real=True)
_SYM_FUNCS = {"exp": sympy.exp, "sin": sympy.sin, "cos": sympy.cos, "tan": sympy.tan,
              "ln": sympy.log, "sqrt": sympy.sqrt, "abs": sympy.Abs}
_FROM_SYM = ((sympy.exp, "exp"), (sympy.sin, "sin"), (sympy.cos, "cos"), (sympy.tan, "tan"),
             (sympy.log, "ln"), (sympy.Abs, "abs"))


def _to_sympy(node: Node) -> sympy.Expr:
    kind = node[0]
    if kind == "var":
        return _X
    if kind == "num":
        v = node[1]
        if isinstance(v, float):
            return sympy.Rational(repr(v))  # exact decimal value of the literal
        v = Fraction(v)
        return sympy.Rational(v.numerator, v.denominator)
    if kind == "const":
        return sympy.pi if node[1] == "pi" else sympy.E
    if kind == "neg":
        return -_to_sympy(node[1])
    if kind == "pow":
        return _to_sympy(node[1]) ** sympy.Integer(node[2])
    if kind == "call":
        return _SYM_FUNCS[node[1]](_to_sympy(node[2]))
    a, b = _to_sympy(node[1]), _to_sympy(node[2])
    return {"add": a + b, "sub": a - b, "mul": a * b, "div": a / b}[kind]


def _from_sympy(s: sympy.Expr) -> Node:
    if s == _X:
        return ("var",)
    if s is sympy.pi:
        return ("const", "pi")
    if s is sympy.E:
        return ("const", "e")
    if s.is_Rational:
        return ("num", Fraction(int(s.p), int(s.q)))
    for cls, name in _FROM_SYM:
        if isinstance(s, cls):
            if len(s.args) != 1:
                break
            return ("call", name, _from_sympy(s.args[0]))
    if s.is_Add:
        terms = s.as_ordered_terms()
        acc = _from_sympy(terms[0])
        for t in terms[1:]:
            acc = ("sub", acc, _from_sympy(-t)) if t.could_extract_minus_sign() else ("add", acc, _from_sympy(t))
        return acc
    if s.is_Mul:
        c, rest = s.as_coeff_Mul()
        if c.is_negative:
            return ("neg", _from_sympy(-s))
        num, den = sympy.fraction(rest, exact=True)
        coef = None if c == 1 else ("num", Fraction(int(c.p), int(c.q)))
        if den == 1:
            top = _product(num)
            return top if coef is None else ("mul", coef, top)
        if num == 1:
            top = coef if coef is not None else ("num", Fraction(1))
        else:
            top = _product(num) if coef is None else ("mul", coef, _product(num))
        return ("div", top, _product(den))
    if s.is_Pow:
        base, e = s.args
        if e.is_Integer:
            k = int(e)
            if abs(k) > MAX_EXPONENT:
                raise ExpressionError(f"derivative needs exponent {k}, outside [-{MAX_EXPONENT}, {MAX_EXPONENT}]")
            return ("pow", _from_sympy(base), k)
        if e.is_Rational and e.q == 2:
            root = ("call", "sqrt", _from_sympy(base))
            p = int(e.p)
            if p == 1:
                return root
            if p < 0:
                return ("div", ("num", Fraction(1)), root if p == -1 else ("pow", root, -p))
            return ("pow", root, p)
    raise ExpressionError(f"derivative contains an unsupported construct: {s}")


def _product(s: sympy.Expr) -> Node:
    if not s.is_Mul:
        return _from_sympy(s)
    factors = s.as_ordered_factors()
    acc = _from_sympy(factors[0])
    for f in factors[1:]:
        acc = ("mul", acc, _from_sympy(f))
    return acc


# --------------------------------------------------------------- printing

_PREC = {"add": 1, "sub": 1, "mul": 2, "div": 2, "neg": 3, "pow": 4}
_SYMBOL = {"add": " + ", "sub": " - ", "mul": "*", "div": "/"}


def _format(node: Node) -> tuple[str, int]:
    kind = node[0]
    if kind == "var":
        return "x", 5
    if kind == "const":
        return node[1], 5
    if kind == "num":
        v = node[1]
        if isinstance(v, Fraction):
            return (str(v.numerator), 5) if v.denominator == 1 else (f"{v.numerator}/{v.denominator}", 2)
        return repr(v), 5
    if kind == "neg":
        s, p = _format(node[1])
        return "-" + (s if p >= 3 else f"({s})"), 3
    if kind == "pow":
        s, p = _format(node[1])
        k = node[2]
        return (s if p >= 5 else f"({s})") + (f"**{k}" if k >= 0 else f"**({k})"), 4
    if kind == "call":
        return f"{node[1]}({_format(node[2])[0]})", 5
    prec = _PREC[kind]
    ls, lp = _format(node[1])
    rs, rp = _format(node[2])
    ls = ls if lp >= prec else f"({ls})"
    rs = rs if rp > prec else f"({rs})"  # left-associative: same-level right operand keeps its parentheses
    return ls + _SYMBOL[kind] + rs, prec
