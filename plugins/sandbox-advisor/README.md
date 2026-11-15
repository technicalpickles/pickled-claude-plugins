# sandbox-advisor

A `PostToolUseFailure` hook that, when a Bash command fails, tells you whether it
failed because of a *known* Claude Code sandbox limitation, and what to do about
it. The message is advisory, not a directive.

## What it does

Knowledge lives in a **failure-mode registry**. When a Bash command **fails**,
the hook identifies the mode in two passes:

1. **Error text alone**, for failures distinctive enough that the command
   doesn't matter (a sorbet LMDB abort looks the same three wrappers deep).
2. **Command shape plus a fingerprint**, for everything else: the command
   picks the mode, and the failure text has to confirm it was the sandbox and
   not an ordinary failure of that command.

The advice prefers a fix that works *inside* the sandbox. Unsandboxing is named
only for modes with no in-sandbox fix.

| Mode | Example failure | Advice |
|---|---|---|
| `git-path-deny` | `unable to create file .mcp.json: Operation not permitted` | Re-run unsandboxed. These paths (`.git/config`, `.git/hooks/*`, `.claude/agents/*`, `.claude/commands/*`, `.mcp.json`, `.vscode/*`, `.idea/*`, `.gitmodules`, shell rc files) are denied regardless of `allowWrite`. A worktree create that died partway already made the branch, so retry without `--create`/`-b`. |
| `git-cwd-scope` | `Unable to create '/other/repo/.git/index.lock': Operation not permitted` | `EnterWorktree` into that repo, then re-run sandboxed. Write access is anchored to the session's working directory, and a shell `cd` or `git -C` doesn't move it. Detected by the lock path (or `cd`/`-C` target) falling outside the hook payload's `cwd`. |
| `git-worktree-delete` | `failed to delete '.../worktrees/x': Operation not permitted` | Re-run unsandboxed; if the directory survives, `/bin/rm -rf` it (plain `rm` is often a trash alias). |
| `git-write` | any other git write EPERM | Identify the case first: `EnterWorktree` if the repo is outside the working directory, unsandbox if it's a denied path. |
| `git-ssh` | `ssh_dispatch_run_fatal: Connection to UNKNOWN port 65535`, `port 22: Operation not permitted` | Raw TCP to port 22 is blocked. If agent SSH goes through a local relay (an ssh `ProxyCommand` to an allowlisted localhost proxy), check and restart the relay. With no relay, re-run unsandboxed. **Don't** switch the remote to HTTPS: that pushes with a different credential than the SSH key. |
| `srb` | `mdb_error="Operation not permitted"` | Re-run unsandboxed. Sorbet's LMDB store uses SysV semaphores the sandbox denies, even with no cache dir. |
| `keychain-write` | `writing destination keychain`, `SecKeychainItemCreateFromContent ... Operation not permitted` | Re-run just the write step unsandboxed; reads work sandboxed afterward. |
| `bun-tmpdir` | `bun is unable to write files to tempdir: EPERM` | Re-run with `BUN_TMPDIR="$TMPDIR"`. No unsandbox needed. |
| `gem-spec-cache` | `Operation not permitted @ dir_s_mkdir - ~/.cache/gem/specs` | Re-run with `GEM_SPEC_CACHE="$TMPDIR/gemspecs"`. No unsandbox needed. |
| `ps-top` | `operation not permitted: ps` | Re-run unsandboxed (setuid binaries; read-only and safe). |

Otherwise it stays silent. Adding a mode is a registry entry (fingerprints,
optional command matcher, advice) plus a corpus case.

## Why reactive (not a proactive guard)

A command-name guard mis-fires: `git add` fails sandboxed only a few percent of
the time. Acting on the actual failure means a command that succeeds sandboxed
is never touched, so the hook can never cause a false sandbox bypass.

## Who it's for

Auto-mode already retries unsandboxed for you. That's the problem this hook
works against: a reflexive unsandbox retry "works" for a cwd-scope mismatch or
a down SSH relay too, and hides the real fix. The advice lands at the moment of
failure, which is when that reflex kicks in. It also covers contexts where a
hard EPERM is a stall instead of a recovery: subagents, cron/headless runs, and
sessions not on auto-mode.

## Guarantees

- **Fail-open.** Any internal error exits 0 with no output; the raw failure
  surfaces unchanged. A broken advisor never wedges work.
- **No rewrite, no block, no state.** It only ever adds advice to an
  already-failed command.

## Testing against real history

`tests/fixtures/replay-corpus.jsonl` is the regression corpus: failure shapes
taken from real sandboxed sessions (paths rewritten), each labeled with the mode
the hook should pick or `null` for silence. It includes the false positives the
replay turned up, like an `index.lock: File exists` from a concurrent git
process.

To check a change against your own sessions, export failed sandboxed Bash calls
as JSONL (`{"command", "error", "cwd", "unsandboxed"}`, one per line) and run:

```bash
python3 tools/replay.py failures.jsonl                 # counts per mode
python3 tools/replay.py failures.jsonl --show git-cwd-scope   # the calls behind one mode
```

`cwd` matters: it's the session's working directory as recorded in the
transcript, which is also what the hook payload carries, and it's what
separates `git-cwd-scope` from a plain git EPERM. Session transcripts under
`~/.claude/projects/` record it on every assistant message. If you use
[cq](https://github.com/technicalpickles/cq), something like:

```sql
with b as (
  select c.session_id, c.timestamp, c.message_uuid, c.input, r.is_error, r.content as err,
         row_number() over (partition by c.session_id order by c.timestamp) as rn
  from tool_calls c join tool_results r using (tool_use_id) where c.name = 'Bash'
), cw as (
  select json->>'uuid' as uuid, json->>'cwd' as cwd from raw_records where json->>'type' = 'assistant'
)
select a.input->>'command' as command, a.err as error, cw.cwd
from b a left join cw on cw.uuid = a.message_uuid
where a.is_error
  and coalesce(json_extract_string(a.input, '$.dangerouslyDisableSandbox'), 'false') <> 'true'
```

When a shape shows up that the hook gets wrong (or misses), add a sanitized
line for it to the corpus.
