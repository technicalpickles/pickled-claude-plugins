#!/usr/bin/env bats

# Checks what the automic-vault skill tells agents against the real `av` CLI,
# and against an upstream source checkout when one is present. Local only:
# av is macOS-only and needs the app, so every test skips without it.
#
# Source checkout: AV_SOURCE_DIR, default ~/github.com/automic-vault/automic-vault.
# Only read-only av commands run here. inject/save/harden/unharden are never executed.

PLUGIN_DIR="$BATS_TEST_DIRNAME/.."
SKILLS="$PLUGIN_DIR"/skills/*/SKILL.md

setup() {
  command -v av >/dev/null 2>&1 || skip "av not installed"
  command -v jq >/dev/null 2>&1 || skip "jq not installed"
  SRC="${AV_SOURCE_DIR:-$HOME/github.com/automic-vault/automic-vault}"
}

need_source() {
  [ -f "$SRC/src/cli/mod.rs" ] || skip "no av source checkout at $SRC"
}

# Subcommands the plugin's skills name in backticks, e.g. `av inject +NAME` -> inject.
skill_subcommands() {
  # shellcheck disable=SC2086
  grep -ohE '`av [a-z][a-z-]*' $SKILLS | sed 's/^`av //' | sort -u
}

# Subcommands listed in a usage block on stdin: lines like "  $ av scan ...".
usage_subcommands() {
  grep -oE '^  \$ av [a-z][a-z-]*' | sed 's/^  \$ av //' | sort -u
}

@test "version: installed av vs source checkout (informational)" {
  need_source
  installed="$(av --version | awk '{print $2}')"
  source_version="$(grep -m1 '^version' "$SRC/Cargo.toml" | sed 's/.*"\(.*\)"/\1/')"
  echo "# installed av $installed, source $source_version" >&3
  [ -n "$installed" ]
  [ -n "$source_version" ]
}

@test "every av subcommand in the skill appears in installed av help" {
  available="$(av help | usage_subcommands)"
  for cmd in $(skill_subcommands); do
    echo "$available" | grep -qx "$cmd" || { echo "skill names 'av $cmd', not in av help"; return 1; }
  done
}

@test "every av subcommand in the skill appears in the source USAGE block" {
  need_source
  available="$(sed -n '/^const USAGE/,/\$";$/p' "$SRC/src/cli/mod.rs" | usage_subcommands)"
  [ -n "$available" ]
  for cmd in $(skill_subcommands); do
    echo "$available" | grep -qx "$cmd" || { echo "skill names 'av $cmd', not in source USAGE"; return 1; }
  done
}

@test "av settings list --json has the documented shape" {
  run av settings list --json
  [ "$status" -eq 0 ]
  echo "$output" | jq -e 'type == "array" and length > 0 and all(.[]; has("key") and has("value") and has("defaultValue") and has("acceptedValues") and has("requiresApproval"))'
}

@test "av settings keys match the source's closed catalog" {
  need_source
  cli_keys="$(av settings list --json | jq -r '.[].key' | sort)"
  src_keys="$(grep -oE 'case [A-Za-z]+ = "[a-z-]+"' "$SRC/src/menu-helper/Sources/MenubarHelperCore/PresentationSettings.swift" | sed 's/.*"\(.*\)"/\1/' | sort)"
  [ -n "$src_keys" ]
  [ "$cli_keys" = "$src_keys" ]
}

@test "read-only commands the skill recommends run" {
  run av list
  [ "$status" -eq 0 ]
  run av hardeners --json
  [ "$status" -eq 0 ]
  echo "$output" | jq -e . >/dev/null
  run av history --json --since 1h --no-pager
  [ "$status" -eq 0 ]
}
