---
title: "gem Backend | mise-en-place"
meta:
  description: "mise-en-place documentation"
---

# gem Backend [​](#gem-backend)

mise can be used to install CLIs from RubyGems. The code for this is inside of the mise repository at [`./src/backend/gem.rs`](https://github.com/jdx/mise/blob/main/src/backend/gem.rs).

## Dependencies [​](#dependencies)

This relies on having `gem` (provided with ruby) installed. You can install it with or without mise. Here is how to install `ruby` with mise:

sh

```
mise use -g ruby
```

## Usage [​](#usage)

The following installs the latest version of [rubocop](https://rubygems.org/gems/rubocop) and sets it as the active version on PATH:

sh

```
mise use -g gem:rubocop
rubocop --version
```

The version will be set in `~/.config/mise/config.toml` with the following format:

toml

```
[tools]
"gem:rubocop" = "latest"
```

## Ruby upgrades [​](#ruby-upgrades)

If the ruby version used by a gem package changes, (by mise or system ruby), you may need to reinstall the gem. This can be done with:

sh

```
mise install -f gem:rubocop
```

Or you can reinstall all gems with:

sh

```
mise install -f "gem:*"
```

## Settings [​](#settings)

Set these with `mise settings set [VARIABLE] [VALUE]` or by setting the environment variable listed.

No settings available.