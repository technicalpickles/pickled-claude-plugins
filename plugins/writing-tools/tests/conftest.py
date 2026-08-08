"""Pytest configuration for writing-tools tests."""

import os
from pathlib import Path

import pytest


@pytest.fixture
def cli_env(tmp_path):
    """Environment dict for CLI subprocess calls.

    Includes PYTHONPATH so the subprocess can import writing_tools, and points
    EMDASH_OUTBOUND_CONFIG at a per-test config path for isolation (bypassing
    the personal/project/shipped discovery chain).
    """
    src_path = Path(__file__).parent.parent / "src"
    config_file = tmp_path / "emdash-outbound.yaml"
    return {
        "PYTHONPATH": str(src_path),
        "PATH": os.environ.get("PATH", ""),
        "EMDASH_OUTBOUND_CONFIG": str(config_file),
    }
