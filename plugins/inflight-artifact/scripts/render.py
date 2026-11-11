#!/usr/bin/env python3
"""render.py PAGE [--out FILE] [--sessions FILE]: facts.json + config/pages/PAGE.json -> HTML. Pure function, no network."""
import argparse, datetime, html, json, os, re, sys
from collections import defaultdict
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser(); ap.add_argument("page"); ap.add_argument("--out")
ap.add_argument("--config-dir", default=os.path.join(ROOT, "config")); ap.add_argument("--state-dir", default=os.path.join(ROOT, "data"))
ap.add_argument("--sessions"); ap.add_argument("--preview", action="store_true", help="mark the page as a scratch preview, not the live page")
ap.add_argument("--banner", default="", help="legacy: same as --preview, with custom bar text")
a = ap.parse_args()
CONFIG, STATE = os.path.expanduser(a.config_dir), os.path.expanduser(a.state_dir)
cfg = json.load(open(os.path.join(CONFIG, "pages", a.page + ".json")))
facts = json.load(open(os.path.join(STATE, "facts.json")))
try: sessions = json.load(open(a.sessions or os.path.join(STATE, "sessions.json")))
except Exception: sessions = []
E = lambda s: html.escape(str(s), quote=True)
EXC = re.compile(cfg["exclude"], re.I) if cfg.get("exclude") else None
excluded = lambda *parts: bool(EXC and EXC.search(" ".join(parts)))
TODAY = datetime.date.today()
threads = cfg["threads"] + [{"id": "unfiled", "title": "Unsorted", "status": "needs sorting", "match": {}}]
T = {t["id"]: t for t in threads}

def rx(p, s): return bool(p and re.search(p, s, re.I))
def in_proj(proj, lst): return any(proj == x or proj.startswith(x + ".") for x in lst)

def thread_of_pr(p):
    ref = f"{p['short']}#{p['n']}"
    for t in cfg["threads"]:
        m = t.get("match", {})
        if ref in m.get("pr_refs", []) or p["short"] in m.get("repos", []) or rx(m.get("pr_title"), p["title"]): return t["id"]
    return "unfiled"

def thread_of_task(k):
    for t in cfg["threads"]:
        m = t.get("match", {})
        if k["id8"] in m.get("task_refs", []) or in_proj(k["project"], m.get("task_projects", [])) \
           or set(k["tags"]) & set(m.get("task_tags", [])) or rx(m.get("task_desc"), k["desc"]): return t["id"]
    return "unfiled"

prs = [p for p in facts["prs"] if not excluded(p["short"], p["title"])]
merged = [p for p in facts["merged"] if not excluded(p["short"], p["title"])]
tasks = [k for k in facts["tasks"] if not excluded(k["project"], " ".join(k["tags"]), k["desc"])]
for p in prs: p["thread"] = thread_of_pr(p)
for p in merged: p["thread"] = thread_of_pr(p)
for k in tasks: k["thread"] = thread_of_task(k)
pend = [k for k in tasks if k["status"] == "pending"]
done = [k for k in tasks if k["status"] == "completed"]
task_by = {k["id8"]: k for k in facts["tasks"]}
pr_by = {f"{p['short']}#{p['n']}": p for p in facts["prs"]}
live_sessions = []
for s in sessions:
    age = (datetime.datetime.now() - datetime.datetime.fromisoformat(s.get("updated", "2000-01-01T00:00"))).days
    if s.get("page", a.page) != a.page: continue
    if s.get("state") in ("done", "failed") and age > 3: continue
    s["_stale"] = age >= 1; live_sessions.append(s)

def pr_link(p, label=None): return f'<a href="{E(p["url"])}">{E(label or p["short"] + "#" + str(p["n"]))}</a>'
def ci_chip(p):
    c = p["ci"]; txt = {"success": "CI pass", "failure": "CI fail", "pending": "CI running", "none": "no CI"}[c["state"]]
    cls = {"success": "done", "failure": "block", "pending": "wait", "none": "quiet"}[c["state"]]
    return f'<a class="chip {cls}" href="{E(c["url"])}">{txt}</a>' if c["url"] else f'<span class="chip {cls}">{txt}</span>'
