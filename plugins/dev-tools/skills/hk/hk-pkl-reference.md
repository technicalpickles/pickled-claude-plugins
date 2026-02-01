# hk.pkl Configuration Reference

## Basic Structure

```pkl
amends "package://github.com/jdx/hk/releases/download/v1.35.0/hk@1.35.0#/Config.pkl"
import "package://github.com/jdx/hk/releases/download/v1.35.0/hk@1.35.0#/Builtins.pkl"

hooks {
  ["pre-commit"] {
    fix = true       // Run fix commands (default: false)
    stash = "git"    // Stash unstaged changes
    steps {
      ["prettier"] = Builtins.prettier
      ["eslint"] = Builtins.eslint
    }
  }
}
```

The `amends` line is required - imports base configuration.

## Hook Types

| Hook | When it runs |
|------|--------------|
| `pre-commit` | Before commit is created |
| `commit-msg` | After commit message entered |
| `prepare-commit-msg` | Before commit message editor |
| `pre-push` | Before push to remote |
| `check` | Manual: `hk check` |
| `fix` | Manual: `hk fix` |

## Hook Options

```pkl
["pre-commit"] {
  fix = true           // Run fix commands (default: false)
  stage = true         // Auto-stage fixed files (default: true)
  stash = "git"        // Stash method: "git", "patch-file", "none"
  steps { ... }
}
```

## Step Definition

```pkl
["step-name"] {
  glob = List("*.js", "*.ts")    // Files to match
  check = "eslint {{files}}"     // Read-only command
  fix = "eslint --fix {{files}}" // Fix command
  batch = true                   // Parallel batching
  depends = "other-step"         // Run after dependency
  profiles = List("slow")        // Only with --profile slow
  exclude = List("vendor/**")    // Skip these files
}
```

### Template Variables

- `{{files}}` - List of files to process
- `{{workspace}}` - Workspace directory path
- `{{workspace_indicator}}` - Matched indicator file path
- `{{commit_msg_file}}` - Commit message file (commit-msg hook)

## Using Builtins

```pkl
// Use as-is
["prettier"] = Builtins.prettier

// Customize
["prettier"] = (Builtins.prettier) {
  glob = List("src/**/*.js")  // Override glob
  batch = false               // Disable batching
}
```

## Local Overrides

Create `hk.local.pkl` (gitignored) to override project config:

```pkl
amends "./hk.pkl"
import "./hk.pkl" as repo_config

hooks = (repo_config.hooks) {
  ["pre-commit"] {
    (steps) {
      ["custom-step"] = new Step { ... }
    }
  }
}
```

## Global Config (~/.hkrc.pkl)

```pkl
amends "package://github.com/jdx/hk/releases/latest/hk#/UserConfig.pkl"

jobs = 4
fail_fast = false
skip_steps = List("slow-test")
```

## Common Patterns

### Conventional Commits

```pkl
hooks {
  ["commit-msg"] {
    steps {
      ["conventional"] = Builtins.check_conventional_commit
    }
  }
}
```

### Monorepo Workspaces

```pkl
["eslint"] = (Builtins.eslint) {
  workspace_indicator = "package.json"
  check = "cd {{workspace}} && npm run lint -- {{workspace_files}}"
}
```

### Profiles for Slow Steps

```pkl
["mypy"] = (Builtins.mypy) {
  profiles = List("slow")  // Only runs with: hk check --slow
}
```

### Dependencies Between Steps

```pkl
["eslint"] = (Builtins.eslint) {
  depends = "prettier"  // Run after prettier
}
```

## Environment Variables

Set in config:
```pkl
env {
  ["NODE_ENV"] = "production"
}
```

Or per-step:
```pkl
["eslint"] {
  env { ["ESLINT_USE_FLAT_CONFIG"] = "true" }
}
```

## Real Example

From this repo's `hk.pkl`:

```pkl
amends "package://github.com/jdx/hk/releases/download/v1.35.0/hk@1.35.0#/Config.pkl"
import "package://github.com/jdx/hk/releases/download/v1.35.0/hk@1.35.0#/Builtins.pkl"

local validate_versions = new Step {
  check = "./scripts/validate-plugin-versions.sh"
}

local conventional_commit = (Builtins.check_conventional_commit) {}

hooks {
  ["pre-commit"] {
    steps {
      ["validate-versions"] = validate_versions
    }
  }
  ["commit-msg"] {
    steps {
      ["conventional-commit"] = conventional_commit
    }
  }
}
```
