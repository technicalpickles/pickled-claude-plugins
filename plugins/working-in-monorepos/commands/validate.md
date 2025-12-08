Run integration tests for the working-in-monorepos plugin.

## What This Tests

1. **Hook Configuration** - Validates hooks.json structure and patterns
2. **Script Execution** - Runs hooks with realistic stdin
3. **Skill Effectiveness** - Tests agent behavior in monorepo scenarios

## Quick Mode (Default)

Run pytest tests only:

```bash
cd plugins/working-in-monorepos && uv run pytest tests/ -v
```

Report results and any failures.

## Full Mode (with --full flag)

Additionally run subagent scenarios from `skills/working-in-monorepos/tests/baseline-scenarios.md`:

1. Set up test monorepo in /tmp with structure:
   - /tmp/test-monorepo/
   - /tmp/test-monorepo/ruby/ (with Gemfile)
   - /tmp/test-monorepo/cli/ (with package.json)

2. For each scenario, dispatch a Task subagent with the scenario prompt

3. Evaluate: Did the agent use absolute paths?

4. Report pass/fail for each scenario

## Usage

```
/working-in-monorepos:validate           # Quick mode - pytest only
/working-in-monorepos:validate --full    # Full mode - includes subagent tests
```
