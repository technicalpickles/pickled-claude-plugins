#!/usr/bin/env python3
"""Gather raw facts for inflight pages -> <state-dir>/facts.json. Read-only.

Usage: gather.py [DAYS=14] [--config-dir D] [--state-dir D] [--github-user U]
                 [--repo-roots P1,P2 | --repo-root P ...] [--task-backend taskwarrior|none]
Settings not given on the command line come from <config-dir>/settings.json
(github_user, repo_roots, task_backend: "taskwarrior" or "none").

Credential brokers can approve every `gh` invocation separately, so this makes at most TWO gh
calls: one GraphQL request with aliased searches, and, only when a page has a `pr_paths` rule,
one request for the changed files of PRs in the repos those rules name. Changed files inside the
search make GitHub answer 502. Do not add per-PR `gh pr view` loops, and run it in the foreground.
"""
import argparse, datetime, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser()
ap.add_argument("days", nargs="?", type=int, default=14)
ap.add_argument("--config-dir", default=os.path.join(ROOT, "config"))
ap.add_argument("--state-dir", default=os.path.join(ROOT, "data"))
ap.add_argument("--github-user")
ap.add_argument("--repo-root", action="append")
ap.add_argument("--repo-roots", help="comma-separated; same as repeating --repo-root")
ap.add_argument("--task-backend", choices=["taskwarrior", "none"])
args = ap.parse_args()
try:
    SETTINGS = json.load(open(os.path.join(os.path.expanduser(args.config_dir), "settings.json")))
except Exception:
    SETTINGS = {}
USER = args.github_user or SETTINGS.get("github_user")
if not USER:
    sys.exit("no GitHub user: pass --github-user or set github_user in <config-dir>/settings.json")
ROOTS = list(args.repo_root or []) + [r.strip() for r in (args.repo_roots or "").split(",") if r.strip()]
REPO_ROOTS = [os.path.expanduser(p) for p in (ROOTS or SETTINGS.get("repo_roots", []))]
TASKS = args.task_backend or SETTINGS.get("task_backend", "taskwarrior")
STATE = os.path.expanduser(args.state_dir)
DAYS = args.days
SINCE = (datetime.date.today() - datetime.timedelta(days=DAYS)).isoformat()


def sh(cmd, cwd=None):
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd).stdout


PR = """number title isDraft mergeable updatedAt mergedAt url headRefName
  author { login } repository { nameWithOwner name }
  commits(last: 1) { nodes { commit { statusCheckRollup { contexts(first: 12) { nodes {
    ... on CheckRun { conclusion status detailsUrl }
    ... on StatusContext { state targetUrl } } } } } } }"""
Q = f"""query {{
  org: search(query: "is:pr is:open user:{USER}", type: ISSUE, first: 50) {{ nodes {{ ... on PullRequest {{ {PR} }} }} }}
  mine: search(query: "is:pr is:open author:{USER}", type: ISSUE, first: 50) {{ nodes {{ ... on PullRequest {{ {PR} }} }} }}
  merged: search(query: "is:pr is:merged author:{USER} merged:>={SINCE}", type: ISSUE, first: 50) {{ nodes {{ ... on PullRequest {{ {PR} }} }} }}
  merged_org: search(query: "is:pr is:merged user:{USER} merged:>={SINCE}", type: ISSUE, first: 50) {{ nodes {{ ... on PullRequest {{ {PR} }} }} }}
}}"""


