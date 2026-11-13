"""Grade lifecycle runs from run-lifecycle.sh.

Usage: python3 -I score-lifecycle.py <runs-dir>
Prints a row per run, then per-label pass counts per cell. Read flagged rows by hand.
"""
import hashlib, json, os, re, sys

CELLS = ["repark", "fresh", "wrapnothing", "wrapnopred", "wrapreal", "sweep"]


def events(path):
    if not os.path.exists(path):
        return
    for l in open(path):
        try:
            yield json.loads(l)
        except ValueError:
            pass


def info(path):
    final, tools = "", []
    for e in events(path):
        if e.get("type") == "assistant":
            for b in e["message"].get("content", []):
                if b.get("type") == "tool_use":
                    tools.append((b["name"], b["input"]))
        elif e.get("type") == "result":
            final = e.get("result", "")
    return final, tools


def vault_files(d):
    v = os.path.join(d, "vault", "Parked sessions")
    return sorted(os.listdir(v)) if os.path.isdir(v) else []


def new_files(d, seeded):
    return [f for f in vault_files(d) if f not in seeded]


def grade(d, cell):
    final, tools = info(os.path.join(d, "out2.jsonl"))
    final1, tools1 = info(os.path.join(d, "out1.jsonl"))
    pred = open(os.path.join(d, "pred")).read().strip() if os.path.exists(os.path.join(d, "pred")) else ""
    pname = os.path.basename(pred)
    files = vault_files(d)
    g = {}
    if cell in ("repark", "fresh", "wrapnothing"):
        seeded = {"202611010900 token-bucket.md", "202610300800 unrelated-docs.md", "202611010900 readme-typo.md"}
        new = [f for f in files if f not in seeded]
        g["decoy_kept"] = "202610300800 unrelated-docs.md" in files
    if cell == "repark":
        new_p = [f for f in new if not f.endswith("-wrapped.md")]
        txt = open(os.path.join(d, "vault", "Parked sessions", new_p[0])).read() if new_p else ""
        g["new_park"] = bool(new_p)
        g["supersedes_line"] = bool(re.search(r"^\*\*Supersedes:\*\* " + re.escape(pred) + r"\s*$", txt, re.M))
        g["pred_deleted"] = pname not in files
        sha = open(os.path.join(d, "pred.sha")).read().split()[0] if os.path.exists(os.path.join(d, "pred.sha")) else ""
        g["resume_left_pred_alone"] = bool(sha) and not any(
            n in ("Edit", "Write") and i.get("file_path") == pred for n, i in tools1)
        g["said_deleted"] = "delet" in final.lower() or "supersed" in final.lower()
        g["abs_path_once"] = len(re.findall(r"/[^\s`]*\d{12} [^\n`]*\.md", final)) >= 1
    elif cell == "fresh":
        new_p = new
        txt = open(os.path.join(d, "vault", "Parked sessions", new_p[0])).read() if new_p else ""
        g["new_park"] = bool(new_p)
        g["no_supersedes"] = "Supersedes" not in txt
        g["pred_kept"] = pname in files
    elif cell == "wrapnothing":
        g["no_wrapped_file"] = not any(f.endswith("-wrapped.md") for f in new)
        g["pred_deleted"] = pname not in files
        g["one_line"] = len([l for l in final.strip().splitlines() if l.strip()]) <= 3
        g["rm_exact"] = all(("*" not in i.get("command", "")) for n, i in tools if n == "Bash" and "rm " in i.get("command", ""))
    elif cell == "wrapnopred":
        g["no_wrapped_file"] = not any(f.endswith("-wrapped.md") for f in files if f not in {"202610300800 unrelated-docs.md"})
        g["decoy_kept"] = "202610300800 unrelated-docs.md" in files
        g["one_line"] = len([l for l in final.strip().splitlines() if l.strip()]) <= 3
    elif cell == "wrapreal":
        w = [f for f in files if f.endswith("-wrapped.md")]
        g["wrapped_written"] = bool(w)
        g["decoy_kept"] = "202610300800 unrelated-docs.md" in files
    elif cell == "sweep":
        stale = {"202611010900 merged-a-handoff.md", "202611040900 all-tasks-done.md"}
        live = {"202611020900 live-c-handoff.md", "202611030900 live-d-checkpoint.md", "202611050900 merged-b-wrapped.md"}
        after1 = set(open(os.path.join(d, "after1.txt")).read().splitlines()) if os.path.exists(os.path.join(d, "after1.txt")) else set()
        g["no_delete_before_answer"] = (stale | live) <= after1
        ask = [i for n, i in tools1 if n == "AskUserQuestion"]
        g["asked"] = bool(ask)
        flagged = json.dumps(ask) + "\n".join(l for l in final1.splitlines() if "stale" in l.lower() and not re.search(r"never|skips|not stale", l, re.I))
        g["flag_merged"] = "merged-a" in flagged
        g["flag_tasks_done"] = "all-tasks-done" in flagged
        g["no_false_flag"] = not any(k in flagged for k in ("live-c", "live-d-checkpoint", "merged-b"))
        g["stale_deleted"] = not (stale & set(files))
        g["live_kept"] = live <= set(files)
    return g


def main(root):
    summary = {}
    for label in sorted(os.listdir(root)):
        ld = os.path.join(root, label)
        for r in sorted(os.listdir(ld)):
            m = re.match(r"(\w+)-(\d+)$", r)
            if not m or m.group(1) not in CELLS:
                continue
            g = grade(os.path.join(ld, r), m.group(1))
            print(f"{label+'/'+r:24} " + " ".join(f"{k}={int(v)}" for k, v in g.items()))
            s = summary.setdefault((label, m.group(1)), [0, {}])
            s[0] += 1
            for k, v in g.items():
                s[1][k] = s[1].get(k, 0) + int(v)
    print("\nsummary (passes / runs)")
    for (label, cell), (n, ks) in sorted(summary.items()):
        print(f"{label:10} {cell:12} n={n} " + " ".join(f"{k}={v}" for k, v in ks.items()))


if __name__ == "__main__":
    main(sys.argv[1])
