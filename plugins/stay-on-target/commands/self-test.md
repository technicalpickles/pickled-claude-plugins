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
   b. Compose the stay-on-target prompt (read all prompt modules)
   c. Dispatch TEST subagent (baseline) - just the user message, no prompt injection
   d. Dispatch TEST subagent (treatment) - with stay-on-target prompt prepended
   e. Load rubric and reviewer prompt
   f. Dispatch REVIEWER subagent to grade baseline response
   g. Dispatch REVIEWER subagent to grade treatment response
   h. Record scores
3. **Write results** to `test/results/YYYY-MM-DD-HHMMSS.md`
4. **Print summary** showing baseline vs treatment delta

## Composing the Prompt

Read and concatenate:
1. `prompts/_base.md`
2. `prompts/behaviors/*.md` (in sorted order)

This mirrors what `hooks-handlers/session-start.sh` does.

## TEST Subagent Prompt (Baseline)

```
You are helping a developer with their codebase.

Working directory: {cwd}

The user says: {user_message}

Respond naturally as you would to help them.
```

## TEST Subagent Prompt (Treatment)

```
{composed_stay_on_target_prompt}

---

Working directory: {cwd}

The user says: {user_message}

Respond naturally as you would to help them.
```

## Dispatching Subagents

Use the Task tool with:
- `subagent_type: "general-purpose"`
- `model: "sonnet"` (fast iteration)
- Capture the full response

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