def pr_chips(p):
    out = ['<span class="chip draft">draft</span>' if p["draft"] else '<span class="chip open">open</span>']
    if p["mergeable"] == "CONFLICTING": out.append('<span class="chip block">conflict</span>')
    out.append(ci_chip(p)); return " ".join(out)
def pr_row(p):
    age = (TODAY - datetime.date.fromisoformat(p["updated"])).days
    return f'<div class="row"><div class="chips">{pr_chips(p)}</div><div class="what">{pr_link(p)} {E(p["title"])}<small>{E(p["author"])} · updated {p["updated"]} ({age}d ago)</small></div></div>'

def resolved(ref):
    kind, _, v = ref.partition(":")
    if kind == "task": return task_by.get(v, {}).get("status") != "pending"
    if kind == "pr": return v not in pr_by
    return False
def ref_html(ref):
    kind, _, v = ref.partition(":")
    if kind == "pr" and v in pr_by: return pr_link(pr_by[v], v)
    return f"<code>{E(v)}</code>"
def row_live(r):
    ref = ("task:" + r["task"]) if r.get("task") else (("pr:" + r["pr"]) if r.get("pr") else None)
    return not (ref and resolved(ref))

# Needs you: page-level plus thread rows marked `you`; an item drops when every ref is resolved.
needs = [n for n in cfg.get("needs", []) if not n.get("refs") or not all(resolved(r) for r in n["refs"])]
for t in cfg["threads"]:
    for r in t.get("next", []):
        if (r.get("you") or r.get("josh")) and row_live(r) and not any(r["text"] == n["text"] for n in needs):
            needs.append({"text": r["text"], "refs": [("task:" + r["task"]) if r.get("task") else ("pr:" + r["pr"])] if (r.get("task") or r.get("pr")) else [], "thread": t["title"]})
def needs_html():
    lis = "".join(f'<li>{E(n["text"])} {" ".join(ref_html(r) for r in n.get("refs", [])[:5])}</li>' for n in needs)
    return f'<div class="needs"><h2>Needs you</h2>{"<ol>" + lis + "</ol>" if lis else "<p class=lede>Nothing is waiting on you.</p>"}</div>'

def sessions_html():
    if not live_sessions: return ""
    order = {"running": 0, "waiting": 1, "idle": 2, "done": 3, "failed": 4}
    cls = {"running": "open", "waiting": "wait", "idle": "quiet", "done": "done", "failed": "block"}
    rows = []
    for s in sorted(live_sessions, key=lambda s: order.get(s.get("state"), 9)):
        th = T.get(s.get("thread", ""), {}).get("title", s.get("thread", ""))
        bits = [x for x in (th, s.get("branch")) if x]
        if s.get("pr") and s["pr"] in pr_by: bits.append(pr_link(pr_by[s["pr"]]))
        note = E(s.get("note", "")) + (f' <strong>Waiting on: {E(s["waiting-on"])}</strong>' if s.get("waiting-on") else "") + (" <em>(may be stale)</em>" if s["_stale"] else "")
        rows.append(f'<div class="row"><div class="chips"><span class="chip {cls.get(s.get("state"), "quiet")}">{E(s.get("state", "?"))}</span></div><div class="what"><a href="claude://claude.ai/epitaxy/{E(s["id"])}">{E(s.get("title", s["id"]))}</a> <button class="copy" data-c="{E(s["id"])}">copy id</button><small>{" · ".join(b if b.startswith("<a") else E(b) for b in bits)}</small><small>{note}</small></div></div>')
    return f'<section><h2>Active sessions <span class="tag">{len(live_sessions)}</span></h2><div class="list">{"".join(rows)}</div></section>'

