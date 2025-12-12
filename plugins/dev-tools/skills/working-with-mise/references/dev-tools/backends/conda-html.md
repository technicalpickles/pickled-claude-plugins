---
title: "Conda Backend | mise-en-place"
meta:
  description: "mise-en-place documentation"
---

# Conda Backend experimental [​](#conda-backend)

You may install packages directly from [conda-forge](https://conda-forge.org/) and other Anaconda channels without needing conda or mamba installed.

This backend fetches pre-built packages from the anaconda.org API and extracts them directly, making it a lightweight way to install conda packages as standalone CLI tools.

The code for this is inside the mise repository at [`./src/backend/conda.rs`](https://github.com/jdx/mise/blob/main/src/backend/conda.rs).

## Dependencies [​](#dependencies)

None. Unlike other conda tools, this backend does not require conda, mamba, or micromamba to be installed. It downloads and extracts packages directly from anaconda.org.

## Usage [​](#usage)

The following installs the latest version of [ruff](https://anaconda.org/conda-forge/ruff) and sets it as the active version on PATH:

sh

```
$ mise use -g conda:ruff
$ ruff --version
ruff 0.8.0
```

The version will be set in `~/.config/mise/config.toml` with the following format:

toml

```
[tools]
"conda:ruff" = "latest"
```

### Specifying a Version [​](#specifying-a-version)

sh

```
mise use -g conda:ruff@0.7.0
```

### Using a Different Channel [​](#using-a-different-channel)

By default, packages are installed from `conda-forge`. You can specify a different channel:

sh

```
mise use -g "conda:ruff[channel=bioconda]"
```

Or in `mise.toml`:

toml

```
[tools]
"conda:ruff" = { version = "latest", channel = "bioconda" }
```

## Platform Support [​](#platform-support)

The conda backend automatically selects the appropriate package for your platform:

| Platform | Conda Subdir |
| --- | --- |
| Linux x64 | linux-64 |
| Linux ARM64 | linux-aarch64 |
| macOS x64 | osx-64 |
| macOS ARM64 | osx-arm64 |
| Windows x64 | win-64 |

If a platform-specific package is not available, the backend will fall back to `noarch` packages.

## Settings [​](#settings)

Set these with `mise settings set [VARIABLE] [VALUE]` or by setting the environment variable listed.

### `conda.channel`[](#conda.channel)

- Type: `string`
- Env: `MISE_CONDA_CHANNEL`
- Default: `conda-forge`

Default conda channel when installing packages with the conda backend. Override per-package with `conda:package[channel=bioconda]`.

The most common channels are:- `conda-forge` - Community-maintained packages (default) - `bioconda` - Bioinformatics packages - `nvidia` - NVIDIA CUDA packages

## Tool Options [​](#tool-options)

The following [tool-options](https://mise.jdx.dev/dev-tools/#tool-options) are available for the `conda` backend—these go in `[tools]` in `mise.toml`.

### `channel` [​](#channel)

Override the conda channel for a specific package:

toml

```
[tools]
"conda:bioconductor-deseq2" = { version = "latest", channel = "bioconda" }
```

## Common Channels [​](#common-channels)

- `conda-forge` - Community-maintained packages (default)
- `bioconda` - Bioinformatics packages
- `nvidia` - NVIDIA CUDA packages

## Limitations [​](#limitations)

- Only installs single packages, not full conda environments with dependencies
- Best suited for standalone CLI tools that don't require complex dependency trees
- Does not manage Python environments or package dependencies like full conda/mamba