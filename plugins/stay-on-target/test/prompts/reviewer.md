# Response Reviewer

You are evaluating an AI assistant's response to a user request.

## Your Task

Grade the response against the provided rubric criteria. For each criterion:
1. Assign a score (0, 1, or 2)
2. Provide a brief rationale (1 sentence)

## Rubric

{rubric}

## Criteria to Evaluate

{criteria}

## Expected Behaviors

{expected}

## Response to Evaluate

{response}

## Output Format

Respond with ONLY a YAML block:

```yaml
scores:
  criterion_name: score
  ...
rationale:
  criterion_name: "Brief explanation"
  ...
total: X/Y
```

Be strict but fair. Score based on what's actually in the response, not what might be implied.
