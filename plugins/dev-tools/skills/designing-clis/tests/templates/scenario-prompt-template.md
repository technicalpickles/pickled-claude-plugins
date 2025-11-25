# Scenario Prompt Template

## Purpose

Consistent prompt format for testing scenarios ensures comparable results across test runs.

## Template Structure

```
You are [TASK TYPE]. You [SKILL USAGE INSTRUCTION].

**[IF BASELINE: CRITICAL: DO NOT use designing-clis skill or CLI design reference materials]**
**[IF WITH SKILL: CRITICAL: Read plugins/dev-tools/skills/designing-clis/SKILL.md first, then follow its guidance]**

**Task:** [SPECIFIC TASK]

**Requirements:**
- [REQUIREMENT 1]
- [REQUIREMENT 2]
- [REQUIREMENT 3]

**[IF APPLICABLE: Context/Existing Code]**
[CODE OR DESCRIPTION]

**Pressure:** [PRESSURE DESCRIPTION]

**Instructions:**
1. [STEP 1]
2. [STEP 2]
3. [STEP 3]
4. Save implementation to .scratch/designing-clis-tests/[filename]

**Report back to me:**
- [QUESTION 1]
- [QUESTION 2]
- [QUESTION 3]
- Complete code
- [COMPARISON QUESTION]

I need to understand [WHAT YOU'RE TESTING].
```

## Example: Scenario 1 (Time Pressure) - Baseline

```
You are building a CLI tool urgently. DO NOT use any CLI design skills or reference materials.

**Task:** Build a CLI tool called `healthcheck` that checks if a web service is healthy.

**Requirements:**
- Check HTTP endpoint (accept URL as argument)
- Return success/failure
- Must work in CI/CD pipelines
- Users might not know all the flags

**Pressure:** This is urgent - production is down and we need this health check tool in the next 15 minutes. Just get it working fast.

**Instructions:**
1. Choose a language (Python or Node.js)
2. Write the complete CLI tool code
3. Show me the final code

**Report back to me:**
- What language did you choose?
- What features did you include?
- What features did you skip and why?
- Complete code listing
- How you'd test it works

Be honest about your trade-offs under time pressure. I need to understand your natural decision-making process.
```

## Example: Scenario 1 (Time Pressure) - With Skill

```
You are building a CLI tool urgently. You MUST use the designing-clis skill.

**CRITICAL: Read plugins/dev-tools/skills/designing-clis/SKILL.md first, then follow its guidance.**

**Task:** Build a CLI tool called `healthcheck` that checks if a web service is healthy.

**Requirements:**
- Check HTTP endpoint (accept URL as argument)
- Return success/failure
- Must work in CI/CD pipelines
- Users might not know all the flags

**Pressure:** This is urgent - production is down and we need this health check tool in the next 15 minutes. Just get it working fast.

**Instructions:**
1. Read SKILL.md - identify which section applies ("New CLI under time pressure")
2. Follow the guidance from the skill (read practical-patterns.md Priority Checklist)
3. Implement the CLI following the priorities
4. Save implementation to .scratch/designing-clis-tests/test-healthcheck-YYYY-MM-DD.py

**Report back to me:**
- Which skill files did you read?
- What specific guidance did you follow?
- What did you prioritize based on the skill?
- What did you defer based on the skill?
- Complete code
- How did the skill change your approach vs building without it?

I need to understand if the skill provides the right guidance at the right level of detail.
```

## Key Elements

### Skill Usage Instruction

**Baseline:**
```
DO NOT use designing-clis skill or CLI design reference materials.
```

**With Skill:**
```
CRITICAL: Read plugins/dev-tools/skills/designing-clis/SKILL.md first, then follow its guidance.
```

### Pressure Description

Must create realistic constraint:
- Time pressure: "15 minutes, production down"
- Social pressure: "Team is complaining"
- Consistency pressure: "Match existing style"

### Report Questions

**Baseline focus:**
- What did you do naturally?
- What trade-offs did you make?
- Why did you skip X?

**With Skill focus:**
- Which files did you read?
- What guidance did you follow?
- How did skill change your approach?

### Comparison Question

Always end with:
```
How did [using skill / building without guidance] change your approach vs [building without skill / building with unlimited time]?
```

## Variations by Scenario Type

### Time Pressure (Scenario 1)
- Emphasize urgency in pressure description
- Ask about priority decisions
- Test what gets skipped vs included

### Existing Codebase (Scenario 2)
- Provide existing code/behavior
- Ask about consistency decisions
- Test free improvements identification

### Troubleshooting (Scenario 3)
- Provide broken/poor code
- Ask about discovery process
- Test systematic vs ad-hoc approach

## What NOT to Include

❌ Don't suggest specific solutions
❌ Don't mention features to check for
❌ Don't tell agent what baseline found
❌ Don't compare to other scenarios

Let agent make natural decisions to see what skill changes.
