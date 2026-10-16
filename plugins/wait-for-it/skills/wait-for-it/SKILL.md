---
name: wait-for-it
description: "Use when the user wants to be told when something happens later, or asks you to monitor or watch something still in progress: CI or a build finishing, PR checks or reviews landing, a deploy or release going out, a feature flag taking traffic, a log line appearing, a metric crossing a threshold. Triggers on \"monitor CI\", \"monitor the PR\", \"monitor the deploy\", \"watch it through deploys\", \"ping me when\", \"tell me as soon as\", \"let me know when\", \"notify me if\", \"wait for it to finish\". Also use when monitoring is the second half of a request (\"open the PR and keep an eye on the checks\", \"ship it, then watch the canary\", \"retry the job and stay on it\"): load this before doing the first step, so a watch gets armed instead of a blocking `gh run watch` or a sleep loop. Also use when a prompt-cron or /loop is polling with no-op ticks. Do NOT use for reading current state once (just read it), for setting up permanent alerting (Datadog monitors, pager rules), or for a watch that must survive the session ending."
---

# wait-for-it

Turn "tell me when X happens" into a shell probe that emits only when X
actually happens.

## The failure this exists to prevent

A scheduled task or a dynamic `/loop` re-evaluates a **prompt** every tick. A
tick where nothing happened still costs a full model turn and still emits a
message. Observed: a 26-second Opus turn whose entire output was "No new hits."

`Monitor` and `Bash(run_in_background)` cost **zero tokens** while nothing is
happening, because they run a command and only your printed lines become
notifications.

## Step 1: pick the tool

| What the user wants | Use |
|---|---|
| One notification total, then done | `Bash` with `run_in_background: true`, running `watch-loop.sh --once` |
| One per occurrence, indefinite | `Monitor` with `timeout_ms` at the max, re-armed on each expiry |
| One per occurrence, until a known time/tick budget runs out | `Monitor`, with `--max-ticks` set from that budget |
| One per occurrence, until the target reaches a known terminal state | `Monitor` with `timeout_ms` at the max, re-armed on each expiry, open-ended (no `--once`/`--max-ticks`) — `watch-loop.sh` has no "stop when terminal" flag, so judge completion from the emitted lines and stop the `Monitor` yourself with `TaskStop` |
| Must survive the session ending | **Stop.** See "The session ceiling" below. |

Ask which, if it is not obvious. "Ping me when the first hits come in" is
ambiguous between row 1 and row 2: the user says *first*, which sounds
one-shot, but may want every subsequent one too. Do not default to `Monitor`
because it is the tool with "monitor" in the name. And do not reach for
`--once` just because a scenario has a "known end" — `--once` stops after the
first event, not after the target finishes.

Every `Monitor` expires after `timeout_ms` (default 5 minutes, capped at 30).
Set it to the max for anything that could outlast the default, and when the
expiry notice arrives, re-arm with the same probe. Re-arming takes a fresh
baseline, so compare the new `armed, baseline=` line against the last state
you saw: if it differs, the change happened during the gap, and that is an
event. For row 3, size `--max-ticks` against the time left, not the original
budget.

## Step 2: write the probe contract

Write all three down **before** arming anything:

- **probe** — a shell command that prints current state and exits 0.
- **condition** — which change earns an event.
- **emit** — what the notification says. This is read by someone who has been
  away for an hour, so `first GraphQL hit on checkout-v2 flag: 0 -> 3` beats
  `changed`.

If you cannot name a shell command for the probe, that is the real problem —
go to "MCP-only sources" below. It is not a reason to fall back to a prompt.

## Step 3: arm it

Never hand-roll the loop. Use the script:

    watch-loop.sh --probe '<cmd>' [--interval SECS] [--label TEXT] [--once] [--max-ticks N]

It emits `armed, baseline=<state>` on the first tick, one `changed:` line per
change, and one `probe FAILED rc=N` line per failure. It exits 1 rather than
arming if the probe fails on the very first call.

Choose `--interval`: 30s or more for anything hitting a remote API (rate
limits), 1s or less only for local checks.

### When the probe needs a file

