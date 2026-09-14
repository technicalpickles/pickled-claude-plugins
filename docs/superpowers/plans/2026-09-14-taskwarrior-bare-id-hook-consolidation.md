# Taskwarrior Bare-ID Hook Consolidation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop bare taskwarrior integer IDs from landing in durable artifacts (CLAUDE.md, docs, commit messages, memory, handoffs) by consolidating the duplicated, gap-ridden nudge hooks currently split across two repos into one set of hooks in the `pickled-claude-plugins` `taskwarrior` plugin.

**Architecture:** Two repos currently each ship half of this safety net with different, non-overlapping blind spots: `dotfiles` (`claude/roles/home.jsonc`) has a `PreToolUse:Write|Edit` content-pattern nudge but restricts it to three hardcoded directories (`.parkinglot/`, `.beans/`, the auto-memory dir), and a working `PreToolUse:Bash(task:*)` mutation nudge; `pickled-claude-plugins` (`plugins/taskwarrior/hooks/`) has a `PostToolUse:Bash` UUID-resolver for `task add` (works) and a `PostToolUse:Skill` nudge that only fires for `agent-meta:park` (far too narrow). Move the two working dotfiles hooks into the plugin, drop the file-path allowlist in favor of matching on content alone (a false-positive nudge is free; a missed real path is not), add a new check for `git commit` message bodies, and delete the park-only hook it supersedes. Delete the now-redundant dotfiles hooks and regenerate local config from the plugin.

**Tech Stack:** Python 3 (hook scripts, JSON stdin/stdout per Claude Code's PreToolUse/PostToolUse hook contract), `bats` (hook tests, matching the `second-brain` plugin's existing test pattern), `jq` (dotfiles hook removal only, no new jq).

**Spec:** No separate spec doc — this plan is scoped directly from investigation findings (see taskwarrior task `63b2fa50-041e-4ec7-bcc8-97a865cbeb41` and its annotation on `f1119451-5cde-49fd-9f20-87a615ec17ee`) and the "Durable references" section of `plugins/taskwarrior/skills/taskwarrior/SKILL.md`.

## Global Constraints

- Bare-ID detection matches on message/content text only, never on file path — no allowlist of "durable" paths. This is the specific decision that fixes the bug (a path allowlist is exactly what missed `CLAUDE.md` and `docs/setup-notes.md` in the incident that prompted this plan).
- All new hooks are **non-blocking**: every `PreToolUse` output uses `permissionDecision: "allow"`, only ever adding `additionalContext`. Never withhold a decision or use `"deny"`/`"ask"`.
- Every hook script must fail silently (exit 0, no output) on malformed/unexpected stdin — never crash and never block a tool call over the hook's own bug. This matches the existing `resolve-added-task-uuid.py` and `check-sb-before-call.py` pattern.
- Bare-ID pattern: case-insensitive `\b(?:taskwarrior|task)\s*#?\s*([0-9]{1,6})\b` — matches `task 518`, `taskwarrior 518`, `task #518`, `task#518`. Deliberately does **not** try to distinguish a genuine all-digit short UUID (e.g. `09351263`) from a real integer ID — that ambiguity already exists in the current dotfiles regex and is out of scope here; the cost of an occasional unnecessary nudge is acceptable.
- Follow this repo's commit-scope convention: `fix(taskwarrior): ...` / `feat(taskwarrior): ...` for plugin changes (scope required for `feat`/`fix`/`perf`), plain `fix: ...` for the dotfiles-repo commit (different repo, different convention — dotfiles has no scope requirement).
- Plan step headers below are kebab-case slugs, not numbers, per `claude/rules/taskwarrior.md`'s "plan step numbers rot" rule — this plan itself has enough steps to qualify.

---

## File Structure

**`pickled-claude-plugins` repo** (this repo, path relative to `plugins/taskwarrior/`):

