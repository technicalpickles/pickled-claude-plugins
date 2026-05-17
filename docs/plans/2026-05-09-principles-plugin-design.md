# Principles Plugin Design

> **For Claude:** Next step is `superpowers:writing-plans` to break this into an implementation plan.

**Goal:** Build a `pickled-claude-plugins` plugin that anchors design conversations to a project's documented principles by walking a depth-first decision tree before brainstorming generates option menus.

**Architecture:** Two skills (`stay-principled:setup`, `stay-principled:grill`) plus one helper command (`skill-advice`). Setup writes a contract file (`docs/agents/principles.md`) following the mattpocock convention. Runtime skill reads that contract, shortlists relevant principles for the topic, and grills depth-first with recommended answers, then synthesizes a brief that downstream brainstorming/planning consumes. Helper is a generic Python conditional advice emitter for `settings.json` hooks.

**Tech Stack:** Python 3 (stdlib only) for the helper. Markdown for skills and config. No external dependencies.

---

## Background

The brineworks (pickled-finances) project has a substantial `docs/principles.md` file: 14 cross-cutting principles plus domain-specific ones, each structured as **statement / Why / Where / cross-references / correction-cases**. cq queries show the file is read in 50+ tool calls across 27+ sessions, predominantly during context restoration (unpark), task triage, design conversations, and implementation kickoffs.

Despite being loaded as upfront context, principles don't *bite*: brainstorming sessions still surface low-level option menus instead of anchoring choices to the principles. Reading principles into context is necessary but not sufficient. They need to act as a forcing function during decision moments.

### Why the gap exists

`grill-me` (upstream from mattpocock/skills) uses depth-first decision-tree walking with recommended answers per node. It naturally stays at the *why* level. `brainstorming` (upstream from superpowers-marketplace) uses breadth-first option menus, which forces enumeration of concrete variants and drags conversations downward. Both can run at any altitude, but breadth-first menus *force* implementation-coloured framing.

Principles are well-suited to depth-first walking: each principle is itself a tree root with sub-questions. The fix is to apply grill-me's mechanism with principles as the anchors, *before* brainstorming opens.

### Capture vs apply

