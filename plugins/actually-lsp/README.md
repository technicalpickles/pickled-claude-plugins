# actually-lsp

Makes Claude Code actually use the LSP tools you've installed.

## Why this exists

Installing an LSP plugin (`rust-analyzer-lsp`, `typescript-lsp`, `ruby-lsp` from `claude-plugins-official`) doesn't change Claude's behavior. Claude defaults to `grep` and `Read` even on tasks where LSP would be better. This is the **activation gap**.

`actually-lsp` detects the state of LSP setup in your project and nudges:

- If you don't have the LSP plugin installed but the project needs it, suggest installing.
- If you have it installed but the environment isn't ready (no `bundle install`, no `cargo build`, etc.), surface that.
- If everything's ready, deliver activation context so Claude reaches for the LSP tool instead of grep.

Full background: [the activation gap share-out](https://github.com/technicalpickles/pickleton/blob/main/projects/claude-test-harness/docs/2026-05-21-lsp-activation-gap-share-out.md).

## Status

v1 supports TypeScript, Rust, and Ruby.

## Install

```bash
/plugin install actually-lsp@pickled-claude-plugins
```

Then install the official LSP plugin for your ecosystem:

```bash
/plugin install typescript-lsp@claude-plugins-official
```

Restart Claude Code.

## Configuration

State lives at `<project>/.claude/actually-lsp.json`. Gitignored by default; commit it if you want shared team state.

## Commands

- `/actually-lsp-doctor [fix] [<ecosystem>]`: diagnose and fix LSP setup. With no args, runs a per-ecosystem diagnostic then fixes anything not `ready`. `fix` skips the report and jumps straight to action. `<ecosystem>` narrows to one of `rust`, `typescript`, `ruby`.
- `/actually-lsp-ignore [<ecosystem>]`: ignore nudges for an ecosystem in this project. With no arg, prompts to pick.

## Internals

- [CONTEXT.md](CONTEXT.md): vocabulary and state machine
- [docs/adr/](docs/adr/): architectural decisions
- [docs/plans/2026-05-27-design.md](docs/plans/2026-05-27-design.md): design spec
