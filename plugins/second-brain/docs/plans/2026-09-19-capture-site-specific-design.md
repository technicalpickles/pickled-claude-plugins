# Capture: site-specific behavior

Status: design, approved in conversation 2026-09-19. Not yet planned or implemented.

## Problem

`capture` treats every URL as a generic web page. Step 2 has a one-row-per-source table
(web, tweet, PDF, Notion, Slack) and nothing else is site-aware. X, YouTube and Reddit each
have their own reading constraints (login walls, transcripts vs slides, comment trees) and
their own useful metadata (author, channel, subreddit, publish date). Two personal scripts
already exist in dotfiles for this (`xtweet`, `yt-digest`); Reddit has none.

## Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Structure | Per-site playbooks in `capture`'s references, dispatched by URL host | One entry point. A skill per site adds trigger surface competing with `capture`, and description tuning has a structural ceiling (see repo CLAUDE.md). |
| Tool distribution | Scripts move into the plugin's `bin/` | A script's own requirements are its own problem (`xtweet` needs `xurl`, `yt-digest` needs `uv` and a logged-in `claude`). X is blocked without such a path anyway. |
| Note shape | Light: extra frontmatter only | Body stays the standard prose note (`note-format.md`). Site fields are cheap to query and don't sprawl into templates. |
| Single dispatcher script (`fetch-source <url>`) | Deferred | Possible followup if playbooks get repetitive. Would hide per-site judgment (talking head vs slides) inside a script, so not first. |

## Layout

```
plugins/second-brain/
├── bin/                      # xtweet, yt-digest, reddit reader (new)
└── skills/capture/
    ├── SKILL.md              # Step 2: host dispatch table
    └── references/sites/
        ├── x.md
        ├── youtube.md
        ├── reddit.md
        └── web.md            # current default, extracted
```

## Step 2 change

Match the URL host to a playbook and read it. Unknown hosts use `web.md`. The dispatch replaces
the URL rows of the current source table; PDF, Notion and Slack rows stay.

## Playbook contract

Every playbook has three parts:

1. **Read**: exact tool, flags, and requirements.
   - X: `xtweet <url>`; `-q` for the quoted chain, `-r` when replies matter. Requires `xurl`.
   - YouTube: `yt-digest` in full mode (video, transcript, on-screen text) by default. The
     agent does not ask the user to choose. Fall back to `--transcript-only` only with a
     concrete reason, stated in the reply: the video is very long (download and OCR cost
     outweigh the value), the download fails or is blocked, or the content is evidently
     audio-only (podcast, talk over a static frame). A talking head alone is not a reason.
   - Reddit: **blocked, no working path yet.** The planned `reddit-post <url>` (unauthenticated
     `.json` endpoint) got a 403 from Reddit on 2026-09-19 (see "To verify"). Needs a redesign
     before a Reddit playbook can ship; until then a Reddit URL stops and says so.
   - Web: `mcp__lightpanda__markdown`, `WebFetch` fallback (unchanged behavior).
2. **Frontmatter extras**, added beside `source`:
   - X: `platform: x`, `author`, `published`
   - YouTube: `platform: youtube`, `channel`, `published`
   - Reddit: `platform: reddit`, `subreddit`, `author`, `published`
   - Vault `CLAUDE.md` vocabulary wins on any collision (per `note-format.md`).
3. **Failure mode**: if the tool is missing, unauthenticated, or blocked, stop and say so.
   No fallback to scraping and no note written from a snippet. This is the existing "never
   fabricate" constraint made site-specific.

## Scripts

- `xtweet` and `yt-digest` move from dotfiles `bin/`. Header comments document requirements.
- Dotfiles' `bin/CLAUDE.md` and `claude/CLAUDE.md` pointers change to say the tools ship with
  second-brain; the dotfiles copies become symlinks or are removed. That is a dotfiles-repo
  change, done separately.
- The Reddit reader is new. Probe first (unauthenticated `.json`, sandbox behavior, rate
  limits, blocking) and design from what works.

## To verify before implementation

- Plugin `bin/` on PATH: verified 2026-09-19 with `claude -p --plugin-dir` against a temp copy
  holding an executable `bin/sb-probe`. A Bash tool call running bare `sb-probe` printed
  `probe-ok`. **`BIN_ON_PATH = yes`**, so playbooks and `allowed-tools` invoke scripts by bare
  name. `${CLAUDE_PLUGIN_ROOT}` did **not** expand in a Bash tool call (`echo
  "${CLAUDE_PLUGIN_ROOT}"` printed an empty line), so don't spell invocations with it.
- Reddit access path (above): probed 2026-09-19 with `curl -A 'second-brain-capture/1.0
  (personal note capture)'` against `https://www.reddit.com/r/commandline/top.json?limit=1&t=week&raw_json=1`.
  **`REDDIT_JSON = blocked`.** Sandboxed, the proxy denied `www.reddit.com:443` (CONNECT 403,
  a `<sandbox_violations>` entry), so that hop is a sandbox allowlist issue. Retried once
  unsandboxed to separate the causes: Reddit itself answered `403` with an HTML block page
  (not JSON, no rate-limit headers), so the unauthenticated `.json` endpoint is blocked from
  this environment. The post-permalink shape check was not possible (no JSON to parse). Two
  requests total; no workaround attempted. The `reddit-post` design must be revisited.
- Frontmatter field names against the vault's own `CLAUDE.md`.

## Testing

- Trigger evals (`skills/capture/evals/`): add per-site prompts so bare `x.com` and
  `youtube.com` links still route to `capture`.
- Scripts: smoke tests for URL parsing at minimum; neither script has tests today.
- Version bump via `./scripts/bump-version.sh --auto`.
