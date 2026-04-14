"""Configuration loading for sandbox-first plugin."""

import json


def load_skip_list_from_file(path: str) -> list[str]:
    """Load skip_failure_requirement entries from a JSON config file.

    Returns an empty list if the file is missing, malformed, or has
    an invalid schema. Non-string entries are filtered out.
    """
    try:
        with open(path) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []

    entries = data.get("skip_failure_requirement") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        return []

    return [e for e in entries if isinstance(e, str)]
