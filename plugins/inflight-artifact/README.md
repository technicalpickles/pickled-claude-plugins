# inflight-artifact

A private "what's in flight" page, as a Claude artifact. It shows your open PRs with links to their CI builds, the Claude sessions you have running, what shipped recently, and what needs you. You shape it by prompting: tell `inflight-artifact-design` which work belongs together ("the Postgres migration", "dev hosts") and it writes the config. A page can also carry hand-written blocks and extra tabs (a status table, a capabilities list) that the refresh keeps current from notes in its config.

## Install

```text
/plugin install inflight-artifact@pickled-claude-plugins
```

The install asks for four settings:

| Setting | What it is |
|---|---|
| `config_dir` | Folder for your pages and settings. Point it at a git checkout or notes vault to keep a history of changes. The plugin never writes the config anywhere else. |
| `github_user` | Login whose PRs to track (open and merged). |
| `repo_roots` | Optional, comma-separated. Folders whose child repos are checked for uncommitted work and drift. |
| `task_backend` | `taskwarrior` or `none`. |

## What's in it

| Piece | What it does |
|---|---|
| [`skills/inflight-artifact-refresh`](skills/inflight-artifact-refresh/SKILL.md) | Keeps the page true: gather facts, follow the page's refresh notes, re-check the hand-written prose against its sources, render, publish. Owns state, never structure. |
| [`skills/inflight-artifact-design`](skills/inflight-artifact-design/SKILL.md) | Owns structure: first-run setup and every later change to sections, match rules, exclusions and tabs. Also runs a cold read to find prose that has gone stale. Iterates on a clearly marked scratch preview and publishes to the live page only on your yes. |
| [`scripts/`](scripts/) | `gather.py` (up to three `gh` GraphQL calls, plus tasks and local repos), `render.py` (pure: facts + config to HTML), `sessions.py` (session registry, one file per session), `session_hook.py` (logs each session's repo and branch at start and whenever its cwd changes, marks it idle at end). |
| [`hooks/hooks.json`](hooks/hooks.json) | SessionStart, CwdChanged and SessionEnd run `session_hook.py`. Pages place logged sessions by scope, linked tasks, or an explicit `--page`. |
| [`examples/config`](examples/config/) | A sanitized starting config. |

## The page

Three tabs with direct links (`#overview`, `#happened`, `#next`):

- **Overview.** A short lede, **Needs you**, active sessions, and a card per section.
- **What happened.** Merged PRs and finished tasks, newest first, filterable by section.
- **What's next.** Per section: next steps, open PRs with draft, conflict and CI chips, top tasks.

Every PR links to GitHub and every open PR carries a CI chip that links to the build, or says "no CI". PRs and tasks that no section claims land in **Unsorted** instead of vanishing.

Previews render with `--preview`: the title becomes "PREVIEW: ... (scratch)", with a sticky warning bar, a dashed outline and a striped background, so a scratch artifact is never mistaken for the live one.

## Notes

- `gather.py` makes at most three `gh` calls (open PRs, merged PRs one search per day, changed files for path-scoped pages; folding them into one request makes GitHub answer 502) and must run in the foreground. A credential broker such as [Automic Vault](../automic-vault/) approves each `gh` invocation separately and ties it to Claude through the process tree, so loops and detached runs get denied.
- Facts and the session registry live in `${CLAUDE_PLUGIN_DATA}`, which survives updates.
- Tests: `python3 -m unittest discover -s tests` from this folder.
