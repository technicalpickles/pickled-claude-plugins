# Verifying park and unpark

Park's behavior has three layers, and each needs a different kind of check. A unit test of one layer says nothing about the others.

| Layer | What it is | How it is checked |
|---|---|---|
| Hook | Code that puts `Park vault:` and `Park destination:` lines in front of the model | `bats tests` (Python hook), `claude plugin test plugins/second-brain` (the `skill.prompt` mod). Mocked engine, fast, free. |
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
| `dest` | The `destination` plugin setting reaches the hook as `CLAUDE_PLUGIN_OPTION_DESTINATION` and the command runs |

## Lessons baked into the script

- **Assert on the injected value, not the label.** The skill text itself contains the words `Park vault:` and `Park destination:`. A bare grep passes with no hook at all, or fails a "line is absent" check. Match `Park vault: <path>` and `Park destination: <template>`.
- **Read the on-disk transcript.** `--output-format stream-json` does not include the expanded skill text. `~/.claude/projects/*/<session_id>.jsonl` does.
- **Allow `Skill` in `--allowedTools`.** Without it, plain-word parks fail with an opaque "Skill load threw an error" that looks like a product bug.
- **Give the vault with `--add-dir`, and keep scratch files under the working directory.** Headless runs block `cat` and redirects to paths outside the allowed directories. A real vault outside the cwd needs the same allowance (an additional directory or sandbox write rule), or parks stop at a permission prompt.
- **Settings for inline plugins** go under `pluginConfigs` keyed `<name>@inline`, with an `options` object.

## Known gaps

- **Slash parks get no `Park destination:` line.** It comes from the `PostToolUse:Skill` Python hook, which does not fire for `/agent-meta:park`. The vault line works for slash because it comes from the `skill.prompt` mod. Moving the destination into that mod would close the gap.
- **Default-vault resolution is unit-tested only.** The script sets `park_vault` explicitly. Reading `~/.claude/second-brain.md` is covered by `claude plugin test`, not end to end, because it reads the real `HOME`.
- **Interactive terminal and desktop app are not exercised.** Only `claude -p`.
- **Model behavior varies.** A single failed `behavior` check can be flake.
