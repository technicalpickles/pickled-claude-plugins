#!/bin/sh
# Fail if a parked file is too big for Claude's Read tool to load in one go.
#
# Read's default cap is 256 KB (262144 bytes). The limit here is 230 KB
# (235520 bytes, ~90%) so a handoff never lands right at the edge.
#
# Usage: check-size.sh FILE
# Exit:  0 under limit, 1 at or over limit, 2 bad usage / unreadable file

LIMIT_BYTES=235520

if [ $# -ne 1 ] || [ ! -f "$1" ]; then
  echo "usage: check-size.sh FILE" >&2
  exit 2
fi

size=$(wc -c < "$1" | tr -d ' ')

if [ "$size" -ge "$LIMIT_BYTES" ]; then
  echo "TOO LARGE: $1 is $size bytes (limit $LIMIT_BYTES, ~230 KB)" >&2
  exit 1
fi

echo "OK: $1 is $size bytes (limit $LIMIT_BYTES)"
