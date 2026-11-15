#!/usr/bin/env python3
"""render.py PAGE [--out FILE] [--preview]: facts.json + config/pages/PAGE.json -> HTML. Pure function, no network.

Config prose (ledes, row text, needs, history, fragment files) is trusted inline HTML written by the design skill.
Text that comes from facts (PR titles, task descriptions) is escaped.
"""
import argparse, datetime, html, json, os, re, sys
from collections import defaultdict
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser(); ap.add_argument("page"); ap.add_argument("--out")
ap.add_argument("--config-dir", default=os.path.join(ROOT, "config")); ap.add_argument("--state-dir", default=os.path.join(ROOT, "data"))
ap.add_argument("--preview", action="store_true", help="mark the page as a scratch preview, not the live page")
ap.add_argument("--banner", default="", help="legacy: same as --preview, with custom bar text")
a = ap.parse_args()
CONFIG, STATE = os.path.expanduser(a.config_dir), os.path.expanduser(a.state_dir)
PDIR = os.path.join(CONFIG, "pages", a.page)
cfg = json.load(open(PDIR + ".json"))
facts = json.load(open(os.path.join(STATE, "facts.json")))
def load(path, default):
    try: return json.load(open(path))
    except Exception: return default
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sessions import load_all
sessions = load_all(STATE)
ledger = load(os.path.join(STATE, "ledger.json"), [])
def frag(name):
    p = os.path.join(PDIR, name)
    if not os.path.exists(p): sys.exit("missing fragment " + p)
    return open(p).read()

E = lambda s: html.escape(str(s), quote=True)
EXC = re.compile(cfg["exclude"], re.I) if cfg.get("exclude") else None
excluded = lambda *parts: bool(EXC and EXC.search(" ".join(parts)))
TODAY = datetime.date.today()
ROWS = ("next", "then", "parked")
threads = cfg["threads"] + [{"id": "unfiled", "title": "Unsorted", "status": "needs sorting", "match": {}}]
T = {t["id"]: t for t in threads}
TONE = {"crit": "block", "warn": "wait", "ok": "done", "info": "open"}

def rx(p, s): return bool(p and re.search(p, s, re.I))
def in_proj(proj, lst): return any(proj == x or proj.startswith(x + ".") for x in lst)
def is_you(r): return bool(r.get("you") or r.get("josh"))

# Page scope: within a rule every key must hold; any rule admits the item. No rules means everything is in scope.
INC = cfg.get("include", {})
def rule_pr(r, p):
    return (not r.get("repos") or p["short"] in r["repos"]) and (not r.get("pr_title") or rx(r["pr_title"], p["title"])) \
        and (not r.get("pr_paths") or any(rx(r["pr_paths"], f) for f in p.get("paths", [])))
def rule_task(r, k):
    return (not r.get("task_projects") or in_proj(k["project"], r["task_projects"])) \
        and (not r.get("task_tags") or bool(set(k["tags"]) & set(r["task_tags"]))) and (not r.get("task_desc") or rx(r["task_desc"], k["desc"]))

# A row that names a task or PR claims it for its thread, ahead of any match rule.
CLAIM_T, CLAIM_P = {}, {}
for t in cfg["threads"]:
    for key in ROWS:
        for r in t.get(key, []):
            if r.get("task"): CLAIM_T.setdefault(r["task"], t["id"])
            if r.get("pr"): CLAIM_P.setdefault(r["pr"], t["id"])

# A task a fragment shows (a tab or overview block) is on the page, so it is not unsorted.
FRAGS = {f: frag(f) for f in cfg.get("overview_html", []) + [t["file"] for t in cfg.get("tabs", [])]}
FRAG_T = {r for text in FRAGS.values() for r in re.findall(r'data-t="([0-9a-f]{8})"', text)}
T["fragment"] = {"id": "fragment", "title": "Elsewhere on this page"}

