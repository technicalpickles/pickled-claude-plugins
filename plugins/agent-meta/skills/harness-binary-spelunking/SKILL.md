---
name: harness-binary-spelunking
description: Use when investigating an agent-harness CLI's internals (Claude Code, codex, opencode, or similar): extracting the system prompt or tool descriptions, finding what code path produces a specific UI message, decoding minified function names or Rust symbols, understanding undocumented config keys, or otherwise spelunking a shipped binary (or its pinned source) to figure out how the tool actually behaves.
---

# Harness Binary Spelunking

"The harness" here means whatever agent CLI you're inspecting: Claude Code, codex, opencode, pi, or any other tool that wraps an LLM in a terminal loop. The technique is the same regardless of which one you're looking at; only the recipes fork, based on how the binary was built.

## Step 0: Decide your approach

Before grepping anything, figure out which situation you're in:

- **Open source, and the pinned version is tagged?** Clone the source at that exact tag and read it. Fastest, most readable, no guessing at minified names. See [references/source-clone.md](references/source-clone.md).
- **Closed source (Claude Code today), or you want ground truth of what actually shipped?** Spelunk the binary directly. Source, even when it exists, is what was *committed*; the binary is what's *running* on your machine right now.
- **Open source but the version isn't tagged yet, or you're debugging a discrepancy between source and behavior?** Spelunk the binary even though source exists. "Open source" doesn't mean "skip verification."

Most investigations start at one of these two ends and only cross over if the first approach runs dry (source doesn't explain the behavior you're seeing; binary strings are too fragmented to be sure).

## Identify the build

If you're spelunking a binary (not reading source), figure out what you're actually holding before you pick a recipe set.

```bash
which <tool>                          # may be a shim, not the real binary
file $(readlink -f $(which <tool>))   # classify the artifact
```

`which` often hands you a **launcher, not the artifact**. npm-installed CLIs are frequently a thin Node script that execs a platform-specific binary elsewhere. Follow the shim:

```bash
$ which codex
/Users/<you>/.local/bin/codex          # a Node launcher: bin/codex.js

$ cat $(which codex)                   # spawns the real binary, e.g.:
# .../@openai/codex/node_modules/@openai/codex-darwin-arm64/vendor/aarch64-apple-darwin/bin/codex

$ file .../codex-darwin-arm64/vendor/aarch64-apple-darwin/bin/codex
Mach-O 64-bit executable arm64        # 203MB, this is the real target
```

Once you have the real artifact, classify it:

| Tells | Build | Recipes |
|-------|-------|---------|
| `strings <bin> \| grep -i bun` hits; paths like `bun-internal/`, `tmp_modules/bun/ffi.ts` | Bun-compiled JS (Claude Code, opencode) | [references/bun-js.md](references/bun-js.md) |
| `strings <bin>` shows `.rs` paths, `.cargo/registry/`, `crate_name::module` paths | Rust | [references/rust.md](references/rust.md) |
| `file` says plain script / small size, `node_modules/` alongside it | Unbundled Node, or thin wrapper over readable source | Just read the source; see the pi note in [references/source-clone.md](references/source-clone.md) |

Don't assume a binary is a Node bundle just because the CLI is npm-installed. Bun and Rust both ship as single Mach-O executables that npm happily distributes as "the binary."

## General method

Once you know the build, the loop is the same for every harness:

1. **Dump once, grep many times.** These binaries run 100MB-200MB+; `strings` over them takes a few seconds but you'll grep dozens of times. Dump to a temp file once and reuse it.
2. **Anchor on stable strings, not derived names.** System-prompt openers, UI-facing error text, telemetry/event names, config-key names, `.rs:line` debug locations: these survive releases. Minified JS identifiers and even some struct layouts do not.
3. **Walk outward from the anchor.** Grep the anchor, then read the surrounding region (`awk` a line range, or grab a character window with `grep -aoE '.{0,N}anchor.{0,N}'`) to find the code, config, or prompt fragments next to it.
4. **Filter noise, but derive the noise list per tool.** Every runtime bakes in its own boilerplate (Bun's `bun-internal`/`oniguruma`, cargo's registry paths, etc.). Don't assume one tool's noise list applies to another; a quick `grep -c` of the suspected noise string tells you whether it's even present.

The per-build reference files below give you the concrete grep recipes for each anchor type (prompts, UI messages, function bodies, config keys). Read the one matching your build classification above.

## Reference files

- [references/bun-js.md](references/bun-js.md): Bun-compiled JS builds (Claude Code, opencode). System prompt extraction, UI-message-to-code-path, pulling minified function bodies, undocumented config keys. Covers the two tools together and calls out where they diverge (anchor scheme, noise filter, prompt fragmentation).
- [references/rust.md](references/rust.md): Rust builds (codex). Whole-string system prompts, serde-derived config keys, `.rs:line` anchors, cargo-registry provenance, and what does NOT carry over from the JS recipes.
- [references/source-clone.md](references/source-clone.md): version-to-git-tag mapping and clone recipe for tools that ship real source (codex, opencode, pi), plus the case (pi) where reading source beats spelunking entirely.