The moment a probe involves real parsing (`jq`, `awk`, `sed` with actual
logic) rather than a bare command (`nc -z`, `grep -c`, `test -f`), write it
to a file first — even a one-line `jq` filter. Escaping a nested-quote
pipeline correctly inside a `--probe` string is easy to get wrong, and a
file can be read back and reviewed before it runs unattended for hours.

`watch-loop.sh` needs no change for this: `run_probe` already does
`eval "$probe"`, so `--probe '/path/to/script.sh <args>'` runs a file the
same as any inline command.

Name the file from `--label`, with a uniqueness guard — `$TMPDIR` is shared
across every session on this machine, so a fixed name risks a stale write
from a different session:

    mktemp -t "wait-for-it-<label>.XXXXXX"

The file itself is a probe like any other: print current state, exit 0
normally, nonzero + stderr on failure.

Some probes are common enough to ship instead of writing fresh each time —
see `probes/` (currently just `github-checks-settled.sh`).

A subagent waiting on its own dispatched background/nested `Agent`-tool
child needs a hook, not a probe alone — see the plugin's `SubagentStop` hook
(`hooks/subagent-done-marker.sh`, registered automatically) and `references/local.md` ("A subagent's own background/nested Agent-tool
child finishing").

## Step 4: notify

On a real change, send `PushNotification`. On the `armed` baseline line, never.

`PushNotification` self-suppresses when the user is at the terminal and returns
"not sent" — that is the expected result, not a failure. Do not retry it, and
do not treat it as an error.

## MCP-only sources

**The trap:** "`Monitor` needs a command, and this only exists behind an MCP
tool, so a prompt loop is the only option." That is wrong, and it is the exact
reasoning that produces the 26-second no-op turns.

`mcporter` turns any configured MCP tool into a one-shot shell command:

    mcporter call <server>.<tool> key=value

It imports server definitions from Claude Code's own config **and reuses its
OAuth tokens** — verified 2026-08-28, no `mcporter auth` step needed. If a
server works in Claude Code, it works from the shell. See
`references/datadog.md`.

## The session ceiling

A `Monitor` dies when the session ends, and re-arming only works while the
session is alive. There is currently **no supported way** to arm a watch here
that outlives the session.

If the user needs that, say so plainly and stop. Do not fake it with a cron, do
not promise it will keep running. That capability needs an out-of-band poller
(a launchd/systemd job, a server-side monitor) that this skill does not
provide.

It is fine to point at the real alternative (a server-side monitor, a proper
alerting rule) if one exists — that is more useful than a bare "can't do
that." But don't start building it. Standing up paging/alerting
infrastructure is a bigger, more permanent action than the user asked for;
say what the real option is and confirm before touching it.

## Rationalizations

| Thought | Reality |
|---|---|
| "It's MCP-only, so I need a prompt loop." | `mcporter call` makes it a shell command. |
| "I'll just grep for the success marker." | Then a crash looks identical to still-running. Probe failure must emit. |
| "A cron every 5 min is basically the same." | It costs a model turn and a message per tick, forever. |
| "I'll skip the baseline event, it's noise." | It is the only proof that auth works and the query parses. |
| "`tail -f log \| grep -m 1` gives me one notification." | If the log goes quiet after the match, `tail` never gets SIGPIPE and it hangs armed. |
| "I'll set a long interval so it's cheap." | Cost per tick is the problem, not tick frequency. Interval tuning does not fix a prompt loop. |
| "Given it's 'ping me the moment it happens' for something that could take hours, my instinct is a Datadog monitor with Slack alerting is the right tool (fires immediately, no session needs to stay alive)." | A `Monitor` re-armed on each expiry runs for the life of the session at zero cost while idle — that is what it is for. "Could take hours" is not a reason to skip straight to permanent external infra (or list `/loop`/`/schedule` as equally valid); it is a reason to use `--max-ticks`/`timeout_ms` and re-arming correctly. |

## Probe recipes

Load only the one in play:

- `references/github.md` — PR checks, Actions runs
- `references/buildkite.md` — builds, jobs
- `references/local.md` — test runs, log files, ports
- `references/datadog.md` — metrics, logs, via `mcporter`

Some recipes point to a shipped script under `probes/` instead of an inline
snippet — run it directly rather than retyping its logic.
