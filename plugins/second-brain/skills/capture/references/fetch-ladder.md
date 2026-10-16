# Fetch ladder

Read the real source, never a snippet. Work down this list and stop at the first rung that
returns the page's actual content. If Josh names a fetch method, use that one, or say plainly why
you can't before moving on.

1. **`lightpanda fetch --dump markdown <url>` via Bash**, when `lightpanda` is on PATH. Under the
   sandbox the URL's host must be in `allowed_domains`. A long page can still be mid-fetch: a
   background command reports "running in background"; wait for it, don't treat it as failed.
2. **The browser pane**, for JS-rendered pages and multi-page captures: `get_page_text`, plus
   `read_page` with `filter: interactive` on the nav to list the real links. Follow those hrefs.
   Guessed subpage URLs 404.
3. **A fetcher built for the source:**

   | Source | Command |
   |--------|---------|
   | Tweet / thread | `xtweet <url-or-id>` (`-q` quoted chain, `-r` replies) |
   | YouTube | `yt-digest --transcript-only <url>` |
   | arXiv | `curl https://arxiv.org/html/<id>`, not `/abs/`; re-check cited numbers against the raw text |
   | GitHub repo | `gh api repos/<owner>/<repo>` and `.../readme` |
   | Hacker News | the Algolia items API |
   | Gmail / Drive / Notion / Slack | their connectors |
   | Local file or upload | `Read` |

4. **WebFetch, last.** It summarizes and silently truncates long pages. A note built from it gets
   `fetched-via: webfetch` in the frontmatter and, right under the title, the line
   `_Read via WebFetch summary_`. For a long or number-heavy source, pair it with one of the rungs
   above.

## Cannot reach the source

Stop and say so. A note needs a page you loaded: no URL you didn't open, no title you inferred, no
details from background knowledge.

## Batch and long sources

Subagents report coverage with their note: roughly what share of the source they retrieved, and
whether anything looked truncated. See [batch.md](batch.md).
