# Finding Claude Sessions for Test Cases

How to find past Claude Code sessions that might contain good test scenarios for this skill.

## Search Strategies

### 1. Search Session History by Keywords

```bash
# Find sessions mentioning Colima
grep -r "colima" ~/.claude/projects/*/sessions/*.json 2>/dev/null | head -20

# Find sessions with Docker daemon errors
grep -r "Cannot connect to the Docker daemon" ~/.claude/projects/*/sessions/*.json 2>/dev/null

# Find sessions mentioning docker.sock
grep -r "docker.sock" ~/.claude/projects/*/sessions/*.json 2>/dev/null

# Find sessions with Docker context issues
grep -r "docker context" ~/.claude/projects/*/sessions/*.json 2>/dev/null
```

### 2. Search by Error Messages

Common error patterns that indicate Colima-related issues:

```bash
# Connection refused errors
grep -r "connection refused" ~/.claude/projects/*/sessions/*.json 2>/dev/null | grep -i docker

# Broken status
grep -r "Broken" ~/.claude/projects/*/sessions/*.json 2>/dev/null | grep -i colima

# Socket not found
grep -r "unix:///var/run/docker.sock" ~/.claude/projects/*/sessions/*.json 2>/dev/null
```

### 3. Recent Sessions in Specific Projects

```bash
# List recent session files, sorted by modification time
ls -lt ~/.claude/projects/*/sessions/*.json 2>/dev/null | head -20

# Find sessions from projects that likely use Docker
ls -lt ~/.claude/projects/*docker*/sessions/*.json 2>/dev/null
ls -lt ~/.claude/projects/*container*/sessions/*.json 2>/dev/null
```

## What to Look For

Good test case candidates have:

1. **Clear problem statement** - User describes a specific Docker/Colima issue
2. **Diagnostic steps** - Shows what commands were run to diagnose
3. **Resolution** - Documents what fixed the issue (or didn't)
4. **Edge cases** - Unusual scenarios or configurations

## Extracting Test Cases

When you find a relevant session:

1. Note the session file path
2. Extract the user's original question/problem
3. Document what the agent did (right or wrong)
4. Identify what the skill should have helped with
5. Add to `test-cases.md` following the RED/GREEN format

## Session JSON Structure

Sessions are stored as JSON with conversation turns:

```json
{
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

Use `jq` to extract readable content:

```bash
# Pretty print a session
cat ~/.claude/projects/foo/sessions/abc123.json | jq '.messages[] | {role, content}'

# Extract just user messages
cat ~/.claude/projects/foo/sessions/abc123.json | jq '.messages[] | select(.role=="user") | .content'
```