- `hooks/nudge-durable-write-bare-id.py` — **new**. `PreToolUse:Write|Edit`. Scans `tool_input.content` / `tool_input.new_string` for the bare-ID pattern; if found, emits an `additionalContext` nudge. No file-path filtering.
- `hooks/guard-bash-task-citation.py` — **new**. `PreToolUse:Bash`. Two independent checks against `tool_input.command`: (a) a mutating `task <N> done|annotate|modify|depends|delete|start|stop` call by bare integer ID, (b) a `git commit` invocation whose message body contains the bare-ID pattern. Either match (or both) produces one combined `additionalContext` nudge.
- `hooks/nudge-uuid-on-handoff.py` — **deleted**. Superseded by `nudge-durable-write-bare-id.py`, which fires on the actual Write/Edit regardless of which skill triggered it.
- `hooks/resolve-added-task-uuid.py` — unchanged.
- `hooks/hooks.json` — updated: drop the `PostToolUse:Skill` entry, add `PreToolUse:Write|Edit` and `PreToolUse:Bash` entries, keep the existing `PostToolUse:Bash` entry.
- `hooks/tests/nudge-durable-write-bare-id.bats` — **new**.
- `hooks/tests/guard-bash-task-citation.bats` — **new**.
- `README.md` — updated Hooks section (drop the park-only description, describe the two new hooks).
- `.claude-plugin/marketplace.json` — version bump (via `scripts/bump-version.sh --auto`, last task).

**`.github/workflows/taskwarrior-plugin-tests.yml`** — **new**, at the repo root (not under `plugins/taskwarrior/`) — mirrors `.github/workflows/second-brain-plugin-tests.yml`, scoped to `plugins/taskwarrior/hooks/**`.

**`dotfiles` repo** (absolute path `/Users/technicalpickles/github.com/technicalpickles/dotfiles/`):

- `claude/roles/home.jsonc` — remove the two `PreToolUse` hook entries (the `Write|Edit` bare-ID nudge and the `Bash(task:*)` mutation nudge, lines ~88–124 as of this writing) and their explanatory comments. The `SessionStart` block and everything else in the file is untouched.

---

## Task 1: write-edit-nudge-script

**Files:**
- Create: `plugins/taskwarrior/hooks/nudge-durable-write-bare-id.py`
- Test: `plugins/taskwarrior/hooks/tests/nudge-durable-write-bare-id.bats`

**Interfaces:**
- Consumes: nothing from other tasks (first task).
- Produces: an executable Python 3 script at `plugins/taskwarrior/hooks/nudge-durable-write-bare-id.py` that reads a JSON `PreToolUse` payload on stdin (`{"tool_input": {"file_path": str, "content": str}}` for `Write`, or `{"tool_input": {"file_path": str, "new_string": str}}` for `Edit`) and either prints nothing (exit 0) or prints one line of JSON matching `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow", "additionalContext": str}}` (exit 0). Later tasks (`hooks-json-rewire`, `readme-update`) depend on this exact behavior and file path.

- [ ] **Step 1: Write the failing tests**

