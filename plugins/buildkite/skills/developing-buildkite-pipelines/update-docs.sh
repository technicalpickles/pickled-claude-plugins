#!/usr/bin/env bash
set -euo pipefail

# Update Buildkite pipeline configuration documentation
# This script fetches the latest docs from buildkite.com and converts them to markdown

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REFS_DIR="${SCRIPT_DIR}/references"
TEMP_OUTPUT="${SCRIPT_DIR}/.temp-output"

echo "=== Updating Buildkite Pipeline Documentation ==="

# Clean up previous temp output
rm -rf "${TEMP_OUTPUT}"

# Fetch latest docs from Buildkite
echo "Fetching docs from buildkite.com..."
npx @mdream/crawl \
  "https://buildkite.com/docs/pipelines/configure/**" \
  --skip-sitemap \
  --output "${TEMP_OUTPUT}" \
  --artifacts "markdown"

# Copy relevant docs to references directory
echo "Copying documentation to references/..."
mkdir -p "${REFS_DIR}"

# Copy core configuration docs
if [ -d "${TEMP_OUTPUT}/docs/pipelines/configure" ]; then
  cp -v "${TEMP_OUTPUT}/docs/pipelines/configure"/*.md "${REFS_DIR}/"

  # Also copy workflow subdirectory if it exists
  if [ -d "${TEMP_OUTPUT}/docs/pipelines/configure/workflows" ]; then
    mkdir -p "${REFS_DIR}/workflows"
    cp -v "${TEMP_OUTPUT}/docs/pipelines/configure/workflows"/*.md "${REFS_DIR}/workflows/"
  fi
fi

# Clean up temp output
rm -rf "${TEMP_OUTPUT}"

echo "=== Update complete ==="
echo "Documentation updated in: ${REFS_DIR}"
echo ""
echo "Key files:"
ls -lh "${REFS_DIR}"/*.md | awk '{print "  " $9}' | head -10
