"""Structural invariants for the git-guard plugin."""
from __future__ import annotations

import ast
import json
from pathlib import Path

PLUGIN_ROOT = Path(__file__).parent.parent
REPO_ROOT = PLUGIN_ROOT.parent.parent

PURE_MODULES = ["model.py", "rules.py", "templates.py", "files.py", "judge.py"]
FORBIDDEN_IMPORTS = {"os", "subprocess", "shutil"}
FORBIDDEN_CALLS = {
    "exists", "resolve", "read_text", "read_bytes",
    "stat", "open", "iterdir", "glob",
}


def test_manifest_valid():
    manifest = json.loads(
        (PLUGIN_ROOT / ".claude-plugin" / "plugin.json").read_text()
    )
    assert manifest["name"] == "git-guard"
    assert manifest["description"]


def test_marketplace_lists_plugin():
    marketplace = json.loads(
        (REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text()
    )
    entries = [p for p in marketplace["plugins"] if p["name"] == "git-guard"]
    assert len(entries) == 1
    assert entries[0]["source"] == "./plugins/git-guard"
    assert entries[0]["version"]


def test_package_importable():
    import gitguard

    assert gitguard.__file__


def _violations(path: Path) -> list[str]:
    found = []
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            found += [
                f"imports {a.name}"
                for a in node.names
                if a.name.split(".")[0] in FORBIDDEN_IMPORTS
            ]
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] in FORBIDDEN_IMPORTS:
                found.append(f"imports from {node.module}")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in FORBIDDEN_CALLS:
                found.append(f"calls .{node.func.attr}() at line {node.lineno}")
    return found


def test_pure_modules_do_no_io():
    """Every pure module exists (so a rename can't silently drop coverage) and does no IO."""
    for module in PURE_MODULES:
        path = PLUGIN_ROOT / "gitguard" / module
        assert path.exists(), module
        assert _violations(path) == [], module
