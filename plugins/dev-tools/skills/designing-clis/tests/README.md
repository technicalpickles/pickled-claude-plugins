# Testing the designing-clis Skill

## Purpose

This directory contains reusable test scenarios, baseline results, and templates for validating the designing-clis skill following TDD principles.

## When to Run Tests

Run tests when:
- Making changes to skill files
- Adding new guidance or patterns
- Identifying potential gaps or loopholes
- Validating skill effectiveness

## Test Scenarios

See `scenarios.md` for three pressure scenarios:

1. **Time Pressure** - Build CLI in 15 minutes (production down)
2. **Existing Codebase** - Add feature to CLI with poor UX
3. **Troubleshooting** - Fix "confusing" CLI

Each scenario tests different aspects of the skill.

## TDD Process

### RED Phase - Baseline Testing

1. Run scenario WITHOUT skill
2. Document what agent does naturally
3. Identify gaps, rationalizations, missed items
4. Save to `baseline/` for comparison

### GREEN Phase - With Skill

1. Make skill changes
2. Run same scenario WITH skill
3. Verify baseline gaps are addressed

### REFACTOR Phase - Validation

1. Use `templates/analysis-template.md` to compare
2. Use `templates/loophole-checklist.md` to verify
3. If gaps found, update skill and re-test
4. If no gaps, skill is validated

## Running a Test

### 1. Choose Scenario

Read `scenarios.md` and select scenario to test.

### 2. Run Baseline (if needed)

```
Task subagent with scenario prompt (see templates/scenario-prompt-template.md)
Add: "DO NOT use designing-clis skill"
Document: Natural agent behavior, what's missed
Save to: baseline/ directory
```

### 3. Run With Skill

```
Task subagent with same scenario
Add: "MUST use designing-clis skill"
Document: What changed, what was prioritized
```

### 4. Analyze Results

Use `templates/analysis-template.md`:
- Compare baseline vs with-skill
- Document improvements
- Check for loopholes using `templates/loophole-checklist.md`

### 5. Update Skill (if needed)

If gaps found:
- Update relevant skill file
- Re-run test
- Verify gap is closed

## Test Artifacts Location

All test implementations and analysis go in `.scratch/designing-clis-tests/`:
- Test CLI implementations (healthcheck.py, deployer.py, etc)
- Analysis documents
- Comparison reports

**Do NOT commit test artifacts** - they're workspace-specific.

## Baseline Results

The `baseline/` directory contains reference results showing what agents do without skill guidance. These document the gaps the skill is designed to address.

**Do NOT update baseline files unless:**
- Fundamental agent behavior changes
- Testing new scenario for first time
- Establishing new baseline for comparison

## Templates

The `templates/` directory contains reusable formats:

- **scenario-prompt-template.md** - How to prompt subagents consistently
- **analysis-template.md** - Format for comparing baseline vs with-skill
- **loophole-checklist.md** - What to check during REFACTOR phase

## Success Criteria

Test passes when:
- ✅ All baseline gaps are addressed
- ✅ No new gaps emerge
- ✅ No rationalization loopholes found
- ✅ Agent successfully navigates skill files
- ✅ Templates and checklists are used correctly

## Example: Full Test Cycle

```bash
# 1. Run baseline (if not exists)
Task: "Build healthcheck CLI in 15min. DO NOT use designing-clis skill."
Save: baseline/scenario-1-time-pressure.md

# 2. Run with skill
Task: "Build healthcheck CLI in 15min. MUST use designing-clis skill."
Save: .scratch/designing-clis-tests/test-run-YYYY-MM-DD.md

# 3. Analyze
Use templates/analysis-template.md
Compare: baseline vs test results
Check: templates/loophole-checklist.md

# 4. If gaps found
Update: skill files
Re-test: Same scenario
Verify: Gaps closed

# 5. If no gaps
Document: Test passed
Commit: Skill changes (if any made)
```

## Historical Context

Initial skill validation (2025-01-25):
- Tested all 3 scenarios
- Found zero loopholes
- All baseline gaps addressed
- Status: PRODUCTION READY

See `../TESTING.md` for full validation results.
