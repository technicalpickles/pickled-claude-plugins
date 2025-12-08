Run integration tests for the working-in-monorepos plugin.

## What This Tests

1. **Hook Configuration** - Validates hooks.json structure and patterns
2. **Script Execution** - Runs hooks with realistic stdin
3. **Skill Effectiveness** - Tests agent behavior in monorepo scenarios

## Full Mode (Default)

### Step 1: Run pytest tests

```bash
cd plugins/working-in-monorepos && uv run pytest tests/ -v
```

Report results and any failures. If tests fail, stop here.

### Step 2: Run subagent scenarios

Run scenarios from `skills/working-in-monorepos/tests/baseline-scenarios.md`:

1. Set up test monorepo in /tmp with structure:
   - /tmp/test-monorepo/
   - /tmp/test-monorepo/ruby/ (with Gemfile)
   - /tmp/test-monorepo/cli/ (with package.json)

2. For each scenario, dispatch a Task subagent with the scenario prompt

3. Evaluate: Did the agent use absolute paths?

4. Report pass/fail for each scenario

## Quick Mode (with --quick flag)

Run pytest tests only, skip subagent scenarios.

## Usage

```
/working-in-monorepos:validate           # Full mode - pytest + subagent tests
/working-in-monorepos:validate --quick   # Quick mode - pytest only
```
