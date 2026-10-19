# Anatomy of a step

The minimal step, the command forms, and builtin overrides below were run against hk 2.0.0 and 2.7.1. The field table comes from the upstream docs (hk 2.7.1) and was not run here. On 1.x the same fields apply, but commands are plain strings (no `CommandSpec`) and the step lives under `hooks { ["<hook>"] { steps { ... } } }`.

## Minimal step (2.x)

```pkl
amends "package://github.com/jdx/hk/releases/download/v2.0.0/hk@2.0.0#/Config.pkl"
import "package://github.com/jdx/hk/releases/download/v2.0.0/hk@2.0.0#/Builtins.pkl"

steps {
  ["no-todo"] {
    glob = List("*.md", "docs/**/*.md")
    exclude = List("docs/vendor/**")
    check = new CommandSpec {
      command = "! grep -n TODO {{files}}"
      effect = "read"
    }
  }
}
```

Top-level `steps` creates the `check`, `fix` and `pre-commit` hooks. `check` never fixes or stages; `fix` applies fixes without staging; `pre-commit` fixes, stages, and stashes unstaged work.

## Fields that matter

| Field | Meaning |
|-------|---------|
| `glob` | Files the step applies to. No match means the step is skipped. No `glob` means it can run with no files, which suits whole-project commands. |
| `exclude` | Patterns removed after `glob`. |
| `check` | Reports problems with a nonzero exit. Must leave files unchanged. |
| `fix` | Applies fixes and reports what remains. |
| `check_diff` | Prints a patch instead of failing. hk can apply it as the fix. |
| `check_list_files` + `check_failed_files = true` | Cheap "which files are bad" pass first, then the full `check` only on those. |
| `depends` | Wait for another step. File locking already stops simultaneous writes; `depends` sets order. |
| `profiles` | Optional steps, e.g. `profiles = List("slow")` runs only with `--slow`. |
| `stage` | After a fix in a staging hook, which paths to `git add`. List generated outputs here, never `git add` inside the command. |
| `dir`, `env`, `prefix` | Working dir, environment, and a launcher such as `List("mise", "x", "--")`. |
| `workspace_indicator` | Group files by the nearest project marker (`Cargo.toml`, `go.mod`) and run once per workspace. |
| `diagnostic_format` | `gcc`, `sarif`, `eslint-json` or `cargo-json`. Without it a failing step has raw output but no structured diagnostics. |

## Command forms

**Shell string.** Runs through a shell, so pipes, `&&`, redirects and expansion work.

```pkl
check = "eslint {{files}} | tee eslint.log"
```

**Structured `argv`.** No shell. Each entry is one argument, so filenames with spaces stay intact. A standalone `{{files}}` entry expands to one argument per file.

```pkl
check = new Command { argv = List("grep", "-q", "hi", "{{files}}") }
```

**With an effect (1.55 and later).** The effect goes on a `CommandSpec`. For argv, nest the `Command` (verified on 2.0.0 and 2.7.1):

```pkl
check = new CommandSpec {
  command = new Command { argv = List("grep", "-q", "hi", "{{files}}") }
  effect = "read"
}
```

Putting `argv` straight on `CommandSpec` fails with `cannot add property 'argv' to non-open class`.

## Templates

`{{files}}`, `{{workspace}}`, `{{workspace_indicator}}`, `{{workspace_files}}`, and in `commit-msg` hooks `{{commit_msg_file}}`. Commands are Tera templates, so a literal `{{` needs `{% raw %}{{...}}{% endraw %}`.

## Overriding a builtin

```pkl
["ruff"] = (Builtins.ruff) {
  glob = List("src/**/*.py")
  exclude = List("**/generated/**")
}
```

The amended object keeps everything you don't override. Overriding a builtin's command with a bare string drops its declared effect (it becomes unknown under `--safe`), so keep it a `CommandSpec` and restate the effect.

## Check vs fix vs staging

A `check` reads; a `fix` may write. hk takes read locks for checks and write locks for fixes, and does not sandbox commands, so a `check` that writes can corrupt another step's view. Staging is a hook setting: on by default in `pre-commit`, off for `hk fix` and custom hooks (use `hk fix --stage` or `stage = true`). A step's `stage` list only filters which paths get staged once staging is on.
