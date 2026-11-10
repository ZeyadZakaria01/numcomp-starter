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
        with pytest.raises(ERRORS[want["error"]]) as caught:
            run(case)
        if "steps_len" in want:
            assert hasattr(caught.value, "steps"), "exception is missing completed steps"
            assert len(caught.value.steps) == want["steps_len"]
        return
    got = run(case)
    if case["kind"] != "root":
        assert same(got, want["value"]), f"{case['input']}: expected {want['value']!r}, got {got!r}"
        return
    problems = mismatches(got, want, level, float_mode=case["input"]["kwargs"].get("sig_figs") is None)
    assert not problems, f"{case['input']}\n" + "\n".join(problems)
