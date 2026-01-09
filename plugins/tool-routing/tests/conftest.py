"""Pytest configuration for tool-routing tests."""

import os
from pathlib import Path

import pytest


@pytest.fixture
def cli_env(tmp_path):
    """Environment dict for CLI subprocess calls.

    Includes PYTHONPATH so subprocess can import tool_routing,
    CLAUDE_PLUGIN_ROOT pointing to tmp_path for test isolation,
    and TOOL_ROUTING_ISOLATED=1 to prevent sibling directory discovery.
    """
    src_path = Path(__file__).parent.parent / "src"
    return {
        "CLAUDE_PLUGIN_ROOT": str(tmp_path),
        "PYTHONPATH": str(src_path),
        "PATH": os.environ.get("PATH", ""),
        "TOOL_ROUTING_ISOLATED": "1",
    }
