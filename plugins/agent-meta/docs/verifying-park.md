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

## Checking park's output shape and resumability

`park-vault.sh` checks where a park lands. `tests/park-eval/` checks what is in it, and whether a session can resume from it. Run it before releasing a change to park's wording, and always against a control: snapshot the previous version (`git archive origin/main plugins/agent-meta | tar -x -C "$ROOT"`) and run both, at least five reps each. One run of either proves nothing.

```bash
plugins/agent-meta/tests/park-eval/run-park.sh control "$ROOT/plugins/agent-meta" 5 "$RUNS"
plugins/agent-meta/tests/park-eval/run-park.sh variant "$PWD/plugins/agent-meta" 5 "$RUNS"
python3 -I plugins/agent-meta/tests/park-eval/score.py "$RUNS"
plugins/agent-meta/tests/park-eval/run-unpark.sh variant "$RUNS"
python3 -I plugins/agent-meta/tests/park-eval/score-unpark.py "$RUNS"
```

Each run spends real tokens (about 10 parks and 5 resumes per label). Two scratch repos stand in for a session:

| Scenario | State | Parks into |
|---|---|---|
| `ratelimit` | In progress: a failing test, an uncommitted change, house rules, one rule `CLAUDE.md` already carries, a question that blocks step 2 | A scratch vault |
| `csvexport` | Clean: everything committed, one next step | `.parkinglot/` |

`score.py` reads each park file and the closing message. It counts the prompt's sentences and how many restate another section, whether the `unpark` path is absolute, whether a rule `CLAUDE.md` already carries was copied into the prompt, `(read)` files, how many of the scenario's key facts survived, and whether the closing message puts the path in a fenced block exactly once, inside the `unpark` line. `run-unpark.sh` then resumes each `ratelimit` park and `score-unpark.py` grades it from the transcript: the fix landed, `make test` ran and bare `pytest` did not, nothing was pushed, `server.py` was left alone, the handoff file was not edited, and the blocking question was asked.

- **Isolate the vault.** `run-park.sh` points `SB_NOTE_VAULT` at a scratch vault. A path that does not exist is not enough: the hook falls back to your default vault and the eval writes a fictional park into it. Use a real directory whose `CLAUDE.md` has no `## Parking` section for the `.parkinglot` case.
- **The session is a narrative.** The scenario text stands in for a real transcript, so this tests the skill's wording, not how the model reads a long session.
- **Skip the report-format column.** `score-unpark.py` reads only the final message, and unpark's report is mid-transcript text.

## Lessons baked into the script

The general rules (assert on the value not the label, read the on-disk transcript, `Skill` in `--allowedTools`, `--add-dir` for the vault, `<name>@inline` settings) are in [docs/testing-plugins.md](../../../docs/testing-plugins.md). Park adds two:

- **A real vault outside the cwd needs the same allowance** (an additional directory or sandbox write rule), or parks stop at a permission prompt.
- **Point the vault with `SB_NOTE_VAULT`, not `HOME`.** The script finds transcripts under `$HOME/.claude/projects` and `claude -p` needs the real config dir for auth, so a scratch `HOME` breaks both. Forgetting to export `SB_NOTE_VAULT` would make a run write to your real default vault.

## Known gaps

- **Default-vault resolution is unit-tested only.** The script sets `SB_NOTE_VAULT` explicitly. Reading `second-brain.md` from `CLAUDE_CONFIG_DIR` or `~/.claude` is covered by `claude plugin test`, not end to end, because it reads the real config dir.
- **Interactive terminal and desktop app are not exercised.** Only `claude -p`.
- **Model behavior varies.** A single failed `behavior` check can be flake.