def ref_of(p): return f"{p['short']}#{p['n']}"
def pr_in(p): return not excluded(p["short"], p["title"]) and (ref_of(p) in CLAIM_P or "prs" not in INC or any(rule_pr(r, p) for r in INC["prs"]))
def task_in(k): return k["id8"] in CLAIM_T or k["id8"] in FRAG_T or (not excluded(k["project"], " ".join(k["tags"]), k["desc"]) and ("tasks" not in INC or any(rule_task(r, k) for r in INC["tasks"])))

def thread_of_pr(p):
    ref = ref_of(p)
    if ref in CLAIM_P: return CLAIM_P[ref]
    for t in cfg["threads"]:
        m = t.get("match", {})
        if ref in m.get("pr_refs", []) or p["short"] in m.get("repos", []) or rx(m.get("pr_title"), p["title"]) \
           or any(rx(m.get("pr_paths"), f) for f in p.get("paths", [])): return t["id"]
    return "unfiled"

def thread_of_task(k):
    if k["id8"] in CLAIM_T: return CLAIM_T[k["id8"]]
    if k["id8"] in FRAG_T: return "fragment"
    for t in cfg["threads"]:
        m = t.get("match", {})
        if k["id8"] in m.get("task_refs", []) or in_proj(k["project"], m.get("task_projects", [])) \
           or set(k["tags"]) & set(m.get("task_tags", [])) or rx(m.get("task_desc"), k["desc"]): return t["id"]
    return "unfiled"

seen_merged = {(p["repo"], p["n"]) for p in facts["merged"]}
all_merged = facts["merged"] + [p for p in ledger if (p["repo"], p["n"]) not in seen_merged]
prs = [p for p in facts["prs"] if pr_in(p)]
merged = [p for p in all_merged if pr_in(p)]
tasks = [k for k in facts["tasks"] if task_in(k)]
for p in prs + merged: p["thread"] = thread_of_pr(p)
for k in tasks: k["thread"] = thread_of_task(k)
pend = [k for k in tasks if k["status"] == "pending"]
done = [k for k in tasks if k["status"] == "completed"]
task_by = {k["id8"]: k for k in facts["tasks"]}
pr_by = {ref_of(p): p for p in facts["prs"]}
# Sessions are logged with facts only; a page shows one it was assigned, or one its scope admits:
# by a task a row here claims, or by repo where the scope is a whole repo (a path or title rule needs a person to decide).
def session_in(s):
    if s.get("page"): return s["page"] == a.page
    repo = s.get("repo", "")
    return any(t in CLAIM_T for t in s.get("tasks", [])) or bool(repo and not excluded(repo) and (
        "prs" not in INC or any(repo in r.get("repos", []) and not r.get("pr_paths") and not r.get("pr_title") for r in INC["prs"])))
def thread_of_session(s):
    if s.get("thread"): return s["thread"]
    claimed = [CLAIM_T[t] for t in s.get("tasks", []) if t in CLAIM_T]
    if claimed: return claimed[0]
    return next((t["id"] for t in cfg["threads"] if s.get("repo") in t.get("match", {}).get("repos", [])), "unfiled")
live_sessions = []
for s in sessions:
    age = (datetime.datetime.now() - datetime.datetime.fromisoformat(s.get("updated", "2000-01-01T00:00").replace("Z", ""))).days
    if not session_in(s): continue
    if (s.get("state") in ("done", "failed") and age > 3) or age > 7: continue
    s["thread"] = thread_of_session(s); s["_stale"] = age >= 1; live_sessions.append(s)
in_session = {t for s in live_sessions if s.get("state") in ("running", "waiting", "idle") for t in s.get("tasks", [])}

def pr_link(p, label=None): return f'<a href="{E(p["url"])}">{E(label or ref_of(p))}</a>'
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
    if kind == "pr" and v in pr_by: return pr_link(pr_by[v], v) + " " + ci_chip(pr_by[v])
    if kind == "task": return f'<code class="task" tabindex="0" role="button" data-t="{E(v)}">{E(v)}</code>'
    return f"<code>{E(v)}</code>"
def row_live(r):
    ref = ("task:" + r["task"]) if r.get("task") else (("pr:" + r["pr"]) if r.get("pr") else None)
    return not (ref and resolved(ref))
def badge(t): return ' <span class="chip open live-badge">in session</span>' if t in in_session else ""

