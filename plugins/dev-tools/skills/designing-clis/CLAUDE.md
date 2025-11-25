# Testing the designing-clis Skill

## Purpose

This skill teaches CLI UX design principles, visual techniques, and practical patterns for creating discoverable, delightful command-line interfaces.

## Testing Approach

### Test Scenarios

The skill has been tested with three pressure scenarios in TDD RED-GREEN-REFACTOR style:

1. **Time Pressure** - Build health check CLI in 15 minutes (production down)
2. **Existing Codebase** - Add feature to CLI with poor UX patterns
3. **Fix Confusing CLI** - Troubleshoot and improve "hard to use" CLI

### Test Files Location

All test files should be created in `.scratch/` directory to avoid cluttering the repository:

```
.scratch/
  designing-clis-tests/
    baseline-scenario-1.md           # RED phase results
    baseline-scenario-2.md
    baseline-scenario-3.md
    green-scenario-1.md              # GREEN phase results with skill
    test-healthcheck.py              # Generated test CLI
    test-teamctl.py                  # Generated test CLI
    test-deployer.py                 # Generated test CLI
```

### Running Tests

**RED Phase (Baseline without skill):**
```
Task: Build/fix CLI without using designing-clis skill
Document: What agent does naturally, what they miss, what they rationalize
```

**GREEN Phase (With skill):**
```
Task: Same scenario but explicitly use designing-clis skill
Document: What changes, what's prioritized, what's skipped
Verify: Gaps from RED phase are addressed
```

**REFACTOR Phase:**
```
Identify: New rationalizations or gaps
Update: Skill to close loopholes
Re-test: Verify improvements
```

## Test Commands

When testing scenarios, use these patterns:

```bash
# Test building new CLI
Task subagent: "Build healthcheck CLI. Use designing-clis skill for guidance."

# Test extending existing CLI
Task subagent: "Add list-users to teamctl. Use designing-clis skill for consistency guidance."

# Test fixing confusing CLI
Task subagent: "Fix deployer CLI. Use designing-clis skill audit checklist."
```

## Key Things to Test

### Priority Framework
- Does agent know what to include under time pressure?
- Are high-impact, low-effort features prioritized?
- Is accessibility (--no-color) included despite urgency?

### Consistency Understanding
- Does agent match existing patterns vs improve?
- Are "free improvements" identified (additive/invisible)?
- Are issues surfaced with template?

### Systematic Auditing
- Does agent use checklist vs ad-hoc testing?
- Are all common issues checked?
- Are fixes comprehensive?

## Success Criteria

**Skill is working when:**
- ✅ Agent references practical-patterns.md checklists
- ✅ Time-pressured builds include accessibility
- ✅ Error messages follow template (what/valid/fix)
- ✅ Extending CLIs surfaces issues properly
- ✅ Audits are systematic, not ad-hoc

**Skill needs work when:**
- ❌ Agent skips accessibility under pressure
- ❌ Agent doesn't know which file to read
- ❌ Agent improves inconsistently without surfacing
- ❌ Agent invents own checklist vs using provided one

## Directory Hygiene

**Always use `.scratch/` for test artifacts:**
- Test CLI implementations
- Baseline documentation
- Comparison analyses
- Generated examples

**Keep skill directory clean:**
- Only skill files (SKILL.md, reference files)
- Research materials in research/ subdirectory
- This CLAUDE.md for testing instructions