The brineworks workflow already has working principle capture: principles get added when design calls crystallize them, and amended when violations are caught (the file's "correction case" entries trace this). A "doc-principle-sweep" runs post-implementation per CONVENTIONS #5. Capture is not greenfield and not the priority.

This spec covers the **apply side** only. Capture-side tooling is out of scope for v1.

---

## Plugin layout

```
plugins/stay-principled/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   ├── setup/
│   │   └── SKILL.md
│   └── grill/
│       └── SKILL.md
├── scripts/
│   └── skill-advice.py
├── README.md
└── docs/
    ├── integration-patterns.md
    └── helper-contract.md
```

Mirrors existing plugin structure in this repo (commands flat, skills nested, hooks/scripts as Python). No `pyproject.toml` needed. The helper script runs via `python3` directly to avoid uv cold-start latency on every Skill invocation.

---

## Skill: `stay-principled:setup`

One-shot configuration scaffolding. `disable-model-invocation: true` (run only when user explicitly asks).

### Process

1. **Explore.**
   - Look for `docs/principles.md`, `docs/ops-principles.md`, any sibling `*principles*.md` files.
   - Check `docs/agents/principles.md` (existing config; update in place if found).
   - Read `CLAUDE.md` (preferred) or `AGENTS.md` for an existing `## Agent skills` block.
   - Check `claude plugin list` for tool-routing.

2. **Present and ask one section at a time** (mattpocock pattern: explainer then question):

   - **Section A — Where do principles live?** Default: any `*principles*.md` files found. Allow multi-file selection. User can describe a different layout.
   - **Section B — Format hint.** Detect: numbered + Why + Where (brineworks shape) or simpler. User confirms or briefly describes their format.
   - **Section C — Domain map (optional).** If principles file has a `## Domain-specific principles` section, propose the mapping. Skip otherwise.
   - **Section D — Hook integration (optional, opt-in).** Offer Pattern A (CLAUDE.md prose), Pattern B (settings.json hook), Pattern C (tool-routing rule, only if detected). User can pick zero, one, or multiple. None of these are required for the runtime skill to work.

3. **Draft and confirm.** Show the user:
   - `docs/agents/principles.md` (full content, will be written)
   - The `### Principles` block to add to CLAUDE.md/AGENTS.md (full content, will be written)
   - Pattern A snippet (if chosen): appended to CLAUDE.md
   - Pattern B snippet (if chosen): *printed* for the user to paste into `settings.json`. High-blast-radius, never auto-written.
   - Pattern C snippet (if chosen): *printed* for paste into a tool-routing routes file.

   Let the user edit before any writes.

4. **Write.**
   - `docs/agents/principles.md`: written.
   - `CLAUDE.md` (or `AGENTS.md`): `### Principles` subsection added to `## Agent skills` block. In-place update if block exists. Never overwrite surrounding content.
   - Pattern B/C snippets: printed only.

5. **Done.** Tell the user setup is complete and which skills will read the config. Re-running is only needed for layout changes; manual edits to `docs/agents/principles.md` are fine.

### File: `docs/agents/principles.md`

Schema (all fields optional except `Files`):

```markdown
# Principles configuration

## Files
- docs/principles.md
- docs/ops-principles.md

## Format
Numbered cross-cutting principles with **bold name**, statement, Why:, Where: sections.
Domain-specific principles under `## Domain-specific principles`.
Cross-references between principles by number ("extends #3").
Correction cases embedded in `Where:` sections.

## Domain map
- PRM → src/brineworks_cli/prm/
- Tasks → src/brineworks_cli/tasks/

## Skip patterns
- Branches matching `chore/*`
```

### File: `CLAUDE.md` `## Agent skills` block addition

```markdown
### Principles

Principles for this project live in `docs/principles.md` and `docs/ops-principles.md`. See `docs/agents/principles.md` for format and configuration. The `stay-principled:grill` skill reads from these files.
```

---

## Skill: `stay-principled:grill`

Runtime skill. Model-invokable. Auto-routes from descriptions like "grill me with principles", "anchor this to the principles", "what principles bear on this", or when the user starts design work and `docs/agents/principles.md` exists.

### Process

1. **Discover principles.**
   - Read `docs/agents/principles.md` if it exists.
   - Otherwise probe `docs/principles.md` and `docs/ops-principles.md` directly.
   - If nothing found, ask: *"No principles configured. Skip principle-anchoring, or run `stay-principled:setup` first?"* and exit cleanly.
   - Resolve principle file paths against `git rev-parse --show-toplevel` so worktree invocations find the right files.

2. **Read and shortlist.**
   - Read all configured principle files.
   - Based on the user's stated topic and visible context (recent commits, branch name, files mentioned), propose a shortlist by number and name: *"I think principles 3 (agent proposes), 4 (capture vs triage), and 9 (resilience) bear on this. Anything I'm missing?"*
   - If the topic touches a named domain in the domain map, include domain-specific principles.

3. **Confirm and walk.** Once the shortlist is settled, walk it depth-first.

   For each principle:
   - Frame the question that would make this principle bite for the current design.
   - Provide a recommended answer, drawing from the `Where:` examples in the file when relevant.
   - Wait for the user to confirm, adjust, or reject.
   - One question at a time.
   - Cite the principle by number explicitly so cross-references are easy.

   Carry constraints forward: an answer to a principle 3 question constrains follow-up principle 9 questions. Don't re-ask what's already settled.

4. **Surface conflicts emergently.** When two principles pull opposite ways on the same decision (e.g. #5 "defer until concrete need" vs #4 "capture is frictionless"), surface the conflict explicitly. Do *not* recommend a resolution. These conflicts are exactly the kind of question that needs the user's judgment, not the agent's. *"#5 says defer, #4 says capture. Which dominates here?"*

5. **Cite correction cases.** When the principles file has correction-case entries (e.g. principle 8's "Disposition rework is a correction case…"), surface them when the topic resembles the original violation. *"Principle 8 had a leak in disposition rework. Does the same pattern apply here?"*

6. **Output the brief.** When the tree is walked or visibly stabilized, synthesize:

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

   Output inline always. Offer to write to `docs/plans/YYYY-MM-DD-<topic>-principle-brief.md` when the brief is non-trivial. Don't auto-write.

### Mode rules (carried from grill-me)

- One question at a time.
- Always include a recommended answer, except when surfacing a principle conflict.
- Explore code/principles file instead of asking when the answer is there.
- Stay at the intent level. If the user pulls toward implementation, redirect: *"That's a brainstorming question. Want to settle the principle 3 boundary first, or jump?"*

---

## Helper: `skill-advice.py`

Generic conditional advice emitter for `settings.json` PreToolUse hooks. Lives at `scripts/skill-advice.py`. Stdlib only. Fast cold start.

### Contract

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/skill-advice.py" \
  --skill <name> \
  [--if-file <path>] \
  --advice <text>
```

### Behavior

1. Read PreToolUse JSON from stdin. If unparseable → exit 0 silently.
2. If `tool_name != "Skill"` → exit 0.
3. If `tool_input.skill != --skill` value → exit 0.
4. If `--if-file` is given and the file does not exist (resolved against the `cwd` field in stdin, falling back to `os.getcwd()`) → exit 0.
5. Otherwise emit:

   ```json
   {"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": "<advice>"}}
   ```

   Exit 0.

### Why this output shape

Per Claude Code's hook documentation, `additionalContext` from PreToolUse hooks is injected as system-reminder-style context for the model's next turn. It does *not* block the call (`permissionDecision: "deny"` does that; see `tool-routing/src/tool_routing/cli.py` for that pattern). The model sees the advice and can act on it; the original Skill call still proceeds if the model chooses.

### Reusability

Nothing in `skill-advice.py` is plugin-specific. Other plugins can use it for any "when this skill is invoked, suggest also doing X" pattern. We ship it inside the principles plugin but treat the contract as stable.

---

## Configuration model

Three layers of `settings.json`, applied in standard Claude Code order:

| Layer | Path | Use |
|---|---|---|
| User | `~/.claude/settings.json` | Universal hookups across all projects |
| Project | `<project>/.claude/settings.json` | Project-specific hookups, checked into git |
| Local | `<project>/.claude/settings.local.json` | Per-machine or per-worktree overrides, gitignored |

Plugin doesn't need its own layering machinery. The `--if-file` flag on `skill-advice` lets a single user-level hook fire only in projects that have `docs/agents/principles.md`. That's the layering achieved through the standard mechanism.

Example user-level entry (`~/.claude/settings.json`):

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

---

## Integration patterns

All three optional, all three offered by `stay-principled:setup` Section D.

### Pattern A — CLAUDE.md prose

Soft, model-driven. A line added to CLAUDE.md:

> *"For design conversations or when invoking brainstorming on non-trivial topics, invoke `stay-principled:grill` first if `docs/agents/principles.md` exists."*

Pros: zero infrastructure, works anywhere CLAUDE.md is loaded.
Cons: model may ignore it; not deterministic.

### Pattern B — Bundled hook helper

Hard, deterministic. The `settings.json` snippet shown above. Installed via copy-paste; we don't auto-write `settings.json`.

Pros: bites every time; works without other plugins.
Cons: requires user to maintain `settings.json` entries.

### Pattern C — tool-routing rule

Hard, deterministic. Only offered if `tool-routing` plugin is detected.

```yaml
- name: brainstorm-suggests-stay-principled
  tool: Skill
  pattern: 'superpowers:brainstorming'
  message: "If docs/agents/principles.md exists, consider stay-principled:grill first to anchor the why."
```

Pros: integrates with existing tool-routing config.
Cons: requires that plugin and its discovery layer.

---

## Edge cases

### Domain-specific principles

The brineworks file has a `## Domain-specific principles` section with PRM and Tasks subsections. The shortlist step pulls these in when the topic is in a named domain (per the domain map in `docs/agents/principles.md`).

### Conflicting principles

Principles can pull opposite ways. The skill surfaces conflicts explicitly without recommending resolution. Two examples from the brineworks file:

- #5 "defer until concrete need" vs #4 "capture is frictionless": capture features get built before they're "needed"
- #13 "design ceremony matches deployment model" vs any principle that imports multi-user discipline

These are user-resolution moments, not agent-resolution moments. The brief records them as "Active conflicts (need user resolution)".

### Correction cases

Some principles have embedded correction cases (e.g. #8's disposition rework). When the current topic resembles the original violation pattern, the skill surfaces the correction case as a question, not just a citation: *"Principle 8 had a leak in disposition rework. Does the same pattern apply here?"*

### No-principles projects

Skill exits cleanly with a redirect to `stay-principled:setup`. No degraded mode that pretends to grill without principles. The whole point is anchoring.

### Worktree paths

When the user is in a worktree (path like `<project>/.worktrees/<branch>/...`), principles still live at `<repo-root>/docs/principles.md`. The skill resolves principle files relative to `git rev-parse --show-toplevel`, not cwd, to handle this.

### CLAUDE.md without `## Agent skills` block

Setup adds the block. Never modifies existing sections beyond the agent-skills block.

---

## Verification

V1 verification is observational, not automated:

1. **Setup smoke test:** Run `stay-principled:setup` in a temp project with no `principles.md`. Confirm it exits cleanly with the "skip or create" branch. Run again with a `principles.md` present. Confirm `docs/agents/principles.md`, CLAUDE.md block, and integration snippets are produced as designed.

2. **Runtime smoke test:** Run `stay-principled:grill` against a small known topic in brineworks. Confirm the shortlist includes principles you'd expect, and the walk produces a brief that downstream brainstorming can use.

3. **Helper unit tests:** `scripts/skill-advice.py` should have stdlib `unittest` coverage for: (a) tool name mismatch, (b) skill name mismatch, (c) file-not-found short-circuit, (d) successful match emits valid JSON, (e) unparseable stdin exits silently.

4. **End-to-end:** With Pattern B configured, invoke `superpowers:brainstorming` and confirm the `additionalContext` appears in the model's next turn (visible in transcripts; can be confirmed via cq).

Automated integration tests for the skill flows (depth-first walking, conflict surfacing) are out of scope for v1. The skills are prompt-driven and verified by use.

---

## Out of scope (v1)

- **Capture-side skill.** Adding a `principle-sweep` skill that runs post-implementation, walks the just-shipped change, and suggests principle amendments. Existing manual workflow stays.
- **Cross-project principle library.** Reusable principles (e.g. mattpocock's, or community ones) are not pulled in.
- **Auto-detection of relevant principles in *every* tool call.** The skill is invoked per design conversation, not as a continuous backseat driver.
- **Multi-language support.** Format-specific parsing assumes markdown.
- **Format-strict validation** of `docs/principles.md`. The skill is format-tolerant; the format hint in `docs/agents/principles.md` is a description, not a schema.

---

## Open questions / followups

- **Capture-side skill (v2).** Worth designing once apply has been used in earnest for a few weeks. Likely a new skill `principle-sweep` plus possible amendments to `stay-principled:setup` to register it.
- **Default integration choice.** Setup currently offers all three patterns. After real use, a default ranking may emerge ("most users pick A; B is for people who really want determinism").
- **Cross-machine config sharing.** If user-level `settings.json` grows, a `~/.claude/principles-config.json` could centralize per-project overrides. Not built until the pain shows up.
- **Principles file watcher.** When `docs/principles.md` changes, no machinery currently invalidates a previously-issued brief. Briefs are inline ephemera, so this matters only for the optional file-write path. Punt.
