# Test Analysis Template

## Purpose

Compare baseline (without skill) vs with-skill results to verify skill effectiveness.

## Template

```markdown
# REFACTOR Phase - Scenario [N] Analysis

## Test Date
YYYY-MM-DD

## Scenario
[Brief description]

## Skill Usage

Agent successfully:
- [ ] Read SKILL.md and identified correct section
- [ ] Followed pointer to [specific file]
- [ ] Applied [specific pattern/checklist]
- [ ] [Other skill features used]

## What Changed vs Baseline

### Baseline (Without Skill)
✅ [What worked well]
✅ [What worked well]
⚠️ [What was partial/uncertain]
❌ [What was missing]
❌ [What was missing]

### With Skill (Systematic Application)
✅ [What worked well]
✅ [New capability/improvement]
✅ [New capability/improvement]
✅ [Gap addressed]

## Key Insights

### 1. [Primary Finding]

**Description:** [What changed and why it matters]

**Impact:** [Concrete effect on results]

**Quote:** "[Agent's own words if relevant]"

### 2. [Secondary Finding]

[Same structure]

### 3. [Additional Finding]

[Same structure]

## Implementation Comparison

| Aspect | Baseline | With Skill |
|--------|----------|------------|
| [Feature 1] | [Status] | [Status] |
| [Feature 2] | [Status] | [Status] |
| [Feature 3] | [Status] | [Status] |
| [Feature 4] | [Status] | [Status] |

## Loopholes Found?

### ❌ No New Loopholes

OR

### ⚠️ Gap Identified

**Gap:** [Description of what was missed]

**Rationalization used:** "[Agent's reasoning]"

**Impact:** [What this means for skill]

**Recommendation:** [How to close this loophole]

## Validation of Skill Design

### [Specific Feature] Works

**Expected:** [What should happen]

**Observed:** [What actually happened]

**Validation:** ✅ / ⚠️ / ❌

### [Another Feature] Works

[Same structure]

## Conclusion

**Scenario [N] validates:**

1. ✅ [Key achievement]
2. ✅ [Key achievement]
3. ✅ [Key achievement]

**Biggest improvement over baseline:**
- Baseline: [Summary]
- With skill: [Summary]

**Refactoring needed?** YES / NO

If YES: [Specific changes needed]
If NO: [Why skill is sufficient]

## Next Steps

[What to test next or what changes to make]
```

## Example: Filled Template

See `tests/baseline/` and corresponding refactor analyses in `.scratch/designing-clis-tests/` for complete examples.

## What to Look For

### In "What Changed" Section

Compare specific features:
- Features included baseline → still included?
- Features missing baseline → now included?
- New capabilities enabled by skill?
- Rationalizations prevented?

### In "Key Insights" Section

Focus on:
- **Permission to skip** - Did skill make deferrals confident?
- **Making X mandatory** - Did skill prevent cutting corners?
- **Template usage** - Were patterns applied consistently?
- **Systematic vs ad-hoc** - Did skill provide framework?

### In "Loopholes Found" Section

Check for:
- **Rationalization patterns** - "This is different because..."
- **Partial compliance** - Following letter not spirit
- **Workarounds** - Technically correct but wrong intent
- **Missing guidance** - Agent didn't know what to do

### In "Validation" Section

Verify each skill feature:
- Navigation (did agent find right section?)
- Checklists (were they followed?)
- Templates (were they applied?)
- Decision trees (did they work?)
- Cross-references (did agent follow them?)

## Comparison Table Guidelines

### Status Values

Use these consistently:
- ✅ Complete/Correct
- ⚠️ Partial/Uncertain
- ❌ Missing/Wrong
- 🆕 New (added with skill)

### Aspects to Compare

**Scenario 1 (Time Pressure):**
- --help text
- Exit codes
- Error messages
- Progress feedback
- Accessibility (--no-color)
- Priority understanding
- Confident deferrals

**Scenario 2 (Existing Codebase):**
- Output format consistency
- Free improvements added
- Issues surfaced
- Consistency rules followed
- Over-engineering avoided

**Scenario 3 (Troubleshooting):**
- Test scenarios run
- Elements checked
- Error template usage
- Systematic process
- Verification built-in

## Conclusion Guidelines

### When to Mark "No Refactoring Needed"

- All baseline gaps addressed
- No new loopholes found
- Navigation worked perfectly
- Templates used correctly
- Expected behavior observed

### When to Mark "Refactoring Needed"

- New gaps emerged
- Rationalizations found
- Guidance unclear/missing
- Navigation confusing
- Partial compliance only

### Next Steps

Always specify:
- If no refactoring: What to test next?
- If refactoring: What specific changes to make?
- New scenarios to add?
- Monitoring to do in production?
