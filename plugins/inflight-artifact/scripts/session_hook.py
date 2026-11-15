#!/usr/bin/env python3
"""SessionStart/CwdChanged/SessionEnd hook: log the session's facts so pages can place it later.

session_hook.py start|cwd|end --state-dir D   (hook input JSON on stdin)
Writes only facts (id, cwd, repo, branch, state); page and section are decided later.
Never fails the session: any error exits 0 silently.
"""
import datetime, json, os, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sessions import upsert  # noqa: E402


def git(cwd, *args):
    try: return subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, timeout=3).stdout.strip()
    except Exception: return ""


def repo_of(cwd):
    url = git(cwd, "remote", "get-url", "origin")
    if url: return os.path.basename(url.rstrip("/")).removesuffix(".git")
    common = git(cwd, "rev-parse", "--path-format=absolute", "--git-common-dir")
    return os.path.basename(os.path.dirname(common)) if common else ""


def main():
    event = sys.argv[1]
    state_dir = sys.argv[sys.argv.index("--state-dir") + 1]
    data = json.load(sys.stdin)
    if os.environ.get("CLAUDE_CODE_ENTRYPOINT") == "sdk-cli": return  # headless `claude -p`: nobody follows it on a page
    cli = data["session_id"]
    # The desktop app's own id (local_...) survives /clear and links to the session; plain CLI sessions use their own id.
    sid = os.environ.get("CLAUDE_CODE_HOST_SESSION_ID") or cli
    path = os.path.join(state_dir, "sessions", sid + ".json")
    try: row = json.load(open(path))
    except Exception: row = {}
    # A `claude` run from inside a desktop session inherits the app's id. The app's own process reports clear or
    # resume after its first startup, so a fresh startup from another CLI session under that id is a nested run.
    owner = row.get("cli")
    if event in ("start", "cwd"):
        if owner and owner != cli and (event == "cwd" or data.get("source", "startup") == "startup"): return
        # A session that moves into another repo (or out of a non-repo folder) is now about that repo.
        cwd = (data.get("new_cwd") if event == "cwd" else data.get("cwd")) or os.getcwd()
        fields = {"cwd": cwd, "repo": repo_of(cwd), "branch": git(cwd, "branch", "--show-current"), "state": "running", "cli": cli}
        if "started" not in row: fields["started"] = datetime.datetime.now().isoformat(timespec="minutes")
        upsert(state_dir, sid, fields)
    elif row.get("state") == "running" and owner in (None, cli):
        upsert(state_dir, sid, {"state": "idle"})


if __name__ == "__main__":
    try: main()
    except Exception: pass
    sys.exit(0)
