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


def check_tool_call(tool_call: dict, routes: dict[str, Route]) -> CheckResult:
    """Check a tool call against all routes.

    Args:
        tool_call: Dict with tool_name and tool_input
        routes: Dictionary of routes to check against

    Returns:
        CheckResult indicating if blocked and why
    """
    tool_name = tool_call.get("tool_name", "")
    tool_input = tool_call.get("tool_input", {})

    # Get the field to match for this tool type
    input_field = TOOL_INPUT_FIELDS.get(tool_name)
    if not input_field:
        # Tool type not monitored
        return CheckResult(blocked=False)

    value = tool_input.get(input_field, "")
    if not value:
        return CheckResult(blocked=False)

    # Check against each route
    for route_name, route in routes.items():
        # Only check routes for this tool type
        if route.tool != tool_name:
            continue

        try:
            if re.search(route.pattern, value, re.IGNORECASE):
                return CheckResult(
                    blocked=True,
                    route_name=route_name,
                    message=route.message,
                    matched_value=value,
                    pattern=route.pattern,
                )
        except re.error:
            # Invalid regex - skip this route (fail open)
            continue

    return CheckResult(blocked=False)
