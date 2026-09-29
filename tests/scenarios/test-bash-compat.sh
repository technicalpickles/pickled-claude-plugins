#!/usr/bin/env bash
# Tests for scripts/check-bash-compat.sh
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT="$REPO_ROOT/scripts/check-bash-compat.sh"
fails=0
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# assert_flagged <label> <line of bash>: the lint rejects a file with this line
assert_flagged() {
  printf '#!/usr/bin/env bash\n%s\n' "$2" > "$tmp/case.sh"
  if "$SCRIPT" "$tmp/case.sh" >/dev/null 2>&1; then
    echo "  ✗ flags $1"; echo "    not flagged: $2"; fails=$((fails+1))
  else
    echo "  ✓ flags $1"
  fi
}

# assert_clean <label> <line of bash>: the lint accepts a file with this line
assert_clean() {
  printf '#!/usr/bin/env bash\n%s\n' "$2" > "$tmp/case.sh"
  if out="$("$SCRIPT" "$tmp/case.sh" 2>&1)"; then
    echo "  ✓ allows $1"
  else
    echo "  ✗ allows $1"; echo "    flagged: $2"; echo "$out" | sed 's/^/    /'; fails=$((fails+1))
  fi
}

echo "Test: bash 4+ constructs are flagged"
assert_flagged "declare -A" 'declare -A seen=()'
assert_flagged "local -A" '  local -A seen'
assert_flagged "declare -gA" 'declare -gA seen'
assert_flagged "mapfile" 'mapfile -t lines < file'
assert_flagged "readarray" 'readarray lines < file'
assert_flagged "nameref" 'local -n ref=$1'
assert_flagged "declare -g" 'declare -g FOO=1'
assert_flagged "uppercase" 'echo "${name^^}"'
assert_flagged "lowercase" 'echo "${name,,}"'
assert_flagged "array element case mod" 'echo "${arr[0]^}"'
assert_flagged "@Q transform" 'echo "${name@Q}"'
assert_flagged "negative index" 'echo "${arr[-1]}"'
assert_flagged "negative substring length" 'echo "${name:0:-1}"'
assert_flagged "[[ -v ]]" 'if [[ -v FOO ]]; then :; fi'
assert_flagged ";;&" '  a) echo a ;;&'
assert_flagged ";&" '  a) echo a ;&'
assert_flagged "|&" 'make |& tee log'
assert_flagged "&>>" 'make &>> log'
assert_flagged "coproc" 'coproc cat'
assert_flagged "wait -n" 'wait -n'
assert_flagged "printf %()T" "printf '%(%F)T' -1"
assert_flagged "{fd}> allocation" 'exec {fd}>file'
assert_flagged "brace step" 'echo {1..10..2}'
assert_flagged "globstar" 'shopt -s globstar'
assert_flagged "EPOCHSECONDS" 'echo "$EPOCHSECONDS"'

echo "Test: bash 3.2 constructs are allowed"
assert_clean "indexed array" 'arr=(a b); echo "${arr[@]}" "${#arr[@]}"'
assert_clean "default expansion" 'echo "${name:-x,}" "${name:+y}"'
assert_clean "negative offset" 'echo "${name: -1}"'
assert_clean "stderr pipe" 'make 2>&1 | tee log'
assert_clean "logical or" 'true || false'
assert_clean "&& chains" 'true && false'
assert_clean "case ;;" '  a) echo a ;;'
assert_clean "plain brace range" 'echo {1..10}'
assert_clean "declare -a" 'declare -a arr=()'
assert_clean "local -r" 'local -r x=1'
assert_clean "shopt nullglob" 'shopt -s nullglob'
assert_clean "comment line" '# declare -A is not allowed here'
assert_clean "indented comment" '    # mapfile would be nice'
assert_clean "allow marker" 'declare -A seen  # bash-compat: allow'

echo "Test: repo scripts are clean"
if out="$("$SCRIPT" 2>&1)"; then
  echo "  ✓ repo passes"
else
  echo "  ✗ repo passes"; echo "$out" | sed 's/^/    /'; fails=$((fails+1))
fi

echo ""
if [[ $fails -gt 0 ]]; then
  echo "$fails assertion(s) failed"
  exit 1
fi
echo "All assertions passed"
