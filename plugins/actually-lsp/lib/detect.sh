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
    if [[ "$ecosystem" == "typescript" ]]; then
      if ! find "$project_dir" -maxdepth 4 -type f \( -name "*.ts" -o -name "*.tsx" \) 2>/dev/null | head -1 | grep -q .; then
        continue
      fi
    fi

    echo "$ecosystem|$marker_path"
  done
}
