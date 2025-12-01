---
title: "Glob pattern syntax | Buildkite Documentation"
meta:
  "og:description": "A glob pattern is a representation of a file name and optionally its path, and is a compact way of specifying multiple files with a single pattern. You can use a glob pattern to find all files in paths that match that pattern."
  "og:title": "Glob pattern syntax"
  description: "A glob pattern is a representation of a file name and optionally its path, and is a compact way of specifying multiple files with a single pattern. You can use a glob pattern to find all files in paths that match that pattern."
---

# Glob pattern syntax

A glob pattern is a representation of a file name and optionally its path, and is a compact way of specifying multiple files with a single pattern. You can use a glob pattern to find all files in paths that match that pattern.

This syntax is used for glob patterns supported in pipelines for artifact uploads (using either [`artifact_paths`](https://buildkite.com/docs/pipelines/configure/step-types/command-step#command-step-attributes) in a pipeline or [`buildkite-agent artifact upload`](https://buildkite.com/docs/agent/v3/cli-pipeline)), and `if_changed` conditions on [command](https://buildkite.com/docs/pipelines/configure/step-types/command-step#agent-applied-attributes), [trigger](https://buildkite.com/docs/pipelines/configure/step-types/trigger-step#agent-applied-attributes) or [group](https://buildkite.com/docs/pipelines/configure/step-types/group-step#agent-applied-attributes) pipeline steps.

[Full path matching](#full-path-matching)

Glob patterns must match whole path strings, and cannot be used to represent substrings. However, glob patterns are evaluated relative to the current directory.

## [Syntax elements](#syntax-elements)

Characters match themselves only, with the following syntax elements having special meaning.

| Syntax element | Meaning |
| --- | --- |
| `\` | Used to _escape_ the next character in the pattern, preventing it from being treated as special syntax. An escaped character matches itself exactly. For example, `\*` matches `*` (_not_ zero or more arbitrary characters). Note that on Windows, `\` and `/` have swapped meanings. |
| `/` | The path separator. Separates segments of each path. Note that on Windows, `\` and `/` have swapped meanings. |
| `?` | Matches exactly one arbitrary character, except for the path separator `/`. |
| `*` | Matches zero or more arbitrary characters, except for the path separator `/`. Note that YAML strings starting with `*` must typically be quoted. |
| `**` | Matches zero or more arbitrary characters, including the path separator `/`. Since `**` can be used to mean zero or more path components, `/**/` also matches `/`. Note that YAML strings starting with `*` must typically be quoted. |
| `{,}` | `{a,b,cd}` matches `a` or `b` or `cd`. A component can be empty, e.g. `{,a,b}` matches either nothing or `a` or `b`. Multiple path segments, `*`, `**`, etc are all allowed within `{}`. To specify a path containing `,` within `{}`, escape it (that is, use `\,`). Note that patterns within braces remain whitespace-sensitive: `{a, b}` matches `a` and ` b` (a space followed by b), not `b`. |
| `[ ]` | `[abc]` matches single characters only (`a` or `b` or `c`). `[]` is a shorter way to write a match for a single character than `{,}`. Note that ranges are currently not supported. |
| `[^ ]` | `[^abc]` matches a single character _other than_ the listed characters. Note that ranges are currently not supported. |
| `~` | Prior to matching, `~` is expanded to the current user's home directory. Note that YAML typically interprets a single `~` as `null`. |

### [On Windows](#syntax-elements-on-windows)

The path separator on Windows is `\`, and therefore, `/` is the escape character when the agent performing the action is running on Windows. On other operating system platforms, `/` is the standard path separator and `\` is the standard escape character for the agent.

### [Character classes](#syntax-elements-character-classes)

Character classes (`[abc]`) and negated character classes (`[^abc]`) currently do _not_ support ranges, and `-` is treated literally. For example, `[c-g]` only matches one of `c`, `g`, or `-`.

## [Examples](#examples)

| Pattern | Explanation |
| --- | --- |
| `foo?.txt` | Matches files in the current directory whose names start with `foo`, followed by any one arbitrary character, and ending with `.txt`. |
| `foo*.txt` | Matches files in the current directory whose names start with `foo`, followed by any number of other characters, and ending with `.txt`. |
| `foo\?.txt` | Matches the file in the current directory named `foo?.txt`. |
| `log????.out` | Matches files in the current directory whose names start with `log`, followed by exactly four arbitrary characters, and ending with `.out`. |
| `log[^789]???.out` | Like `log????.out`, but the first character after `log` must not be `7`, `8`, or `9`. |
| `log???[16].out` | Like `log????.out`, but the last character before `.out` must be `1` or `6`. |
| `foo/*` | Matches all files within the `foo` directory only. |
| `foo/**` | Matches all files within the `foo` directory, as well as any subdirectory of `foo`. |
| `*.go` | Matches all Go files within the current directory only. |
| `**.go` | Matches all Go files within the current directory as well as any of its subdirectories. |
| `**/*.go` | Equivalent to `**.go`. |
| `foo/**.go` | Matches all Go files within the `foo` directory as well as any of its subdirectories. |
| `foo/**/*.go` | Equivalent to `foo/**.go`. |
| `foo/**/bar/*` | Matches all files in every subdirectory named `bar` anywhere within the `foo` directory (including, for example, both `foo/bar` and `foo/tmp/logs/bar`). |
| `{foo,bar}.go` | Matches the files `foo.go` and `bar.go` in the current directory. |
| `foo{,bar}.go` | Matches the files `foo.go` and `foobar.go` in the current directory. |
| `go.{mod,sum}` | Matches the files `go.mod` and `go.sum` in the current directory. |
| `**/go.{mod,sum}` | Matches `go.mod` and `go.sum` within the current directory as well as any of its subdirectories. |
| `{foo,bar}/**.go` | Matches all Go files within the `foo` directory, the `bar` directory, as well as any of their subdirectories. |
| `{foo/**.go,fixtures/**}` | Matches all Go files within the `foo` directory as well as its subdirectories, and all files within the `fixtures` directory as well as its subdirectories. |
| `side[AB]` | Matches the files `sideA` and `sideB` in the current directory. |
| `scale_[ABCDEFG]` | Matches the files `scale_A` through `scale_G` in the current directory. |
| `~/.bash_profile` | Matches the `.bash_profile` file in the current user's home directory. |