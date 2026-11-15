#!/usr/bin/env bats

SCRIPT="$BATS_TEST_DIRNAME/../survey-inbox.py"

setup() {
  INBOX="$BATS_TEST_TMPDIR/inbox"
  mkdir -p "$INBOX" "$BATS_TEST_TMPDIR/config/projects/-Users-me-code-repo"
  touch "$BATS_TEST_TMPDIR/config/projects/-Users-me-code-repo/aaaa1111-2222-3333-4444-555566667777.jsonl"
  export CLAUDE_CONFIG_DIR="$BATS_TEST_TMPDIR/config"
}

note() {
  printf '%s\n' "$2" > "$INBOX/$1"
}

bucket_of() {
  python3 "$SCRIPT" "$INBOX" | jq -r --arg f "$1" '.next | to_entries[] | select(any(.value[]; .file == $f)) | .key'
}

@test "a seedling capture goes straight to routing and keeps its status" {
  note "202611010900 glide.md" $'---\nstatus: seedling\n---\n\n# Glide\n\nA browser.'
  [ "$(bucket_of '202611010900 glide.md')" = "route-keep-status" ]
}

@test "a lifecycle status like filed also routes as-is" {
  note "202611010900 old.md" $'---\nstatus: filed\n---\n\n# Old\n\nBody.'
  [ "$(bucket_of '202611010900 old.md')" = "route-keep-status" ]
}

@test "a note with no status that is not a session note routes as-is" {
  note "202611010900 rlm.md" $'---\nsource: https://example.com\n---\n\n# RLM\n\nBody.'
  [ "$(bucket_of '202611010900 rlm.md')" = "route-keep-status" ]
}

@test "pipeline statuses map to their next stage" {
  note "1.md" $'---\nstatus: ingested\ntype: insight\n---\n\nBody.'
  note "2.md" $'---\nstatus: pending-review\n---\n\nBody.'
  note "3.md" $'---\nstatus: connected\n---\n\nBody.'
  [ "$(bucket_of 1.md)" = "enrich" ]
  [ "$(bucket_of 2.md)" = "route" ]
  [ "$(bucket_of 3.md)" = "link-daily" ]
}

@test "a status outside every vocabulary is reported, not guessed" {
  note "w.md" $'---\nstatus: wip\n---\n\n# W\n\nBody.'
  [ "$(bucket_of w.md)" = "unknown-status" ]
}

@test "a title-only stub is flagged empty whatever its frontmatter says" {
  note "202611030000 test.md" '# test'
  note "202611030001 stub.md" $'---\nstatus: seedling\n---\n\n# Untitled\n'
  [ "$(bucket_of '202611030000 test.md')" = "empty" ]
  [ "$(bucket_of '202611030001 stub.md')" = "empty" ]
}

@test "a raw session note whose transcript is on disk is ingested" {
  note "s.md" $'---\nsource: claude-code session aaaa1111 (repo, branch main)\nstatus: raw\ntype: session-notes\n---\n\n- a bullet'
  [ "$(bucket_of s.md)" = "ingest" ]
}

@test "a raw session note from another machine is held, with the session id" {
  note "s.md" $'---\nsession-id: bbbb1111-2222-3333-4444-555566667777\nstatus: raw\ntype: session-notes\n---\n\n- a bullet'
  [ "$(bucket_of s.md)" = "session-not-on-disk" ]
  run python3 "$SCRIPT" "$INBOX"
  [ "$(printf '%s' "$output" | jq -r '.next["session-not-on-disk"][0].session')" = "bbbb1111-2222-3333-4444-555566667777" ]
}

@test "a session note with a malformed session id is held" {
  note "s.md" $'---\nsource: claude-code session local_bc (repo, branch main)\nstatus: raw\ntype: session-notes\n---\n\n- a bullet'
  run python3 "$SCRIPT" "$INBOX"
  [ "$(printf '%s' "$output" | jq -r '.next["session-not-on-disk"][0].reason')" = "malformed session id" ]
}

@test "a session note that names no session is ingested as before" {
  note "s.md" $'---\nsource-session: some topic\nstatus: raw\ntype: session-notes\n---\n\n- a bullet'
  [ "$(bucket_of s.md)" = "ingest" ]
}

@test "the transcript lookup honors a CLAUDE_CONFIG_DIR list" {
  note "s.md" $'---\nsource: claude-code session aaaa1111 (repo, branch main)\nstatus: raw\ntype: session-notes\n---\n\n- a bullet'
  CLAUDE_CONFIG_DIR="$BATS_TEST_TMPDIR/missing:$BATS_TEST_TMPDIR/config"
  [ "$(bucket_of s.md)" = "ingest" ]
}

