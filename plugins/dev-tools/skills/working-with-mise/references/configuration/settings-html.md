---
title: "Settings | mise-en-place"
meta:
  description: "mise-en-place documentation"
---

# Settings [​](#settings)

The following is a list of all of mise's settings. These can be set via `mise settings key=value`, by directly modifying `~/.config/mise/config.toml` or local config, or via environment variables.

Some of them also can be set via global CLI flags.

## `activate_aggressive`[](#activate_aggressive)

- Type: `Bool`
- Env: `MISE_ACTIVATE_AGGRESSIVE`
- Default: `false`

Pushes tools' bin-paths to the front of PATH instead of allowing modifications of PATH after activation to take precedence. For example, if you have the following in your `mise.toml`:

```toml
[tools]
node = '20'
python = '3.12'
```

But you also have this in your `~/.zshrc`:

```sh
eval "$(mise activate zsh)"
PATH="/some/other/python:$PATH"
```

What will happen is `/some/other/python` will be used instead of the python installed by mise. This means you typically want to put `mise activate` at the end of your shell config so nothing overrides it.

If you want to always use the mise versions of tools despite what is in your shell config, set this to `true`. In that case, using this example again, `/some/other/python` will be after mise's python in PATH.

## `all_compile`[](#all_compile)

- Type: `Bool`
- Env: `MISE_ALL_COMPILE`
- Default: `false`

Default: false unless running NixOS or Alpine (let me know if others should be added)

Do not use precompiled binaries for all languages. Useful if running on a Linux distribution like Alpine that does not use glibc and therefore likely won't be able to run precompiled binaries.

Note that this needs to be setup for each language. File a ticket if you notice a language that is not working with this config.

## `always_keep_download`[](#always_keep_download)

- Type: `Bool`
- Env: `MISE_ALWAYS_KEEP_DOWNLOAD`
- Default: `false`

should mise keep downloaded files after installation

## `always_keep_install`[](#always_keep_install)

- Type: `Bool`
- Env: `MISE_ALWAYS_KEEP_INSTALL`
- Default: `false`

should mise keep install files after installation even if the installation fails

## `arch`[](#arch)

- Type: `string`
- Env: `MISE_ARCH`
- Default: `"x86_64" | "aarch64" | "arm" | "loongarch64" | "riscv64"`

Architecture to use for precompiled binaries. This is used to determine which precompiled binaries to download. If unset, mise will use the system's architecture.

## `auto_install`[](#auto_install)

- Type: `Bool`
- Env: `MISE_AUTO_INSTALL`
- Default: `true`

Automatically install missing tools when running `mise x`, `mise run`, or as part of the 'not found' handler.

## `auto_install_disable_tools`[](#auto_install_disable_tools)

- Type: `string[]`(optional)
- Env: `MISE_AUTO_INSTALL_DISABLE_TOOLS`(comma separated)
- Default: `None`

List of tools to skip automatically installing when running `mise x`, `mise run`, or as part of the 'not found' handler.

## `cache_prune_age`[](#cache_prune_age)

- Type: `Duration`
- Env: `MISE_CACHE_PRUNE_AGE`
- Default: `30d`

The age of the cache before it is considered stale. mise will occasionally delete cache files which have not been accessed in this amount of time.

Set to `0s` to keep cache files indefinitely.

## `color`[](#color)

- Type: `Bool`
- Env: `MISE_COLOR`
- Default: `true`

Use color in mise terminal output

## `default_config_filename`[](#default_config_filename)

- Type: `string`
- Env: `MISE_DEFAULT_CONFIG_FILENAME`
- Default: `mise.toml`

The default config filename read. `mise use` and other commands that create new config files will use this value. This must be an env var.

## `default_tool_versions_filename`[](#default_tool_versions_filename)

- Type: `string`
- Env: `MISE_DEFAULT_TOOL_VERSIONS_FILENAME`
- Default: `.tool-versions`

The default .tool-versions filename read. This will not ignore .tool-versions—use override_tool_versions_filename for that. This must be an env var.

## `disable_backends`[](#disable_backends)

- Type: `string[]`
- Env: `MISE_DISABLE_BACKENDS`(comma separated)
- Default: `[]`

Backends to disable such as `asdf` or `pipx`

## `disable_default_registry`[](#disable_default_registry)

- Type: `Bool`
- Env: `MISE_DISABLE_DEFAULT_REGISTRY`
- Default: `false`

Disable the default mapping of short tool names like `php` -> `asdf:mise-plugins/asdf-php`. This parameter disables only for the backends `vfox` and `asdf`.

## `disable_hints`[](#disable_hints)

- Type: `SetString`
- Env: `MISE_DISABLE_HINTS`
- Default: `[]`

Turns off helpful hints when using different mise features

## `disable_tools`[](#disable_tools)

- Type: `SetString`
- Env: `MISE_DISABLE_TOOLS`
- Default: `[]`

Tools defined in mise.toml that should be ignored

## `enable_tools`[](#enable_tools)

- Type: `SetString`
- Env: `MISE_ENABLE_TOOLS`
- Default: `[]`

Tools defined in mise.toml that should be used - all other tools are ignored

## `env`[](#env)

- Type: `string[]`
- Env: `MISE_ENV`(comma separated)
- Default: `[]`

