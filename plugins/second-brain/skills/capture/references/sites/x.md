# X / Twitter

Hosts: `x.com`, `twitter.com`, `mobile.twitter.com`.

## Read

```bash
xtweet <url-or-id>        # a single post
xtweet -q <url-or-id>     # this post + everything it quotes
xtweet -r <url-or-id>     # this post + its replies (one API call)
```

Use `-q` when the post quotes another (the quoted post is usually the point). Use `-r` when the
replies carry the substance (a question, a thread of corrections). For a multi-post thread by one
author, run `xtweet` on each post URL the user gave; do not guess at posts you were not shown.

**Requires** `xurl` authenticated for the X API and `jq`. Direct fetches of x.com are blocked
(login wall, JS rendering), so `xtweet` is the only path in.

## Frontmatter extras

Beside `source`:

```yaml
platform: x
author: "@handle"
published: 2026-01-01
```

`author` and `published` come from the `xtweet` header line (`Name (@handle) -- <created_at>`).
Quote `author` (an unquoted leading `@` is a YAML reserved indicator).

## Failure mode

If `xtweet` is not found, `xurl` is unauthenticated, or the API returns an error, stop and report
the exact message. Do not retry via WebFetch or a browser and do not write from memory of the post.
