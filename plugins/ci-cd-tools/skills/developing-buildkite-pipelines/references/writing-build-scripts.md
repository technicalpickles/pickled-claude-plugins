---
title: "Writing build scripts | Buildkite Documentation"
meta:
  "og:description": "One of the most common actions that Buildkite steps perform is running shell scripts. These scripts are checked in alongside your code and pipeline.yml file."
  "og:title": "Writing build scripts"
  description: "One of the most common actions that Buildkite steps perform is running shell scripts. These scripts are checked in alongside your code and pipeline.yml file."
---

# Writing build scripts

One of the most common actions that Buildkite steps perform is running shell scripts. These scripts are checked in alongside your code and `pipeline.yml` file.

The [Buildkite Agent](https://buildkite.com/docs/agent/v3) will run your scripts, capture and report the log output, and use the exit status to mark each job, as well as the overall build, as passed or failed.

## [Configuring Bash](#configuring-bash)

The shell that runs your scripts in Buildkite is a clean Bash prompt with no settings. If you rely on anything from your `~/.bash_profile` or `~/.bashrc` files when you run scripts locally, you'll need to explicitly add the relevant items to your build scripts.

When writing Bash shell scripts there are a number of options you can set to help prevent unexpected errors:

| `e` | Exit script immediately if any command returns a non-zero exit status. |
| --- | --- |
| `u` | Exit script immediately if an undefined variable is used (for example, `echo "$UNDEFINED_ENV_VAR"`). |
| `o pipefail` | Ensure Bash pipelines (for example, `cmd \| othercmd`) return a non-zero status if any of the commands fail, rather than returning the exit status of the last command in the pipeline. |
| `x` | Expand and print each command before executing. See [Debugging your environment](https://buildkite.com/docs/builds/writing-build-scripts#debugging-your-environment) for more information. |

Bash's built-in `set` command can be used to enable and disable options. For example, `set -u` enables the `u` option, and `set +u` disables the `u` option. You can also set multiple options at once, for example `set -ue` enables both the `u` and `e` options.

The following example enables the most commonly used options for build scripts:

```
#!/bin/bash

set -euo pipefail

run_tests
```

For a full list of options, see the [Bash reference manual](https://www.gnu.org/software/bash/manual/html_node/The-Set-Builtin.html).

[Unbound variable errors](#unbound-variable-errors)

Note that while enabling the `u` option is generally a good default to use for all build scripts, it can cause some tools like [rvm](https://rvm.io) to fail with “unbound variable” errors. If you encounter errors, you can either remove `u` from the list of options, or run the tool causing the error wrapped in `set +u` and `set -u` to remove the option for only that command. For example: `set +u; rvm xxx; set -u`.

## [Capturing exit status](#capturing-exit-status)

Build scripts can sometimes contain commands that shouldn't affect the overall exit status. For example, take the following script:

```
#!/bin/bash

# Note that we don't enable the 'e' option, which would cause the script to
# immediately exit if 'run_tests' failed
set -uo pipefail

run_tests

clean_up
```

Running this script will exit with the status returned by the final command, `clean_up`. However, what we really care about is the exit status of the first command, `run_tests`.

By using a variable to store the exit status of `run_tests`, we can run additional commands while still returning the original exit status. For example:

```
#!/bin/bash

# Note that we don't enable the 'e' option, which would cause the script to
# immediately exit if 'run_tests' failed
set -uo pipefail

# Run the main command we're most interested in
run_tests

# Capture the exit status
TESTS_EXIT_STATUS=$?

# Run additional commands
clean_up

# Exit with the status of the original command
exit $TESTS_EXIT_STATUS
```

Using this technique gives you control over the exit code of your script, and the final success or failure of your build job.

## [Debugging your environment](#debugging-your-environment)

The first step in debugging your build script is to view the environment variables from the Buildkite web interface:

![Screenshot of viewing a job's environment tab](https://buildkite.com/docs/assets/viewing-job-environment-variables-4dd26da4.png)

There may be additional environment variables available in your build job that don't appear in this list, such as ones set by your [job lifecycle hooks](https://buildkite.com/docs/agent/v3/hooks#job-lifecycle-hooks). To debug these, you can print them using `echo $SOME_VAR` before the command you're wanting to run. For example:

```
#!/bin/bash

echo "$PATH"

some_command
```

If you require more environment information, you can execute `env` to print out all the environment variable names and their values. If you use `env` you should filter the output using a tool such as `grep` or `egrep`, to ensure you don't leak private keys or other information.

[Security recommendation](#security-recommendation)

If you use environment variables to define sensitive data such as API keys or Secret Access Keys, you should always filter the output of `env` to ensure you're not exposing any secrets in your build log.

For example, the following prints all environment variable names and values containing the words "git" or "node", using a case-insensitive search:

```
#!/bin/bash

env | grep -i -E 'git|node'

some_command
```

Enabling Bash's debug mode using `set -x` can also help to debug your build scripts. This debug output can be very noisy, so it's best enable this before the command you want to debug, and then to disable it straight after. For example:

```
#!/bin/bash

set -x # Enable debugging
some_command
set +x # Disable debugging

some_other_command
```

For more information about the `x` option and debugging in general, see the [Bash Guide for Beginners' page on debugging Bash scripts](http://tldp.org/LDP/Bash-Beginners-Guide/html/sect_02_03.html).

## [Help with linting and debugging](#help-with-linting-and-debugging)

To check your shell scripts for common errors and mistakes we highly recommend using a linting tool like [Shellcheck](https://www.shellcheck.net). Shellcheck is a shell script linter with a web-based front-end, a command line tool, and integrates directly with most code editors.

For an explanation of a shell script snippet, the [explainshell.com](https://explainshell.com) tool is extremely useful. explainshell.com can tell you, in plain English, what a line of shell script does. It also integrates the man pages of common tools such as `ssh` and `git`.

## [Managing log output](#managing-log-output)

If your script is generating output that is too large, there are several strategies you can employ to reduce the output or redirect the log. Take a look at our guide to [managing log output guide](https://buildkite.com/docs/builds/managing-log-output) for a step by step introduction.