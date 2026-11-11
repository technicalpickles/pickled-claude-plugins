#!/usr/bin/env python3
"""Session registry. sessions.py list|upsert|remove [--file F]. Default file: data/sessions.json."""
import argparse, json, os, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser()
ap.add_argument("cmd", choices=["list", "upsert", "remove"])
ap.add_argument("--state-dir", default=os.path.join(ROOT, "data"))
ap.add_argument("--file")
ap.add_argument("--id")
for k in ("title", "page", "thread", "state", "branch", "pr", "note", "waiting-on"):
    ap.add_argument("--" + k)
a = ap.parse_args()
a.file = a.file or os.path.join(os.path.expanduser(a.state_dir), "sessions.json")
try: rows = json.load(open(a.file))
except Exception: rows = []
if a.cmd == "list":
    for r in rows: print(r["id"], r.get("state"), r.get("page"), r.get("thread"), r.get("title"))
else:
    rows = [r for r in rows if r["id"] != a.id]
    if a.cmd == "upsert":
        old = next((r for r in json.load(open(a.file)) if r["id"] == a.id), {}) if os.path.exists(a.file) else {}
        for k in ("title", "page", "thread", "state", "branch", "pr", "note", "waiting-on"):
            v = getattr(a, k.replace("-", "_"))
            if v is not None: old[k] = v
        old["id"] = a.id; old["updated"] = datetime.datetime.now().isoformat(timespec="minutes")
        rows.append(old)
    json.dump(rows, open(a.file, "w"), indent=1)
    print("ok", len(rows), "sessions")
