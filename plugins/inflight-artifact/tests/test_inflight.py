import json, os, shutil, subprocess, sys, tempfile, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
EXAMPLE_CONFIG = os.path.join(ROOT, "examples", "config")
FIXTURE = os.path.join(ROOT, "tests", "fixtures", "facts.json")


def run(script, *args, check=True):
    p = subprocess.run([sys.executable, os.path.join(SCRIPTS, script), *args], capture_output=True, text=True)
    if check and p.returncode != 0:
        raise AssertionError(f"{script} failed: {p.stderr or p.stdout}")
    return p


class RenderTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.state = os.path.join(self.tmp, "state")
        os.makedirs(self.state)
        shutil.copy(FIXTURE, os.path.join(self.state, "facts.json"))
        self.out = os.path.join(self.tmp, "out.html")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def render(self, config=EXAMPLE_CONFIG):
        run("render.py", "example", "--config-dir", config, "--state-dir", self.state, "--out", self.out)
        with open(self.out) as f:
            return f.read()

    def test_tabs_and_pr_links(self):
        html = self.render()
        for tab in ("#overview", "#happened", "#next"):
            self.assertIn(f'href="{tab}"', html)
        self.assertIn('href="https://github.com/acme/widgets/pull/12"', html)

    def test_ci_chip_links_to_the_build(self):
        html = self.render()
        self.assertIn('href="https://ci.example/builds/2"', html)
        self.assertIn("CI fail", html)
        self.assertIn("no CI", html)

    def test_merged_pr_links_to_its_checks(self):
        self.assertIn("/pull/11/checks", self.render())

    def test_unmatched_pr_is_unsorted_not_dropped(self):
        html = self.render()
        self.assertIn("Unsorted", html)
        self.assertIn("Unrelated tweak", html)

    def test_exclude_pattern_hides_a_repo(self):
        self.assertNotIn("Excluded by pattern", self.render())

    def test_ignored_section_is_collapsed(self):
        html = self.render()
        self.assertIn("Collapsed: Old, to look at later", html)

    def test_needs_item_drops_when_its_pr_is_no_longer_open(self):
        cfg = os.path.join(self.tmp, "cfg")
        shutil.copytree(EXAMPLE_CONFIG, cfg)
        path = os.path.join(self.state, "facts.json")
        with open(path) as f: facts = json.load(f)
        facts["prs"] = [p for p in facts["prs"] if p["n"] != 12]
        with open(path, "w") as f: json.dump(facts, f)
        html = self.render(cfg)
        self.assertNotIn("Review the open widgets PR.", html)
        self.assertIn("Nothing is waiting on you", html)

    def test_preview_is_titled_and_styled_differently_from_live(self):
        live = self.render()
        run("render.py", "example", "--config-dir", EXAMPLE_CONFIG, "--state-dir", self.state, "--out", self.out, "--preview")
        with open(self.out) as f: preview = f.read()
        self.assertIn("<title>PREVIEW: In-Flight Review (scratch)</title>", preview)
        self.assertIn('class="preview"', preview)
        self.assertIn("preview-bar", preview)
        self.assertIn("<title>In-Flight Review</title>", live)
        self.assertNotIn('class="preview"', live)

    def test_needs_item_shows_while_its_pr_is_open(self):
        self.assertIn("Review the open widgets PR.", self.render())

    def test_rows_marked_you_appear_under_needs(self):
        cfg = os.path.join(self.tmp, "cfg")
        shutil.copytree(EXAMPLE_CONFIG, cfg)
        page = os.path.join(cfg, "pages", "example.json")
        with open(page) as f: data = json.load(f)
        data["threads"][0]["next"] = [{"text": "Decide on the cutover", "you": True}]
        with open(page, "w") as f: json.dump(data, f)
        self.assertIn("Decide on the cutover", self.render(cfg))


