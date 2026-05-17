"""Tests for the skill-advice hook helper.

Runs the helper script as a subprocess, feeding PreToolUse-shaped JSON to
stdin, and asserts on exit code and stdout.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parent / "skill-advice.py"


def run_helper(stdin_text: str, args: list[str]) -> tuple[int, str]:
    """Invoke skill-advice.py as a subprocess. Return (exit_code, stdout)."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        input=stdin_text,
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout


class SkillAdviceTests(unittest.TestCase):
    def test_tool_mismatch_emits_nothing(self):
        stdin = json.dumps({"tool_name": "Bash", "tool_input": {}})
        code, out = run_helper(
            stdin, ["--skill", "superpowers:brainstorming", "--advice", "hi"]
        )
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_skill_mismatch_emits_nothing(self):
        stdin = json.dumps(
            {"tool_name": "Skill", "tool_input": {"skill": "other"}}
        )
        code, out = run_helper(
            stdin, ["--skill", "superpowers:brainstorming", "--advice", "hi"]
        )
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_unparseable_stdin_exits_silently(self):
        code, out = run_helper(
            "not json",
            ["--skill", "superpowers:brainstorming", "--advice", "hi"],
        )
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_empty_stdin_exits_silently(self):
        code, out = run_helper(
            "",
            ["--skill", "superpowers:brainstorming", "--advice", "hi"],
        )
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_match_emits_additional_context(self):
        stdin = json.dumps(
            {"tool_name": "Skill", "tool_input": {"skill": "x"}}
        )
        code, out = run_helper(
            stdin, ["--skill", "x", "--advice", "do the thing"]
        )
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(
            payload,
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "additionalContext": "do the thing",
                }
            },
        )

    def test_if_file_missing_exits_silently(self):
        with tempfile.TemporaryDirectory() as tmp:
            stdin = json.dumps(
                {"tool_name": "Skill", "tool_input": {"skill": "x"}, "cwd": tmp}
            )
            code, out = run_helper(
                stdin,
                ["--skill", "x", "--if-file", "missing.md", "--advice", "hi"],
            )
            self.assertEqual(code, 0)
            self.assertEqual(out, "")

    def test_if_file_present_relative_emits_advice(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "found.md").write_text("here")
            stdin = json.dumps(
                {"tool_name": "Skill", "tool_input": {"skill": "x"}, "cwd": tmp}
            )
            code, out = run_helper(
                stdin,
                ["--skill", "x", "--if-file", "found.md", "--advice", "hi"],
            )
            self.assertEqual(code, 0)
            payload = json.loads(out)
            self.assertEqual(
                payload["hookSpecificOutput"]["additionalContext"], "hi"
            )

    def test_if_file_absolute_path(self):
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            stdin = json.dumps(
                {"tool_name": "Skill", "tool_input": {"skill": "x"}}
            )
            code, out = run_helper(
                stdin,
                ["--skill", "x", "--if-file", tmp_path, "--advice", "hi"],
            )
            self.assertEqual(code, 0)
            payload = json.loads(out)
            self.assertEqual(
                payload["hookSpecificOutput"]["additionalContext"], "hi"
            )
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_missing_required_args_errors(self):
        # argparse exits 2 on missing required args, prints to stderr.
        # The hook will degrade silently because the wrapper command should
        # be configured correctly, but the script itself should fail loudly
        # on misconfiguration to surface bad settings.json entries during
        # development.
        proc = subprocess.run(
            [sys.executable, str(SCRIPT)],
            input="",
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(proc.returncode, 0)


if __name__ == "__main__":
    unittest.main()
