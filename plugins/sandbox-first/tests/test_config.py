import json

import pytest

from sandbox_first.config import load_skip_list_from_file


class TestLoadSkipListFromFile:
    def test_valid_config(self, tmp_path):
        """Reads skip_failure_requirement from a valid JSON file."""
        config = tmp_path / "sandbox-first.json"
        config.write_text(json.dumps({"skip_failure_requirement": ["docker", "bk"]}))
        assert load_skip_list_from_file(str(config)) == ["docker", "bk"]

    def test_missing_file(self):
        """Missing file returns empty list."""
        assert load_skip_list_from_file("/nonexistent/sandbox-first.json") == []

    def test_malformed_json(self, tmp_path):
        """Malformed JSON returns empty list."""
        config = tmp_path / "sandbox-first.json"
        config.write_text("not json {{{")
        assert load_skip_list_from_file(str(config)) == []

    def test_missing_key(self, tmp_path):
        """JSON without skip_failure_requirement returns empty list."""
        config = tmp_path / "sandbox-first.json"
        config.write_text(json.dumps({"other_key": "value"}))
        assert load_skip_list_from_file(str(config)) == []

    def test_wrong_type_for_key(self, tmp_path):
        """Non-array skip_failure_requirement returns empty list."""
        config = tmp_path / "sandbox-first.json"
        config.write_text(json.dumps({"skip_failure_requirement": "not-an-array"}))
        assert load_skip_list_from_file(str(config)) == []

    def test_filters_non_strings(self, tmp_path):
        """Non-string values in the array are filtered out."""
        config = tmp_path / "sandbox-first.json"
        config.write_text(json.dumps({"skip_failure_requirement": ["docker", 42, None, "bk"]}))
        assert load_skip_list_from_file(str(config)) == ["docker", "bk"]

    def test_extra_keys_ignored(self, tmp_path):
        """Extra keys in the config are silently ignored."""
        config = tmp_path / "sandbox-first.json"
        config.write_text(json.dumps({
            "skip_failure_requirement": ["docker"],
            "future_key": True,
        }))
        assert load_skip_list_from_file(str(config)) == ["docker"]


from sandbox_first.config import load_merged_skip_list


class TestLoadMergedSkipList:
    def test_both_files_present(self, tmp_path):
        """Union of user and project lists."""
        user = tmp_path / "user" / "sandbox-first.json"
        user.parent.mkdir()
        user.write_text(json.dumps({"skip_failure_requirement": ["docker"]}))

        project = tmp_path / "project" / "sandbox-first.json"
        project.parent.mkdir()
        project.write_text(json.dumps({"skip_failure_requirement": ["bk"]}))

        result = load_merged_skip_list(str(user), str(project))
        assert sorted(result) == ["bk", "docker"]

    def test_duplicates_deduplicated(self, tmp_path):
        """Same entry in both files appears once."""
        user = tmp_path / "user" / "sandbox-first.json"
        user.parent.mkdir()
        user.write_text(json.dumps({"skip_failure_requirement": ["docker"]}))

        project = tmp_path / "project" / "sandbox-first.json"
        project.parent.mkdir()
        project.write_text(json.dumps({"skip_failure_requirement": ["docker", "bk"]}))

        result = load_merged_skip_list(str(user), str(project))
        assert sorted(result) == ["bk", "docker"]

    def test_only_user_file(self, tmp_path):
        """Only user config exists."""
        user = tmp_path / "sandbox-first.json"
        user.write_text(json.dumps({"skip_failure_requirement": ["docker"]}))

        result = load_merged_skip_list(str(user), "/nonexistent/sandbox-first.json")
        assert result == ["docker"]

    def test_only_project_file(self, tmp_path):
        """Only project config exists."""
        project = tmp_path / "sandbox-first.json"
        project.write_text(json.dumps({"skip_failure_requirement": ["bk"]}))

        result = load_merged_skip_list("/nonexistent/sandbox-first.json", str(project))
        assert result == ["bk"]

    def test_neither_file(self):
        """No config files returns empty list."""
        result = load_merged_skip_list("/nonexistent/a.json", "/nonexistent/b.json")
        assert result == []
