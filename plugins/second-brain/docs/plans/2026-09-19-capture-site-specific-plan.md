# Capture Site-Specific Behavior Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `capture` reads X, YouTube and Reddit sources through per-site playbooks backed by scripts that ship in the second-brain plugin, and records a few site-specific frontmatter fields.

**Architecture:** `capture/SKILL.md` Step 2 dispatches on the URL host to `references/sites/<site>.md`. Each playbook states how to read the source, which frontmatter extras to add, and the failure mode. `xtweet` and `yt-digest` move from dotfiles into `plugins/second-brain/bin/`; a new `reddit-post` script joins them. The vault CLAUDE.md pointer template is widened so bare X/YouTube/Reddit links still trigger `capture`.

**Tech Stack:** bash + jq (`xtweet`), Python via `uv run --script` (`yt-digest`, `reddit-post`), bats and unittest for tests.

**Spec:** [2026-09-19-capture-site-specific-design.md](2026-09-19-capture-site-specific-design.md)

## Global Constraints

- Commit format `type(scope): description`; `feat`/`fix`/`perf` need a scope; scope here is `second-brain`. Commit trailer: `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>`.
- All paths below are relative to the worktree root. Run commands from there.
- Step references in commits and docs use the slugs below, never ordinals.
- Frontmatter extras go beside `source`; on any collision the vault's own `CLAUDE.md` vocabulary wins (`note-format.md`).
- A playbook whose tool is missing, unauthenticated or blocked stops and says so. No scraping fallback, no note from a snippet.
- YouTube defaults to full `yt-digest`. `--transcript-only` only with a stated reason: very long video, download fails or is blocked, or evidently audio-only. A talking head alone is not a reason.
- Body of a captured note stays the standard prose note; playbooks change frontmatter only.
- Existing scripts must keep working unchanged when moved (same flags, same output).
- Plugin versions are bumped via `./scripts/bump-version.sh --auto`, committed as `chore(second-brain): bump version to X.Y.Z`.

---

### probe-plugin-bin: does a plugin `bin/` reach PATH?

**Files:**
- Create (temporary, deleted at end of task): `plugins/second-brain/bin/sb-probe`
- Modify: `plugins/second-brain/docs/plans/2026-09-19-capture-site-specific-design.md` (record result under "To verify before implementation")

**Interfaces:**
- Produces: a recorded answer, `BIN_ON_PATH = yes|no`, used by `capture-dispatch` to choose how `allowed-tools` and playbooks spell script invocations.

- [ ] **Step 1: Create the probe script**

```bash
mkdir -p plugins/second-brain/bin
printf '#!/usr/bin/env bash\necho probe-ok\n' > plugins/second-brain/bin/sb-probe
chmod +x plugins/second-brain/bin/sb-probe
```

- [ ] **Step 2: Ask a headless Claude whether `sb-probe` is a bare command**

An installed `second-brain` wins over `--plugin-dir`, so run against a temp copy (same trick as `trigger_eval.py`):

```bash
PROBE_DIR="$(mktemp -d)" && cp -R plugins/second-brain "$PROBE_DIR/second-brain"
cd "$PROBE_DIR" && claude -p --plugin-dir "$PROBE_DIR/second-brain" --allowedTools "Bash" \
  "Run exactly: sb-probe   Then report its stdout verbatim, or the shell error if it is not found." ; cd -
```

Expected: either `probe-ok` (bin is on PATH) or `command not found`.

- [ ] **Step 3: If not found, check the `${CLAUDE_PLUGIN_ROOT}` form**

```bash
cd "$PROBE_DIR" && claude -p --plugin-dir "$PROBE_DIR/second-brain" --allowedTools "Bash" \
  'Run exactly: echo "${CLAUDE_PLUGIN_ROOT}"   Report stdout verbatim.' ; cd -
```

Record whether it prints the plugin path. If it prints empty, the plan's fallback invocation is a path found via `sb`-style discovery; stop and report to the user before continuing.

- [ ] **Step 4: Record the result and remove the probe**

Under "To verify before implementation" in the design doc, replace the first bullet with the observed result (`BIN_ON_PATH = yes/no`, and whether `${CLAUDE_PLUGIN_ROOT}` expanded in Bash). Then:

```bash
rm plugins/second-brain/bin/sb-probe && rmdir plugins/second-brain/bin 2>/dev/null || true
git add plugins/second-brain/docs/plans/2026-09-19-capture-site-specific-design.md
git commit -m "docs(second-brain): record plugin bin PATH probe result

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### probe-reddit: what Reddit access actually works

**Files:**
- Modify: `plugins/second-brain/docs/plans/2026-09-19-capture-site-specific-design.md` (fill the Reddit "Read" entry)

**Interfaces:**
- Produces: a recorded answer, `REDDIT_JSON = works|blocked`. **Gate:** if `blocked`, stop; the `reddit-post` task below is written for the `.json` path and must be redesigned with the user before continuing.

- [ ] **Step 1: Probe the unauthenticated JSON endpoint (sandboxed)**

```bash
curl -sS -o "$TMPDIR/reddit.json" -w '%{http_code}\n' \
  -A 'second-brain-capture/1.0 (personal note capture)' \
  'https://www.reddit.com/r/commandline/top.json?limit=1&t=week&raw_json=1'
```

Expected: `200`. A `403`/`429`, or a `<sandbox_violations>` block naming the host, is the signal for the gate.

- [ ] **Step 2: If sandbox-denied, retry unsandboxed once to separate "sandbox" from "Reddit blocks us"**

Re-run Step 1 with `dangerouslyDisableSandbox: true` only because Step 1 showed a sandbox denial. Record which case you hit.

- [ ] **Step 3: Confirm a real post + comments URL has the shape the script will parse**

Take any `permalink` from `$TMPDIR/reddit.json` (`jq -r '.data.children[0].data.permalink' "$TMPDIR/reddit.json"`), then:

```bash
curl -sS -A 'second-brain-capture/1.0 (personal note capture)' \
  "https://www.reddit.com$(jq -r '.data.children[0].data.permalink' "$TMPDIR/reddit.json").json?limit=5&raw_json=1" \
  | jq 'type, length, (.[0].data.children[0].data | keys | map(select(. == "title" or . == "selftext" or . == "author" or . == "subreddit" or . == "created_utc" or . == "permalink" or . == "score" or . == "num_comments" or . == "url" or . == "is_self")))'
```

Expected: `"array"`, `2`, and all ten field names listed.

- [ ] **Step 4: Record result in the design doc and commit**

Replace `Reddit: TBD by probe (see below).` in the design doc's Read section with `Reddit: reddit-post <url> (unauthenticated .json endpoint; probed 2026-09-19: <result>)`, and add the sandbox/rate-limit observation to "To verify".

```bash
git add plugins/second-brain/docs/plans/2026-09-19-capture-site-specific-design.md
git commit -m "docs(second-brain): record reddit access probe result

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### probe-reddit-rss: does .rss or old.reddit.com work when .json is blocked?

