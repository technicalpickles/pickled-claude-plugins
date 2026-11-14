---
name: woodpecker-investigating-pipelines
description: Use when a Woodpecker CI pipeline failed or its status is unclear - a red `ci/woodpecker/...` check, "Pipeline failed" from `gh pr checks`, a Woodpecker `/repos/<id>/pipeline/<n>` URL, "why did CI fail" in a repo that builds with Woodpecker, or a push that has no CI result at all.
---

# Investigating Woodpecker pipelines

Woodpecker's web UI and REST API need a login Claude doesn't have, and a forge status only says "failed". `woodpecker-snapshot` drives `woodpecker-cli` (already logged in) and prints one block: the pipeline's state, every step's state, and the first failed step's log tail.

## Run it

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/woodpecker-snapshot" [REF] [--pr N | --sha SHA] [--repo owner/name] [--tail N]
```

| Input | Looks up |
|-------|----------|
| nothing | the pipeline for the current commit (repo from the git remote) |
| `--pr N` or `--sha SHA` | the pipeline for that commit (needs `gh` for `--pr`) |
| a number | that pipeline number |
| a pipeline URL | the repo ID and number in it |

Exit 0 means a state was reported, including `failed`. Exit 2 means it couldn't read Woodpecker; the `State:` line says why.

## Read the State line first

The first line is always `State: <state>`. Report that state, not a guess from the forge status.

| State | Do this |
|-------|---------|
| `failed` | Read the log tail for the **first** failure. Later skipped steps are fallout. If the tail cuts off before the error, rerun with a larger `--tail`. |
| `passed` | Mention any "failed but ignored" warning. It means a step fails on every run. |
| `running`, `queued`, `blocked` | Say so and stop. Don't call it passed or failed. `blocked` needs approval in the Woodpecker UI, which is the user's step. |
| `no pipeline` | Never read this as passing. Go through the listed causes. A silent webhook outage looks exactly like this. |
| `not set up`, `unauthorized` | The login is the user's step (it stores a token in the system keychain, which a command sandbox may block). Show the printed fix and see [references/setup.md](references/setup.md). |
| `unreachable` | Says nothing about the code. If the sandbox blocked the host, the printed fix is an allowlist entry. |
| `unknown` | Show the raw status or error as printed. Don't interpret it. |

## When the snapshot isn't enough

Raw commands, status strings seen so far, and CLI quirks are in [references/states.md](references/states.md).