def counts(tid):
    ps = [p for p in prs if p["thread"] == tid]; ks = [k for k in pend if k["thread"] == tid]
    ss = [s for s in live_sessions if s.get("thread") == tid and s.get("state") in ("running", "waiting", "idle")]
    bits = [f"{len(ps)} open PR{'s' if len(ps) != 1 else ''}"]
    c = sum(1 for p in ps if p["mergeable"] == "CONFLICTING"); f = sum(1 for p in ps if p["ci"]["state"] == "failure")
    if c: bits.append(f"{c} conflict")
    if f: bits.append(f"{f} CI failing")
    bits.append(f"{len(ks)} tasks")
    if ss: bits.append(f"{len(ss)} session{'s' if len(ss) != 1 else ''}")
    return " · ".join(bits)

def card_overview(t):
    nxt = [r for r in t.get("next", []) if row_live(r)][:2]
    n = "".join(f"<li>{E(r['text'])}</li>" for r in nxt)
    return f'<div class="card"><h3>{E(t["title"])} <span class="tag">{E(t.get("status", ""))}</span></h3><p class="lede">{E(t.get("lede", ""))}</p><p class="counts">{counts(t["id"])}</p>{"<ul>" + n + "</ul>" if n else ""}</div>'

def unfiled_note():
    n = sum(1 for p in prs if p["thread"] == "unfiled"); m = sum(1 for k in pend if k["thread"] == "unfiled")
    return f'<p class="warn">{n} open PRs and {m} tasks are unsorted (no section claims them). Use inflight-artifact-design to sort them.</p>' if n else ""

overview = f'''<p class="lede big">{E(cfg.get("lede", ""))}</p>{needs_html()}{sessions_html()}
<section><h2>Sections</h2>{unfiled_note()}<div class="cards">{"".join(card_overview(t) for t in cfg["threads"] if not t.get("ignore") and (any(p["thread"] == t["id"] for p in prs) or any(k["thread"] == t["id"] for k in pend) or t.get("next")))}</div></section>'''

# What happened
ev = []
for p in merged: ev.append((p["date"], p["thread"], f'{pr_link(p)} {E(p["title"])} <a class="chip done" href="{E(p["url"])}/checks">merged · checks</a>'))
for k in done: ev.append((k["end"][:4] + "-" + k["end"][4:6] + "-" + k["end"][6:8] if len(k["end"]) >= 8 else "", k["thread"], f'<code>{k["id8"]}</code> {E(k["desc"][:110])} <span class="chip quiet">task done</span>'))
for h in cfg.get("history", []): ev.append((h["date"], h.get("thread", "unfiled"), E(h["text"])))
ev.sort(key=lambda x: x[0], reverse=True)
byday = defaultdict(list)
for d, t, h in ev: byday[d].append((t, h))
chips = "".join(f'<button class="f" data-f="{t["id"]}">{E(t["title"].split(":")[0])}</button>' for t in threads if any(x[1] == t["id"] for x in ev))
tl = "".join(f'<h3 class="day">{d or "undated"}</h3><div class="list">' + "".join(f'<div class="row ev" data-t="{t}"><div class="what">{h}<small>{E(T[t]["title"])}</small></div></div>' for t, h in rows) + "</div>" for d, rows in byday.items())
happened = f'<p class="lede">Merged PRs and finished tasks from the last {facts["days"]} days, newest first. Check marks link to the merge commit\'s checks.</p><div class="filters"><button class="f on" data-f="all">All</button>{chips}</div>{tl}'

