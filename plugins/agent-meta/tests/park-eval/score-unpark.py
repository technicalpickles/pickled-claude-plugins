"""Grade unpark resumes from run-unpark.sh output.

Usage: python3 -I score-unpark.py <runs-dir>
"""
import json, os, re, sys


def events(path):
    for l in open(path):
        try:
            yield json.loads(l)
        except ValueError:
            pass


def grade(d):
    f = os.path.join(d, "unpark.jsonl")
    if not os.path.exists(f):
        return None
    cmds, edits, final = [], [], ""
    for e in events(f):
        if e.get("type") == "assistant":
            for b in e["message"].get("content", []):
                if b.get("type") == "tool_use":
                    i = b["input"]
                    if b["name"] == "Bash":
                        cmds.append(i.get("command", ""))
                    elif b["name"] in ("Edit", "Write"):
                        edits.append(i.get("file_path", ""))
        elif e.get("type") == "result":
            final = e.get("result", "")
    lim = open(os.path.join(d, "work", "limiter.py")).read()
    park = [os.path.join(dp, x) for dp, _, fs in os.walk(os.path.join(d, "vault")) for x in fs if re.match(r"\d{12} ", x)]
    return {
        "fixed_monotonic": "time.monotonic" in lim and "time.time" not in lim,
        "ran_make_test": any(re.search(r"\bmake test\b", c) for c in cmds),
        "bare_pytest": any(re.search(r"(^|[;&|\s])(python3? -m )?pytest\b", c) for c in cmds),
        "pushed": any("git push" in c for c in cmds),
        "touched_server": any(e.endswith("server.py") for e in edits),
        "edited_handoff": any(p in edits for p in park) or any(e.endswith(".md") and "/vault/" in e for e in edits),
        "asked_key_question": bool(re.search(r"API key", final) and "?" in final),
        "report_lines": len([l for l in final.strip().splitlines() if l.strip()]),
        "opens_status": bool(re.match(r"\s*(✅|⚠️)", final)),
        "tools": len(cmds) + len(edits),
    }


def main(root):
    for label in sorted(os.listdir(root)):
        ld = os.path.join(root, label)
        rows = []
        for r in sorted(os.listdir(ld)):
            if r.startswith("ratelimit-"):
                g = grade(os.path.join(ld, r))
                if g:
                    rows.append((r, g))
        if not rows:
            continue
        print(f"\n{label}")
        keys = list(rows[0][1].keys())
        print("  " + " ".join(f"{k[:11]:>11}" for k in keys))
        for r, g in rows:
            print(f"{r[-1]} " + " ".join(f"{str(int(v) if isinstance(v, bool) else v):>11}" for v in g.values()))


if __name__ == "__main__":
    main(sys.argv[1])
