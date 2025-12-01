#!/usr/bin/env python3 -u
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""
Tool Routing Hook for Claude Code
Suggests better tools when WebFetch is used for services with alternatives.

For design principles and implementation details, see:
docs/tool-routing-hook.md
"""
import json
import sys
import os
import re
from pathlib import Path

# Debug mode controlled by environment variable
DEBUG = os.environ.get('TOOL_ROUTING_DEBUG', '').lower() in ('1', 'true', 'yes')

# Log file for debugging
DEBUG_LOG_FILE = os.path.expanduser('~/.claude/tool-routing-debug.log') if DEBUG else None

def debug_log(message):
    """Print debug message if debug mode is enabled."""
    if DEBUG:
        print(f"[DEBUG] {message}", file=sys.stderr)
        # Also write to file
        if DEBUG_LOG_FILE:
            try:
                with open(DEBUG_LOG_FILE, 'a') as f:
                    import datetime
                    timestamp = datetime.datetime.now().isoformat()
                    f.write(f"[{timestamp}] {message}\n")
            except:
                pass  # Fail silently if can't write to log

def load_config():
    """Load routing configuration from plugin hooks directory."""
    plugin_root = os.environ.get('CLAUDE_PLUGIN_ROOT', '')
    if not plugin_root:
        debug_log("CLAUDE_PLUGIN_ROOT not set, allowing WebFetch")
        return None

    config_path = Path(plugin_root) / 'hooks' / 'tool-routes.json'
    debug_log(f"Loading config from: {config_path}")

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            debug_log(f"Loaded {len(config.get('routes', {}))} routes")
            return config
    except FileNotFoundError:
        debug_log(f"Config not found: {config_path}, allowing WebFetch")
        return None
    except json.JSONDecodeError as e:
        debug_log(f"Invalid JSON in config: {e}, allowing WebFetch")
        return None

def get_tool_data():
    """Extract tool use data from stdin."""
    try:
        raw_input = sys.stdin.read()
        debug_log(f"Raw stdin input: {raw_input[:500]}")  # Log first 500 chars
        data = json.loads(raw_input)
        debug_log(f"Parsed tool data: {json.dumps(data, indent=2)}")
        return data
    except json.JSONDecodeError as e:
        debug_log(f"Failed to parse JSON: {e}")
        return {}

def check_url_patterns(url, routes):
    """Check if URL matches any routing patterns."""
    if not url:
        debug_log("No URL in tool input")
        return None

    debug_log(f"Checking URL: {url}")

    for route_name, route_config in routes.items():
        pattern = route_config.get('pattern', '')
        if not pattern:
            continue

        try:
            if re.search(pattern, url, re.IGNORECASE):
                debug_log(f"Matched route: {route_name}")
                return {
                    'route_name': route_name,
                    'message': route_config.get('message', 'Use alternative tool'),
                    'matched_url': url,
                    'pattern': pattern
                }
        except re.error as e:
            debug_log(f"Invalid regex in route '{route_name}': {e}")
            continue

    debug_log("No routes matched")
    return None

def check_bash_command_patterns(command, routes):
    """Check if Bash command matches any routing patterns."""
    if not command:
        debug_log("No command in tool input")
        return None

    debug_log(f"Checking Bash command: {command}")

    for route_name, route_config in routes.items():
        command_pattern = route_config.get('command_pattern', '')
        if not command_pattern:
            continue

        try:
            if re.search(command_pattern, command):
                debug_log(f"Matched route: {route_name}")
                return {
                    'route_name': route_name,
                    'message': route_config.get('message', 'Use alternative tool'),
                    'matched_command': command,
                    'pattern': command_pattern
                }
        except re.error as e:
            debug_log(f"Invalid regex in route '{route_name}': {e}")
            continue

    debug_log("No routes matched")
    return None

def main():
    """Main hook execution."""
    # Load configuration
    config = load_config()
    if not config:
        # Fail open - allow tool use if config issues
        debug_log("No config loaded, allowing tool use")
        sys.exit(0)

    routes = config.get('routes', {})
    if not routes:
        # No routes configured, allow tool use
        debug_log("No routes configured, allowing tool use")
        sys.exit(0)

    # Get tool data from stdin
    tool_data = get_tool_data()
    tool_name = tool_data.get('tool_name', '')
    tool_input = tool_data.get('tool_input', {})

    debug_log(f"Tool: {tool_name}")

    match = None

    # Check WebFetch URL patterns
    if tool_name == 'WebFetch':
        url = tool_input.get('url', '')
        match = check_url_patterns(url, routes)

    # Check Bash command patterns
    elif tool_name == 'Bash':
        command = tool_input.get('command', '')
        match = check_bash_command_patterns(command, routes)

    else:
        debug_log(f"Tool '{tool_name}' not monitored, allowing tool use")
        sys.exit(0)

    if match:
        # Found a match - block and provide message
        if DEBUG:
            # Debug mode: show full details (but truncate long values)
            print(f"❌ Tool Routing: {match['route_name']}", file=sys.stderr)
            if 'matched_url' in match:
                url = match['matched_url']
                display = url if len(url) <= 200 else url[:200] + '...'
                print(f"Matched URL: {display}", file=sys.stderr)
            if 'matched_command' in match:
                cmd = match['matched_command']
                display = cmd if len(cmd) <= 200 else cmd[:200] + '...'
                print(f"Matched Command: {display}", file=sys.stderr)
            print(f"Pattern: {match['pattern']}", file=sys.stderr)
            print("", file=sys.stderr)
            print(match['message'], file=sys.stderr)
        else:
            # Normal mode: minimal output to save tokens
            print(match['message'], file=sys.stderr)
        sys.exit(2)  # Block the tool use

    # No match - allow tool use
    debug_log("No routes matched, allowing tool use")
    sys.exit(0)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        # Fail open on unexpected errors
        debug_log(f"Error in tool routing hook: {e}")
        sys.exit(0)
