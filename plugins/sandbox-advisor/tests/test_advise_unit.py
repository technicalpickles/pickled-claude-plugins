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

    def test_git_ssh_port_22(self):
        assert advise.matches_mode_fingerprints(
            "ssh: connect to host github.com port 22: Operation not permitted",
            "git-ssh",
        )

    def test_git_ssh_negotiation_failed(self):
        assert advise.matches_mode_fingerprints(
            "nc: authentication method negotiation failed\n"
            "Connection closed by UNKNOWN port 65535\n"
            "fatal: Could not read from remote repository.",
            "git-ssh",
        )

    def test_git_ssh_gh_wrapped(self):
        assert advise.matches_mode_fingerprints(
            "fatal: Could not read from remote repository.\n\n"
            "Please make sure you have the correct access rights\n"
            "and the repository exists.\n"
            "failed to run git: exit status 128",
            "git-ssh",
        )

    def test_git_ssh_does_not_fire_on_bare_operation_not_permitted(self):
        # The generic EPERM string alone must not trigger git-ssh -- it's
        # excluded from this mode's fingerprints because the `gh` matcher is
        # broad and would otherwise false-positive on unrelated gh failures.
        assert not advise.matches_mode_fingerprints(
            "Operation not permitted", "git-ssh"
        )

    def test_keychain_write_seckeychain_api_name(self):
        assert advise.matches_mode_fingerprints(
            "security: SecKeychainItemCreateFromContent (<default>): "
            "UNIX[Operation not permitted]",
            "keychain-write",
        )

    def test_keychain_write_bare_eperm(self):
        # Safe here (unlike git-ssh) because the command matcher is narrow:
        # only gh auth login/refresh/logout/setup-git and security add-/
        # delete-*-password classify as keychain-write in the first place.
        assert advise.matches_mode_fingerprints(
            "Operation not permitted", "keychain-write"
        )


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

    def test_git_push_is_git_ssh_not_git_write(self):
        assert advise.classify_command("git push origin main") == "git-ssh"

    def test_git_fetch_is_git_ssh(self):
        assert advise.classify_command("git fetch origin") == "git-ssh"

    def test_git_pull_is_git_ssh(self):
        assert advise.classify_command("git pull") == "git-ssh"

    def test_git_clone_is_git_ssh(self):
        assert advise.classify_command(
            "git clone git@github.com:foo/bar.git"
        ) == "git-ssh"

    def test_git_ls_remote_is_git_ssh(self):
        assert advise.classify_command("git ls-remote origin") == "git-ssh"

    def test_gh_pr_checkout_is_git_ssh(self):
        assert advise.classify_command("gh pr checkout 99") == "git-ssh"

    def test_gh_pr_list_is_git_ssh(self):
        # Broad on purpose -- fingerprint gating in decide_advice() keeps
        # unrelated gh failures silent.
        assert advise.classify_command("gh pr list") == "git-ssh"

    def test_git_add_stays_git_write(self):
        assert advise.classify_command("git add .") == "git-write"

    def test_gh_auth_login_is_keychain_write(self):
        assert advise.classify_command("gh auth login") == "keychain-write"

    def test_gh_auth_refresh_is_keychain_write(self):
        assert advise.classify_command(
            "gh auth refresh -h github.com"
        ) == "keychain-write"

    def test_gh_auth_logout_is_keychain_write(self):
        assert advise.classify_command("gh auth logout") == "keychain-write"

    def test_gh_auth_setup_git_is_keychain_write(self):
        assert advise.classify_command("gh auth setup-git") == "keychain-write"

    def test_gh_auth_status_is_not_keychain_write(self):
        # Read-only: must fall through to the broad gh (git-ssh) bucket, not
        # keychain-write.
        assert advise.classify_command("gh auth status") == "git-ssh"

    def test_security_add_generic_password_is_keychain_write(self):
        assert advise.classify_command(
            "security add-generic-password -a foo -s bar -w baz"
        ) == "keychain-write"

    def test_security_delete_generic_password_is_keychain_write(self):
        assert advise.classify_command(
            "security delete-generic-password -a foo -s bar"
        ) == "keychain-write"

    def test_security_find_generic_password_is_not_keychain_write(self):
        # Read-only: unaffected by the sandbox, so it must classify as None
        # rather than trigger keychain-write advice.
        assert advise.classify_command(
            "security find-generic-password -a foo -s bar"
        ) is None


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

    def test_git_push_ssh_block_advises(self):
        reason = advise.decide_advice(
            self._payload(
                "git push origin main",
                "ssh: connect to host github.com port 22: "
                "Operation not permitted",
            )
        )
        assert reason is not None
        assert "dangerouslyDisableSandbox" in reason
        assert "https" in reason.lower()

    def test_gh_pr_checkout_ssh_block_advises(self):
        reason = advise.decide_advice(
            self._payload(
                "gh pr checkout 99",
                "nc: authentication method negotiation failed\n"
                "Connection closed by UNKNOWN port 65535\n"
                "fatal: Could not read from remote repository.\n"
                "failed to run git: exit status 128",
            )
        )
        assert reason is not None
        assert "ssh-agent" in reason.lower()

    def test_gh_unrelated_failure_stays_silent(self):
        # gh classifies broadly as git-ssh, but a validation error shares no
        # fingerprint with the mode -> must stay silent.
        reason = advise.decide_advice(
            self._payload(
                "gh issue create --title ''",
                "validation failed: title can't be blank",
            )
        )
        assert reason is None

    def test_gh_auth_login_keychain_block_advises(self):
        reason = advise.decide_advice(
            self._payload(
                "gh auth login",
                "security: SecKeychainItemCreateFromContent (<default>): "
                "UNIX[Operation not permitted]",
            )
        )
        assert reason is not None
        assert "dangerouslyDisableSandbox" in reason
        assert "keychain" in reason.lower()

    def test_security_add_password_keychain_block_advises(self):
        reason = advise.decide_advice(
            self._payload(
                "security add-generic-password -a foo -s bar -w baz",
                "security: SecKeychainItemCreateFromContent (<default>): "
                "UNIX[Operation not permitted]",
            )
        )
        assert reason is not None
        assert "keychain" in reason.lower()

    def test_security_find_password_success_stays_silent(self):
        # Reads aren't classified at all, so this hook never even considers
        # it -- included as a belt-and-suspenders check.
        reason = advise.decide_advice(
            self._payload(
                "security find-generic-password -a foo -s bar",
                "Operation not permitted",
            )
        )
        assert reason is None