```bash
cat > plugins/taskwarrior/hooks/tests/nudge-durable-write-bare-id.bats <<'BATS_EOF'
#!/usr/bin/env bats
# Tests for the PreToolUse:Write|Edit hook that nudges on a bare taskwarrior
# integer-ID citation in the content being written. Deliberately not scoped
# to any file path -- see the plan header for why.

HOOK="$BATS_TEST_DIRNAME/../nudge-durable-write-bare-id.py"

run_hook() {
  # run_hook <json>
  run bash -c "echo '$1' | python3 '$HOOK'"
}

@test "silent when content has no task reference at all" {
  run_hook '{"tool_input": {"file_path": "CLAUDE.md", "content": "Nothing to see here."}}'

  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "silent when the citation is already a UUID" {
  run_hook '{"tool_input": {"file_path": "CLAUDE.md", "content": "see taskwarrior c9dca83f for context"}}'

  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "nudges on a bare integer ID in CLAUDE.md (the file the real incident hit)" {
  run_hook '{"tool_input": {"file_path": "CLAUDE.md", "content": "replaced 2026-09-13, see taskwarrior 518"}}'

  [ "$status" -eq 0 ]
  [[ "$output" == *'"permissionDecision": "allow"'* ]]
  [[ "$output" == *"additionalContext"* ]]
  [[ "$output" == *"518"* ]]
}

@test "nudges on a bare integer ID in a non-durable-looking path (no path filtering)" {
  run_hook '{"tool_input": {"file_path": "docs/setup-notes.md", "content": "closes taskwarrior 71701d18 and see task 518 for the follow-up"}}'

  [ "$status" -eq 0 ]
  [[ "$output" == *"additionalContext"* ]]
}

@test "handles Edit's new_string field the same as Write's content field" {
  run_hook '{"tool_input": {"file_path": "docs/notes.md", "new_string": "task 42 covers this"}}'

  [ "$status" -eq 0 ]
  [[ "$output" == *"additionalContext"* ]]
}

@test "fails silently on malformed stdin" {
  run bash -c "echo 'not json' | python3 '$HOOK'"

  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "fails silently when tool_input is missing entirely" {
  run_hook '{}'

  [ "$status" -eq 0 ]
  [ -z "$output" ]
}
BATS_EOF
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `bats plugins/taskwarrior/hooks/tests/nudge-durable-write-bare-id.bats`
Expected: every test FAILs (or errors) with "No such file or directory" for the hook script — it doesn't exist yet.

- [ ] **Step 3: Write the hook script**

```bash
cat > plugins/taskwarrior/hooks/nudge-durable-write-bare-id.py <<'PY_EOF'
#!/usr/bin/env python3
"""
PreToolUse:Write|Edit hook that nudges taskwarrior UUID-safety whenever the
content being written cites a bare integer task ID.

Why content-only, no file-path scoping: an earlier version of this check
(in dotfiles' claude/roles/home.jsonc) restricted itself to three
hardcoded "durable artifact" directories (.parkinglot/, .beans/, the
auto-memory dir). A real incident (2026-09-13, pickleclaw session
55438e39) cited a bare integer ID ("taskwarrior 518") 8 times across
CLAUDE.md and docs/setup-notes.md -- neither path was in the allowlist,
so nothing fired. A bare-content match with no path filter is strictly
broader and the cost of a false positive is one extra line of
additionalContext, so there is no reason to maintain a path allowlist
that will always be one directory behind wherever the model actually
writes prose. See plugins/taskwarrior/skills/taskwarrior/SKILL.md's
"Durable references" section for the underlying policy.

This intentionally does not try to distinguish a genuine short UUID that
happens to be all-digits (e.g. "09351263") from a real integer ID -- that
ambiguity already existed in the dotfiles version of this check and an
occasional unnecessary nudge is cheap.
"""
import json
import re
import sys

_BARE_ID_RE = re.compile(
    r"\b(?:taskwarrior|task)\s*#?\s*([0-9]{1,6})\b",
    re.IGNORECASE,
)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    try:
        tool_input = payload.get("tool_input") or {}
        content = tool_input.get("content")
        if content is None:
            content = tool_input.get("new_string")
        if not isinstance(content, str):
            sys.exit(0)

        match = _BARE_ID_RE.search(content)
        if not match:
            sys.exit(0)

        task_id = match.group(1)
        file_path = tool_input.get("file_path") or "(unknown file)"

        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "additionalContext": (
                    f"This write to {file_path} cites a bare numeric task "
                    f"reference ({task_id}). Integer taskwarrior IDs are "
                    "reused as the pending list reorders, so anything that "
                    "outlives this shell (docs, CLAUDE.md, commit messages, "
                    "memory, handoffs, PRs) should cite the UUID instead -- "
                    f"verify it first with `task {task_id} info` or "
                    "`task <uuid> info`, don't just reuse a cached ID. See "
                    "the taskwarrior skill's Durable references section."
                ),
            }
        }
        print(json.dumps(output))
    except Exception:
        sys.exit(0)
    sys.exit(0)


if __name__ == "__main__":
    main()
PY_EOF
chmod +x plugins/taskwarrior/hooks/nudge-durable-write-bare-id.py
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `bats plugins/taskwarrior/hooks/tests/nudge-durable-write-bare-id.bats`
Expected: all 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/taskwarrior/hooks/nudge-durable-write-bare-id.py plugins/taskwarrior/hooks/tests/nudge-durable-write-bare-id.bats
git commit -m "$(cat <<'EOF'
feat(taskwarrior): add content-only bare-ID nudge for any Write/Edit

Replaces the file-path-scoped version of this check that lived in
dotfiles (.parkinglot/.beans/memory-dir only). A real incident cited
a bare integer ID 8 times across CLAUDE.md and docs/setup-notes.md,
neither of which was in that allowlist. Matching on content alone,
with no path filter, closes that gap -- a false-positive nudge is
free, a missed durable file is not.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: bash-guard-script

