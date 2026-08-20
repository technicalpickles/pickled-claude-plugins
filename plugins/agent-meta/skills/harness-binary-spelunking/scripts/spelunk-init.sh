#!/usr/bin/env bash
# Resolve a harness binary, classify its build, and dump strings once into a
# shared workspace under $TMPDIR so every recipe in this skill reads from the
# same place instead of each investigation inventing its own path/filename.

set -euo pipefail

usage() {
  cat << EOF
Usage: $0 <tool> [binary-path]

Set up (or reuse) the spelunking workspace for <tool>.

Arguments:
  tool          Name of the harness CLI (e.g. claude, codex, opencode)
  binary-path   Optional: the real binary to dump, if you've already
                followed a launcher/shim to its spawn target. If omitted,
                resolves via \`which <tool>\`.

If the resolved path is a launcher/shim (a script, not a real binary), this
prints the shim's content and exits without dumping anything -- follow the
spawn target by hand, then rerun with that path as <binary-path>. Chasing an
arbitrary spawn chain is a judgment call, not a mechanical step.

On success, prints the workspace directory and manifest. Every other script
and recipe in this skill assumes:
  \$TMPDIR/spelunk/<tool>/strings.txt   -- full strings dump
  \$TMPDIR/spelunk/<tool>/manifest.txt  -- tool, binary, build_type, sizes

Examples:
  $0 claude
  $0 codex ~/.local/share/mise/installs/node/22/.../codex-darwin-arm64/vendor/aarch64-apple-darwin/bin/codex
EOF
  exit 1
}

if [[ $# -lt 1 || $# -gt 2 ]]; then
  usage
fi

TOOL="$1"
WORKSPACE="${TMPDIR:-/tmp}/spelunk/$TOOL"
STRINGS_FILE="$WORKSPACE/strings.txt"
MANIFEST_FILE="$WORKSPACE/manifest.txt"

resolve_binary() {
  if [[ $# -eq 1 ]]; then
    echo "$1"
    return
  fi
  local which_path
  which_path="$(command -v "$TOOL" || true)"
  if [[ -z "$which_path" ]]; then
    echo "error: \`which $TOOL\` found nothing. Pass the binary path explicitly." >&2
    exit 2
  fi
  readlink -f "$which_path" 2>/dev/null || echo "$which_path"
}

if [[ $# -eq 2 ]]; then
  BIN="$(resolve_binary "$2")"
else
  BIN="$(resolve_binary)"
fi

if [[ ! -f "$BIN" ]]; then
  echo "error: resolved path does not exist: $BIN" >&2
  exit 2
fi

FILE_INFO="$(file -b "$BIN")"

# A shim/launcher is a script, not the artifact we want to classify or dump.
# Detecting "is this a shim" is mechanical; finding the spawn target inside
# it is not (it varies per tool, per platform) -- hand that back to the agent.
if [[ "$FILE_INFO" == *"script"* || "$FILE_INFO" == *"ASCII text"* || "$FILE_INFO" == *"text executable"* ]]; then
  echo "'$BIN' looks like a launcher/shim, not the real binary:"
  echo "  $FILE_INFO"
  echo
  echo "Contents:"
  cat "$BIN"
  echo
  echo "Find the spawn target above, then rerun: $0 $TOOL <spawn-target-path>"
  exit 3
fi

mkdir -p "$WORKSPACE"

BIN_SIZE="$(stat -f%z "$BIN" 2>/dev/null || stat -c%s "$BIN" 2>/dev/null)"

# Reuse an existing dump if it was made from this same binary (path + size
# match). Re-running `strings` over a 100-200MB+ binary on every session is
# the exact freelancing this script exists to avoid.
if [[ -f "$MANIFEST_FILE" ]] && grep -q "^binary=$BIN\$" "$MANIFEST_FILE" 2>/dev/null \
   && grep -q "^size_bytes=$BIN_SIZE\$" "$MANIFEST_FILE" 2>/dev/null \
   && [[ -f "$STRINGS_FILE" ]]; then
  echo "Reusing existing dump for $BIN (unchanged size $BIN_SIZE bytes)."
else
  echo "Dumping strings for $BIN ($BIN_SIZE bytes) -- this can take a few seconds..."
  strings "$BIN" > "$STRINGS_FILE"
fi

# Classify build type from markers in the dump. Bun markers win even when
# rust markers are also present: a Bun-compiled JS bundle can embed a native
# Rust addon (e.g. Claude Code ships a napi/tokio addon alongside its Bun
# runtime, so .cargo/registry hits alone are not decisive). Only fall
# through to "rust" when there's no Bun signal at all -- true of standalone
# Rust binaries like codex.
BUN_HITS="$(grep -c 'tmp_modules/bun\|oniguruma\|bun-internal' "$STRINGS_FILE" || true)"
RUST_HITS="$(grep -c '\.cargo/registry' "$STRINGS_FILE" || true)"

if [[ "${BUN_HITS:-0}" -gt 0 ]]; then
  BUILD_TYPE="bun-js"
elif [[ "${RUST_HITS:-0}" -gt 0 ]]; then
  BUILD_TYPE="rust"
else
  BUILD_TYPE="unknown"
fi

cat > "$MANIFEST_FILE" << EOF
tool=$TOOL
binary=$BIN
size_bytes=$BIN_SIZE
build_type=$BUILD_TYPE
bun_marker_hits=${BUN_HITS:-0}
rust_marker_hits=${RUST_HITS:-0}
strings_dump=$STRINGS_FILE
created_at=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
EOF

echo
echo "Workspace ready: $WORKSPACE"
echo "  binary:      $BIN"
echo "  build type:  $BUILD_TYPE (bun markers: ${BUN_HITS:-0}, rust markers: ${RUST_HITS:-0})"
echo "  strings:     $STRINGS_FILE"
echo "  manifest:    $MANIFEST_FILE"
if [[ "$BUILD_TYPE" == "unknown" ]]; then
  echo
  echo "No bun or rust markers found. Check 'file $BIN' and read references/source-clone.md" \
       "-- this may be unbundled Node/readable source rather than something to spelunk."
fi
