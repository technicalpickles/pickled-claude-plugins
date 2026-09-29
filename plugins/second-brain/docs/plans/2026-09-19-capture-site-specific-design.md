# Capture: site-specific behavior

Status: implemented (see 2026-09-19-capture-site-specific-plan.md).

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
├── bin/                      # xtweet, yt-digest, reddit-post
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
   - Reddit: `reddit-post <url>` reads the post's Atom feed (`<permalink>.rss`), not `.json`
     (blocked, see "Verified during implementation"). Feed carries post title, author, body, comment bodies and the subreddit
     (`<category term="commandline" label="r/commandline"/>`); comments have only `updated`.
     The sandbox proxy denies `www.reddit.com`, so the script needs that host allowlisted or an
     unsandboxed run, and it must handle HTTP 429 (rate limit hit on a request seconds after the previous one). Reddit not reachable or blocked: stop and say so.
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

All three live in `plugins/second-brain/bin/`, on PATH for Bash tool calls. Tests are in
`plugins/second-brain/bin/tests/` (`xtweet.bats`, `test_yt_digest.py`, `test_reddit_post.py`).

- `xtweet` and `yt-digest` moved from dotfiles `bin/`. Header comments document requirements.
  `yt-digest` also writes `metadata.json` (title, channel, published, url, duration_seconds),
  because the frontmatter needs channel and published. It is best-effort, written on fresh
  runs and `--transcript-only`, not with `--skip-download`.
- `reddit-post` is a stdlib-only Python `uv run --script`. It reads the post's Atom feed
  (`<permalink>.rss`), not the `.json` endpoint (blocked, HTTP 403) and not curl/jq. It retries
  HTTP 429 with backoff (waits about 30s, twice).
- The dotfiles side (copies of `xtweet`/`yt-digest`, pointer docs) is a separate change, see
  Followups.

## Verified during implementation

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
- Reddit RSS alternative: probed 2026-09-19 with the same User-Agent. **`REDDIT_ALT = rss`.**
  Sandboxed, the proxy again denied `www.reddit.com:443` (sandbox blocker, separate from
  Reddit). Unsandboxed: `https://www.reddit.com/r/commandline/top/.rss?t=week&limit=1` returned
  `200` Atom XML. A post feed `<permalink>.rss?limit=5` returned `429` on the first try
  (seconds after the previous request; a bare 429, empty body), then `200` (6177 bytes) after a
  30s wait, with `x-ratelimit-used: 1`, `x-ratelimit-remaining: 0.0`, `x-ratelimit-reset: 26`,
  so back-to-back requests get throttled and the script needs a retry/backoff. Sample
  permalink: `https://www.reddit.com/r/commandline/comments/1wfk0ns/a_gopher_watches_your_typing_test/`.
  Post feed shape: first `<entry>` is the post (`id` `t3_...`, `title`, `author/name` as
  `/u/name`, `content` HTML with the self-text or link, `updated` and `published`); following
  entries are comments (`id` `t1_...`, `title` "/u/x on <post title>", `author/name`, `content`
  HTML, `updated` only, no `published`). Limit 5 gave the post plus 5 comments. old.reddit.com
  was not tried (not needed). Untested: nested reply structure, long threads, "more comments"
  handling, deleted posts. Four-request budget: 3 requests reached Reddit (one 200, one 429, one
  200), plus the sandbox-denied attempt.
- Frontmatter field names against the vault's own `CLAUDE.md`: done. No collisions found in
  `~/Vaults/pickled-knowledge/CLAUDE.md` as of 2026-09-19.

## Testing

- Trigger evals (`skills/capture/evals/`) extended to 24 queries, including per-site prompts, and
  measured with no regression. The new positives were already 3/3 before the pointer widening,
  so no lift shown; the queries guard against regression.
- Scripts have tests (see Scripts).
- Version bump via `./scripts/bump-version.sh --auto`.

## Followups

Each is filed as a taskwarrior task (tag `second-brain`).

1. `fetch-source <url>` dispatcher script (option C from brainstorming, deferred).
2. Dotfiles cleanup: replace `bin/xtweet` and `bin/yt-digest` in the dotfiles repo with symlinks
   to the plugin's bin (or remove), and update dotfiles `bin/CLAUDE.md` and `claude/CLAUDE.md`
   pointers.
3. Sandbox network allowlist: the command sandbox's proxy denies `www.reddit.com`, so
   `reddit-post` only works unsandboxed until the host is allowed (dotfiles `claude/roles/*.jsonc`
   holds sandbox network config). `api.x.com` and the YouTube hosts for xtweet/yt-digest are also
   unverified under the sandbox.
4. `trigger_eval.py` crashes on a relative `--plugin-src ../../..` (`Path.name` is `..`), and
   `evals/README.md` "Running them" still shows that command. Fix with `Path(p).resolve()` in the
   script.
