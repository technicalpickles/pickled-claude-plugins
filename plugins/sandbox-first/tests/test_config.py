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
