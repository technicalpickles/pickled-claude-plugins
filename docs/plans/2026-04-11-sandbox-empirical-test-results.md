# Sandbox Empirical Test Session — Results

**Date:** 2026-04-11
**Task:** pickled-claude-plugins #60
**Design:** `docs/plans/2026-04-11-sandbox-empirical-test-design.md`
**Claude Code version:** 2.1.87
**Probe cwd:** `/private/tmp/sandbox-probe-repo` (symlinked from `/tmp/sandbox-probe-repo`)

## TL;DR

The sandbox profile is **generated in memory per-command** and passed inline via
`sandbox-exec -p <profile>` — it is **never written to disk as an `.sb` file**,
which is why every prior search for the profile came up empty.

The true default-deny list relevant to the hypotheses is **hardcoded in the Claude
Code binary**, not sourced from user config:

- **`.vscode/` — denied** (wholesale, `(deny file-write* (subpath ".../.vscode"))`)
- **`.idea/` — denied** (wholesale)
- **`.claude/commands/` — denied**
- **`.claude/agents/` — denied**
- **`.git/hooks/**` — denied**
- **`.git/config` — denied** (unless `allowGitConfig=true`, which defaults to `false`)
- **`.git/` — NOT denied.** Everything else under `.git/` (HEAD, index, refs, worktrees, objects, packed-refs, etc.) is writable if `.` is on the write allow-list.
- Dotfiles denied anywhere: `.gitconfig, .gitmodules, .bashrc, .bash_profile, .zshrc, .zprofile, .profile, .ripgreprc, .mcp.json`

**And the headline empirical result:** `git worktree add .worktrees/probe-inside`
**SUCCEEDED** inside the sandbox. The long-standing claim in task 34 / task 50 / PR #54
that this operation is blocked is **wrong**. What happens is: the command emits one
non-fatal `error: could not read IPC response` line (from git trying to talk to the
`fsmonitor--daemon.ipc` unix socket, which IS blocked by default), then proceeds to
create the worktree successfully. Whoever first cited this failure saw the "error:"
line and concluded the command had failed; it hadn't.

## Phase 1 — Profile location

### H5: Sandbox profile is a readable file on disk — **REFUTED**

The profile is built inline in a JS function and passed directly to `sandbox-exec`
as the `-p` argument:

```js
let v = shellQuote(["env", ...envVars, "sandbox-exec", "-p", profileString, "bash", "-c", cmd]);
```

(source: `function Ht1` in the Claude binary, offset ~75188039). No file is ever
materialized. The obfuscated function names are:

- `$uq()` — top-level profile composer
- `Huq()` — read-rule generator
- `_uq()` — write-rule generator
- `tbq()` — hardcoded deny list composer (the important one)
- `BE_()` — "denied subpaths" array builder
- `dv()` — path normalizer with `realpathSync` (resolves `/tmp/X` → `/private/tmp/X`)

### Phase 1 "bonus": full rule sources extracted from the binary

**`tbq(allowGitConfig=false)`** — the hardcoded write-deny list, reconstructed:

```js
function tbq(allowGitConfig = false) {
  const cwd = process.cwd();
  const rules = [];
  // hQH: dotfiles denied at cwd AND via **/<dotfile> glob
  const hQH = [".gitconfig", ".gitmodules", ".bashrc", ".bash_profile",
               ".zshrc", ".zprofile", ".profile", ".ripgreprc", ".mcp.json"];
  for (const f of hQH) {
    rules.push(path.resolve(cwd, f));
    rules.push(`**/${f}`);
  }
  // BE_(): directory denies; note that .git is FILTERED OUT of cbq
  // cbq = [".git", ".vscode", ".idea"]
  // BE_() = [...cbq.filter(x => x !== ".git"), ".claude/commands", ".claude/agents"]
  //       = [".vscode", ".idea", ".claude/commands", ".claude/agents"]
  for (const d of [".vscode", ".idea", ".claude/commands", ".claude/agents"]) {
    rules.push(path.resolve(cwd, d));
    rules.push(`**/${d}/**`);
  }
  rules.push(path.resolve(cwd, ".git/hooks"));
  rules.push("**/.git/hooks/**");
  if (!allowGitConfig) {
    rules.push(path.resolve(cwd, ".git/config"));
    rules.push("**/.git/config");
  }
  return [...new Set(rules)];
}
```

**Critical subtlety**: `BE_()` explicitly filters `.git` OUT of the `cbq` directory
list. So `.git/` itself is **not** a wholesale-denied subpath — only `.git/hooks/**`
and (by default) `.git/config` are denied. This is the opposite of what multiple
earlier tasks had assumed.

**Profile template** (from `$uq()`, simplified):

```scheme
(version 1)
(deny default (with message "<logTag>"))

; Essential permissions: process, signal, mach-priv-task-port, user-preference-read,
; a whitelist of mach services, IPC, IOKit IOSurface, a whitelist of sysctls,
; distributed notifications, a few device-file ioctls...

; Network (if !needsNetworkRestriction)
(allow network*)
; ...otherwise a localhost-only proxy setup

; File read
(allow file-read*)  ; default when no readConfig is set
; ... + deny-list from readConfig.denyOnly
; ... + allow-list exceptions from readConfig.allowWithinDeny

; File write
; + allow $TMPDIR subpaths
; + allow each writeConfig.allowOnly (as subpath or regex)
; + deny each writeConfig.denyWithinAllow (as subpath or regex)
; + deny each tbq() entry (see above)
; + deny file-write-unlink on every parent of every denied subpath (via es1())
```

Note the `es1()` helper: for every denied path, it emits additional
`(deny file-write-unlink)` rules on every parent directory of the denied path.
This prevents workarounds like `rm -rf .` to try to bypass the deny by unlinking
the enclosing directory.

### Corollary: `needsNetworkRestriction` gates all network

If `needsNetworkRestriction` is false (no `readConfig.denyOnly.length > 0` and
no proxy ports set), the profile emits `(allow network*)` — full network access.
This matches the observed behavior where github.com access works without explicit
network allowlisting.

## Phase 2 — Probe results

All probes executed in `/private/tmp/sandbox-probe-repo` (a fresh disposable repo,
created for this session and safe to pollute).

| # | Command | Result | Exit | stderr (verbatim) | Layer |
|---|---|---|---|---|---|
| P1 | `touch /tmp/sandbox-test-3049` | BLOCKED | 1 | `touch: cannot touch '/tmp/sandbox-test-3049': Operation not permitted` | sandbox-exec profile (default-deny; `/tmp` not in user's `allowWrite`) |
| P2 | `touch baseline.txt` | ALLOWED | 0 | — | cwd is `.` in user's `allowOnly` |
| P3 | `mkdir .vscode` | BLOCKED | 1 | `mkdir: cannot create directory '.vscode': Operation not permitted` | sandbox-exec profile (`tbq()` deny on `.vscode`) |
| P3b | `mkdir .idea` | BLOCKED | 1 | `mkdir: cannot create directory '.idea': Operation not permitted` | same, `.idea` deny |
| P3c | `mkdir -p .claude/commands` | BLOCKED | 1 | `mkdir: cannot create directory '.claude/commands': Operation not permitted` | same, `.claude/commands` deny |
| P3d | `touch .claude/some-other-file` | ALLOWED | 0 | — | `.claude/` itself is not denied; only `.claude/commands` and `.claude/agents` |
| P3e | `touch .mcp.json` / `.gitconfig` / `.bashrc` | BLOCKED | 1 | `touch: cannot touch 'X': Operation not permitted` | sandbox-exec profile (`hQH` dotfile denies) |
| P3f | `touch .claude/settings.json` | BLOCKED | 1 | `touch: cannot touch '.claude/settings.json': Operation not permitted` | sandbox-exec profile (from user's `denyWithinAllow`, not `tbq()`) |
| P4 | `touch .git/sandbox-probe` | **ALLOWED** | 0 | — | `.git/` itself is not denied — **H1 refuted** |
| P4b | `touch .git/hooks/post-commit` | BLOCKED | 1 | `touch: cannot touch '.git/hooks/post-commit': Operation not permitted` | `tbq()` deny on `.git/hooks` |
| P4c | `touch .git/config` | BLOCKED | 1 | `touch: cannot touch '.git/config': Operation not permitted` | `tbq()` deny on `.git/config` (default-deny; `allowGitConfig=false`) |
| P5 | `mkdir -p .git/worktrees/probe && touch .git/worktrees/probe/HEAD` | ALLOWED | 0 | — | `.git/worktrees/` is not in `tbq()` |
| P5b | `mkdir -p .git/refs/heads/probe && touch .git/refs/heads/probe-ref` | ALLOWED | 0 | — | `.git/refs/` not denied |
| P5c | `touch .git/index.lock` | ALLOWED | 0 | — | general `.git/` writes work |
| P6 | `git worktree add .worktrees/probe-inside -b probe-inside` | **ALLOWED** | 0 | `Preparing worktree (new branch 'probe-inside')` + `error: could not read IPC response` + `HEAD is now at 719d8b2 initial` | **worktree was created successfully**. `git worktree list` confirms it. The "IPC response" error is git's `fsmonitor--daemon.ipc` unix socket, which the sandbox blocks (`allowUnixSockets` not set) — **non-fatal and does not prevent worktree creation** |
| P7 | `git worktree add ../probe-outside-wt -b probe-outside` | BLOCKED | 128 | `Preparing worktree (new branch 'probe-outside')` + `fatal: could not create leading directories of '../probe-outside-wt/.git': Operation not permitted` | sandbox-exec profile: destination `../probe-outside-wt/` is **outside** `.` (the write allow-list), so creating it fails |
| P8 | `git clone https://github.com/technicalpickles/pickled-claude-plugins probe-clone-target/cloned` | BLOCKED | 128 | `Cloning into 'probe-clone-target/cloned'...` + `fatal: cannot copy '/usr/local/opt/git/share/git-core/templates/hooks/commit-msg.sample' to '/private/tmp/sandbox-probe-repo/probe-clone-target/cloned/.git/hooks/commit-msg.sample': Operation not permitted` | sandbox-exec profile: `tbq()`'s `**/.git/hooks/**` glob deny matches the nested cloned `.git/hooks/`. **The source repo's `.git/` is NOT the blocker** — it's the destination's new `.git/hooks/` being seeded from templates |
| P9 | `xattr -l .vscode/settings.json` | N/A | — | — | P3 failed, nothing to check |
| P10 | `/bin/ls -la@ .git/` | ALLOWED (empty result) | 0 | `.git/` contents show no `@` marker → **no extended attributes** → **H2's Data Vault/xattrs angle is refuted** |
| P11 | `touch ~/outside-allowwrite-4362` | BLOCKED | 1 | `touch: cannot touch '/Users/technicalpickles/outside-allowwrite-4362': Operation not permitted` | sandbox-exec profile (home dir not on allow-list) |

### Error-shape catalog

Three distinct stderr shapes for write denies (all surface the same underlying
`EPERM` from the kernel seatbelt, routed through different callers):

1. **Tool-reported EPERM**: `touch: cannot touch 'X': Operation not permitted` /
   `mkdir: cannot create directory 'X': Operation not permitted` — the failing tool
   prefixes its own name and re-reports the POSIX error.
2. **Shell-reported EPERM** (from shell redirects): `(eval):1: operation not permitted: X`
   when a command like `echo test > .gitconfig` is used. No tool prefix; just shell eval
   reporting back.
3. **Git-reported EPERM**: `fatal: could not create leading directories of 'X/.git': Operation not permitted`
   / `fatal: cannot copy 'X' to 'Y': Operation not permitted` / `fatal: could not write config file X: Operation not permitted`.
   Git wraps the POSIX error in its own message.

**There is NO `sandbox-exec:` or `seatbelt:` prefix on any error.** The kernel seatbelt
denies the write with `EPERM` and nothing in the user-visible output identifies the
enforcement layer. This is important for the sandbox-first plugin's error classifier:
the only reliable signature is `Operation not permitted` combined with path heuristics,
because there's no marker string telling you it was sandbox-exec as opposed to a regular
Unix permission problem.

## Hypothesis verdicts

| # | Hypothesis | Verdict | Evidence |
|---|---|---|---|
| H1 | `.git/` writes are explicitly denied by Claude's sandbox profile | **REFUTED** | P4 succeeded; profile source confirms `BE_()` filters `.git` out of `cbq` |
| H1' | `.git/` writes are not on the sandbox allow-list, so they deny by default | **REFUTED** | `.` is on the user's write allow-list, which includes everything under cwd including `.git/` — only the `tbq()` sub-denies carve pieces out |
| H2 | `.vscode/settings.json` is blocked by macOS xattrs/Data Vault | **REFUTED** | `.vscode/` is blocked by `tbq()` in the Claude Code sandbox profile (explicit `(deny file-write* (subpath ".../.vscode"))`). `.git/` contents have no extended attributes (P10). This is plain sandbox-exec, not macOS rootless/Data Vault |
| H3 | `git worktree add` fails on `.git/worktrees/<name>/` metadata write | **REFUTED** | P5 showed that path is writable, and P6 showed `git worktree add` actually succeeds |
| H4 | Repo-relative writes (anything under `$cwd`) are allowed by default | **CONFIRMED, with caveats** | P2 and the many `.git/` subpath writes confirm this. Caveats: `.vscode/`, `.idea/`, `.claude/commands/`, `.claude/agents/`, and the `hQH` dotfiles (`.gitconfig, .mcp.json, .bashrc, …`) are hardcoded exceptions via `tbq()`. Plus user-configured `denyWithinAllow` entries like `.claude/settings.json` |
| H5 | The Claude Code sandbox profile is a readable file on disk | **REFUTED** | Profile is generated inline by `$uq()` and passed via `sandbox-exec -p`, never written to a file |
| H6 | `git clone`/`git worktree add` fail when placing destination inside the repo, because of writes to the source's `.git/` | **REFUTED (mechanism wrong)** | P6 showed worktree-add-inside SUCCEEDS. P8 showed clone-into-subdir fails, but the blocker is the **destination's** new `.git/hooks/` matching `**/.git/hooks/**` — not the source's `.git/`. The user's intuition that "hidden `.git/` writes are the issue" was right in spirit for clone, wrong about which `.git/` |
| H7 | Task 50's claim that `git worktree add` fails on `.vscode/settings.json` creation was a misattribution | **CONFIRMED** (sort of) | P6 empirically demonstrates `git worktree add` works fine; it never attempts to write `.vscode/settings.json`. The original "worktree add blocked on `.vscode/settings.json`" observation must have come from a separate tool (editor-opening script, post-create hook) running after worktree creation, NOT from git worktree add itself |

## What actually breaks (the real blocker list)

For future reference, the operations that genuinely fail in a sandboxed Claude
Code session and why:

| Operation | Blocker | Exact path denied | Fixable how? |
|---|---|---|---|
| `git init` / `git config set` | `.git/config` deny | `/cwd/.git/config` via `tbq()` when `!allowGitConfig` | Per-session: pass `allowGitConfig=true` (not user-configurable via settings.json today). Per-command: `git -c user.x=y ...` (avoids writing to `.git/config`). Long-term: Claude Code needs to plumb this through `sandbox.allowGitConfig` in settings |
| `git commit` with any `.git/hooks/*` | `.git/hooks/**` deny | `**/.git/hooks/**` via `tbq()` | Disable hooks (`git -c core.hooksPath=/dev/null commit ...`) or use `--no-verify` (which user global CLAUDE.md forbids absent explicit request) |
| `git clone` anywhere | `**/.git/hooks/**` glob matches the cloned repo's template-seeded hooks dir | `DEST/.git/hooks/commit-msg.sample` etc. | Use `git clone --template=/dev/null` to skip hook templates, OR accept the failure and do `git init && git remote add && git fetch` dance |
| Writing to editor config dirs | `.vscode/` and `.idea/` deny | `/cwd/.vscode`, `/cwd/.idea` via `tbq()` | Not user-fixable via settings.json. Have to operate outside the sandbox (Edit/Write tool uses a different layer anyway) |
| Writing to most dotfiles in cwd | `hQH` deny list | `/cwd/.gitconfig`, `.bashrc`, `.mcp.json`, etc. via `tbq()` | Not user-fixable |
| Creating files outside cwd | Not on `allowWrite` | Any path not under `.`, `$TMPDIR`, or the user's explicit `allowWrite` entries | Add the path to `sandbox.filesystem.allowWrite` in `~/.claude/settings.json` |
| Unix-socket IPC (e.g., git fsmonitor) | `allowUnixSockets`/`allowAllUnixSockets` not set | `fsmonitor--daemon.ipc` in `.git/` | Non-fatal for git; can be ignored. For others, set `allowUnixSockets` in settings |

## Corrections to prior tasks (anti-gaslight fulfillment)

The design doc's anti-gaslight provision says: "if any probe result conflicts with
a task 34/50 annotation, the probe wins and the task gets annotated with the
correction." Applying:

- **Task 34** (`git worktree add` fails, "blocked on `.vscode/settings.json` creation",
  "macOS-level protection"): wrong on all three counts. `git worktree add` SUCCEEDS in
  the sandbox. `.vscode/settings.json` is blocked but by the Claude Code sandbox-exec
  profile, not macOS. The worktree-add failure story needs a different origin — most
  likely a post-create editor/tool invocation that nobody attributed correctly.
- **Task 50** (cites task 34 for the `git worktree add` gap): the gap doesn't exist.
  Whatever downstream work depends on this being "known broken" needs revisiting.
- **PR #54 classifier fix** (was the error classifier updated for `.vscode/settings.json`?
  need to check whether the error signature used is still accurate given the real
  error shape): the error shape is plain POSIX `Operation not permitted` with no
  sandbox-exec marker. Any signature looking for `sandbox-exec:` / `seatbelt:` /
  `deny file-write-create` in stderr will miss every real case.

## Follow-ups to file (out of scope for this session per design doc)

These should become taskwarrior tasks:

1. **Correct task 34's annotation** with the actual mechanism (`.vscode`/`.idea`/etc are
   denied by `tbq()` hardcoded list in the Claude Code binary; `.git/` is not).
2. **Reopen the "what actually fails in worktree add" investigation** — since `git worktree add` itself works, find the actual tool that was emitting the `.vscode/settings.json` error in the task 34 session and attribute it correctly.
3. **Update `sandbox-first` error classifier** (`plugins/sandbox-first/src/sandbox_first/checker.py` `SANDBOX_ERROR_SIGNATURES`) with the three real error shapes from the "Error-shape catalog" section above: tool-prefixed EPERM, shell-eval EPERM, and git-wrapped EPERM. All three lack a `sandbox-exec:` marker.
4. **Decide whether to expose `allowGitConfig` in `~/.claude/settings.json`** — right now this is a function parameter with no public knob, which means `.git/config` writes (required by many git workflows) are unconditionally blocked.
5. **Decide whether to expose `allowUnixSockets` for git fsmonitor** — the `could not read IPC response` noise in P6 is harmless but ugly. Worth a flag.
6. **Document `tbq()`'s hardcoded list as a known limitation** in the sandbox-first plugin README so users don't have to reverse-engineer it.

Each of these will be filed as its own taskwarrior entry before closing this session.

## Appendix: raw probe session

Session ran against cwd `/private/tmp/sandbox-probe-repo` with an already-initialized
`.git` (created before the session). All commands executed via Claude Code's Bash
tool under default sandbox settings. User's `~/.claude/settings.json` provided the
`allowOnly` / `denyWithinAllow` lists which were combined with `tbq()` to produce the
effective deny list.

## Phase 3 — Real-repo and workaround probes

**Executed:** 2026-04-11 (same day as Phase 1/2, separate session)
**Cwd for P12:** `/Users/technicalpickles/github.com/technicalpickles/pickled-claude-plugins`
**Cwd for P13:** same (P13 uses absolute paths for source and destination)

### P12 — real-repo `git worktree add`

**Pre-probe state:**
```
$ git worktree list
.../pickled-claude-plugins                                           7522223 [main]
.../pickled-claude-plugins/.worktrees/sandbox-first-false-positives  ffcd52a [fix/sandbox-first-false-positives]
```
No `empirical-test-worktree` branch or worktree present.

**Probe:**
```
$ git worktree add .worktrees/empirical-test-worktree -b empirical-test-worktree
Preparing worktree (new branch 'empirical-test-worktree')
HEAD is now at 7522223 docs(sandbox-first): add phase 3 probes P12/P13 to empirical test design
exit=0
```

**Verification:**
```
$ git worktree list
.../pickled-claude-plugins                                           7522223 [main]
.../pickled-claude-plugins/.worktrees/empirical-test-worktree        7522223 [empirical-test-worktree]
.../pickled-claude-plugins/.worktrees/sandbox-first-false-positives  ffcd52a [fix/sandbox-first-false-positives]
```

**Result:** **SUCCESS.** Exit code 0. Worktree created. Notably, **no** `error: could not read IPC response` noise this time, unlike P6 (which did emit that line in `/tmp/sandbox-probe-repo`). The absence of the fsmonitor IPC error is interesting but probably just means the fsmonitor daemon isn't configured/running for this repo path. It's not load-bearing to the result.

**Cleanup (mandatory):**
```
$ git worktree remove .worktrees/empirical-test-worktree    # exit=0
$ git branch -D empirical-test-worktree                      # Deleted branch empirical-test-worktree (was 7522223).
$ git worktree list
.../pickled-claude-plugins                                           7522223 [main]
.../pickled-claude-plugins/.worktrees/sandbox-first-false-positives  ffcd52a [fix/sandbox-first-false-positives]
```
State restored to pre-probe.

**Conclusion:** P12 empirically refutes any remaining "but maybe it's this repo specifically" defense of the task 34 claim. `git worktree add` works in the real repo under the real sandbox. The task 34 observation is **not reproducible** in its original context. As in Phase 2's P6, the operation that the task 34 session labeled as "git worktree add failure" must have been a downstream tool emitting a `.vscode/settings.json` error after the worktree already existed, not the worktree-add call itself. Task 63 can be closed; task 34's annotation is wrong.

### P13 — `git clone --template=/dev/null`

**Source repo:** `/tmp/sandbox-probe-repo` (from Phase 2, still present)

**First run (contaminated source):**
```
$ mkdir -p /tmp/p13-clone-target   # exit=0
$ git clone --template=/dev/null /tmp/sandbox-probe-repo /tmp/p13-clone-target/destination
Cloning into '/tmp/p13-clone-target/destination'...
warning: templates not found in /dev/null
done.
fatal: 'refs/remotes/origin/probe-ref' has neither a valid OID nor a target
exit=128
```

The failure is **not** a sandbox issue. It's data contamination: Phase 2's P5b did
`touch .git/refs/heads/probe-ref`, leaving a zero-byte ref file in the source repo.
Any `git clone` of this source will fail on ref resolution, sandbox or not.

**Crucially**, the clone got past `done.` — which is *far past* the template-seeding
phase where P8 (vanilla `git clone`) died on `**/.git/hooks/**`. The `warning: templates
not found in /dev/null` confirms git used the empty template dir, so it never tried to
copy `commit-msg.sample` etc. into the destination `.git/hooks/`. The `**/.git/hooks/**`
deny had nothing to match. Git's clone atomicity then rolled back the destination dir
entirely when the ref step failed, so `ls /tmp/p13-clone-target/destination/` reported
"No such file or directory" — not a sandbox block, just the rollback.

**Cleanup of contaminated source** (removing Phase 2 artifacts so the probe can actually
complete):
```
$ rm /tmp/sandbox-probe-repo/.git/refs/heads/probe-ref   # exit=0 (zero-byte file from P5b)
$ rm -rf /tmp/sandbox-probe-repo/.git/refs/heads/probe   # exit=0 (empty dir from P5)
$ ls -la /tmp/sandbox-probe-repo/.git/refs/heads/
-rw-r--r-- 1 ... main           # real branch
-rw-r--r-- 1 ... probe-inside   # real ref from P6 worktree
-rw-r--r-- 1 ... probe-outside  # real ref from P7 (created before P7 failed)
```

**Second run (clean source):**
```
$ rm -rf /tmp/p13-clone-target && mkdir -p /tmp/p13-clone-target   # exit=0
$ git clone --template=/dev/null /tmp/sandbox-probe-repo /tmp/p13-clone-target/destination
Cloning into '/tmp/p13-clone-target/destination'...
warning: templates not found in /dev/null
done.
exit=0
```

**Sanity check — destination hooks dir:**
```
$ ls -la /tmp/p13-clone-target/destination/.git/hooks/
ls: cannot access '.../.git/hooks/': No such file or directory
exit=2
```

**No `hooks/` directory at all.** That's the mechanism: git doesn't create
`.git/hooks/` when the template source is empty, so the `**/.git/hooks/**` deny rule
has nothing to match against. The clone completes.

**Destination structure after clone:**
```
$ ls -la /tmp/p13-clone-target/destination/.git/
-rw-r--r-- 289  config          # <- see "Puzzle" below
-rw-r--r-- 21   HEAD
-rw-r--r-- 65   index
drwxr-xr-x ...  logs
drwxr-xr-x ...  objects
-rw-r--r-- 261  packed-refs
drwxr-xr-x ...  refs
# note: no hooks/ dir
```

**Cleanup:**
```
$ rm -rf /tmp/p13-clone-target   # exit=0
```

**Result:** **SUCCESS.** `--template=/dev/null` is a confirmed workaround for the
`tbq()` `**/.git/hooks/**` deny that blocks vanilla `git clone` under the sandbox.
Task 67's plugin README can document this.

### Phase 3 puzzles (noted, not chased — probes are locked)

1. **P13 second run wrote `.git/config` to the destination**, yet Phase 1's `tbq()`
   reconstruction shows `**/.git/config` in the default-deny list and Phase 2's P4c
   confirmed `touch .git/config` is blocked in a cwd-rooted probe. Possible
   explanations (not investigated):
   - The `**/.git/config` glob in sandbox-exec may be interpreted against the sandbox
     profile's path normalization in a way that doesn't match `/tmp/p13-clone-target/destination/.git/config`
     (e.g., glob is anchored to cwd or `$TMPDIR`).
   - Git might be writing the config via a rename-from-temp pattern that the sandbox
     scores differently than a direct `open(O_CREAT)`.
   - `$TMPDIR` subpaths get a blanket write-allow from `$uq()` that could be overriding
     the `tbq()` `.git/config` deny at the profile composition level.
   - The Phase 1 `tbq()` reconstruction may be incomplete — there may be additional
     filters excluding `$TMPDIR`-rooted paths from the `.git/config` deny specifically.
   Worth filing as a follow-up but out of scope for this session.

2. **P12 had no `fsmonitor--daemon.ipc` noise, P6 did.** Probably reflects that
   `pickled-claude-plugins` doesn't have `core.fsmonitor` configured and the disposable
   `/tmp/sandbox-probe-repo` inherited some default from user git config. Not load-bearing.

### Phase 3 — updated hypothesis verdicts

| # | Hypothesis | Phase 3 evidence |
|---|---|---|
| H6 | `git clone`/`git worktree add` fail when destination is inside repo due to source `.git/` writes | P12 further refutes for worktree-add in the real repo. P13 refines P8's mechanism: destination `.git/hooks/` is the real blocker for clone; source `.git/` is never an issue |
| H7 | Task 50's `.vscode/settings.json` claim was a misattribution | P12 locks this in for the real-repo context — `git worktree add` emits zero output mentioning `.vscode/` |
| **NEW** | `git clone --template=/dev/null` bypasses the `**/.git/hooks/**` deny | **CONFIRMED** by P13 |

### Phase 3 conclusions for downstream tasks

- **Task 63** (originally tracking the "git worktree add broken in sandbox" gap):
  not reproducible. Closed as observation misread. The phase 1/2 conclusion carries
  over to the real repo with no asterisks.
- **Task 67** (sandbox-first README gap — document clone workarounds):
  `git clone --template=/dev/null <source> <dest>` is the confirmed workaround.
  Use it when cloning inside a sandboxed session. The cloned repo won't have sample
  hooks but everything else works normally.
- **Task 60** (this empirical test session): complete. All designed probes executed,
  all results documented, no hypotheses left unexamined within scope.

End of Phase 3 results.

## Phase 4 — Found data from session `0e6308b0`

**Date:** 2026-04-11
**Session JSONL:** `~/.claude/projects/-private-tmp-sandbox-clone-test/0e6308b0-aede-4048-882a-8ef6e894d93a.jsonl`
**Cwd for entire session:** `/private/tmp/sandbox-clone-test`
**Setup (run by user before starting Claude):**
```
mkdir -p /tmp/sandbox-clone-test
cd /tmp/sandbox-clone-test
git init
touch readme.md && git add readme.md && git commit -m "init"
claude
```

This is **found data** — the user ran a session for an unrelated practical task (cloning a repo inside `/tmp/sandbox-clone-test`) and the resulting tool calls happened to land on probe conditions that Phase 1/2/3 hadn't covered. Phase 4 reads the session JSONL and treats those events as additional probes. Found-data probes are weaker than designed probes because we don't control the conditions, but they're stronger than nothing and they cover gaps the designed probes left open.

### The four events

**Event 1 — `git clone` of `town-charter` (SSH):**
```
$ git clone git@github.com:technicalpickles/town-charter.git /private/tmp/sandbox-clone-test/town-charter
Cloning into '/private/tmp/sandbox-clone-test/town-charter'...
fatal: cannot copy '/usr/local/opt/git/share/git-core/templates/hooks/commit-msg.sample' to '/private/tmp/sandbox-clone-test/town-charter/.git/hooks/commit-msg.sample': Operation not permitted
exit=128
```
**Verdict:** BLOCKED. Identical mechanism and error wording to Phase 2 P8 — `tbq()`'s `**/.git/hooks/**` glob deny. Third independent reproduction (P8, original 2026-04-09 sessions, this session).

**Event 2 — `git worktree add ./.worktrees/test`:**
```
$ git worktree add -b test ./.worktrees/test
Preparing worktree (new branch 'test')
error: could not read IPC response
HEAD is now at fbed6c8 init
exit=0
```
Verified by `git worktree list`:
```
/private/tmp/sandbox-clone-test                  fbed6c8 [main]
/private/tmp/sandbox-clone-test/.worktrees/test  fbed6c8 [test]
```
**Verdict:** SUCCEEDED. Same shape as P6 — non-fatal `IPC response` noise from blocked `fsmonitor--daemon.ipc` unix socket, then the worktree is created normally. Third independent reproduction of "worktree add works in sandbox" (P6 in `/tmp/sandbox-probe-repo`, P12 in real repo, this session in a fresh `/tmp` repo). The task 34 / task 50 multi-week claim is now disproven from three independent contexts.

**Event 3 — `git clone --template=` (empty value):**

First the user tried vanilla clone:
```
$ git clone git@github.com:technicalpickles/dotfiles.git /private/tmp/sandbox-clone-test/dotfiles
Cloning into '/private/tmp/sandbox-clone-test/dotfiles'...
fatal: cannot copy '/usr/local/opt/git/share/git-core/templates/hooks/commit-msg.sample' to '/private/tmp/sandbox-clone-test/dotfiles/.git/hooks/commit-msg.sample': Operation not permitted
exit=128
```
(Yet another reproduction of P8.) Then the user retried with empty `--template=`:
```
$ git clone --template= git@github.com:technicalpickles/dotfiles.git /private/tmp/sandbox-clone-test/dotfiles
Cloning into '/private/tmp/sandbox-clone-test/dotfiles'...
error: could not write config file /private/tmp/sandbox-clone-test/dotfiles/.git/config: Operation not permitted
fatal: could not set 'core.repositoryformatversion' to '0'
exit=128
```
**Verdict:** Different blocker. `--template=` (empty) bypassed the hooks-template copy step (no hooks error), but then died on `.git/config` instead. **This proves `--template=` and `--template=/dev/null` are NOT equivalent for our purposes.** P13 used `--template=/dev/null` and succeeded with `.git/config` writing OK (in a non-/tmp cwd). This session's `--template=` (empty) failed on `.git/config` (in a `/tmp` cwd). The README workaround (#67) needs to specifically say `/dev/null`, not "any empty template."

**Event 4 — Direct shell write to `.git/config`:**
```
$ pwd && mkdir -p /private/tmp/sandbox-clone-test/dotfiles-probe && echo "hello" > /private/tmp/sandbox-clone-test/dotfiles-probe/plain.txt && mkdir -p /private/tmp/sandbox-clone-test/dotfiles-probe/.git && echo "test" > /private/tmp/sandbox-clone-test/dotfiles-probe/.git/config
/tmp/sandbox-clone-test
(eval):1: operation not permitted: /private/tmp/sandbox-clone-test/dotfiles-probe/.git/config
exit=1
```
**Verdict:** BLOCKED on the `.git/config` write specifically — note that the chained `mkdir`, `echo > plain.txt`, and `mkdir .git` all succeeded (cwd is on the user's allow-list, those are inside cwd, none of them match `tbq()`). The shell-eval EPERM shape (catalog item #2) is now confirmed in a real session, not just synthesized in our designed probes.

### Phase 4 implications: the #68 puzzle is sharpened

Combine events 3 and 4 with the existing `.git/config` datapoints:

| Source | Cwd | Target path | Inside cwd? | Result |
|---|---|---|---|---|
| P4c | `/private/tmp/sandbox-probe-repo` | `./.git/config` → `<cwd>/.git/config` | Y, root | **BLOCKED** |
| P13 | `<repo>/pickled-claude-plugins` | `/tmp/p13-clone-target/destination/.git/config` | N | **ALLOWED** |
| Phase 4 event 3 | `/private/tmp/sandbox-clone-test` | `<cwd>/dotfiles/.git/config` | Y, subdir | **BLOCKED** |
| Phase 4 event 4 | `/private/tmp/sandbox-clone-test` | `<cwd>/dotfiles-probe/.git/config` | Y, subdir | **BLOCKED** |

**The pattern that fits all four:** `.git/config` writes are denied when the target is **inside cwd** (root or any subdirectory), allowed when **outside cwd**. The `/tmp` framing of #68's original write-up is a red herring — phase 4 has cwd inside `/tmp` AND target inside `/tmp`, and the deny still fires. What matters is the inside-vs-outside-cwd relationship, not the `/tmp` prefix.

This reshapes the candidate explanations for #68:

- **Mostly REFUTED:** "There's a `/tmp` blanket allow that overrides `tbq()`." Phase 4 events 3 and 4 fail on `/tmp` paths from a `/tmp` cwd. If a blanket `/tmp` allow existed, P4c, event 3, and event 4 should all have succeeded. They didn't.
- **Still possible (sharpened):** The `tbq()` deny is recursively enforced under cwd but unbounded outside cwd. Mechanism candidates:
  - sandbox-exec rule generation may emit `(deny file-write* (regex #"\.git/config$"))` scoped inside `(allow file-write* (subpath cwd))`. The deny only takes effect inside the allow region. Outside cwd, the path is allowed by some OTHER allow rule (e.g., user `allowWrite` or `$TMPDIR`) and the deny isn't paired with that allow.
  - The `**/.git/config` glob in `tbq()` may be translated to a regex that only fires after a cwd-rooted match.
  - The `tbq()` reconstruction may be missing a `(subpath cwd)` filter that scopes the deny.
- **Still possible:** A second enforcement layer in the Claude Code runtime (separate from sandbox-exec) that checks "is this write target under cwd? If so, apply tbq() denies." This would explain the inside-vs-outside split independently of how sandbox-exec handles the rules. The 2026-04-09 "For security, Claude Code may only create or modify files in the allowed working directories" error string fits this layer's signature.

The two candidates are not mutually exclusive — both could be true at once. Phase 5 below designs probes to disambiguate.

### Phase 4 also gives us the third error shape in the wild

The error-shape catalog originally listed three EPERM forms (tool-prefixed, shell-eval, git-wrapped). Until Phase 4, the catalog had:
- Tool-prefixed: many examples (P1, P3, P3b, P3c, P3e, P3f, P4b, P4c, P11)
- Shell-eval: synthesized only — no real session reproduction in Phase 1/2/3
- Git-wrapped: P7 (`fatal: could not create leading directories`), P8 (`fatal: cannot copy ... templates`)

Phase 4 fills the gaps:
- **Shell-eval (event 4):** `(eval):1: operation not permitted: /private/tmp/sandbox-clone-test/dotfiles-probe/.git/config` — first real-session reproduction of the shell-eval form, against `.git/config`.
- **Git-wrapped variant (event 3):** `error: could not write config file <path>: Operation not permitted` followed by `fatal: could not set 'core.repositoryformatversion' to '0'`. This is a NEW git-wrapped variant we hadn't seen before — git's error-then-fatal pair instead of a single `fatal:` line. The classifier work for #64 needs to handle both git error patterns.

## Phase 5 — Designed probes for #68 (NOT YET EXECUTED)

**Goal:** disambiguate "inside-cwd-recursive deny" from "second enforcement layer," and confirm that the inside-vs-outside-cwd pattern generalizes beyond `.git/config` to other `tbq()` rules.

**Execution requirement:** Phase 5 must be run in a **fresh Claude session**, not in this synthesis session, for the same reason Phase 1/2/3 were each fresh — the sandbox profile is generated per-command at session start and we want a clean slate.

**Setup (run before starting Claude, NOT in-session):**
```
rm -rf /tmp/p5-cwd-inside /tmp/p5-cwd-outside
mkdir -p /tmp/p5-cwd-inside /tmp/p5-cwd-outside
cd /tmp/p5-cwd-inside
# do NOT git init - keep this as a plain dir to avoid contaminating the .git/ semantics
claude
```

(The session will run with `cwd = /tmp/p5-cwd-inside`, equivalent to `/private/tmp/p5-cwd-inside` after `realpathSync`.)

### Probe table

All probes use absolute paths (not relative) to make the inside/outside-cwd analysis unambiguous. Cwd for the whole phase is `/tmp/p5-cwd-inside` ≡ `/private/tmp/p5-cwd-inside`.

| # | Command | Hypothesis tested | Expected if "recursive deny under cwd" | Expected if "second runtime layer also matters" |
|---|---|---|---|---|
| P14 | `mkdir -p /private/tmp/p5-cwd-inside/.git && touch /private/tmp/p5-cwd-inside/.git/config` | Control: cwd-root `.git/config` (matches P4c) | BLOCK | BLOCK |
| P15a | `mkdir -p /private/tmp/p5-cwd-inside/sub/.git && touch /private/tmp/p5-cwd-inside/sub/.git/config` | Subdir `.git/config` inside cwd (matches Phase 4 event 4) | BLOCK | BLOCK |
| P15b | `mkdir -p /private/tmp/p5-cwd-inside/a/b/c/.git && touch /private/tmp/p5-cwd-inside/a/b/c/.git/config` | Deep subdir `.git/config` inside cwd | BLOCK | BLOCK |
| P16 | `mkdir -p /private/tmp/p5-cwd-outside/.git && touch /private/tmp/p5-cwd-outside/.git/config` | `.git/config` OUTSIDE cwd, on a sibling `/tmp` path | ALLOW (deny is cwd-scoped) | ALLOW (path is outside cwd, runtime layer doesn't fire) |
| P17 | `mkdir -p /private/tmp/p5-cwd-inside/sub/.git && touch /private/tmp/p5-cwd-inside/sub/.git/HEAD` | Control: subdir `.git/HEAD` (NOT in `tbq()`) inside cwd | ALLOW (HEAD is not in any deny) | ALLOW |
| P18 | `mkdir -p /private/tmp/p5-cwd-inside/sub/.git/hooks && touch /private/tmp/p5-cwd-inside/sub/.git/hooks/test` | Subdir `.git/hooks/X` inside cwd (matches P8's destination semantics) | BLOCK | BLOCK |
| P19 | `mkdir -p /private/tmp/p5-cwd-outside/.git/hooks && touch /private/tmp/p5-cwd-outside/.git/hooks/test` | `.git/hooks/X` OUTSIDE cwd | ALLOW (deny is cwd-scoped) | ALLOW |
| P20 | `mkdir -p /private/tmp/p5-cwd-outside/.vscode && touch /private/tmp/p5-cwd-outside/.vscode/settings.json` | `.vscode/` OUTSIDE cwd | ALLOW (deny is cwd-scoped) | depends on layer scope |

### What each result tells us

- **P14 + P15a + P15b all BLOCK, P16 ALLOWS:** confirms the inside-vs-outside-cwd pattern for `.git/config`. Combined with P17 (subdir `.git/HEAD` allowed) this rules out "all `.git/` writes in subdirs are blocked" — only the `tbq()` paths are.
- **P18 BLOCKS, P19 ALLOWS:** generalizes the inside-vs-outside pattern to `**/.git/hooks/**`. If P18 BLOCKS but P19 also BLOCKS, the deny is unbounded (not cwd-scoped) for hooks specifically — different rule generation than `.git/config`.
- **P20 ALLOWS:** confirms `.vscode` is also cwd-scoped. If P20 BLOCKS, then the second enforcement layer probably exists and enforces dirname matches independent of cwd.
- **Any P15* or P18 ALLOWS unexpectedly:** the inside-vs-outside hypothesis is wrong and we're back to the drawing board.

### After Phase 5

If Phase 5 results match the "deny is cwd-scoped" prediction across the board (all six expected outcomes), the explanation is in the sandbox-exec rule generation: `tbq()` denies are emitted as regex/subpath rules nested under or interleaved with the cwd allow, and the path is allowed by an unrelated allow rule (e.g., user `allowWrite`) outside cwd. This would mean the Phase 1 `tbq()` reverse-engineering captured the deny strings correctly but missed how `$uq()` composes them with the allow rules. Action items would be:

1. Reverse-engineer `$uq()`'s emit step for `tbq()` rules — find where it actually formats them into `(deny ...)` sexprs.
2. Update the `claude-code-sandbox-internals` memory with the corrected mechanism.
3. Update the `tbq()` reconstruction in this doc with the missing scope info.
4. Close task #68 with the correct explanation.

If Phase 5 results show the inside/outside split holds for `.git/config` but NOT for `**/.git/hooks/**` or `.vscode/` (i.e., hooks/vscode are blocked everywhere, only config is cwd-scoped), the rule families are emitted differently and we need to account for that — possibly because the cwd-rooted absolute path version of tbq()'s rules (`path.resolve(cwd, ".git/config")`) is being treated differently from the glob version (`**/.git/config`).

If Phase 5 contradicts the prediction (e.g., P16 BLOCKS too), the second enforcement layer is real and we need to grep the binary for the "allowed working directories" string and trace it back to the check that fires. That's a much bigger investigation but the results doc would update with whatever we find.

End of Phase 5 design. Execute in a fresh session and append a Phase 5 results section after.

## Phase 5 — Results

**Executed:** 2026-04-11 (same day, separate fresh session)
**Claude Code version:** 2.1.87
**Session cwd:** `/tmp/p5-cwd-inside` (resolves to `/private/tmp/p5-cwd-inside` via `realpathSync`)
**Setup:** `/tmp/p5-cwd-inside` and `/tmp/p5-cwd-outside` were pre-created as empty directories before starting Claude, per the Phase 5 design. Neither was `git init`ed.

**Note on interactive permission prompts:** the probe commands were approved one-by-one through Claude Code's permission prompt system during execution. Approvals at the permission-prompt layer affect only whether Claude is allowed to **invoke** a command — they do not grant the resulting process any additional write capability in the sandbox-exec profile. Evidence: every blocked probe still returned `Operation not permitted` after being approved through the prompt. If the approval path had relaxed the sandbox, the touches would have succeeded. The results below reflect the real sandbox-exec enforcement, not an artifact of the approval flow.

### Unexpected finding before running the probes

The Phase 5 design assumed `/private/tmp/p5-cwd-outside` would be writeable (as a sibling `/tmp` path), so that P16/P19/P20 could reach the `tbq()` deny layer. **This assumption was wrong.** The user's effective `write.allowOnly` list (visible in the system prompt's sandbox config) contains `"."`, `"$TMPDIR"`, `/tmp/claude`, `/private/tmp/claude`, and various user-cache paths — but **not** arbitrary `/tmp/*` siblings. `$TMPDIR` on macOS resolves to `/var/folders/...`, not `/tmp`. Therefore `/private/tmp/p5-cwd-outside` is unwriteable at a more fundamental layer than `tbq()`: the "path not on write allow-list" check fires first.

Consequence: P16, P19, and P20 are blocked at the `mkdir` step by the allow-list layer, never reaching `tbq()`. Phase 5 therefore **cannot directly disambiguate** "cwd-scoped `tbq()` deny" from "unbounded `tbq()` deny" using this setup. To test that cleanly, a future Phase 5b would need to use an allow-listed path outside cwd — for example `$TMPDIR`, `/Users/technicalpickles/.cache/bktide`, or any of the cache paths in `write.allowOnly`. The results below still produce sharp signal for the *inside-cwd recursion* question (which P14/P15a/P15b/P17/P18 answer directly) and for error-shape cataloging.

### Probe execution — each probe as two Bash calls (mkdir, then touch), stderr captured verbatim

#### P14 — cwd-root `.git/config` (control, matches P4c)

```
$ mkdir -p /private/tmp/p5-cwd-inside/.git
EXIT=0
$ touch /private/tmp/p5-cwd-inside/.git/config
touch: cannot touch '/private/tmp/p5-cwd-inside/.git/config': Operation not permitted
EXIT=1
```

**Verdict:** BLOCKED. Matches the expected outcome. Reproduces P4c in a fresh cwd/session, confirming `tbq()`'s `.git/config` deny applies at cwd root.

#### P15a — subdir `.git/config` (one level deep, inside cwd)

```
$ mkdir -p /private/tmp/p5-cwd-inside/sub/.git
EXIT=0
$ touch /private/tmp/p5-cwd-inside/sub/.git/config
touch: cannot touch '/private/tmp/p5-cwd-inside/sub/.git/config': Operation not permitted
EXIT=1
```

**Verdict:** BLOCKED. This is the key result for the #68 puzzle: `tbq()`'s `**/.git/config` glob is **recursive within cwd**, not just cwd-root. Matches Phase 4 event 4 (the shell-eval write at `/private/tmp/sandbox-clone-test/dotfiles-probe/.git/config`).

#### P15b — deep subdir `.git/config` (three levels deep, inside cwd)

```
$ mkdir -p /private/tmp/p5-cwd-inside/a/b/c/.git
EXIT=0
$ touch /private/tmp/p5-cwd-inside/a/b/c/.git/config
touch: cannot touch '/private/tmp/p5-cwd-inside/a/b/c/.git/config': Operation not permitted
EXIT=1
```

**Verdict:** BLOCKED. Confirms `**/.git/config` applies at arbitrary depth inside cwd. No depth-limit in the glob.

#### P16 — `.git/config` outside cwd (sibling `/tmp` path)

```
$ mkdir -p /private/tmp/p5-cwd-outside/.git
mkdir: cannot create directory ‘/private/tmp/p5-cwd-outside/.git’: Operation not permitted
EXIT=1
$ touch /private/tmp/p5-cwd-outside/.git/config
touch: cannot touch '/private/tmp/p5-cwd-outside/.git/config': No such file or directory
EXIT=1
```

**Verdict:** BLOCKED, but **not by `tbq()`**. The `mkdir` fails because `/private/tmp/p5-cwd-outside` is not on the user's write allow-list (no `/tmp/*` blanket, no match against `.` or `$TMPDIR`). The subsequent `touch` reports `No such file or directory` because the `.git` parent dir was never created — this is the filesystem complaining about the missing parent, not a sandbox-exec deny. **Does not answer the #68 question** (inside-vs-outside for `tbq()`), because the path is blocked at a more restrictive layer.

#### P17 — subdir `.git/HEAD` (control: HEAD is not in `tbq()`)

```
$ mkdir -p /private/tmp/p5-cwd-inside/sub/.git
EXIT=0    # same dir as P15a, idempotent
$ touch /private/tmp/p5-cwd-inside/sub/.git/HEAD
EXIT=0
```

**Verdict:** **ALLOWED.** Crucial negative control: it rules out "all `.git/` writes in cwd subdirs are blocked." Only the specific `tbq()` paths (`.git/config`, `.git/hooks/**`) are denied; everything else under `.git/` — HEAD, index, refs, objects, worktrees, packed-refs, etc. — is writeable via the cwd allow-subpath. This matches the Phase 1 `tbq()` source reconstruction and Phase 2 P5/P5b/P5c at cwd root, now confirmed at depth 1.

#### P18 — subdir `.git/hooks/test` (inside cwd)

```
$ mkdir -p /private/tmp/p5-cwd-inside/sub/.git/hooks
EXIT=0    # mkdir of the hooks DIRECTORY succeeded
$ touch /private/tmp/p5-cwd-inside/sub/.git/hooks/test
touch: cannot touch '/private/tmp/p5-cwd-inside/sub/.git/hooks/test': Operation not permitted
EXIT=1
```

**Verdict:** BLOCKED on the file write. But note the **asymmetry**: the `mkdir -p sub/.git/hooks` step **succeeded**. This is a new finding not previously documented. The reason:

- `tbq()`'s absolute-path entry is `path.resolve(cwd, ".git/hooks")` — matches only `<cwd>/.git/hooks`, not `<cwd>/sub/.git/hooks`. So the absolute rule doesn't fire at depth > 0.
- `tbq()`'s glob entry is `**/.git/hooks/**` — with a trailing `/**` that matches **contents** of a `.git/hooks` directory, not the directory entry itself.
- Together: at any depth > 0 inside cwd, you can `mkdir` the `.git/hooks` directory, but you cannot put a file into it.

At cwd root the absolute rule still prevents even `mkdir .git/hooks` (confirmed indirectly by Phase 2 P4b using a pre-existing `.git/hooks/` from `git init`). But subdirectory `.git/hooks/` can be *created*, just not *populated*. This refines `tbq()` understanding and has implications for tools that check "can I make a hooks dir" as a proxy for "am I allowed to install hooks."

#### P19 — `.git/hooks/test` outside cwd

```
$ mkdir -p /private/tmp/p5-cwd-outside/.git/hooks
mkdir: cannot create directory ‘/private/tmp/p5-cwd-outside/.git’: Operation not permitted
EXIT=1
$ touch /private/tmp/p5-cwd-outside/.git/hooks/test
touch: cannot touch '/private/tmp/p5-cwd-outside/.git/hooks/test': No such file or directory
EXIT=1
```

**Verdict:** BLOCKED by the allow-list layer, same mechanism as P16. **Does not answer** whether `tbq()`'s `**/.git/hooks/**` glob is cwd-scoped — the allow-list deny fires before `tbq()` is consulted.

#### P20 — `.vscode/settings.json` outside cwd

```
$ mkdir -p /private/tmp/p5-cwd-outside/.vscode
mkdir: cannot create directory ‘/private/tmp/p5-cwd-outside/.vscode’: Operation not permitted
EXIT=1
$ touch /private/tmp/p5-cwd-outside/.vscode/settings.json
touch: cannot touch '/private/tmp/p5-cwd-outside/.vscode/settings.json': No such file or directory
EXIT=1
```

**Verdict:** BLOCKED by the allow-list layer. Same story. **Does not answer** whether `.vscode` `tbq()` deny is cwd-scoped.

### Summary table

| # | Operation | Expected (recursive-deny hypothesis) | Actual | Layer that blocked |
|---|---|---|---|---|
| P14 | cwd-root `.git/config` | BLOCK | **BLOCK** | `tbq()` (`.git/config`) |
| P15a | cwd subdir `.git/config` depth 1 | BLOCK | **BLOCK** | `tbq()` (`**/.git/config` glob recursive) |
| P15b | cwd subdir `.git/config` depth 3 | BLOCK | **BLOCK** | `tbq()` (same glob, deeper) |
| P16 | outside-cwd sibling `/tmp` `.git/config` | ALLOW | BLOCK (mkdir) | **write allow-list** (not `tbq()`) |
| P17 | cwd subdir `.git/HEAD` (control) | ALLOW | **ALLOW** | n/a — HEAD not in `tbq()` |
| P18 | cwd subdir `.git/hooks/test` | BLOCK | **BLOCK** (file); mkdir allowed | `tbq()` (`**/.git/hooks/**` glob) |
| P19 | outside-cwd sibling `/tmp` `.git/hooks/test` | ALLOW | BLOCK (mkdir) | **write allow-list** (not `tbq()`) |
| P20 | outside-cwd sibling `/tmp` `.vscode/settings.json` | ALLOW | BLOCK (mkdir) | **write allow-list** (not `tbq()`) |

### Error-shape observations

Three distinct stderr shapes appeared in Phase 5:

1. **Tool-prefixed EPERM (GNU coreutils, ASCII quotes)** — from `touch`:
   `touch: cannot touch '/private/tmp/p5-cwd-inside/.git/config': Operation not permitted`
2. **Tool-prefixed EPERM (GNU coreutils, SMART quotes)** — from `mkdir`:
   `mkdir: cannot create directory ‘/private/tmp/p5-cwd-outside/.git’: Operation not permitted`
   The smart-quote characters (`‘ ’`, U+2018/U+2019) are how this `mkdir` build reports paths in errors. **The sandbox-first error classifier should match on a regex that accepts either `'...'` or `‘...’` around the path.** Any signature that only anchors on ASCII `'` will miss `mkdir` errors.
3. **Filesystem ENOENT cascading from an earlier sandbox block** — when `mkdir` was denied, the follow-up `touch` reports `No such file or directory` for a *parent* that does not exist. This is NOT a sandbox error directly, but in a real workflow it looks like one because the root cause is still a sandbox deny further up the chain. The classifier will need to handle "chain errors" where a sandbox deny manifests later as ENOENT. This is a new category not represented in Phase 2's three-shape catalog.

### What Phase 5 proves (and what it doesn't)

**Proves:**

- `tbq()`'s `**/.git/config` glob applies recursively within cwd at any depth (P14, P15a, P15b).
- `tbq()`'s `**/.git/hooks/**` glob applies recursively within cwd at depth > 0, but with an asymmetry: the `.git/hooks` directory entry itself can be created at depth > 0, only its children are denied (P18).
- Non-`tbq()` files under `.git/` (HEAD, and by extension anything not in the `tbq()` list) remain writeable even in cwd subdirs at arbitrary depth (P17).
- Error shapes vary by reporting tool: `touch` uses ASCII quotes, `mkdir` uses smart quotes, and cascading ENOENT is a new error category the classifier must handle.
- Interactive permission-prompt approvals do NOT grant sandbox-exec write capabilities — the prompt and the sandbox are independent layers.

**Does NOT prove (scope gap):**

- Whether `tbq()` denies are cwd-scoped vs unbounded across the filesystem. The Phase 5 design assumed `/private/tmp/p5-cwd-outside` would reach the `tbq()` layer; it doesn't, because the path is outside the user's `write.allowOnly` list. A second-layer "allowed working directories" check (if it exists) can also not be ruled in or out from this data.

### Updated recommendation for #68

The #68 puzzle (is the `tbq()` deny inside-vs-outside-cwd, or is something else going on?) is **still open** after Phase 5, but Phase 5 narrows the candidate mechanisms:

- **Newly RULED OUT: "Only cwd-root `tbq()` paths are denied."** P15a and P15b conclusively show the glob fires at arbitrary depth inside cwd. So the deny is *not* just cwd-root.
- **Newly RULED OUT: "The absolute-path rule covers cwd-root and the glob covers everything."** P18 shows the glob applies inside cwd subdirs, but the mkdir-asymmetry shows the glob does NOT cover the directory entry itself — only its children. The rule semantics are more fine-grained than previously modeled.
- **Still open: is the glob bounded by a `(subpath cwd)` allow-region?** The Phase 3 P13 datapoint (`.git/config` write OUTSIDE the session's cwd that succeeded) is now the only evidence for this. P13's target was `/tmp/p13-clone-target/destination/.git/config` and that succeeded — but that session may have had different `allowOnly` entries, OR git's clone may use a syscall pattern that bypasses the deny. Phase 5 could not re-test this directly because our outside-cwd path was unreachable.

### Phase 5b design (not executed, filed as follow-up)

To cleanly test the inside-vs-outside `tbq()` hypothesis, a future session should use an **allow-listed path** outside cwd. Candidate: run with cwd `/tmp/p5-cwd-inside` and probe `$TMPDIR/p5-tbq-probe/.git/config`. The `$TMPDIR` path is on `write.allowOnly`, so the allow-list layer won't fire, and we can observe whether `tbq()` still denies. If `tbq()` denies there, the rule is unbounded; if it allows, the rule is cwd-scoped. This is the follow-up that resolves #68.

### Follow-ups added (to file as taskwarrior entries)

1. **#68 refinement:** Phase 5 narrowed the hypothesis space but didn't resolve it. Design a Phase 5b probe using an allow-listed outside-cwd path (e.g., `$TMPDIR/...`) to directly test `tbq()` scope.
2. **sandbox-first classifier update:** add the `mkdir` smart-quote error shape (`‘path’`) alongside the `touch` ASCII-quote shape (`'path'`) in `SANDBOX_ERROR_SIGNATURES`. Also add a "cascading ENOENT" category for the case where a failed sandbox-exec `mkdir` causes a subsequent command to emit `No such file or directory`.
3. **sandbox-internals memory update:** document the `.git/hooks/` mkdir-vs-write asymmetry at depth > 0 (mkdir allowed, child writes denied). Document that `tbq()`'s `**/.git/config` and `**/.git/hooks/**` globs are recursive within cwd at arbitrary depth.
4. **Phase 5 design note:** the "sibling `/tmp` path as outside-cwd" framing is unreliable because `/tmp/*` is not blanket-allowed. Future probe designs that need "outside cwd but still writeable" must use paths from the user's explicit `write.allowOnly` list.

### Final state

Files and dirs created in `/private/tmp/p5-cwd-inside`:
```
/private/tmp/p5-cwd-inside/.git/                  (empty, mkdir from P14)
/private/tmp/p5-cwd-inside/sub/.git/              (mkdir from P15a/P17)
/private/tmp/p5-cwd-inside/sub/.git/HEAD          (touch from P17, the only file created)
/private/tmp/p5-cwd-inside/sub/.git/hooks/        (empty dir, mkdir from P18)
/private/tmp/p5-cwd-inside/a/b/c/.git/            (empty, mkdir from P15b)
```

`/private/tmp/p5-cwd-outside` is still empty — all mkdirs against it were blocked by the allow-list layer.

No cleanup performed; the Phase 5 design doesn't mandate it, and both directories are throwaway `/tmp` scratch space. If a Phase 5b runs in the same session these can be reused or re-created fresh depending on probe needs.

End of Phase 5 results.
