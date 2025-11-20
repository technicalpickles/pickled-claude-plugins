# Go Library Discovery

Progressive commands for exploring Go modules and finding current API documentation.

## Path Issues

If `go` command not found and using mise: `mise exec -- go <command>`

## Overview

| Level | Goal | Primary Commands |
|------|------|------------------|
| 🟢 Basic | Docs & version | `go doc`, `go list -m` |
| 🟡 Usage | Examples/tests | `grep` for examples in package |
| 🔵 Source | Source structure | `grep` definitions, `go doc -src` |

**Start with: docs → examples → source**

## 1️⃣ Basic: API Documentation

```bash
# Get version of installed package
go list -m github.com/spf13/cobra

# View package-level docs
go doc github.com/spf13/cobra

# View specific type/function docs
go doc github.com/spf13/cobra.Command
go doc github.com/spf13/cobra.Command.Flags
```

**Key insight:** `go doc` shows docs for the version in your `go.mod`, not latest or training data version.

## 2️⃣ Usage: Examples and Tests

```bash
# Find package installation path
path=$(go list -m -f '{{.Dir}}' github.com/spf13/cobra)

# Find example functions
grep -nR '^func Example' "$path"

# Search tests for usage patterns
grep -nRE 'Example|New|Marshal|Unmarshal' --include='*_test.go' "$path"
```

**Why examples matter:** Real usage patterns from the actual installed version.

## 3️⃣ Source: Deep Exploration

```bash
# Find package path
path=$(go list -m -f '{{.Dir}}' github.com/spf13/cobra)

# List source files
find "$path" -type f -name '*.go' -maxdepth 2 | head -n 50

# Find type and function definitions
grep -nR '^(type|func) ' "$path" --include='*.go'

# View function source
go doc -src github.com/spf13/cobra.Command.Flags
```

**When to go deep:** Examples unclear, docs incomplete, or complex API structure.

## Progressive Discovery Example

**Scenario:** Need to add flag to Cobra command, getting "unknown flag" errors.

```bash
# Step 1: Check version
go list -m github.com/spf13/cobra
# Output: github.com/spf13/cobra v1.8.1

# Step 2: View Command docs
go doc github.com/spf13/cobra.Command

# Step 3: Look for flag-related methods
go doc github.com/spf13/cobra.Command | grep -i flag

# Step 4: Check specific method
go doc github.com/spf13/cobra.Command.Flags

# Step 5: Find examples
path=$(go list -m -f '{{.Dir}}' github.com/spf13/cobra)
grep -nR 'Flags()' --include='*_test.go' "$path" | head -20
```

## Notes

- `go doc` respects your `go.mod` - shows docs for locked version
- `grep -nR` includes file + line numbers for easy navigation
- Check examples/tests before diving into source
- Package path from `go list -m -f '{{.Dir}}'` works in all environments