def row_html(r, where=""):
    chips = f'<span class="chip {TONE.get(r.get("tone"), "quiet")}">{E(r["kind"])}</span> ' if r.get("kind") else ""
    tail = (' <span class="chip block">you</span>' if is_you(r) else "") + (f" <small>{E(where)}</small>" if where else "")
    if r.get("pr"): tail += " " + ref_html("pr:" + r["pr"])
    if r.get("task"):
        return f'<li class="task" tabindex="0" role="button" data-t="{E(r["task"])}"><div>{chips}{r.get("text", "")} <code>{E(r["task"])}</code>{tail}{badge(r["task"])}</div></li>'
    return f'<li><div>{chips}{r.get("text", "")}{tail}</div></li>'
def task_li(k):
    return f'<li class="task" tabindex="0" role="button" data-t="{k["id8"]}"><div><code>{k["id8"]}</code> {E(k["desc"][:120])}{badge(k["id8"])}</div></li>'

# Needs you: page-level items plus thread rows marked `you`; an item drops when every ref is resolved.
needs = [f'<li><div>{n["text"]} {" ".join(ref_html(r) for r in n.get("refs", [])[:5])}</div></li>'
         for n in cfg.get("needs", []) if not n.get("refs") or not all(resolved(r) for r in n["refs"])]
needs += [row_html(r, t["title"]) for t in cfg["threads"] for key in ROWS for r in t.get(key, [])
          if is_you(r) and row_live(r) and not any(r.get("text", "") == n.get("text") for n in cfg.get("needs", []))]
# A task carrying one of the page's needs_tags is on you too, so tagging it is enough to list it here.
you_rows = {r["task"] for t in cfg["threads"] for key in ROWS for r in t.get(key, []) if is_you(r) and r.get("task")}
needs += [f'<li class="task" tabindex="0" role="button" data-t="{k["id8"]}"><div>{E(k["desc"][:160])} <code>{k["id8"]}</code> <span class="chip block">you</span> <small>{E(T.get(k["thread"], {}).get("title", "Unsorted"))}</small>{badge(k["id8"])}</div></li>'
          for k in sorted(pend, key=lambda k: -k["urgency"]) if set(k["tags"]) & set(cfg.get("needs_tags", [])) and k["id8"] not in you_rows]
def needs_html():
    return f'<div class="needs"><h2>Needs you</h2>{"<ol>" + "".join(needs) + "</ol>" if needs else "<p class=lede>Nothing is waiting on you.</p>"}</div>'

def upnext_html():
    now = [t for t in cfg["threads"] if t.get("status") == "now"]
    body = "".join(f'<h3>{E(t["title"])}</h3><ul class="rows">{"".join(row_html(r) for r in t.get("next", []) if row_live(r) and not is_you(r))}</ul>' for t in now)
    return f'<section><h2>Up next <small>the next steps on sections marked now</small></h2>{body}</section>' if now else ""

def sessions_html():
    if not live_sessions: return ""
    order = {"waiting": 0, "running": 1, "idle": 2, "failed": 3, "done": 4}
    cls = {"running": "open", "waiting": "wait", "idle": "quiet", "done": "done", "failed": "block"}
    rows = []
    for s in sorted(live_sessions, key=lambda s: order.get(s.get("state"), 9)):
        th = T.get(s.get("thread", ""), {}).get("title", s.get("thread", ""))
        bits = [E(x) for x in (th, s.get("repo"), s.get("branch")) if x]
        if s.get("pr") and s["pr"] in pr_by: bits.append(pr_link(pr_by[s["pr"]]))
        bits += [f'<a href="#" class="task" data-t="{E(t)}">task {E(t)}</a>' for t in s.get("tasks", [])]
        note = E(s.get("note", "")) + (f' <strong>Waiting on: {E(s["waiting-on"])}</strong>' if s.get("waiting-on") else "") + (" <em>(may be stale)</em>" if s["_stale"] else "")
        title = E(s.get("title") or " · ".join(x for x in (s.get("repo"), s.get("branch")) if x) or s["id"])
        name = f'<a href="claude://claude.ai/epitaxy/{E(s["id"])}">{title}</a>' if s["id"].startswith("local_") else title
        rows.append(f'<div class="row"><div class="chips"><span class="chip {cls.get(s.get("state"), "quiet")}">{E(s.get("state", "?"))}</span></div><div class="what">{name} <button class="copy" data-c="{E(s["id"])}">copy id</button><small>{" · ".join(bits)}</small><small>{note}</small></div></div>')
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
def lede_of(t): return t.get("lede", t.get("goal", ""))

