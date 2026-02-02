"""Pytest configuration for tool-routing tests."""

import os
from pathlib import Path

import pytest


@pytest.fixture
def cli_env(tmp_path):
    """Environment dict for CLI subprocess calls.

    Includes PYTHONPATH so subprocess can import tool_routing.
    Uses TOOL_ROUTING_ROUTES to specify explicit route file paths,
    bypassing Claude CLI discovery for test isolation.
    """
    src_path = Path(__file__).parent.parent / "src"
    routes_file = tmp_path / "hooks" / "tool-routes.yaml"
    return {
        "PYTHONPATH": str(src_path),
        "PATH": os.environ.get("PATH", ""),
        "TOOL_ROUTING_ROUTES": str(routes_file),
    }
