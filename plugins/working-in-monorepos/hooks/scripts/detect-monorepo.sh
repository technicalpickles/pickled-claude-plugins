#!/usr/bin/env bash
# detect-monorepo.sh: SessionStart hook to detect monorepo structure

# Consume stdin (hook receives JSON input that we don't need)
cat > /dev/null

# Check if we're in a git repository
if ! git rev-parse --show-toplevel &>/dev/null; then
  exit 0
fi

REPO_ROOT=$(git rev-parse --show-toplevel)

# Check if .monorepo.json exists
if [[ -f "$REPO_ROOT/.monorepo.json" ]]; then
  # Monorepo configuration already exists
  num_subprojects=$(jq '.subprojects | length' "$REPO_ROOT/.monorepo.json" 2>/dev/null || echo "0")
  echo "✓ Monorepo detected: $num_subprojects subproject(s) configured in .monorepo.json"
  exit 0
fi

# Look for common monorepo indicators
artifact_count=$(find "$REPO_ROOT" -maxdepth 3 -type f \( \
  -name 'package.json' -o \
  -name 'Gemfile' -o \
  -name 'go.mod' -o \
  -name 'pyproject.toml' -o \
  -name 'Cargo.toml' -o \
  -name 'build.gradle' -o \
  -name 'pom.xml' \
  \) 2>/dev/null | wc -l | tr -d ' ')

# If we find multiple project artifacts, suggest monorepo initialization
if [[ "$artifact_count" -ge 2 ]]; then
  echo "Potential monorepo detected ($artifact_count project files found)"
  echo "Run /monorepo-init to configure subproject navigation"
fi
