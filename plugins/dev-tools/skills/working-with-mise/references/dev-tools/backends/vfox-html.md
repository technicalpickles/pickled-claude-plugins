---
title: "Vfox Backend | mise-en-place"
meta:
  description: "mise-en-place documentation"
---

# Vfox Backend [​](#vfox-backend)

[Vfox](https://github.com/version-fox/vfox) plugins may be used in mise to install tools.

The code for this is inside the mise repository at [`./src/backend/vfox.rs`](https://github.com/jdx/mise/blob/main/src/backend/vfox.rs).

## Dependencies [​](#dependencies)

No dependencies are required for vfox. Vfox lua code is read via a lua interpreter built into mise.

## Usage [​](#usage)

The following installs the latest version of cmake and sets it as the active version on PATH:

sh

```
$ mise use -g vfox:version-fox/vfox-cmake
$ cmake --version
cmake version 3.21.3
```

The version will be set in `~/.config/mise/config.toml` with the following format:

toml

```
[tools]
"vfox:version-fox/vfox-cmake" = "latest"
```

## Default plugin backend [​](#default-plugin-backend)

On Windows, mise uses vfox plugins by default. If you'd like to use plugins by default even on Linux/macOS, set the following settings:

sh

```
mise settings add disable_backends asdf
```

Now you can list available plugins with `mise registry`:

sh

```
$ mise registry | grep vfox:
clang                         vfox:mise-plugins/vfox-clang
cmake                         vfox:mise-plugins/vfox-cmake
crystal                       vfox:mise-plugins/vfox-crystal
dart                          vfox:mise-plugins/vfox-dart
dotnet                        vfox:mise-plugins/vfox-dotnet
etcd                          aqua:etcd-io/etcd vfox:mise-plugins/vfox-etcd
flutter                       vfox:mise-plugins/vfox-flutter
gradle                        aqua:gradle/gradle vfox:mise-plugins/vfox-gradle
groovy                        vfox:mise-plugins/vfox-groovy
kotlin                        vfox:mise-plugins/vfox-kotlin
maven                         aqua:apache/maven vfox:mise-plugins/vfox-maven
php                           vfox:mise-plugins/vfox-php
scala                         vfox:mise-plugins/vfox-scala
terraform                     aqua:hashicorp/terraform vfox:mise-plugins/vfox-terraform
vlang                         vfox:mise-plugins/vfox-vlang
```

And they will be installed when running commands such as `mise use -g cmake` without needing to specify `vfox:cmake`.

## Plugins [​](#plugins)

In addition to the standard vfox plugins, mise supports modern plugins that can manage multiple tools using the `plugin:tool` format. These plugins are perfect for:

- Installing tools from private repositories
- Package managers (npm, pip, etc.)
- Custom tool families

### Example: Plugin Usage [​](#example-plugin-usage)

bash

```
# Install a plugin
mise plugin install my-plugin https://github.com/username/my-plugin

# Use the plugin:tool format
mise install my-plugin:some-tool@1.0.0
mise use my-plugin:some-tool@latest
```

### Install from Zip File [​](#install-from-zip-file)

bash

```
# Install a plugin from a zip file over HTTPS
mise plugin install <plugin-name> <zip-url>
# Example: Installing a plugin from a zip file
mise plugin install vfox-cmake https://github.com/mise-plugins/vfox-cmake/archive/refs/heads/main.zip
```

For more information, see:

- [Using Plugins](https://mise.jdx.dev/../../plugin-usage.html) - End-user guide
- [Plugin Development](https://mise.jdx.dev/../../tool-plugin-development.html) - Developer guide
- [Plugin Template](https://github.com/jdx/mise-tool-plugin-template) - Quick start template for creating plugins