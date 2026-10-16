# Local probes

## A file growing / a log line appearing

Count of matching lines. Prefer this over `tail -f | grep` when you want a
*count* that `watch-loop.sh` can diff.

    grep -c 'ERROR' /path/to/app.log

When you genuinely want one event per matching line as it is written, skip
`watch-loop.sh` and give `Monitor` the tail directly — but widen the pattern so
a crash is not silent:

    tail -f /path/to/app.log | grep -E --line-buffered 'ERROR|Traceback|FAILED|Killed|OOM'

Every pipe stage must flush per line: `grep` needs `--line-buffered`, `awk`
needs `fflush()`. Never use `| head -N` — it cannot flush, so it delivers
nothing until N matches accumulate.

## A port becoming ready

    nc -z localhost 3000 && echo up || echo down

Both branches of `&&`/`||` succeed, so this probe can never itself register a
`probe FAILED` — a broken `nc` looks identical to a real "down". Fine for
`nc`, which rarely breaks on its own; if that risk matters more here, use a
command that can actually fail instead of swallowing its exit code.

## A test run finishing

Single notification, so this is a `Bash(run_in_background)` case, not a
`watch-loop.sh` case:

    until [ -f .test-done ]; do sleep 1; done; echo "tests finished"

## A subagent's own background/nested Agent-tool child finishing

A subagent that dispatches its own background child (`Agent` tool,
`run_in_background: true`) gets no completion notification of its own --
that delivery only reaches the top-level session. Reading/tailing the
child's transcript to detect completion is explicitly disallowed by the
`Agent` tool itself. Do not hand-roll a sleep-and-poll loop here (observed:
a subagent burning 12 manual `echo idle`/`echo waiting` turns waiting for a
notification that structurally could never arrive) -- there is a real,
sanctioned marker to poll instead.

**Setup:** none. This plugin registers `hooks/subagent-done-marker.sh` as a
`SubagentStop` hook with no matcher, so it fires for every subagent at every
nesting depth and writes a marker keyed by `agent_id`.

**Then probe** for the marker the same way as any other single-notification
case, once you have the child's `agent_id` (returned in the dispatch's own
tool result):

    until [ -f "${TMPDIR:-/tmp}/wait-for-it-subagent-done/<agent_id>.json" ]; do sleep 2; done

This works at any depth -- a subagent polling for its *own* dispatched
child's marker behaves identically to the top-level session polling for one
of its direct children. Verified live 2026-09-11 against a real depth-2
nested dispatch (harness-reported `subagent_stats.max_depth: 2`). A first docs-only pass at
this question concluded the opposite ("hooks only run at the top level")
before it was actually tested -- don't trust an unverified claim about
harness internals here, confirm live if it matters.

## Notes

- Interval 1s or less is fine here; nothing is rate-limited.
- Use `$TMPDIR`, not `/tmp`, for any scratch state the probe writes. Plain
  `/tmp` is the single largest source of self-inflicted sandbox EPERMs.
