# Command effects and `--safe`

Added in hk 1.55 (2026-08-11). Not available before that. Verified on hk 2.0.0 and 2.7.1.

## What it is

Each command declares what it does to the world:

| Effect | Meaning | Under `--safe` |
|--------|---------|----------------|
| `read` | Only reads project files | allowed |
| `write` | May modify files, or write caches and build output | allowed |
| `destructive` | Deletes or overwrites things that can't be recovered | **refused** |
| (none) | Plain string command, or `CommandSpec` without `effect` | **refused** (unknown) |

`--safe` is an all-or-nothing preflight. If any runnable command is unknown or destructive, hk refuses before starting any step:

```
--safe refused to run:
  s.check: effect is unknown
```

It checks declared effects only. It is not a sandbox, and hk does not verify a command behaves as declared.

## Declaring one

```pkl
["typecheck"] {
  check = new CommandSpec {
    command = "pyrefly check"
    effect = "write"
  }
}
```

For both halves of a formatter:

```pkl
check = new CommandSpec { command = "fmt --check {{files}}"; effect = "read" }
fix   = new CommandSpec { command = "fmt {{files}}"; effect = "write" }
```

## Choosing

- **Pure linters and format checks: `read`.** The command reads files and prints findings.
- **Fixers: `write`.**
- **Type checkers, compilers, and anything that populates a cache or `obj/`/`target/`: usually `write`.** Upstream's own `mypy`, `tsc`, and `dotnet_format` builtins use `write` because they leave caches or build output in the tree. Don't assume it from the category: run the tool and diff the tree before and after. `pyrefly check` leaves nothing behind, so brineworks declares it `read` (technicalpickles/brineworks#65). Mislabeling something as `read` is the dangerous direction; when unsure, say `write`.
- **`destructive`** for commands that delete or irreversibly rewrite. `--safe` will never run them, which is the point.
- **Scripts you wrote that only inspect the repo** (version validators, link checkers): `read`, once you've read the script.

## Why `read` is a promise

From hk 2.4 and 2.5, steps declared `read` run in parallel, including in fix hooks, and a `check_diff` with `effect = "read"` computes its patch under read locks. A step that claims `read` but writes will race with other steps. Declare `read` only if it really only reads the step's files.

## Builtins

Every builtin command declares an effect (1.55 and later; no builtin is `destructive`), so builtins work under `--safe` unchanged. Only your own steps, and builtin commands you override with a bare string, need declaring.

## Where this bites

Coding-agent hooks (`hk agent hooks --target claude-code` calls `hk agent stop-hook`, which runs `hk run check --safe`). A project with custom string-command steps gets a Stop hook that refuses until each step has an effect. That's expected: declare them once.
