"""Find routes that match the same command, across every loaded plugin."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from tool_routing.checker import matching_routes
from tool_routing.config import Route


@dataclass
class Finding:
    """One overlap result. severity is "error" or "warning"."""

    severity: str
    source: str
    desc: str
    matches: list[str]
    message: str


def load_corpus(path: Path) -> list[dict]:
    """Load hand-written cross-route cases from a YAML file.

    Each case has desc, input (a tool call) and expect. expect is "allow"
    (no route may match) or "block" with `routes`, the exact set of route
    names that should match.
    """
    data = yaml.safe_load(Path(path).read_text()) or {}
    return data.get("cases", [])


def find_overlaps(routes: dict[str, Route], corpus: list[dict] | None = None) -> list[Finding]:
    """Replay every route test input, and every corpus case, against all routes.

    - An allow input matched by any route is an error.
    - A block input matched by routes besides its own is a warning.
    - A corpus case whose matches differ from what it expects is an error.
    """
    findings = []

    for route_name, route in routes.items():
        for test in route.tests:
            matches = matching_routes(test.input, routes)
            desc = test.desc or "(no description)"
            if test.expect == "allow" and matches:
                findings.append(
                    Finding(
                        "error",
                        route_name,
                        desc,
                        matches,
                        f"allow input is matched by {', '.join(matches)}",
                    )
                )
            elif test.expect == "block":
                others = [m for m in matches if m != route_name]
                if others:
                    findings.append(
                        Finding(
                            "warning",
                            route_name,
                            desc,
                            matches,
                            f"block input is also matched by {', '.join(others)}",
                        )
                    )

    for case in corpus or []:
        matches = matching_routes(case["input"], routes)
        desc = case.get("desc", "(no description)")
        if case.get("expect") == "allow":
            if matches:
                findings.append(
                    Finding(
                        "error",
                        "corpus",
                        desc,
                        matches,
                        f"corpus allow case is matched by {', '.join(matches)}",
                    )
                )
        elif sorted(matches) != sorted(case.get("routes", [])):
            findings.append(
                Finding(
                    "error",
                    "corpus",
                    desc,
                    matches,
                    f"expected routes {sorted(case.get('routes', []))}, got {sorted(matches)}",
                )
            )

    return findings
