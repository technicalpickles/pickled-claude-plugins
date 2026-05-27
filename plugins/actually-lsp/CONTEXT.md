# actually-lsp

Closes the LSP activation gap across the whole lifecycle: detection, setup, activation, and failure diagnosis. The plugin layers on top of the official LSP plugins from `claude-plugins-official` (`rust-analyzer-lsp`, `typescript-lsp`, `ruby-lsp`) and makes sure they're discoverable, installable, runnable, and actually reached for by Claude.

## Language

**activation gap**:
The gap between an LSP plugin being installed and Claude actually reaching for the LSP tool. Documented in the [share-out](../../../../projects/claude-test-harness/docs/2026-05-21-lsp-activation-gap-share-out.md). The reason this plugin exists.

**ecosystem**:
A code ecosystem that has one or more LSP server options. The unit the plugin reasons about. Examples: Rust (via Cargo), TypeScript (via npm), Ruby (via Bundler). One project may contain multiple ecosystems (polyglot repo).
_Avoid_: language, runtime, toolchain.

**ecosystem marker**:
A file whose presence signals an ecosystem is in use in a directory. The plugin detects ecosystems by scanning for these. Examples: `Cargo.toml` (Rust), `package.json` (TypeScript/JavaScript), `Gemfile` (Ruby).
_Avoid_: manifest, language signal, project file.

**language server**:
The actual LSP server process for an ecosystem. Multiple servers may exist per ecosystem; the plugin doesn't lock in a choice. Examples: `rust-analyzer`, `typescript-language-server`, `ruby-lsp`, `solargraph`, `vtsls`.
_Avoid_: LSP (which is the protocol, not a server).

**LSP plugin**:
A Claude Code plugin from a marketplace that wires up a language server via the `lspServers` field in its marketplace entry. Examples: `rust-analyzer-lsp@claude-plugins-official`. One ecosystem can have multiple LSP plugins available; this plugin recommends one per ecosystem but doesn't enforce.
_Avoid_: LSP server plugin, LSP integration.

**LSP state**:
The condition of LSP for a specific (project, ecosystem) pair. One state per ecosystem detected in a project. The state machine the plugin reasons about and stores in the project state file.

The six states:

- `not-detected`: no **ecosystem marker** present for this ecosystem in this project. Hook is silent.
- `dismissed`: user opted out for this ecosystem via `/actually-lsp-ignore`. Hook is silent.
- `no-lsp-plugin`: ecosystem detected, no compatible **LSP plugin** enabled. Hook suggests install.
- `server-not-runnable`: LSP plugin enabled, but **language server** can't start (missing binary, missing deps). Hook suggests env fix.
- `ready`: LSP plugin enabled, language server runnable. Hook emits activation context. Rust's warm-up caveat is handled inside the Rust-specific activation context, not as a separate state.
- `error`: detection itself failed (broken marker file, filesystem permission denied, etc.). Hook surfaces the error rather than failing silently.

Possible future extension: `permission-missing` (LSP plugin works, `LSP` tool not in `permissions.allow` while user is on permission prompts). Folded into `server-not-runnable` for v1; split out if it deserves its own fix flow.

**nudge**:
The user-facing text the plugin emits when an ecosystem isn't in `ready` state. Audience is the user reading the session output. Short, suggests a setup action (install the plugin, run `cargo build`, etc.). Fires on `no-lsp-plugin`, `server-not-runnable`, and `error` states.
_Avoid_: hint, suggestion, prompt.

