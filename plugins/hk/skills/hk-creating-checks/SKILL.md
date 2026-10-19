---
name: hk-creating-checks
description: Use when adding, writing, or fixing a check (step) in an hk.pkl, picking a builtin or writing a custom command, declaring an effect for `--safe`, or when hk reports "effect is unknown", "unexpected argument '--safe'", or "Hook 'check' not found". Also use when a step's syntax differs between hk 1.x and 2.x.
---

# Creating hk checks

A check is an hk **step**: a name, the files it applies to, and `check` / `fix` commands. This skill is about writing one that works on the hk version the project actually runs.

## First: which hk?

Syntax and agent-safety features changed a lot between 1.x and 2.x. Find out before writing anything:

```bash
hk --version                                  # the runtime
grep -m1 'hk@' hk.pkl                         # the schema the config amends (hk@X.Y.Z)
grep -n 'hk' mise.toml .mise.toml 2>/dev/null # what the project pins
```

The `amends` URL decides what syntax is valid; the binary decides what runs. They can disagree. Check [references/versions.md](references/versions.md) for what each version supports. The short version:

| hk | What you can use |
|----|------------------|
| before 1.55 | String commands only. No `effect`, no `--safe`, no `hk agent`. |
| 1.55 and later | `CommandSpec` with `effect`, `--safe`, `hk agent`, `hk mcp`. |
| 2.0 and later | Top-level `steps` (implicit `check`, `fix`, `pre-commit` hooks), flat builtins with options, Pkl-only config. |

## Workflow

1. **Look for a builtin first.** `hk builtins | grep -i <tool>`. Use `Builtins.<name>` and override only what differs: `(Builtins.ruff) { glob = List("src/**/*.py") }`. Builtins already declare effects (1.55 and later).
2. **Otherwise write a step.** See [references/step-anatomy.md](references/step-anatomy.md) for fields, command forms (shell string vs `argv`), templates like `{{files}}`, and `check` vs `fix` vs `check_diff`.
3. **Declare the effect** (1.55 and later). `--safe` refuses a step whose effect is unknown, and coding-agent hooks run `--safe`. See [references/effects.md](references/effects.md) for how to choose `read`, `write`, or `destructive`.
4. **Wire it into hooks.** On 2.x, put it under top-level `steps` and it appears in `check`, `fix`, and `pre-commit`. On 1.x, add it to each `hooks { ... steps { } }` block.
5. **Verify** (below).

## Verify

```bash
hk validate                                    # config loads
hk run check --plan --all                      # which steps and files would run
hk run check --step <name> --all               # run just this step
hk run check --safe --all --format json        # what an agent hook will see (1.55 and later)
```

If `--safe` fails with `effect is unknown`, the step needs a `CommandSpec`. If it passes a step you expect to fail, run the step's command by hand: hk only reports what the command's exit status says.

## Common failures

| Symptom | Cause | Fix |
|---------|-------|-----|
| `--safe refused to run: s.check: effect is unknown` | String command, or `CommandSpec` without `effect` | Wrap in `new CommandSpec { command = "..."; effect = "read" }` |
| `unexpected argument '--safe'` | hk older than 1.55 | Drop `--safe`, or upgrade the pin |
| `Hook 'check' not found` | `hk.pkl` has hooks but no `check` hook | 2.x: define top-level `steps`. 1.x: add a `check` hook |
| `cannot add property 'argv' to non-open class` | `argv` put directly on `CommandSpec` | `command = new Command { argv = List(...) }` |
| Template error on a command with `{{` | The command's own syntax uses `{{` and hk renders it as a template | Wrap in `{% raw %}...{% endraw %}` |
| Step runs on no files | No `glob`, so it runs whenever the hook does | Add `glob`, or accept it as a whole-project check |
| Check edits files | `check` must be read-only, and hk's file locking assumes it is | Move the edit to `fix`, or declare `effect = "write"` honestly |

## Sources

Built from the upstream hk docs and release notes, current as of hk 2.7.1 (2026-10-19). Examples marked verified were run against a real hk 2.0.0. See [references/versions.md](references/versions.md) for how to refresh.
