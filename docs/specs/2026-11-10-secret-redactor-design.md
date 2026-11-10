# secret-redactor plugin: design

Status: draft. The core mechanism was spiked on 2026-11-10 against Claude Code 2.1.310 in headless (`claude -p`) mode. Sections say which claims were observed and which are still open.

Tracked in taskwarrior as `03ef7b88-297a-4d8b-9aa8-44c5f5a66901`.

This doc says what a `secret-redactor` plugin should do, how it decides what counts as a secret, and where it falls short.

## The problem

Secrets end up in session transcripts, and a transcript is a durable file that gets searched, summarized, synced, and read by later sessions.

One real path, with names removed:

1. A task runner loaded a `.env` file, so every recipe it ran had the whole file in its environment.
2. The user pressed Ctrl+T during a long deploy. macOS printed the runner's child process line, which carried every variable and its value, into the terminal.
3. A later `read_terminal` tool call (an MCP tool that returns the terminal's text) copied that screen into the transcript.

The agent did nothing wrong in steps 1 and 2. The leak happened at the last step, where tool output enters the conversation.

A second path was the agent's own: it queried old transcripts for secret-shaped strings and tried to mask them by length. Short passwords slipped through the mask and were printed in clear text. A mask that guesses by shape misses exactly the secrets that don't have a shape.

## Decision: redact tool output by exact value

A PostToolUse hook replaces known secret values in a tool's output before it reaches the model. The match is against the actual values from the user's secret sources, not against patterns. Shape patterns stay as a second layer for secrets the sources don't know about.

Why exact values first:

- **Short passwords have no shape.** A 12-character password with mixed case looks like any other string. Only knowing the value finds it.
- **Precision.** A hit means the output holds a value the user declared secret. There's no pattern guessing to tune.
- **It covers the whole output.** The hook doesn't care which tool produced the text, so a terminal reader, a shell command, and a web fetch are all covered by one rule.

## What the spike observed

Setup: a fake secret in a file, a hook that reads that file and masks any occurrence in the tool response, and a headless session that printed the secret.

| Tool type | `tool_response` shape | Hook output key | Model saw | Secret in saved transcript |
|---|---|---|---|---|
| Bash | object: `stdout`, `stderr`, `interrupted`, `isImage`, `noOutputExpected` | `updatedToolOutput` | `[REDACTED]` | 0 occurrences |
| MCP tool (stub server) | list of content blocks | `updatedMCPToolOutput` | `[REDACTED]` | 0 occurrences, including `toolUseResult` |

A search of the whole `~/.claude` directory found the secret only in the session where the spike was authored, because its commands contained the fake string.

The docs don't promise that a replacement reaches the transcript file. The spike is the evidence that it does, on this version.

Not observed:

- Interactive sessions. Only `-p` was run.
- Subagent transcripts, and whether PostToolUse fires inside subagents.
- OpenTelemetry and analytics. The docs say they record the original output before hooks run.
- Terminal display. A hook can't change what a terminal panel draws.

## Data shape

```
Secret    = { label: string, value: string, source: SourceRef }
Variant   = { text: string, secret: Secret }          # one searchable form
SecretSet = { variants: Variant[] }                    # longest first
```

`label` is the variable name (`DB_PASSWORD`), never the value. It goes into the replacement, so the model and the user can tell which secret was masked: `[REDACTED:DB_PASSWORD]`.

A `SecretSet` is built per hook call and thrown away. Nothing derived from a secret is written to disk.

## Where secrets come from

Phase 0 reads dotenv-style files. The list of files lives in config:

- `.claude/secret-redactor.json` in the project (checked in, holds paths only)
- `~/.config/secret-redactor/config.json` for user-wide sources

Each source file is re-read on every hook call. A typical `.env` parses in under a millisecond, and reading fresh means a rotated secret is covered the moment it lands, with no cache to invalidate.

A key counts as a secret when its name matches `PASSWORD|PASSWD|TOKEN|SECRET|KEY|DSN|CREDENTIAL|AUTH` (case-insensitive) or the user lists it under `include`. Keys under `exclude` never count. Everything else, like a region or a hostname, passes through.

A value is skipped when it is shorter than 8 characters (configurable) or appears on a small stoplist (`true`, `false`, `us`, and similar). Without that floor, masking a value like `us` would corrupt ordinary output.

Later sources (phase 2) are other secret managers that can list values for the current user. They plug in behind the same `Secret` shape.

## Variants

A secret rarely appears raw. The transcript from the real incident held it inside escaped quotes. Each secret expands to:

- the raw value
- the JSON-escaped form (quotes and backslashes escaped), so it matches inside tool output that is itself JSON
- the URL-encoded form
- standard and URL-safe base64 of the value
- for multiline values such as keys, each line of 20 or more characters

Matching runs longest variant first so a long value is masked whole instead of leaving a tail behind.

## Hook behavior

PostToolUse, registered for `Bash`, `Grep`, `WebFetch`, and `mcp__.*`.

1. Parse the hook input and take `tool_response`.
2. Walk it recursively. Every string is run through the `SecretSet`.
3. If nothing matched, print nothing and exit 0. The common case costs one process start.
4. If something matched, print the same structure with strings replaced, under `updatedMCPToolOutput` when `tool_name` starts with `mcp__`, otherwise `updatedToolOutput`. Keep the shape identical: dict stays dict, list stays list.
5. Append one line to `~/.local/state/secret-redactor/events.jsonl` (mode 0600): timestamp, tool name, labels, count. Never the value.

Implementation is Python standard library only, started with `-S` and `-E` to keep start-up small.

### Failure mode

Default is fail-open: if the hook errors, the tool output passes through unmasked and a warning goes to stderr. A hook that breaks every tool call is worse for most users than the leak it was guarding.

A strict mode (`"onError": "withhold"`) replaces the output with a short "withheld: redactor error" message instead. Users who handle high-value secrets can opt in.

### Read, Edit and Write

These are off by default. If `Read` output is masked, the next `Edit` call has an `old_string` that no longer matches the file, and the edit fails in a way that is hard to diagnose.

The leak path for secret files is closed a different way: `secret-redactor init` prints a `permissions.deny` snippet with `Read` rules for every configured source file. Permission rules apply to the `Read` tool. They don't stop a shell command from reading the file, which the hook covers.

## Second layer: shape patterns

High-precision patterns for secrets the sources don't know about (one the user pasted, one a command fetched from an API): GitHub tokens (`ghp_`, `github_pat_`), cloud access key prefixes, private key headers, and a few chat-platform token prefixes. They label hits by pattern, for example `[REDACTED:github-token]`.

Shape patterns are never the only defense. They would have caught one token in the real incident and none of the short passwords.

## Phase 1: inputs

Output redaction closes the path from a tool into the conversation. Secrets also travel the other way, when an agent puts a value into a command line. PreToolUse on `Bash`, `Write`, and `Edit` can check `tool_input` for any known secret and ask or deny. This catches patterns like passing a password as a command-line argument, where it lands in process listings and shell history.

Prompts the user types can't be rewritten by a hook. The plugin can warn that a prompt contained a known secret.

## Surfaces

- **Skill `redaction-report`.** Reads the events file and says what was masked, from which tool, how often. This is the tuning loop for over-redaction.
- **`secret-redactor init`.** Prints the config skeleton and the `permissions.deny` snippet. It never writes to settings files itself.

## Testing

Per [`docs/testing-plugins.md`](../testing-plugins.md): `bats` for the hook script's stdin and stdout contract, plus one headless end-to-end test.

The end-to-end test is the spike, kept:

1. Write a fake secret to a temp source file.
2. Run `claude -p --plugin-dir plugins/secret-redactor` with a stub MCP server that returns the fake secret, and a second run that `cat`s it through Bash.
3. Assert the model's reply holds `[REDACTED:...]`.
4. Find the session's JSONL under the config directory and assert the fake secret appears 0 times.

Step 4 is the one that matters. It's what turns "the model didn't see it" into "the transcript doesn't hold it", and it will catch a Claude Code release that changes the write order.

## Where it falls short

- **It only knows what it's told.** A secret that isn't in a configured source and doesn't match a shape pattern goes through. The `redaction-report` skill and a `--scan` mode that lists high-entropy strings in tool output are the way to find gaps.
- **Telemetry may keep the original.** The docs say so. If an organization exports tool spans, redaction here doesn't cover that copy.
- **The display isn't covered.** Terminals and app panels still draw the secret.
- **A partial value still matches nothing.** If a tool prints only part of a secret, exact matching won't see it. A minimum-length floor on a rolling window is a possible later addition.
- **Over-redaction.** A short password that is also a common word will mask harmless text. The events file shows this quickly, and `exclude` is the fix.
- **It is a backstop.** Not loading the secret in the first place is stronger. A project that stops exporting its whole `.env` to every command needs the redactor far less.

## Open questions

- Does the replacement reach the transcript in interactive sessions, and for subagent tool calls? Run the end-to-end test in both before calling this done.
- Hook latency budget. One Python start per tool call is acceptable for `Bash` and MCP calls. Measure before extending the matcher.
- Should this share detectors with the `automic-vault` plugin? Its CLI exposes detector metadata. Reuse would avoid maintaining two pattern lists, but couples the plugins.
- Where does `Read` masking belong for files that aren't declared sources but still hold secrets?

## Phases

0. Hook, dotenv sources, Bash and MCP matcher, events log, `bats` tests, the end-to-end canary test.
1. Variants, shape patterns, PreToolUse input guard, `init`, `redaction-report`.
2. Other secret sources, interactive and subagent verification, strict mode, latency measurements.