def card_overview(t):
    nxt = [r for r in t.get("next", []) if row_live(r)][:2]
    n = "".join(f"<li>{r.get('text', '')}</li>" for r in nxt)
    return f'<div class="card"><h3>{E(t["title"])} <span class="tag">{E(t.get("status", ""))}</span></h3><p class="lede">{lede_of(t)}</p><p class="counts">{counts(t["id"])}</p>{"<ul>" + n + "</ul>" if n else ""}</div>'

unf_prs = [p for p in prs if p["thread"] == "unfiled"]
unf_tasks = [k for k in pend if k["thread"] == "unfiled"]
def unfiled_note():
    n, m = len(unf_prs), len(unf_tasks)
    return f'<p class="warn">{n} open PRs and {m} tasks are unsorted (no section claims them). Use inflight-artifact-design to sort them.</p>' if n or m else ""
def has_work(t): return any(p["thread"] == t["id"] for p in prs) or any(k["thread"] == t["id"] for k in pend) or any(t.get(key) for key in ROWS)

overview = f'''<p class="lede big">{cfg.get("lede", "")}</p>{"".join(FRAGS[f] for f in cfg.get("overview_html", []))}{needs_html()}{upnext_html()}{sessions_html()}
<section><h2>Sections</h2>{unfiled_note()}<div class="cards">{"".join(card_overview(t) for t in cfg["threads"] if not t.get("ignore") and has_work(t))}</div></section>'''

# What happened. Filter groups come from `filters` (by repo or task project) or, without them, from the sections.
FILTERS = cfg.get("filters")
def group_of(thread, repo=None, project=None):
    if not FILTERS: return thread
    for f in FILTERS:
        if (repo and repo in f.get("repos", [])) or (project and in_proj(project, f.get("task_projects", []))): return f["id"]
    return ""
def group_label(g): return next((f["label"] for f in FILTERS if f["id"] == g), g) if FILTERS else T.get(g, {}).get("title", g)
ev = []
if cfg.get("auto_events", True):
    for p in merged:
        if p.get("date", "") >= facts["since"]:
            ev.append((p["date"], group_of(p["thread"], repo=p["short"]), f'{pr_link(p)} {E(p["title"])} <a class="chip done" href="{E(p["url"])}/checks">merged · checks</a>', T[p["thread"]]["title"]))
    for k in done:
        d = k["end"][:4] + "-" + k["end"][4:6] + "-" + k["end"][6:8] if len(k["end"]) >= 8 else ""
        ev.append((d, group_of(k["thread"], project=k["project"]), f'<code>{k["id8"]}</code> {E(k["desc"][:110])} <span class="chip quiet">task done</span>', T[k["thread"]]["title"]))
for h in cfg.get("history", []):
    g = h.get("group") or group_of(h.get("thread", "unfiled"))
    ev.append((h["date"], g, h["text"], T[h["thread"]]["title"] if h.get("thread") in T else group_label(g)))
