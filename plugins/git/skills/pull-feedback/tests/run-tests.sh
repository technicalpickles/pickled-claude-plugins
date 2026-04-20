#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
FETCH="$SKILL_DIR/fetch.sh"
FIXTURES="$SCRIPT_DIR/fixtures"
GOLDEN="$SCRIPT_DIR/golden"

pass=0
fail=0

for graphql in "$FIXTURES"/*.json; do
  # Skip companion comments files
  case "$graphql" in
    *.comments.json) continue ;;
  esac

  name="$(basename "$graphql" .json)"
  comments="$FIXTURES/$name.comments.json"
  expected="$GOLDEN/$name.md"

  if [[ ! -f "$comments" ]]; then
    echo "SKIP $name (no .comments.json)"
    continue
  fi
  if [[ ! -f "$expected" ]]; then
    echo "SKIP $name (no golden)"
    continue
  fi

  actual_file=$(mktemp)
  "$FETCH" --render-only --graphql "$graphql" --comments "$comments" > "$actual_file"
  if diff -u "$expected" "$actual_file" > /dev/null; then
    echo "PASS $name"
    pass=$((pass + 1))
  else
    echo "FAIL $name"
    diff -u "$expected" "$actual_file" || true
    fail=$((fail + 1))
  fi
  rm -f "$actual_file"
done

echo
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
