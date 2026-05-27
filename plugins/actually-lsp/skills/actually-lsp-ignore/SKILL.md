---
name: actually-lsp-ignore
description: Ignore actually-lsp nudges for an ecosystem in this project. Use when the user wants to silence, dismiss, or ignore the LSP setup nudges for a specific ecosystem (Rust, TypeScript, Ruby), or invokes `/actually-lsp-ignore` directly. Writes `dismissed=true` to `.claude/actually-lsp.json`. Persistent across sessions for this project only.
---

# /actually-lsp-ignore

Parse args:

- `rust` | `typescript` | `ruby` as an arg ignores that ecosystem directly.
- No args: read `.claude/actually-lsp.json` in the current project root, present the detected ecosystems, and ask the user which to ignore.

## Action

Update the project state file at `.claude/actually-lsp.json`: set `.ecosystems.<ecosystem>.dismissed` to `true`. If the file doesn't exist, create it with version 1 schema:

```json
{
  "version": 1,
  "ecosystems": {
    "<ecosystem>": {
      "state": "dismissed",
      "dismissed": true,
      "last_check_at": null,
      "last_marker_mtime": null,
      "last_plugin_list_hash": null,
      "last_error": null
    }
  }
}
```

If the file exists, preserve all other fields and only flip `dismissed`.

The internal state value stays `dismissed` (that's the state-machine name from `CONTEXT.md`); only the user-facing skill name is `ignore`.

## Confirmation output

Output a one-line confirmation per ignored ecosystem:

```
Ignoring <ecosystem> for this project. To re-enable, manually edit .claude/actually-lsp.json and set dismissed back to false. (A re-enable command is a future extension.)
```
