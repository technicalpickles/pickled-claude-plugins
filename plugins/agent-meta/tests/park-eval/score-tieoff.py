"""Score a tie-off eval run. Usage: python3 -I score-tieoff.py <runs-dir>/<label>"""
import json, os, subprocess, sys


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True).stdout


def assistant_text(run):
    # All assistant text, not the final result: a user's own Stop hooks can
    # add a turn after park's closing message.
    parts = []
    for line in open(os.path.join(run, "out.jsonl")):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("type") == "assistant":
            parts += [c.get("text", "") for c in d["message"].get("content", []) if c.get("type") == "text"]
    return "\n".join(parts)


def check(run):
    repo = os.path.join(run, "repo")
    todo = open(os.path.join(repo, "TODO.md")).read().lower()
    return {
        "readme_committed": "README.md" not in git(repo, "status", "--short"),
        "retry_filed": "retry" in todo,
        "done_item_removed": "write the fetch command" not in todo,
        "worktree_removed": not os.path.exists(os.path.join(run, "wt-fetch")),
        "tally": any(w in assistant_text(run).lower() for w in ("closed", "filed", "removed", "held")),
    }


root = sys.argv[1]
want = {
    "closeout": {k: True for k in ("readme_committed", "retry_filed", "done_item_removed", "worktree_removed", "tally")},
    "continuation": {"retry_filed": False, "done_item_removed": False, "worktree_removed": False},
}
ok = True
for mode, expect in want.items():
    got = check(os.path.join(root, mode))
    for k, v in expect.items():
        mark = "PASS" if got[k] == v else "FAIL"
        ok &= got[k] == v
        print(f"{mode:13} {k:18} {mark} (got {got[k]}, want {v})")
sys.exit(0 if ok else 1)
