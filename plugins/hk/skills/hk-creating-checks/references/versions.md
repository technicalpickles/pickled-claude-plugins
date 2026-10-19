# hk versions: what changes for checks

Source: upstream `docs/` and GitHub release notes for jdx/hk, current as of v2.7.1 (2026-10-19). Examples in this skill were run against hk 2.0.0 and 2.7.1; behavior from releases in between is sourced from release notes and not run here. 1.x syntax could not be run in the authoring sandbox (hk 1.x shells out to the `pkl` CLI, which needs network access to fetch the schema package).

## Timeline

| Release | Date | Change that matters for writing checks |
|---------|------|----------------------------------------|
| 1.54 | 2026-07-31 | Each hk command declares its own effect in the usage spec. |
| **1.55** | 2026-08-11 | `CommandSpec` with `effect = read|write|destructive`. `--safe`. `hk agent`, `hk mcp`, `--format json|jsonl`. Every builtin declares effects. String commands are "unknown" effect. |
| 1.56 | 2026-08-19 | About 100 builtins move to structured `argv`. |
| **2.0** | 2026-09-13 | Top-level `steps` creates implicit `check`, `fix`, `pre-commit` hooks. Staging is contextual (only `pre-commit` stages by default). Builtins are flat typed steps with options. Config must be `hk.pkl` (no `hk.toml`/`.yaml`/`.json`). `hk.local.pkl` replaces project `.hkrc.pkl`. hk no longer invokes the `pkl` CLI. |
| 2.4 | 2026-09-28 | `check_diff` with `effect = "read"` runs under read locks, in parallel. |
| 2.5 | 2026-10-04 | Read-only `check` steps run in parallel in fix hooks. `hk agent stop-hook` (Stop hooks now call it). `--safe` refuses a hook-level `report` with unknown effect. |
| 2.6 | 2026-10-12 | `hk agent stop-hook` passes in projects with no hk config or no `check` hook. |

The `hk` plugin in this repo targets 2.5 and later for that reason: its Stop hook is `hk agent stop-hook`, and hk older than 2.5 gets no hook from it.

## Same step, three ways

**hk 1.x before 1.55** (unverified here, from upstream v1 docs): string commands, steps inside hooks.

```pkl
amends "package://github.com/jdx/hk/releases/download/v1.35.0/hk@1.35.0#/Config.pkl"
import "package://github.com/jdx/hk/releases/download/v1.35.0/hk@1.35.0#/Builtins.pkl"

hooks {
  ["check"] {
    steps {
      ["no-todo"] { glob = List("*.md") check = "! grep -n TODO {{files}}" }
    }
  }
}
```

**hk 1.55 and later 1.x**: same shape, but `check = new CommandSpec { command = "..."; effect = "read" }` so `--safe` accepts it.

**hk 2.x** (verified on 2.0.0 and 2.7.1):

```pkl
amends "package://github.com/jdx/hk/releases/download/v2.0.0/hk@2.0.0#/Config.pkl"

steps {
  ["no-todo"] {
    glob = List("*.md")
    check = new CommandSpec { command = "! grep -n TODO {{files}}"; effect = "read" }
  }
}
```

## Translating 1.x to 2.x

- Move shared steps to top-level `steps`. Existing steps inside `hooks` still work in 2.x, and you don't have to move them.
- `gitleaks_staged` is `(Builtins.gitleaks) { scan = "staged" }`; `knip_strict` is `strict = true`; `pinact_v3` is `version = "3"`.
- `Builtins.check_byte_order_marker` and `fix_byte_order_marker` become `Builtins.byte_order_marker`.
- `hk generate` is `hk init`. `~/.hkrc.pkl` is `~/.config/hk/config.pkl`. `defaults { jobs = ... }` settings move to the top level.
- Staging is contextual in 2.x: `pre-commit` fixes and stages, while `hk fix` and custom hooks leave changes unstaged unless `stage = true` or `--stage`. Check hooks you migrate for staging you were relying on.

## Picking a schema version

Pin the `amends` URL to the hk the project runs (`hk@2.0.0` in the URL, matching the `mise.toml` pin), so the schema and the binary agree on which fields exist.

## Refreshing this skill

1. `gh api repos/jdx/hk/releases --jq '.[0:5][] | .tag_name'` for the latest.
2. Read `docs/configuration.md`, `docs/agents.md`, `docs/migration-v2.md` from `gh api -H "Accept: application/vnd.github.raw" repos/jdx/hk/contents/docs/<file>`.
3. Grep release bodies for `effect`, `CommandSpec`, `--safe`, `Breaking Changes`, and update the timeline above.
4. Re-run the verified examples against a real `hk` and update the version note in SKILL.md.