Added 2026-09-19 after `probe-reddit` found the `.json` endpoint blocked (sandbox proxy denies
`www.reddit.com`; Reddit itself answers 403 to unauthenticated curl). The user chose to probe
the cheap alternatives before considering a browser or OAuth path.

**Files:**
- Modify: `plugins/second-brain/docs/plans/2026-09-19-capture-site-specific-design.md` (record result in "To verify" and the Reddit "Read" entry)

**Interfaces:**
- Produces: a recorded answer, `REDDIT_ALT = rss | old-html | none`, plus the working URL shape and sample permalink. **Gate:** `reddit-reader` only proceeds on `rss` (or `old-html` if the user agrees to HTML parsing). On `none`, stop and ask the user to choose between the browser and OAuth paths.

- [ ] **Step 1: Probe the RSS endpoint of a post and of a subreddit (sandbox first)**

```bash
UA='second-brain-capture/1.0 (personal note capture)'
curl -sS -o "$TMPDIR/sub.rss" -w '%{http_code}\n' -A "$UA" 'https://www.reddit.com/r/commandline/top/.rss?t=week&limit=1'
```

Expected: `200` and Atom XML (`head -c 400 "$TMPDIR/sub.rss"`). A `<sandbox_violations>` denial means retry this one command once with `dangerouslyDisableSandbox: true` and record that the sandbox is a separate blocker from Reddit.

- [ ] **Step 2: If Step 1 gave a post link, try that post's RSS (comments included)**

Take a post permalink from `$TMPDIR/sub.rss` (`grep -o 'https://www.reddit.com/r/commandline/comments/[^"<]*' "$TMPDIR/sub.rss" | head -1`), then:

```bash
curl -sS -o "$TMPDIR/post.rss" -w '%{http_code}\n' -A "$UA" "<permalink>.rss?limit=5"
```

Expected: `200`; the feed has the post entry first and comment entries after it.

- [ ] **Step 3: Only if RSS is blocked, try old.reddit.com once**

```bash
curl -sS -o "$TMPDIR/old.html" -w '%{http_code}\n' -A "$UA" "https://old.reddit.com/<permalink path>"
```

At most 4 requests total across the task. No other endpoints, no third-party mirrors, no scraping loops.

- [ ] **Step 4: Record and commit**

Record the status codes, sandbox-vs-Reddit attribution, the working URL shape, and what fields the feed carries (title, author, published date, body, comment bodies) in the design doc; set `REDDIT_ALT`. Commit as `docs(second-brain): record reddit rss probe result`.

---

### move-xtweet: bring xtweet into the plugin with tests

**Files:**
- Create: `plugins/second-brain/bin/xtweet` (copied byte-for-byte from `~/github.com/technicalpickles/dotfiles/bin/xtweet`)
- Test: `plugins/second-brain/bin/tests/xtweet.bats`

**Interfaces:**
- Produces: `xtweet [-j] [-q] [-r] <tweet-url-or-id>...`, unchanged. Requires `xurl` (authenticated for the X API) and `jq` on PATH.

- [ ] **Step 1: Write the failing test**

Create `plugins/second-brain/bin/tests/xtweet.bats`:

```bash
#!/usr/bin/env bats
# xtweet tests: a stub `xurl` on PATH returns canned API JSON, so no X
# credentials or network are needed.

XTWEET="$BATS_TEST_DIRNAME/../xtweet"

setup() {
  STUB_DIR="$(mktemp -d)"
  export PATH="$STUB_DIR:$PATH"
  cat > "$STUB_DIR/xurl" <<'STUB'
#!/usr/bin/env bash
if [[ -n "${XURL_FAIL:-}" ]]; then
  echo '{"errors":[{"code":453,"message":"boom"}]}'
else
  echo '{"data":{"id":"123","text":"hello world","created_at":"2026-01-01T00:00:00Z","author_id":"9","public_metrics":{"like_count":1,"retweet_count":2,"reply_count":3,"impression_count":4}},"includes":{"users":[{"id":"9","name":"Ann","username":"ann"}]}}'
fi
STUB
  chmod +x "$STUB_DIR/xurl"
}

teardown() {
  rm -rf "$STUB_DIR"
}

@test "--help exits 0 and prints usage" {
  run "$XTWEET" --help
  [ "$status" -eq 0 ]
  [[ "$output" == *"usage: xtweet"* ]]
}

@test "no arguments exits 1 with usage" {
  run "$XTWEET"
  [ "$status" -eq 1 ]
  [[ "$output" == *"usage: xtweet"* ]]
}

@test "bare numeric ID formats author and text" {
  run "$XTWEET" 123
  [ "$status" -eq 0 ]
  [[ "$output" == *"Ann (@ann)"* ]]
  [[ "$output" == *"hello world"* ]]
  [[ "$output" == *"https://x.com/ann/status/123"* ]]
}

@test "status URL resolves to the same tweet as a bare ID" {
  run "$XTWEET" "https://x.com/ann/status/123"
  [ "$status" -eq 0 ]
  [[ "$output" == *"hello world"* ]]
}

@test "a string with no tweet ID exits 1 and says so" {
  run "$XTWEET" "https://example.com/not-a-tweet"
  [ "$status" -eq 1 ]
  [[ "$output" == *"couldn't find a tweet ID"* ]]
}

@test "API errors are reported, not swallowed" {
  XURL_FAIL=1 run "$XTWEET" 123
  [[ "$output" == *"API error for 123"* ]]
  [[ "$output" == *"boom"* ]]
}
```

- [ ] **Step 2: Run to verify it fails**

Run: `bats plugins/second-brain/bin/tests/xtweet.bats`
Expected: FAIL (`xtweet` does not exist in the plugin yet).

- [ ] **Step 3: Copy the script in**

```bash
cp ~/github.com/technicalpickles/dotfiles/bin/xtweet plugins/second-brain/bin/xtweet
chmod +x plugins/second-brain/bin/xtweet
```

Then add a "Requires" block to the header comment, directly under the `# xtweet -- read a tweet ...` paragraph:

```bash
# Requires: `xurl` on PATH and authenticated for the X API (`xurl auth ...`),
# plus `jq`. Without xurl, X content is unreachable from the CLI, so this
# script is the path in; it has no scraping fallback by design.
```

- [ ] **Step 4: Run to verify it passes**

Run: `bats plugins/second-brain/bin/tests/xtweet.bats`
Expected: 6 tests, all pass. Also `shellcheck plugins/second-brain/bin/xtweet` should report nothing new versus the dotfiles copy (`shellcheck ~/github.com/technicalpickles/dotfiles/bin/xtweet` for the baseline).

- [ ] **Step 5: Commit**

