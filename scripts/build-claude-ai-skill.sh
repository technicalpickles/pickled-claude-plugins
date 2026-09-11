#!/usr/bin/env bash
#
# Packages a claude.ai Skill (a plugin's claude-ai-skills/{name}/ directory) into an
# uploadable zip. claude.ai Skills are a separate product from this repo's Claude Code
# plugins - see plugins/{plugin}/claude-ai-skills/ and docs/claude-ai-skill-porting.md.
#
# Usage:
#   ./scripts/build-claude-ai-skill.sh <plugin> [skill-name ...]
#   ./scripts/build-claude-ai-skill.sh second-brain                # build every skill under second-brain
#   ./scripts/build-claude-ai-skill.sh second-brain vault-capture  # build just one
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <plugin> [skill-name ...]" >&2
  exit 1
fi

plugin="$1"
shift
skills_root="$REPO_ROOT/plugins/$plugin/claude-ai-skills"

if [ ! -d "$skills_root" ]; then
  echo "error: no claude-ai-skills directory at plugins/$plugin/claude-ai-skills" >&2
  exit 1
fi

dist_dir="$skills_root/dist"
mkdir -p "$dist_dir"

skills=("$@")
explicit=0
[ "${#skills[@]}" -gt 0 ] && explicit=1
if [ "${#skills[@]}" -eq 0 ]; then
  for dir in "$skills_root"/*/; do
    name="$(basename "$dir")"
    [ "$name" = "dist" ] && continue
    [ -f "$dir/SKILL.md" ] && skills+=("$name")
  done
fi

if [ "${#skills[@]}" -eq 0 ]; then
  echo "error: no skill directories with SKILL.md found under $skills_root" >&2
  exit 1
fi

for name in "${skills[@]}"; do
  skill_dir="$skills_root/$name"
  if [ ! -f "$skill_dir/SKILL.md" ]; then
    if [ "$explicit" -eq 1 ]; then
      echo "error: $name has no SKILL.md" >&2
      exit 1
    fi
    echo "skip: $name has no SKILL.md" >&2
    continue
  fi
  out="$dist_dir/$name.zip"
  rm -f "$out"
  (cd "$skill_dir" && zip -X -r "$out" . -x '.*' -x '*/.*')
  echo "built plugins/$plugin/claude-ai-skills/dist/$name.zip"
done
