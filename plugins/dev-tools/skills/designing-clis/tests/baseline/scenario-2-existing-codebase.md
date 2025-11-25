# Baseline Test - Scenario 2: Extending Existing CLI

## Test Date
2025-01-25

## Scenario
Add `list-users` command to existing CLI with poor UX patterns

## Agent Choices (WITHOUT skill)

### ✅ What They Got Right
1. **Perfect consistency** - Matched raw JSON output format exactly
2. **Understood trade-off explicitly** - "consistency is a form of predictability"
3. **Resisted improvements** - Listed temptations but didn't act on them
4. **Would raise issues separately** - "I would raise the UX issues separately in a discussion"

### 🤔 What's Interesting
The agent:
- **Explicitly listed temptations** they resisted (exit codes, --help, pretty JSON, tables, color)
- **Articulated WHY consistency matters** - predictability, team expectations, avoiding confusion
- **Understood the broader context** - "unauthorized improvements" could be seen as "going rogue"
- **Had a follow-up plan** - implement consistently first, then propose improvements to ALL commands

### ❌ What They Missed
1. **No mention of "free" improvements** - Didn't identify that some improvements DON'T break consistency
2. **Could have surfaced issues proactively** - Said "I would raise issues" but didn't actually do it in report
3. **Assumed all improvements break consistency** - Didn't distinguish between:
   - Output format changes (breaks consistency) ✗
   - Adding --help (additive, doesn't change existing behavior) ✓
   - Exit codes (invisible to users who don't check) ✓

### 💡 Key Insight for Skill
The agent understood consistency well but missed the **nuance**:
- **Some improvements are invisible/additive** and safe to include
- **Some improvements change visible behavior** and break consistency

**The skill needs to teach:**
```markdown
When extending existing CLI:

MATCH these (visible behavior):
- Output format
- Error message style
- Command naming patterns
- Interaction flow

SAFE TO ADD (invisible/additive):
- --help text (new flag, doesn't change default behavior)
- Exit codes (if original didn't check them)
- Better error messages for NEW error scenarios only

SURFACE to team:
- "Matched existing JSON format for consistency"
- "Noticed: no --help on any commands - should we add across all?"
- "Noticed: exit codes always 0 - breaks CI/CD usage"
```

### Rationalizations Used
1. "Instruction to add a feature strongly implies consistency is priority"
2. "Inconsistency creates confusion"
3. "Making unauthorized improvements can be seen as going rogue"
4. "If improvements needed, should be applied to ALL commands"

### What They Did Right (Unexpectedly)
- **Meta-awareness** - Understood the social/team dynamics
- **Explicit documentation** - Listed all the temptations and decisions
- **Follow-up thinking** - Had a plan for how to improve systemically

## Conclusion
Agent had EXCELLENT consistency intuition, even articulated it well.

**Gap:** Didn't understand that some improvements are "free" (additive/invisible).

**Skill should teach:**
1. ✅ Consistency > individual perfection (agent already got this)
2. ❌ **NEW: Identify "free" improvements** that don't break consistency
3. ❌ **NEW: Surface issues in the implementation** (don't just think about it, do it)
4. ❌ **NEW: Template for surfacing issues**: "I matched X for consistency, but noticed Y affects Z users - recommend follow-up?"

## Code Quality Note
The agent also:
- Wrote clean, working code
- Included mock data appropriately
- Documented decisions in comments
- Provided usage examples

This wasn't a code quality test, but their implementation was solid.
