---
title: "Getting Started | mise-en-place"
meta:
  description: "mise-en-place documentation"
---

# Getting Started [​](#getting-started)

This will show you how to install mise and get started with it. This is a suitable way when using an interactive shell like `bash`, `zsh`, or `fish`.

## 1. Install `mise` CLI [​](#installing-mise-cli)

See [installing mise](https://mise.jdx.dev/installing-mise.html) for other ways to install mise (`macport`, `apt`, `yum`, `nix`, etc.).

shell

```
curl https://mise.run | sh
```

By default, mise will be installed to `~/.local/bin` (this is simply a suggestion. `mise` can be installed anywhere). You can verify the installation by running:

shell

```
~/.local/bin/mise --version
# mise 2024.x.x
```

- `~/.local/bin` does not need to be in `PATH`. mise will automatically add its own directory to `PATH` when [activated](#activate-mise).

`mise` respects [`MISE_DATA_DIR`](https://mise.jdx.dev/configuration.html) and [`XDG_DATA_HOME`](https://mise.jdx.dev/configuration.html) if you'd like to change these locations.

## 2. mise `exec` and `run` [​](#mise-exec-run)

Once `mise` is installed, you can immediately start using it. `mise` can be used to install and run [tools](https://mise.jdx.dev/dev-tools/), launch [tasks](https://mise.jdx.dev/tasks/), and manage [environment variables](https://mise.jdx.dev/environments/).

The most essential feature `mise` provides is the ability to run [tools](https://mise.jdx.dev/dev-tools/) with specific versions. A simple way to run a shell command with a given tool is to use [`mise x|exec`](https://mise.jdx.dev/cli/exec.html). For example, here is how you can start a Python 3 interactive shell (REPL):

> _In the examples below, use `~/.local/bin/mise` (or the absolute path to `mise`) if `mise` is not already on `PATH`_

sh

```
mise exec python@3 -- python
# this will download and install Python if it is not already installed
# Python 3.13.2
# >>> ...
```

or run node 24:

sh

```
mise exec node@24 -- node -v
# v24.x.x
```

[`mise x|exec`](https://mise.jdx.dev/cli/exec.html) is a powerful way to load the current `mise` context (tools & environment variables) without modifying your shell session or running ad-hoc commands with mise tools set. Installing [`tools`](https://mise.jdx.dev/dev-tools/) is as simple as running [`mise u|use`](https://mise.jdx.dev/cli/use.html).

shell

```
mise use --global node@24 # install node 24 and set it as the global default
mise exec -- node my-script.js
# run my-script.js with node 24...
```

Another useful command is [`mise r|run`](https://mise.jdx.dev/cli/run.html) which allows you to run a [`mise task`](https://mise.jdx.dev/tasks/) or a script with the `mise` context.

TIP

You can set a shell alias in your shell's rc file like `alias x="mise x --"` to save some keystrokes.

## 3. Activate `mise` optional [​](#activate-mise)

While using [`mise x|exec`](https://mise.jdx.dev/cli/exec.html) is useful, for interactive shells, you might prefer to activate `mise` to automatically load the `mise` context (`tools` and `environment variables`) in your shell session. Another option is to use [shims](https://mise.jdx.dev/dev-tools/shims.html).

- [`mise activate`](https://mise.jdx.dev/cli/activate.html) method updates your environment variable and `PATH` every time your prompt is run to ensure you use the correct versions.
- [Shims](https://mise.jdx.dev/dev-tools/shims.html) are symlinks to the `mise` binary that intercept commands and load the appropriate environment. Note that [**shims do not support all the features of `mise activate`**](https://mise.jdx.dev/dev-tools/shims.html#shims-vs-path).

For interactive shells, `mise activate` is recommended. In non-interactive sessions, like CI/CD, IDEs, and scripts, using `shims` might work best. You can also not use any and call `mise exec/run` directly instead. See [this guide](https://mise.jdx.dev/dev-tools/shims.html) for more information.

Here is how you can activate `mise` depending on your shell and the installation method:

bashzshfish

sh

```
echo 'eval "$(~/.local/bin/mise activate bash)"' >> ~/.bashrc
```

sh

```
echo 'eval "$(~/.local/bin/mise activate zsh)"' >> ~/.zshrc
```

sh

```
echo '~/.local/bin/mise activate fish | source' >> ~/.config/fish/config.fish
```

Make sure you restart your shell session after modifying your rc file in order for it to take effect. You can run [`mise dr|doctor`](https://mise.jdx.dev/cli/doctor.html) to verify that mise is correctly installed and activated.

Now that `mise` is activated or its shims have been added to `PATH`, `node` is also available directly! (without using `mise exec`):

sh

```
mise use --global node@24
node -v
# v24.x.x
```

Note that when you ran `mise use --global node@24`, `mise` updated the global `mise` configuration.

~/.config/mise/config.toml

toml

```
[tools]
node = "24"
```

## 4. Use tools from backends (npm, pipx, core, aqua, github) [​](#tool-backends)

Backends are ecosystems or package managers that mise uses to install tools. With `mise use`, you can install multiple tools from each backend.

For example, to install [claude-code](https://www.npmjs.com/package/@anthropic-ai/claude-code) with the npm backend:

sh

```
# run claude-code via mise x|exec
mise exec npm:@anthropic-ai/claude-code -- claude --version

# or if mise is activated in your shell
mise use --global npm:@anthropic-ai/claude-code
claude --version
```

Install [black](https://github.com/psf/black) with the pipx backend:

sh

```
# run black via mise x|exec
mise exec pipx:black -- black --version

# or if mise is activated in your shell
mise use --global pipx:black
black --version
```

mise can also install tools directly from github with the github backend:

sh

```
# run ripgrep via mise x|exec
mise exec github:BurntSushi/ripgrep -- ripgrep --version

# or if mise is activated in your shell
mise use --global github:BurntSushi/ripgrep
ripgrep --version
```

See [Backends](https://mise.jdx.dev/dev-tools/backends/) for more ecosystems and details.

## 5. Setting environment variables [​](#environment-variables)

You can set environment variables in `mise.toml` which will be set if mise is activated or if `mise x|exec` is used in a directory:

mise.toml

toml

```
[env]
NODE_ENV = "production"
```

sh

```
mise exec -- node --eval 'console.log(process.env.NODE_ENV)'

# or if mise is activated in your shell
echo "node env: $NODE_ENV"
# node env: production
```

## 6. Run a task [​](#run-a-task)

You can define simple tasks in `mise.toml` and run them with `mise run`:

mise.toml

toml

```
[tasks]
hello = "echo hello from mise"
```

Run it:

sh

```
mise run hello
# hello from mise
```

TIP

mise tasks will automatically install all of the tools from `mise.toml` before running the task.

See [tasks](https://mise.jdx.dev/tasks/) for more information on how to define and use tasks.

## 7. Next steps [​](#next-steps)

Follow the [walkthrough](https://mise.jdx.dev/walkthrough.html) for more examples on how to use mise.

### Set up autocompletion [​](#autocompletion)

See [autocompletion](https://mise.jdx.dev/installing-mise.html#autocompletion) to learn how to set up autocompletion for your shell.

### GitHub API rate limiting [​](#github-api-rate-limiting)

WARNING

Many tools in mise require the use of the GitHub API. Unauthenticated requests to the GitHub API are often rate limited. If you see 4xx errors while using mise, you can set `MISE_GITHUB_TOKEN` or `GITHUB_TOKEN` to a token [generated from here](https://github.com/settings/tokens/new?description=MISE_GITHUB_TOKEN) which will likely fix the issue. The token does not require any scopes.