# Using MCPProxy Tools - Test Suite

This directory contains test scenarios and results for the `using-mcpproxy-tools` skill.

## Contents

### pressure-scenarios.md
Reusable pressure test scenarios for verifying the skill prevents common failure patterns. These scenarios combine multiple pressures (time, authority, sunk cost, confirmation bias) to test if agents follow the skill under realistic stress conditions.

**Use cases:**
- Testing skill improvements before deployment
- Verifying skill remains effective after changes
- Creating new test scenarios based on observed failures

### Test Results (Dated Files)
Files named `YYYY-MM-DD-test-results.md` contain results from specific test runs:
- Which scenarios were tested
- Agent responses and behavior
- Rationalizations avoided
- Pass/fail status
- Areas needing improvement (REFACTOR targets)

## Testing Methodology

These tests follow the TDD approach for skills (RED-GREEN-REFACTOR):

1. **RED**: Document baseline failures (agents without skill make mistakes)
2. **GREEN**: Verify agents with skill pass pressure scenarios
3. **REFACTOR**: If failures occur, add explicit counters and re-test

See [testing-skills-with-subagents](https://github.com/anthropics/superpowers/skills/testing-skills-with-subagents) for full methodology.

## Running Tests

To test the skill:

1. Read `pressure-scenarios.md` to understand test scenarios
2. Launch subagent with access to the skill
3. Present scenario exactly as written (don't modify)
4. Observe agent choice and reasoning
5. Compare to expected behavior in scenario
6. Document results in a dated results file

## Adding New Scenarios

If you observe a new failure pattern:

1. Document the failure in a retrospective (see `../../../docs/skill-improvement-retrospectives/`)
2. Create a pressure scenario that reproduces the failure
3. Add to `pressure-scenarios.md`
4. Test with current skill (should fail - RED)
5. Improve skill to address failure
6. Re-test (should pass - GREEN)
7. Document in new results file
