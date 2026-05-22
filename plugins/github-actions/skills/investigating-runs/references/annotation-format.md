# GitHub Actions annotation format

GHA workflows emit "workflow commands" to logs using a special syntax. These commands surface as annotations in the GitHub UI and in API responses. This is the format the `gha-snapshot` Annotations section extracts from `gh run view --log-failed` output.

## Syntax

```
::<command> <key>=<value>,<key>=<value>::<message>
```

The double-colon prefix and suffix bracket the directive. Parameters between are `key=value` pairs separated by commas. Everything after the final `::` is the message body.

Whitespace is significant: the line must start with `::` and the command name follows directly with no space.

## Annotation commands

| Command | Use | Renders as |
|---------|-----|------------|
| `::error::` | A fatal problem | Red ❌ in the UI, file/line if provided |
| `::warning::` | A non-fatal problem | Yellow ⚠️ |
| `::notice::` | An informational message | Blue ℹ️ |

These three are the annotations the snapshot extracts and groups by job.

## Parameters

| Param | Example | Effect |
|-------|---------|--------|
| `file` | `file=src/app.ts` | Repo-relative path the annotation is anchored to |
| `line` | `line=42` | Starting line in the file |
| `endLine` | `endLine=45` | Ending line (for multi-line ranges) |
| `col` | `col=10` | Starting column |
| `endColumn` | `endColumn=20` | Ending column |
| `title` | `title=Type error` | Short header shown above the message |

Annotations with `file=` and `line=` show up inline in the GitHub "Files changed" view of the associated PR, which is often the highest-signal place to look first.

## Examples

```
::error file=src/foo.ts,line=42::Expected 1, got 2
::warning::Deprecated API used
::notice file=README.md,line=5,title=Style::Missing trailing newline
::error file=src/app.ts,line=10,endLine=15,col=4,endColumn=12,title=Type error::Type 'string' is not assignable to type 'number'
```

## Group markers

Used to bracket sections of log output. Not annotations themselves, but useful for understanding step boundaries when reading raw logs.

```
::group::Installing dependencies
npm ci
...
::endgroup::
```

The GitHub UI collapses everything between `::group::` and `::endgroup::` into a foldable block. `gh run view` preserves them as plain text.

## Masking

```
::add-mask::<value>
```

Adds `<value>` to GHA's secret masking list. Any subsequent occurrence of that string in logs is replaced with `***`. Commonly used to mask credentials that come from a source other than `secrets.*` (e.g., output of a `vault read` step).

If you see `::add-mask::` in logs, masking is active for that value. The presence of `***` in later log lines is the masker doing its job.

## Output (deprecated form)

You may still see this in older workflows:

```
::set-output name=foo::bar
```

This is **deprecated**. Modern equivalent:

```bash
echo "foo=bar" >> "$GITHUB_OUTPUT"
```

If a workflow still uses `::set-output::`, it'll work but logs a deprecation warning. The fix is straightforward — replace with the env-file form.

## Where annotations surface

| Surface | What you see |
|---------|--------------|
| Run summary page | Bulleted list at the top with severity icons |
| Files changed tab (PR view) | Inline marker on the annotated line if `file=` + `line=` set |
| `gh run view --log-failed` | Plain text in the log stream, prefixed with `<job>\t<step>\t::error::...` |
| Check-run annotations API | Structured JSON via `gh api repos/{owner}/{repo}/check-runs/{id}/annotations` |
| GHA annotation in PR conversation | Posted as a check-run annotation under the workflow's check |

The check-run annotations API is the most structured source — useful when you need programmatic access (file path, line number, annotation level) without parsing log text. The snapshot prefers parsing logs because that gets you annotations from the failed steps directly without an extra API hop and works even if check-run annotations weren't created (some annotations only flow through if the action explicitly creates a check run).

## Limits

GitHub caps annotations:

- **10 errors, 10 warnings, 10 notices per run** at the run-summary level
- Per-check-run annotations: 50 per request to the check-runs API
- Annotation message body capped around 4 KB

If you don't see an annotation you expect, it may have been clipped by these limits, especially in workflows that emit many.
