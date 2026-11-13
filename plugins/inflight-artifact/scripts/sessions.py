#!/usr/bin/env python3
"""Session registry: one JSON file per session in <state-dir>/sessions/, so concurrent writers never share a file.

sessions.py list|upsert|remove [--state-dir D] [--id ID] [--field value ...]
Only the fields you pass change. `--page ""` or `--thread ""` clears an assignment.
"""
import argparse, datetime, glob, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIELDS = ("title", "page", "thread", "state", "branch", "pr", "repo", "cwd", "note", "waiting-on")


def registry(state_dir):
    d = os.path.join(os.path.expanduser(state_dir), "sessions")
    os.makedirs(d, exist_ok=True)
    legacy = os.path.join(os.path.expanduser(state_dir), "sessions.json")
    if os.path.exists(legacy):  # one-time move from the single-file registry
        for row in json.load(open(legacy)):
            path = os.path.join(d, safe(row["id"]) + ".json")
            if not os.path.exists(path): json.dump(row, open(path, "w"), indent=1)
        os.rename(legacy, legacy + ".migrated")
    return d


def safe(sid): return re.sub(r"[^A-Za-z0-9_.-]", "_", sid)


def load_all(state_dir):
    rows = []
    for f in sorted(glob.glob(os.path.join(registry(state_dir), "*.json"))):
        try: rows.append(json.load(open(f)))
        except Exception: pass
    return rows


def upsert(state_dir, sid, fields):
    path = os.path.join(registry(state_dir), safe(sid) + ".json")
    try: row = json.load(open(path))
    except Exception: row = {}
    for k, v in fields.items():
        if v is None: continue
        if v == "" and k in ("page", "thread"): row.pop(k, None)
        else: row[k] = v
    row["id"] = sid
    row["updated"] = datetime.datetime.now().isoformat(timespec="minutes")
    tmp = path + ".tmp"
    json.dump(row, open(tmp, "w"), indent=1)
    os.replace(tmp, path)
    return row


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["list", "upsert", "remove"])
    ap.add_argument("--state-dir", default=os.path.join(ROOT, "data"))
    ap.add_argument("--id")
    for k in FIELDS: ap.add_argument("--" + k)
    ap.add_argument("--tasks", help="comma-separated 8-hex task prefixes")
    a = ap.parse_args()
    if a.cmd == "list":
        for r in load_all(a.state_dir):
            print(r["id"], r.get("state"), r.get("page", "-"), r.get("thread", "-"), r.get("repo", "-"), r.get("title", ""))
    elif a.cmd == "remove":
        p = os.path.join(registry(a.state_dir), safe(a.id) + ".json")
        if os.path.exists(p): os.remove(p)
        print("removed", a.id)
    else:
        f = {k: getattr(a, k.replace("-", "_")) for k in FIELDS}
        if a.tasks is not None: f["tasks"] = [t.strip() for t in a.tasks.split(",") if t.strip()]
        upsert(a.state_dir, a.id, f)
        print("ok", a.id)
