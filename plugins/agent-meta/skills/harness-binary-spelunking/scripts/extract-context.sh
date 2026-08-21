#!/usr/bin/env bash
# Print the context window around every match of an anchor in a strings
# dump, without going through grep's bounded-repetition engine.
#
# `grep -aoE '.{0,N}anchor.{0,N}'` is the recipe every reference file in this
# skill used to reach for. It fails two different ways depending on which
# grep is on PATH:
#   - BSD grep: "repetition-operator operand invalid" / "maximum repetition
#     count exceeds 255" once N gets past ~255.
#   - ugrep (common shim for `grep` on macOS): "exceeds complexity limits",
#     at a threshold that depends on the pattern, not just N.
# Both are the same root cause (bounded-repetition blowup in the regex
# engine), just different error strings -- which is exactly why grepping the
# docs for one message misses the other. Perl's regex engine has no such
# cap, so this script does the actual extraction in perl and sidesteps the
# whole class of failure rather than tuning N to dodge it.

set -euo pipefail

usage() {
  cat << EOF
Usage: $0 <anchor> <file> [width]

Print up to <width> characters of context on each side of every match of
<anchor> (an extended regex) in <file>.

Arguments:
  anchor   Extended regex to search for (e.g. 'autoAllowBashIfSandboxed')
  file     File to search (typically a strings dump from spelunk-init.sh)
  width    Characters of context per side. Default: 250.

Examples:
  $0 'autoAllowBashIfSandboxed' "\$TMPDIR/spelunk/claude/strings.txt"
  $0 'Auto-allowed with sandbox' "\$TMPDIR/spelunk/claude/strings.txt" 400
EOF
  exit 1
}

if [[ $# -lt 2 || $# -gt 3 ]]; then
  usage
fi

ANCHOR="$1"
FILE="$2"
WIDTH="${3:-250}"

if [[ ! -f "$FILE" ]]; then
  echo "error: no such file: $FILE" >&2
  exit 2
fi

# Cheap existence check first (plain grep, no bounded repetition -- this
# form never hits the 255/complexity limit) so a missing anchor fails fast
# with a clear message instead of perl silently printing nothing.
if ! grep -qE -- "$ANCHOR" "$FILE"; then
  echo "no matches for /$ANCHOR/ in $FILE" >&2
  exit 1
fi

ANCHOR="$ANCHOR" WIDTH="$WIDTH" FILE="$FILE" perl -e '
  my $anchor = $ENV{ANCHOR};
  my $width  = $ENV{WIDTH};
  local $/;
  open(my $fh, "<", $ENV{FILE}) or die $!;
  my $content = <$fh>;
  my $n = 0;
  while ($content =~ /(.{0,$width}$anchor.{0,$width})/gs) {
    $n++;
    print "--- match $n ---\n$1\n";
  }
  exit($n == 0 ? 1 : 0);
'
