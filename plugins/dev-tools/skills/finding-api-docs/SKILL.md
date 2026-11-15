---
name: api-documentation-discovery
description: Use when APIs fail repeatedly with version-related errors (method not found, wrong arguments, unknown flag) or when about to use library APIs with uncertain knowledge - guides finding current, accurate documentation instead of guessing from training data
---

# API Documentation Discovery

## Overview

When an API call fails in a way that points at a version mismatch, look up the installed version's docs instead of retrying from memory. Training data ages; the installed version is the truth.

## When to Use

- Two or more failed attempts against the same library or API.
- Errors like "method not found", "wrong number of arguments", "unknown flag", "undefined method", or a version mismatch in a stack trace.
- You're about to rely on an API detail you haven't checked against the installed version, including one the user is sure of that keeps failing.

Skip it for a first failure whose error names the fix, and for errors that aren't about API usage (logic bugs, type errors in your own code).

## The Discovery Workflow

### Step 1: Stop retrying
Treat the trigger as the signal to look it up, not to try another variation.

### Step 2: Identify Context
- What library/framework is failing? (check imports, stack traces, go.mod/Gemfile)
- What version is installed? (language tools show this)
- What operation are you trying? (the actual goal, not the syntax attempt)

### Step 3: Use Language Discovery Tools
Check language-specific reference for HOW to discover documentation:
- `references/go.md` - Go module exploration
- `references/ruby.md` - Ruby gem exploration

Follow progressive discovery: **docs → examples → source**

### Step 4: Verify Before Using
- Found API signature? Verify it matches your use case
- Found example? Adapt it, don't just copy pattern from memory
- Found docs? Read them, don't skim for confirmation

## Common Anti-Patterns

| Rationalization | Reality |
|----------------|---------|
| "User is confident, syntax is probably right" | User confidence ≠ current API. Verify. |
| "Training data shows this pattern" | Training data ages. Check installed version. |
| "Let me try one more variation" | Guessing wastes time. Check docs now. |
| "This is documented somewhere" | Then go READ it before claiming confidence. |
| "Should be simple, just tweak syntax" | Simplicity bias. Use discovery tools. |
| "We've spent enough time on this" | Sunk cost fallacy. 2 min checking docs beats 20 min guessing. |

## Navigation: Language References

**Available language discovery guides:**
- `references/go.md` - Go: `go doc`, `go list`, example/test scanning
- `references/ruby.md` - Ruby: `bundle info`, `ri`, gem exploration

**Path issues:** If `go` or `bundle` isn't found, `mise exec -- <command>` is fine for a one-off doc lookup. If it keeps happening, it's a shell activation problem; see `dev-tools:working-with-mise`.

**Extending this skill:** To add a new language reference, see `references/WRITING.md` for principles and template.

## After Finding Documentation

1. **Verify**: API signature matches your use case
2. **Adapt**: Use the pattern for your specific need
3. **Test**: Try the verified approach
4. **Update understanding**: Note what changed from your training data
