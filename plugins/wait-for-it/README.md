# wait-for-it

Turn "tell me when X happens" into a shell probe that only speaks up when X
actually happens.

A `/loop` or scheduled prompt re-runs the model every tick, so a tick where
nothing changed still costs a full turn and still emits a message. `Monitor`
and `Bash(run_in_background)` cost zero tokens while idle: they run a command,
and only the lines it prints become notifications. This plugin's skill steers
Claude to the second shape and gives it the pieces to do that well.

## What's in it

- **`wait-for-it` skill**: picks between one-shot (`Bash` background +
  `--once`) and ongoing (`Monitor`) watches, writes the probe contract
  (probe / condition / emit), and covers MCP-only sources via `mcporter`.
- **`watch-loop.sh`**: the polling loop. Emits an `armed, baseline=` line,
  one `changed:` line per change, and one `probe FAILED` line per failure, so
  a crashed probe never looks like "still waiting".
- **`probes/github-checks-settled.sh`**: a PR-checks probe that survives the
  check count growing mid-watch (reruns, late-added checks).
- **`SubagentStop` hook** (`hooks/subagent-done-marker.sh`): writes a marker
  at `$TMPDIR/wait-for-it-subagent-done/<agent_id>.json` when any subagent
  finishes. A subagent waiting on its own background child polls for that,
  since completion notifications only reach the top-level session. Requires
  `jq`.
- **Probe recipes** in `skills/wait-for-it/references/`: GitHub, Buildkite,
  local (tests, logs, ports, subagents), Datadog.

## Limits

`Monitor` dies with the session. Nothing here arms a watch that outlives it;
the skill says so instead of faking it with a cron.

## Tests

```bash
cd plugins/wait-for-it
bats tests/
```

Trigger evals: see [`skills/wait-for-it/evals/README.md`](skills/wait-for-it/evals/README.md).
