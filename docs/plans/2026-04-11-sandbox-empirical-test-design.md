# Sandbox Empirical Test Session — Design

**Date:** 2026-04-11
**Task:** pickled-claude-plugins #60
**Status:** DESIGN (not yet executed)
**Related:** #34 (hook findings), #50 (git worktree add gap), PR #54 (classifier fix)

## Prior empirical results (2026-04-09, plugin build day)

During the sandbox-first plugin build there were integration-test sessions at
`/private/tmp/sandbox-hook-test` and `/private/tmp/sandbox-integration-test`
(session JSONLs still exist under `~/.claude/projects/`). They did probe the
sandbox, but only to verify the hook fired correctly. Established facts:

1. **`/tmp/*` writes are blocked in sandbox.** `touch /tmp/anything` returns
   `Operation not permitted`. This rules out the "allow-list with /tmp as
   default-allowed" assumption — Claude's sandbox-exec profile is
   **allow-list style** (anything not explicitly listed is denied), not
   deny-list style.
2. **Two independent write-denial layers exist.** When a sandboxed `touch`
   failed and the model retried with `dangerouslyDisableSandbox: true`, the
   retry was *also* blocked — but by a different layer with a different error
   string: "Claude Code may only create or modify files in the allowed working
   directories." That's a Claude Code runtime check separate from sandbox-exec.
   Any fix we propose must name which layer it targets.
3. The `.git/`, `.vscode/`, and `.worktrees/` paths — the targets of this
   session — were **never probed** in the plugin-build tests. Prior work only
   validated the hook's behavior on `/tmp/` denials.

So hypothesis H1 ("`.git/` is explicitly blocked") should be re-phrased as
H1': "`.git/` writes are not on the sandbox allow-list, so they deny by default."
Functionally identical, but the fix path differs — we'd be *adding* `.git` to
`allowWrite`, not removing a deny rule.

## Why this exists

Task 34 (2026-04-10) recorded the observation that `git worktree add` fails in the
Claude Code sandbox, apparently blocked on `.vscode/settings.json` creation, and
speculated the cause was "macOS-level protection (xattrs or Data Vault)." That
observation has since been cited in task 50, PR #52, PR #54, and multiple parked
sessions — but no one has ever opened the sandbox profile or run a controlled
write to confirm which layer is enforcing what.

Before changing any sandbox config, we need to know:

1. **Where** the sandbox is enforced (sandbox-exec profile? macOS system
   integrity? Claude Code hook layer?)
2. **What** is actually blocked vs. what the task annotations *claim* is blocked
3. **How** to fix each failure (config edit, command rewrite, or unfixable)

## Hypotheses to test

| # | Hypothesis | Source | Status |
|---|---|---|---|
| H1 | `.git/` writes are explicitly denied by Claude's sandbox profile | User intuition, 2026-04-11 | Untested |
| H2 | `.vscode/settings.json` is blocked by macOS xattrs/Data Vault | Task 34 annotation | Untested |
| H3 | `git worktree add` fails on `.git/worktrees/<name>/` metadata write, not on `.vscode/settings.json` | Alternative reading of the symptom | Untested |
| H4 | Repo-relative writes (anything under `$cwd`) are allowed by default | Implicit in current sandbox config (no repo paths in allowWrite) | Untested |
| H5 | The Claude Code sandbox profile is a readable file on disk | Standard sandbox-exec pattern | Untested |
| H6 | `git clone` and `git worktree add` fail when placing the destination *inside* the current repo, specifically because they write to the source repo's `.git/` dir (which isn't on the allow-list). The destination's location is a red herring — the blocker is the hidden `.git/` write. | User, 2026-04-11 | Untested |
| H7 | Task 50's claim that `git worktree add` fails on `.vscode/settings.json` creation was a misattribution — the real failure was the `.git/worktrees/<name>/` metadata write, and `.vscode/settings.json` was just the next failing write after the first one got worked around | Hypothesis from H6 | Untested |

## Method

Two phases, in order. Stop after phase 1 if it answers everything.

### Phase 1: Read the rules (if possible)

Goal: locate the generated sandbox-exec profile and read it directly. If this
works we can skip most of phase 2.

Tactics to try, in order of cheapness:

1. `ps aux | grep sandbox-exec` while a sandboxed command is mid-flight — the
   profile path is typically argv[1] or passed via `-f`
2. Search candidate dirs:
   - `~/.claude/` (we already listed this, no `.sb` files)
   - `~/Library/Application Support/Claude/`
   - `~/Library/Caches/Claude/`
   - `/tmp/claude-sandbox-*`, `/tmp/claude-*.sb`
   - Temporarily export a dump-on-open technique if sandbox-exec has debug flags
3. `lsof` the Claude CLI process to find open file descriptors mentioning `.sb`
   or `sandbox`
