# Verifying park and unpark

Park's behavior has three layers, and each needs a different kind of check. A unit test of one layer says nothing about the others.

| Layer | What it is | How it is checked |
|---|---|---|
| Hook | Mods that put `Park vault:` and `Park destination:` lines in front of the model | `claude plugin test` in `plugins/agent-meta` (destination) and `plugins/second-brain` (vault). Mocked engine, fast, free. |
| Delivery | Whether the real engine fires the hook, with the skill name and settings you assumed | `tests/e2e/park-vault.sh`, deterministic: grep the session transcript for the injected line. |
| Behavior | Whether the model then writes the file where the vault's `CLAUDE.md` says | Same script, model-dependent: look at the filesystem. Rerun a failure once before calling it a regression. |

## Running the end-to-end check

```bash
plugins/agent-meta/tests/e2e/park-vault.sh
```

It runs five headless `claude -p` sessions (about two minutes, real tokens) with `--plugin-dir` pointing at this checkout, a scratch vault, and a scratch working directory. It never touches your real vault or `~/.claude/second-brain.md`. Run it before releasing a change to park, unpark, the `park-vault` mod, or the destination settings. It is not in CI.

| Case | Proves |
|---|---|
| `slash` | `/agent-meta:park` gets the vault line, writes `YYYYMMDDHHMM topic.md` in the vault, and the `unpark` line is an absolute path |
| `plain` | The Skill-tool path gets the same |
| `unpark` | `unpark` gets the line and finds the file |
| `off` | `park_in_vault: false` injects nothing and parks to `.parkinglot/` |
| `dest` | The `destination` plugin setting reaches a slash park and the command runs |

## Lessons baked into the script

The general rules (assert on the value not the label, read the on-disk transcript, `Skill` in `--allowedTools`, `--add-dir` for the vault, `<name>@inline` settings) are in [docs/testing-plugins.md](../../../docs/testing-plugins.md). Park adds one: a real vault outside the cwd needs the same allowance, or parks stop at a permission prompt.

## Known gaps

- **Default-vault resolution is unit-tested only.** The script sets `park_vault` explicitly. Reading `~/.claude/second-brain.md` is covered by `claude plugin test`, not end to end, because it reads the real `HOME`.
- **Interactive terminal and desktop app are not exercised.** Only `claude -p`.
- **Model behavior varies.** A single failed `behavior` check can be flake.
