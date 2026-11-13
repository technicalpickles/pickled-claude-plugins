"""Score park files from a park-eval run directory.

Usage: python3 -I score.py <runs-dir>

Layout: <runs-dir>/<label>/<scenario>-<rep>/{out.jsonl,work/,vault/}
Prints one row per run and a per-label, per-scenario summary.
"""
import json, os, re, statistics as st, sys

STOP = set("the and for that this with from into then when will have what which their there about after before first next also only each over under been being does done not are was but you your can should would could them they its our".split())

KEEP = {  # facts a resumer needs, by scenario
    "ratelimit": ["monotonic", "make test", "push", "API key", "server.py", "token bucket"],
    "csvexport": ["utf-8-sig", "git:pull-request"],
}


def words(s):
    return {w for w in re.findall(r"[a-z0-9_./-]{4,}", s.lower()) if w not in STOP}


def find_park(run):
    cands = []
    for root in (os.path.join(run, "vault"), os.path.join(run, "work", ".parkinglot")):
        for dp, _, fs in os.walk(root):
            for f in fs:
                if re.match(r"\d{12} .*\.md$", f):
                    cands.append(os.path.join(dp, f))
    return sorted(cands)[-1] if cands else None


def final_text(run):
    out = ""
    p = os.path.join(run, "out.jsonl")
    if os.path.exists(p):
        for l in open(p):
            try:
                d = json.loads(l)
            except ValueError:
                continue
            if d.get("type") == "result":
                out = d.get("result", "")
    return out


def fences(text):
    return re.findall(r"```[a-z]*\n(.*?)```", text, re.S)


def score(run, scenario):
    path = find_park(run)
    if not path:
        return None
    t = open(path).read()
    r = {"path": path, "words": len(t.split())}
    r["heading_ok"] = t.startswith("# Parked:")
    r["session_uuid"] = bool(re.search(r"\*\*Session:\*\*\s*[0-9a-f]{8}-[0-9a-f]{4}-", t))
    m = re.search(r"## Resume Prompt\n+```[a-z]*\n(.*?)```", t, re.S)
    prompt = m.group(1) if m else ""
    lines = [l for l in prompt.splitlines() if l.strip()]
    ul = next((l for l in lines if l.strip().startswith("unpark")), "")
    r["unpark_abs"] = bool(re.match(r'unpark\s+"?/', ul.strip()))
    body = " ".join(l for l in lines if not l.strip().startswith("unpark"))
    sents = [s for s in re.split(r"(?<=[.!?])\s+", body) if len(s.split()) >= 4]
    rest = t.replace(m.group(0), "") if m else t
    rw = words(rest)
    novel = [s for s in sents if len(words(s) & rw) / max(1, len(words(s))) < 0.5]
    r["prompt_words"] = len(body.split())
    r["prompt_sents"] = len(sents)
    r["prompt_restated"] = len(sents) - len(novel)
    r["dup_claude_md"] = "conventional" in prompt.lower()
    rf = re.search(r"## Relevant [Ff]iles\n(.*?)(?=\n## |\Z)", t, re.S)
    r["read_files"] = len(re.findall(r"\((read|referenced)\)", rf.group(1))) if rf else 0
    keep = KEEP[scenario]
    r["facts_kept"] = sum(1 for k in keep if k.lower() in t.lower())
    r["facts_total"] = len(keep)
    ft = final_text(run)
    fb = fences(ft)
    r["after_path_fenced"] = any(path in b for b in fb)
    r["after_unpark_fenced"] = any(re.search(r"unpark\s+\"?" + re.escape(path), b) for b in fb)
    r["after_blockquote"] = bool(re.search(r"^>\s*unpark", ft, re.M))
    return r


def main(root):
    rows = []
    for label in sorted(os.listdir(root)):
        ld = os.path.join(root, label)
        if not os.path.isdir(ld):
            continue
        for run in sorted(os.listdir(ld)):
            m = re.match(r"(ratelimit|csvexport)-(\d+)$", run)
            if not m:
                continue
            s = score(os.path.join(ld, run), m.group(1))
            rows.append((label, m.group(1), run, s))
    print(f"{'run':28} {'words':>5} {'pW':>4} {'pS':>3} {'rest':>4} {'abs':>3} {'dup':>3} {'rd':>2} {'facts':>5} {'aft-path':>8} {'aft-cmd':>7} {'bq':>2}")
    for label, sc, run, s in rows:
        if not s:
            print(f"{label+'/'+run:28} NO PARK FILE")
            continue
        print(f"{label+'/'+run:28} {s['words']:5} {s['prompt_words']:4} {s['prompt_sents']:3} {s['prompt_restated']:4} "
              f"{int(s['unpark_abs']):3} {int(s['dup_claude_md']):3} {s['read_files']:2} {s['facts_kept']}/{s['facts_total']:<3} "
              f"{int(s['after_path_fenced']):8} {int(s['after_unpark_fenced']):7} {int(s['after_blockquote']):2}")
    print("\nsummary (median over reps; n = parks found / runs)")
    keys = sorted({(l, sc) for l, sc, _, _ in rows})
    for l, sc in keys:
        ss = [s for ll, ssc, _, s in rows if ll == l and ssc == sc]
        ok = [s for s in ss if s]
        if not ok:
            print(f"{l:10} {sc:10} n=0/{len(ss)}")
            continue
        med = lambda k: st.median(x[k] for x in ok)
        cnt = lambda k: sum(1 for x in ok if x[k])
        print(f"{l:10} {sc:10} n={len(ok)}/{len(ss)} words={med('words'):.0f} promptW={med('prompt_words'):.0f} "
              f"promptS={med('prompt_sents'):.0f} restated={med('prompt_restated'):.0f} abs={cnt('unpark_abs')} "
              f"dup={cnt('dup_claude_md')} readFiles={med('read_files'):.0f} facts={sum(x['facts_kept'] for x in ok)}/{sum(x['facts_total'] for x in ok)} "
              f"afterPath={cnt('after_path_fenced')} afterCmd={cnt('after_unpark_fenced')} bq={cnt('after_blockquote')}")


if __name__ == "__main__":
    main(sys.argv[1])
