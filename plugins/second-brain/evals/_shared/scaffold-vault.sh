#!/usr/bin/env bash
# Shared scaffold for second-brain eval cases. Runs in the eval's throwaway
# workspace (cwd = run cwd, HOME = run home) before the agent starts, with
# network; the agent's own sandbox has no npm registry access.
#
# Builds a small Obsidian vault at ./vault, points sb at it, installs sb
# locally so `npx @techpickles/sb` resolves offline, and drops fixtures.
set -euo pipefail
VAULT="$PWD/vault"
INBOX="10-19 System & Capture/11 Inbox & triage"

mkdir -p "$VAULT/.obsidian" "$VAULT/$INBOX" "$VAULT/Fleeting" "$VAULT/Templates" \
  "$VAULT/60-69 Software & Engineering" "$PWD/sources" "$PWD/.eval"
printf '{"newFileFolderPath": "%s"}\n' "$INBOX" > "$VAULT/.obsidian/app.json"
printf '{"folder": "Fleeting", "template": "Templates/daily"}\n' > "$VAULT/.obsidian/daily-notes.json"
printf -- '---\ntags: [daily]\n---\n\n## Links\n\n## Notes\n' > "$VAULT/Templates/daily.md"

mkdir -p "$HOME/.claude"
printf '# Second Brain Configuration\n\n## Vaults\n\n- test: %s\n\nDefault: test\n' "$VAULT" \
  > "$HOME/.claude/second-brain.md"

# A routed neighbor note in the legacy shape capture must NOT copy.
cat > "$VAULT/60-69 Software & Engineering/202601010000 astar.md" <<'NOTE'
---
type: reference
status: filed
tags: [#algorithms, #pathfinding]
created: 2026-01-01
---
# A* search

Best-first pathfinding using f(n) = g(n) + h(n) with an admissible heuristic.
NOTE

# A same-subject note capture should link to but never edit. Opt-in (set
# WITH_SAME_SUBJECT_NOTE=1 before sourcing): it triggers capture's strong-match
# stop, which would end any case that isn't testing it.
if [ "${WITH_SAME_SUBJECT_NOTE:-0}" = 1 ]; then
cat > "$VAULT/60-69 Software & Engineering/202605050000 roc-algorithm.md" <<'NOTE'
---
status: seedling
tags: [algorithms, pathfinding]
created: 2026-05-05
source: https://example.com/roc-intro
---
# Roc algorithm

Early notes on Roc, a hierarchical pathfinding algorithm.
NOTE
fi

# The source the capture cases hand over.
cat > "$PWD/sources/roc-article.md" <<'NOTE'
# Roc: a fast pathfinding algorithm

Roc trades a small amount of preprocessing time for large runtime speedups on
repeated pathfinding queries over the same map, using a hierarchical
decomposition of the search space. It was published in 2026 by Ada Example.

Features:
- Hierarchical map decomposition
- Incremental updates when the map changes
- Bounded-suboptimal paths with a tunable epsilon
- Parallel query batching

Implementations: the [Rust crate](https://example.com/roc-rs), a
[Python port](https://example.com/roc-py), and published
[benchmarks](https://example.com/roc-bench).
NOTE

# sb, installed locally so npx resolves it without the registry.
npm install --silent --no-audit --no-fund @techpickles/sb > /dev/null

# Wrap sb so every `note create` leaves a stable pointer at .eval/latest-note.md:
# eval file graders take fixed paths only, and sb's filenames are timestamped.
REAL_SB="$(readlink -f node_modules/.bin/sb)"
rm node_modules/.bin/sb
cat > node_modules/.bin/sb <<WRAP
#!/usr/bin/env bash
out="\$(node "$REAL_SB" "\$@")"; status=\$?
printf '%s\n' "\$out"
if [ "\$1 \$2" = "note create" ] && [ \$status -eq 0 ]; then
  path="\$(printf '%s' "\$out" | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{const j=JSON.parse(s);process.stdout.write(j.path||"")}catch{}})')"
  if [ -n "\$path" ]; then
    case "\$path" in /*) abs="\$path" ;; *) abs="$VAULT/\$path" ;; esac
    ln -sf "\$abs" "$PWD/.eval/latest-note.md"
  fi
fi
exit \$status
WRAP
chmod +x node_modules/.bin/sb
