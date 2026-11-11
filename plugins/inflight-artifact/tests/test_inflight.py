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


class SessionsTest(unittest.TestCase):
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
