"""Run advise.py as a subprocess with stdin, like Claude Code does."""
import json
import subprocess
from pathlib import Path

PLUGIN_ROOT = Path(__file__).parent.parent
HOOK = PLUGIN_ROOT / "hooks" / "advise.py"
FIXTURES = PLUGIN_ROOT / "tests" / "fixtures"


def _run(stdin_text: str):
    return subprocess.run(
        ["python3", str(HOOK)],
        input=stdin_text,
        capture_output=True,
        text=True,
        timeout=10,
    )


def _run_fixture(name: str):
    return _run((FIXTURES / name).read_text())


def _advice(result):
    """Parse additionalContext from stdout, or None if no output."""
    out = result.stdout.strip()
    if not out:
        return None
    return json.loads(out)["hookSpecificOutput"]["additionalContext"]


def test_srb_eperm_advises_unsandbox():
    result = _run_fixture("srb-eperm.json")
    assert result.returncode == 0
    advice = _advice(result)
    assert advice and "dangerouslyDisableSandbox" in advice


def test_git_write_eperm_advises_unsandbox():
    result = _run_fixture("git-write-eperm.json")
    assert result.returncode == 0
    advice = _advice(result)
    assert advice and "git" in advice.lower()


def test_ps_eperm_advises_unsandbox():
    result = _run_fixture("ps-eperm.json")
    assert result.returncode == 0
    advice = _advice(result)
    assert advice and "setuid" in advice.lower()


def test_git_push_ssh_eperm_advises_unsandbox():
    result = _run_fixture("git-push-ssh-eperm.json")
    assert result.returncode == 0
    advice = _advice(result)
    assert advice and "dangerouslyDisableSandbox" in advice
    assert "https" in advice.lower()


def test_gh_checkout_ssh_eperm_advises_unsandbox():
    result = _run_fixture("gh-checkout-ssh-eperm.json")
    assert result.returncode == 0
    advice = _advice(result)
    assert advice and "ssh-agent" in advice.lower()


def test_gh_unrelated_error_stays_silent():
    result = _run_fixture("gh-unrelated-error.json")
    assert result.returncode == 0
    assert _advice(result) is None


def test_gh_auth_login_keychain_eperm_advises_unsandbox():
    result = _run_fixture("gh-auth-login-keychain-eperm.json")
    assert result.returncode == 0
    advice = _advice(result)
    assert advice and "dangerouslyDisableSandbox" in advice
    assert "keychain" in advice.lower()


def test_srb_typecheck_error_stays_silent():
    result = _run_fixture("srb-typecheck-error.json")
    assert result.returncode == 0
    assert _advice(result) is None


def test_already_unsandboxed_stays_silent():
    result = _run_fixture("already-unsandboxed.json")
    assert result.returncode == 0
    assert _advice(result) is None


def test_malformed_stdin_fails_open():
    result = _run((FIXTURES / "malformed.txt").read_text())
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_empty_stdin_fails_open():
    result = _run("")
    assert result.returncode == 0
    assert result.stdout.strip() == ""
