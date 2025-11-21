# Skill Improvement Retrospectives

This directory contains case studies and retrospectives of skill improvement efforts in the dev-tools plugin.

## Purpose

When a skill fails to prevent a problem in production (real conversations), we:

1. **Analyze the failure** - What went wrong? What did the agent do instead?
2. **Document rationalizations** - What excuses did the agent make?
3. **Identify root causes** - Why didn't the skill prevent this?
4. **Create improvements** - What changes will prevent this failure?
5. **Test with pressure** - Does the improved skill work under stress?
6. **Document the process** - Share learnings with the team

These retrospectives serve as:
- **Case studies** for improving other skills
- **Patterns** of common skill weaknesses
- **Test scenarios** derived from real failures
- **Evidence** that improvements work

## File Naming

Files are named: `YYYY-MM-DD-[skill-name]-[source].md`

Examples:
- `2025-11-21-mcpproxy-conversation-a6858584.md` - Improvement based on specific conversation
- `2025-11-22-api-docs-github-issue-42.md` - Improvement based on GitHub issue

## Contents

Each retrospective should include:

### 1. Problem Analysis
- What conversation/scenario revealed the failure?
- What did the agent do wrong?
- What were the exact rationalizations used?
- Why didn't the current skill prevent it?

### 2. Root Causes
- What was unclear in the skill?
- What rationalizations weren't addressed?
- What examples were missing?
- What structure problems existed?

### 3. Recommendations
- Prioritized improvements (1-6)
- Specific text changes
- New sections to add
- Structure changes

### 4. Implementation
- What was actually changed
- Token budget impact
- Progressive disclosure considerations

### 5. Verification
- Test scenarios created
- Test results (link to skill's tests/)
- Pass/fail status
- Remaining issues (if any)

## Related Directories

### Skill Tests
Each skill has its own `tests/` directory with:
- Pressure scenarios for that skill
- Test results from verification runs

Example: `../../skills/using-mcpproxy-tools/tests/`

### Skill References
Skills with extensive content use `references/` for on-demand loading:
- Common mistakes
- Troubleshooting guides
- Examples

## Methodology

These retrospectives follow the **TDD approach for skills**:

1. **RED**: Document the baseline failure (skill didn't prevent mistake)
2. **GREEN**: Improve skill and verify with pressure tests
3. **REFACTOR**: Close remaining loopholes iteratively

See [testing-skills-with-subagents](https://github.com/anthropics/superpowers/skills/testing-skills-with-subagents) for full methodology.

## Using These Retrospectives

**When creating a new skill:**
- Review retrospectives for similar skills
- Learn from past failure patterns
- Apply proven improvement patterns

**When improving an existing skill:**
- Create a retrospective documenting the failure
- Follow the TDD cycle (RED-GREEN-REFACTOR)
- Link to this retrospective from skill tests

**When debugging skill failures:**
- Check if similar failure exists in retrospectives
- Apply proven solutions
- Document new patterns discovered
