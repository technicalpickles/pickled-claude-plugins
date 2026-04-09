import json
import tempfile

from sandbox_plugin.transcript import find_recent_sandboxed_failure


def write_transcript(entries):
    """Write list of JSONL dicts to a temp file, return path."""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
    for entry in entries:
        f.write(json.dumps(entry) + "\n")
    f.close()
    return f.name


def make_tool_use_entry(command, dangerously_disable=False):
    """Create a transcript entry with a Bash tool_use block."""
    tool_input = {"command": command}
    if dangerously_disable:
        tool_input["dangerouslyDisableSandbox"] = True
    return {
        "message": {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "Bash",
                    "input": tool_input,
                }
            ],
        }
    }


def make_tool_error_entry(error_text):
    """Create a transcript entry representing a tool failure."""
    return {
        "message": {
            "role": "tool",
            "content": [
                {
                    "type": "tool_result",
                    "is_error": True,
                    "content": error_text,
                }
            ],
        }
    }


def make_tool_success_entry(stdout="ok"):
    """Create a transcript entry representing a tool success."""
    return {
        "message": {
            "role": "tool",
            "content": [
                {
                    "type": "tool_result",
                    "is_error": False,
                    "content": stdout,
                }
            ],
        }
    }


class TestFindRecentSandboxedFailure:
    def test_no_entries(self):
        path = write_transcript([])
        assert find_recent_sandboxed_failure(path, lookback=10) is False

    def test_sandboxed_failure_found(self):
        entries = [
            make_tool_use_entry("curl https://example.com"),
            make_tool_error_entry("Operation not permitted"),
        ]
        path = write_transcript(entries)
        assert find_recent_sandboxed_failure(path, lookback=10) is True

    def test_unsandboxed_failure_not_counted(self):
        entries = [
            make_tool_use_entry("curl https://example.com", dangerously_disable=True),
            make_tool_error_entry("Connection refused"),
        ]
        path = write_transcript(entries)
        assert find_recent_sandboxed_failure(path, lookback=10) is False

    def test_sandboxed_success_not_counted(self):
        entries = [
            make_tool_use_entry("echo hello"),
            make_tool_success_entry("hello"),
        ]
        path = write_transcript(entries)
        assert find_recent_sandboxed_failure(path, lookback=10) is False

    def test_outside_lookback_window(self):
        entries = [
            make_tool_use_entry("curl https://example.com"),
            make_tool_error_entry("Operation not permitted"),
        ]
        # Push failure outside lookback window
        for i in range(15):
            entries.append(make_tool_use_entry(f"echo {i}"))
            entries.append(make_tool_success_entry(str(i)))
        path = write_transcript(entries)
        assert find_recent_sandboxed_failure(path, lookback=5) is False

    def test_sandboxed_failure_within_lookback(self):
        entries = [
            make_tool_use_entry("echo old"),
            make_tool_success_entry("old"),
            make_tool_use_entry("curl https://example.com"),
            make_tool_error_entry("Operation not permitted"),
            make_tool_use_entry("echo thinking"),
            make_tool_success_entry("thinking"),
        ]
        path = write_transcript(entries)
        assert find_recent_sandboxed_failure(path, lookback=10) is True

    def test_malformed_lines_skipped(self):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
        f.write("not json\n")
        f.write(json.dumps(make_tool_use_entry("curl https://x.com")) + "\n")
        f.write(json.dumps(make_tool_error_entry("Operation not permitted")) + "\n")
        f.close()
        assert find_recent_sandboxed_failure(f.name, lookback=10) is True

    def test_missing_file_returns_false(self):
        assert find_recent_sandboxed_failure("/nonexistent/path.jsonl", lookback=10) is False