**Files:**
- Create: `plugins/taskwarrior/hooks/guard-bash-task-citation.py`
- Test: `plugins/taskwarrior/hooks/tests/guard-bash-task-citation.bats`

**Interfaces:**
- Consumes: nothing from Task 1 directly (independent script), but reuses the same bare-ID regex concept documented in Task 1's docstring — keep the two patterns textually identical (`\b(?:taskwarrior|task)\s*#?\s*([0-9]{1,6})\b`) so both hooks nudge on the same inputs.
- Produces: an executable Python 3 script at `plugins/taskwarrior/hooks/guard-bash-task-citation.py` reading `{"tool_input": {"command": str}}` on stdin, emitting the same `additionalContext` JSON shape as Task 1 (or nothing). Later task `hooks-json-rewire` depends on this exact file path.

- [ ] **Step 1: Write the failing tests**

```bash
cat > plugins/taskwarrior/hooks/tests/guard-bash-task-citation.bats <<'BATS_EOF'
#!/usr/bin/env bats
# Tests for the PreToolUse:Bash hook guarding two risky bare-ID patterns:
# (1) mutating a task by its plain numeric ID, (2) citing a bare numeric ID
# in a git commit message.

HOOK="$BATS_TEST_DIRNAME/../guard-bash-task-citation.py"

run_hook() {
  # run_hook <json>
  run bash -c "echo '$1' | python3 '$HOOK'"
}

@test "silent on an unrelated Bash command" {
  run_hook '{"tool_input": {"command": "ls -la"}}'

  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "silent on a read-only task command" {
  run_hook '{"tool_input": {"command": "task 518 info"}}'

  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "nudges on task done by bare integer ID" {
  run_hook '{"tool_input": {"command": "task 518 done"}}'

  [ "$status" -eq 0 ]
  [[ "$output" == *'"permissionDecision": "allow"'* ]]
  [[ "$output" == *"518"* ]]
}

@test "nudges on task annotate/modify/depends/delete/start/stop by bare ID" {
  for verb in annotate modify depends delete start stop; do
    run_hook "{\"tool_input\": {\"command\": \"task 42 $verb\"}}"
    [ "$status" -eq 0 ]
    [[ "$output" == *"additionalContext"* ]]
  done
}

@test "silent on a git commit with no task reference" {
  run_hook '{"tool_input": {"command": "git commit -m \"fix: typo\""}}'

  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "nudges on a git commit -m citing a bare integer ID" {
  run_hook '{"tool_input": {"command": "git commit -m \"fix: matches taskwarrior 518\""}}'

  [ "$status" -eq 0 ]
  [[ "$output" == *"additionalContext"* ]]
  [[ "$output" == *"518"* ]]
}

@test "nudges on a git commit heredoc body citing a bare integer ID (the real incident's shape)" {
  run_hook '{"tool_input": {"command": "git commit -m \"$(cat <<'"'"'EOF'"'"'\nmatching picklehome'"'"'s already-deployed fix (taskwarrior 518).\nEOF\n)\""}}'

  [ "$status" -eq 0 ]
  [[ "$output" == *"additionalContext"* ]]
}

@test "silent on a git commit citing a UUID, not an integer" {
  run_hook '{"tool_input": {"command": "git commit -m \"closes taskwarrior c9dca83f\""}}'

  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "fails silently on malformed stdin" {
  run bash -c "echo 'not json' | python3 '$HOOK'"

  [ "$status" -eq 0 ]
  [ -z "$output" ]
}
BATS_EOF
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `bats plugins/taskwarrior/hooks/tests/guard-bash-task-citation.bats`
Expected: every test FAILs — the hook script doesn't exist yet.

- [ ] **Step 3: Write the hook script**

```bash
cat > plugins/taskwarrior/hooks/guard-bash-task-citation.py <<'PY_EOF'
#!/usr/bin/env python3
"""
PreToolUse:Bash hook guarding two risky bare-integer-ID patterns in a
single `task` or `git` command:

1. A mutating `task <N> done|annotate|modify|depends|delete|start|stop`
   call by plain decimal ID. Numeric IDs are reused as the pending list
   reorders; if this ID was captured more than a couple of commands ago,
   or anything else touched taskwarrior in between, it may no longer
   point at the intended task.

2. A `git commit` whose message text (via -m or a heredoc body) cites a
   bare integer ID. This is the exact shape of a real incident
   (2026-09-13, pickleclaw session 55438e39): "taskwarrior 518" landed
   in a commit message 7.5 hours after the task-add-time UUID resolver
   shipped, because that hook only fires when *creating* a task -- it
   has nothing to say about citing an *existing* task from memory.

Formerly two separate hooks living in dotfiles' claude/roles/home.jsonc
(the mutation check) and nowhere at all (the commit-message check).
Consolidated here so this plugin, not personal dotfiles config, is the
single owner of taskwarrior safety behavior -- see plugins/taskwarrior/
skills/taskwarrior/SKILL.md's "Durable references" section.
"""
import json
import re
import sys

