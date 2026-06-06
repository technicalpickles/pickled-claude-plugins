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


class TestClassifyCommand:
    def test_bare_git_write(self):
        assert advise.classify_command("git add .") == "git-write"

    def test_git_write_after_cd(self):
        assert advise.classify_command(
            "cd repos/x/worktrees/y && git commit -m wip"
        ) == "git-write"

    def test_git_read_is_none(self):
        assert advise.classify_command("git log --oneline") is None

    def test_git_status_is_none(self):
        assert advise.classify_command("git status") is None

    def test_srb_bundle_exec(self):
        assert advise.classify_command("bundle exec srb tc") == "srb"

    def test_srb_bin(self):
        assert advise.classify_command("bin/srb tc") == "srb"

    def test_ps(self):
        assert advise.classify_command("ps aux") == "ps-top"

    def test_rtk_ps(self):
        assert advise.classify_command("rtk ps -ef") == "ps-top"

    def test_top(self):
        assert advise.classify_command("/usr/bin/top -l 1") == "ps-top"

    def test_psql_is_not_ps(self):
        assert advise.classify_command("psql -c 'select 1'") is None

    def test_unrelated_is_none(self):
        assert advise.classify_command("cat file.txt") is None

    def test_env_prefix_stripped(self):
        assert advise.classify_command("FOO=bar srb tc") == "srb"


class TestDecideAdvice:
    def _payload(self, command, output, unsandboxed=False):
        return {
            "tool_name": "Bash",
            "tool_input": {
                "command": command,
                "dangerouslyDisableSandbox": unsandboxed,
            },
            "tool_response": {"stderr": output},
        }

    def test_srb_sandbox_failure_advises(self):
        reason = advise.decide_advice(
            self._payload("bundle exec srb tc", "Operation not permitted")
        )
        assert reason is not None
        assert "dangerouslyDisableSandbox" in reason
        assert "sorbet" in reason.lower() or "lmdb" in reason.lower()

    def test_git_write_in_worktree_advises(self):
        reason = advise.decide_advice(
            self._payload(
                "cd repos/x/worktrees/y && git add .",
                "Unable to create '.git/worktrees/y/index.lock': "
                "Operation not permitted",
            )
        )
        assert reason is not None
        assert "git" in reason.lower()

    def test_ps_advises(self):
        reason = advise.decide_advice(
            self._payload("ps aux", "Operation not permitted (os error 1)")
        )
        assert reason is not None
        assert "setuid" in reason.lower()

    def test_srb_non_sandbox_failure_silent(self):
        # srb failed with type errors, not a sandbox EPERM -> no advice.
        reason = advise.decide_advice(
            self._payload("srb tc", "srb: typecheck found 3 errors")
        )
        assert reason is None

    def test_unknown_command_with_eperm_silent(self):
        reason = advise.decide_advice(
            self._payload("some-tool --x", "Operation not permitted")
        )
        assert reason is None

    def test_already_unsandboxed_silent(self):
        reason = advise.decide_advice(
            self._payload(
                "srb tc", "Operation not permitted", unsandboxed=True
            )
        )
        assert reason is None

    def test_fingerprint_in_command_text_only_stays_silent(self):
        # The fingerprint appears only in the command (a commit message), not
        # in the failure output -> must stay silent.
        reason = advise.decide_advice(self._payload(
            "git commit -m 'operation not permitted'",
            "nothing to commit, working tree clean",
        ))
        assert reason is None
