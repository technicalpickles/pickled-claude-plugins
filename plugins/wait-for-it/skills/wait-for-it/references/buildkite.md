# Buildkite probes

This machine's buildkite tool preference is `bktide`, not `bk` — a hook
intercepts raw `bk` calls and tells you to use `bktide` instead. Recipes below
use `bktide build <ref>` (not `bktide builds`, the list command, which returns
lowercase state strings — a different casing than the detail command below;
don't mix them up).

## A build reaching a terminal state

    bktide build <ORG>/<PIPELINE>/<NUM> --format json | jq -r '.state'

State values are UPPERCASE (`PASSED`, `FAILED`, `CANCELED`, ... — confirmed
against real builds in each of those three states). Do not try to enumerate
every possible state and filter to it; treat any change in the emitted string
as worth reporting.

## Per-job results as they land

    bktide build <ORG>/<PIPELINE>/<NUM> --format json --jobs \
      | jq -r '[.jobs[] | "\(.label // "?"):\(.state // "null")"] | sort | join(",")'

Jobs use `.label`, not `.name`. A job's `.state` can be `null` (seen on a real
build, on a step with no run state) — the `// "null"` guards that so the probe
never errors on it.

## The jq trap

A build's JSON can contain large multi-line fields (the commit message body).
Round-tripping that through a shell variable and `echo` risks truncation or
mangling. Pipe directly from the command, or write to a temp file under
`$TMPDIR` and `jq -f` it. Never do `echo "$json" | jq ...`.

## Notes

- Interval 30s or more.
- For diagnosing *why* a build failed, this is the wrong tool — use the
  `buildkite:investigating-builds` skill. `wait-for-it` only tells you that it
  finished.