## Shortcut: check whether someone already extracted this

Before reassembling fragments yourself, check whether someone already did the extraction and published it. For Claude Code specifically, [Piebald-AI/claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts) tracks system/tool/agent/skill prompts as plain markdown, tagged per Claude Code version:

```bash
git clone https://github.com/Piebald-AI/claude-code-system-prompts /tmp/ccsp
git -C /tmp/ccsp tag | sort -V | tail        # versions available, e.g. v2.1.190
git -C /tmp/ccsp show v2.1.190:system-prompts/<file>.md   # a specific version's prompt
ls /tmp/ccsp/system-prompts/                 # grouped: system- tool- agent- skill- data-
```

It's a third-party extraction: it can lag the newest release, and it's someone else's reading, not authoritative. The binary (or source, per Step 0) on your machine is ground truth. Drop to the recipes when you need to verify a fragment, inspect a version not yet covered, or dig into anything past prompts (config keys, code paths, function bodies). The same instinct applies to other harnesses too: check for an existing extraction project before you start from scratch.

## Patterns

| Pattern | Why |
|---------|-----|
| Anchor on UI strings, telemetry events, config keys, `.rs:line` locations | Stable across releases; minified names and even struct shapes are not |
| Dump `strings` to a temp file once, reuse it | Binaries run 100-200MB+; re-running `strings` per grep is slow |
| Follow `which` through shims to the real artifact before classifying | npm/pip installs often distribute a launcher script, not the binary |
| Derive the noise filter per tool instead of reusing another tool's | Bun/Rust/Node each bake in different runtime boilerplate; presence isn't guaranteed |
| Prefer cloning tagged source over spelunking when the tool is open source and tagged | Faster, more readable, no guessing at derived names |

## Pitfalls

- **Assuming build type from install method.** npm-installed does not mean JS bundle; codex installs via npm but ships a Rust binary. Always `file` the real artifact.
- **Trusting `which` at face value.** It frequently returns a launcher/shim, not the artifact you want to classify.
- **Reusing one tool's noise filter on another.** `bun-internal` noise present in Claude Code is entirely absent from opencode's Bun build; check before you filter.
- **First match for a generic UI string is rarely the only code path.** Disambiguate with nearby classification tags, telemetry event names, or (in Rust) `.rs:line` locations.
- **Baking derived/minified names into a plan.** Minified JS identifiers rotate every release. Rust struct/function names are more stable but crate-internal ones can still shift. Write down the anchor that leads you there, not the name itself.
- **BSD grep's `{0,N}` cap at 255.** `grep -E '.{0,500}'` errors with "maximum repetition exceeds 255" on macOS. Drop below 255 or chain `[^}]*}` segments.
- **Assuming source and shipped binary agree.** Source is what was committed; the binary is what's running. When behavior doesn't match source, or the version isn't tagged yet, spelunk the binary even for open-source tools.

## Real-world references

Five investigations show the technique end-to-end, across three harnesses:

- **Claude Code, sandbox internals:** starting from a config key (`autoAllowBashIfSandboxed`), walked the Seatbelt profile generator and dynamic ripgrep deny-scan, decompiling a chain of minified functions (`mu4`, `bu4`, `Vu4`, `_N_`, `Zu4`, `uu4`) to understand how the sandbox profile is constructed.
- **Claude Code, command parser pipeline:** starting from a UI string ("This command requires approval"), traced pre-parse checks, the AST walker, the known-complex set, the auto-allow gate, the interactive-vs-agent gate, and the tracked-variables store.
- **codex, Node-shim-to-Rust-binary chase:** `which codex` resolved to a Node launcher; following the spawn target landed on a 203MB Mach-O Rust binary, confirmed via cargo-registry paths and `.rs` locations in the strings output.
- **codex, whole-prompt and config-key extraction:** grepping `you are (codex|a coding)` pulled entire system-prompt constants (not fragments), and grepping `approval_policy|sandbox_mode|model_reasoning_effort` pulled plain serde snake_case config keys directly.
- **opencode, Bun-build comparison:** confirmed the same Bun-compiled family as Claude Code, but with zero `bun-internal` noise, named-string function/provider wrappers (`l.fn("Gemini.fromRequest")`, `bo.make("google")`) standing in for `tengu_*` anchors, and a near-whole system-prompt template literal instead of Claude's fragmented assembly.

Each started from one anchor (a config key, a UI string, or a "what is this binary" question) and walked outward.