Enables profile-specific config files such as `.mise.development.toml`. Use this for different env vars or different tool versions in development/staging/production environments. See [Configuration Environments](https://mise.jdx.dev/configuration/environments.html) for more on how to use this feature.

Multiple envs can be set by separating them with a comma, e.g. `MISE_ENV=ci,test`. They will be read in order, with the last one taking precedence.

## `env_file`[](#env_file)

- Type: `Path`(optional)
- Env: `MISE_ENV_FILE`
- Default: `None`

Path to a file containing environment variables to automatically load.

## `exec_auto_install`[](#exec_auto_install)

- Type: `Bool`
- Env: `MISE_EXEC_AUTO_INSTALL`
- Default: `true`

Automatically install missing tools when running `mise x`.

## `experimental`[](#experimental)

- Type: `Bool`
- Env: `MISE_EXPERIMENTAL`
- Default: `false`

Enables experimental features. I generally will publish new features under this config which needs to be enabled to use them. While a feature is marked as "experimental" its behavior may change or even disappear in any release.

The idea is experimental features can be iterated on this way so we can get the behavior right, but once that label goes away you shouldn't expect things to change without a proper deprecation—and even then it's unlikely.

Also, I very often will use experimental as a beta flag as well. New functionality that I want to test with a smaller subset of users I will often push out under experimental mode even if it's not related to an experimental feature.

If you'd like to help me out, consider enabling it even if you don't have a particular feature you'd like to try. Also, if something isn't working right, try disabling it if you can.

## `fetch_remote_versions_cache`[](#fetch_remote_versions_cache)

- Type: `Duration`
- Env: `MISE_FETCH_REMOTE_VERSIONS_CACHE`
- Default: `1h`

duration that remote version cache is kept for "fast" commands (represented by PREFER_STALE), these are always cached. For "slow" commands like `mise ls-remote` or `mise install`:

- if MISE_FETCH_REMOTE_VERSIONS_CACHE is set, use that - if MISE_FETCH_REMOTE_VERSIONS_CACHE is not set, use HOURLY

## `fetch_remote_versions_timeout`[](#fetch_remote_versions_timeout)

- Type: `Duration`
- Env: `MISE_FETCH_REMOTE_VERSIONS_TIMEOUT`
- Default: `20s`

Timeout in seconds for HTTP requests to fetch new tool versions in mise.

## `global_config_file`[](#global_config_file)

- Type: `Path`(optional)
- Env: `MISE_GLOBAL_CONFIG_FILE`
- Default: `None`

Path to the global mise config file. Default is `~/.config/mise/config.toml`. This must be an env var.

## `global_config_root`[](#global_config_root)

- Type: `Path`(optional)
- Env: `MISE_GLOBAL_CONFIG_ROOT`
- Default: `None`

Path which is used as `{{config_root}}` for the global config file. Default is `$HOME`. This must be an env var.

## `go_default_packages_file`[](#go_default_packages_file)

- Type: `Path`
- Env: `MISE_GO_DEFAULT_PACKAGES_FILE`
- Default: `~/.default-go-packages`

Path to a file containing default go packages to install when installing go

## `go_download_mirror`[](#go_download_mirror)

- Type: `string`
- Env: `MISE_GO_DOWNLOAD_MIRROR`
- Default: `https://dl.google.com/go`

Mirror to download go sdk tarballs from.

## `go_repo`[](#go_repo)

- Type: `Url`
- Env: `MISE_GO_REPO`
- Default: `https://github.com/golang/go`

URL to fetch go from.

## `go_set_gobin`[](#go_set_gobin)

- Type: `Bool`(optional)
- Env: `MISE_GO_SET_GOBIN`
- Default: `None`

Defaults to `~/.local/share/mise/installs/go/.../bin`. Set to `true` to override GOBIN if previously set. Set to `false` to not set GOBIN (default is `${GOPATH:-$HOME/go}/bin`).

## `go_set_gopath`[](#go_set_gopath)deprecated

- Type: `Bool`
- Env: `MISE_GO_SET_GOPATH`
- Default: `false`
- Deprecated: Use env._go.set_goroot instead.

[deprecated] Set to true to set GOPATH=~/.local/share/mise/installs/go/.../packages.

## `go_set_goroot`[](#go_set_goroot)

- Type: `Bool`
- Env: `MISE_GO_SET_GOROOT`
- Default: `true`

Sets GOROOT=~/.local/share/mise/installs/go/.../.

## `go_skip_checksum`[](#go_skip_checksum)

- Type: `Bool`
- Env: `MISE_GO_SKIP_CHECKSUM`
- Default: `false`

Set to true to skip checksum verification when downloading go sdk tarballs.

## `gpg_verify`[](#gpg_verify)

- Type: `Bool`(optional)
- Env: `MISE_GPG_VERIFY`
- Default: `None`

Use gpg to verify all tool signatures.

## `http_retries`[](#http_retries)

- Type: `integer`
- Env: `MISE_HTTP_RETRIES`
- Default: `0`

Uses an exponential backoff strategy. The duration is calculated by taking the base (10ms) to the n-th power.

## `http_timeout`[](#http_timeout)

- Type: `Duration`
- Env: `MISE_HTTP_TIMEOUT`
- Default: `30s`

Timeout in seconds for all HTTP requests in mise.

## `idiomatic_version_file_enable_tools`[](#idiomatic_version_file_enable_tools)

- Type: `SetString`
- Env: `MISE_IDIOMATIC_VERSION_FILE_ENABLE_TOOLS`
- Default: `[]`

By default, idiomatic version files are disabled. You can enable them for specific tools with this setting.

For example, to enable idiomatic version files for node and python:```
mise settings add idiomatic_version_file_enable_tools node
mise settings add idiomatic_version_file_enable_tools python
```

See [Idiomatic Version Files](https://mise.jdx.dev/configuration.html#idiomatic-version-files) for more information.

## `ignored_config_paths`[](#ignored_config_paths)

- Type: `string[]`
- Env: `MISE_IGNORED_CONFIG_PATHS`(colon separated)
- Default: `[]`

This is a list of config paths that mise will ignore.

## `jobs`[](#jobs)

- Type: `integer`
- Env: `MISE_JOBS`
- Default: `8`

How many jobs to run concurrently such as tool installs.

## `locked`[](#locked)

- Type: `Bool`
- Env: `MISE_LOCKED`
- Default: `false`

> [!NOTE] This setting requires both [lockfile](#lockfile) and [experimental](#experimental) to be enabled.

When enabled, `mise install` will fail if tools don't have pre-resolved URLs in the lockfile for the current platform. This prevents API calls to GitHub, aqua registry, etc. and ensures reproducible installations.

This is useful in CI/CD environments where you want to:- Avoid GitHub API rate limits - Ensure deterministic builds using pre-resolved URLs - Fail fast if the lockfile is incomplete

To generate lockfile URLs, run:```sh
mise lock
```

Equivalent to passing `--locked` to `mise install`.

## `lockfile`[](#lockfile)

- Type: `Bool`
- Env: `MISE_LOCKFILE`
- Default: `true`

> [!NOTE] This feature is [experimental](#experimental) and may change in the future.

Read/update lockfiles for tool versions. This is useful when you'd like to have loose versions in mise.toml like this:```toml
[tools]
node = "22"
gh = "latest"
```

But you'd like the versions installed to be consistent within a project. When this is enabled, mise will update mise.lock files next to mise.toml files containing pinned versions. When installing tools, mise will reference this lockfile if it exists and this setting is enabled to resolve versions.

The lockfiles are not created automatically. To generate them, run the following (assuming the config file is `mise.toml`):

```sh
touch mise.lock && mise install
```

The lockfile is named the same as the config file but with `.lock` instead of `.toml` as the extension, e.g.:- `mise.toml` -> `mise.lock`- `mise.local.toml` -> `mise.local.lock`- `.config/mise.toml` -> `.config/mise.lock`

## `netrc`[](#netrc)

- Type: `Bool`
- Env: `MISE_NETRC`
- Default: `true`

When enabled, mise will read credentials from the netrc file and apply HTTP Basic authentication for matching hosts. This is useful for accessing private artifact repositories like Artifactory or Nexus.

On Unix/macOS, the default path is `~/.netrc`. On Windows, mise looks for `%USERPROFILE%\_netrc` first, then falls back to `%USERPROFILE%\.netrc`.

The netrc file format is:```
machine artifactory.example.com
  login myuser
  password mytoken
```

You can also specify a custom netrc file path using the `netrc_file` setting.

## `netrc_file`[](#netrc_file)

- Type: `Path`(optional)
- Env: `MISE_NETRC_FILE`
- Default: `None`

Override the default netrc file path. This is useful if you want to use a different netrc file for mise or if your netrc file is in a non-standard location.

## `not_found_auto_install`[](#not_found_auto_install)

- Type: `Bool`
- Env: `MISE_NOT_FOUND_AUTO_INSTALL`
- Default: `true`

Set to false to disable the "command not found" handler to autoinstall missing tool versions. Disable this if experiencing strange behavior in your shell when a command is not found.

**Important limitation**: This handler only installs missing versions of tools that already have at least one version installed. mise cannot determine which tool provides a binary without having the tool installed first, so it cannot auto-install completely new tools.

This also runs in shims if the terminal is interactive.

## `os`[](#os)

- Type: `string`
- Env: `MISE_OS`
- Default: `"linux" | "macos" | "windows"`

OS to use for precompiled binaries.

## `override_config_filenames`[](#override_config_filenames)

- Type: `string[]`
- Env: `MISE_OVERRIDE_CONFIG_FILENAMES`(colon separated)
- Default: `[]`

If set, mise will ignore default config files like `mise.toml` and use these filenames instead. This must be an env var.

## `override_tool_versions_filenames`[](#override_tool_versions_filenames)

- Type: `string[]`
- Env: `MISE_OVERRIDE_TOOL_VERSIONS_FILENAMES`(colon separated)
- Default: `[]`

If set, mise will ignore .tool-versions files and use these filenames instead. Can be set to `none` to disable .tool-versions. This must be an env var.

## `paranoid`[](#paranoid)

- Type: `Bool`
- Env: `MISE_PARANOID`
- Default: `false`

Enables extra-secure behavior. See [Paranoid](https://mise.jdx.dev/paranoid.html).

## `pin`[](#pin)

- Type: `Bool`
- Env: `MISE_PIN`
- Default: `false`

This sets `--pin` by default when running `mise use` in mise.toml files. This can be overridden by passing `--fuzzy` on the command line.

## `plugin_autoupdate_last_check_duration`[](#plugin_autoupdate_last_check_duration)

- Type: `string`
- Env: `MISE_PLUGIN_AUTOUPDATE_LAST_CHECK_DURATION`
- Default: `7d`

How long to wait before updating plugins automatically (note this isn't currently implemented).

## `quiet`[](#quiet)

- Type: `Bool`
- Env: `MISE_QUIET`
- Default: `false`

Suppress all output except errors.

## `raw`[](#raw)

- Type: `Bool`
- Env: `MISE_RAW`
- Default: `false`

Connect stdin/stdout/stderr to child processes.

## `shorthands_file`[](#shorthands_file)

- Type: `Path`(optional)
- Env: `MISE_SHORTHANDS_FILE`
- Default: `None`

Use a custom file for the shorthand aliases. This is useful if you want to share plugins within an organization.

Shorthands make it so when a user runs something like `mise install elixir` mise will automatically install the [asdf-elixir](https://github.com/asdf-vm/asdf-elixir) plugin. By default, it uses the shorthands in [`registry.toml`](https://github.com/jdx/mise/blob/main/registry.toml).

The file should be in this toml format:```toml
elixir = "https://github.com/my-org/mise-elixir.git"
node = "https://github.com/my-org/mise-node.git"
```

## `silent`[](#silent)

- Type: `Bool`
- Env: `MISE_SILENT`
- Default: `false`

Suppress all `mise run|watch` output except errors—including what tasks output.

## `system_config_file`[](#system_config_file)

- Type: `Path`(optional)
- Env: `MISE_SYSTEM_CONFIG_FILE`
- Default: `None`

Path to the system mise config file. Default is `/etc/mise/config.toml`. This must be an env var.

## `task_disable_paths`[](#task_disable_paths)

- Type: `string[]`
- Env: `MISE_TASK_DISABLE_PATHS`(colon separated)
- Default: `[]`

Paths that mise will not look for tasks in.

## `task_output`[](#task_output)

- Type: `string`(optional)
- Env: `MISE_TASK_OUTPUT`
- Default: `None`
- Choices:
  - `prefix` – (default if jobs > 1) print by line with the prefix of the task name
  - `interleave` – (default if jobs == 1 or all tasks run sequentially) print output as it comes in
  - `keep-order` – print output from tasks in the order they are defined
  - `replacing` – replace stdout each time a line is printed-this uses similar logic as `mise install`
  - `timed` – only show stdout lines that take longer than 1s to complete
  - `quiet` – print only stdout/stderr from tasks and nothing from mise
  - `silent` – print nothing from tasks or mise

Change output style when executing tasks. This controls the output of `mise run`.

## `task_remote_no_cache`[](#task_remote_no_cache)

- Type: `Bool`(optional)
- Env: `MISE_TASK_REMOTE_NO_CACHE`
- Default: `None`

Mise will always fetch the latest tasks from the remote, by default the cache is used.

## `task_run_auto_install`[](#task_run_auto_install)

- Type: `Bool`
- Env: `MISE_TASK_RUN_AUTO_INSTALL`
- Default: `true`

Automatically install missing tools when executing tasks.

## `task_skip`[](#task_skip)

- Type: `SetString`
- Env: `MISE_TASK_SKIP`
- Default: `[]`

Tasks to skip when running `mise run`.

## `task_skip_depends`[](#task_skip_depends)

- Type: `Bool`
- Env: `MISE_TASK_SKIP_DEPENDS`
- Default: `false`

Run only specified tasks skipping all dependencies.

## `task_timeout`[](#task_timeout)

- Type: `Duration`(optional)
- Env: `MISE_TASK_TIMEOUT`
- Default: `None`

Default timeout for tasks. Can be overridden by individual tasks.

## `task_timings`[](#task_timings)

- Type: `Bool`(optional)
- Env: `MISE_TASK_TIMINGS`
- Default: `None`

Show completion message with elapsed time for each task on `mise run`. Default shows when output type is `prefix`.

## `terminal_progress`[](#terminal_progress)

- Type: `Bool`
- Env: `MISE_TERMINAL_PROGRESS`
- Default: `true`

Enable terminal progress indicators using OSC 9;4 escape sequences. This provides native progress bars in the terminal window chrome for terminals that support it, including Ghostty, VS Code's integrated terminal, Windows Terminal, and VTE-based terminals (GNOME Terminal, Ptyxis, etc.).

When enabled, mise will send progress updates to the terminal during operations like tool installations. The progress bar appears in the terminal's window UI, separate from the text output.

mise automatically detects whether your terminal supports OSC 9;4 and will only send these sequences if supported. Terminals like Alacritty, iTerm2, WezTerm, and kitty do not support OSC 9;4 and will not receive these sequences.

Set to false to disable this feature if you prefer not to see these indicators.

## `trusted_config_paths`[](#trusted_config_paths)

- Type: `string[]`
- Env: `MISE_TRUSTED_CONFIG_PATHS`(colon separated)
- Default: `[]`

This is a list of config paths that mise will automatically mark as trusted.

## `unix_default_file_shell_args`[](#unix_default_file_shell_args)

- Type: `string`
- Env: `MISE_UNIX_DEFAULT_FILE_SHELL_ARGS`
- Default: `sh`

Default shell arguments for Unix to be used for file commands. For example, `sh` for sh.

## `unix_default_inline_shell_args`[](#unix_default_inline_shell_args)

- Type: `string`
- Env: `MISE_UNIX_DEFAULT_INLINE_SHELL_ARGS`
- Default: `sh -c -o errexit`

Default shell arguments for Unix to be used for inline commands. For example, `sh -c` for sh.

## `url_replacements`[](#url_replacements)

- Type: `object`(optional)
- Env: `MISE_URL_REPLACEMENTS`
- Default: `None`

Map of URL patterns to replacement URLs. This feature supports both simple hostname replacements and advanced regex-based URL transformations for download mirroring and custom registries.

See [URL Replacements](https://mise.jdx.dev/url-replacements.html) for more information.

## `use_file_shell_for_executable_tasks`[](#use_file_shell_for_executable_tasks)

- Type: `Bool`
- Env: `MISE_USE_FILE_SHELL_FOR_EXECUTABLE_TASKS`
- Default: `false`

Determines whether to use a specified shell for executing tasks in the tasks directory. When set to true, the shell defined in the file will be used, or the default shell specified by `windows_default_file_shell_args` or `unix_default_file_shell_args` will be applied. If set to false, tasks will be executed directly as programs.

## `use_versions_host`[](#use_versions_host)

- Type: `Bool`
- Env: `MISE_USE_VERSIONS_HOST`
- Default: `true`

Set to "false" to disable using [mise-versions](https://mise-versions.jdx.dev) as a quick way for mise to query for new versions. This host regularly grabs all the latest versions of core and community plugins. It's faster than running a plugin's `list-all` command and gets around GitHub rate limiting problems when using it.

mise-versions itself also struggles with rate limits but you can help it to fetch more frequently by authenticating with its [GitHub app](https://github.com/apps/mise-versions). It does not require any permissions since it simply fetches public repository information.

See [Troubleshooting](https://mise.jdx.dev/troubleshooting.html#new-version-of-a-tool-is-not-available) for more information.

## `verbose`[](#verbose)

- Type: `Bool`
- Env: `MISE_VERBOSE`
- Default: `false`

Shows more verbose output such as installation logs when installing tools.

## `windows_default_file_shell_args`[](#windows_default_file_shell_args)

- Type: `string`
- Env: `MISE_WINDOWS_DEFAULT_FILE_SHELL_ARGS`
- Default: `cmd /c`

Default shell arguments for Windows to be used for file commands. For example, `cmd /c` for cmd.exe.

## `windows_default_inline_shell_args`[](#windows_default_inline_shell_args)

- Type: `string`
- Env: `MISE_WINDOWS_DEFAULT_INLINE_SHELL_ARGS`
- Default: `cmd /c`

Default shell arguments for Windows to be used for inline commands. For example, `cmd /c` for cmd.exe.

## `windows_executable_extensions`[](#windows_executable_extensions)

- Type: `string[]`
- Env: `MISE_WINDOWS_EXECUTABLE_EXTENSIONS`(comma separated)
- Default: `[ "exe", "bat", "cmd", "com", "ps1", "vbs" ]`

List of executable extensions for Windows. For example, `exe` for .exe files, `bat` for .bat files, and so on.

## `windows_shim_mode`[](#windows_shim_mode)

- Type: `string`
- Env: `MISE_WINDOWS_SHIM_MODE`
- Default: `file`

- values:  - `file`: Creates a file with the content `mise exec`.  - `hardlink`: Uses Windows NTFS Hardlink, required on same filesystems. Need run `mise reshim --force` after upgrade mise.  - `symlink`: Uses Windows NTFS SymbolicLink. Requires Windows Vista or later with admin privileges or enabling "Developer Mode" in Windows 10/11.

## `yes`[](#yes)

- Type: `Bool`
- Env: `MISE_YES`
- Default: `false`

This will automatically answer yes or no to prompts. This is useful for scripting.

## `age`[](#age)

### `age.identity_files`[](#age.identity_files)

- Type: `string[]`(optional)
- Env: `MISE_AGE_IDENTITY_FILES`
- Default: `None`

[experimental] List of age identity files to use for decryption.

### `age.key_file`[](#age.key_file)

- Type: `Path`
- Env: `MISE_AGE_KEY_FILE`
- Default: `~/.config/mise/age.txt`

[experimental] Path to the age private key file to use for encryption/decryption.

### `age.ssh_identity_files`[](#age.ssh_identity_files)

- Type: `string[]`(optional)
- Env: `MISE_AGE_SSH_IDENTITY_FILES`
- Default: `None`

[experimental] List of SSH identity files to use for age decryption.

### `age.strict`[](#age.strict)

- Type: `Bool`
- Env: `MISE_AGE_STRICT`
- Default: `true`

If true, fail when age decryption fails (including when age is not available, the key is missing, or the key is invalid). If false, skip decryption and continue in these cases.

## `aqua`[](#aqua)

### `aqua.baked_registry`[](#aqua.baked_registry)

- Type: `Bool`
- Env: `MISE_AQUA_BAKED_REGISTRY`
- Default: `true`

Use baked-in aqua registry.

### `aqua.cosign`[](#aqua.cosign)

- Type: `Bool`
- Env: `MISE_AQUA_COSIGN`
- Default: `true`

Use cosign to verify aqua tool signatures.

### `aqua.cosign_extra_args`[](#aqua.cosign_extra_args)

- Type: `string[]`(optional)
- Env: `MISE_AQUA_COSIGN_EXTRA_ARGS`
- Default: `None`

Extra arguments to pass to cosign when verifying aqua tool signatures.

### `aqua.github_attestations`[](#aqua.github_attestations)

- Type: `Bool`
- Env: `MISE_AQUA_GITHUB_ATTESTATIONS`
- Default: `true`

Enable/disable GitHub Artifact Attestations verification for aqua tools. When enabled, mise will verify the authenticity and integrity of downloaded tools using GitHub's artifact attestation system.

### `aqua.minisign`[](#aqua.minisign)

- Type: `Bool`
- Env: `MISE_AQUA_MINISIGN`
- Default: `true`

Use minisign to verify aqua tool signatures.

### `aqua.registry_url`[](#aqua.registry_url)

- Type: `Url`(optional)
- Env: `MISE_AQUA_REGISTRY_URL`
- Default: `None`

URL to fetch aqua registry from. This is used to install tools from the aqua registry.

If this is set, the baked-in aqua registry is not used.

By default, the official aqua registry is used: https://github.com/aquaproj/aqua-registry

### `aqua.slsa`[](#aqua.slsa)

- Type: `Bool`
- Env: `MISE_AQUA_SLSA`
- Default: `true`

Use SLSA to verify aqua tool signatures.

## `cargo`[](#cargo)

### `cargo.binstall`[](#cargo.binstall)

- Type: `Bool`
- Env: `MISE_CARGO_BINSTALL`
- Default: `true`

If true, mise will use `cargo binstall` instead of `cargo install` if [`cargo-binstall`](https://crates.io/crates/cargo-binstall) is installed and on PATH. This makes installing CLIs with cargo _much_ faster by downloading precompiled binaries.

You can install it with mise:```sh
mise use -g cargo-binstall
```

### `cargo.registry_name`[](#cargo.registry_name)

- Type: `string`(optional)
- Env: `MISE_CARGO_REGISTRY_NAME`
- Default: `None`

Packages are installed from the official cargo registry.

You can set this to a different registry name if you have a custom feed or want to use a different source.

Please follow the [cargo alternative registries documentation](https://doc.rust-lang.org/cargo/reference/registries.html#using-an-alternate-registry) to configure your registry.

## `conda`[](#conda)

### `conda.channel`[](#conda.channel)

- Type: `string`
- Env: `MISE_CONDA_CHANNEL`
- Default: `conda-forge`

Default conda channel when installing packages with the conda backend. Override per-package with `conda:package[channel=bioconda]`.

The most common channels are:- `conda-forge` - Community-maintained packages (default) - `bioconda` - Bioinformatics packages - `nvidia` - NVIDIA CUDA packages

## `dotnet`[](#dotnet)

### `dotnet.package_flags`[](#dotnet.package_flags)

- Type: `string[]`
- Env: `MISE_DOTNET_PACKAGE_FLAGS`(comma separated)
- Default: `[]`

This is a list of flags to extend the search and install abilities of dotnet tools.

Here are the available flags:- 'prerelease' : include prerelease versions in search and install

### `dotnet.registry_url`[](#dotnet.registry_url)

- Type: `Url`
- Env: `MISE_DOTNET_REGISTRY_URL`
- Default: `https://api.nuget.org/v3/index.json`

URL to fetch dotnet tools from. This is used when installing dotnet tools.

By default, mise will use the [nuget](https://api.nuget.org/v3/index.json) API to fetch.

However, you can set this to a different URL if you have a custom feed or want to use a different source.

## `erlang`[](#erlang)

### `erlang.compile`[](#erlang.compile)

- Type: `Bool`(optional)
- Env: `MISE_ERLANG_COMPILE`
- Default: `None`

If true, compile erlang from source. If false, use precompiled binaries. If not set, use precompiled binaries if available.

## `node`[](#node)

### `node.compile`[](#node.compile)

- Type: `Bool`(optional)
- Env: `MISE_NODE_COMPILE`
- Default: `None`

Compile node from source.

### `node.flavor`[](#node.flavor)

- Type: `string`(optional)
- Env: `MISE_NODE_FLAVOR`
- Default: `None`

Install a specific node flavor like glibc-217 or musl. Use with unofficial node build repo.

### `node.gpg_verify`[](#node.gpg_verify)

- Type: `Bool`(optional)
- Env: `MISE_NODE_GPG_VERIFY`
- Default: `None`

Use gpg to verify node tool signatures.

### `node.mirror_url`[](#node.mirror_url)

- Type: `Url`(optional)
- Env: `MISE_NODE_MIRROR_URL`
- Default: `None`

Mirror to download node tarballs from.

## `npm`[](#npm)

### `npm.bun`[](#npm.bun)deprecated

- Type: `Bool`
- Env: `MISE_NPM_BUN`
- Default: `false`
- Deprecated: Use npm.package_manager instead.

If true, mise will use `bun` instead of `npm` if [`bun`](https://bun.sh/) is installed and on PATH. This makes installing CLIs faster by using `bun` as the package manager.

You can install it with mise:```sh
mise use -g bun
```

### `npm.package_manager`[](#npm.package_manager)

- Type: `string`
- Env: `MISE_NPM_PACKAGE_MANAGER`
- Default: `npm`

Package manager to use for installing npm packages. Can be one of:- `npm` (default) - `bun`- `pnpm`

## `pipx`[](#pipx)

### `pipx.registry_url`[](#pipx.registry_url)

- Type: `string`
- Env: `MISE_PIPX_REGISTRY_URL`
- Default: `https://pypi.org/pypi/{}/json`

URL to use for pipx registry.

This is used to fetch the latest version of a package from the pypi registry.

The default is `https://pypi.org/pypi/{}/json` which is the JSON endpoint for the pypi registry.

You can also use the HTML endpoint by setting this to `https://pypi.org/simple/{}/`.

### `pipx.uvx`[](#pipx.uvx)

- Type: `Bool`
- Env: `MISE_PIPX_UVX`
- Default: `true`

If true, mise will use `uvx` instead of `pipx` if [`uv`](https://docs.astral.sh/uv/) is installed and on PATH. This makes installing CLIs _much_ faster by using `uv` as the package manager.

You can install it with mise:```sh
mise use -g uv
```

## `python`[](#python)

### `python.compile`[](#python.compile)

- Type: `Bool`(optional)
- Env: `MISE_PYTHON_COMPILE`
- Default: `None`

- Values:  - `true` - always compile with python-build instead of downloading [precompiled binaries](https://mise.jdx.dev/lang/python.html#precompiled-python-binaries).  - `false` - always download precompiled binaries.  - [undefined] - use precompiled binary if one is available for the current platform, compile otherwise.

### `python.default_packages_file`[](#python.default_packages_file)

- Type: `Path`(optional)
- Env: `MISE_PYTHON_DEFAULT_PACKAGES_FILE`
- Default: `None`

Path to a file containing default python packages to install when installing a python version.

### `python.patch_url`[](#python.patch_url)

- Type: `Url`(optional)
- Env: `MISE_PYTHON_PATCH_URL`
- Default: `None`

URL to fetch python patches from to pass to python-build.

### `python.patches_directory`[](#python.patches_directory)

- Type: `Path`(optional)
- Env: `MISE_PYTHON_PATCHES_DIRECTORY`
- Default: `None`

Directory to fetch python patches from.

### `python.precompiled_arch`[](#python.precompiled_arch)

- Type: `string`
- Env: `MISE_PYTHON_PRECOMPILED_ARCH`
- Default: `"apple-darwin" | "unknown-linux-gnu" | "unknown-linux-musl"`

Specify the architecture to use for precompiled binaries.

### `python.precompiled_flavor`[](#python.precompiled_flavor)

- Type: `string`
- Env: `MISE_PYTHON_PRECOMPILED_FLAVOR`
- Default: `install_only_stripped`

Specify the flavor to use for precompiled binaries.

Options are available here: [https://gregoryszorc.com/docs/python-build-standalone/main/running.html](https://gregoryszorc.com/docs/python-build-standalone/main/running.html)

### `python.precompiled_os`[](#python.precompiled_os)

- Type: `string`
- Env: `MISE_PYTHON_PRECOMPILED_OS`
- Default: `"x86_64_v3" | "aarch64"`

Specify the architecture to use for precompiled binaries. If on an old CPU, you may want to set this to "x86_64" for the most compatible binaries. See https://gregoryszorc.com/docs/python-build-standalone/main/running.html for more information.

### `python.pyenv_repo`[](#python.pyenv_repo)

- Type: `string`
- Env: `MISE_PYENV_REPO`
- Default: `https://github.com/pyenv/pyenv.git`

URL to fetch pyenv from for compiling python with python-build.

### `python.uv_venv_auto`[](#python.uv_venv_auto)

- Type: `Bool`
- Env: `MISE_PYTHON_UV_VENV_AUTO`
- Default: `false`

Integrate with uv to automatically create/source venvs if uv.lock is present.

### `python.uv_venv_create_args`[](#python.uv_venv_create_args)

- Type: `string[]`(optional)
- Env: `MISE_PYTHON_UV_VENV_CREATE_ARGS`(colon separated)
- Default: `None`

Arguments to pass to uv when creating a venv.

### `python.venv_auto_create`[](#python.venv_auto_create)deprecated

- Type: `Bool`
- Env: `MISE_PYTHON_VENV_AUTO_CREATE`
- Default: `false`
- Deprecated: Use env._python.venv instead.

Automatically create virtualenvs for python tools.

### `python.venv_create_args`[](#python.venv_create_args)

- Type: `string[]`(optional)
- Env: `MISE_PYTHON_VENV_CREATE_ARGS`(colon separated)
- Default: `None`

Arguments to pass to python when creating a venv. (not used for uv venv creation)

### `python.venv_stdlib`[](#python.venv_stdlib)

- Type: `Bool`
- Env: `MISE_VENV_STDLIB`
- Default: `false`

Prefer to use venv from Python's standard library.

## `ruby`[](#ruby)

### `ruby.apply_patches`[](#ruby.apply_patches)

- Type: `string`(optional)
- Env: `MISE_RUBY_APPLY_PATCHES`
- Default: `None`

A list of patch files or URLs to apply to ruby source.

### `ruby.default_packages_file`[](#ruby.default_packages_file)

- Type: `string`
- Env: `MISE_RUBY_DEFAULT_PACKAGES_FILE`
- Default: `~/.default-gems`

Path to a file containing default ruby gems to install when installing ruby.

### `ruby.ruby_build_opts`[](#ruby.ruby_build_opts)

- Type: `string`(optional)
- Env: `MISE_RUBY_BUILD_OPTS`
- Default: `None`

Options to pass to ruby-build.

### `ruby.ruby_build_repo`[](#ruby.ruby_build_repo)

- Type: `string`
- Env: `MISE_RUBY_BUILD_REPO`
- Default: `https://github.com/rbenv/ruby-build.git`

The URL used to fetch ruby-build. This accepts either a Git repository or a ZIP archive.

### `ruby.ruby_install`[](#ruby.ruby_install)

- Type: `Bool`
- Env: `MISE_RUBY_INSTALL`
- Default: `false`

Use ruby-install instead of ruby-build.

### `ruby.ruby_install_opts`[](#ruby.ruby_install_opts)

- Type: `string`(optional)
- Env: `MISE_RUBY_INSTALL_OPTS`
- Default: `None`

Options to pass to ruby-install.

### `ruby.ruby_install_repo`[](#ruby.ruby_install_repo)

- Type: `string`
- Env: `MISE_RUBY_INSTALL_REPO`
- Default: `https://github.com/postmodern/ruby-install.git`

The URL used to fetch ruby-install. This accepts either a Git repository or a ZIP archive.

### `ruby.verbose_install`[](#ruby.verbose_install)

- Type: `Bool`(optional)
- Env: `MISE_RUBY_VERBOSE_INSTALL`
- Default: `None`

Set to true to enable verbose output during ruby installation.

## `rust`[](#rust)

### `rust.cargo_home`[](#rust.cargo_home)

- Type: `Path`(optional)
- Env: `MISE_CARGO_HOME`
- Default: `None`

Path to the cargo home directory. Defaults to `~/.cargo` or `%USERPROFILE%\.cargo`

### `rust.rustup_home`[](#rust.rustup_home)

- Type: `Path`(optional)
- Env: `MISE_RUSTUP_HOME`
- Default: `None`

Path to the rustup home directory. Defaults to `~/.rustup` or `%USERPROFILE%\.rustup`

## `sops`[](#sops)

### `sops.age_key`[](#sops.age_key)

- Type: `string`(optional)
- Env: `MISE_SOPS_AGE_KEY`
- Default: `None`

The age private key to use for sops secret decryption.

### `sops.age_key_file`[](#sops.age_key_file)

- Type: `Path`
- Env: `MISE_SOPS_AGE_KEY_FILE`
- Default: `~/.config/mise/age.txt`

Path to the age private key file to use for sops secret decryption.

### `sops.age_recipients`[](#sops.age_recipients)

- Type: `string`(optional)
- Env: `MISE_SOPS_AGE_RECIPIENTS`
- Default: `None`

The age public keys to use for sops secret encryption.

### `sops.rops`[](#sops.rops)

- Type: `Bool`
- Env: `MISE_SOPS_ROPS`
- Default: `true`

Use rops to decrypt sops files. Disable to shell out to `sops` which will slow down mise but sops may offer features not available in rops.

### `sops.strict`[](#sops.strict)

- Type: `Bool`
- Env: `MISE_SOPS_STRICT`
- Default: `true`

If true, fail when sops decryption fails (including when sops is not available, the key is missing, or the key is invalid). If false, skip decryption and continue in these cases.

## `status`[](#status)

### `status.missing_tools`[](#status.missing_tools)

- Type: `string`
- Env: `MISE_STATUS_MESSAGE_MISSING_TOOLS`
- Default: `if_other_versions_installed`

| Choice | Description |
| --- | --- | | `if_other_versions_installed` [default] | Show the warning only when the tool has at least 1 other version installed | | `always` | Always show the warning | | `never` | Never show the warning |

Show a warning if tools are not installed when entering a directory with a `mise.toml` file.

Disable tools with [`disable_tools`](#disable_tools).

### `status.show_env`[](#status.show_env)

- Type: `Bool`
- Env: `MISE_STATUS_MESSAGE_SHOW_ENV`
- Default: `false`

Show configured env vars when entering a directory with a mise.toml file.

### `status.show_tools`[](#status.show_tools)

- Type: `Bool`
- Env: `MISE_STATUS_MESSAGE_SHOW_TOOLS`
- Default: `false`

Show configured tools when entering a directory with a mise.toml file.

### `status.truncate`[](#status.truncate)

- Type: `Bool`
- Env: `MISE_STATUS_MESSAGE_TRUNCATE`
- Default: `true`

Truncate status messages.

## `swift`[](#swift)

### `swift.gpg_verify`[](#swift.gpg_verify)

- Type: `Bool`(optional)
- Env: `MISE_SWIFT_GPG_VERIFY`
- Default: `None`

Use gpg to verify swift tool signatures.

### `swift.platform`[](#swift.platform)

- Type: `string`
- Env: `MISE_SWIFT_PLATFORM`
- Default: `"osx" | "windows10" | "ubuntu20.04" | "ubuntu22.04" | "ubuntu24.04" | "amazonlinux2" | "ubi9" | "fedora39"`

Override the platform to use for precompiled binaries.

## `task`[](#task)

### `task.monorepo_depth`[](#task.monorepo_depth)

- Type: `integer`
- Env: `MISE_TASK_MONOREPO_DEPTH`
- Default: `5`

When using monorepo mode (experimental_monorepo_root = true), this controls how deep mise will search for task files in subdirectories.

**Depth levels:**

- 1 = immediate children only (monorepo_root/projects/) - 2 = grandchildren (monorepo_root/projects/frontend/) - 5 = default (5 levels deep)

**Performance tip:** Reduce this value if you have a very large monorepo and notice slow task discovery. For example, if your projects are all at `projects/*`, set to 2.

**Example:**

```toml
[settings]
task.monorepo_depth = 3  # Only search 3 levels deep
```

Or via environment variable:```bash
export MISE_TASK_MONOREPO_DEPTH=3
```

### `task.monorepo_exclude_dirs`[](#task.monorepo_exclude_dirs)

- Type: `string[]`
- Env: `MISE_TASK_MONOREPO_EXCLUDE_DIRS`(comma separated)
- Default: `[]`

If empty (default), uses default exclusions: node_modules, target, dist, build. If you specify any patterns, ONLY those patterns will be excluded (defaults are NOT included). For example, setting to [".temp", "vendor"] will exclude only those two directories.

### `task.monorepo_respect_gitignore`[](#task.monorepo_respect_gitignore)

- Type: `Bool`
- Env: `MISE_TASK_MONOREPO_RESPECT_GITIGNORE`
- Default: `true`

When enabled, mise will skip directories that are ignored by .gitignore files when discovering tasks in a monorepo.

## `zig`[](#zig)

### `zig.use_community_mirrors`[](#zig.use_community_mirrors)

- Type: `Bool`
- Env: `MISE_ZIG_USE_COMMUNITY_MIRRORS`
- Default: `true`

This setting allows mise to fetch Zig from one of many community-maintained mirrors.

The ziglang.org website does not offer any uptime or speed guarantees, and it recommends to use the mirrors. The mirror list is cached and allows the installs to succeed even if the main server is unavailable.

The downloaded tarballs are always verified against Zig Software Foundation's public key, so there is no risk of third-party modifications. Read more on [ziglang.org](https://ziglang.org/download/community-mirrors/).

If you don't have the mirror list cached locally, you can place the newline-separated server list inside `mise cache path`, folder `zig` as `community-mirrors.txt`.