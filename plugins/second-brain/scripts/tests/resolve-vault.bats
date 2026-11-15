#!/usr/bin/env bats

SCRIPT="$BATS_TEST_DIRNAME/../resolve-vault.sh"

setup() {
  ROOT=$(cd "$BATS_TEST_TMPDIR" && pwd -P)
  mkdir -p "$ROOT/primary/notes" "$ROOT/work" "$ROOT/code/project"
  export SB_VAULTS_JSON="[{\"name\":\"primary\",\"path\":\"$ROOT/primary\"},{\"name\":\"work\",\"path\":\"$ROOT/work\"}]"
  unset SB_NOTE_VAULT
}

@test "prints the vault that contains the directory" {
  run bash "$SCRIPT" "$ROOT/primary/notes"
  [ "$status" -eq 0 ]
  [ "$output" = "primary" ]
}

@test "matches the vault root itself" {
  run bash "$SCRIPT" "$ROOT/work"
  [ "$output" = "work" ]
}

@test "prints nothing outside every vault, so sb's default applies" {
  run bash "$SCRIPT" "$ROOT/code/project"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "SB_NOTE_VAULT overrides the directory match" {
  SB_NOTE_VAULT=work run bash "$SCRIPT" "$ROOT/primary/notes"
  [ "$output" = "work" ]
}

@test "does not match a sibling directory that shares a name prefix" {
  mkdir -p "$ROOT/primary-old"
  run bash "$SCRIPT" "$ROOT/primary-old"
  [ -z "$output" ]
}

@test "picks the deepest vault when vaults nest" {
  mkdir -p "$ROOT/primary/inner"
  SB_VAULTS_JSON="[{\"name\":\"primary\",\"path\":\"$ROOT/primary\"},{\"name\":\"inner\",\"path\":\"$ROOT/primary/inner\"}]" \
    run bash "$SCRIPT" "$ROOT/primary/inner"
  [ "$output" = "inner" ]
}

@test "follows symlinks to the vault's real path" {
  ln -s "$ROOT/work" "$ROOT/code/link"
  run bash "$SCRIPT" "$ROOT/code/link"
  [ "$output" = "work" ]
}