# What's next
def next_card(t):
    ps = [p for p in prs if p["thread"] == t["id"]]; ks = sorted([k for k in pend if k["thread"] == t["id"]], key=lambda k: -k["urgency"])
    nxt = [r for r in t.get("next", []) if row_live(r)]
    h = f'<div class="card wide"><h3 id="n-{t["id"]}">{E(t["title"])} <span class="tag">{E(t.get("status", ""))}</span></h3><p class="lede">{E(t.get("lede", ""))}</p>'
    if nxt: h += "<h4>Next</h4><ul>" + "".join(f'<li>{E(r["text"])}{" <span class=chip block>you</span>" if (r.get("you") or r.get("josh")) else ""}{" <code>" + r["task"] + "</code>" if r.get("task") else ""}</li>' for r in nxt) + "</ul>"
    if ps: h += '<h4>Open PRs</h4><div class="list">' + "".join(pr_row(p) for p in sorted(ps, key=lambda p: p["updated"], reverse=True)) + "</div>"
    if ks:
        h += f'<h4>Tasks ({len(ks)})</h4><ul class="tasks">' + "".join(f'<li><code>{k["id8"]}</code> {E(k["desc"][:120])}</li>' for k in ks[:5]) + "</ul>"
        if len(ks) > 5: h += f'<details><summary>{len(ks) - 5} more</summary><ul class="tasks">' + "".join(f'<li><code>{k["id8"]}</code> {E(k["desc"][:120])}</li>' for k in ks[5:30]) + "</ul></details>"
    h += "</div>"
    if t.get("ignore"): h = h.replace('<div class="card wide">', '<details class="card wide"><summary>Collapsed: ' + E(t["title"]) + '</summary>', 1)[:-6] + "</details>"
    return h
active = [t for t in threads if t["id"] != "unfiled" and (any(p["thread"] == t["id"] for p in prs) or any(k["thread"] == t["id"] for k in pend) or t.get("next"))]
unf_prs = [p for p in prs if p["thread"] == "unfiled"]
unf = ""
if unf_prs or any(k["thread"] == "unfiled" for k in pend):
    by = defaultdict(int)
    for k in pend:
        if k["thread"] == "unfiled": by[k["project"] or "-"] += 1
    unf = f'<div class="card wide"><h3>Unsorted <span class="tag">needs sorting</span></h3>' + ('<div class="list">' + "".join(pr_row(p) for p in unf_prs) + "</div>" if unf_prs else "") + '<p class="lede">Unsorted tasks by project: ' + E(", ".join(f"{k} {v}" for k, v in sorted(by.items(), key=lambda x: -x[1])[:15])) + "</p></div>"
trees = [x for x in facts["trees"] if not excluded(x["repo"])]
tr = f'<div class="card wide"><h3>Uncommitted work and drift</h3><ul class="tasks">' + "".join(f'<li><code>{E(x["repo"])}</code> {x["dirty"]} dirty · {E(x["status"].replace("## ", ""))}</li>' for x in trees) + "</ul></div>" if trees else ""
nxt_html = "".join(next_card(t) for t in active) + unf + tr

def asset(name):
    for d in (CONFIG, os.path.join(ROOT, "assets")):
        if os.path.exists(os.path.join(d, name)): return open(os.path.join(d, name)).read()
    sys.exit("missing asset " + name)
CSS, JS = asset("page.css"), asset("page.js")
PREVIEW = a.preview or bool(a.banner)
PAGE_TITLE = f'PREVIEW: {cfg["title"]} (scratch)' if PREVIEW else cfg["title"]
banner = f'<div class="preview-bar">{E(a.banner or "PREVIEW · scratch copy · this is not the live page")}</div>' if PREVIEW else ""
out = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>{E(PAGE_TITLE)}</title><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap"><style>{CSS}</style></head><body class="{"preview" if PREVIEW else ""}">{banner}<main>
<header><div class="meta">Refreshed {facts["generated"].replace("T", " ")} · last {facts["days"]} days</div><h1>{E(PAGE_TITLE)}</h1>
<nav><a data-tab="overview" href="#overview">Overview</a><a data-tab="happened" href="#happened">What happened</a><a data-tab="next" href="#next">What's next</a></nav></header>
<div id="v-overview">{overview}</div><div id="v-happened" hidden>{happened}</div><div id="v-next" hidden>{nxt_html}</div>
<footer>Short hex codes are taskwarrior UUID prefixes. Refresh with the inflight-artifact skill; change the page with inflight-artifact-design.</footer></main><script>{JS}</script></body></html>'''
dest = a.out or os.path.join(STATE, a.page + ".html")
open(dest, "w").write(out); print(dest, len(out), "bytes;", "unsorted PRs:", len(unf_prs))
