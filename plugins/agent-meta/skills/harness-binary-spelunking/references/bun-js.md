# Bun-compiled JS builds: Claude Code and opencode

Claude Code and opencode are both shipped as single Mach-O binaries compiled by **Bun**, with the application as minified JavaScript embedded as plain string constants. `strings` reads it back, `grep` queries it. No deobfuscation, no decompilation needed. The hard part is knowing what to grep for.

The recipes below were developed against Claude Code and confirmed to transfer to opencode with two real differences, called out inline: the noise filter, and the anchor scheme for stable functions/providers. Everything else (splitting minified JS, chaining past braces, the BSD grep 255 cap) applies to both as written.

## What you're working with

```bash
which claude                                          # /Users/<you>/.local/bin/claude
file $(readlink -f $(which claude))                   # Mach-O 64-bit executable arm64
strings $(readlink -f $(which claude)) | grep -i bun   # confirms Bun build
```

For opencode, the same shape applies:

```bash
which opencode
file $(readlink -f $(which opencode))                 # Mach-O 64-bit executable arm64, ~114MB
```

**Noise filter is tool-specific, don't assume it transfers.** Claude Code's strings include `/Users/runner/work/bun-internal/bun-internal/embedded/oniguruma/...`, Bun-runtime boilerplate you filter out or drown in. opencode's build has **none of it**:

```bash
strings $(readlink -f $(which opencode)) | grep -c bun-internal   # 0
```

Check what noise is actually present in the binary you're looking at before you build a filter; don't reuse another tool's list.

## One-time setup per session

Dump strings to a temp file once, grep it many times. The binary is 100-200MB+; `strings` over it takes a few seconds. Re-running for every grep is wasteful.

```bash
BIN=$(readlink -f $(which claude))       # or opencode
strings "$BIN" > $TMPDIR/harness-strings.txt
ls -lh $TMPDIR/harness-strings.txt       # ~37MB typically for Claude Code
```

Every recipe below assumes `$TMPDIR/harness-strings.txt` exists and `$BIN` points at the real artifact.

## Recipe 1: Extract the system prompt

**Claude Code:** the system prompt is stored as a literal string starting with `You are Claude Code,`. Different invocations (CLI, Agent SDK, "explanatory mode") use different opener variants.

```bash
grep -n "^You are Claude" $TMPDIR/harness-strings.txt
```

You'll see something like:

```
140267: You are Claude. Not a persona, not a character ...
153955: You are Claude Code, Anthropic's official CLI for Claude.
153956: You are Claude Code, ... running within the Claude Agent SDK.
```

Each match is *one line* of the assembled prompt. The full prompt is composed at runtime from many adjacent string constants. To see the surrounding fragments:

```bash
awk 'NR>=153955 && NR<=154100' $TMPDIR/harness-strings.txt
```

Tool names (`Bash`, `Grep`, `Read`, `Glob`...) and their descriptions live as adjacent constants in the same region: read forward until the strings stop being prose.

**Caveat:** the assembled prompt you see in a real session is the ground truth. The binary holds the *fragments*. If you want the exact concatenation, observe a session; the binary tells you what fragments *exist*. For a pre-assembled, version-tagged copy of Claude Code's prompts, see the shortcut in the main SKILL.md.

**opencode is different here: the prompt is a near-whole template literal**, not fragmented adjacent constants. From opencode 1.17.5:

```
Vi = "You are OpenCode, the best coding agent on the planet.\nYou are an interactive CLI tool..."
```

One grep on a distinctive opener phrase lands the (mostly) whole prompt in a single match, no `awk` reassembly needed. Don't assume every Bun-compiled tool fragments its prompt the way Claude Code does; check whether your first match already looks complete before reaching for a line-range walk.

## Recipe 2: UI message to code path

You see a specific message in the UI ("This command requires approval", "Auto-allowed with sandbox", "Newline followed by `#` hides arguments"). You want the code that emits it.

```bash
grep -n "This command requires approval" $TMPDIR/harness-strings.txt
```

If the string appears in *multiple* code paths (it usually does for generic messages), look for nearby **classification tags** or **telemetry event names**, which are far more specific than the user-facing text.

**Claude Code** prefixes its stable telemetry events with `tengu_`:

```bash
# classification tags - stable across releases
grep -ao 'bashMissKind:"[a-z-]*"' "$BIN" | sort -u
grep -ao 'kind:"too-complex",reason:"[^"]*"' "$BIN" | sort -u

# telemetry events - extremely stable
grep -ao 'tengu_[a-z_]*' "$BIN" | sort -u
```

`tengu_bash_ast_too_complex`, `bashMissKind:"too-complex"`, `kind:"semantics"` etc. are the *real* names of code states.

**opencode has no `tengu_*` equivalent.** Its stable anchors are **named-string function/provider wrappers**: the minified bundler keeps a literal string name attached to the wrapped function or provider, even though the variable holding it is minified:

```bash
grep -ao 'l\.fn("[A-Za-z.]*")' "$BIN" | sort -u    # e.g. l.fn("Gemini.fromRequest")
grep -ao 'bo\.make("[a-z]*")' "$BIN" | sort -u     # e.g. bo.make("google"), bo.make("openai")
```

These are the opencode equivalent of `tengu_*`: stable, semantic, safe to anchor on even as the surrounding minified code changes. The wrapper function names (`l.fn`, `bo.make`) are themselves minified and could shift release to release; the *string literal argument* is the durable anchor. When you land in an unfamiliar Bun bundle, look for this pattern (a short minified call wrapping a human-readable string) before assuming there's no stable anchor.

## Recipe 3: Pull a function body from minified JS

The binary is one giant minified line per `;`-separated statement. Plain `grep` over the strings file works for short matches; for whole function bodies you need to split it. This applies as-is to both Claude Code and opencode.

```bash
# Split on ; into one line per statement, then grep
strings "$BIN" | tr ';' '\n' | grep 'function Em_' | head -5
```

Or capture a context window around a known anchor (works around BSD grep's `{0,255}` repetition cap by chaining):

```bash
# Anchor on a UI string, grab ~250 chars of surrounding minified JS
grep -aoE '.{0,250}Auto-allowed with sandbox.{0,200}' "$BIN" | head -3
```

For function bodies past one closing brace, chain `[^}]*}` as many times as you need:

```bash
strings "$BIN" | grep -oE 'async function Vu4[^}]*}[^}]*}[^}]*}' | head -1 | fold -w 120
```

**Function names rotate every release** (`Vu4`, `Em_`, `w5_`, `Zj_` are all minified identifiers regenerated by the bundler, in both tools). Never bake them into a plan. Always re-derive them via stable anchors (UI strings, `tengu_*` events, `l.fn(...)`/`bo.make(...)` wrappers, `kind:"..."` tags) for the version you're inspecting.

## Recipe 4: Find undocumented config / settings keys

Settings keys live as quoted JSON-property strings, in both tools:

```bash
grep -oE '"[a-zA-Z][a-zA-Z0-9]*Sandboxed?"' $TMPDIR/harness-strings.txt | sort -u
grep -oE '"(allow|deny|hooks?|permission)[A-Z][a-zA-Z]*"' $TMPDIR/harness-strings.txt | sort -u

# Or context-window around a known one
grep -ao '.\{0,150\}autoAllowBashIfSandboxed.\{0,150\}' "$BIN" | head -3
```

For the schema of a config object, find the validator (Zod schemas leave readable shape strings):

```bash
grep -ao '\.object({[^}]*})' "$BIN" | grep -i sandbox | head
```

## Pitfalls specific to Bun-compiled JS

- **"It's a Node.js bundle"**: No, it's Bun. The build paths in the strings (`bun-internal/`, `tmp_modules/bun/ffi.ts`, when present) prove it. Matters because Bun bundles use naming conventions standard JS bundlers don't.
- **Assuming Claude Code's noise filter (`bun-internal`, `oniguruma`) applies to every Bun build.** opencode's build has zero `bun-internal` hits. Check with `grep -c` first.
- **Assuming every Bun-compiled prompt is fragmented like Claude Code's.** opencode's is a near-whole template literal. Look at your first match before reaching for line-range reassembly.
- **First match for a UI string is rarely the one you want.** Generic messages like "This command requires approval" are emitted from multiple code paths. Disambiguate via nearby `bashMissKind:`, `kind:`, `tengu_*`, or `l.fn(...)`/`bo.make(...)` tags.
- **BSD grep limit:** `grep -E '.{0,500}'` errors with "maximum repetition exceeds 255". Drop to 250 or chain.
- **Minified names change every release.** Don't write down "the function is `Vu4`" and expect it to mean anything next week. Write down the *anchors* that lead you to the function.
