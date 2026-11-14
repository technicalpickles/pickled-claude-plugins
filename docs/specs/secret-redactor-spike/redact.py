#!/usr/bin/env python3
import json, sys, pathlib

here = pathlib.Path(__file__).parent
canary = (here / "canary.txt").read_text().strip()
payload = json.load(sys.stdin)
resp = payload.get("tool_response")

def mask(v):
    if isinstance(v, str):
        return v.replace(canary, "[REDACTED]")
    if isinstance(v, list):
        return [mask(x) for x in v]
    if isinstance(v, dict):
        return {k: mask(x) for k, x in v.items()}
    return v

hit = canary in json.dumps(resp)
with (here / "hook.log").open("a") as f:
    f.write(json.dumps({"tool": payload.get("tool_name"), "resp_type": type(resp).__name__,
                        "resp_keys": list(resp) if isinstance(resp, dict) else None, "hit": hit}) + "\n")
if hit:
    key = "updatedMCPToolOutput" if str(payload.get("tool_name", "")).startswith("mcp__") else "updatedToolOutput"
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", key: mask(resp)}}))
