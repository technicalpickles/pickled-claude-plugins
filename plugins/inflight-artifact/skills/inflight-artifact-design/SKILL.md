---
name: inflight-artifact-design
description: Use when the user wants to set up or change what the in-flight page captures or how it is organized: first-run setup, add or rename a section, sort unsorted PRs or tasks, add a page (for example a separate one for a side project), change exclusions or the lede, or asks "what does it capture". Iterates on a scratch preview before touching the live page. For routine refreshes use inflight-artifact.
---

# inflight-artifact-design

Owns everything that *defines* the pages. Its sibling `inflight-artifact` only runs them. The config is written by prompting: the user describes what they want, this skill writes the JSON. Nobody hand-edits it.

Where things live:

| Thing | Location | Written by |
|---|---|---|
| Pages: scope, exclusions, sections and their match rules, rows, needs, tabs, refresh notes | `${user_config.config_dir}/pages/<page>.json` | this skill |
| Page content that goes stale: lede, history entries, hand-written blocks | `pages/<page>.json`, `pages/<page>/*.html` | `inflight-artifact` on refresh, as the page's `refresh` notes say; this skill when the user asks |
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

Prose in the config (`lede`, `intro`, row `text`, `needs`, `history` text, fragment files) is inline HTML: write `<code>`, `<a href>` and `<b>` directly, and escape a literal `<` or `&`. Text that comes from facts (PR titles, task descriptions) is escaped by the renderer.

- `exclude`: regex, case-insensitive, matched against repo name, PR title, task project, tags and description.
- `include`: the page's scope, `{"prs": [rule], "tasks": [rule]}`. Every key in a rule must hold; any rule admits the item. Leave a list out to admit everything. PR rule keys: `repos`, `pr_title`, `pr_paths` (regex over changed file paths; gather fetches paths for the repos a page scopes, or for every PR when the page has no PR scope, so keep path-matched pages scoped). Task rule keys: `task_projects`, `task_tags`, `task_desc`. A task or PR that a row names is always in scope.
- `threads[]` (sections), in priority order, first match wins: `id`, `title`, `status` (`now` feeds the Overview's "Up next"), `lede`, `ignore` (true collapses it on What's next and hides it from the Overview), `match`, and three row lists: `next`, `then`, `parked` (folded away).
- `match` keys: `repos`, `pr_refs` (`repo#n`), `pr_title` (regex), `pr_paths` (regex), `task_projects` (prefix match), `task_tags`, `task_desc` (regex), `task_refs` (8-hex prefix). A row's `task` or `pr` claims it for that section before any match rule runs.
- Rows: `{"text", "task": "<8-hex>" | "pr": "repo#n", "you": true, "kind": "security", "tone": "crit|warn|ok|info"}`. Set `"you": true` for rows only the user can do; they appear under "Needs you" instead of "Up next". Rows with a ref disappear when the task completes or the PR is no longer open.
- `needs[]`: `{"text", "refs": ["task:<8-hex>", "pr:repo#n"]}`; an item drops when every ref has resolved.
- `history[]`: `{"date", "text", "thread" | "group"}` hand-written notes on What happened. Never trimmed.
- `filters[]`: `{"id", "label", "repos", "task_projects"}` replaces the per-section filter on What happened with groups such as one per repo. History entries name their `group`.
- `auto_events`: `false` keeps What happened to the hand-written history; merged PRs still list under "Shipped, by repo" (which reads `ledger.json`, every merged PR gather has seen).
- `intro` (under the title), `happened_lede`, `next_lede`: page-level prose.
- Hand-written blocks live as files in `pages/<page>/`: `overview_html` (list, shown after the lede), `tabs` (`[{"id", "title", "file"}]`, extra tabs after What's next), `css` (extra CSS for those blocks; scope it under a wrapper class so it cannot restyle the rest of the page), `shipped_archive` (an old hand-written shipped list, folded under "Shipped, by repo"). Task rows in a block use `<li class="task" tabindex="0" role="button" data-t="<8-hex>">` so they open the task popup, and a task a block shows counts as sorted. An element with `data-checked="YYYY-MM-DD"` gets a "stale Nd" chip once that date is three days old (or `data-stale-after` days), counted when the page is opened, so a block that says when it was last verified cannot look fresh days after a refresh.
- `refresh[]`: instructions the run skill follows on every refresh of this page (which block to rewrite from which command, what to re-verify and against what). Put page-specific knowledge here, not in the skills.

After a render, `${CLAUDE_PLUGIN_DATA}/<page>.unsorted.json` lists the PR refs and task prefixes no section claims. Read it when sorting.

## Rules

- Never publish a design change straight to the live page.
- Keep PR and CI links on every PR row.
- Page copy: plain direct wording, no emoji.
- Do not edit the state directory. If the facts are stale, run `inflight-artifact`.
- Gather makes at most three `gh` calls and runs in the foreground; a credential broker may bulk-deny loops or detached runs.
- On a "what does it capture" question, answer with a table of every field in `facts.json`, its source command, and where `render.py` shows it, so gaps are visible.
