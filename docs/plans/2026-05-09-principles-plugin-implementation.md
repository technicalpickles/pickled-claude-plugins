# Stay-Principled Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a `stay-principled` plugin in `pickled-claude-plugins/` that anchors design conversations to a project's documented principles via depth-first grilling before brainstorming opens.

**Architecture:** Two skills (`stay-principled:setup`, `stay-principled:grill`) plus a generic Python helper (`scripts/skill-advice.py`) that emits `additionalContext` from PreToolUse hooks. Setup writes a contract file (`docs/agents/principles.md`) following the mattpocock convention. Runtime reads that contract and grills depth-first using grill-me's mechanism with principles as tree roots.

**Tech Stack:** Python 3 stdlib only for the helper. Markdown for skills and config. No external dependencies. No `pyproject.toml` for the plugin (helper runs via direct `python3` invocation to avoid uv cold-start latency).

**Spec:** [`docs/plans/2026-05-09-principles-plugin-design.md`](2026-05-09-principles-plugin-design.md)

**Step naming:** Tasks use kebab-case slugs as headers per the repo convention (commit messages cite the slug, not an ordinal). Slugs are insertion-stable across plan edits.

---

## File structure

Files to create under `plugins/stay-principled/`:

| Path | Responsibility |
|---|---|
| `.claude-plugin/plugin.json` | Plugin manifest (no version per repo convention) |
| `scripts/skill-advice.py` | Generic conditional advice emitter for PreToolUse hooks. Stdlib only. |
| `scripts/test_skill_advice.py` | Unit tests for the helper |
| `skills/setup/SKILL.md` | One-shot config skill, `disable-model-invocation: true` |
| `skills/grill/SKILL.md` | Runtime grilling skill |
| `docs/helper-contract.md` | Contract documentation for `skill-advice.py` |
| `docs/integration-patterns.md` | The three integration patterns A/B/C with full examples |
| `README.md` | Plugin overview, install instructions, usage |

Files to modify:

| Path | Change |
|---|---|
| `.claude-plugin/marketplace.json` | Append `stay-principled` plugin entry with `version: "0.1.0"` |

---

## Task: plugin-scaffold

Create the plugin directory structure, manifest, marketplace registration, and a README stub. After this task, the plugin is registered (empty) and `feat(stay-principled):` becomes a valid commit scope for subsequent tasks.

**Files:**
- Create: `plugins/stay-principled/.claude-plugin/plugin.json`
- Create: `plugins/stay-principled/README.md` (stub; expanded in `readme-finalization`)
- Create: `plugins/stay-principled/scripts/.gitkeep`
- Create: `plugins/stay-principled/skills/.gitkeep`
- Create: `plugins/stay-principled/docs/.gitkeep`
- Modify: `.claude-plugin/marketplace.json` (append `stay-principled` entry)

- [ ] **Step 1: Create the plugin directory structure**

```bash
mkdir -p plugins/stay-principled/.claude-plugin
mkdir -p plugins/stay-principled/scripts
mkdir -p plugins/stay-principled/skills
mkdir -p plugins/stay-principled/docs
touch plugins/stay-principled/scripts/.gitkeep
touch plugins/stay-principled/skills/.gitkeep
touch plugins/stay-principled/docs/.gitkeep
```

- [ ] **Step 2: Write `plugins/stay-principled/.claude-plugin/plugin.json`**

```json
{
  "name": "stay-principled",
  "description": "Anchor design conversations to project principles via depth-first grilling before brainstorming generates options. Reads docs/principles.md (or docs/agents/principles.md), surfaces relevant principles for the topic, asks one question at a time with recommended answers, and outputs a brief that downstream planning can consume."
}
```

No `version` field. Versions live in `.claude-plugin/marketplace.json` only per repo convention (see project CLAUDE.md `## Versioning`).

- [ ] **Step 3: Write a stub `plugins/stay-principled/README.md`**

```markdown
# principles

Anchor design conversations to a project's documented principles before brainstorming opens.

Full documentation arrives in subsequent commits.
```

This stub is replaced in the `readme-finalization` task.

- [ ] **Step 4: Append the plugin entry to `.claude-plugin/marketplace.json`**

The current file ends with the `taskwarrior` entry. Insert the new entry inside the `plugins` array, after the `taskwarrior` block, preserving the closing `]` and `}`.

Modify the tail of `.claude-plugin/marketplace.json` so it reads:

```json
    {
      "name": "taskwarrior",
      "source": "./plugins/taskwarrior",
      "version": "1.0.0"
    },
    {
      "name": "stay-principled",
      "source": "./plugins/stay-principled",
      "version": "0.1.0"
    }
  ]
}
```

- [ ] **Step 5: Verify marketplace.json parses and the new plugin is listed**

Run: `jq '.plugins[] | select(.name == "principles")' .claude-plugin/marketplace.json`

Expected output:

```json
{
  "name": "stay-principled",
  "source": "./plugins/stay-principled",
  "version": "0.1.0"
}
```

- [ ] **Step 6: Verify the validator accepts the new scope**

Run: `bash scripts/validate-plugin-versions.sh` (if it exists; otherwise skip).

Run: `printf 'feat(stay-principled): scaffold plugin\n' > /tmp/test-msg && bash scripts/check-commit-scope.sh /tmp/test-msg && rm /tmp/test-msg`

