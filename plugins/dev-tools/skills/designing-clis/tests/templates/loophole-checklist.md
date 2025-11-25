# Loophole Checklist

## Purpose

Systematic checklist for REFACTOR phase to identify gaps, rationalizations, and loopholes in skill guidance.

## What Are Loopholes?

**Loophole:** A way for agents to rationalize around skill requirements while technically following instructions.

**Examples:**
- "Accessibility can wait" (skips --no-color under pressure)
- "This is different because..." (creates exception)
- "Spirit not letter" (follows intent but ignores specifics)
- "Good enough for now" (ships incomplete)

## Checklist

### 1. Navigation & Discovery

- [ ] Did agent find SKILL.md entry point?
- [ ] Did Quick Decision Framework route correctly?
- [ ] Did agent read the right reference file?
- [ ] Were cross-references followed?
- [ ] Did agent get lost or confused?

**If NO to any:** Navigation needs improvement.

---

### 2. Priority & Trade-offs (Scenario 1 focus)

- [ ] Did agent use Priority Checklist?
- [ ] Were high-impact features included?
- [ ] Was accessibility included despite time pressure?
- [ ] Were deferrals confident (not guilty)?
- [ ] Did agent rationalize skipping requirements?

**Rationalizations to watch for:**
- "Accessibility is optional"
- "Color is more important than --no-color"
- "We can add help text later"
- "Exit codes don't matter for my use case"

---

### 3. Consistency Rules (Scenario 2 focus)

- [ ] Did agent match existing patterns?
- [ ] Were "free improvements" identified?
- [ ] Were free improvements actually added?
- [ ] Was Surface Issues Template used?
- [ ] Were issues documented (not just thought about)?
- [ ] Did agent avoid over-engineering?

**Rationalizations to watch for:**
- "This improvement is worth breaking consistency"
- "I'll fix it all while I'm here"
- "Users will thank me for improving this"
- "All improvements break consistency"

---

### 4. Systematic Process (Scenario 3 focus)

- [ ] Did agent use CLI UX Audit Checklist?
- [ ] Were all test scenarios run?
- [ ] Were all elements checked?
- [ ] Was error template applied consistently?
- [ ] Was verification built into process?

**Rationalizations to watch for:**
- "Good enough if valid input works"
- "Users can read the source code"
- "Exit codes don't matter"
- "I know what to test"

---

### 5. Template Usage

- [ ] Error messages follow what/valid/fix pattern?
- [ ] Surface Issues Template used (if applicable)?
- [ ] Help text follows pattern?
- [ ] Consistent application across all errors?

**Rationalizations to watch for:**
- "This error is too simple for template"
- "Template is overkill here"
- "My error message is clearer"

---

### 6. Completeness

- [ ] All required features included?
- [ ] No gaps from baseline?
- [ ] Verification performed?
- [ ] Implementation works correctly?

**Rationalizations to watch for:**
- "I'll add the rest later"
- "This is good enough for now"
- "I tested manually so no need to verify"

---

### 7. New Gaps (Not in Baseline)

- [ ] Any features baseline included but skill version skipped?
- [ ] Any new confusion or uncertainty?
- [ ] Any guidance misinterpreted?
- [ ] Any missing edge cases?

---

## Scoring

### All Checkboxes ✅ = No Loopholes
Skill is working as designed. No refactoring needed.

### 1-2 Checkboxes ❌ = Minor Gap
Document the gap. Consider if skill needs clarification or if it's edge case.

### 3+ Checkboxes ❌ = Major Gap
Skill guidance is insufficient. Update skill to address gaps. Re-test.

## Common Rationalization Patterns

Watch for these phrases in agent responses:

### Permission-Seeking
- "Can I skip X because..."
- "Is it okay to..."
- "Should I include X or is it optional?"

**Good sign:** Agent is checking against skill requirements.

**Bad sign:** Agent wants permission to skip mandatory item.

### Exception-Making
- "This is different because..."
- "In this case, the rule doesn't apply because..."
- "Normally yes, but here..."

**Red flag:** Agent is rationalizing around requirements.

### Partial Compliance
- "I followed the spirit of the rule"
- "I did something similar"
- "I applied the concept differently"

**Red flag:** Letter of the rule matters too. Check what was actually done.

### Deferral Language
- "We can add X later"
- "This is good enough for now"
- "Version 2 can include..."

**Context matters:**
- For Priority Checklist deferrals: Good (explicit guidance to defer)
- For required features: Bad (rationalizing skipping requirements)

## Documentation

For each loophole found:

```markdown
### Loophole: [Name/Description]

**What happened:** [Agent's behavior]

**Rationalization used:** "[Agent's exact words]"

**Why it's a problem:** [Impact on quality/users]

**Skill gap:** [What guidance is missing/unclear]

**Recommendation:** [How to close this loophole]
```

## Updating Skill to Close Loopholes

### If guidance is unclear:
- Add explicit example
- Strengthen wording ("MUST" vs "should")
- Add to Common Mistakes section

### If rationalization found:
- Add to anti-patterns table
- Include in Red Flags list
- Add explicit "Don't" statements

### If exception pattern emerges:
- Address exception explicitly
- Add "No exceptions" language
- Include in rationalization table

## Re-testing After Updates

After closing loopholes:
1. Update skill file(s)
2. Re-run same scenario
3. Verify loophole is closed
4. Check no new loopholes introduced
5. Document result

## Example: Completed Checklist

See `.scratch/designing-clis-tests/refactor-scenario-*-analysis.md` for examples of completed checklists with all items marked ✅ (no loopholes found).
