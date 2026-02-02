# hk Built-in Linters Reference

hk provides 90+ pre-configured linters via `Builtins.pkl`.

## Usage

```pkl
import "package://github.com/jdx/hk/releases/download/v1.35.0/hk@1.35.0#/Builtins.pkl"

hooks {
  ["pre-commit"] {
    steps {
      ["prettier"] = Builtins.prettier
    }
  }
}
```

## Quick Reference by Language

| Language | Builtins |
|----------|----------|
| JavaScript/TypeScript | `prettier`, `eslint`, `biome`, `deno`, `tsc`, `standard_js`, `ox_lint`, `xo` |
| Python | `black`, `ruff`, `ruff_format`, `mypy`, `pylint`, `flake8`, `isort` |
| Go | `go_fmt`, `golangci_lint`, `go_vet`, `go_imports`, `staticcheck` |
| Rust | `cargo_fmt`, `cargo_clippy`, `cargo_check`, `rustfmt` |
| Ruby | `rubocop`, `standard_rb`, `reek`, `sorbet`, `brakeman` |
| Shell | `shellcheck`, `shfmt` |
| CSS | `stylelint`, `prettier` |
| YAML | `yamllint`, `yamlfmt`, `prettier` |
| JSON | `prettier`, `biome`, `jq` |
| TOML | `taplo`, `taplo_format`, `tombi` |
| Markdown | `markdown_lint`, `prettier`, `rumdl` |
| SQL | `sql_fluff` |
| Terraform | `terraform`, `tf_lint`, `tofu` |
| Nix | `alejandra`, `nix_fmt`, `nixpkgs_format` |
| Docker | `hadolint` |
| Proto | `buf_lint`, `buf_format` |

## Validation & Security

| Builtin | Purpose |
|---------|---------|
| `check_conventional_commit` | Enforce conventional commit format |
| `check_merge_conflict` | Detect merge conflict markers |
| `check_added_large_files` | Prevent large file commits |
| `detect_private_key` | Detect private keys in commits |
| `check_case_conflict` | Detect case-insensitive conflicts |
| `check_symlinks` | Validate symbolic links |
| `check_executables_have_shebangs` | Ensure scripts have shebangs |
| `no_commit_to_branch` | Prevent commits to protected branches |

## Formatting & Whitespace

| Builtin | Purpose |
|---------|---------|
| `trailing_whitespace` | Fix trailing whitespace |
| `newlines` | Fix end-of-file newlines |
| `mixed_line_ending` | Fix mixed line endings |
| `byte_order_marker` | Remove BOM markers |
| `fix_smart_quotes` | Convert smart quotes to ASCII |

## Multi-Language Formatters

| Builtin | Languages |
|---------|-----------|
| `prettier` | JS, TS, CSS, HTML, JSON, YAML, MD, GraphQL, Vue, Svelte |
| `biome` | JS, TS, JSON |
| `dprint` | Multiple (configurable) |
| `editorconfig_checker` | All (validates .editorconfig) |

## Commonly Used Builtins

### prettier
- **Glob:** `*.js`, `*.ts`, `*.css`, `*.json`, `*.yaml`, `*.md`, etc.
- **Check:** `prettier --check {{files}}`
- **Fix:** `prettier --write {{files}}`

### eslint
- **Glob:** `*.js`, `*.jsx`, `*.ts`, `*.tsx`
- **Check:** `eslint {{files}}`
- **Fix:** `eslint --fix {{files}}`

### black
- **Glob:** `*.py`
- **Check:** `black --check {{files}}`
- **Fix:** `black {{files}}`

### ruff
- **Glob:** `*.py`, `*.pyi`
- **Check:** `ruff check --force-exclude {{files}}`
- **Fix:** `ruff check --force-exclude --fix {{files}}`

### golangci_lint
- **Glob:** `*.go`
- **Check:** `golangci-lint run --fix=false {{files}}`
- **Fix:** `golangci-lint run --fix {{files}}`

### cargo_clippy
- **Glob:** `*.rs`
- **Check:** `cargo clippy --manifest-path {{workspace_indicator}} --quiet`
- **Fix:** `cargo clippy --manifest-path {{workspace_indicator}} --fix --allow-dirty --allow-staged --quiet`

### shellcheck
- **Glob:** `*.sh`, `*.bash`
- **Check:** `shellcheck {{files}}`

### check_conventional_commit
- **Hook:** commit-msg
- **Check:** `hk util check-conventional-commit {{commit_msg_file}}`

### typos
- **Glob:** `*`
- **Check:** `typos --diff {{files}}`
- **Fix:** `typos --write-changes {{files}}`

## Customizing Builtins

```pkl
// Override glob patterns
["prettier"] = (Builtins.prettier) {
  glob = List("src/**/*.js", "src/**/*.ts")
}

// Add dependencies
["eslint"] = (Builtins.eslint) {
  depends = "prettier"
}

// Set profile requirement
["mypy"] = (Builtins.mypy) {
  profiles = List("slow")
}

// Workspace-specific
["cargo_clippy"] = (Builtins.cargo_clippy) {
  workspace_indicator = "Cargo.toml"
}
```

## Full List

Run `hk builtins` to see all available builtins with their configurations.
