# Writing Language Reference Guides

This guide explains how to create new language-specific discovery references for this skill.

## Principles

- **Progressive context:** start tiny, expand only as needed: **docs → examples → source**.
- **Locked versions:** read from the project's lockfile; never assume "latest".
- **Non‑interactive by default:** no editors/pagers; output includes **file + line numbers**.
- **Built‑ins first:** prefer core tooling; third‑party optional/segregated.
- **Direct paths:** locate installed package path early, then operate within it.
- **Token‑lean:** terse overview table + minimal headings; commands over prose.
- **Portable:** shell‑only; avoid environment‑specific assumptions.

## Template Structure

Each language reference should follow this structure:

```markdown
# {{LANGUAGE}} Library Discovery

Progressive commands for exploring {{LANGUAGE}} packages and finding current API documentation.

## Path Issues

[How to handle common tooling/path issues for this ecosystem]

## Overview

| Level | Goal | Primary Commands |
|------|------|------------------|
| 🟢 Basic | Docs & version | [built-in doc tools] |
| 🟡 Usage | Examples/tests | [grep for examples] |
| 🔵 Source | Source structure | [grep definitions] |

**Start with: docs → examples → source**

## 1️⃣ Basic: API Documentation

```bash
# Get locked version
{{PKG_LIST_VERSION_CMD}} {{EXAMPLE_PKG}}

# View package-level docs
{{DOC_CMD}} {{EXAMPLE_PKG}}

# View specific symbol docs
{{DOC_CMD}} {{EXAMPLE_PKG}}.SymbolName
```

**Key insight:** Explain how the tooling respects lockfiles.

## 2️⃣ Usage: Examples and Tests

```bash
# Find package installation path
{{PATH_VAR}}=$({{PKG_PATH_CMD}} {{EXAMPLE_PKG}})

# Find example functions/files
grep -nR {{EXAMPLE_PATTERN}} "${{PATH_VAR}}"

# Search tests for usage patterns
grep -nRE {{TEST_PATTERNS}} "${{PATH_VAR}}"
```

**Why examples matter:** Real usage patterns from the actual installed version.

## 3️⃣ Source: Deep Exploration

```bash
# Find package path
{{PATH_VAR}}=$({{PKG_PATH_CMD}} {{EXAMPLE_PKG}})

# List source files
find "${{PATH_VAR}}/{{SRC_ROOT}}" -type f -maxdepth 2 | head -n 50

# Find type and function definitions
grep -nR {{DEF_PATTERNS}} "${{PATH_VAR}}"

# View function source (if tool supports)
{{DOC_SRC_CMD}} {{EXAMPLE_PKG}}.SymbolName
```

**When to go deep:** Examples unclear, docs incomplete, or complex API structure.

## Progressive Discovery Example

**Scenario:** [Realistic scenario for this ecosystem]

```bash
# Step-by-step walkthrough showing the progressive approach
```

## Notes

- Emphasize lockfile awareness
- Include line number flags
- Mention when to use each level
- Note any ecosystem-specific gotchas
```

## Placeholders to Fill

When creating a new language reference, replace these placeholders:

- `{{LANGUAGE}}` - Language name (e.g., "Go", "Ruby", "Python")
- `{{EXAMPLE_PKG}}` - Realistic package name (e.g., "github.com/spf13/cobra", "karafka")
- `{{PKG_LIST_VERSION_CMD}}` - Command to show locked version
- `{{PKG_PATH_CMD}}` - Command to get installation path
- `{{DOC_CMD}}` - Built-in documentation command
- `{{DOC_SRC_CMD}}` - Command to view source (if available)
- `{{PATH_VAR}}` - Shell variable for resolved path (often just `path`)
- `{{SRC_ROOT}}` - Source directory within package (e.g., `lib`, `src`, `pkg`)
- `{{EXAMPLE_PATTERN}}` - Pattern for finding examples
- `{{TEST_PATTERNS}}` - Patterns for finding tests
- `{{DEF_PATTERNS}}` - Patterns for finding definitions

## Examples

See existing references:
- `go.md` - Uses `go doc`, `go list`, respects `go.mod`
- `ruby.md` - Uses `bundle info`, `ri`, respects `Gemfile.lock`

## Testing Your Reference

1. Pick a real project using that language
2. Follow your own guide to discover an API
3. Verify each command produces useful output
4. Ensure output includes file + line numbers where helpful
5. Confirm lockfile versions are respected

## Design Goals

**Keep it minimal:**
- Users shouldn't load this unless extending the skill
- Language references should be self-contained
- Each step should take 30 seconds or less
- Output should be scannable, not overwhelming

**Make it progressive:**
- Level 1 (Basic) should answer 80% of questions
- Level 2 (Usage) for when docs aren't enough
- Level 3 (Source) only when absolutely necessary
- Each level builds on the previous one

**Make it accurate:**
- Never use commands that assume "latest" version
- Always show how to get the locked/installed version first
- Prefer built-in tools over third-party dependencies
- Test commands in isolated environments
