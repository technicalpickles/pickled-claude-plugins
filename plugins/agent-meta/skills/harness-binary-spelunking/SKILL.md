---
name: harness-binary-spelunking
description: Use when investigating the Claude Code CLI binary's internals (the agent harness): extracting the system prompt or tool descriptions, finding what code path produces a specific UI message, decoding minified function names, understanding undocumented config keys, or otherwise spelunking the binary to figure out how Claude Code actually behaves.
---

# Harness Binary Spelunking

"The harness" here means the Claude Code CLI binary. The recipes are Claude-Code-specific (Bun compilation, `tengu_*` events, the `You are Claude Code` system prompt) because that IS the binary being inspected.

The Claude Code CLI ships as a single Mach-O binary (~200MB) compiled by **Bun**. The application is minified JavaScript embedded as plain string constants: `strings` reads it back, `grep` queries it. No deobfuscation, no decompilation. The hard part is knowing what to grep for.

## What you're working with

```bash
which claude                                          # /Users/<you>/.local/bin/claude
file $(readlink -f $(which claude))                   # Mach-O 64-bit executable arm64
strings $(readlink -f $(which claude)) | grep -i bun  # confirms Bun build
```

You will see references like `/Users/runner/work/bun-internal/bun-internal/embedded/oniguruma/...`. That's the Bun runtime baked into the binary. **Filter it out** when you grep, or you drown in noise.

## One-time setup per session

Dump strings to a temp file once, grep it many times. The binary is ~200MB; `strings` over it takes a few seconds. Re-running for every grep is wasteful.

```bash
CLAUDE_BIN=$(readlink -f $(which claude))
strings "$CLAUDE_BIN" > $TMPDIR/claude-strings.txt
ls -lh $TMPDIR/claude-strings.txt   # ~37MB typically
```

Every recipe below assumes `$TMPDIR/claude-strings.txt` exists.

## Shortcut: pre-extracted prompts by version

If all you need is the system prompt, a tool/agent/skill prompt, or the tool descriptions (not arbitrary binary internals), someone already does the extraction for you: [Piebald-AI/claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts) tracks these as plain markdown, grouped by kind and tagged per Claude Code version. It's faster and far more readable than reassembling adjacent string fragments out of `strings`.

```bash
git clone https://github.com/Piebald-AI/claude-code-system-prompts /tmp/ccsp
git -C /tmp/ccsp tag | sort -V | tail        # versions available, e.g. v2.1.190
git -C /tmp/ccsp show v2.1.190:system-prompts/<file>.md   # a specific version's prompt
ls /tmp/ccsp/system-prompts/                 # grouped: system- tool- agent- skill- data-
```

It is a third-party extraction, so two caveats: it can lag the newest release, and it is someone else's reading, not authoritative. The binary on your machine is ground truth. Drop to the recipes below to verify a fragment, to inspect a version not yet tagged there, or for anything past the prompts (config keys, code paths, minified function bodies).

## Recipes

### Recipe 1: Extract the system prompt

The system prompt is stored as a literal string starting with `You are Claude Code,`. Different invocations (CLI, Agent SDK, "explanatory mode") use different opener variants.

```bash
grep -n "^You are Claude" $TMPDIR/claude-strings.txt
```

You'll see something like:

```
140267: You are Claude. Not a persona, not a character ...
153955: You are Claude Code, Anthropic's official CLI for Claude.
153956: You are Claude Code, ... running within the Claude Agent SDK.
```

Each match is *one* line of the assembled prompt. The full prompt is composed at runtime from many adjacent string constants. To see the surrounding fragments:

```bash
awk 'NR>=153955 && NR<=154100' $TMPDIR/claude-strings.txt
```

Tool names (`Bash`, `Grep`, `Read`, `Glob`...) and their descriptions live as adjacent constants in the same region: read forward until the strings stop being prose.