_MUTATION_RE = re.compile(
    r"\btask\s+([0-9]{1,6})\s+"
    r"(done|annotate|modify|depends|delete|start|stop)\b"
)
_BARE_ID_RE = re.compile(
    r"\b(?:taskwarrior|task)\s*#?\s*([0-9]{1,6})\b",
    re.IGNORECASE,
)
_GIT_COMMIT_RE = re.compile(r"\bgit\s+commit\b")


def _mutation_context(command: str) -> str | None:
    match = _MUTATION_RE.search(command)
    if not match:
        return None
    task_id, verb = match.group(1), match.group(2)
    return (
        f"This mutates taskwarrior task {task_id} by its plain numeric ID "
        f"(`{verb}`). Numeric IDs are reused as the pending list reorders "
        f"-- if this ID was captured more than a couple of commands ago "
        "(or anything else touched taskwarrior in between), re-resolve it "
        f"first: `task {task_id} info` (or re-grep by description) to "
        "confirm it still points at the task you mean. See the "
        "taskwarrior skill's Durable references section."
    )


def _commit_context(command: str) -> str | None:
    if not _GIT_COMMIT_RE.search(command):
        return None
    match = _BARE_ID_RE.search(command)
    if not match:
        return None
    task_id = match.group(1)
    return (
        f"This commit message cites a bare numeric task reference "
        f"({task_id}). Commit messages outlive the shell they were "
        "written in -- verify this resolves to the intended task "
        f"(`task {task_id} info`) and cite the UUID instead. See the "
        "taskwarrior skill's Durable references section."
    )


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    try:
        tool_input = payload.get("tool_input") or {}
        command = tool_input.get("command")
        if not isinstance(command, str):
            sys.exit(0)

        contexts = [
            ctx
            for ctx in (_mutation_context(command), _commit_context(command))
            if ctx
        ]
        if not contexts:
            sys.exit(0)

        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "additionalContext": " ".join(contexts),
            }
        }
        print(json.dumps(output))
    except Exception:
        sys.exit(0)
    sys.exit(0)


if __name__ == "__main__":
    main()
PY_EOF
chmod +x plugins/taskwarrior/hooks/guard-bash-task-citation.py
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `bats plugins/taskwarrior/hooks/tests/guard-bash-task-citation.bats`
Expected: all 9 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/taskwarrior/hooks/guard-bash-task-citation.py plugins/taskwarrior/hooks/tests/guard-bash-task-citation.bats
git commit -m "$(cat <<'EOF'
feat(taskwarrior): guard bare-ID task mutations and git commit citations

Consolidates the mutation-by-bare-ID check that used to live only in
dotfiles' claude/roles/home.jsonc, and adds a new check nothing
covered before: a git commit message citing a bare integer ID. This
second check is the exact gap that let "taskwarrior 518" land in a
real commit message 7.5 hours after the task-add-time UUID resolver
shipped -- that hook only fires when creating a task, not when citing
an existing one from memory.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: hooks-json-rewire

**Files:**
- Modify: `plugins/taskwarrior/hooks/hooks.json`
- Delete: `plugins/taskwarrior/hooks/nudge-uuid-on-handoff.py`