@test "notes whose titles contain one another are paired as possible duplicates" {
  note "202610131258 rlm.md" $'---\nstatus: seedling\n---\n\n# Recursive Language Models\n\nBlog.'
  note "202610131259 rlm-paper.md" $'---\nstatus: seedling\n---\n\n# Recursive Language Models (paper)\n\nPaper.'
  note "202610131300 other.md" $'---\nstatus: seedling\n---\n\n# Language of birds\n\nBirds.'
  run python3 "$SCRIPT" "$INBOX"
  [ "$(printf '%s' "$output" | jq -c '.near_duplicates')" = '[["202610131258 rlm.md","202610131259 rlm-paper.md"]]' ]
}

@test "two notes split from one source are not duplicates" {
  note "a.md" $'---\nstatus: seedling\nsource: https://example.com/post\n---\n\n# Power words\n\nA.'
  note "b.md" $'---\nstatus: seedling\nsource: https://example.com/post\n---\n\n# Did you check\n\nB.'
  run python3 "$SCRIPT" "$INBOX"
  [ "$(printf '%s' "$output" | jq -c '.near_duplicates')" = '[]' ]
}

@test "session notes on the same project are not duplicates" {
  note "a.md" $'---\nstatus: raw\ntype: session-notes\n---\n\n# Session: come-on autofire planning\n\n- a'
  note "b.md" $'---\nstatus: raw\ntype: session-notes\n---\n\n# Session: come-on autofire planning and evals\n\n- b'
  run python3 "$SCRIPT" "$INBOX"
  [ "$(printf '%s' "$output" | jq -c '.near_duplicates')" = '[]' ]
}

@test "a note captured more than two weeks ago is stale" {
  note "202001010000 old.md" $'---\nstatus: seedling\ncaptured: 2020-01-01T00:00:00Z\n---\n\n# Old\n\nBody.'
  run python3 "$SCRIPT" "$INBOX"
  [ "$(printf '%s' "$output" | jq -r '.stale[0]')" = "202001010000 old.md" ]
}

@test "a short title inside several longer ones does not chain them together" {
  note "1.md" $'---\nstatus: seedling\n---\n\n# Claude Code\n\nA.'
  note "2.md" $'---\nstatus: seedling\n---\n\n# Claude Code hooks\n\nB.'
  note "3.md" $'---\nstatus: seedling\n---\n\n# Claude Code skills\n\nC.'
  run python3 "$SCRIPT" "$INBOX"
  [ "$(printf '%s' "$output" | jq -c '.near_duplicates')" = '[["1.md","2.md"],["1.md","3.md"]]' ]
}

@test "two notes with the same one-word title are duplicates" {
  note "1.md" $'---\nstatus: seedling\n---\n\n# Kubernetes\n\nA.'
  note "2.md" $'---\nstatus: seedling\n---\n\n# Kubernetes\n\nB.'
  run python3 "$SCRIPT" "$INBOX"
  [ "$(printf '%s' "$output" | jq -c '.near_duplicates')" = '[["1.md","2.md"]]' ]
}

@test "a note whose body is tag-led lines is not empty" {
  note "t.md" $'---\nstatus: seedling\n---\n\n# TIL\n\n#til Python sorts are stable'
  [ "$(bucket_of t.md)" = "route-keep-status" ]
}

@test "a split session original kept as a record is not sent to enrich" {
  note "s.md" $'---\nstatus: ingested\ntype: session-notes\n---\n\n- a bullet'
  [ "$(bucket_of s.md)" = "kept-record" ]
}

@test "a raw note that is not a session note is reported, not ingested" {
  note "r.md" $'---\nstatus: raw\n---\n\n# R\n\nBody.'
  [ "$(bucket_of r.md)" = "unknown-status" ]
}

@test "an inline comment after a status is ignored" {
  note "c.md" $'---\nstatus: seedling # fresh\n---\n\n# C\n\nBody.'
  [ "$(bucket_of c.md)" = "route-keep-status" ]
}

@test "a note that is not valid UTF-8 does not stop the survey" {
  printf -- '---\nstatus: seedling\n---\n\n# Caf\xe9\n\nBody.\n' > "$INBOX/l.md"
  run python3 "$SCRIPT" "$INBOX"
  [ "$status" -eq 0 ]
  [ "$(bucket_of l.md)" = "route-keep-status" ]
}

@test "a missing inbox fails with a one-line error" {
  run python3 "$SCRIPT" "$BATS_TEST_TMPDIR/nope"
  [ "$status" -ne 0 ]
  [[ "$output" == "survey-inbox: "* ]]
}