ev.sort(key=lambda x: x[0], reverse=True)
byday = defaultdict(list)
for d, g, h, label in ev: byday[d].append((g, h, label))
groups = [(f["id"], f["label"]) for f in FILTERS] if FILTERS else [(t["id"], t["title"].split(":")[0]) for t in threads]
chips = "".join(f'<button class="f" data-f="{E(g)}">{E(l)}</button>' for g, l in groups if any(x[1] == g for x in ev))
tl = "".join(f'<h3 class="day">{d or "undated"}</h3><div class="list">' + "".join(f'<div class="row ev" data-g="{E(g)}"><div class="what">{h}<small>{E(label)}</small></div></div>' for g, h, label in rows) + "</div>" for d, rows in byday.items())
shipped = defaultdict(list)
for p in sorted(merged, key=lambda p: p.get("date", ""), reverse=True): shipped[p["short"]].append(p)
ship_html = "".join(f'<div class="card"><h3>{E(repo)}</h3><ul>' + "".join(f'<li>{pr_link(p)} merged {p.get("date", "")[5:]}: {E(p["title"])} <a class="chip done" href="{E(p["url"])}/checks">checks</a></li>' for p in ps) + "</ul></div>" for repo, ps in sorted(shipped.items(), key=lambda x: -len(x[1])))
archive = f'<details><summary>Earlier, written by hand</summary>{frag(cfg["shipped_archive"])}</details>' if cfg.get("shipped_archive") else ""
happened = (f'<p class="lede">{cfg.get("happened_lede", "Merged PRs, finished tasks and notes, newest first. Check marks link to the merge commit&#39;s checks.")}</p>'
            f'<div class="filters"><button class="f on" data-f="all">All</button>{chips}</div>{tl}'
            f'<section><h2>Shipped, by repo</h2><div class="cards">{ship_html}</div>{archive}</section>')

# What's next
def next_card(t):
    ps = [p for p in prs if p["thread"] == t["id"]]
    rowed = {r["task"] for key in ROWS for r in t.get(key, []) if r.get("task")}
    ks = sorted([k for k in pend if k["thread"] == t["id"] and k["id8"] not in rowed], key=lambda k: -k["urgency"])
    lists = {key: [r for r in t.get(key, []) if row_live(r)] for key in ROWS}
    h = f'<div class="card wide"><h3 id="n-{t["id"]}">{E(t["title"])} <span class="tag">{E(t.get("status", ""))}</span></h3><p class="lede">{lede_of(t)}</p>'
    for key, label in (("next", "Next"), ("then", "Then")):
        if lists[key]: h += f'<h4>{label}</h4><ul class="rows">' + "".join(row_html(r) for r in lists[key]) + "</ul>"
    if ps: h += '<h4>Open PRs</h4><div class="list">' + "".join(pr_row(p) for p in sorted(ps, key=lambda p: p["updated"], reverse=True)) + "</div>"
    if ks:
        h += f'<h4>Tasks ({len(ks)})</h4><ul class="tasks">' + "".join(task_li(k) for k in ks[:5]) + "</ul>"
        if len(ks) > 5: h += f'<details><summary>{len(ks) - 5} more</summary><ul class="tasks">' + "".join(task_li(k) for k in ks[5:30]) + "</ul></details>"
    if lists["parked"]: h += f'<details><summary>Parked ({len(lists["parked"])})</summary><ul class="rows">' + "".join(row_html(r) for r in lists["parked"]) + "</ul></details>"
    h += "</div>"
    if t.get("ignore"): h = h.replace('<div class="card wide">', '<details class="card wide"><summary>Collapsed: ' + E(t["title"]) + '</summary>', 1)[:-6] + "</details>"
    return h
active = [t for t in threads if t["id"] != "unfiled" and has_work(t)]
unf = ""
if unf_prs or unf_tasks:
    by = defaultdict(int)
    for k in unf_tasks: by[k["project"] or "-"] += 1
    unf = f'<div class="card wide"><h3>Unsorted <span class="tag">needs sorting</span></h3>' + ('<div class="list">' + "".join(pr_row(p) for p in unf_prs) + "</div>" if unf_prs else "") + '<p class="lede">Unsorted tasks by project: ' + E(", ".join(f"{k} {v}" for k, v in sorted(by.items(), key=lambda x: -x[1])[:15])) + "</p></div>"
trees = [x for x in facts["trees"] if not excluded(x["repo"]) and ("prs" not in INC or any(x["repo"] in r.get("repos", []) for r in INC["prs"]))]
tr = f'<div class="card wide"><h3>Uncommitted work and drift</h3><ul class="tasks">' + "".join(f'<li><code>{E(x["repo"])}</code> {x["dirty"]} dirty · {E(x["status"].replace("## ", ""))}</li>' for x in trees) + "</ul></div>" if trees else ""
nxt_html = (f'<p class="lede">{cfg["next_lede"]}</p>' if cfg.get("next_lede") else "") +"".join(next_card(t) for t in active) + unf + tr

