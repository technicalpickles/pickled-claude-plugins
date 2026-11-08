# Verifying park and unpark

Park's behavior has three layers, and each needs a different kind of check. A unit test of one layer says nothing about the others.

| Layer | What it is | How it is checked |
|---|---|---|
| Hook | A mod that puts a `Park vault:` line in front of the model | `claude plugin test` in `plugins/second-brain`. Mocked engine, fast, free. |
| Delivery | Whether the real engine fires the hook, with the skill name and environment you assumed | `tests/e2e/park-vault.sh`, deterministic: grep the session transcript for the injected line. |
| Behavior | Whether the model then writes the file where the vault's `CLAUDE.md` says | Same script, model-dependent: look at the filesystem. Rerun a failure once before calling it a regression. |

## Running the end-to-end check

```bash
plugins/agent-meta/tests/e2e/park-vault.sh
```

It runs five headless `claude -p` sessions (about three minutes, real tokens) with `--plugin-dir` pointing at this checkout, a scratch vault, and a scratch working directory. The script exports `SB_NOTE_VAULT` at the scratch vault, which the `park-vault` mod prefers over `second-brain.md`, so it never touches your real vault. Run it before releasing a change to park, unpark, or the `park-vault` mod. It is not in CI.

| Case | Proves |
|---|---|
| `slash` | `/agent-meta:park` gets the vault line, writes `YYYYMMDDHHMM topic.md` in the vault, and the `unpark` line is an absolute path |
| `plain` | The Skill-tool path gets the same |
| `unpark` | `unpark` gets the line and finds the file |
| `both` | A vault is configured and `.parkinglot/` holds an older, untimestamped park: `unpark` lists both |
| `noparking` | A vault whose `CLAUDE.md` has no `## Parking` section sends the park to `.parkinglot/` with a timestamped name and leaves the vault empty |

## Lessons baked into the script

- **Assert on the injected value, not the label.** The skill text itself contains the words `Park vault:`. A bare grep passes with no hook at all. Match `Park vault: <path>`.
- **Read the on-disk transcript.** `--output-format stream-json` does not include the expanded skill text. `~/.claude/projects/*/<session_id>.jsonl` does.
- **Allow `Skill` in `--allowedTools`.** Without it, plain-word parks fail with an opaque "Skill load threw an error" that looks like a product bug.
- **Give the vault with `--add-dir`, and keep scratch files under the working directory.** Headless runs block `cat` and redirects to paths outside the allowed directories. A real vault outside the cwd needs the same allowance (an additional directory or sandbox write rule), or parks stop at a permission prompt.
- **Point the vault with `SB_NOTE_VAULT`, not `HOME`.** The script finds transcripts under `$HOME/.claude/projects` and `claude -p` needs the real config dir for auth, so a scratch `HOME` breaks both. Forgetting to export `SB_NOTE_VAULT` would make a run write to your real default vault.

## Known gaps

- **Default-vault resolution is unit-tested only.** The script sets `SB_NOTE_VAULT` explicitly. Reading `second-brain.md` from `CLAUDE_CONFIG_DIR` or `~/.claude` is covered by `claude plugin test`, not end to end, because it reads the real config dir.
- **Interactive terminal and desktop app are not exercised.** Only `claude -p`.
- **Model behavior varies.** A single failed `behavior` check can be flake.
