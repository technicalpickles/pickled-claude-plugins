#!/usr/bin/env bash
#
# Flags bash 4+ constructs in the repo's shell scripts.
#
# macOS ships /bin/bash 3.2, and `#!/usr/bin/env bash` can resolve to it even
# when a newer Homebrew bash is installed. Scripts here must run on 3.2, so this
# check rejects the constructs that don't (e.g. `declare -A` fails there with
# `declare: -A: invalid option`).
#
# Usage:
#   ./scripts/check-bash-compat.sh            # Check all tracked shell scripts
#   ./scripts/check-bash-compat.sh FILE...    # Check specific files
#
# Scans tracked *.sh / *.bash files plus any tracked file with a bash or sh
# shebang. Comment lines are ignored. To allow a match on purpose (e.g. the
# construct is inside a heredoc, or the script checks the bash version first),
# append `# bash-compat: allow` to the line.
#
# Not caught here: expanding an empty array (`"${arr[@]}"`) under `set -u`,
# which errors with "unbound variable" on bash < 4.4. Guard it with a length
# check or `${arr[@]+"${arr[@]}"}`.
#

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# This script and its tests quote the constructs they look for
EXCLUDE="scripts/check-bash-compat.sh
tests/scenarios/test-bash-compat.sh"
ALLOW_MARKER="bash-compat: allow"

cd "$REPO_ROOT"

# List tracked shell scripts: by extension, or by a bash/sh shebang.
list_shell_files() {
    {
        git ls-files -- '*.sh' '*.bash'
        # file:line:content; keep files whose shebang is on line 1
        git grep -nI -E '^#!.*([/ ]bash|[/ ]sh)([[:space:]]|$)' -- ':!*.sh' ':!*.bash' \
            | while IFS= read -r match; do
                [[ "$match" == *:1:* ]] && echo "${match%%:1:*}"
            done
    } | grep -vxF "$EXCLUDE" | sort -u
}

FILES=()
if [[ $# -gt 0 ]]; then
    FILES=("$@")
else
    while IFS= read -r f; do
        [[ -f "$f" ]] && FILES+=("$f")
    done < <(list_shell_files)
fi

if [[ ${#FILES[@]} -eq 0 ]]; then
    echo "No shell scripts to check."
    exit 0
fi

violations=0

# check <extended-regex> <description>
check() {
    local regex="$1"
    local desc="$2"
    local matches match content

    matches=$(grep -nHE -e "$regex" -- "${FILES[@]}" 2>/dev/null) || return 0

    # Each match is file:line:content. Skip comment lines and allowed lines.
    # Filtered in-shell rather than with more greps: each process spawn adds up.
    while IFS= read -r match; do
        content="${match#*:}"
        content="${content#*:}"
        content="${content#"${content%%[![:space:]]*}"}"
        [[ "$content" == \#* ]] && continue
        [[ "$match" == *"$ALLOW_MARKER"* ]] && continue
        echo "$match"
        echo "    ^ $desc"
        violations=$((violations + 1))
    done <<< "$matches"
}

check '(declare|typeset|local)[[:space:]]+-[a-zA-Z]*A' \
    'associative array (bash 4.0+); use parallel indexed arrays or a delimited string'
check '(^|[^[:alnum:]_-])(mapfile|readarray)([[:space:]]|$)' \
    'mapfile/readarray (bash 4.0+); use a `while IFS= read -r` loop'
check '(declare|typeset|local)[[:space:]]+-[a-zA-Z]*n' \
    'nameref (bash 4.3+)'
check '(declare|typeset)[[:space:]]+-[a-zA-Z]*g' \
    'declare -g (bash 4.2+)'
check '\$\{[A-Za-z_][A-Za-z0-9_]*(\[[^]]*\])?(\^\^?|,,?)\}' \
    'case modification ${var^^} / ${var,,} (bash 4.0+); use tr'
check '\$\{[A-Za-z_][A-Za-z0-9_]*(\[[^]]*\])?@[A-Za-z]\}' \
    'parameter transformation ${var@X} (bash 4.4+)'
check '\$\{[A-Za-z_][A-Za-z0-9_]*\[-[0-9]+\]\}' \
    'negative array index (bash 4.3+)'
check '\$\{[A-Za-z_][A-Za-z0-9_]*:[^}:]*:[[:space:]]*-[0-9]' \
    'negative substring length ${var:0:-1} (bash 4.2+)'
check '\[\[[[:space:]]+-v[[:space:]]' \
    '[[ -v var ]] (bash 4.2+); use [[ -n "${var+x}" ]]'
check ';;&|(^|[^;&]);&[[:space:]]*$' \
    'case fallthrough ;& / ;;& (bash 4.0+)'
check '(^|[^|])[|]&' \
    '|& pipe (bash 4.0+); use 2>&1 |'
check '&>>' \
    '&>> redirect (bash 4.0+); use >>file 2>&1'
check '(^|[^[:alnum:]_])coproc([[:space:]]|$)' \
    'coproc (bash 4.0+)'
check 'wait[[:space:]]+-n' \
    'wait -n (bash 4.3+)'
check '%\([^)]*\)T' \
    "printf '%(fmt)T' (bash 4.2+); use date"
check '\{[A-Za-z_][A-Za-z0-9_]*\}[<>]' \
    '{var}> fd allocation (bash 4.1+)'
check '\{[0-9]+\.\.[0-9]+\.\.[0-9]+\}' \
    'brace expansion step {a..b..n} (bash 4.0+); use seq'
check 'shopt[[:space:]]+-s[[:space:]].*(globstar|lastpipe|autocd|checkjobs|dirspell|direxpand|globasciiranges|assoc_expand_once|localvar_inherit)' \
    'shopt option not in bash 3.2'
check '(EPOCHSECONDS|EPOCHREALTIME|BASH_ARGV0|SRANDOM)' \
    'variable not in bash 3.2 (bash 5.0+)'

if [[ $violations -gt 0 ]]; then
    echo ""
    echo "Found $violations bash 4+ construct(s). Scripts must run on bash 3.2 (macOS /bin/bash)."
    echo "Rewrite them portably, or append '# $ALLOW_MARKER' to a line you've made safe."
    exit 1
fi

echo "✓ ${#FILES[@]} shell scripts are bash 3.2 compatible."
