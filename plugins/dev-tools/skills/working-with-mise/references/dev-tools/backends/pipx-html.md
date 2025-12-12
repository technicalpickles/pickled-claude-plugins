---
title: "pipx Backend | mise-en-place"
meta:
  description: "mise-en-place documentation"
---

# pipx Backend [​](#pipx-backend)

pipx is a tool for running Python CLIs in isolated virtualenvs. This is necessary for Python CLIs because it prevents conflicting dependencies between CLIs or between a CLI and Python projects. In essence, this backend lets you add Python CLIs to mise.

To be clear, pipx is not pip and it's not used to manage Python dependencies generally. mise is a tool manager, not a dependency manager like pip, uv, or poetry. You can, however, use mise to install said package managers. You'd want to use the pipx backend to install a CLI like "black", not a library like "NumPy" or "requests".

Somewhat confusingly, the pipx backend will actually default to using [`uvx`](https://docs.astral.sh/uv/guides/tools/) (the equivalent of pipx for uv) if uv is installed. This should just mean that it installs much faster, but see below to disable or configure since occasionally tools don't work with uvx.

The pipx backend supports the following sources:

- PyPI
- Git
- GitHub
- Http

The code for this is inside of the mise repository at [`./src/backend/pipx.rs`](https://github.com/jdx/mise/blob/main/src/backend/pipx.rs).

## Dependencies [​](#dependencies)

This relies on having `pipx` installed. You can install it with or without mise. Here is how to install `pipx` with mise:

sh

```
mise use -g python
pip install --user pipx
```

[Other installation instructions](https://pipx.pypa.io/latest/installation/)

## Usage [​](#usage)

The following installs the latest version of [black](https://github.com/psf/black) and sets it as the active version on PATH:

sh

```
$ mise use -g pipx:psf/black
$ black --version
black, 24.3.0
```

The version will be set in `~/.config/mise/config.toml` with the following format:

toml

```
[tools]
"pipx:psf/black" = "latest"
```

## Python upgrades [​](#python-upgrades)

If the python version used by a pipx package changes, (by mise or system python), you may need to reinstall the package. This can be done with:

sh

```
mise install -f pipx:psf/black
```

Or you can reinstall all pipx packages with:

sh

```
mise install -f "pipx:*"
```

mise _should_ do this automatically when using `mise up python`.

### Supported Pipx Syntax [​](#supported-pipx-syntax)

| Description | Usage |
| --- | --- |
| PyPI shorthand latest version | `pipx:black` |
| PyPI shorthand for specific version | `pipx:black@24.3.0` |
| GitHub shorthand for latest version | `pipx:psf/black` |
| GitHub shorthand for specific version | `pipx:psf/black@24.3.0` |
| Git syntax for latest version | `pipx:git+https://github.com/psf/black.git` |
| Git syntax for a branch | `pipx:git+https://github.com/psf/black.git@main` |
| Https with zipfile | `pipx:https://github.com/psf/black/archive/18.9b0.zip` |

Other syntax may work but is unsupported and untested.

## Settings [​](#settings)

Set these with `mise settings set [VARIABLE] [VALUE]` or by setting the environment variable listed.

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

## Tool Options [​](#tool-options)

The following [tool-options](https://mise.jdx.dev/dev-tools/#tool-options) are available for the `pipx` backend—these go in `[tools]` in `mise.toml`.

### `extras` [​](#extras)

Install additional components.

toml

```
[tools]
"pipx:harlequin" = { version = "latest", extras = "postgres,s3" }
```

### `pipx_args` [​](#pipx-args)

Additional arguments to pass to `pipx` when installing the package.

toml

```
[tools]
"pipx:black" = { version = "latest", pipx_args = "--preinstall" }
```

### `uvx` [​](#uvx)

Set to `false` to always disable uv for this tool.

toml

```
[tools]
"pipx:ansible" = { version = "latest", uvx = "false", pipx_args = "--include-deps" }
```

### `uvx_args` [​](#uvx-args)

Additional arguments to pass to `uvx` when installing the package.

toml

```
[tools]
"pipx:ansible-core" = { version = "latest", uvx_args = "--with ansible" }
```