4. Strings-search the Claude Code binary for `sandbox-exec` invocation patterns
   (last resort — binary may be bundled/obfuscated)

**Success criterion:** a file we can read whose contents reference
`allow file-write*` or `deny file-write*` rules.

**If found:** grep it for `.git`, `.vscode`, and any paths under the repo. Done.

### Phase 2: Probe with controlled writes

If the profile can't be read, probe the sandbox empirically from inside a
sandboxed Claude Code Bash call.

**Setup:**
- Work in a fresh scratch repo under `scratch/sandbox-probe-repo/` (git init'd,
  outside `.worktrees/`, outside any existing git structure)
- Each probe records: command, exit code, stderr, stdout, inferred layer
- Results go to `docs/plans/2026-04-11-sandbox-empirical-test-results.md`

**Probes (in order, simplest first):**

| # | Command | Expected | Measures |
|---|---|---|---|
| P1 | `touch /tmp/sandbox-test-$$` | **blocked** (per prior 2026-04-09 results) | baseline: confirms prior result still holds |
| P2 | `touch baseline.txt` (in scratch/probe-repo) | ? | H4: is repo cwd writable? |
| P3 | `touch .vscode/settings.json` (mkdir `.vscode` first if needed) | ? | H2: task 50's claim — is `.vscode/` specifically blocked? |
| P4 | `touch .git/sandbox-probe` | ? | H1': plain `.git/` write |
| P5 | `mkdir -p .git/worktrees/probe && touch .git/worktrees/probe/HEAD` | ? | H3: specifically the worktree-metadata path git would use |
| P6 | `git worktree add .worktrees/probe-inside -b probe-inside` | ? | **H6: inside-repo worktree.** If this fails, capture *which* write triggered the denial (stderr should name the path) |
| P7 | `git worktree add ../probe-outside-wt -b probe-outside` | ? | H6 control: outside-repo worktree. If this behaves differently from P6, H6 gets stronger |
| P8 | `mkdir probe-clone-target && git clone https://github.com/technicalpickles/pickled-claude-plugins probe-clone-target/cloned` | ? | H6 extension: clone into subdir of repo. Same `.git/` write pattern as worktree |
| P9 | `xattr -l .vscode/settings.json` (only if P3 succeeded) | ? | H2: if P3 DID succeed, check whether the file has a Data Vault marker that would block a second write |
| P10 | `ls -la@ .git/` | allowed | H2 complement: do `.git/` contents carry macOS extended attrs that differ from normal dirs? |
| P11 | `touch ~/outside-allowwrite-$$` | **blocked** | sanity: unlisted home dir should fail (confirms allow-list semantics still apply) |

For each probe, the exact stderr text matters. Three distinct error shapes will
tell us the layer:
- `sandbox-exec: deny file-write-create ...` → Apple seatbelt / Claude profile
- `Operation not permitted` with no sandbox-exec prefix → macOS system integrity
  (SIP / Data Vault / rootless)
- `permission denied` (POSIX EPERM) from git/shell wrapper → same as above, just
  reported differently by the calling tool

**Success criterion:** every hypothesis above is marked CONFIRMED or REFUTED
with a direct quote of the error output.

## Out of scope for this session

- Fixing the gaps we find (separate task)
- Updating the sandbox-first plugin's error signatures based on what we learn
  (separate task)
- Proposing changes to `~/.claude/settings.json` (separate task)
- Investigating the PreToolUse retry-friction bug from task 34 (separate task)

If any of those feel urgent mid-investigation, add a taskwarrior entry and
continue.

## Deliverables

1. **Results doc**: `docs/plans/2026-04-11-sandbox-empirical-test-results.md` —
   every probe with its exact output, hypotheses marked CONFIRMED/REFUTED, and
   a one-paragraph summary of the true blocking rules
2. **Taskwarrior followups**: one task per real gap found, scoped to the layer
   that needs changing
3. **(Optional)** update `plugins/sandbox-first/src/sandbox_first/checker.py`'s
   `SANDBOX_ERROR_SIGNATURES` if phase 2 surfaces new error shapes the
   classifier should recognize

## Open design questions

- **Fresh session or here?** Running the probes in this already-polluted session
  is faster but less reproducible. A fresh session is cleaner but requires
  context handoff. LEANING: fresh session, with this design doc as the handoff.
- **Scratch repo location?** `scratch/` is gitignored and existing. Good enough.
- **Should we capture stderr to files, or rely on tool output?** Files are
  greppable across probes — lean toward capturing.

## Anti-gaslight provision

This session exists specifically because the sandbox claims have been cited for
weeks without verification. If any probe result conflicts with a task 34/50
annotation, the probe wins and the task gets annotated with the correction.
Observation is not evidence.
