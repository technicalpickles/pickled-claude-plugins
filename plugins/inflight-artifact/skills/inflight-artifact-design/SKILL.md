---
name: inflight-artifact-design
description: Use when the user wants to set up or change what the in-flight page captures or how it is organized: first-run setup, add or rename a section, sort unsorted PRs or tasks, add a page (for example a separate one for a side project), change exclusions or the lede, or asks "what does it capture". Iterates on a scratch preview before touching the live page. For routine refreshes use inflight-artifact.
---

# inflight-artifact-design

Owns everything that *defines* the pages. Its sibling `inflight-artifact` only runs them. The config is written by prompting: the user describes what they want, this skill writes the JSON. Nobody hand-edits it.

Where things live:

| Thing | Location | Written by |
|---|---|---|
| Pages: exclusions, sections and their match rules, lede, needs, next rows, history | `${user_config.config_dir}/pages/<page>.json` | this skill |
| Settings: github_user, repo_roots, task_backend (used when flags are not passed) | `${user_config.config_dir}/settings.json` | this skill |
| CSS/JS overrides (optional; the plugin's own are the default) | `${user_config.config_dir}/page.css`, `page.js` | this skill |
| Facts, session registry, rendered HTML | `${CLAUDE_PLUGIN_DATA}` | `inflight-artifact` only |
| Engine: `gather.py`, `render.py`, templates | `${CLAUDE_PLUGIN_ROOT}` | the plugin's source repo, not this skill |

A change that needs the engine (a new captured field, a new kind of card) is a change to the plugin's source. Say so, offer to make it in a checkout of the plugin repo, and do not edit files under `${CLAUDE_PLUGIN_ROOT}`: they are replaced on update.

## First run

1. Ask for the page's name and scope: which repos and owners count, and what is off limits (becomes `exclude`, a regex over repo names, titles and task projects).
2. Copy `${CLAUDE_PLUGIN_ROOT}/examples/config/pages/example.json` to `${user_config.config_dir}/pages/<name>.json`.
3. Run a gather (see `inflight-artifact`), render with no sections, and look at the Unsorted list together. Propose sections from what is there: group by repo, title keywords and task projects, and cross-repo efforts the user names.
4. Continue with the loop below until the page reads right.

## Loop

1. **Restate** the change in one or two lines, and what it touches.
2. **Change** the config. A new section or page is JSON only.
3. **Re-render from the saved `facts.json`** (no re-gather, so it is fast and offline): `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/render.py" <page> --config-dir "${user_config.config_dir}" --state-dir "${CLAUDE_PLUGIN_DATA}" --preview --out <scratch dir>/<page>.html`. Re-gather only when the change needs fresh data.
4. **Publish to a scratch artifact**, never the live URL: one artifact reused for every preview (find it by its title starting "PREVIEW:" with `Artifact` action `list`; create it on first use). `--preview` makes it unmistakable: the page title is "PREVIEW: <title> (scratch)", and it carries a sticky warning bar, a dashed outline and a striped background. Show the link and say what moved.
5. **Wait for approval.** On a yes, render without the banner and publish to the page's `artifact_url` (read it first; a new page gets its URL recorded in its config). Append a dated line to `${user_config.config_dir}/CHANGELOG.md`: what changed and why, in a sentence.

## Config reference

- `exclude`: regex, case-insensitive, matched against repo name, PR title, task project, tags and description.
- `threads[]` (sections), in priority order, first match wins: `id`, `title`, `status`, `lede`, `ignore` (true collapses it on What's next and hides it from the Overview), `match`, `next`.
- `match` keys: `repos`, `pr_refs` (`repo#n`), `pr_title` (regex), `task_projects` (prefix match), `task_tags`, `task_desc` (regex), `task_refs` (8-hex prefix).
- `next[]` rows: `{"text", "task": "<8-hex>" | "pr": "repo#n", "you": true}`. Set `"you": true` for rows only the user can do; they also appear under "Needs you". Rows with a ref disappear when the task completes or the PR is no longer open.
- `needs[]`: `{"text", "refs": ["task:<8-hex>", "pr:repo#n"]}`; an item drops when every ref has resolved.
- `history[]`: `{"date", "thread", "text"}` hand-written notes shown on What happened.

## Rules

- Never publish a design change straight to the live page.
- Keep PR and CI links on every PR row.
- Page copy: plain direct wording, no emoji.
- Do not edit the state directory. If the facts are stale, run `inflight-artifact`.
- Gather makes one `gh` call and runs in the foreground; a credential broker may bulk-deny loops or detached runs.
- On a "what does it capture" question, answer with a table of every field in `facts.json`, its source command, and where `render.py` shows it, so gaps are visible.
