"""Tests for reddit-post. The Atom fixture is synthetic but follows the shape
observed from a real post feed on 2026-09-19 (see the design doc)."""
import importlib.machinery
import importlib.util
import http.client
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
    def setUp(self):
        # fetch() reports 429 backoff on stderr; keep test output pristine
        patcher = mock.patch.object(sys, "stderr", io.StringIO())
        patcher.start()
        self.addCleanup(patcher.stop)

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


class FooterStripping(unittest.TestCase):
    FOOTER = "submitted by /u/a [link] [comments]"

    def test_mid_text_submitted_by_is_preserved(self):
        text = "Body: my post was submitted by my boss.\n\nImportant second para.\n\n" + self.FOOTER
        self.assertEqual(
            rp._strip_footer(text),
            "Body: my post was submitted by my boss.\n\nImportant second para.",
        )

    def test_submitted_by_without_footer_is_untouched(self):
        text = "It was submitted by my boss.\n\nMore text."
        self.assertEqual(rp._strip_footer(text), text)

    def test_footer_with_trailing_url_is_removed(self):
        text = "Hi\n\nsubmitted by /u/a (https://x/u/a) [link] (https://y) [comments] (https://z)"
        self.assertEqual(rp._strip_footer(text), "Hi")


class ReadFailures(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.object(sys, "stderr", io.StringIO())
        self.err = patcher.start()
        self.addCleanup(patcher.stop)

    def opener_raising(self, exc=None, body=None):
        class Resp(FakeResponse):
            def read(self_inner):
                if exc:
                    raise exc
                return body

        def opener(req, timeout):
            return Resp("")

        return opener

    def cases(self):
        return [
            self.opener_raising(TimeoutError("timed out")),
            self.opener_raising(http.client.IncompleteRead(b"")),
            self.opener_raising(ConnectionResetError("reset")),
            self.opener_raising(http.client.RemoteDisconnected("closed")),
        ]

    def test_read_failures_become_reddit_error(self):
        for opener in self.cases():
            with self.assertRaises(rp.RedditError):
                rp.fetch("https://x", opener=opener, sleep=lambda s: None)

    def test_bad_utf8_does_not_raise(self):
        opener = self.opener_raising(body=b"ok \xff bytes")
        self.assertIn("ok", rp.fetch("https://x", opener=opener))

    def test_main_exits_1_with_message_and_no_traceback(self):
        for opener in self.cases():
            self.err.truncate(0)
            self.err.seek(0)
            fetcher = lambda url, o=opener: rp.fetch(url, opener=o, sleep=lambda s: None)
            code = rp.main([PERMALINK], fetcher=fetcher, out=io.StringIO())
            self.assertEqual(code, 1)
            self.assertIn("reddit-post:", self.err.getvalue())
            self.assertNotIn("Traceback", self.err.getvalue())


class FeedUrlEdges(unittest.TestCase):
    def test_scheme_is_case_insensitive(self):
        self.assertEqual(
            rp.feed_url("HTTPS://Reddit.com/r/x/comments/abc123/t/", 5),
            "https://www.reddit.com/r/x/comments/abc123/t.rss?limit=5",
        )

    def test_trailing_rss_is_not_doubled(self):
        self.assertEqual(
            rp.feed_url("https://www.reddit.com/r/x/comments/abc123/t.rss", 5),
            "https://www.reddit.com/r/x/comments/abc123/t.rss?limit=5",
        )

    def test_comment_permalink_normalizes_to_post_feed(self):
        self.assertEqual(
            rp.feed_url("https://www.reddit.com/r/x/comments/abc123/t/c1abc/", 5),
            "https://www.reddit.com/r/x/comments/abc123/t.rss?limit=5",
        )

    def test_bare_comments_id_still_works(self):
        self.assertEqual(
            rp.feed_url("https://www.reddit.com/comments/abc123", 5),
            "https://www.reddit.com/comments/abc123.rss?limit=5",
        )

    def test_hostile_hosts_are_rebuilt_on_reddit(self):
        for hostile in (
            "https://evil.com/r/x/comments/abc/t/",
            "https://www.reddit.com@evil.com/r/x/comments/abc/t/",
            "//evil.com/r/x/comments/abc/t/",
        ):
            with self.subTest(url=hostile):
                self.assertTrue(rp.feed_url(hostile, 10).startswith("https://www.reddit.com/"))


class CountValidation(unittest.TestCase):
    def test_non_positive_counts_are_rejected(self):
        for bad in ("0", "-1"):
            with mock.patch.object(sys, "stderr", io.StringIO()):
                with self.assertRaises(SystemExit) as ctx:
                    rp.main(["-n", bad, "--print-url", PERMALINK], fetcher=None, out=io.StringIO())
            self.assertEqual(ctx.exception.code, 2)


class EmptyTextLinks(unittest.TestCase):
    def test_image_only_link_leaves_no_stray_url(self):
        html_in = '<a href="https://www.reddit.com/r/x/comments/abc/t/"><img src="a.png"/></a><div><p>hi</p></div>'
        self.assertEqual(rp._to_text(html_in), "hi")


if __name__ == "__main__":
    unittest.main()
