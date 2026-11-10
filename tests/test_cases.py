"""Data-driven tests. The same file runs the public cases (students) and the
private cases (grader); NUMCOMP_CASES selects the case file.

Run:  uv run pytest            (public cases)
      uv run pytest -k newton  (one method)

PROVIDED: do not edit.
"""

import json
import os
from pathlib import Path

import pytest

from caselib import ERRORS, mismatches, run, same

CASES_FILE = Path(os.environ.get("NUMCOMP_CASES", Path(__file__).parent / "cases" / "public.json"))
CASES = json.loads(CASES_FILE.read_text())


def _levels(case):
    if case["kind"] == "root" and "error" not in case["expect"]:
        return ("result", "iterations", "trace")
    return ("value",)


PARAMS = [
    pytest.param(case, level, id=f"{case['category']}/{case['tag']}/{case['id']}/{level}")
    for case in CASES
    for level in _levels(case)
]


@pytest.mark.parametrize("case, level", PARAMS)
def test_case(case, level):
    want = case["expect"]
    if "error" in want:
        cls = ERRORS[want["error"]]
        expected = f"expected {want['error']} ({want['message']!r})"
        try:
            got = run(case)
        except Exception as exc:
            if type(exc) is not cls:
                raise AssertionError(f"{case['input']}: {expected}, got {type(exc).__name__}: {exc}") from exc
            caught = exc
        else:
            if hasattr(got, "stop_reason"):
                got = f"root={got.root!r}, stop_reason={got.stop_reason!r}"
            pytest.fail(f"{case['input']}: {expected}, but nothing was raised (returned {got})")
        if "steps_len" in want:
            rows = getattr(caught, "steps", None)
            assert rows is not None, f"{case['input']}: the exception has no .steps (rows completed before the error)"
            assert len(rows) == want["steps_len"], (
                f"{case['input']}: exception .steps has {len(rows)} rows, expected {want['steps_len']} "
                "(only rows completed before the error)")
        return
    got = run(case)
    if case["kind"] != "root":
        assert same(got, want["value"]), f"{case['input']}: expected {want['value']!r}, got {got!r}"
        return
    problems = mismatches(got, want, level, float_mode=case["input"]["kwargs"].get("sig_figs") is None)
    assert not problems, f"{case['input']}\n" + "\n".join(problems)
