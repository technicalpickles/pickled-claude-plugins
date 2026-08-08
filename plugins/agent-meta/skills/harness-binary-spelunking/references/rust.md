# Rust builds: codex

codex (`openai/codex`, 0.139.0 at the time of this recon) installs via npm but ships a **Rust** binary, not a JS bundle. `which codex` returns a Node launcher (`.../@openai/codex/bin/codex.js`) that spawns the real platform binary; follow the shim before you classify anything:

```
$ which codex
/Users/<you>/.local/bin/codex                          # Node launcher

$ cat $(which codex)                                    # spawns the real binary at:
/Users/<you>/.local/share/mise/installs/node/<v>/lib/node_modules/@openai/codex/node_modules/@openai/codex-darwin-arm64/vendor/aarch64-apple-darwin/bin/codex

$ file .../codex-darwin-arm64/vendor/aarch64-apple-darwin/bin/codex
Mach-O 64-bit executable arm64                          # 203MB
```

**Lesson:** `which` may hand you a shim. Chase the spawn target to the real artifact before classifying it as a build type. An npm-installed CLI is not automatically a JS bundle.

## Confirming it's Rust

Strings carry unmistakable Rust/cargo provenance:

```bash
CODEX=.../codex-darwin-arm64/vendor/aarch64-apple-darwin/bin/codex
strings "$CODEX" | grep -c '.cargo/registry'    # cargo-registry paths, nonzero
strings "$CODEX" | grep -oE '[a-z_]+::[a-z_]+' | sort -u | head    # crate::module paths
```

You'll see things like `/Users/runner/.cargo/registry/...`, `.rs` file paths, and crate paths like `codex_models_manager::manager`.

## What transfers from the JS recipes, and what doesn't

The general method (dump strings once, anchor on stable strings, walk outward) is the same. The concrete recipes are different because Rust doesn't minify or bundle the way a JS build does:

- **No `tr ';' '\n'` splitting.** That trick exists because minified JS is one giant `;`-joined statement; Rust binaries aren't shaped that way.
- **No Zod `.object({...})` schema strings.** That's a JS-validator-library artifact. Rust's config schema shows up differently (see below).
- **Rust tells instead:** whole-string prompts (not fragments), serde field-name runs, `.rs:line` debug/panic locations, and cargo-registry paths as provenance.

## Recipe 1: Extract the system prompt (comes out WHOLE)

This is the biggest divergence from the JS recipes. Claude Code and opencode store prompts as string fragments or a near-whole template literal that still needs a grep to locate. codex's Rust build embeds each prompt as a **complete string constant**, so one grep on a distinctive opening clause returns the entire block:

```bash
strings "$CODEX" | grep -iE 'you are (codex|a coding)'
```

From codex 0.139.0, this yields entire prompt blocks in one match each, no reassembly:

- `You are Codex, an OpenAI general-purpose agentic assistant that helps the user complete tasks...`
- `You are a coding agent running in the Codex CLI, a terminal-based coding assistant...`
- `You are Codex, a coding agent based on GPT-5. You and the user share the same workspace...`

Templating is visible too, as literal placeholder strings rather than assembled fragments: `{{ personality }}`, `instructions_template`, `instructions_variables`.

## Recipe 2: Find undocumented config keys (plain serde snake_case)

Rust's serde-derived config structs serialize field names as plain snake_case strings, directly greppable with no JSON-quote or camelCase guessing:

```bash
strings "$CODEX" | grep -iE 'approval_policy|sandbox_mode|model_reasoning_effort'
```

From codex 0.139.0, this also surfaces `personality_default`, `personality_pragmatic`, `context_window`, `auto_compact_token_limit`, and serde struct summaries like:

```
struct ModelInfo with 36 elements
```

followed by a run of the struct's field names as adjacent strings. That struct-summary line is itself a useful anchor: grep `struct \w+ with \d+ elements` to enumerate config/data structs you didn't know existed, then read the field-name run that follows.

## Recipe 3: Anchor on `.rs:line` locations

Rust's panic and debug-assertion machinery embeds source file:line pairs as strings. These are semantically stable (they name the actual source location) and, unlike minified JS identifiers, don't rotate on every release the same way, though line numbers shift as the file changes:

```bash
strings "$CODEX" | grep -oE '[a-z_/-]+\.rs:[0-9]+' | sort -u | head -20
```

From this recon: `models-manager/src/manager.rs:231`, `models-manager/src/model_info.rs:67`. These double as a map of the crate layout: the path segment before `src/` is usually the crate name (`models-manager`), which you can cross-reference against the cloned source (see [source-clone.md](source-clone.md)) to jump straight to the relevant file.

## Patterns specific to Rust builds

| Pattern | Why |
|---------|-----|
| Follow npm-launcher shims to the real platform binary before classifying | `which` returns the Node wrapper, not the Rust artifact |
| Grep whole prompt openers directly, expect complete matches | Rust embeds prompts as full string constants, not fragments |
| Grep snake_case config-key fragments directly, no quoting needed | serde field names are plain strings, not JSON-quoted like JS `"camelCase"` keys |
| Anchor on `.rs:line` locations | Semantically named, tied to real source structure, crosses over cleanly to a source clone |
| Grep `struct \w+ with \d+ elements` to enumerate structs | serde/debug summaries name structs you didn't know to look for |

## Pitfalls

- **Assuming npm install means JS bundle.** codex installs via `npm install -g @openai/codex`; the actual binary is Rust. Always `file` the real artifact after following shims.
- **Reaching for JS-bundle recipes first.** `tr ';' '\n'` and Zod schema greps do nothing useful here; they assume a minified-JS shape codex doesn't have.
- **Treating `.rs:line` as immutable.** The file path segment is stable; the line number will drift between versions as the source changes. Use it as a "which file" anchor, then re-locate the exact line in a fresh clone if you need precision.
- **Missing the struct-summary anchor.** `struct X with N elements` lines are an easy way to enumerate config/data shapes wholesale instead of guessing field names one at a time.