**Interfaces:**
- Consumes: `nudge-durable-write-bare-id.py` (Task 1) and `guard-bash-task-citation.py` (Task 2) as command paths.
- Produces: the plugin's live hook wiring — no other task depends on this file's contents beyond it being correct.

- [ ] **Step 1: Delete the superseded hook**

```bash
git rm plugins/taskwarrior/hooks/nudge-uuid-on-handoff.py
```

- [ ] **Step 2: Rewrite hooks.json**

```bash
cat > plugins/taskwarrior/hooks/hooks.json <<'JSON_EOF'
{
  "description": "Nudge taskwarrior UUID-safety on any Write/Edit or risky Bash command citing a bare integer task ID; auto-resolve the UUID of a task just created with `task add`",
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}\"/hooks/nudge-durable-write-bare-id.py"
          }
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}\"/hooks/guard-bash-task-citation.py"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}\"/hooks/resolve-added-task-uuid.py"
          }
        ]
      }
    ]
  }
}
JSON_EOF
```

- [ ] **Step 3: Verify the JSON is well-formed**

Run: `jq . plugins/taskwarrior/hooks/hooks.json`
Expected: pretty-printed JSON, no parse error.

- [ ] **Step 4: Verify no stale references remain**

Run: `grep -rn "nudge-uuid-on-handoff" plugins/ || echo "clean"`
Expected: `clean` (only remaining hit, if any, should be in this plan file itself — that's fine).

- [ ] **Step 5: Commit**

```bash
git add plugins/taskwarrior/hooks/hooks.json plugins/taskwarrior/hooks/nudge-uuid-on-handoff.py
git commit -m "$(cat <<'EOF'
fix(taskwarrior): rewire hooks.json onto the consolidated bare-ID hooks

Drops the PostToolUse:Skill hook scoped to agent-meta:park only
(nudge-uuid-on-handoff.py, deleted) in favor of the new
PreToolUse:Write|Edit hook, which fires on the actual write
regardless of which skill triggered it. Adds the new
PreToolUse:Bash guard alongside the existing PostToolUse:Bash
UUID-resolver.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: readme-and-ci

**Files:**
- Modify: `plugins/taskwarrior/README.md`
- Create: `.github/workflows/taskwarrior-plugin-tests.yml`

**Interfaces:**
- Consumes: file paths from Tasks 1–3 (documents them; no code dependency).
- Produces: CI coverage so a future regression in these hooks fails a PR check, matching the existing `second-brain` plugin's pattern.

- [ ] **Step 1: Update the README's Hooks section**

In `plugins/taskwarrior/README.md`, replace the existing `## Hooks` section (the `PostToolUse:Skill` bullet and the `PostToolUse:Bash` bullet) with:

```markdown
## Hooks

- A `PreToolUse:Write|Edit` hook nudges taskwarrior UUID-safety whenever the content being written cites a bare integer task reference (`task 518`, `taskwarrior 518`, `task #518`). Fires on any Write or Edit, not just durable-looking paths -- an earlier, path-scoped version of this check (once part of personal dotfiles config, restricted to `.parkinglot/`, `.beans/`, and the auto-memory dir) missed a real incident where a bare ID landed in `CLAUDE.md` and `docs/setup-notes.md`. See `hooks/nudge-durable-write-bare-id.py`.
- A `PreToolUse:Bash` hook guards two risky patterns in one pass: mutating a task (`done`/`annotate`/`modify`/`depends`/`delete`/`start`/`stop`) by its plain numeric ID, and a `git commit` whose message cites a bare integer ID. See `hooks/guard-bash-task-citation.py`.
- A `PostToolUse:Bash` hook resolves the UUID of a task just created with `task add`, without needing a follow-up tool call. It detects a `Created task <N>.` message, resolves `N` to its UUID via `task _get <N>.uuid`, and injects both into context. This exists because in practice the follow-up UUID resolution almost never happens on its own (measured: 32 of 33 `task add` calls across a week of sessions had no inline resolution) -- the bare integer is what's sitting in context when a durable artifact gets written later, so removing the need to remember the follow-up removes the leak at its source. See `hooks/resolve-added-task-uuid.py`.
```

- [ ] **Step 2: Add the CI workflow**

```bash
cat > .github/workflows/taskwarrior-plugin-tests.yml <<'YML_EOF'
name: taskwarrior plugin tests

on:
  pull_request:
    branches: [main]
    paths:
      - 'plugins/taskwarrior/hooks/**'
      - '.github/workflows/taskwarrior-plugin-tests.yml'

permissions:
  contents: read

jobs:
  bats:
    name: bats
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: plugins/taskwarrior
    steps:
      - uses: actions/checkout@v4

      - name: Install bats
        run: sudo apt-get update && sudo apt-get install -y bats

      - name: Run bats
        run: bats hooks/tests/
YML_EOF
```

- [ ] **Step 3: Run the full test suite locally to confirm the CI command works**

Run: `cd plugins/taskwarrior && bats hooks/tests/`
Expected: all tests from Tasks 1 and 2 PASS (16 tests total).

- [ ] **Step 4: Commit**

```bash
git add plugins/taskwarrior/README.md .github/workflows/taskwarrior-plugin-tests.yml
git commit -m "$(cat <<'EOF'
docs(taskwarrior): document consolidated hooks, add bats CI workflow

README now describes the two new PreToolUse hooks in place of the
park-only PostToolUse:Skill hook. CI workflow mirrors
second-brain-plugin-tests.yml so a regression in hook behavior fails
the PR instead of surfacing as a silent leak weeks later.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: version-bump

**Files:**
- Modify: `.claude-plugin/marketplace.json`

**Interfaces:**
- Consumes: the conventional-commit history from Tasks 1–4 (all `feat(taskwarrior)`/`fix(taskwarrior)`/`docs`), auto-detected by the bump script.
- Produces: nothing further depends on this.

- [ ] **Step 1: Run the bump script**

Run: `./scripts/bump-version.sh --auto`
Expected: output confirms a minor bump for the `taskwarrior` plugin (the change set contains `feat(taskwarrior)` commits, which take precedence over `fix`/`docs`), and regenerates the root README's plugin table.

- [ ] **Step 2: Verify the version and table**

Run: `git diff .claude-plugin/marketplace.json README.md`
Expected: `taskwarrior`'s `version` field bumped (e.g. `1.3.0` → `1.4.0`); README plugin table row for `taskwarrior` unchanged in content (description didn't change) but present.

