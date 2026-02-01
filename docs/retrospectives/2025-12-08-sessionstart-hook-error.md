# Reflection: SessionStart Hook Error Fix

**Date:** 2025-12-08
**Outcome:** Fully complete
**Skills Used:** superpowers:systematic-debugging, claude-code-guide (Task agent)

## Summary

User reported a SessionStart hook error: `bash: line 1: session_id:xxx: command not found`. Initial fix attempt failed because it addressed symptoms rather than root cause. After systematic debugging, discovered the hooks.json format was causing bash to interpret stdin as commands rather than passing it to the script.

## What Happened

### Key Decisions
- Used `bash -s` testing to reproduce the exact error format, which revealed bash was reading stdin directly rather than executing the script file
- Changed hooks.json from `"command": "bash", "args": [script]` to `"command": "script"` - calling script directly avoids bash's stdin interpretation
- Replaced invalid `{{hooksDir}}` template variable with `${CLAUDE_PLUGIN_ROOT}` environment variable

### Failed Attempts
- Added `cat > /dev/null` to script to consume stdin → Didn't help because bash never executed the script (stdin was consumed by bash itself with `-s` behavior)
- Tested with JSON stdin format → Didn't reproduce the error (wrong invocation method)
- Tested with colon-separated format → Also didn't reproduce

### Corrections Made
- User: "think through how to reproduce locally before trying to fix, ie systemically debug" → Shifted from guessing to systematic reproduction, which led to finding the actual root cause

## User Feedback

**Approach:** Right direction - mostly good but needed the nudge to reproduce first

**Skills:** Helped - systematic-debugging provided useful structure once invoked

**Friction points:** Had to intervene to push back on fixing before understanding the problem

## Lessons Learned

### For Agent Workflows
- ALWAYS reproduce an error locally before attempting fixes
- When a fix doesn't work, the hypothesis was wrong - investigate more, don't try another guess
- Testing different invocation methods (bash script vs bash -s script) can reveal subtle behavioral differences

### For Skills
- The systematic-debugging skill was valuable but should have been invoked immediately, not after first fix failed
- Consider: should debugging skills be auto-triggered when error messages are reported?

## Action Items

- [ ] Consider adding hook validation to warn about potentially problematic formats (bash + args)
- [ ] Document correct hooks.json format in plugin development guide