Expected: exit 0 (scope `stay-principled` now valid because it's in marketplace.json).

- [ ] **Step 7: Commit**

```bash
git add plugins/stay-principled/.claude-plugin/plugin.json plugins/stay-principled/README.md plugins/stay-principled/scripts/.gitkeep plugins/stay-principled/skills/.gitkeep plugins/stay-principled/docs/.gitkeep .claude-plugin/marketplace.json
git commit -m "feat(stay-principled): scaffold plugin and register in marketplace

Empty plugin scaffold with manifest, README stub, and marketplace
registration at version 0.1.0. Subsequent commits add the helper script,
both skills, and documentation."
```

---

## Task: helper-tests

Write failing tests for `scripts/skill-advice.py` covering all behaviors described in the spec's Helper Contract section: tool-name filter, skill-name filter, file-existence guard, JSON output shape, silent failure on unparseable stdin.

**Files:**
- Create: `plugins/stay-principled/scripts/test_skill_advice.py`

- [ ] **Step 1: Write the test file with failing tests for all behaviors**

Create `plugins/stay-principled/scripts/test_skill_advice.py`:

```python
"""Tests for the skill-advice hook helper.

Runs the helper script as a subprocess, feeding PreToolUse-shaped JSON to
stdin, and asserts on exit code and stdout.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parent / "skill-advice.py"


def run_helper(stdin_text: str, args: list[str]) -> tuple[int, str]:
    """Invoke skill-advice.py as a subprocess. Return (exit_code, stdout)."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        input=stdin_text,
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout


class SkillAdviceTests(unittest.TestCase):
    def test_tool_mismatch_emits_nothing(self):
        stdin = json.dumps({"tool_name": "Bash", "tool_input": {}})
        code, out = run_helper(
            stdin, ["--skill", "superpowers:brainstorming", "--advice", "hi"]
        )
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_skill_mismatch_emits_nothing(self):
        stdin = json.dumps(
            {"tool_name": "Skill", "tool_input": {"skill": "other"}}
        )
        code, out = run_helper(
            stdin, ["--skill", "superpowers:brainstorming", "--advice", "hi"]
        )
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_unparseable_stdin_exits_silently(self):
        code, out = run_helper(
            "not json",
            ["--skill", "superpowers:brainstorming", "--advice", "hi"],
        )
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_empty_stdin_exits_silently(self):
        code, out = run_helper(
            "",
            ["--skill", "superpowers:brainstorming", "--advice", "hi"],
        )
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_match_emits_additional_context(self):
        stdin = json.dumps(
            {"tool_name": "Skill", "tool_input": {"skill": "x"}}
        )
        code, out = run_helper(
            stdin, ["--skill", "x", "--advice", "do the thing"]
        )
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(
            payload,
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "additionalContext": "do the thing",
                }
            },
        )

    def test_if_file_missing_exits_silently(self):
        with tempfile.TemporaryDirectory() as tmp:
            stdin = json.dumps(
                {"tool_name": "Skill", "tool_input": {"skill": "x"}, "cwd": tmp}
            )
            code, out = run_helper(
                stdin,
                ["--skill", "x", "--if-file", "missing.md", "--advice", "hi"],
            )
            self.assertEqual(code, 0)
            self.assertEqual(out, "")

    def test_if_file_present_relative_emits_advice(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "found.md").write_text("here")
            stdin = json.dumps(
                {"tool_name": "Skill", "tool_input": {"skill": "x"}, "cwd": tmp}
            )
            code, out = run_helper(
                stdin,
                ["--skill", "x", "--if-file", "found.md", "--advice", "hi"],
            )
            self.assertEqual(code, 0)
            payload = json.loads(out)
            self.assertEqual(
                payload["hookSpecificOutput"]["additionalContext"], "hi"
            )

    def test_if_file_absolute_path(self):
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            stdin = json.dumps(
                {"tool_name": "Skill", "tool_input": {"skill": "x"}}
            )
            code, out = run_helper(
                stdin,
                ["--skill", "x", "--if-file", tmp_path, "--advice", "hi"],
            )
            self.assertEqual(code, 0)
            payload = json.loads(out)
            self.assertEqual(
                payload["hookSpecificOutput"]["additionalContext"], "hi"
            )
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_missing_required_args_errors(self):
        # argparse exits 2 on missing required args, prints to stderr.
        # The hook will degrade silently because the wrapper command should
        # be configured correctly, but the script itself should fail loudly
        # on misconfiguration to surface bad settings.json entries during
        # development.
        proc = subprocess.run(
            [sys.executable, str(SCRIPT)],
            input="",
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(proc.returncode, 0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail (skill-advice.py does not exist yet)**

Run: `python3 -m unittest plugins/stay-principled/scripts/test_skill_advice.py -v`

Expected: All tests fail or error because `plugins/stay-principled/scripts/skill-advice.py` does not exist. Common failure: `FileNotFoundError` from the subprocess invocation, surfaced as test errors.

- [ ] **Step 3: Commit (red phase)**

```bash
git add plugins/stay-principled/scripts/test_skill_advice.py
git commit -m "test(stay-principled): add skill-advice helper tests

Tests for tool/skill matching, JSON output shape, file-existence guard
(relative and absolute paths), unparseable/empty stdin handling, and
missing-arg errors. Tests fail until the next commit adds the helper.

Per superpowers TDD: red commit first, then green."
```

---

## Task: helper-implementation

Implement `scripts/skill-advice.py` to satisfy the tests from the previous task. Stdlib only. Argparse for the CLI; json for stdin parsing and stdout emission.

**Files:**
- Create: `plugins/stay-principled/scripts/skill-advice.py`

- [ ] **Step 1: Write the helper implementation**

Create `plugins/stay-principled/scripts/skill-advice.py`:

```python
#!/usr/bin/env python3
"""Conditional advice emitter for PreToolUse hooks on the Skill tool.

Reads the PreToolUse JSON payload from stdin. If tool_name is "Skill" and
tool_input.skill matches --skill, optionally checks --if-file (resolved
against payload.cwd or os.getcwd() if relative), and on success emits
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": ...}}
to stdout. Any non-match exits 0 silently. Misconfiguration (missing
required args) exits non-zero so settings.json mistakes surface during
development.

Wired in settings.json via:

    {
      "hooks": {
        "PreToolUse": [{
          "matcher": "Skill",
          "hooks": [{
            "type": "command",
            "command": "python3 \\"${CLAUDE_PLUGIN_ROOT}/scripts/skill-advice.py\\" --skill <name> --advice <text>"
          }]
        }]
      }
    }
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Conditional advice emitter for Skill PreToolUse hooks.",
    )
    parser.add_argument("--skill", required=True, help="Target skill name to match.")
    parser.add_argument(
        "--if-file",
        dest="if_file",
        help="Optional path. Skip emission if the file does not exist.",
    )
    parser.add_argument(
        "--advice",
        required=True,
        help="Text emitted as additionalContext when the match succeeds.",
    )
    args = parser.parse_args(argv)

    raw = sys.stdin.read()
    if not raw.strip():
        return 0
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return 0

    if not isinstance(payload, dict):
        return 0
    if payload.get("tool_name") != "Skill":
        return 0

    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return 0
    if tool_input.get("skill") != args.skill:
        return 0

    if args.if_file:
        cwd = payload.get("cwd") or os.getcwd()
        candidate = Path(args.if_file)
        if not candidate.is_absolute():
            candidate = Path(cwd) / candidate
        if not candidate.exists():
            return 0

    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": args.advice,
        }
    }
    print(json.dumps(output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Make the helper executable (defensive, in case someone invokes it directly)**

```bash
chmod +x plugins/stay-principled/scripts/skill-advice.py
```

- [ ] **Step 3: Run the tests and verify they all pass**

Run: `python3 -m unittest plugins/stay-principled/scripts/test_skill_advice.py -v`

Expected: 9 tests pass (8 behavioral tests + 1 missing-arg test).

If any fail, fix the implementation. Do not modify the tests.

- [ ] **Step 4: Smoke-test the helper manually**

Run:

```bash
echo '{"tool_name": "Skill", "tool_input": {"skill": "superpowers:brainstorming"}}' \
  | python3 plugins/stay-principled/scripts/skill-advice.py \
      --skill superpowers:brainstorming \
      --advice "principles configured: consider grilling first"
```

Expected stdout:

```json
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": "principles configured: consider grilling first"}}
```

Run again with a non-matching skill and confirm no output:

```bash
echo '{"tool_name": "Skill", "tool_input": {"skill": "other"}}' \
  | python3 plugins/stay-principled/scripts/skill-advice.py \
      --skill superpowers:brainstorming \
      --advice "should not appear"
```

Expected: empty stdout, exit code 0.

- [ ] **Step 5: Commit (green phase)**

```bash
git add plugins/stay-principled/scripts/skill-advice.py
git commit -m "feat(stay-principled): implement skill-advice hook helper

Stdlib-only Python script. Reads PreToolUse JSON from stdin, filters
on tool_name=Skill and tool_input.skill matching --skill, optionally
guards on --if-file existence, emits hookSpecificOutput.additionalContext
JSON. All tests from the previous commit now pass.

Generic by design: nothing plugin-specific. Other plugins can use
the same helper for any 'when this skill is invoked, suggest X' pattern."
```

---

## Task: helper-contract-doc

Document the helper's contract so other plugins can reuse it without reading the source.

**Files:**
- Create: `plugins/stay-principled/docs/helper-contract.md`

- [ ] **Step 1: Write the helper contract document**

Create `plugins/stay-principled/docs/helper-contract.md`:

```markdown
# `skill-advice` helper contract

`scripts/skill-advice.py` is a generic conditional-advice emitter for Claude Code PreToolUse hooks targeting the `Skill` tool. Nothing in it is plugin-specific; other plugins can wire it into their own hooks.

## Invocation

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/skill-advice.py" \
  --skill <name> \
  [--if-file <path>] \
  --advice <text>
```

## Behavior

| Condition | Result |
|---|---|
| stdin unparseable or empty | exit 0, no output |
| `tool_name` != `Skill` | exit 0, no output |
| `tool_input.skill` != `--skill` value | exit 0, no output |
| `--if-file` given and file does not exist | exit 0, no output |
| All checks pass | emit `hookSpecificOutput` JSON, exit 0 |
| Required args missing (`--skill`, `--advice`) | exit non-zero (argparse), error to stderr |

The non-zero exit on missing args is intentional — settings.json misconfigurations should surface during development, not fail silently in production.

## Path resolution for `--if-file`

- Absolute path → used as-is.
- Relative path → resolved against `cwd` from the stdin payload, or `os.getcwd()` as fallback.

This means a single user-level hook in `~/.claude/settings.json` with `--if-file docs/agents/principles.md` will fire only in projects that have that file at their root, regardless of which project is active.

## Output shape

When all conditions match, stdout is exactly:

```json
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": "<--advice text>"}}
```

Per Claude Code's hook documentation, `additionalContext` from PreToolUse hooks is injected as system-reminder-style context for the model's next turn. It does not block the call (`permissionDecision: "deny"` would do that). The model sees the advice and can act on it; the original Skill call still proceeds.

See the [Claude Code hooks reference](https://code.claude.com/docs/en/hooks.md) for the full schema.

## Reusability

To use this helper from another plugin, invoke it with a path that resolves to this plugin's cache directory:

```bash
python3 "$HOME/.claude/plugins/cache/pickled-claude-plugins/stay-principled/latest/scripts/skill-advice.py" ...
```

The contract is stable. Future versions will not change argument names or output shape without a major version bump.
```

- [ ] **Step 2: Commit**

```bash
git add plugins/stay-principled/docs/helper-contract.md
git commit -m "docs(stay-principled): document skill-advice helper contract

Contract reference for other plugins that want to reuse the helper.
Covers invocation, behavior table, path resolution rules, output shape,
and reusability guidance."
```

---

## Task: setup-skill

Write the `stay-principled:setup` skill that scaffolds project configuration. Mattpocock-style: explore, present, confirm, write. `disable-model-invocation: true` so it only runs when the user explicitly asks.

**Files:**
- Create: `plugins/stay-principled/skills/setup/SKILL.md`

- [ ] **Step 1: Write the setup skill**

Create `plugins/stay-principled/skills/setup/SKILL.md`:

```markdown
---
name: stay-principled:setup
description: Scaffolds principle-anchoring configuration for a project. Writes docs/agents/principles.md, adds an `### Principles` block to `## Agent skills` in CLAUDE.md or AGENTS.md, and optionally drafts hook integration snippets for settings.json or tool-routing. Run once per project before using stay-principled:grill. Re-run only if the principles file layout changes.
disable-model-invocation: true
---

# Setup Principles

Scaffold the per-project configuration that `stay-principled:grill` reads. This is a prompt-driven skill, not a deterministic script. Explore, present what you found, confirm with the user, then write.

## Process

### 1. Explore

Look at the current repo to understand its starting state. Read whatever exists; don't assume:

- `docs/principles.md`, `docs/ops-principles.md`, any sibling `*principles*.md` files at the repo root or under `docs/`
- `docs/agents/principles.md` — existing config; update in place if found
- `CLAUDE.md` (preferred) or `AGENTS.md` at the repo root — does either exist? Is there already an `## Agent skills` section?
- `claude plugin list --json` — is `tool-routing` installed and enabled? (Affects whether Pattern C is offered.)
- `git rev-parse --show-toplevel` — used as the canonical repo root for path resolution; principles inside worktrees still live at the worktree root.

### 2. Present findings and ask

Summarize what's present and what's missing. Then walk the user through the four sections **one at a time** — present a section, get the user's answer, then move to the next. Don't dump all sections at once.

Assume the user does not know what these terms mean. Each section starts with a short explainer (what it is, why this skill needs it, what changes if they pick differently).

**Section A — Where do principles live?**

> Explainer: The `stay-principled:grill` skill needs to know which markdown files contain your principles. Most projects have one (`docs/principles.md`); some split into multiple (e.g. engineering vs ops). The skill reads all of them at session start to build a working set.

Default posture: list any `*principles*.md` files found during exploration. Ask the user to confirm or describe a different layout. Multi-file is fine.

**Section B — Format hint.**

> Explainer: This is a free-form description of how the principles are structured in your file. The skill uses this to reason about cross-references, correction cases, and domain-specific sections. The format is not a schema — the skill is format-tolerant — but a description helps it reason better.

Default detection: skim the first 50 lines of the principles file. If it has numbered cross-cutting principles with bold names, "Why:" and "Where:" sections, propose:

> "Numbered cross-cutting principles with **bold name**, statement, Why:, and Where: sections. Domain-specific principles under `## Domain-specific principles`. Cross-references between principles by number. Correction cases embedded in `Where:` sections."

If the format is simpler (bullets, plain headers), describe what you see and let the user adjust.

**Section C — Domain map (optional).**

> Explainer: Some principles only apply to specific subsystems (e.g. PRM, Tasks). The domain map tells the skill which directories trigger which principle subsets, so it can pull in domain-specific principles when the topic is in a named domain.

If the principles file has a `## Domain-specific principles` section (or similar), propose a mapping by reading the section headings and looking for matching directories under `src/` or similar. Otherwise skip this section entirely.

**Section D — Hook integration (optional, opt-in).**

> Explainer: By default, you invoke `stay-principled:grill` manually. Hook integration makes other skills (typically `superpowers:brainstorming`) suggest grilling first when this project has principles configured. Three patterns are available; pick zero, one, or multiple.

Present the three patterns. The user can decline all of them — the runtime skill works fine without integration.

- **Pattern A — CLAUDE.md prose.** Soft, model-driven. A line added to CLAUDE.md telling the model to consider grilling first.
- **Pattern B — Hook helper.** Hard, deterministic. A `settings.json` snippet that fires `skill-advice` on every `superpowers:brainstorming` invocation.
- **Pattern C — tool-routing rule.** Hard, deterministic. Only offered if `tool-routing` is installed.

For each chosen pattern, draft the snippet. See the project [`docs/integration-patterns.md`](../../docs/integration-patterns.md) for the templates.

### 3. Draft and confirm

Show the user a draft of:

- The contents of `docs/agents/principles.md`
- The `### Principles` block to add to whichever of `CLAUDE.md` / `AGENTS.md` is being edited
- Pattern A snippet (if chosen) — appended to CLAUDE.md as a routing line
- Pattern B snippet (if chosen) — printed for paste into `settings.json`. Do not auto-write `settings.json`.
- Pattern C snippet (if chosen) — printed for paste into a tool-routing routes file. Do not auto-write.

Let the user edit before writing.

### 4. Write

**Pick the file to edit:**

- If `CLAUDE.md` exists, edit it.
- Else if `AGENTS.md` exists, edit it.
- If neither exists, ask the user which one to create — don't pick for them.

Never create `AGENTS.md` when `CLAUDE.md` already exists (or vice versa) — always edit the one that's already there.

If an `## Agent skills` block already exists, add the `### Principles` subsection in-place. Don't append a duplicate. Don't overwrite user edits to surrounding sections.

The block:

```markdown
## Agent skills

### Principles

[one-line summary of where principles live]. See `docs/agents/principles.md` for format and configuration. The `stay-principled:grill` skill reads from these files.
```

Then write `docs/agents/principles.md` using this template:

```markdown
# Principles configuration

## Files
- [path to first principles file]
- [path to second, if any]

## Format
[user-confirmed format description from Section B]

## Domain map
[domain → directory mappings from Section C, or omit if skipped]

## Skip patterns
[branch-name or path patterns where principle anchoring should be skipped, or omit]
```

Pattern A/B/C snippets: write Pattern A inline into CLAUDE.md (append a routing line at the end of the agent-skills block). Print Pattern B and Pattern C snippets for the user to paste manually.

### 5. Done

Tell the user:

1. Setup is complete.
2. Which files were written.
3. That `stay-principled:grill` will now read from `docs/agents/principles.md`.
4. That re-running this skill is only needed if the file layout changes; manual edits to `docs/agents/principles.md` are fine.

If integration patterns were offered, remind the user to paste any Pattern B/C snippets into the appropriate config file.
```

- [ ] **Step 2: Commit**

```bash
git add plugins/stay-principled/skills/setup/SKILL.md
git commit -m "feat(stay-principled): add stay-principled:setup skill

One-shot configuration scaffold for projects that want principle
anchoring. Mattpocock-style flow: explore, present sections one at a
time, confirm, write. disable-model-invocation: true so it only runs
when the user explicitly asks.

Writes docs/agents/principles.md and an Agent skills block in
CLAUDE.md/AGENTS.md. Optionally drafts integration snippets for
Pattern A (CLAUDE.md prose), Pattern B (settings.json hook), or
Pattern C (tool-routing rule). settings.json and tool-routing
snippets are printed, not auto-written, given their blast radius."
```

---

## Task: runtime-skill

Write the `stay-principled:grill` skill — the core runtime. Reads the config from `stay-principled:setup`, shortlists relevant principles for the topic, walks depth-first with recommended answers, surfaces conflicts emergently, outputs a brief.

**Files:**
- Create: `plugins/stay-principled/skills/grill/SKILL.md`

- [ ] **Step 1: Write the runtime skill**

Create `plugins/stay-principled/skills/grill/SKILL.md`:

```markdown
---
name: stay-principled:grill
description: Walk a depth-first decision tree anchored to a project's documented principles before brainstorming opens options. Reads docs/agents/principles.md (or probes docs/principles.md and docs/ops-principles.md directly), shortlists principles relevant to the topic, asks one question at a time with a recommended answer per question, surfaces conflicts emergently, and outputs a brief that downstream brainstorming or planning can consume. Use when starting design work and the project has principles documented; redirects to stay-principled:setup otherwise. Auto-routes from phrases like "grill me with principles", "anchor this to the principles", "what principles bear on this".
---

# Grill with Principles

Walk a depth-first decision tree using the project's principles as the tree roots, before brainstorming opens. The mechanism is grill-me's: one question at a time, recommended answer per node, explore the codebase instead of asking when the answer is there. The anchor is principles, not generic decisions.

## Why this exists

Brainstorming-style breadth-first menus drag conversations toward implementation variants. Depth-first walking with principle anchoring stays at the *why* level. Principles loaded as upfront context are necessary but not sufficient — they need to act as a forcing function during decision moments, not as wallpaper.

## Process

### 1. Discover principles

- Read `docs/agents/principles.md` if it exists. This is the canonical config written by `stay-principled:setup`.
- Otherwise probe `docs/principles.md` and `docs/ops-principles.md` directly.
- Resolve all paths against `git rev-parse --show-toplevel` so worktree invocations find the right files.
- If nothing is found, ask: *"No principles configured. Skip principle-anchoring, or run `stay-principled:setup` first?"* and exit cleanly. Do not pretend to grill without principles — the whole point is anchoring.

### 2. Read and shortlist

- Read all configured principle files into your working set.
- Based on the user's stated topic and visible context (recent commits, branch name, files mentioned, current cwd), propose a shortlist by number and name.
- Cite by number AND name so the user can react fast: *"I think principles 3 (agent proposes), 4 (capture vs triage), and 9 (resilience) bear on this. Anything I'm missing?"*
- If the topic touches a named domain in the domain map, include the domain-specific principles for that domain.
- Wait for the user to confirm, add, or remove before moving on.

### 3. Confirm and walk

Walk the shortlist depth-first, one principle at a time.

For each principle:
- Frame the question that would make this principle bite for the current design. Don't ask abstract questions — ask the concrete one this principle implies.
- Provide a recommended answer, drawing from the `Where:` examples in the principles file when relevant. If the principles file has correction cases for this principle, mention them as part of the recommendation when relevant.
- Wait for the user to confirm, adjust, or reject.
- One question at a time. Never present a menu.
- Cite the principle by number explicitly so cross-references stay easy: *"Per #3..."*

Carry constraints forward. An answer to a principle 3 question constrains follow-up principle 9 questions. Don't re-ask what's already settled.

### 4. Surface conflicts emergently

When two principles pull opposite ways on the same decision, surface the conflict explicitly. Do **not** recommend a resolution. These are exactly the kind of question that needs the user's judgment, not the agent's.

Example conflicts the brineworks file already shows:
- #5 "defer until concrete need" vs #4 "capture is frictionless" — capture features get built before they're "needed".
- #13 "design ceremony matches deployment model" vs any principle that imports multi-user discipline.

Frame: *"#5 says defer, #4 says capture. Which dominates here?"*

### 5. Cite correction cases

When the principles file has correction-case entries (e.g. `Where:` mentions like "Disposition rework is a correction case for #8"), surface them when the topic resembles the original violation pattern. Don't just cite — ask whether the same shape applies:

> "Principle 8 had a leak in disposition rework where mutation logic ended up in skill prose. Does the same pattern apply to what we're discussing?"

### 6. Output the brief

When the tree is walked or visibly stabilized, synthesize a brief inline:

```
## Principle brief: <topic>

**Anchored to:** principles 3, 4, 9

**Resolved:**
- Per #3: agent proposes, human confirms at the X boundary
- Per #4: capture lands raw at Y; filtering happens in triage step Z

**Open at brainstorm time:** ...

**Honored constraints:** ...

**Active conflicts (need user resolution):** ...
```

Always output inline. Offer to write to `docs/plans/YYYY-MM-DD-<topic>-principle-brief.md` when the brief is non-trivial. Never auto-write — the brief is a starting point, and the user may want to edit it before downstream skills consume it.

## Mode rules (carried from grill-me)

- One question at a time. Never present a menu.
- Always include a recommended answer, except when surfacing a principle conflict.
- Explore the codebase or principles file instead of asking when the answer is there.
- Stay at the intent level. If the user pulls toward implementation, redirect:

  > "That's a brainstorming question. Want to settle the principle 3 boundary first, or jump?"

- Cite principles by number, always. The numbering is the lingua franca that makes cross-references and correction-case citations cheap.

## What this skill does not do

- Generate option menus. That's `superpowers:brainstorming`'s job, downstream.
- Recommend resolutions to principle conflicts.
- Write or amend the principles file. That's a future capture-side skill (`principle-sweep`), out of scope for v1.
- Handle non-markdown principle files. The skill is format-tolerant for markdown but does not parse other formats.
```

- [ ] **Step 2: Commit**

```bash
git add plugins/stay-principled/skills/grill/SKILL.md
git commit -m "feat(stay-principled): add stay-principled:grill runtime skill

Depth-first decision-tree walker anchored to project principles.
Reads docs/agents/principles.md (or probes docs/principles.md
directly), shortlists relevant principles per topic, walks one
question at a time with recommended answers, surfaces conflicts
emergently without resolving them, cites correction cases when
patterns recur, outputs an inline brief.

Mechanism is grill-me's; the anchor is principles, not generic
decisions. The skill exits cleanly when no principles are
configured rather than degrading into unprincipled grilling."
```

---

## Task: integration-patterns-doc

Write the integration-patterns reference document. This is what `stay-principled:setup` Section D pulls templates from, and what users read directly to add new integration points.

**Files:**
- Create: `plugins/stay-principled/docs/integration-patterns.md`

- [ ] **Step 1: Write the integration patterns document**

Create `plugins/stay-principled/docs/integration-patterns.md`:

```markdown
# Integration patterns

`stay-principled:grill` works fine without any integration — invoke it manually whenever you start design work. These patterns make other skills (typically `superpowers:brainstorming`) suggest grilling first when this project has principles configured.

All three patterns are optional. Pick zero, one, or multiple. They compose; using multiple is harmless because each is idempotent.

## Pattern A — CLAUDE.md prose

Soft, model-driven. A line added to `CLAUDE.md` telling the model to consider grilling first.

**Where:** Append to the `### Principles` subsection in CLAUDE.md's `## Agent skills` block.

**Snippet:**

```markdown
For design conversations or when invoking brainstorming on non-trivial topics, invoke `stay-principled:grill` first if `docs/agents/principles.md` exists.
```

**Pros:** Zero infrastructure. Works anywhere CLAUDE.md is loaded into context.
**Cons:** Model may ignore it. Not deterministic.

## Pattern B — Bundled hook helper

Hard, deterministic. A `settings.json` PreToolUse hook that fires `skill-advice` whenever `superpowers:brainstorming` is invoked, emitting advice as `additionalContext`.

**Where:** Add to one of (precedence is standard Claude Code order):

| Layer | Path | Use |
|---|---|---|
| User | `~/.claude/settings.json` | Universal across all projects |
| Project | `<project>/.claude/settings.json` | Project-specific, checked into git |
| Local | `<project>/.claude/settings.local.json` | Per-machine or per-worktree, gitignored |

**Snippet (user-level example with `--if-file` guard):**

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Skill",
        "hooks": [{
          "type": "command",
          "command": "python3 \"$HOME/.claude/plugins/cache/pickled-claude-plugins/stay-principled/latest/scripts/skill-advice.py\" --skill superpowers:brainstorming --if-file docs/agents/principles.md --advice 'Principles configured for this project. Consider stay-principled:grill first to anchor the why before generating options.'"
        }]
      }
    ]
  }
}
```

The `--if-file docs/agents/principles.md` guard means this user-level hook fires only in projects that have principles configured. That's the per-project layering achieved through standard mechanisms — no plugin-internal config needed.

**Pros:** Bites every time. Works without other plugins.
**Cons:** Requires user to maintain `settings.json` entries. Path to the helper depends on where the plugin cache lives.

**Helper contract:** see [`helper-contract.md`](helper-contract.md) for full reference.

## Pattern C — tool-routing rule

Hard, deterministic. Uses the existing `tool-routing` plugin's PreToolUse interception rather than a fresh hook.

**Requires:** `tool-routing` plugin installed and enabled.

**Where:** A route file readable by tool-routing (typically `plugins/tool-routing/scripts/tool-routes.yaml` or a per-project routes file).

**Snippet:**

```yaml
- name: brainstorm-suggests-stay-principled
  tool: Skill
  pattern: 'superpowers:brainstorming'
  message: "If docs/agents/principles.md exists, consider stay-principled:grill first to anchor the why."
```

**Pros:** Integrates with existing tool-routing config; centralized place to manage all routing rules.
**Cons:** Requires that plugin and its discovery layer.

## Choosing among patterns

- **Just want it to work?** Pattern A. Done in one line.
- **Want determinism?** Pattern B. The model has no choice but to see the advice.
- **Already use tool-routing for everything?** Pattern C. Keeps your routing rules consolidated.
- **Don't care?** Skip all three. Invoke `stay-principled:grill` manually.
```

- [ ] **Step 2: Commit**

```bash
git add plugins/stay-principled/docs/integration-patterns.md
git commit -m "docs(stay-principled): document the three integration patterns

Reference for users wiring stay-principled:grill into other skills'
flows. Pattern A (CLAUDE.md prose, soft), Pattern B (settings.json
hook with skill-advice helper, hard), Pattern C (tool-routing rule,
hard, requires that plugin). All three optional and composable."
```

---

## Task: readme-finalization

Replace the README stub with a complete plugin overview. Covers what the plugin does, why it exists, how to install, how to use both skills, and links to the helper contract and integration patterns docs.

**Files:**
- Modify: `plugins/stay-principled/README.md`

- [ ] **Step 1: Replace the README with the full version**

Overwrite `plugins/stay-principled/README.md` with:

```markdown
# principles

Anchor design conversations to a project's documented principles via depth-first grilling before brainstorming opens.

## Why

If your project has a `docs/principles.md` file, you've already done the hard work of articulating *why* decisions land where they do. But principles loaded as upfront context don't necessarily *bite* during design moments. Brainstorming sessions still surface low-level option menus instead of anchoring choices to the principles.

This plugin closes that gap. It applies grill-me's depth-first decision-tree walking with principles as the tree roots, before brainstorming opens. The result: brainstorming starts at the right altitude with most options already constrained or ruled out.

## What's in here

| Component | Purpose |
|---|---|
| `stay-principled:setup` skill | One-shot config scaffolder. Run once per project. |
| `stay-principled:grill` skill | Runtime grilling. Invoke at the start of design work. |
| `scripts/skill-advice.py` | Generic Python helper for PreToolUse hooks. Used by Pattern B integration. Reusable from other plugins. |

## Install

```bash
/plugin install stay-principled@pickled-claude-plugins
```

Restart Claude Code after install (per the marketplace's directory-source caching).

## Quick start

In a project that has principles documented (a `docs/principles.md` or similar markdown file):

1. **Configure once:**

   ```
   /skill stay-principled:setup
   ```

   Walks you through where principles live, format hints, optional domain map, and optional integration patterns. Writes `docs/agents/principles.md` and adds an `### Principles` subsection to your CLAUDE.md.

2. **Use whenever you start design work:**

   ```
   /skill stay-principled:grill
   ```

   Or just say "grill me with principles on this" / "anchor this to the principles" / similar.

## Using without setup

`stay-principled:grill` works without setup if `docs/principles.md` exists at the repo root. Setup adds nuance (domain map, format hints, integration). Skip setup if you just want quick grilling on a one-off project.

## Integration with other skills

The plugin offers three optional ways to make `superpowers:brainstorming` (or any other skill) suggest grilling first:

- **Pattern A** — CLAUDE.md prose. Soft, model-driven.
- **Pattern B** — Bundled hook helper (`skill-advice`). Hard, deterministic.
- **Pattern C** — `tool-routing` rule. Hard, requires that plugin.

See [`docs/integration-patterns.md`](docs/integration-patterns.md) for full templates and tradeoffs.

## Reusing the helper

The `scripts/skill-advice.py` helper is generic — nothing plugin-specific about it. Other plugins can wire it into their own PreToolUse hooks for "when this skill is invoked, suggest also doing X" patterns.

See [`docs/helper-contract.md`](docs/helper-contract.md) for the contract.

## What this plugin does not do (v1)

- Capture-side workflow (post-implementation principle sweeps, principle amendments). The existing manual workflow stays.
- Principles file format validation. The plugin is format-tolerant for markdown.
- Auto-detection of relevant principles in every tool call. Grilling is invoked per design conversation, not as a continuous backseat driver.

## Contributing

This plugin lives in [`pickled-claude-plugins`](https://github.com/technicalpickles/pickled-claude-plugins). PRs welcome.
```

- [ ] **Step 2: Verify the README links resolve correctly**

Run: `ls plugins/stay-principled/docs/integration-patterns.md plugins/stay-principled/docs/helper-contract.md`

Expected: both files exist (created in earlier tasks).

- [ ] **Step 3: Commit**

```bash
git add plugins/stay-principled/README.md
git commit -m "docs(stay-principled): expand README with full overview

Replaces the stub from plugin-scaffold. Covers what the plugin does,
why, install, quick start (with and without setup), the three
integration patterns at a glance, helper reusability, and v1
non-goals. Links to helper-contract.md and integration-patterns.md."
```

---

## Self-review

After completing all tasks above, run through this checklist before marking the plan done.

### Spec coverage

Skim each major section of the spec at [`docs/plans/2026-05-09-principles-plugin-design.md`](2026-05-09-principles-plugin-design.md). Each section should map to a task:

| Spec section | Implementing task(s) |
|---|---|
| Plugin layout | `plugin-scaffold` |
| `stay-principled:setup` skill | `setup-skill` |
| `stay-principled:grill` skill | `runtime-skill` |
| Helper `skill-advice.py` | `helper-tests`, `helper-implementation` |
| Helper "Why this output shape" | `helper-contract-doc` |
| Configuration model (three layers) | `integration-patterns-doc` (Pattern B section), `setup-skill` (Section D) |
| Integration patterns (A/B/C) | `integration-patterns-doc`, `setup-skill` |
| Edge cases (worktrees, no-principles, conflicts, correction cases) | `runtime-skill` (process steps 1, 4, 5) |
| Verification approach | This self-review section + manual smoke tests in `helper-implementation` step 4 |

### Placeholder scan

Search the plan for these patterns and remove or replace:

- `TBD`, `TODO`, "implement later", "fill in details" — none should appear.
- "Add appropriate error handling" or similar — every error path is explicit (helper exits 0 silently for non-matches).
- "Write tests for the above" without tests — `helper-tests` contains the full test code.
- "Similar to Task N" — every task is self-contained.

### Type / path / name consistency

Verify across tasks:

- Helper script path is `plugins/stay-principled/scripts/skill-advice.py` everywhere. (Tests reference it via `Path(__file__).parent / "skill-advice.py"`.)
- Helper test path is `plugins/stay-principled/scripts/test_skill_advice.py` everywhere.
- Skill paths: `plugins/stay-principled/skills/setup/SKILL.md` and `plugins/stay-principled/skills/grill/SKILL.md`.
- Doc paths: `plugins/stay-principled/docs/helper-contract.md` and `plugins/stay-principled/docs/integration-patterns.md`.
- Output JSON shape `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": "..."}}` is identical in tests, implementation, helper-contract doc, and integration-patterns doc.
- Skill description triggers in `grill/SKILL.md` match the auto-route phrasing in the spec.
- Marketplace.json entry uses `"version": "0.1.0"` consistently.

### Final verification (after all tasks committed)

- [ ] All tests pass: `python3 -m unittest plugins/stay-principled/scripts/test_skill_advice.py -v`
- [ ] Marketplace entry parses: `jq '.plugins[] | select(.name == "principles")' .claude-plugin/marketplace.json`
- [ ] Plugin manifest parses: `jq '.' plugins/stay-principled/.claude-plugin/plugin.json`
- [ ] All commits use valid scopes (`feat(stay-principled):`, `test(stay-principled):`, `docs(stay-principled):`).
- [ ] No `TBD`/`TODO`/placeholder strings in any file under `plugins/stay-principled/`.
- [ ] Smoke-test the helper end-to-end (Step 4 of `helper-implementation` task).

---

## Open questions / followups (post-implementation)

These are not blockers for v1 but worth noting once the plugin is in use:

- **Capture-side skill (v2).** A `principle-sweep` skill that runs post-implementation, walks the just-shipped change, and suggests principle amendments. Worth designing once apply has been used in earnest for a few weeks.
- **Default integration pattern.** Setup currently offers all three. After real use, a default ranking may emerge.
- **Principles file watcher.** When `docs/principles.md` changes, no machinery currently invalidates a previously-issued brief. Briefs are inline ephemera, so this only matters for the optional file-write path.
- **Cross-machine config sharing.** If user-level `settings.json` grows unwieldy with multiple `--if-file`-guarded hooks, a `~/.claude/principles-config.json` could centralize per-project overrides. Not built until pain shows up.