```bash
git add plugins/second-brain/bin/xtweet plugins/second-brain/bin/tests/xtweet.bats
git commit -m "feat(second-brain): ship xtweet in the plugin bin

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### reddit-reader: new reddit-post script (Atom/RSS)

Rewritten 2026-09-19 after `probe-reddit` (`.json` blocked) and `probe-reddit-rss` (`REDDIT_ALT = rss`).
Observed: `<post permalink>.rss?limit=N` returns an Atom feed: entry 1 is the post (`published`, `author/name`
as `/u/<user>`, HTML `content`), entries 2..N+1 are comments (`author/name`, `updated` only, HTML `content`),
and the feed-level `<category term="<sub>" label="r/<sub>"/>` names the subreddit. Reddit answers `429`
(empty body) to back-to-back requests and recovers after ~30s (`x-ratelimit-reset`). The sandbox proxy denies
`www.reddit.com` (CONNECT 403), so a sandboxed run cannot reach it.

**Files:**
- Create: `plugins/second-brain/bin/reddit-post`
- Test: `plugins/second-brain/bin/tests/test_reddit_post.py`

**Interfaces:**
- Produces: `reddit-post [-n COUNT] [--print-url] <reddit-post-url>` (`-n` default 10). Prints a header line `r/<sub> -- u/<author> -- <YYYY-MM-DD>`, then `🔗 <permalink>`, the title, the post body as plain text, `🔗 <url>` when the post links out, then `--- comments (N) ---` and each comment as `u/<author> -- <YYYY-MM-DD>` plus its plain-text body. `--print-url` prints the feed URL it would fetch and exits 0. Exit 1 with a `reddit-post:` message on a non-post URL, HTTP error, or unreachable host. On `429` it waits (the `x-ratelimit-reset` header + 1s, else 30s, capped at 60s) and retries up to twice, saying so on stderr. If the connection error is the sandbox proxy's ("Tunnel connection failed"), the message adds `(sandbox proxy? www.reddit.com may need allowlisting)`.
- Python module-level functions, importable by the test: `feed_url(url: str, count: int) -> str`, `parse_feed(xml_text: str) -> dict` with keys `subreddit, permalink, post, comments` (post/comment dicts: `author, date, text`; post also `title, link`), `fetch(url, ua=UA, opener=urllib.request.urlopen, sleep=time.sleep, retries=2) -> str`, `format_output(feed: dict) -> str`, `RedditError(Exception)`.
- Requires `uv` only (stdlib script, no dependencies, same `uv run --script` convention as `yt-digest`). No credentials.

- [ ] **Step 1: Write the failing tests**

`plugins/second-brain/bin/tests/test_reddit_post.py`:

```python
"""Tests for reddit-post. The Atom fixture is synthetic but follows the shape
observed from a real post feed on 2026-09-19 (see the design doc)."""
import importlib.machinery
import importlib.util
import io
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parent.parent / "reddit-post"


