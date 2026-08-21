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

## Identify the build and set up your workspace

If you're spelunking a binary (not reading source), run [scripts/spelunk-init.sh](scripts/spelunk-init.sh) before anything else. It resolves the binary, classifies the build, dumps `strings` once, and writes a manifest, all into a workspace shared by every recipe in this skill:

```bash
scripts/spelunk-init.sh claude
# Workspace ready: $TMPDIR/spelunk/claude
#   binary:      /path/to/the/real/binary
#   build type:  bun-js (bun markers: 7, rust markers: 118)
#   strings:     $TMPDIR/spelunk/claude/strings.txt
#   manifest:    $TMPDIR/spelunk/claude/manifest.txt
```

This exists because freelancing this step drifts fast: past investigations dumped to `claude-strings.txt`, then `harness-strings.txt`, with no per-tool suffix (so a second harness in the same session clobbers the first), and one reference file skipped the dump/reuse discipline entirely and re-ran `strings` on every recipe. One workspace shape, one script, no more re-deriving the path or the classification logic per investigation.

`which <tool>` often hands you a **launcher, not the artifact** (npm-installed CLIs are frequently a thin Node script that execs a platform-specific binary elsewhere). The script detects this and stops, printing the shim's contents so you can find the real spawn target by hand:

```bash
$ scripts/spelunk-init.sh codex
'/Users/<you>/.local/bin/codex' looks like a launcher/shim, not the real binary:
  a /usr/bin/env node script text executable
...
Find the spawn target above, then rerun: scripts/spelunk-init.sh codex <spawn-target-path>

$ scripts/spelunk-init.sh codex .../codex-darwin-arm64/vendor/aarch64-apple-darwin/bin/codex
Workspace ready: $TMPDIR/spelunk/codex
  build type:  rust (bun markers: 0, rust markers: 3565)
```

Chasing an arbitrary spawn chain is a judgment call (it varies per tool, per platform); classifying what you're holding once you have it is not, so that part is scripted. If the build type comes back `unknown`, `file $BIN` and check whether it's unbundled Node or readable source instead; see the pi note in [references/source-clone.md](references/source-clone.md).

Don't assume a binary is a Node bundle just because the CLI is npm-installed. Bun and Rust both ship as single Mach-O executables that npm happily distributes as "the binary." And don't assume bun/rust markers are mutually exclusive: a Bun-compiled JS bundle can embed a native Rust addon (Claude Code ships a napi/tokio one), so the script treats any Bun signal as decisive even when rust markers are also present.

## General method

Once your workspace is set up, the loop is the same for every harness:

1. **Reuse the dump.** `spelunk-init.sh` skips re-dumping if the binary hasn't changed size; every recipe below reads from its `strings.txt`, not a fresh `strings` call.
2. **Anchor on stable strings, not derived names.** System-prompt openers, UI-facing error text, telemetry/event names, config-key names, `.rs:line` debug locations: these survive releases. Minified JS identifiers and even some struct layouts do not.
3. **Walk outward from the anchor.** Grep the anchor, then read the surrounding region: `awk` a line range for a known window, or [scripts/extract-context.sh](scripts/extract-context.sh) `<anchor> <file> [width]` for a character window around a match anywhere in the file. Reach for the script over hand-rolling `grep -aoE '.{0,N}anchor.{0,N}'`; see the pitfall below for why.
4. **Filter noise, but derive the noise list per tool.** Every runtime bakes in its own boilerplate (Bun's `bun-internal`/`oniguruma`, cargo's registry paths, etc.). Don't assume one tool's noise list applies to another; a quick `grep -c` of the suspected noise string tells you whether it's even present.

The per-build reference files below give you the concrete grep recipes for each anchor type (prompts, UI messages, function bodies, config keys). Read the one matching your build classification above.

## Scripts

