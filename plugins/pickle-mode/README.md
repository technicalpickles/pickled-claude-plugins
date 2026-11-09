# pickle-mode

My agent style, layered on [pstack](https://github.com/michael-denyer/pstack-claude)'s `poteto-mode`. pstack does the heavy lifting: principles, playbooks, subagent routing, autonomy. pickle-mode adds how I think about work (principles), a short list of gates where I work differently, and playbook overlays that route generic steps to plugins I already use.

## Install

```text
/plugin marketplace add michael-denyer/pstack-claude
/plugin install pstack@pstack-claude
/plugin install pickle-mode@pickled-claude-plugins
```

Optional, to stop pstack's own SessionStart hook from also routing to plain `poteto-mode`: add `session hook: off` to `~/.claude/pstack-models.md` (`/setup-pstack` writes that file). pickle-mode's hook works either way.

## What's in it

| Piece | What it does |
|---|---|
| [`skills/pickle-mode`](skills/pickle-mode/SKILL.md) | Loads `poteto-mode`, then applies precedence, principles, gates, and overlays |
| [`hooks/`](hooks/) | SessionStart routing to `pickle-mode` instead of `poteto-mode` |
| [`.agents/playbooks/`](.agents/playbooks/) | Overlays on pstack playbooks, in pstack's project-playbook format |
| [`scripts/check-overlays.sh`](scripts/check-overlays.sh) | Runs pstack's `check-playbooks.mjs` against the overlays |

Precedence, first match wins: the user's instructions, then the repository being worked in, then pickle-mode, then `poteto-mode`.

## Overlays

| Playbook | Routes to |
|---|---|
| Pause safely | `agent-meta:park` |
| Session pickup | `agent-meta:unpark` |

Overlays anchor on quoted step text from pstack's playbooks. pstack rewrites steps often, so CI runs `check-overlays.sh` daily against pstack-claude's `main` and fails when an anchor disappears.

```bash
plugins/pickle-mode/scripts/check-overlays.sh            # newest installed pstack
plugins/pickle-mode/scripts/check-overlays.sh <pstack>   # a specific checkout's plugins/pstack
```
