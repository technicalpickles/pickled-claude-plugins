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

End of results.
