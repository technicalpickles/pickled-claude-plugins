#!/usr/bin/env python3 -u
"""
Tool Routing Hook for Claude Code
Suggests better tools when WebFetch is used for services with alternatives.
"""
import json
import sys
import os
import re
from pathlib import Path

def load_config():
    """Load routing configuration from plugin hooks directory."""
    plugin_root = os.environ.get('CLAUDE_PLUGIN_ROOT', '')
    if not plugin_root:
        print("⚠️  CLAUDE_PLUGIN_ROOT not set, allowing WebFetch", file=sys.stderr)
        return None

    config_path = Path(plugin_root) / 'hooks' / 'tool-routes.json'

    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️  Config not found: {config_path}, allowing WebFetch", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"⚠️  Invalid JSON in config: {e}, allowing WebFetch", file=sys.stderr)
        return None

def get_tool_data():
    """Extract tool use data from stdin."""
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}

def check_url_patterns(url, routes):
    """Check if URL matches any routing patterns."""
    if not url:
        return None

    for route_name, route_config in routes.items():
        pattern = route_config.get('pattern', '')
        if not pattern:
            continue

        try:
            if re.search(pattern, url, re.IGNORECASE):
                return {
                    'route_name': route_name,
                    'message': route_config.get('message', 'Use alternative tool'),
                    'matched_url': url
                }
        except re.error as e:
            print(f"⚠️  Invalid regex in route '{route_name}': {e}", file=sys.stderr)
            continue

    return None

def main():
    """Main hook execution."""
    # Load configuration
    config = load_config()
    if not config:
        # Fail open - allow WebFetch if config issues
        sys.exit(0)

    routes = config.get('routes', {})
    if not routes:
        # No routes configured, allow WebFetch
        sys.exit(0)

    # Get tool data from stdin
    tool_data = get_tool_data()
    tool_name = tool_data.get('tool_name', '')

    # Only check WebFetch calls
    if tool_name != 'WebFetch':
        sys.exit(0)

    # Extract URL from tool input
    url = tool_data.get('tool_input', {}).get('url', '')

    # Check against routing patterns
    match = check_url_patterns(url, routes)

    if match:
        # Found a match - block and provide message
        print(f"\n❌ Tool Routing: {match['route_name']}", file=sys.stderr)
        print(f"\nMatched URL: {match['matched_url']}", file=sys.stderr)
        print(f"\n{match['message']}", file=sys.stderr)
        print("", file=sys.stderr)
        sys.exit(1)  # Block the tool use

    # No match - allow WebFetch
    sys.exit(0)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        # Fail open on unexpected errors
        print(f"⚠️  Error in tool routing hook: {e}", file=sys.stderr)
        sys.exit(0)
