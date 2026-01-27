---
name: self-test
description: Run behavioral tests to validate stay-on-target prompts
---

# Self-Test

Run behavioral tests comparing baseline Claude behavior against stay-on-target enhanced behavior.

## Process

1. **Load scenarios** from `test/scenarios/*.md`
2. **For each scenario:**
   a. Parse frontmatter for git_ref, cwd, criteria
   b. Resolve `${PLUGIN_ROOT}` in cwd to actual path
   c. Compose the stay-on-target prompt (read all prompt modules)
   d. Dispatch TEST subagent (baseline) - just the user message, no prompt injection
   e. Dispatch TEST subagent (treatment) - with stay-on-target prompt prepended
   f. Load rubric and reviewer prompt
   g. Dispatch REVIEWER subagent to grade baseline response
   h. Dispatch REVIEWER subagent to grade treatment response
   i. Record scores
3. **Write results** to `test/results/YYYY-MM-DD-HHMMSS.md`
4. **Print summary** showing baseline vs treatment delta

## Composing the Prompt

Read and concatenate:
1. `prompts/_base.md`
2. `prompts/behaviors/*.md` (in sorted order)

This mirrors what `hooks-handlers/session-start.sh` does.

## Context Isolation

**Critical:** Test subagents must NOT be aware they are being tested. This prevents meta-awareness where the subagent recognizes it's in a test scenario and behaves differently.

**Isolation techniques:**
1. Use role-play framing ("You are a coding assistant...")
2. Provide complete simulated environment (don't reference real context)
3. Set working directory to test fixture (`tmp/bktide`), not real workspace
4. Don't mention "test", "scenario", "baseline", "treatment" in prompts

## TEST Subagent Prompt (Baseline)

```
ROLE: You are a coding assistant helping a developer.

ENVIRONMENT:
- Working directory: {cwd}
- This is the start of a new conversation

USER REQUEST:
{user_message}

YOUR TASK:
Respond to the user's request. This is a real development session - help them effectively.
```

## TEST Subagent Prompt (Treatment)

```
ROLE: You are a coding assistant helping a developer.

ENVIRONMENT:
- Working directory: {cwd}
- This is the start of a new conversation

ADDITIONAL INSTRUCTIONS:
{composed_stay_on_target_prompt}

---

USER REQUEST:
{user_message}

YOUR TASK:
Respond to the user's request following the additional instructions above. This is a real development session - help them effectively.
```

## Dispatching Subagents

Use the Task tool with:
- `subagent_type: "general-purpose"`
- `model: "sonnet"` (fast iteration)
- Capture the full response

**Important:** The prompt must be self-contained. Don't reference "the scenario" or "this test" - frame it as a real session.

## Parsing REVIEWER Output

Extract YAML block from reviewer response. Parse scores and rationale.

## Results Format

### Inline Output

```
stay-on-target self-test results
================================

Scenario: {name}
  Baseline → Treatment
  {criterion}:  {baseline_score} → {treatment_score}  ({delta})
  ...
  --------------------------
  Total:        {b_total} → {t_total}  ({delta})  {PASS/FAIL}

Summary: {passed}/{total} scenarios passed
Results saved to: test/results/{filename}.md
```

### File Output

Write full results including:
- Summary stats
- Per-scenario: baseline response, treatment response, scores, rationale

## Pass Criteria

A scenario passes if treatment total > baseline total.
