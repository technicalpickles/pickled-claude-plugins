"""Pattern matching for tool calls against routes."""

import re
from dataclasses import dataclass
from typing import Optional

from tool_routing.config import Route

# Maps tool name to the field in tool_input to match against
TOOL_INPUT_FIELDS = {
    "WebFetch": "url",
    "Bash": "command",
}


@dataclass
class CheckResult:
    """Result of checking a tool call against routes."""

    blocked: bool
    route_name: Optional[str] = None
    message: Optional[str] = None
    matched_value: Optional[str] = None
    pattern: Optional[str] = None


def _target_value(tool_call: dict) -> tuple[str, str]:
    """Return (tool_name, value to match), or (tool_name, "") if unmonitored."""
    tool_name = tool_call.get("tool_name", "")
    input_field = TOOL_INPUT_FIELDS.get(tool_name)
    if not input_field:
        return tool_name, ""
    return tool_name, tool_call.get("tool_input", {}).get(input_field, "")


def matching_routes(tool_call: dict, routes: dict[str, Route]) -> list[str]:
    """Names of every route that matches the tool call, in table order."""
    tool_name, value = _target_value(tool_call)
    if not value:
        return []

    names = []
    for route_name, route in routes.items():
        if route.tool != tool_name:
            continue
        try:
            if re.search(route.pattern, value, re.IGNORECASE):
                names.append(route_name)
        except re.error:
            # Invalid regex - skip this route (fail open)
            continue
    return names


def check_tool_call(tool_call: dict, routes: dict[str, Route]) -> CheckResult:
    """Check a tool call against all routes.

    Args:
        tool_call: Dict with tool_name and tool_input
        routes: Dictionary of routes to check against

    Returns:
        CheckResult for the first matching route
    """
    names = matching_routes(tool_call, routes)
    if not names:
        return CheckResult(blocked=False)

    route = routes[names[0]]
    return CheckResult(
        blocked=True,
        route_name=names[0],
        message=route.message,
        matched_value=_target_value(tool_call)[1],
        pattern=route.pattern,
    )
