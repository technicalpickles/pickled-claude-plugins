#!/usr/bin/env python3
"""Sort a vault inbox into what process-inbox should do with each note.

Usage: survey-inbox.py [INBOX_DIR]

With no argument, the inbox of sb's default vault is used. Prints one JSON
object. Notes are in filename order, which is capture order. Every note lands in exactly one bucket of `next`; `stale` and
`near_duplicates` are cross-cutting flags on notes that are also bucketed.
Session notes are left out of the duplicate check: two sessions on the same
project read alike in title without repeating each other.

The `status` key carries three vocabularies in one field: pipeline state
(raw ... connected), zettelkasten maturity (seedling, budding, evergreen) and
vault lifecycle (filed, incubating, active, complete, dormant, abandoned).
Only pipeline state says which stage is next. A note with a maturity or
lifecycle status is already a finished note sitting in the inbox, so it goes
straight to routing and keeps its status. So does a note with no status that
isn't a session note: it was written by hand or by capture, not by the
pipeline, and has nothing to ingest.
"""
import glob
import json
import os
import re
import subprocess
import sys
from datetime import date, datetime

PIPELINE_NEXT = {
    "raw": "ingest",
    "ingested": "enrich",
    "enriched": "route",
    "pending-review": "route",
    "routed": "connect",
    "connected": "link-daily",
}
VAULT_STATUSES = {
    "seedling", "budding", "evergreen",
    "filed", "incubating", "active", "complete", "dormant", "abandoned",
}
BUCKETS = (
    "empty", "session-not-on-disk", "ingest", "enrich", "route",
    "route-keep-status", "connect", "link-daily", "kept-record", "unknown-status",
)
STALE_DAYS = 14
SESSION_KEYS = ("session-id", "session_id", "session")
SESSION_SOURCE_RE = re.compile(r"claude-code session\b\s*(\S*)")
SESSION_ID_RE = re.compile(r"^[0-9a-f]{8}[0-9a-f-]*$")
STOPWORDS = {"a", "an", "and", "the", "of", "for", "to", "in", "on", "with", "vs", "how", "why", "what"}


def run_sb(*args):
    out = subprocess.run(
        ["npx", "@techpickles/sb", *args], check=True, capture_output=True, text=True
    ).stdout
    return json.loads(out)


def default_inbox():
    vault = run_sb("vault", "info")["path"]
    inbox = run_sb("vault", "obsidian").get("inbox") or "Inbox"
    return os.path.join(vault, inbox)


def split_note(text):
    """Return (frontmatter dict, body) using top-level `key: value` lines."""
    meta = {}
    if not text.startswith("---"):
        return meta, text
    lines = text.splitlines()
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return meta, "\n".join(lines[i + 1:])
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if m:
            value = re.sub(r"\s+#.*$", "", m.group(2))
            meta[m.group(1)] = value.strip().strip("'\"")
    return {}, text


def has_content(body):
    return any(
        line.strip() and not re.match(r"^\s*#{1,6}(\s|$)", line)
        for line in body.splitlines()
    )


def title_of(filename, body):
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return re.sub(r"^\d{12}\s+", "", filename[:-3]).replace("-", " ")


def session_ref(meta):
    """Return (named, session_id). named is False when the note claims no session."""
    for key in SESSION_KEYS:
        if meta.get(key):
            value = meta[key].lower()
            return True, value if SESSION_ID_RE.match(value) else None
    m = SESSION_SOURCE_RE.search(meta.get("source", ""))
    if m:
        value = m.group(1).lower()
        return True, value if SESSION_ID_RE.match(value) else None
    return False, None


def config_dirs():
    raw = os.environ.get("CLAUDE_CONFIG_DIR", "")
    dirs = [d for d in re.split(r"[:,]", raw) if d]
    return dirs or [os.path.expanduser("~/.claude")]


def transcript_on_disk(session_id):
    return any(
        glob.glob(os.path.join(d, "projects", "*", session_id + "*.jsonl"))
        for d in config_dirs()
    )


def captured_on(filename, meta):
    for value in (meta.get("captured", "")[:10], meta.get("created", "")[:10]):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            pass
    try:
        return datetime.strptime(filename[:8], "%Y%m%d").date()
    except ValueError:
        return None


def classify(meta, body):
    """Return (bucket, extra fields for the entry)."""
    if not has_content(body):
        return "empty", {}
    session_notes = meta.get("type") == "session-notes"
    status = meta.get("status", "").lower()
    if not status:
        if not session_notes:
            return "route-keep-status", {"status": None}
        status = "raw"
    if status == "raw" and not session_notes:
        return "unknown-status", {"status": status}
    if status == "ingested" and session_notes:
        return "kept-record", {}
    if status == "raw" and session_notes:
        named, session_id = session_ref(meta)
        if named and session_id is None:
            return "session-not-on-disk", {"repo": meta.get("repo"), "reason": "malformed session id"}
        if named and not transcript_on_disk(session_id):
            return "session-not-on-disk", {
                "repo": meta.get("repo"), "session": session_id, "reason": "no transcript on this machine",
            }
    if status in PIPELINE_NEXT:
        return PIPELINE_NEXT[status], {}
    if status in VAULT_STATUSES:
        return "route-keep-status", {"status": status}
    return "unknown-status", {"status": status}


def title_words(title):
    return {w for w in re.findall(r"[a-z0-9]+", title.lower()) if w not in STOPWORDS}


def near_duplicates(notes):
    """Pairs of notes where one title's words all appear in the other's.

    Pairs, not groups: a short title like "Claude Code" is inside many longer
    ones that aren't duplicates of each other. A shared source is not a
    signal either: one source split into atomic notes is the intended shape.
    """
    pairs = []
    for i, a in enumerate(notes):
        for b in notes[i + 1:]:
            small, big = sorted((a["words"], b["words"]), key=len)
            if small and (small == big or (len(small) >= 2 and small <= big)):
                pairs.append([a["file"], b["file"]])
    return pairs


def survey(inbox, today):
    report = {"inbox": inbox, "total": 0, "next": {b: [] for b in BUCKETS}, "stale": []}
    seen = []
    for filename in sorted(os.listdir(inbox)):
        if not filename.endswith(".md"):
            continue
        with open(os.path.join(inbox, filename), encoding="utf-8", errors="replace") as f:
            meta, body = split_note(f.read())
        bucket, extra = classify(meta, body)
        report["total"] += 1
        report["next"][bucket].append(dict(file=filename, **extra))
        when = captured_on(filename, meta)
        if when and (today - when).days > STALE_DAYS:
            report["stale"].append(filename)
        if bucket != "empty" and meta.get("type") != "session-notes":
            title = title_of(filename, body)
            seen.append({"file": filename, "words": title_words(title)})
    report["near_duplicates"] = near_duplicates(seen)
    return report


def main():
    try:
        inbox = sys.argv[1] if len(sys.argv) > 1 else default_inbox()
        report = survey(inbox, date.today())
    except (OSError, subprocess.CalledProcessError) as e:
        sys.exit(f"survey-inbox: {e}")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
