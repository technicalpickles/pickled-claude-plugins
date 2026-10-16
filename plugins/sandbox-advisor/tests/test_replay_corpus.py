"""Regression corpus: failure shapes seen in real sandboxed sessions.

Each line of fixtures/replay-corpus.jsonl is modeled on a real failed Bash
call from session history (paths rewritten), labeled with the mode the hook
should pick, or null for "stay silent". Run tools/replay.py against your own
history to find new shapes worth adding here.
"""
import importlib.util
import json
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location(
    "advise", Path(__file__).parent.parent / "hooks" / "advise.py"
)
advise = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(advise)

CORPUS = Path(__file__).parent / "fixtures" / "replay-corpus.jsonl"
CASES = [json.loads(line) for line in CORPUS.read_text().splitlines() if line.strip()]


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_corpus_case(case):
    payload = {
        "tool_name": "Bash",
        "cwd": case["cwd"],
        "tool_input": {
            "command": case["command"],
            "dangerouslyDisableSandbox": case.get("unsandboxed", False),
        },
        "tool_response": {"stderr": case["error"]},
    }
    assert advise.decide_mode(payload) == case["expect"]


def test_every_advice_mode_is_covered():
    covered = {c["expect"] for c in CASES if c["expect"]}
    assert covered == set(advise._ADVICE)
