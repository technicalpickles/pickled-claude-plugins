"""Configuration loading and merging for tool routing."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class TestCase:
    """Inline test case for a route."""

    input: dict
    expect: str  # "block" or "allow"
    desc: Optional[str] = None
    contains: Optional[str] = None


@dataclass
class Route:
    """A single routing rule."""

    tool: str
    pattern: str
    message: str
    tests: list[TestCase] = field(default_factory=list)
    source: Optional[str] = None  # File path where route was defined


def load_routes_file(path: Path) -> dict[str, Route]:
    """Load routes from a YAML file.

    Returns empty dict if file doesn't exist or is invalid (fail open).
    """
    if not path.exists():
        return {}

    try:
        with open(path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError:
        return {}

    if not data or "routes" not in data:
        return {}

    routes = {}
    for name, route_data in data.get("routes", {}).items():
        tests = []
        for test_data in route_data.get("tests", []):
            tests.append(
                TestCase(
                    input=test_data["input"],
                    expect=test_data["expect"],
                    desc=test_data.get("desc"),
                    contains=test_data.get("contains"),
                )
            )

        routes[name] = Route(
            tool=route_data["tool"],
            pattern=route_data["pattern"],
            message=route_data["message"],
            tests=tests,
            source=str(path),
        )

    return routes