def ci_of(node):
    ctx = []
    for c in node.get("commits", {}).get("nodes", []) or []:
        roll = (c.get("commit") or {}).get("statusCheckRollup") or {}
        ctx = (roll.get("contexts") or {}).get("nodes", []) or []
    states, urls, fail_url = [], [], None
    for c in ctx:
        url = c.get("detailsUrl") or c.get("targetUrl") or ""
        raw = (c.get("conclusion") or c.get("state") or c.get("status") or "").upper()
        if raw in ("FAILURE", "ERROR", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED"):
            states.append("failure"); fail_url = fail_url or url
        elif raw in ("SUCCESS", "NEUTRAL", "SKIPPED"):
            states.append("success")
        else:
            states.append("pending")
        if url: urls.append(url)
    if not states: return {"state": "none", "url": ""}
    st = "failure" if "failure" in states else ("pending" if "pending" in states else "success")
    return {"state": st, "url": fail_url or (urls[0] if urls else "")}


import time

data, raw = None, ""
for attempt in range(3):  # GitHub's GraphQL front end intermittently answers 502 (HTML) to heavy searches
    raw = sh(["gh", "api", "graphql", "-f", f"query={Q}"])
    try:
        data = json.loads(raw)["data"]
        break
    except Exception:
        if attempt < 2: time.sleep(5 * (attempt + 1))
if data is None:
    sys.exit("gh graphql failed (a credential broker denied it, or an API error). Raw output:\n" + raw[:600])


def path_repos():
    """Repos named next to a pr_paths rule in any page; only their PRs get changed files fetched."""
    out = set()
    pages = os.path.join(os.path.expanduser(args.config_dir), "pages")
    for f in (os.listdir(pages) if os.path.isdir(pages) else []):
        if not f.endswith(".json"): continue
        page = json.load(open(os.path.join(pages, f)))
        rules = page.get("include", {}).get("prs", []) + [t.get("match", {}) for t in page.get("threads", [])]
        out |= {r for rule in rules if rule.get("pr_paths") for r in rule.get("repos", [])}
    return out


def fetch_paths(found):
    want = [n for n in found if n["repository"]["name"] in path_repos()]
    if not want: return {}
    parts = [f'p{i}: repository(owner: "{n["repository"]["nameWithOwner"].split("/")[0]}", name: "{n["repository"]["name"]}") '
             f'{{ pullRequest(number: {n["number"]}) {{ files(first: 100) {{ nodes {{ path }} }} }} }}' for i, n in enumerate(want)]
    try: res = json.loads(sh(["gh", "api", "graphql", "-f", "query={ " + " ".join(parts) + " }"]))["data"]
    except Exception: sys.exit("gh graphql for changed files failed; rerun, or drop the pr_paths rule")
    return {(n["repository"]["nameWithOwner"], n["number"]): [f["path"] for f in res[f"p{i}"]["pullRequest"]["files"]["nodes"]]
            for i, n in enumerate(want)}




def nodes(*keys):
    seen = {}
    for k in keys:
        for n in data[k]["nodes"]:
            if n: seen[(n["repository"]["nameWithOwner"], n["number"])] = n
    return list(seen.values())


PATHS = fetch_paths(nodes("org", "mine", "merged", "merged_org"))
def paths_of(n): return PATHS.get((n["repository"]["nameWithOwner"], n["number"]), [])


prs = [{"repo": n["repository"]["nameWithOwner"], "short": n["repository"]["name"], "n": n["number"],
        "title": n["title"], "url": n["url"], "draft": n["isDraft"], "mergeable": n["mergeable"],
        "updated": n["updatedAt"][:10], "branch": n["headRefName"],
        "author": (n.get("author") or {}).get("login", ""), "ci": ci_of(n), "paths": paths_of(n)}
       for n in nodes("org", "mine")]
merged = [{"repo": n["repository"]["nameWithOwner"], "short": n["repository"]["name"], "n": n["number"],
           "title": n["title"], "url": n["url"], "date": (n.get("mergedAt") or n["updatedAt"])[:10], "paths": paths_of(n)}
          for n in nodes("merged", "merged_org")]


def js(cmd, default):
    try: return json.loads(sh(cmd))
    except Exception: return default


tasks = []
for status, extra in (() if TASKS == "none" else (("pending", []), ("completed", [f"end.after:{SINCE}"]))):
    for t in js(["task", *extra, f"status:{status}", "export"], []):
        tasks.append({"uuid": t["uuid"], "id8": t["uuid"][:8], "project": t.get("project", ""),
                      "tags": t.get("tags", []), "desc": t["description"], "status": t["status"],
                      "end": (t.get("end", "") or "")[:8], "urgency": t.get("urgency", 0),
                      "annotations": [x["description"] for x in t.get("annotations", [])]})

trees = []
for gh_dir in REPO_ROOTS:
    if not os.path.isdir(gh_dir): continue
    for r in sorted(os.listdir(gh_dir)):
        d = os.path.join(gh_dir, r)
        if not os.path.isdir(os.path.join(d, ".git")): continue
        dirty = len([l for l in sh(["git", "status", "--porcelain"], d).splitlines() if l])
        head = (sh(["git", "status", "-sb"], d).splitlines() or [""])[0]
        if dirty or "ahead" in head or "behind" in head:
            trees.append({"repo": r, "dirty": dirty, "status": head})

out = {"generated": datetime.datetime.now().isoformat(timespec="minutes"), "days": DAYS, "since": SINCE,
       "prs": prs, "merged": merged, "tasks": tasks, "trees": trees}
os.makedirs(STATE, exist_ok=True)
json.dump(out, open(os.path.join(STATE, "facts.json"), "w"), indent=1)
# ledger.json keeps every merged PR ever gathered, so "Shipped, by repo" outlives the gather window.
LEDGER = os.path.join(STATE, "ledger.json")
try: ledger = {(p["repo"], p["n"]): p for p in json.load(open(LEDGER))}
except Exception: ledger = {}
for p in merged: ledger[(p["repo"], p["n"])] = p
json.dump(sorted(ledger.values(), key=lambda p: p["date"], reverse=True), open(LEDGER, "w"), indent=1)
print(f"facts.json: {len(prs)} open PRs, {len(merged)} merged, {len(tasks)} tasks, {len(trees)} trees")