- [ ] **Step 3: Commit**

```bash
git add .claude-plugin/marketplace.json README.md
git commit -m "$(cat <<'EOF'
chore(taskwarrior): bump version to 1.4.0

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: dotfiles-hook-removal

**Files:**
- Modify (in the `dotfiles` repo, absolute path `/Users/technicalpickles/github.com/technicalpickles/dotfiles/claude/roles/home.jsonc`): remove the two `PreToolUse` hook entries superseded by Tasks 1–3.

This task lands in a **different repository** from Tasks 1–5. Do not attempt it inside the `pickled-claude-plugins` worktree — `cd` to the dotfiles checkout first (or open a fresh session there once `main` in `pickled-claude-plugins` has the plugin changes merged).

**Interfaces:**
- Consumes: the fact that `nudge-durable-write-bare-id.py` and `guard-bash-task-citation.py` are live in the plugin (Tasks 1–3 merged) before removing the dotfiles equivalents, or there is a window with no coverage at all.
- Produces: nothing further depends on this within this plan.

- [ ] **Step 1: Confirm the plugin changes are live first**

Run (from the dotfiles repo): `claude plugin list --json | jq '.[] | select(.name == "taskwarrior") | .version'`
Expected: the version from Task 5 (e.g. `"1.4.0"`), not the pre-plan version. If this doesn't match yet, stop here and wait for the plugin update/reinstall — removing the dotfiles hooks before this lands a real coverage gap.

- [ ] **Step 2: Remove the two hook entries from home.jsonc**

Open `claude/roles/home.jsonc` and delete the comment block and both entries under `"hooks": { "PreToolUse": [ ... ] }` that implement the Write|Edit bare-ID nudge and the `Bash(task:*)` mutation nudge (the two entries whose `command` starts with `jq -c`, and the explanatory comments immediately above each — currently lines ~88–124). Leave the `"SessionStart"` block and everything else in the file untouched. If removing both `PreToolUse` entries empties the `"PreToolUse"` array, remove the now-empty `"PreToolUse": []` key entirely rather than leaving a dangling empty array — check whether `"hooks"` still has other keys (it does not, as of this writing, so `"hooks": { ... }` may need to be dropped from the file if it becomes `{"hooks": {}}` after this edit; if a `"SessionStart"` block exists elsewhere at the top level rather than nested under the same `"hooks"` key, keep it — recheck the file structure before deleting, don't assume this plan's line numbers are still exact).

- [ ] **Step 3: Regenerate local config**

Run: `./claudeconfig.sh`
Expected: exits 0, no errors.

- [ ] **Step 4: Verify the plugin's hooks are what's active now**

Run: `jq '.hooks.PreToolUse' ~/.claude/settings.json` (or wherever `claudeconfig.sh` writes the merged settings — check its output for the actual path if this doesn't match)
Expected: no `jq -c` command strings referencing the old bare-ID checks; the plugin's hooks (surfaced via the installed plugin's own `hooks.json`, not `settings.json` directly, depending on how Claude Code merges plugin hooks — verify by checking the plugin cache path instead if `settings.json` doesn't show it: `cat ~/.claude/plugins/cache/pickled-claude-plugins/taskwarrior/*/hooks/hooks.json`) matches Task 3's `hooks.json`.

- [ ] **Step 5: Manually smoke-test end to end**

Run: `echo '{"tool_input": {"file_path": "CLAUDE.md", "content": "see taskwarrior 518"}}' | python3 ~/.claude/plugins/cache/pickled-claude-plugins/taskwarrior/*/hooks/nudge-durable-write-bare-id.py`
Expected: JSON output with `additionalContext` mentioning `518`.

- [ ] **Step 6: Commit (dotfiles repo)**

```bash
git add claude/roles/home.jsonc
git commit -m "$(cat <<'EOF'
fix: remove bare-ID nudge hooks superseded by the taskwarrior plugin

