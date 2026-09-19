# Reddit

Hosts: `reddit.com`, `www.reddit.com`, `old.reddit.com`, `redd.it` (short links: resolve to the
full `/comments/<id>` URL first if the user gave one). Resolve a `redd.it` short link by fetching
it with `WebFetch` (it follows the redirect) and reading the final URL, then pass that to
`reddit-post`. If that does not yield a `/comments/<id>` URL, stop and ask the user for the full
link. This is only redirect resolution, not content scraping.

## Read

```bash
reddit-post <post-url>            # post + 10 comments
reddit-post -n 25 <post-url>      # more comments when the discussion is the point (comments come in the order Reddit's feed returns them, not ranked)
```

Only post permalinks (`/comments/<id>`) work. For a subreddit or user page, ask the user which
post they mean.

**Requires** `uv` (stdlib-only script) and a shell that can reach `www.reddit.com`; no Reddit credentials. It reads the post's Atom feed (`<permalink>.rss`). Reddit rate-limits back-to-back requests; the script waits and retries twice on its own. If it reports `sandbox proxy? www.reddit.com may need allowlisting`, that is the sandbox, not Reddit: say so and let the user allowlist the host or approve an unsandboxed run.

## Frontmatter extras

Beside `source`, from the `reddit-post` header line (`r/<sub> -- u/<author> -- <YYYY-MM-DD>`; the date is the post's `published`):

```yaml
platform: reddit
subreddit: commandline
author: alice
published: 2026-01-01
```

## Failure mode

If `reddit-post` exits non-zero (rate limit, block, deleted post), stop and report the HTTP status
it printed. Do not fall back to scraping HTML or write from the thread title alone.
