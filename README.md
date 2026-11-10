# Numerical Computing Project: Roots of Equations

Write `numcomp`, a Python package with six root-finding methods (bisection,
false position, fixed point, Newton, modified Newton, secant) that run on a
**simulated calculator keeping *n* significant figures**: every operation is
rounded or chopped to *n* digits, like the tutorials' hand calculations.
`sig_figs=None` means ordinary double precision. Dates and report requirements
are in `project.pdf`.

```python
>>> import numcomp as nc
>>> r = nc.bisection("-0.4*x**2 + 2.2*x + 4.7", 5, 10, eps=5)   # Tutorial 3 table
>>> r.root, r.iterations, r.stop_reason
(7.1875, 4, 'tolerance')
```

## 1. Setup

Requires Python ≥ 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync                          # create .venv with the pinned packages
uv run pytest                    # all public tests (they fail until you implement)
uv run pytest -k bisection       # one category
uv run pytest -k t3-bisection    # cases whose id contains "t3-bisection"
uv run pytest -x --tb=short      # stop at the first failure, short traceback
uv run pytest "tests/test_cases.py::test_case[bisection/normal/t3-bisection/result]"   # one test
```

Test ids are `category/tag/case-id/level`. Root-finding cases have three levels
(`result`, `iterations`, `trace`); other cases, and cases that expect an
exception, have one (`value`). Inputs and expected outputs are in
`tests/cases/public.json`.

| File | Who | Content |
|---|---|---|
| `numcomp/machine.py` | **you** | `round_sig`, `Machine` |
| `numcomp/roots.py` | **you** | the six methods |
| `numcomp/plot.py` | **you** | `plot` |
| `expr.py`, `errors.py`, `result.py`, `__init__.py`, `tests/` | provided | parser, exceptions, `RootResult`, tests |

**Do not edit the provided files**: the grader replaces them. You may add
helper modules inside `numcomp/`.

Create your team's repository from this template: **Use this template →
Create a new repository → Private**. Do not fork it: a fork of a public
repository is public. Add `ZeyadZakaria01` as a collaborator. The included
workflow runs the public tests on every push. Each member commits under their
own account: the history is used in the oral discussion.

Suggested order (each step builds on the previous one):

| Step | Implement | Test with `uv run pytest -k …` |
|---|---|---|
| 1 | `round_sig` | `rounding` |
| 2 | `Machine` | `machine`, then `expression` (the provided parser on your machine) |
| 3 | `bisection` (the loop all methods share) | `bisection` |
| 4 | the other methods | `false_position`, `fixed_point`, `"newton and not modified"`, `modified_newton`, `secant` |
| 5 | `plot` | not autograded |

## 2. The machine (`machine.py`)

Every operation takes the **exact decimal values** of its operands, computes
the **exact** result with `Fraction`, then **rounds once**. Float arithmetic is
not enough: `-14.8 + 16.5` is `1.6999999999999993` in floats, which chops to
`1.69`; `Machine(3, "chop")` must give `1.70`.

Worked example: *y = x³ − 5x² + 7x − 0.25* at *x* = 2.37, *n* = 3, chopping.

| Step | Operation | Exact | Stored |
|---|---|---|---|
| x² | 2.37 × 2.37 | 5.6169 | 5.61 |
| x³ | 5.61 × 2.37 | 13.2957 | 13.2 |
| 5x² | 5 × 5.61 | 28.05 | 28.0 |
| 7x | 7 × 2.37 | 16.59 | 16.5 |
| | 13.2 − 28.0 | −14.8 | −14.8 |
| | −14.8 + 16.5 | 1.7 | 1.70 |
| y | 1.70 − 0.25 | 1.45 | 1.45 |

The nested form `((x - 5)*x + 7)*x - 0.25` gives 1.57 (true value 1.567553).

**`round_sig(value, n, mode="round") -> float`**

1. Exact value: `int`/`Fraction` as is; a float via `Fraction(repr(float(value)))`
   (not `Fraction(value)`, which gives the binary value: `2.675` → `2.67499…`).
2. Find *e* with 10^e ≤ |q| < 10^(e+1) **exactly** (not with `math.log10`).
3. Keep *n* digits. `"round"`: add one unit if the rest is ≥ ½ unit, so ties
   go away from zero. `"chop"`: drop the rest.
4. Return a `float`.

| value | n | mode | result |
|---|---|---|---|
| 2.675 | 3 | round | 2.68 |
| 9.995 | 3 | round | 10.0 |
| 0.0072684 | 3 | round | 0.00727 |
| 150.23 | 1 | round | 200.0 |
| −2.5 | 1 | round | −3.0 |
| 3.1415926535 | 7 | chop | 3.141592 |
| −2.59 | 2 | chop | −2.5 |

Checks in this order, each `ValueError`: `n` not an `int` in 1…12 or `None`;
`mode` not `"round"`/`"chop"`; `value` not an `int`, `float` or `Fraction`
(`bool` is never accepted). `n=None` only converts to `float`. inf, nan or a
result too large for a float → `DivergenceError`. Underflow to `0.0` is fine;
never return `-0.0`.

**`Machine(sig_figs=None, mode="round")`** validates like `round_sig`. Every
result follows the same rules; with `sig_figs=None` it is plain float math.

| Method | Behaviour |
|---|---|
| `enter(v)` | round an outside number (literal, constant, starting value) once; `v` is checked like `value` |
| `add`, `sub`, `mul`, `div` | exact result, rounded once; `div` by 0 → `ZeroDivisionError` |
| `pow_int(a, k)` | `k = 0`: `enter(1)`; `k > 0`: `r = a`, then `r = mul(r, a)` k−1 times; `k < 0`: `div(enter(1), pow_int(a, -k))` |
| `call(name, a)` | `exp sin cos tan ln sqrt` with `math`, then `enter`; `ValueError` propagates, `OverflowError` → `DivergenceError` |

## 3. Expressions (provided)

```python
f = nc.parse("x**3 - 5*x**2 + 7*x - 0.25")   # methods also accept the string
m = nc.Machine(4)
f.evaluate(m, m.enter(2.37))                  # x must already be a machine number
print(f.derivative(), f.derivative(2))        # 3*x**2 - 10*x + 7   2*(3*x - 5)
```

Syntax: `x`, `pi`, `e`, `+ - * /`, `**` or `^` with integer exponents in
−64…64, `exp sin cos tan ln log sqrt abs`; write `2*x`, not `2x`. Expressions
are **evaluated exactly as typed** (Python precedence, left operand first, one
machine operation per operator, literals entered each time; unary minus and
`abs` are exact), so `x**3 - 5*x**2` and `(x - 5)*x**2` can differ. Domain
errors → `ExpressionError`, overflow → `DivergenceError`. Derivatives come from
SymPy; print them to see exactly what is evaluated (a coefficient like `4/5`
is one constant). Unsupported derivatives (e.g. of `abs(x)`) →
`ExpressionError`.

## 4. Methods (`roots.py`)

```python
bisection(f, xl, xu, *, sig_figs=None, mode="round", eps=None, max_iter=50, true_root=None)
false_position(f, xl, xu, *, ...)   fixed_point(g, x0, *, ...)   secant(f, x0, x1, *, ...)
newton(f, x0, *, ...)               modified_newton(f, x0, *, ...)
```

Arguments (otherwise `ValueError`; numbers are `int`/`float`, never `bool`):

- starting values: finite `int`/`float` (an integer too large for a float is
  invalid; overflow while entering one → `DivergenceError`);
- `eps`: ε_s in **percent**, finite and > 0; default 0.5 × 10^(2−n) %, or
  0.001 % when `sig_figs=None`;
- `max_iter`: positive `int`;
- `true_root`: `None` or finite; only used for `true_sig_figs`, never rounded.

**Every method:**

1. Validate `sig_figs`, `mode`, `eps`, `max_iter`, `true_root` in that order.
2. Parse `f`; Newton builds `f′`, modified Newton `f′` then `f″` (before the
   starting values are checked).
3. Validate and `enter` each starting value in signature order.
4. Setup and pre-loop checks (below). A pre-loop exact zero returns that value
   with `iterations = 0`, `steps = []`, `ea = None`, `residual = 0.0`,
   `stop_reason = "computed_zero"`.
5. For `i = 1 … max_iter`: compute the new estimate, evaluate the function
   there, compute ε_a, append the row, then stop on the first of:
   `"computed_zero"` (function value exactly 0), `"stagnated"` (no movement),
   `"tolerance"` (ε_a ≤ ε_s, not <), `"max_iter"` (normal result, not an error).

**For all methods:**

- Compute each formula below with machine operations **in the order written**
  (inner parentheses first). Equivalent rewrites give different answers.
- ε_a = |(x_new − x_old) / x_new| × 100, in double precision. If
  `x_new == 0`: ε_a = 0 when `x_old == 0`, else `inf`.
- With finite `sig_figs` and the default `eps`, a run never stops by
  `"tolerance"` (the default is below the machine's resolution).
- Trace rows hold machine values; `i` starts at 1.

### Bisection and false position

```text
bisection:       xr = (xl + xu) / 2                            # 2 is m.enter(2)
false position:  xr = xu - f(xu)*(xl - xu) / (f(xl) - f(xu))   # plain version only
```

- **Before the loop:** `xl < xu` after `enter`, else `ValueError`. Return `xl`
  if `f(xl) == 0`, then `xu` if `f(xu) == 0`. If both have the same sign, raise
  `BracketError`.
- **Update:** `xu = xr` if `f(xl)` and `f(xr)` differ in sign, else `xl = xr`.
  Compare signs; don't multiply (the product can underflow to 0).
- **ε_a:** this `xr` vs the previous `xr`; `None` on row 1.
- **Stagnated:** `xr` is not strictly between `xl` and `xu`.
- The false-position denominator cannot be 0; overflow there is a
  `DivergenceError`.
- **Trace:** `i, xl, f_xl, xu, f_xu, xr, f_xr, ea` (bracket before the update).

### Fixed point

```text
x_new = g(x)
```

- Takes *g*, not *f*.
- **Before the loop:** `g_prime_x0` = *g′(x0)*, a diagnostic only (never
  refuse to run). If it raises a `NumCompError`, use `None`.
- Each iteration evaluates only `g(x)`. **Computed zero:** `g(x) == x`.
  Never stagnated.
- **ε_a:** `g(x)` vs `x`.
- Catch only `NumCompError` (for `g_prime_x0` and the residual).
- **Trace:** `i, x, g_x, ea`.

### Newton and modified Newton

```text
Newton:           x_new = x - f(x)/f'(x)
modified Newton:  x_new = x - f(x)*f'(x) / (f'(x)*f'(x) - f(x)*f''(x))
```

- **Before the loop:** return `x0` if `f(x0) == 0`.
- Each iteration evaluates `f′(x)` (then `f″(x)`). A zero denominator raises
  `ZeroDerivativeError`. Reuse `f(x_new)` as the next `f(x)`.
- **ε_a:** `x_new` vs `x`. **Stagnated:** `x_new == x`.
- **Trace:** `i, x, f_x, df_x, x_next, ea`; modified Newton adds `d2f_x`
  before `x_next`.

### Secant

```text
x_new = x1 - f(x1)*(x0 - x1) / (f(x0) - f(x1))
```

- **Before the loop:** return `x1` if `f(x1) == 0`, then `x0` if `f(x0) == 0`.
- `f(x0) − f(x1) = 0` raises `ZeroDerivativeError`.
- **ε_a:** `x_new` vs `x1`. **Stagnated:** `x_new == x1`.
- **Update:** `x0, x1 = x1, x_new`.
- **Trace:** `i, x_prev, x, f_prev, f_x, x_next, ea` (`x_prev` is `x0`).

## 5. Result and errors

`RootResult` fields (see `result.py`): `method` is the function name, e.g.
`"false_position"`; `time_s` is the call's `perf_counter` time (not graded);
`root` is the last new estimate;
`iterations = len(steps)`; `ea` is the last row's ε_a; `residual` is the
function value at `root` on the machine; `g_prime_x0` is `None` except for
fixed point. For fixed point, the residual is 0.0 on `"computed_zero"`, else
`m.sub(g(root), root)` evaluated once after stopping (`nan` if that raises a
`NumCompError`).

Significant figures, with *cap* = `sig_figs` (15 if `None`) and *E* in percent:
digits(E) = `None` if *E* is `None`, *cap* if 0, 0 if inf, otherwise
⌊2 − log₁₀(2E)⌋ clamped to [0, cap].
`estimated_sig_figs` = digits(ε_a), but `None` when `"stagnated"`;
`true_sig_figs` = digits(|(true_root − root) / true_root| × 100), or `None`
without a nonzero `true_root`.

Errors are documented in `errors.py`; invalid arguments raise `ValueError`.
Raise exactly the class named here, not a subclass of it (tests check the
exact type).
When a method raises during its iterations, attach the completed rows
(`exc.steps`). Messages say what went wrong and where, e.g.
`f(xl) = 5.7 and f(xu) = 4.1 have the same sign: [5, 6] does not bracket a root`.

## 6. Plotting (`plot.py`)

`plot(expr, a, b, path, *, fixed_point=False, points=400) -> Path` saves a PNG
of *f(x)* and the x-axis, or *g(x)* and *y = x*, evaluated with
`Machine(None)`, with gaps where `expr` is undefined. `ValueError` unless
`a < b` and `points ≥ 2`. Not autograded; use it to choose starting values
and include the plots in your report.

## 7. Grading and rules

- Public tests are the tutorial examples plus one case of each kind of
  failure.
- Private tests run the same test code on many more cases (every *n* from 1
  to 12, ties, carries, every stop reason and error). **Passing the public
  tests is not enough: follow this document.** Each root case scores `root` +
  `stop_reason`, the other fields, and the trace, compared to 13 significant
  digits (with `sig_figs=None`, residuals and function values within `1e-12`,
  ε_a within `1e-9`). Teams receive their failed categories, not the cases.
- Individual oral: predict trace rows by hand, explain a failure, change your
  code on the spot.
- Allowed: the standard library; SymPy only via `expr.py`; matplotlib/NumPy
  only in `plot.py`. Not allowed: `decimal`, `round()`, `Fraction.__round__`,
  `scipy`, `mpmath`, `eval`/`exec`, SymPy solvers. Submissions are scanned.
- AI tools (ChatGPT, Copilot, Claude, Cursor, …) must not be used to write any
  part of the code or the report; using them, or copying from other teams or
  previous years, is cheating. Submissions are compared with each other and
  with AI-generated solutions, and similar ones are examined in the oral. Code
  you cannot explain and modify yourself in the oral counts as not yours.