Both PreToolUse hooks (Write|Edit content nudge, Bash(task:*)
mutation nudge) are now owned by pickled-claude-plugins' taskwarrior
plugin (nudge-durable-write-bare-id.py, guard-bash-task-citation.py),
which also fixes the path-allowlist gap these dotfiles versions had
(CLAUDE.md and docs/*.md weren't covered -- see
docs/superpowers/plans/2026-09-14-taskwarrior-bare-id-hook-consolidation.md
in pickled-claude-plugins). Personal config no longer needs to
duplicate reusable plugin behavior.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: close-out-tracking

**Files:** none (taskwarrior only, no repo files).

**Interfaces:** none.

- [ ] **Step 1: Mark the fix task done**

Run: `task 63b2fa50-041e-4ec7-bcc8-97a865cbeb41 done`
Expected: confirms task 63b2fa50 completed.

- [ ] **Step 2: Annotate and close the review task early**

Run: `task f1119451-5cde-49fd-9f20-87a615ec17ee annotate "Closed early: the fix (was task 63b2fa50) landed via docs/superpowers/plans/2026-09-14-taskwarrior-bare-id-hook-consolidation.md before the 2026-09-20 due date. Root cause and resolution documented there."`

Run: `task f1119451-5cde-49fd-9f20-87a615ec17ee done`
Expected: confirms task f1119451 completed.

---

## Self-Review Notes

- **Spec coverage:** every gap identified in the investigation has a task — Write/Edit path-allowlist gap (Task 1), Bash mutation check preserved (Task 2), commit-message gap that caused the actual incident (Task 2), stale hook removed (Task 3), docs/CI (Task 4), version bump (Task 5), dotfiles-side removal to close the split (Task 6), tracking close-out (Task 7).
- **Placeholder scan:** no TBD/TODO markers; every code step has real code; the "check the actual output path" caveats in Task 6 Steps 3–4 are deliberate (settings-merge output location depends on installed Claude Code version and wasn't verified during planning) rather than a placeholder — Step 5's direct hook invocation is the authoritative verification regardless of where `settings.json` ends up.
- **Type/name consistency:** `nudge-durable-write-bare-id.py` and `guard-bash-task-citation.py` are the two names used consistently from Task 1 through the README and hooks.json; the bare-ID regex `\b(?:taskwarrior|task)\s*#?\s*([0-9]{1,6})\b` is identical text in both scripts' source (Tasks 1 and 2) and both bats suites.