def asset(name):
    for d in (CONFIG, os.path.join(ROOT, "assets")):
        if os.path.exists(os.path.join(d, name)): return open(os.path.join(d, name)).read()
    sys.exit("missing asset " + name)
CSS, JS = asset("page.css") + (frag(cfg["css"]) if cfg.get("css") else ""), asset("page.js")
PREVIEW = a.preview or bool(a.banner)
PAGE_TITLE = f'PREVIEW: {cfg["title"]} (scratch)' if PREVIEW else cfg["title"]
banner = f'<div class="preview-bar">{E(a.banner or "PREVIEW · scratch copy · this is not the live page")}</div>' if PREVIEW else ""
views = [("overview", "Overview", overview), ("happened", "What happened", happened), ("next", "What's next", nxt_html)] \
    + [(t["id"], t["title"], FRAGS[t["file"]]) for t in cfg.get("tabs", [])]
nav = "".join(f'<a data-tab="{E(v)}" href="#{E(v)}">{E(title)}</a>' for v, title, _ in views)
body = "".join(f'<div id="v-{E(v)}"{" hidden" if i else ""}>{b}</div>' for i, (v, _, b) in enumerate(views))

# Task popups: embed only the pending tasks this page shows. Report config rows, needs refs and fragment blocks that
# point at finished tasks; a session's linked tasks come from the registry, not config, so there is nothing to drop.
done = lambda r: task_by.get(r, {}).get("status") != "pending"
refs = sorted(r for r in set(re.findall(r'data-t="([0-9a-f]{8})"', body)) if not done(r))
config_refs = set(CLAIM_T) | FRAG_T | {ref.partition(":")[2] for n in cfg.get("needs", []) for ref in n.get("refs", []) if ref.startswith("task:")}
gone = sorted(r for r in config_refs if done(r))
popup = [{"uuid": task_by[r].get("uuid", r), "description": task_by[r]["desc"], "project": task_by[r]["project"], "tags": task_by[r]["tags"],
          "annotations": task_by[r].get("annotations", [])} for r in refs]
sess_js = [{k: s.get(k) for k in ("id", "title", "state", "note", "tasks")} for s in live_sessions if s.get("tasks")]
repos = sorted({p["repo"] for p in facts["prs"] + all_merged})
blob = lambda x: json.dumps(x).replace("</", "<\\/")
data = f'<script id="inflight-data" type="application/json">{blob({"tasks": popup, "sessions": sess_js, "repos": repos})}</script>'

out = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>{E(PAGE_TITLE)}</title><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap"><style>{CSS}</style></head><body class="{"preview" if PREVIEW else ""}">{banner}<main>
<header><div class="meta">Refreshed {facts["generated"].replace("T", " ")} · last {facts["days"]} days</div><h1>{E(PAGE_TITLE)}</h1>{f"<p>{cfg['intro']}</p>" if cfg.get("intro") else ""}
<nav>{nav}</nav></header>
{body}
<footer>Short hex codes are taskwarrior UUID prefixes; tap one for its details. Refresh with the inflight-artifact-refresh skill; change the page with inflight-artifact-design.</footer></main><dialog id="dlg"><div class="dlg" id="dlg-body"></div></dialog>{data}<script>{JS}</script></body></html>'''
dest = a.out or os.path.join(STATE, a.page + ".html")
open(dest, "w").write(out)
json.dump({"prs": [ref_of(p) for p in unf_prs], "tasks": [k["id8"] for k in unf_tasks], "sessions": [s["id"] for s in live_sessions if s["thread"] == "unfiled"]}, open(os.path.join(STATE, a.page + ".unsorted.json"), "w"), indent=1)
print(dest, len(out), "bytes;", "unsorted PRs:", len(unf_prs), "· unsorted tasks:", len(unf_tasks))
if gone: print("no longer pending, drop these rows: " + ", ".join(gone))