**Caveat:** the assembled prompt you see in a real session is the ground truth. The binary holds the *fragments*. If you want the exact concatenation, observe a session (e.g. via the conversation context); the binary tells you what fragments *exist*. For a pre-assembled, version-tagged copy, see the [shortcut](#shortcut-pre-extracted-prompts-by-version) above.

### Recipe 2: UI message to code path

You see a specific message in the UI ("This command requires approval", "Auto-allowed with sandbox", "Newline followed by `#` hides arguments"). You want the code that emits it.

```bash
grep -n "This command requires approval" $TMPDIR/claude-strings.txt
```

If the string appears in *multiple* code paths (it usually does for generic messages), look for nearby **classification tags** or **telemetry event names**, which are far more specific than the user-facing text:

```bash
# classification tags - stable across releases
grep -ao 'bashMissKind:"[a-z-]*"' "$CLAUDE_BIN" | sort -u
grep -ao 'kind:"too-complex",reason:"[^"]*"' "$CLAUDE_BIN" | sort -u

# telemetry events - extremely stable, prefixed with `tengu_`
grep -ao 'tengu_[a-z_]*' "$CLAUDE_BIN" | sort -u
```

`tengu_bash_ast_too_complex`, `bashMissKind:"too-complex"`, `kind:"semantics"` etc. are the *real* names of code states. They're the right anchors for "what behavior is this."

### Recipe 3: Pull a function body from minified JS

The binary is one giant minified line per `;`-separated statement. Plain `grep` over the strings file works for short matches; for whole function bodies you need to split it.

```bash
# Split on ; into one line per statement, then grep
strings "$CLAUDE_BIN" | tr ';' '\n' | grep 'function Em_' | head -5
```

Or capture a context window around a known anchor (works around BSD grep's `{0,255}` repetition cap by chaining):

```bash
# Anchor on a UI string, grab ~250 chars of surrounding minified JS
grep -aoE '.{0,250}Auto-allowed with sandbox.{0,200}' "$CLAUDE_BIN" | head -3
```

For function bodies past one closing brace, chain `[^}]*}` as many times as you need:

```bash
strings "$CLAUDE_BIN" | grep -oE 'async function Vu4[^}]*}[^}]*}[^}]*}' | head -1 | fold -w 120
```

**Function names rotate every release** (`Vu4`, `Em_`, `w5_`, `Zj_` are all minified identifiers regenerated by the bundler). Never bake them into a plan. Always re-derive them via stable anchors (UI strings, `tengu_*` events, `kind:"..."` tags) for the version you're inspecting.

### Recipe 4: Find undocumented config / settings keys

Settings keys live as quoted JSON-property strings:

```bash
grep -oE '"[a-zA-Z][a-zA-Z0-9]*Sandboxed?"' $TMPDIR/claude-strings.txt | sort -u
grep -oE '"(allow|deny|hooks?|permission)[A-Z][a-zA-Z]*"' $TMPDIR/claude-strings.txt | sort -u

# Or context-window around a known one
grep -ao '.\{0,150\}autoAllowBashIfSandboxed.\{0,150\}' "$CLAUDE_BIN" | head -3
```

For the schema of a config object, find the validator (Zod schemas leave readable shape strings):

```bash
grep -ao '\.object({[^}]*})' "$CLAUDE_BIN" | grep -i sandbox | head
```

## Patterns

| Pattern | Why |
|---------|-----|
| Anchor on UI strings, telemetry events, classification tags | Stable across releases; minified function names are not |
| Dump `strings` to `$TMPDIR` once, reuse | The binary is 200MB; re-running `strings` per grep is slow |
| Use `tr ';' '\n'` before grep when looking for function definitions | Minified JS is one line; `;`-split makes per-statement matches feasible |
| Chain `[^}]*}` to walk past N closing braces | BSD grep on macOS caps `{0,N}` at 255; chaining gets past that limit |
| Filter out `bun-internal`, `oniguruma`, `__STDC_*` | Bun runtime noise, not Claude Code logic |
| `grep -ao` (treat binary as text, only-matching) | Faster than `grep` of the strings file when you have a precise anchor |

## Pitfalls

- **"It's a Node.js bundle"**: No, it's Bun. The build paths in the strings (`bun-internal/`, `tmp_modules/bun/ffi.ts`) prove it. Matters because Bun bundles use specific naming conventions the standard JS bundlers don't.
- **First match for a UI string is rarely the one you want.** Generic messages like "This command requires approval" are emitted from multiple code paths. Disambiguate via nearby `bashMissKind:`, `kind:`, or `tengu_*` tags.
- **BSD grep limit:** `grep -E '.{0,500}'` errors with "maximum repetition exceeds 255". Drop to 250 or chain.
- **Minified names change every release.** Don't write down "the function is `Vu4`" and expect it to mean anything next week. Write down the *anchors* that lead you to the function.
- **The system prompt is fragmented.** You can't grep one continuous blob: the binary stores it as adjacent string constants assembled at runtime. `awk` a line range to see the neighbors.
- **`grep -i` over the raw binary is loud.** Match against `$TMPDIR/claude-strings.txt` for cleaner output, or use precise anchors with `grep -ao`.

## Real-world references

Two prior investigations show the technique end-to-end:

- **Sandbox internals dig:** Starting from a config key (`autoAllowBashIfSandboxed`), walked the Seatbelt profile generator and dynamic ripgrep deny-scan. Decompiled a chain of minified functions (`mu4`, `bu4`, `Vu4`, `_N_`, `Zu4`, `uu4`) to understand how the sandbox profile is constructed.
- **Command parser pipeline walk:** Starting from a UI string ("This command requires approval"), traced the full pipeline: pre-parse checks, AST walker, known-complex set, auto-allow gate, interactive-vs-agent gate, tracked-variables store.

Both started from one anchor (a UI string or a config key) and walked outward.
