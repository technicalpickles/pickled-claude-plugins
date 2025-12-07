# Ruby Library Discovery

Progressive commands for exploring Ruby gems and finding current API documentation.

## Path Issues

If `bundle` command not found and using mise: `mise exec -- bundle <command>`

## Overview

| Level | Goal | Primary Commands |
|------|------|------------------|
| 🟢 Basic | Version & docs | `bundle info`, `ri` |
| 🟡 Usage | Examples/tests | `grep` for usage patterns |
| 🔵 Source | Source structure | `grep` definitions, `find lib/` |

**Start with: docs → examples → source**

## 1️⃣ Basic: Version and Documentation

```bash
# Get gem version and info
bundle info <gem>

# Get gem installation path
bundle info <gem> --path

# List all gems in bundle
bundle list

# Ruby documentation (if available)
ri ClassName
ri ClassName#method_name
```

**Note:** `ri` docs often missing (Bundler skips docs by default in many environments).

## 2️⃣ Usage: Examples and Tests

```bash
# Find gem path
path=$(bundle info <gem> --path)

# Search for usage examples in README
grep -nEi 'usage|example|readme' -R "$path"

# Find example directory
find "$path/examples" -type f -maxdepth 2 2>/dev/null

# Search test files for usage patterns
grep -nE 'describe |context |it\(' -R "$path" 2>/dev/null
```

**Why search tests:** Shows real usage patterns from the installed gem version.

## 3️⃣ Source: Deep Exploration

```bash
# Find gem path
path=$(bundle info <gem> --path)

# List main source files
find "$path/lib" -type f -maxdepth 2 | head -n 50

# Find module and class definitions
grep -nE '^(module|class) ' -R "$path/lib"

# Find method definitions
grep -nE '^\s*def ' -R "$path/lib"
```

**When to go deep:** Docs missing, examples unclear, or complex API.

## 4️⃣ Optional: Runtime Introspection

```bash
# Interactive exploration
bundle exec irb -r bundler/setup -r <gem>

# Command-line introspection
ruby -r bundler/setup -r <gem> -e 'p Module.const_get(:ClassName).instance_methods(false)'
```

**Use when:** Need to see actual methods available, not just source.

## Progressive Discovery Example

**Scenario:** Need to use Karafka consumer method, getting NoMethodError.

```bash
# Step 1: Check version
bundle info karafka
# Output: karafka (2.4.0)

# Step 2: Get gem path
path=$(bundle info karafka --path)

# Step 3: Find consumer examples
find "$path/examples" -name '*consumer*' 2>/dev/null

# Step 4: Search test files for usage
grep -nE 'consumer|consume' --include='*_spec.rb' -R "$path" | head -20

# Step 5: Check actual class methods
grep -nE 'class.*Consumer' -A 20 "$path/lib" | grep 'def '
```

## Notes

- Commands reflect **Gemfile.lock** versions, not latest or training data
- Works in CI, containers, or minimal shells
- `ri` often unavailable - rely on source/tests for docs
- `bundle info --path` is reliable across environments
