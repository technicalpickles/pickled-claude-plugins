#!/usr/bin/env bash
# lib/detect.sh: ecosystem detection helpers for actually-lsp
# Sourced by hooks. Requires $ecosystems array (from lib/ecosystems.sh).

# detect_ecosystems <project_dir>
#   Walks the project dir for ecosystem markers.
#   Emits one line per detected ecosystem: "<ecosystem>|<marker_path>"
detect_ecosystems() {
  local project_dir="${1:-.}"
  local row ecosystem marker recommended_plugin server_binary env_check

  for row in "${ecosystems[@]}"; do
    IFS='|' read -r ecosystem marker recommended_plugin server_binary env_check <<< "$row"

    local marker_path="$project_dir/$marker"
    if [[ ! -f "$marker_path" ]]; then
      continue
    fi

    # TypeScript-specific check: package.json without any .ts/.tsx files in
    # the tree is not a TypeScript project (it's plain JavaScript).
    #
    # `-print -quit` stops find after the first match. Don't pipe to
    # `head -1`: under pipefail, the SIGPIPE find receives once its output
    # exceeds the OS pipe buffer (~64KB, hit by any project with
    # node_modules) flips the existence check and silently drops TypeScript.
    if [[ "$ecosystem" == "typescript" ]]; then
      if [[ -z "$(find "$project_dir" -maxdepth 4 -type f \( -name "*.ts" -o -name "*.tsx" \) -print -quit 2>/dev/null)" ]]; then
        continue
      fi
    fi

    echo "$ecosystem|$marker_path"
  done
}