**activation context**:
The Claude-facing content the plugin emits when an ecosystem is `ready`. Audience is Claude. Names `ToolSearch select:LSP` and the operations the language server supports (`workspaceSymbol`, `goToDefinition`, etc.). Delivered as `additionalContext` from the hook. The name borrows directly from the Claude Code hook API field. This is the share-out's "preamble" by another name.
_Avoid_: preamble (the share-out's word, fine in research prose, less fine here where we want to anchor on the Claude Code platform vocab), hint, LSP context.

**dismissal**:
A user's choice to silence nudges for a specific (project, ecosystem) pair. Scope is per-project. Dismissing Rust in project A does not affect project B. Persistent across sessions. Set by `/actually-lsp-ignore`. Once dismissed, the plugin stays silent for that ecosystem in that project (no nudge, no activation context) until the user explicitly undoes it (future extension).

**trust-but-verify**:
The plugin's approach to **LSP state** caching. The cache is the fast path; detection re-runs on signal. The signals: ecosystem marker mtime change, `claude plugin list --json` hash change, an LSP tool failure in PostToolUse, or an explicit `/actually-lsp-doctor` invocation. No time-based TTL: verification is signal-driven, not periodic.

**/actually-lsp-doctor**:
The single user-facing action command. Diagnoses **LSP state** per detected ecosystem, then fixes anything that isn't `ready`, with a per-action permission prompt gating any state-changing step (gem installs, env builds, plugin installs). Arguments narrow focus: `fix` skips the diagnostic report and jumps straight to action; `<ecosystem>` scopes to one of `rust`, `typescript`, `ruby`. Matches the `bundle doctor` / `nvm doctor` pattern where a single command does both phases with the user steering via prompts.

The internal phases (named for prose, not commands):

- **diagnose**: read cache, run trust-but-verify checks, compute current **LSP state** per ecosystem.
- **setup**: initial installation phase when ecosystem state is `no-lsp-plugin`. Install the recommended **LSP plugin** (via `claude plugin install`, user-approved), then env fixes.
- **fix**: repair phase when ecosystem state is `server-not-runnable` or `error`. Run env fixes (e.g., `bundle install`, `cargo build`).

setup and fix are different phases of the same behavior; both transition an ecosystem toward `ready`. The user's invocation always lands in `/doctor`; the plugin picks which phases to run based on current state.

**/actually-lsp-ignore**:
Dismissal command. Scoped per-(project, ecosystem). With no argument, prompts the user to pick which detected ecosystem(s) to dismiss. With `<ecosystem>` argument, dismisses that one directly. Writes the **dismissal** to the project state file.

**failure context**:
The content the PostToolUse hook emits as `additionalContext` when an `LSP` tool call errors. Audience is Claude. Sibling concept to **activation context**. Both are additional-context payloads but for different lifecycle moments. v1 scope is minimal: pass the error through verbatim, name the affected ecosystem, and point at `/actually-lsp-doctor <ecosystem>` for re-verification. The hook also invalidates the cached LSP state for that ecosystem so the next deferred detection re-checks. No automated recovery in v1. Classifying failure modes is deferred until there's a corpus of real failures to pattern-match against.

**deferred detection**:
LSP state detection that runs after SessionStart, triggered by a PreToolUse hook when Claude touches a path outside the initial cwd's detected scope. Motivated by polyglot workspaces (e.g., pickletown) where SessionStart fires at a non-project root and the actual project work happens after a directory shift. Activation context delivered at this hook position lands at 0.4/5 per the share-out, below the activation cliff. The recourse is `/actually-lsp-doctor`, which surfaces activation context at the inline-prompt position (4.6/5) on demand.

**polyglot project**:
A project containing multiple ecosystem markers (e.g., a Rails app with a TypeScript frontend has both `Gemfile` and `package.json`). The plugin tracks LSP state independently per ecosystem; each ecosystem has its own dismissal flag, its own cached state, its own activation context. Hook output groups by ecosystem so the user can see per-ecosystem status at a glance.

## Relationships

- An **ecosystem** is detected by the presence of an **ecosystem marker**.
- An **ecosystem** has zero or more **language servers** available.
- An **LSP plugin** wraps exactly one **language server** and registers it for a Claude Code session.
- One project may contain multiple **ecosystems** (each with its own marker, its own **LSP state**).
- The **LSP state** is computed per (project, ecosystem) pair, never globally.

## Example dialogue

> **Dev:** Why doesn't Claude reach for the LSP I just installed?
> **Expert:** That's the **activation gap**. The **LSP plugin** registers the **language server**, but Claude defaults to grep unless it sees **activation context** at session start. `actually-lsp` delivers that.
>
> **Dev:** So if I'm in a polyglot repo with Rust and Ruby?
> **Expert:** Each **ecosystem** has its own **LSP state**. Rust might be `ready`, Ruby might be `no-lsp-plugin`. The hook emits a **nudge** for Ruby and activation context for Rust. Same SessionStart, two per-ecosystem outputs.
>
> **Dev:** What if rust-analyzer crashes mid-session?
> **Expert:** The PostToolUse hook catches that, emits **failure context** to Claude (so it doesn't loop on the same broken call), and invalidates the cache for Rust. Next time Claude touches a Rust file, **deferred detection** re-runs and computes fresh state.
>
> **Dev:** And if I don't want LSP for this project at all?
> **Expert:** `/actually-lsp-ignore rust`. That's a **dismissal**. Persists across sessions for this project, doesn't touch others.
>
> **Dev:** What about setup? I'm in a fresh Rust project.
> **Expert:** `/actually-lsp-doctor`. One command, runs whichever **setup** or **fix** phases the current state needs, prompts you before each state-changing action.

## Flagged ambiguities

- "doctor" was used both for the slash command and for the PostToolUse hook's diagnosis behavior. Resolved: the slash command is **/actually-lsp-doctor**, the hook's output is **failure context**. Both diagnose, but one is user-invoked and acts; the other is automatic and only emits context to Claude.
- "marker" was overloaded: ecosystem markers (`Cargo.toml`, etc.) vs marker files (state persistence). Resolved: **ecosystem marker** for the detection trigger, "state file" (or "project state file") for persistence. Reserved "marker" prefix for the detection role.
- "preamble" (from the share-out) vs "activation context". Resolved: **activation context** in this plugin's vocab to anchor on the Claude Code platform's `additionalContext` field. The share-out's "preamble" remains accurate for that document's research framing; this plugin uses "activation context" going forward.