- [scripts/spelunk-init.sh](scripts/spelunk-init.sh): resolve, classify, and dump a harness binary into `$TMPDIR/spelunk/<tool>/` (`strings.txt` + `manifest.txt`). Run this first.
- [scripts/extract-context.sh](scripts/extract-context.sh): print the context window around every match of an anchor, using perl instead of grep's bounded-repetition engine so it works past the widths where grep itself breaks (see Pitfalls).

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
| Run `scripts/spelunk-init.sh <tool>` once per investigation, reuse its workspace | Binaries run 100-200MB+; re-running `strings` per grep is slow, and a shared path means every recipe agrees on where things are |
| Follow `which` through shims to the real artifact before classifying | npm/pip installs often distribute a launcher script, not the binary |
| Derive the noise filter per tool instead of reusing another tool's | Bun/Rust/Node each bake in different runtime boilerplate; presence isn't guaranteed |
| Prefer cloning tagged source over spelunking when the tool is open source and tagged | Faster, more readable, no guessing at derived names |
| Use `scripts/extract-context.sh` for context windows instead of hand-rolled `grep -aoE '.{0,N}...'` | Sidesteps the grep repetition-cap class of failure entirely (see Pitfalls) |

## Pitfalls

- **Assuming build type from install method.** npm-installed does not mean JS bundle; codex installs via npm but ships a Rust binary. Always `file` the real artifact (`spelunk-init.sh` does this for you).
- **Trusting `which` at face value.** It frequently returns a launcher/shim, not the artifact you want to classify.
- **Assuming bun and rust markers are mutually exclusive.** A Bun-compiled JS bundle can embed a native Rust addon (Claude Code ships one via napi/tokio), so `.cargo/registry` hits alone don't mean the binary is a standalone Rust build. `spelunk-init.sh` treats any Bun-specific marker (`tmp_modules/bun`, `oniguruma`, `bun-internal`) as decisive over rust markers for exactly this reason.
- **Reusing one tool's noise filter on another.** `bun-internal` noise present in Claude Code is entirely absent from opencode's Bun build; check before you filter.
- **First match for a generic UI string is rarely the only code path.** Disambiguate with nearby classification tags, telemetry event names, or (in Rust) `.rs:line` locations.
- **Baking derived/minified names into a plan.** Minified JS identifiers rotate every release. Rust struct/function names are more stable but crate-internal ones can still shift. Write down the anchor that leads you there, not the name itself.
- **Grep's bounded-repetition cap, in whichever error string your `grep` happens to produce.** `grep -aoE '.{0,500}anchor.{0,500}'` fails past a certain width, but the message depends on what's actually running as `grep`: BSD grep says "repetition-operator operand invalid" / "maximum repetition count exceeds 255"; ugrep (a common `grep` shim, including via Claude Code's own file-scoped grep wrapper) says "exceeds complexity limits" at a threshold that depends on the pattern, not just the width. Same root cause, different text, so grepping the docs for one message won't surface the other. Use `scripts/extract-context.sh` instead of hand-rolling this grep; it does the extraction in perl, which has no such cap, and sidesteps the whole class of failure rather than tuning the width to dodge it.
- **Assuming source and shipped binary agree.** Source is what was committed; the binary is what's running. When behavior doesn't match source, or the version isn't tagged yet, spelunk the binary even for open-source tools.

## Real-world references

Five investigations show the technique end-to-end, across three harnesses:

- **Claude Code, sandbox internals:** starting from a config key (`autoAllowBashIfSandboxed`), walked the Seatbelt profile generator and dynamic ripgrep deny-scan, decompiling a chain of minified functions (`mu4`, `bu4`, `Vu4`, `_N_`, `Zu4`, `uu4`) to understand how the sandbox profile is constructed.
- **Claude Code, command parser pipeline:** starting from a UI string ("This command requires approval"), traced pre-parse checks, the AST walker, the known-complex set, the auto-allow gate, the interactive-vs-agent gate, and the tracked-variables store.
- **codex, Node-shim-to-Rust-binary chase:** `which codex` resolved to a Node launcher; following the spawn target landed on a 203MB Mach-O Rust binary, confirmed via cargo-registry paths and `.rs` locations in the strings output.
- **codex, whole-prompt and config-key extraction:** grepping `you are (codex|a coding)` pulled entire system-prompt constants (not fragments), and grepping `approval_policy|sandbox_mode|model_reasoning_effort` pulled plain serde snake_case config keys directly.
- **opencode, Bun-build comparison:** confirmed the same Bun-compiled family as Claude Code, but with zero `bun-internal` noise, named-string function/provider wrappers (`l.fn("Gemini.fromRequest")`, `bo.make("google")`) standing in for `tengu_*` anchors, and a near-whole system-prompt template literal instead of Claude's fragmented assembly.

Each started from one anchor (a config key, a UI string, or a "what is this binary" question) and walked outward.
