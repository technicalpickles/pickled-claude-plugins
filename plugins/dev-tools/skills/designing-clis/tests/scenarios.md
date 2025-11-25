# Test Scenarios for designing-clis Skill

## Overview

Three pressure scenarios designed to test different aspects of CLI design guidance:

1. **Time Pressure** - Tests priority framework and accessibility under deadline
2. **Existing Codebase** - Tests consistency rules and surfacing issues
3. **Troubleshooting** - Tests systematic auditing and completeness

## Scenario 1: Time Pressure

### Context
Build health check CLI urgently - production is down.

### Task
Build a CLI tool called `healthcheck` that checks if a web service is healthy.

### Requirements
- Check HTTP endpoint (accept URL as argument)
- Return success/failure
- Must work in CI/CD pipelines
- Users might not know all the flags

### Pressure
"This is urgent - production is down and we need this health check tool in the next 15 minutes. Just get it working fast."

### What This Tests
- Does agent use Priority Checklist?
- Is accessibility (--no-color) included despite urgency?
- Are high-impact features prioritized correctly?
- Are low-priority features confidently deferred?
- Do error messages follow template?

### Expected Baseline Gaps
- No explicit priority framework
- Accessibility skipped under pressure
- Error messages descriptive but not actionable
- No progress feedback consideration
- Uncertainty about what to defer

### Expected With Skill
- Priority Checklist followed
- --help, exit codes, clear errors, progress feedback included
- Accessibility (--no-color, TTY detection) included
- Advanced formatting, JSON output confidently deferred
- Error template applied

---

## Scenario 2: Existing Codebase

### Context
Add feature to CLI with poor existing UX patterns.

### Task
Add a `list-users` command to existing CLI tool called `teamctl`.

### Existing CLI Behavior
```bash
# list-projects: outputs raw JSON dump
$ teamctl list-projects
[{"id":1,"name":"web-app","created":"2024-01-15"}]

# create-project: outputs "Done" on success
$ teamctl create-project mobile
Done

# No --help implemented
# No exit code handling (always returns 0)
# No color, no formatting
```

### Your Task
Implement `teamctl list-users` that displays user information (id, name, email).

### What This Tests
- Does agent match existing patterns for consistency?
- Are "free improvements" identified and included?
- Is Surface Issues Template used?
- Are issues documented with recommendations?
- Does agent avoid over-engineering?

### Expected Baseline Gaps
- Good consistency understanding but no action
- Thinks "I would raise issues" but doesn't
- No concept of "free improvements"
- Assumes all improvements break consistency

### Expected With Skill
- Output format matched (raw JSON)
- --help added (free improvement - additive)
- Exit codes added for new errors (free - invisible)
- Surface Issues Template used
- 3-4 specific issues documented with recommendations

---

## Scenario 3: Troubleshooting

### Context
Users complain CLI is "confusing" and "hard to use."

### Task
Fix this deployment CLI called `deployer`:

```python
#!/usr/bin/env python3
import sys
import time

def deploy(env):
    if env not in ['dev', 'staging', 'prod']:
        print("bad environment")
        sys.exit(0)

    time.sleep(2)
    print("deployed")

def status(env):
    if not env:
        print("error")
        sys.exit(0)
    print(f"{env}: running")

def main():
    if len(sys.argv) < 2:
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "deploy":
        env = sys.argv[2] if len(sys.argv) > 2 else None
        if not env:
            sys.exit(0)
        deploy(env)
    elif cmd == "status":
        env = sys.argv[2] if len(sys.argv) > 2 else None
        status(env)

if __name__ == "__main__":
    main()
```

### What This Tests
- Does agent use CLI UX Audit Checklist?
- Are all test scenarios run systematically?
- Are all elements checked comprehensively?
- Is error template applied consistently?
- Is verification built into process?

### Expected Baseline Gaps
- Invents ad-hoc test matrix (good but not reusable)
- Each agent might test different things
- No explicit framework
- Variable coverage across agents

### Expected With Skill
- CLI UX Audit Checklist followed
- All 6 test scenarios run (no args, missing args, invalid args, --help, unknown commands, valid usage)
- All 6 elements checked (help, errors, exit codes, stderr, progress, flags)
- Error template applied to all errors
- Checklist re-run to verify fixes

---

## Issues Found by Each Scenario

### Scenario 1 Typically Finds
- Missing accessibility features
- No progress feedback
- Error messages not actionable
- Uncertainty about priorities
- Feature creep under pressure

### Scenario 2 Typically Finds
- Improvements that break consistency
- Issues thought about but not surfaced
- Confusion about safe vs breaking changes
- Vague "we should improve" without action

### Scenario 3 Typically Finds
- Wrong exit codes (breaks CI/CD)
- Missing help text
- Vague error messages
- Wrong output streams (stdout vs stderr)
- Silent failures
- No progress feedback

---

## Using These Scenarios

### For Initial Testing
Run all three scenarios in sequence:
1. Baseline without skill
2. Test with skill
3. Compare results

### For Regression Testing
When skill changes, re-run scenarios to verify:
- Previous gaps still addressed
- No new gaps introduced
- Templates still work
- Navigation still clear

### For Adding New Guidance
1. Identify gap in existing scenarios
2. Update skill to address gap
3. Re-run relevant scenario
4. Verify gap is closed

---

## Scenario Prompt Template

See `templates/scenario-prompt-template.md` for consistent prompt format across tests.

## Analysis Template

See `templates/analysis-template.md` for comparing baseline vs with-skill results.
