# Woodpecker states and manual commands

## How the snapshot decides

| Source | Detail |
|--------|--------|
| Pipeline status | `success`, `failure`, `error`, `killed`, `canceled`, `running`, `started`, `pending`, `blocked` map to a state. Anything else reports `unknown` with the raw value. |
| Seen on a live server | `success`, `failure`, `running`, `killed`, `canceled`. The rest are expected from upstream but unseen. |
| First failure | The first step in order whose state is a failure. Steps after it are usually `skipped`. |
| Passed with a failed step | A step with `failure: ignore` can fail while the pipeline passes. Reported as a warning. |

## Manual commands

`<repo>` is `owner/name` or a numeric repo ID. A failed pipeline still exits 0, so read the status from the output.

```bash
# Compact list, newest first
woodpecker-cli pipeline ls <repo> --limit 20 --output 'go-format={{.Number}} {{.Status}} {{.Commit}} {{.Branch}}'

# Step states for one pipeline
woodpecker-cli pipeline ps <repo> <n> --format '{{.workflow.Name}}/{{.step.Name}}={{.step.State}}'

# One step's log (name or PID). Output has ANSI color codes.
woodpecker-cli pipeline log show <repo> <n> <step>
```

## Quirks

- **Template keys differ by command.** `pipeline ls` uses Go struct names (`.Number`, `.Commit`). `pipeline ps` uses lowercase keys (`.workflow`, `.step`); `{{.Step.Name}}` prints `<no value>`.
- **The default `pipeline ls` table prints each full commit message**, multi-line. Use `go-format` for anything you parse.
- **No lookup by commit.** The snapshot scans the newest 100 pipelines and matches the commit itself.
- **Pipeline numbers can have gaps.** Numbers missing from `pipeline ls` returned 404 from `pipeline show`, so the list looked complete. Why they vanish is unknown (checked on one repo).
- **No JSON output** on these commands, only tables and Go templates.