class PageFeaturesTest(unittest.TestCase):
    """Features a hand-built page needs: scope, row-claimed tasks, fragments, extra tabs, popups, a merged ledger."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.state = os.path.join(self.tmp, "state")
        os.makedirs(self.state)
        shutil.copy(FIXTURE, os.path.join(self.state, "facts.json"))
        self.cfg = os.path.join(self.tmp, "cfg")
        os.makedirs(os.path.join(self.cfg, "pages", "p"))
        self.page = {"id": "p", "title": "P", "lede": "Lede with <code>markup</code>.", "threads": [
            {"id": "cache", "title": "Cache", "status": "now", "goal": "Faster widgets.",
             "next": [{"text": "Tune <code>ttl</code>", "task": "aaaa1111", "kind": "perf", "tone": "warn"},
                      {"text": "Sign off on the cache", "you": True}],
             "then": [{"text": "Back up v1", "task": "bbbb2222"}],
             "parked": [{"text": "Someday: rewrite it"}]}]}

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def render(self, *extra):
        with open(os.path.join(self.cfg, "pages", "p.json"), "w") as f: json.dump(self.page, f)
        out = os.path.join(self.tmp, "out.html")
        p = run("render.py", "p", "--config-dir", self.cfg, "--state-dir", self.state, "--out", out, *extra)
        with open(out) as f: return f.read(), p.stdout

    def write(self, name, text):
        with open(os.path.join(self.cfg, "pages", "p", name), "w") as f: f.write(text)

    def popup_tasks(self, html):
        blob = html.split('<script id="inflight-data" type="application/json">')[1].split("</script>")[0]
        return {t["uuid"][:8]: t for t in json.loads(blob)["tasks"]}

    def test_include_rule_needs_every_key_and_paths_match_files(self):
        self.page["include"] = {"prs": [{"repos": ["widgets"]}, {"repos": ["infra"], "pr_paths": "^services/db/"}], "tasks": [{"task_projects": ["widgets"]}]}
        html, _ = self.render()
        self.assertIn("Migrate database to v2", html)
        self.assertNotIn("Unrelated tweak", html)
        self.assertNotIn("Water the plants", html)
        self.page["include"]["prs"][1]["pr_paths"] = "^charts/"
        self.assertNotIn("Migrate database to v2", self.render()[0])

    def test_a_row_claims_its_task_even_outside_the_scope(self):
        self.page["include"] = {"tasks": [{"task_projects": ["widgets"]}]}
        html, out = self.render()
        self.assertIn("Back up v1", html)
        self.assertIn("unsorted tasks: 0", out)

    def test_config_prose_is_html_and_fact_text_is_escaped(self):
        html, _ = self.render()
        self.assertIn("Lede with <code>markup</code>.", html)
        self.assertIn("Tune <code>ttl</code>", html)

    def test_now_sections_feed_up_next_and_you_rows_feed_needs(self):
        html, _ = self.render()
        overview = html.split('id="v-overview"')[1].split('id="v-happened"')[0]
        up = overview.split("Up next")[1].split("Sections")[0]
        self.assertIn("Tune <code>ttl</code>", up)
        self.assertIn("Sign off on the cache", overview.split("Needs you")[1].split("Up next")[0])
        self.assertNotIn("Sign off on the cache", up)

    def test_then_and_parked_rows_show_on_whats_next(self):
        nxt = self.render()[0].split('id="v-next"')[1]
        self.assertIn("<h4>Then</h4>", nxt)
        self.assertIn("Parked (1)", nxt)
        self.assertIn("Someday: rewrite it", nxt)

    def test_fragments_add_overview_blocks_tabs_and_css(self):
        self.write("today.html", "<h2>Service status</h2>")
        self.write("caps.html", '<ul><li class="task" data-t="dddd4444"><div>Water</div></li></ul>')
        self.write("page.css", ".capgrid{gap:3px}")
        self.page.update(overview_html=["today.html"], tabs=[{"id": "caps", "title": "Capabilities", "file": "caps.html"}], css="page.css")
        html, _ = self.render()
        self.assertIn('href="#caps"', html)
        self.assertIn('<div id="v-caps" hidden>', html)
        self.assertIn("<h2>Service status</h2>", html.split('id="v-overview"')[1].split('id="v-happened"')[0])
        self.assertIn(".capgrid{gap:3px}", html)
        self.assertIn("dddd4444", self.popup_tasks(html))

    def test_a_task_shown_in_a_fragment_is_not_unsorted(self):
        self.page["include"] = {"tasks": [{"task_projects": ["garden"]}]}
        self.assertIn("unsorted tasks: 1", self.render()[1])
        self.write("caps.html", '<li class="task" data-t="dddd4444">Water</li>')
        self.page["tabs"] = [{"id": "caps", "title": "Caps", "file": "caps.html"}]
        self.assertIn("unsorted tasks: 0", self.render()[1])
        with open(os.path.join(self.state, "p.unsorted.json")) as f: self.assertEqual(json.load(f)["tasks"], [])

    def test_popups_carry_annotations_and_finished_refs_are_reported(self):
        self.page["threads"][0]["next"].append({"text": "Old ADR", "task": "cccc3333"})
        html, out = self.render()
        tasks = self.popup_tasks(html)
        self.assertEqual(tasks["aaaa1111"]["annotations"], ["2026-01-10: hit rate is 40%"])
        self.assertNotIn("cccc3333", tasks)
        self.assertNotIn("Old ADR", html)
        self.write("caps.html", '<li class="task" data-t="cccc3333">x</li>')
        self.page["tabs"] = [{"id": "caps", "title": "Caps", "file": "caps.html"}]
        self.assertIn("no longer pending, drop these rows: cccc3333", self.render()[1])

    def test_history_filters_group_by_repo_and_auto_events_can_be_off(self):
        self.page.update(filters=[{"id": "w", "label": "widgets", "repos": ["widgets"]}], auto_events=False,
                         history=[{"date": "2026-01-14", "group": "w", "text": "Shipped <a href=\"#x\">the cache</a>"}])
        happened = self.render()[0].split('id="v-happened"')[1].split('id="v-next"')[0]
        self.assertIn('data-f="w">widgets</button>', happened)
        self.assertIn('<div class="row ev" data-g="w">', happened)
        self.assertNotIn("merged · checks", happened)

    def test_shipped_by_repo_reads_the_ledger_beyond_the_window(self):
        with open(os.path.join(self.state, "ledger.json"), "w") as f:
            json.dump([{"repo": "acme/widgets", "short": "widgets", "n": 2, "title": "Ancient fix", "url": "https://github.com/acme/widgets/pull/2", "date": "2025-06-01"}], f)
        happened = self.render()[0].split('id="v-happened"')[1].split('id="v-next"')[0]
        shipped = happened.split("Shipped, by repo")[1]
        self.assertIn("Ancient fix", shipped)
        self.assertIn("Fix widget leak", shipped)
        self.assertNotIn("Ancient fix", happened.split("Shipped, by repo")[0])

    def test_session_tasks_badge_rows_and_reach_the_popup(self):
        with open(os.path.join(self.state, "sessions.json"), "w") as f:
            json.dump([{"id": "local_1", "title": "Tuning", "state": "running", "page": "p", "tasks": ["aaaa1111"], "updated": "2999-01-01T00:00"}], f)
        html, _ = self.render()
        self.assertIn("in session", html)
        blob = json.loads(html.split('<script id="inflight-data" type="application/json">')[1].split("</script>")[0])
        self.assertEqual(blob["sessions"][0]["tasks"], ["aaaa1111"])


class SessionFieldsTest(unittest.TestCase):
    def test_tasks_and_repo_are_stored(self):
        with tempfile.TemporaryDirectory() as d:
            run("sessions.py", "upsert", "--state-dir", d, "--id", "s1", "--tasks", "aaaa1111, bbbb2222", "--repo", "widgets")
            with open(os.path.join(d, "sessions.json")) as f: row = json.load(f)[0]
            self.assertEqual((row["tasks"], row["repo"]), (["aaaa1111", "bbbb2222"], "widgets"))

    def test_upsert_merges_fields_and_remove_deletes(self):
        with tempfile.TemporaryDirectory() as d:
            run("sessions.py", "upsert", "--state-dir", d, "--id", "s1", "--title", "First", "--state", "running")
            run("sessions.py", "upsert", "--state-dir", d, "--id", "s1", "--note", "later")
            with open(os.path.join(d, "sessions.json")) as f: rows = json.load(f)
            self.assertEqual(len(rows), 1)
            self.assertEqual((rows[0]["title"], rows[0]["state"], rows[0]["note"]), ("First", "running", "later"))
            run("sessions.py", "remove", "--state-dir", d, "--id", "s1")
            with open(os.path.join(d, "sessions.json")) as f: self.assertEqual(json.load(f), [])


class GatherArgsTest(unittest.TestCase):
    def test_missing_github_user_fails_before_any_network_call(self):
        with tempfile.TemporaryDirectory() as d:
            p = run("gather.py", "--config-dir", d, "--state-dir", d, check=False)
            self.assertNotEqual(p.returncode, 0)
            self.assertIn("no GitHub user", p.stderr + p.stdout)


if __name__ == "__main__":
    unittest.main()
