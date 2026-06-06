"""Unit tests for sandbox-advisor pure functions."""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "advise", Path(__file__).parent.parent / "hooks" / "advise.py"
)
advise = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(advise)


class TestMatchesModeFingerprints:
    def test_git_index_lock(self):
        assert advise.matches_mode_fingerprints(
            "fatal: Unable to create '.git/worktrees/x/index.lock': "
            "Operation not permitted",
            "git-write",
        )

    def test_git_blocked_path(self):
        assert advise.matches_mode_fingerprints(
            "error: unable to create file .claude/agents/x.md: "
            "Operation not permitted",
            "git-write",
        )

    def test_git_downstream_reset_index(self):
        # The polymorphic case: only the downstream message is visible.
        assert advise.matches_mode_fingerprints(
            "fatal: Could not reset index file to revision 'HEAD'.",
            "git-write",
        )

    def test_srb_lmdb(self):
        assert advise.matches_mode_fingerprints(
            'mdb_error: "Operation not permitted" failed to create database',
            "srb",
        )

    def test_ps_setuid_eperm(self):
        assert advise.matches_mode_fingerprints(
            "ps: Operation not permitted (os error 1)", "ps-top"
        )

    def test_srb_typecheck_is_not_a_sandbox_failure(self):
        assert not advise.matches_mode_fingerprints(
            "srb: typecheck found 3 errors in 2 files", "srb"
        )

    def test_git_fingerprint_does_not_leak_to_srb(self):
        # An index.lock message is a git signature, not an srb one.
        assert not advise.matches_mode_fingerprints(
            "Unable to create 'index.lock'", "srb"
        )

    def test_empty(self):
        assert not advise.matches_mode_fingerprints("", "git-write")