def load_module():
    loader = importlib.machinery.SourceFileLoader("reddit_post", str(SCRIPT))
    spec = importlib.util.spec_from_loader("reddit_post", loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules["reddit_post"] = module
    loader.exec_module(module)
    return module


rp = load_module()

PERMALINK = "https://www.reddit.com/r/commandline/comments/abc123/a_neat_tool/"

FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:media="http://search.yahoo.com/mrss/">
  <category term="commandline" label="r/commandline"/>
  <title>a neat tool : commandline</title>
  <entry>
    <author><name>/u/alice</name><uri>https://www.reddit.com/user/alice</uri></author>
    <content type="html">&lt;!-- SC_OFF --&gt;&lt;div class="md"&gt;&lt;p&gt;Body text &lt;a href="https://example.com/repo"&gt;the repo&lt;/a&gt;.&lt;/p&gt;&lt;/div&gt;&lt;!-- SC_ON --&gt; &amp;#32; submitted by &amp;#32; &lt;a href="https://www.reddit.com/user/alice"&gt; /u/alice &lt;/a&gt; &lt;span&gt;&lt;a href="https://example.com/repo"&gt;[link]&lt;/a&gt;&lt;/span&gt; &lt;span&gt;&lt;a href="https://www.reddit.com/r/commandline/comments/abc123/a_neat_tool/"&gt;[comments]&lt;/a&gt;&lt;/span&gt;</content>
    <id>t3_abc123</id>
    <link href="https://www.reddit.com/r/commandline/comments/abc123/a_neat_tool/"/>
    <updated>2026-01-01T10:00:00+00:00</updated>
    <published>2026-01-01T09:00:00+00:00</published>
    <title>A neat tool</title>
  </entry>
  <entry>
    <author><name>/u/bob</name><uri>https://www.reddit.com/user/bob</uri></author>
    <content type="html">&lt;div class="md"&gt;&lt;p&gt;First comment&lt;/p&gt;&lt;/div&gt;</content>
    <id>t1_c1</id>
    <link href="https://www.reddit.com/r/commandline/comments/abc123/a_neat_tool/c1/"/>
    <updated>2026-01-02T11:00:00+00:00</updated>
    <title>/u/bob on A neat tool</title>
  </entry>
  <entry>
    <author><name>/u/carol</name><uri>https://www.reddit.com/user/carol</uri></author>
    <content type="html">&lt;div class="md"&gt;&lt;p&gt;Second comment&lt;/p&gt;&lt;/div&gt;</content>
    <id>t1_c2</id>
    <link href="https://www.reddit.com/r/commandline/comments/abc123/a_neat_tool/c2/"/>
    <updated>2026-01-03T12:00:00+00:00</updated>
    <title>/u/carol on A neat tool</title>
  </entry>
</feed>
"""


class FeedUrl(unittest.TestCase):
    def test_normalizes_host_strips_query_and_fragment(self):
        url = "https://old.reddit.com/r/commandline/comments/abc123/a_neat_tool/?utm_source=share#x"
        self.assertEqual(
            rp.feed_url(url, 10),
            "https://www.reddit.com/r/commandline/comments/abc123/a_neat_tool.rss?limit=10",
        )

    def test_count_is_used(self):
        self.assertIn("limit=3", rp.feed_url(PERMALINK, 3))

    def test_host_without_scheme(self):
        self.assertTrue(rp.feed_url("reddit.com/r/x/comments/abc123/t/", 5).startswith("https://www.reddit.com/r/x/comments/abc123/t.rss"))

    def test_non_post_url_is_an_error(self):
        with self.assertRaises(rp.RedditError) as ctx:
            rp.feed_url("https://www.reddit.com/r/commandline/", 10)
        self.assertIn("/comments/", str(ctx.exception))


class ParseFeed(unittest.TestCase):
    def setUp(self):
        self.feed = rp.parse_feed(FEED)

    def test_subreddit_and_permalink(self):
        self.assertEqual(self.feed["subreddit"], "commandline")
        self.assertEqual(self.feed["permalink"], PERMALINK)

    def test_post_fields(self):
        post = self.feed["post"]
        self.assertEqual(post["title"], "A neat tool")
        self.assertEqual(post["author"], "alice")
        self.assertEqual(post["date"], "2026-01-01")
        self.assertIn("Body text", post["text"])
        self.assertNotIn("submitted by", post["text"])
        self.assertNotIn("[comments]", post["text"])
        self.assertNotIn("<", post["text"])

    def test_link_post_url_is_captured_only_when_it_leaves_reddit(self):
        self.assertEqual(self.feed["post"]["link"], "https://example.com/repo")

    def test_comments_use_updated_when_no_published(self):
        comments = self.feed["comments"]
        self.assertEqual([c["author"] for c in comments], ["bob", "carol"])
        self.assertEqual(comments[0]["date"], "2026-01-02")
        self.assertEqual(comments[0]["text"], "First comment")

    def test_empty_feed_is_an_error(self):
        with self.assertRaises(rp.RedditError):
            rp.parse_feed('<feed xmlns="http://www.w3.org/2005/Atom"></feed>')


class FormatOutput(unittest.TestCase):
    def test_full_output(self):
        out = rp.format_output(rp.parse_feed(FEED))
        self.assertIn("r/commandline -- u/alice -- 2026-01-01", out)
        self.assertIn(PERMALINK, out)
        self.assertIn("A neat tool", out)
        self.assertIn("Body text", out)
        self.assertIn("--- comments (2) ---", out)
        self.assertIn("u/bob -- 2026-01-02", out)
        self.assertIn("Second comment", out)


def http_error(code, headers=None):
    return urllib.error.HTTPError("https://x", code, "err", headers or {}, io.BytesIO(b""))


class FakeResponse:
    def __init__(self, body):
        self.body = body

    def read(self):
        return self.body.encode()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class Fetch(unittest.TestCase):
    def test_retries_429_using_the_reset_header_then_succeeds(self):
        calls = iter([http_error(429, {"x-ratelimit-reset": "26"}), FakeResponse("ok")])

        def opener(req, timeout):
            result = next(calls)
            if isinstance(result, Exception):
                raise result
            return result

        sleeps = []
        self.assertEqual(rp.fetch("https://x", opener=opener, sleep=sleeps.append), "ok")
        self.assertEqual(sleeps, [27])

    def test_429_without_header_waits_30s(self):
        calls = iter([http_error(429), FakeResponse("ok")])

        def opener(req, timeout):
            result = next(calls)
            if isinstance(result, Exception):
                raise result
            return result

        sleeps = []
        rp.fetch("https://x", opener=opener, sleep=sleeps.append)
        self.assertEqual(sleeps, [30])

    def test_gives_up_after_retries(self):
        def opener(req, timeout):
            raise http_error(429)

        with self.assertRaises(rp.RedditError) as ctx:
            rp.fetch("https://x", opener=opener, sleep=lambda s: None, retries=2)
        self.assertIn("HTTP 429", str(ctx.exception))

    def test_other_http_errors_do_not_retry(self):
        attempts = []

        def opener(req, timeout):
            attempts.append(1)
            raise http_error(403)

        with self.assertRaises(rp.RedditError) as ctx:
            rp.fetch("https://x", opener=opener, sleep=lambda s: None)
        self.assertIn("HTTP 403", str(ctx.exception))
        self.assertEqual(len(attempts), 1)

    def test_sandbox_proxy_denial_gets_a_hint(self):
        def opener(req, timeout):
            raise urllib.error.URLError("Tunnel connection failed: 403 Forbidden")

        with self.assertRaises(rp.RedditError) as ctx:
            rp.fetch("https://x", opener=opener, sleep=lambda s: None)
        self.assertIn("allowlisting", str(ctx.exception))


class Main(unittest.TestCase):
    def test_print_url_needs_no_network(self):
        out = io.StringIO()
        code = rp.main(["--print-url", "-n", "4", PERMALINK], fetcher=None, out=out)
        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue().strip(), "https://www.reddit.com/r/commandline/comments/abc123/a_neat_tool.rss?limit=4")

    def test_non_post_url_exits_1(self):
        err = io.StringIO()
        with mock.patch.object(sys, "stderr", err):
            code = rp.main(["https://www.reddit.com/r/commandline/"], fetcher=None, out=io.StringIO())
        self.assertEqual(code, 1)
        self.assertIn("reddit-post:", err.getvalue())

    def test_prints_formatted_feed(self):
        out = io.StringIO()
        code = rp.main([PERMALINK], fetcher=lambda url: FEED, out=out)
        self.assertEqual(code, 0)
        self.assertIn("First comment", out.getvalue())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run to verify it fails**

Run: `python3 plugins/second-brain/bin/tests/test_reddit_post.py`
Expected: FAIL at load (`reddit-post` does not exist: `FileNotFoundError`).

- [ ] **Step 3: Write the script**

`plugins/second-brain/bin/reddit-post`:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""reddit-post -- read a Reddit post and its comments by URL, via the post's
Atom feed (append .rss to any post permalink).

Requires: uv (stdlib-only script). No Reddit credentials. If Reddit blocks or
rate-limits the request this exits 1 with the HTTP status; it never falls back
to scraping HTML. www.reddit.com must be reachable: a sandboxed shell may deny
it (the error says so).

Usage:
    reddit-post <post-url>
    reddit-post -n 25 <post-url>         # more comments (default 10)
    reddit-post --print-url <post-url>   # show the feed URL and exit
"""

from __future__ import annotations

import argparse
import html
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

ATOM = "{http://www.w3.org/2005/Atom}"
UA = "second-brain-capture/1.0 (personal note capture)"
POST_PATH = re.compile(r"/comments/[A-Za-z0-9]+")


class RedditError(Exception):
    pass


def feed_url(url: str, count: int) -> str:
    """Keep only the path, require a /comments/<id> permalink, rebuild on www.reddit.com."""
    path = re.sub(r"^(?:[a-z]+://)?[^/]+", "", url.strip())
    path = re.split(r"[?#]", path, maxsplit=1)[0].rstrip("/")
    if not POST_PATH.search(path):
        raise RedditError(f"expected a post URL containing /comments/<id>, got: {url}")
    return f"https://www.reddit.com{path}.rss?limit={count}"


def _wait_seconds(headers) -> int:
    try:
        return min(max(int(float(headers.get("x-ratelimit-reset", 30))) + 1, 1), 60)
    except (TypeError, ValueError):
        return 30


def fetch(url, ua=UA, opener=urllib.request.urlopen, sleep=time.sleep, retries=2) -> str:
    for attempt in range(retries + 1):
        request = urllib.request.Request(url, headers={"User-Agent": ua})
        try:
            with opener(request, timeout=30) as response:
                return response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < retries:
                wait = _wait_seconds(exc.headers)
                print(f"reddit-post: rate limited (429), waiting {wait}s", file=sys.stderr)
                sleep(wait)
                continue
            raise RedditError(f"HTTP {exc.code} from {url}") from exc
        except urllib.error.URLError as exc:
            hint = ""
            if "Tunnel connection failed" in str(exc.reason):
                hint = " (sandbox proxy? www.reddit.com may need allowlisting)"
            raise RedditError(f"could not reach {url}: {exc.reason}{hint}") from exc
    raise RedditError(f"gave up on {url}")  # unreachable; keeps the type checker honest


class _TextExtractor(HTMLParser):
    """HTML to plain text: paragraph breaks kept, links written as `text <url>`."""

    BREAKS = {"p", "br", "li", "div", "tr", "blockquote", "pre", "h1", "h2", "h3"}

    def __init__(self):
        super().__init__()
        self.parts: list[str] = []
        self._href: str | None = None
        self._link_text: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in self.BREAKS:
            self.parts.append("\n")
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._link_text = []

    def handle_endtag(self, tag):
        if tag == "a" and self._href:
            text = "".join(self._link_text).strip()
            if self._href.startswith("http") and text != self._href:
                self.parts.append(f" <{self._href}>")
            self._href = None

    def handle_data(self, data):
        self.parts.append(data)
        if self._href is not None:
            self._link_text.append(data)


def _to_text(raw_html: str) -> str:
    parser = _TextExtractor()
    parser.feed(raw_html)
    text = html.unescape("".join(parser.parts))
    text = re.sub(r"[ \t ]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _strip_footer(text: str) -> str:
    """Drop Reddit's trailing `submitted by /u/x [link] [comments]` line."""
    return re.sub(r"\n?\s*submitted by\b.*?\[comments\]\s*$", "", text, flags=re.S).strip()


def parse_feed(xml_text: str) -> dict:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise RedditError(f"response was not a valid Atom feed: {exc}") from exc
    entries = root.findall(f"{ATOM}entry")
    if not entries:
        raise RedditError("feed has no entries (deleted or removed post?)")

    category = root.find(f"{ATOM}category")
    subreddit = (category.get("term") if category is not None else None) or "?"

    def entry_fields(entry) -> dict:
        author = (entry.findtext(f"{ATOM}author/{ATOM}name") or "?").removeprefix("/u/")
        date = (entry.findtext(f"{ATOM}published") or entry.findtext(f"{ATOM}updated") or "")[:10]
        raw = entry.findtext(f"{ATOM}content") or ""
        return {"author": author, "date": date, "raw": raw, "text": _strip_footer(_to_text(raw))}

    first = entries[0]
    link_el = first.find(f"{ATOM}link")
    permalink = link_el.get("href") if link_el is not None else ""

    post = entry_fields(first)
    post["title"] = first.findtext(f"{ATOM}title") or ""
    outbound = re.search(r'<a href="([^"]+)">\[link\]</a>', post.pop("raw"))
    post["link"] = outbound.group(1) if outbound and "/comments/" not in outbound.group(1) else None

    comments = []
    for entry in entries[1:]:
        fields = entry_fields(entry)
        fields.pop("raw")
        comments.append(fields)
    return {"subreddit": subreddit, "permalink": permalink, "post": post, "comments": comments}


def format_output(feed: dict) -> str:
    post = feed["post"]
    lines = [
        f"r/{feed['subreddit']} -- u/{post['author']} -- {post['date']}",
        f"🔗 {feed['permalink']}",
        post["title"],
    ]
    if post["text"]:
        lines += ["", post["text"]]
    if post["link"]:
        lines.append(f"🔗 {post['link']}")
    lines += ["", f"--- comments ({len(feed['comments'])}) ---", ""]
    for comment in feed["comments"]:
        lines += [f"u/{comment['author']} -- {comment['date']}", comment["text"], ""]
    return "\n".join(lines)


def main(argv=None, fetcher=fetch, out=sys.stdout) -> int:
    parser = argparse.ArgumentParser(prog="reddit-post", description="Read a Reddit post and its comments via the Atom feed.")
    parser.add_argument("url", help="Reddit post URL (must contain /comments/<id>)")
    parser.add_argument("-n", type=int, default=10, help="number of comments to fetch (default 10)")
    parser.add_argument("--print-url", action="store_true", help="print the feed URL and exit")
    args = parser.parse_args(argv)
    try:
        url = feed_url(args.url, args.n)
        if args.print_url:
            print(url, file=out)
            return 0
        print(format_output(parse_feed(fetcher(url))), file=out)
        return 0
    except RedditError as exc:
        print(f"reddit-post: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

```bash
chmod +x plugins/second-brain/bin/reddit-post
```

- [ ] **Step 4: Run to verify it passes**

Run: `python3 plugins/second-brain/bin/tests/test_reddit_post.py`
Expected: all tests pass, output pristine. If a `FEED` fixture assertion fails because the real feed differs from the synthetic one, fix the parser against `.superpowers`-free evidence: the shape recorded in the design doc, not by loosening assertions.

- [ ] **Step 5: Live smoke test (needs network; run unsandboxed only after a shown sandbox denial)**

```bash
plugins/second-brain/bin/reddit-post -n 3 "https://www.reddit.com/r/commandline/comments/1wfk0ns/a_gopher_watches_your_typing_test/"
```

Expected: a header line `r/commandline -- u/mkhamat -- 2026-09-13`, the permalink, title, body, and 3 comments as plain text with no HTML tags or `submitted by` footer. A stderr line `rate limited (429), waiting Ns` followed by success is the expected backoff path. If Reddit answers 403, stop and report DONE_WITH_CONCERNS with the output.

- [ ] **Step 6: Commit**

```bash
git add plugins/second-brain/bin/reddit-post plugins/second-brain/bin/tests/test_reddit_post.py
git commit -m "feat(second-brain): add reddit-post reader for capture

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### move-yt-digest: bring yt-digest in and make it emit metadata

**Files:**
- Create: `plugins/second-brain/bin/yt-digest` (copied from `~/github.com/technicalpickles/dotfiles/bin/yt-digest`)
- Modify: `plugins/second-brain/bin/yt-digest` (add `select_metadata`, `write_metadata`, call sites)
- Test: `plugins/second-brain/bin/tests/test_yt_digest.py`

**Interfaces:**
- Produces: `select_metadata(info: dict) -> dict` returning exactly the keys `title`, `channel`, `published` (`YYYY-MM-DD` or `None`), `url`, `duration_seconds`; and `write_metadata(url: str, out_dir: Path) -> None` writing `out_dir/metadata.json` (skips if it exists; on any failure prints a `[metadata]` warning to stderr and continues). Both the `--transcript-only` and full paths call `write_metadata` when a URL is given. All existing flags and outputs unchanged.

- [ ] **Step 1: Copy the script in**

```bash
cp ~/github.com/technicalpickles/dotfiles/bin/yt-digest plugins/second-brain/bin/yt-digest
chmod +x plugins/second-brain/bin/yt-digest
```

- [ ] **Step 2: Write the failing test**

The script has heavy dependencies (`yt_dlp`, `claude_agent_sdk`, OCR, ffmpeg), so the test stubs those modules and loads the script by path; it never runs the pipeline.

`plugins/second-brain/bin/tests/test_yt_digest.py`:

```python
"""Unit tests for yt-digest's pure helpers. Heavy deps are stubbed; the
pipeline itself is not exercised here (it needs network, ffmpeg, and Claude)."""
import importlib.machinery
import importlib.util
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parent.parent / "yt-digest"


def load_module():
    for name in ("yt_dlp", "claude_agent_sdk", "imageio_ffmpeg", "wordfreq"):
        sys.modules.setdefault(name, mock.MagicMock())
    rapid = types.ModuleType("rapidocr_onnxruntime")
    rapid.RapidOCR = mock.MagicMock()
    sys.modules.setdefault("rapidocr_onnxruntime", rapid)
    loader = importlib.machinery.SourceFileLoader("yt_digest", str(SCRIPT))
    spec = importlib.util.spec_from_loader("yt_digest", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


yt = load_module()


class SelectMetadata(unittest.TestCase):
    def test_maps_and_formats_fields(self):
        info = {
            "title": "A Talk",
            "channel": "Some Channel",
            "upload_date": "20260102",
            "webpage_url": "https://www.youtube.com/watch?v=abc",
            "duration": 3725,
            "formats": ["ignored"],
        }
        self.assertEqual(
            yt.select_metadata(info),
            {
                "title": "A Talk",
                "channel": "Some Channel",
                "published": "2026-01-02",
                "url": "https://www.youtube.com/watch?v=abc",
                "duration_seconds": 3725,
            },
        )

    def test_missing_fields_become_none(self):
        self.assertEqual(
            yt.select_metadata({}),
            {"title": None, "channel": None, "published": None, "url": None, "duration_seconds": None},
        )

    def test_falls_back_to_uploader_when_no_channel(self):
        self.assertEqual(yt.select_metadata({"uploader": "Someone"})["channel"], "Someone")


class WriteMetadata(unittest.TestCase):
    def test_writes_metadata_json(self):
        info = {"title": "T", "channel": "C", "upload_date": "20260102", "webpage_url": "u", "duration": 1}
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            fake_ydl = mock.MagicMock()
            fake_ydl.__enter__.return_value.extract_info.return_value = info
            with mock.patch.object(yt.yt_dlp, "YoutubeDL", return_value=fake_ydl):
                yt.write_metadata("https://youtu.be/abc", out)
            self.assertEqual(json.loads((out / "metadata.json").read_text())["published"], "2026-01-02")

    def test_failure_warns_and_does_not_raise(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(yt.yt_dlp, "YoutubeDL", side_effect=RuntimeError("blocked")):
                yt.write_metadata("https://youtu.be/abc", Path(tmp))
            self.assertFalse((Path(tmp) / "metadata.json").exists())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run to verify it fails**

Run: `python3 plugins/second-brain/bin/tests/test_yt_digest.py`
Expected: FAIL with `AttributeError: module 'yt_digest' has no attribute 'select_metadata'`. If instead it fails at import time, a top-level import in the script needs another stub; add it to `load_module()` and re-run until the failure is the `AttributeError`.

- [ ] **Step 4: Implement the helpers**

In `plugins/second-brain/bin/yt-digest`, add directly above `def download_video(`:

```python
def select_metadata(info: dict) -> dict:
    upload_date = info.get("upload_date")
    published = f"{upload_date[0:4]}-{upload_date[4:6]}-{upload_date[6:8]}" if upload_date else None
    return {
        "title": info.get("title"),
        "channel": info.get("channel") or info.get("uploader"),
        "published": published,
        "url": info.get("webpage_url"),
        "duration_seconds": info.get("duration"),
    }


def write_metadata(url: str, out_dir: Path) -> None:
    """Write metadata.json (title, channel, published, url, duration). Best
    effort: a failure here must not abort the digest."""
    path = out_dir / "metadata.json"
    if path.exists():
        return
    try:
        with yt_dlp.YoutubeDL({"skip_download": True, "quiet": True, "no_warnings": True}) as ydl:
            info = ydl.extract_info(url, download=False)
        path.write_text(json.dumps(select_metadata(info), indent=2))
        print(f"[metadata] wrote {path}")
    except Exception as exc:  # noqa: BLE001 - metadata is optional
        print(f"[metadata] could not fetch metadata: {exc}", file=sys.stderr)
```

Ensure `import json` exists in the script's import block (add it next to the other stdlib imports if missing). Then call it in `async_main()`:

- In the `--transcript-only` branch, immediately after the `if not args.url: sys.exit(...)` check: `write_metadata(args.url, out_dir)`
- In the full path, immediately after the `if not args.skip_download:` block's `video_path = download_video(...)` line: `write_metadata(args.url, out_dir)` (inside the `if not args.skip_download:` block, so `args.url` is guaranteed).

Also add `metadata.json` to `_describe_output_file` with the description `"video title/channel/date/url/duration"`, following that function's existing pattern.

- [ ] **Step 5: Run to verify it passes**

Run: `python3 plugins/second-brain/bin/tests/test_yt_digest.py`
Expected: 5 tests pass.

- [ ] **Step 6: Smoke-check the CLI still parses**

Run: `python3 -c "import ast,sys; ast.parse(open('plugins/second-brain/bin/yt-digest').read())"`
Expected: no output. (A live end-to-end run needs network and a logged-in `claude`; do it once by hand: `plugins/second-brain/bin/yt-digest --transcript-only --out-dir "$TMPDIR/ytd-smoke" "<a short public video URL>"` and confirm `metadata.json` and `transcript.md` appear.)

- [ ] **Step 7: Commit**

```bash
git add plugins/second-brain/bin/yt-digest plugins/second-brain/bin/tests/test_yt_digest.py
git commit -m "feat(second-brain): ship yt-digest in the plugin bin, emit metadata.json

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### site-playbooks: write the four playbooks and the frontmatter extras

**Files:**
- Create: `plugins/second-brain/skills/capture/references/sites/web.md`
- Create: `plugins/second-brain/skills/capture/references/sites/x.md`
- Create: `plugins/second-brain/skills/capture/references/sites/youtube.md`
- Create: `plugins/second-brain/skills/capture/references/sites/reddit.md`
- Modify: `plugins/second-brain/skills/capture/references/note-format.md` (add "Site fields" section)

**Interfaces:**
- Consumes: `xtweet`, `reddit-post`, `yt-digest` (+ `metadata.json`) from the tasks above; invocation spelling per `BIN_ON_PATH`. The text below uses bare command names (`BIN_ON_PATH = yes`). If the probe recorded `no`, replace each bare `xtweet`/`yt-digest`/`reddit-post` with `"${CLAUDE_PLUGIN_ROOT}/bin/<name>"` throughout these files.
- Produces: file paths that `capture-dispatch` links to: `references/sites/{web,x,youtube,reddit}.md`.

- [ ] **Step 0: Check the field names against the vault's vocabulary**

```bash
grep -n -iE 'platform|author|channel|subreddit|published' ~/Vaults/pickled-knowledge/CLAUDE.md
```

If the vault's `CLAUDE.md` already names equivalents (e.g. `creator` instead of `author`), use the vault's names in every playbook and in the "Site fields" table below, and note the substitution in the design doc. No matches means the names below stand.

- [ ] **Step 1: Write `web.md`**

````markdown
# Web pages (default)

Used for any host without its own playbook.

## Read

- Preferred: `mcp__lightpanda__markdown {url}`
- Fallback: `WebFetch`

## Frontmatter extras

None. `source` is the URL.

## Failure mode

If neither tool returns the page (login wall, 4xx/5xx, empty body), stop and say so. Do not write
a note from the search snippet, the title, or background knowledge.
````

- [ ] **Step 2: Write `x.md`**

````markdown
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
````

- [ ] **Step 3: Write `youtube.md`**

````markdown
# YouTube

Hosts: `youtube.com`, `www.youtube.com`, `m.youtube.com`, `youtu.be`.

## Read

Default is the full pull: video, spoken transcript, and on-screen text (slides, infographics)
merged into one chronological document. Do not ask the user which mode.

```bash
OUT="$TMPDIR/yt-digest/<video-id>"
yt-digest --out-dir "$OUT" "<url>"
```

Then `Read` `$OUT/full_context.md` (transcript + on-screen text) and `$OUT/metadata.json`.

Fall back to `--transcript-only` (reads `$OUT/transcript.md`) only with a concrete reason, and say
which reason in your reply:

- the video is very long, so download and OCR cost outweighs the value
- the download fails or is blocked
- the content is evidently audio-only (podcast, talk over a static frame)

A talking head alone is not a reason: they still show slides, demos and screens.

**Requires** `uv` and a logged-in `claude` CLI (`yt-digest` runs as `uv run --script`; first run
downloads its dependencies). Use `$TMPDIR`, never the vault or the repo, for `--out-dir`.

## Frontmatter extras

Beside `source`, from `$OUT/metadata.json`:

```yaml
platform: youtube
channel: Some Channel
published: 2026-01-02
```

If `metadata.json` is missing, omit `channel` and `published` rather than guessing.

## Failure mode

If `yt-digest` fails outright (not just the full-mode fallback above), stop and report the error
output. Do not write a note from the video title, the description, or someone else's summary.
````

- [ ] **Step 4: Write `reddit.md`**

````markdown
# Reddit

Hosts: `reddit.com`, `www.reddit.com`, `old.reddit.com`, `redd.it` (short links: resolve to the
full `/comments/<id>` URL first if the user gave one).

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
````

- [ ] **Step 5: Add "Site fields" to `note-format.md`**

Insert after the "Reconciling with what sb scaffolds" section, before "## Body":

````markdown
### Site fields

When the source came from a site with its own playbook, add the fields that playbook names
beside `source`. They describe the source, not the note, and stay out of the body:

| Site | Fields |
|------|--------|
| X | `platform: x`, `author: "@handle"`, `published` |
| YouTube | `platform: youtube`, `channel`, `published` |
| Reddit | `platform: reddit`, `subreddit`, `author`, `published` |

`published` is `YYYY-MM-DD`. See [sites/](sites/) for where each value comes from. If the vault's
own `CLAUDE.md` names different fields for the same idea, use the vault's.
````

- [ ] **Step 6: Commit**

```bash
git add plugins/second-brain/skills/capture/references/sites plugins/second-brain/skills/capture/references/note-format.md
git commit -m "feat(second-brain): add per-site capture playbooks and frontmatter fields

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### capture-dispatch: wire the playbooks into capture

**Files:**
- Modify: `plugins/second-brain/skills/capture/SKILL.md` (frontmatter `allowed-tools`, Step 2, Step 3 note)
- Modify: `plugins/second-brain/README.md:127`

**Interfaces:**
- Consumes: `references/sites/{web,x,youtube,reddit}.md`; script invocation spelling per `BIN_ON_PATH`. Below is the `yes` form. If `no`, use `Bash(${CLAUDE_PLUGIN_ROOT}/bin/xtweet:*)` etc. in `allowed-tools`.

- [ ] **Step 1: Allow the scripts in `allowed-tools`**

In the SKILL.md frontmatter, after `- Bash(npx @techpickles/sb:*)`, add:

```yaml
  - Bash(xtweet:*)
  - Bash(reddit-post:*)
  - Bash(yt-digest:*)
```

The skill-scoped `PreToolUse` hook only acts on `sb` invocations (see
`hooks/tests/check-sb-before-call.bats`, "ignores Bash calls that aren't sb invocations"), so it
does not need changing.

- [ ] **Step 2: Replace the Step 2 source table**

Replace the whole table under "## Step 2: Read the actual primary source" (through the row for Slack) with:

````markdown
Match the source, then follow its playbook. For a URL, match on the host:

| Source | Playbook / tool |
|--------|-----------------|
| `x.com`, `twitter.com` | [references/sites/x.md](references/sites/x.md) |
| `youtube.com`, `youtu.be` | [references/sites/youtube.md](references/sites/youtube.md) |
| `reddit.com`, `redd.it` | [references/sites/reddit.md](references/sites/reddit.md) |
| Any other URL | [references/sites/web.md](references/sites/web.md) |
| PDF or local file | `Read` |
| Notion page | `mcp__notiongusto__notion-fetch` |
| Slack thread | the `slack` skill |

Each playbook also names frontmatter fields to add beside `source` in Step 3; carry them into the
note. New site: add `references/sites/<site>.md` and one row here.
````

Keep the two paragraphs after the table ("**If you cannot reach the source...**") exactly as they are.

- [ ] **Step 3: Point Step 3 at the site fields**

In "## Step 3: Create the note through sb", after the sentence "Then write the body at the returned path with `Write`/`Edit`.", add:

```markdown
Add any site fields from the playbook to the frontmatter (see
[references/note-format.md](references/note-format.md#site-fields)).
```

- [ ] **Step 4: Update the plugin README line**

At `plugins/second-brain/README.md:127`, change
`2. **Read the primary source** (lightpanda / WebFetch / xtweet / Read / Notion), never a snippet`
to
`2. **Read the primary source** through its site playbook (X via xtweet, YouTube via yt-digest, Reddit via reddit-post, other pages via lightpanda / WebFetch; Read / Notion for files and pages), never a snippet`

Also add a short "Bundled tools" subsection to the README near the capture section:

```markdown
### Bundled tools

`bin/` ships the readers `capture` uses. Each has its own requirements:

| Tool | Needs |
|------|-------|
| `xtweet` | `xurl` authenticated for the X API, `jq` |
| `reddit-post` | `uv`; `www.reddit.com` reachable from the shell |
| `yt-digest` | `uv`, a logged-in `claude` CLI |
```

- [ ] **Step 5: Verify and commit**

Run: `grep -n 'references/sites' plugins/second-brain/skills/capture/SKILL.md` (expect 4 matches) and `for f in web x youtube reddit; do test -f plugins/second-brain/skills/capture/references/sites/$f.md && echo ok $f; done` (expect 4 `ok` lines).

```bash
git add plugins/second-brain/skills/capture/SKILL.md plugins/second-brain/README.md
git commit -m "feat(second-brain): dispatch capture reads through site playbooks

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### pointer-and-evals: keep bare links triggering capture

The eval README measured that the vault CLAUDE.md pointer, not the skill description, is what makes `capture` fire, and that a pointer only catches intents it names. So the pointer must name these link types.

**Files:**
- Modify: `plugins/second-brain/templates/vault-claude-md.md` (pointer bullets)
- Modify: `plugins/second-brain/skills/capture/evals/trigger-evals.json` (new queries)

**Interfaces:**
- Consumes: the running trigger harness, `skills/capture/evals/trigger_eval.py`.

- [ ] **Step 1: Add eval queries first**

Append these objects to the array in `trigger-evals.json`:

```json
  {
    "query": "https://www.youtube.com/watch?v=dQw4w9WgXcQ make a note for this",
    "should_trigger": true,
    "note": "site playbook: bare YouTube link with note intent"
  },
  {
    "query": "read this reddit thread and put together an atomic note https://www.reddit.com/r/commandline/comments/abc123/a_neat_tool/",
    "should_trigger": true,
    "note": "site playbook: Reddit permalink with note intent"
  },
  {
    "query": "https://x.com/karpathy/status/1917920338492977296 capture this",
    "should_trigger": true,
    "note": "site playbook: bare tweet link"
  },
  {
    "query": "watch https://www.youtube.com/watch?v=dQw4w9WgXcQ and tell me if the demo at the end is worth trying, dont save anything",
    "should_trigger": false,
    "note": "near-miss: YouTube link, but a question about the video, not a note"
  }
```

These are synthetic (the rest of the file is verbatim from real sessions); the `note` fields say so. Replace them with verbatim prompts as real ones accumulate.

- [ ] **Step 2: Run the baseline against the current pointer**

Build a throwaway vault-shaped dir (never the real vault) and run, from `plugins/second-brain/skills/capture/evals/`:

```bash
VAULT_DIR="$(mktemp -d)" && mkdir -p "$VAULT_DIR/.obsidian" && cp ../../../templates/vault-claude-md.md "$VAULT_DIR/CLAUDE.md"
./trigger_eval.py --eval-set trigger-evals.json --plugin-src ../../.. \
  --skill capture --namespace second-brain --cwd "$VAULT_DIR" \
  --runs 3 --workers 6 --turns 2 --out "results/$(date +%F)-site-baseline.json"
```

Expected: record recall on the three new positives. This is the "before" number.

- [ ] **Step 3: Widen the pointer**

In `templates/vault-claude-md.md`, change the "Creating one from a source" bullet to:

```markdown
- **Creating one from a source** - "read \<url/pdf/tweet/video/reddit thread\> and make a note for it", "make an atomic note for X", or a bare X, YouTube or Reddit link handed over with intent to write it up
```

- [ ] **Step 4: Re-run and compare**

Copy the edited template over `"$VAULT_DIR/CLAUDE.md"` and re-run Step 2's command with `--out "results/$(date +%F)-site-pointer.json"`.
Expected: the new positives at least as high as baseline, the existing 10 positives and 11 negatives unchanged (specificity 100%). If any existing query regresses, revert the pointer change and report before continuing.

- [ ] **Step 5: Note results in the evals README and commit**

Add a short "Site-specific links (2026-09-19)" section to `skills/capture/evals/README.md` with the baseline vs widened recall for the three new positives and the specificity result, and that the queries are synthetic.

```bash
git add plugins/second-brain/templates/vault-claude-md.md plugins/second-brain/skills/capture/evals
git commit -m "feat(second-brain): name X/YouTube/Reddit links in the capture pointer

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### spec-close-out: sync the spec and file the followups

**Files:**
- Modify: `plugins/second-brain/docs/plans/2026-09-19-capture-site-specific-design.md`

- [ ] **Step 1: Update the spec to match what shipped**

- Status line: change to `Status: implemented (see plan).`
- Scripts section: add that `yt-digest` now writes `metadata.json` (title, channel, published, url, duration) because the frontmatter needs it, and that `reddit-post` is `curl` + `jq` on the unauthenticated `.json` endpoint.
- Add a "Followups" list: `fetch-source` dispatcher (deferred option C), and dotfiles cleanup.

- [ ] **Step 2: File the dotfiles followup in taskwarrior**

Per the user's global rule, capture it as a task, not a note. Check the right project first:

```bash
task projects | head -20
task add "dotfiles: replace bin/xtweet and bin/yt-digest with symlinks to second-brain plugin bin; update bin/CLAUDE.md and claude/CLAUDE.md pointers" project:<dotfiles project from list above>
```

Do not cite the task's integer ID in any commit or doc; if a reference is needed, use its UUID (`task <id> _uuid`).

- [ ] **Step 3: Commit**

```bash
git add plugins/second-brain/docs/plans/2026-09-19-capture-site-specific-design.md
git commit -m "docs(second-brain): sync site-specific capture spec with implementation

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### version-bump: bump and verify

**Files:**
- Modify: `.claude-plugin/marketplace.json`, root `README.md` (via script)

- [ ] **Step 1: Run the repo-wide tests once more**

```bash
bats plugins/second-brain/bin/tests plugins/second-brain/hooks/tests plugins/second-brain/scripts/tests
python3 plugins/second-brain/bin/tests/test_yt_digest.py
./scripts/check-commit-scope.sh 2>&1 | tail -5
```

Expected: all pass; scope check clean.

- [ ] **Step 2: Bump**

```bash
./scripts/bump-version.sh --auto
git diff --stat
```

Expected: `second-brain` goes to `1.15.0` (a `feat` since the last bump) in `.claude-plugin/marketplace.json`; README plugin table unchanged or regenerated.

- [ ] **Step 3: Commit**

```bash
git add -A .claude-plugin README.md
git commit -m "chore(second-brain): bump version to 1.15.0

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

Use the actual version the script wrote if it differs from `1.15.0`.
