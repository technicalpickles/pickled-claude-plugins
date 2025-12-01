---
title: "Environment variables | Buildkite Documentation"
meta:
  "og:description": "When the agent invokes your build scripts it passes in a set of standard Buildkite environment variables, along with any that you&#39;ve defined in your build configuration. You can use these environment variables in your build steps and job lifecycle hooks."
  "og:title": "Environment variables"
  description: "When the agent invokes your build scripts it passes in a set of standard Buildkite environment variables, along with any that you&#39;ve defined in your build configuration. You can use these environment variables in your build steps and job lifecycle hooks."
---

# Environment variables

When the agent invokes your build scripts it passes in a set of standard Buildkite environment variables, along with any that you've defined in your build configuration. You can use these environment variables in your [build steps](https://buildkite.com/docs/pipelines/configure/defining-steps) and [job lifecycle hooks](https://buildkite.com/docs/agent/v3/hooks#job-lifecycle-hooks).

Environment variable size limits are dependent on the operating systems the agents are run on. When a program or process is started, it can typically accept inputs as either one or more environment variables in the form of `key=value` pairs, or a list (array) of command line arguments (referred to as a vector of arguments or `argv`). Depending on the operating system, these limits could be shared size limit across all such environment variables and `argv`, whereas others impose size limits per item (such as an environment variable's size limit).

For best practices and recommendations about using secrets in your environment variables, see the [Managing secrets](https://buildkite.com/docs/pipelines/security/secrets/managing) guide.

## [Buildkite environment variables](#buildkite-environment-variables)

The following environment variables may be visible in your commands, plugins, and hooks.

[Unverified commits](#unverified-commits)

Note that GitHub accepts [unsigned commits](https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification), including information about the commit author and passes them along to webhooks, so you should not rely on these for authentication unless you are confident that all of your commits are trusted.

| `BUILDKITE` [#](#BUILDKITE) This value cannot be modified | Always `true` |
| --- | --- |
| `BUILDKITE_AGENT_ACCESS_TOKEN` [#](#BUILDKITE_AGENT_ACCESS_TOKEN) This value cannot be modified | The agent session token for the job. The variable is read by the agent `artifact` and `meta-data` commands.**Example:** `83d544ccc223c157d2bf80d3f2a32982c32c3c0db8e3674820da5064783fb091` |
| `BUILDKITE_AGENT_DEBUG` [#](#BUILDKITE_AGENT_DEBUG)- **Possible values:**- `true`- `false` This value cannot be modified | The value of the `debug` [agent configuration option](https://buildkite.com/docs/agent/v3/configuration). |
| `BUILDKITE_AGENT_DISCONNECT_AFTER_JOB` [#](#BUILDKITE_AGENT_DISCONNECT_AFTER_JOB)- **Possible values:**- `true`- `false` This value cannot be modified | The value of the `disconnect-after-job` [agent configuration option](https://buildkite.com/docs/agent/v3/configuration). |
| `BUILDKITE_AGENT_DISCONNECT_AFTER_IDLE_TIMEOUT` [#](#BUILDKITE_AGENT_DISCONNECT_AFTER_IDLE_TIMEOUT) This value cannot be modified | The value of the `disconnect-after-idle-timeout` [agent configuration option](https://buildkite.com/docs/agent/v3/configuration).**Example:** `10` |
| `BUILDKITE_AGENT_ENDPOINT` [#](#BUILDKITE_AGENT_ENDPOINT)**Default**: `https://agent.buildkite.com/v3` This value cannot be modified | The value of the `endpoint` [agent configuration option](https://buildkite.com/docs/agent/v3/configuration). This is set as an environment variable by the bootstrap and then read by most of the `buildkite-agent` commands. |
| `BUILDKITE_AGENT_EXPERIMENT` [#](#BUILDKITE_AGENT_EXPERIMENT) This value cannot be modified | A list of the [experimental agent features](https://buildkite.com/docs/agent/v3#experimental-features) that are currently enabled. The value can be set using the `--experiment` flag on the [`buildkite-agent start` command](https://buildkite.com/docs/agent/v3/cli-start#starting-an-agent) or in your [agent configuration file](https://buildkite.com/docs/agent/v3/configuration).**Example:** `experiment1,experiment2` |
| `BUILDKITE_AGENT_HEALTH_CHECK_ADDR` [#](#BUILDKITE_AGENT_HEALTH_CHECK_ADDR) This value cannot be modified | The value of the `health-check-addr` [agent configuration option](https://buildkite.com/docs/agent/v3/configuration).**Example:** `localhost:8080` |
| `BUILDKITE_AGENT_ID` [#](#BUILDKITE_AGENT_ID) This value cannot be modified | The UUID of the agent.**Example:** `1a222222-e999-3636-8ddd-802222222222` |
| `BUILDKITE_AGENT_META_DATA_*` [#](#BUILDKITE_AGENT_META_DATA_) This value cannot be modified | The value of each [agent tag](https://buildkite.com/docs/agent/v3/cli-start#setting-tags). The tag name is appended to the end of the variable name. They can be set using the `--tags` flag on the `buildkite-agent start` command, or in the [agent configuration file](https://buildkite.com/docs/agent/v3/configuration). The [Queue tag](https://buildkite.com/docs/agent/v3/queues) is specifically used for isolating jobs and agents, and appears as the `BUILDKITE_AGENT_META_DATA_QUEUE` environment variable.**Example:** `"BUILDKITE_AGENT_META_DATA_TAGNAME=tagvalue", "BUILDKITE_AGENT_META_DATA_QUEUE=some-queue"` |
| `BUILDKITE_AGENT_NAME` [#](#BUILDKITE_AGENT_NAME) This value cannot be modified | The name of the agent that ran the job.**Example:** `elastic-builders-088264dc4f9` |
| `BUILDKITE_AGENT_PID` [#](#BUILDKITE_AGENT_PID) This value cannot be modified | The process ID of the agent.**Example:** `6` |
| `BUILDKITE_ARTIFACT_PATHS` [#](#BUILDKITE_ARTIFACT_PATHS) | The artifact paths to upload after the job, if any have been specified. The value can be modified by exporting the environment variable in the `environment` or `pre-checkout` hooks.**Example:** `tmp/capybara/**/*;coverage/**/*` |
| `BUILDKITE_ARTIFACT_UPLOAD_DESTINATION` [#](#BUILDKITE_ARTIFACT_UPLOAD_DESTINATION) | The path where artifacts will be uploaded. This variable is read by the `buildkite-agent artifact upload` command, and during the artifact upload phase of [command steps](https://buildkite.com/docs/pipelines/command-step#command-step-attributes). It can only be set by exporting the environment variable in the `environment`, `pre-checkout` or `pre-command` hooks.**Example:** `s3://name-of-your-s3-bucket/$BUILDKITE_PIPELINE_ID/$BUILDKITE_BUILD_ID/$BUILDKITE_JOB_ID` |
| `BUILDKITE_BIN_PATH` [#](#BUILDKITE_BIN_PATH) This value cannot be modified | The path to the directory containing the `buildkite-agent` binary.**Example:** `/usr/local/bin` |
| `BUILDKITE_BRANCH` [#](#BUILDKITE_BRANCH) This value cannot be modified | The branch being built. Note that for manually triggered builds, this branch is not guaranteed to contain the commit specified by `BUILDKITE_COMMIT`. When a build is triggered by a GitHub webhook tag `push` event, this variable will also be set to the name of the tag being built (same value as `BUILDKITE_TAG`).**Example:** `main` |
| `BUILDKITE_BUILD_CHECKOUT_PATH` [#](#BUILDKITE_BUILD_CHECKOUT_PATH) This value cannot be modified | The path where the agent has checked out your code for this build. This variable is read by the bootstrap when the agent is started, and can only be set by exporting the environment variable in the `environment` or `pre-checkout` hooks.**Example:** `/var/lib/buildkite-agent/builds/agent-1/pipeline-2` |
| `BUILDKITE_BUILD_AUTHOR` [#](#BUILDKITE_BUILD_AUTHOR) This value cannot be modified | The name of the user who authored the commit being built. May be **[unverified](#unverified-commits)**. This value can be blank in some situations, including builds manually triggered using API or Buildkite web interface.**Example:** `Carol Danvers` |
| `BUILDKITE_BUILD_AUTHOR_EMAIL` [#](#BUILDKITE_BUILD_AUTHOR_EMAIL) This value cannot be modified | The notification email of the user who authored the commit being built. May be **[unverified](#unverified-commits)**. This value can be blank in some situations, including builds manually triggered using API or Buildkite web interface.**Example:** `cdanvers@kree-net.com` |
| `BUILDKITE_BUILD_CREATOR` [#](#BUILDKITE_BUILD_CREATOR) This value cannot be modified | The name of the user who created the build. The value differs depending on how the build was created:<ul><li>**Buildkite dashboard:** Set based on who manually created the build.</li><li>**GitHub webhook:** Set from the **[unverified](#unverified-commits)** HEAD commit.</li><li>**Webhook:** Set based on which user is attached to the API Key used.</li></ul>**Example:** `Carol Danvers` |
| `BUILDKITE_BUILD_CREATOR_EMAIL` [#](#BUILDKITE_BUILD_CREATOR_EMAIL) This value cannot be modified | The notification email of the user who created the build. The value differs depending on how the build was created:<ul><li>**Buildkite dashboard:** Set based on who manually created the build.</li><li>**GitHub webhook:** Set from the **[unverified](#unverified-commits)** HEAD commit.</li><li>**Webhook:** Set based on which user is attached to the API Key used.</li></ul>**Example:** `cdanvers@kree-net.com` |
| `BUILDKITE_BUILD_CREATOR_TEAMS` [#](#BUILDKITE_BUILD_CREATOR_TEAMS) This value cannot be modified | A colon separated list of non-private team slugs that the build creator belongs to. The value differs depending on how the build was created:<ul><li>**Buildkite dashboard:** Set based on who manually created the build.</li><li>**GitHub webhook:** Set from the **[unverified](#unverified-commits)** HEAD commit.</li><li>**Webhook:** Set based on which user is attached to the API Key used.</li></ul>**Example:** `everyone:platform` |
| `BUILDKITE_BUILD_ID` [#](#BUILDKITE_BUILD_ID) This value cannot be modified | The UUID of the build.**Example:** `4735ba57-80d0-46e2-8fa0-b28223a86586` |
| `BUILDKITE_BUILD_NUMBER` [#](#BUILDKITE_BUILD_NUMBER) This value cannot be modified | The build number. This number increases with every build, and is guaranteed to be unique within each pipeline.**Example:** `1514` |
| `BUILDKITE_BUILD_PATH` [#](#BUILDKITE_BUILD_PATH) This value cannot be modified | The value of the `build-path` [agent configuration option](https://buildkite.com/docs/agent/v3/configuration).**Example:** `/var/lib/buildkite-agent/builds/` |
| `BUILDKITE_BUILD_URL` [#](#BUILDKITE_BUILD_URL) This value cannot be modified | The url for this build on Buildkite.**Example:** `https://buildkite.com/acme-inc/my-project/builds/1514` |
| `BUILDKITE_CANCEL_GRACE_PERIOD` [#](#BUILDKITE_CANCEL_GRACE_PERIOD)**Default**: `10` This value cannot be modified | The value of the `cancel-grace-period` [agent configuration option](https://buildkite.com/docs/agent/v3/configuration) in seconds. |
| `BUILDKITE_CANCEL_SIGNAL` [#](#BUILDKITE_CANCEL_SIGNAL)**Default**: `SIGTERM` | The value of the `cancel-signal` [agent configuration option](https://buildkite.com/docs/agent/v3/configuration). |
| `BUILDKITE_CLEAN_CHECKOUT` [#](#BUILDKITE_CLEAN_CHECKOUT)- **Possible values:**- `true`- `false` This value cannot be modified | Whether the build should perform a clean checkout. The variable is read during the default checkout phase of the bootstrap and can be overridden in `environment` or `pre-checkout` hooks. |
| `BUILDKITE_CLUSTER_ID` [#](#BUILDKITE_CLUSTER_ID) This value cannot be modified | The UUID value of the cluster, but only if the build has an associated `cluster_queue`. Otherwise, this environment variable is not set.**Example:** `4735ba57-80d0-46e2-8fa0-b28223a86586` |
| `BUILDKITE_CLUSTER_NAME` [#](#BUILDKITE_CLUSTER_NAME) This value cannot be modified | The name of the cluster in which the job is running.**Example:** `production` |
| `BUILDKITE_COMMAND` [#](#BUILDKITE_COMMAND) This value cannot be modified | The command that will be run for the job.**Example:** `script/buildkite/specs` |
| `BUILDKITE_COMMAND_EVAL` [#](#BUILDKITE_COMMAND_EVAL)- **Possible values:**- `true`- `false` This value cannot be modified | The opposite of the value of the `no-command-eval` [agent configuration option](https://buildkite.com/docs/agent/v3/configuration). |
| `BUILDKITE_COMMAND_EXIT_STATUS` [#](#BUILDKITE_COMMAND_EXIT_STATUS) This value cannot be modified | The exit code from the last command run in the command hook.**Example:** `-1` |
| `BUILDKITE_COMPUTE_TYPE` [#](#BUILDKITE_COMPUTE_TYPE) This value cannot be modified | `hosted` if the job is running on Hosted Agents, otherwise `self-hosted`.**Example:** `hosted` |
| `BUILDKITE_COMMIT` [#](#BUILDKITE_COMMIT) This value cannot be modified | The git commit object of the build. This is usually a 40-byte hexadecimal SHA-1 hash, but can also be a symbolic name like `HEAD`.**Example:** `83a20ec058e2fb00e7fa4558c4c6e81e2dcf253d` |
| `BUILDKITE_COMMIT_RESOLVED` [#](#BUILDKITE_COMMIT_RESOLVED)- **Possible values:**- `true`- `false` This value cannot be modified | Tells the Buildkite agent if BUILDKITE_COMMIT has been resolved to a full Git SHA and its metadata (author, subject, body) has been uploaded.**Example:** `"BUILDKITE_COMMIT_RESOLVED=true", "BUILDKITE_COMMIT_RESOLVED=false"` |
| `BUILDKITE_CONFIG_PATH` [#](#BUILDKITE_CONFIG_PATH)**Default**: `/buildkite/buildkite-agent.cfg` This value cannot be modified | The path to the agent config file. |
| `BUILDKITE_ENV_FILE` [#](#BUILDKITE_ENV_FILE) This value cannot be modified | The path to the file containing the job's environment variables.**Example:** `/tmp/job-env-36711a2a-711a-484e-b180-e1b3711a80cf51b18711a` |
| `BUILDKITE_GIT_CLEAN_FLAGS` [#](#BUILDKITE_GIT_CLEAN_FLAGS) | The value of the `git-clean-flags` [agent configuration option](https://buildkite.com/docs/agent/v3/configuration). The value can be modified by exporting the environment variable in the `environment` or `pre-checkout` hooks.**Example:** `-ffxdq` |
| `BUILDKITE_GIT_CLONE_FLAGS` [#](#BUILDKITE_GIT_CLONE_FLAGS) | The value of the `git-clone-flags` [agent configuration option](https://buildkite.com/docs/agent/v3/configuration). The value can be modified by exporting the environment variable in the `environment` or `pre-checkout` hooks.**Example:** `-v` |
| `BUILDKITE_GIT_FETCH_FLAGS` [#](#BUILDKITE_GIT_FETCH_FLAGS) | The value of the `git-fetch-flags` [agent configuration option](https://buildkite.com/docs/agent/v3/configuration). The value can be modified by exporting the environment variable in the `environment` or `pre-checkout` hooks.**Example:** `-v --prune` |
| `BUILDKITE_GIT_SUBMODULES` [#](#BUILDKITE_GIT_SUBMODULES)- **Possible values:**- `true`- `false` This value cannot be modified | The opposite of the value of the `no-git-submodules` [agent configuration option](https://buildkite.com/docs/agent/v3/configuration). |
| `BUILDKITE_GITHUB_DEPLOYMENT_ID` [#](#BUILDKITE_GITHUB_DEPLOYMENT_ID) This value cannot be modified | The GitHub deployment ID. Only available on builds triggered by a [GitHub Deployment](https://developer.github.com/v3/repos/deployments/).**Example:** `87972451` |
| `BUILDKITE_GITHUB_DEPLOYMENT_ENVIRONMENT` [#](#BUILDKITE_GITHUB_DEPLOYMENT_ENVIRONMENT) This value cannot be modified | The name of the GitHub deployment environment. Only available on builds triggered by a [GitHub Deployment](https://developer.github.com/v3/repos/deployments/).**Example:** `production` |
| `BUILDKITE_GITHUB_DEPLOYMENT_TASK` [#](#BUILDKITE_GITHUB_DEPLOYMENT_TASK) This value cannot be modified | The name of the GitHub deployment task. Only available on builds triggered by a [GitHub Deployment](https://developer.github.com/v3/repos/deployments/).**Example:** `deploy` |
| `BUILDKITE_GITHUB_DEPLOYMENT_PAYLOAD` [#](#BUILDKITE_GITHUB_DEPLOYMENT_PAYLOAD) This value cannot be modified | The GitHub deployment payload data as serialized JSON. Only available on builds triggered by a [GitHub Deployment](https://developer.github.com/v3/repos/deployments/).**Example:** `production` |
| `BUILDKITE_GROUP_ID` [#](#BUILDKITE_GROUP_ID) This value cannot be modified | The UUID of the [group step](https://buildkite.com/docs/pipelines/group-step) the job belongs to. This variable is only available if the job belongs to a group step.**Example:** `4a331026-8c9a-4714-aff0-8aa30211a34e` |
| `BUILDKITE_GROUP_KEY` [#](#BUILDKITE_GROUP_KEY) This value cannot be modified | The value of the `key` attribute of the [group step](https://buildkite.com/docs/pipelines/group-step) the job belongs to. This variable is only available if the job belongs to a group step.**Example:** `audit-tasks` |
| `BUILDKITE_GROUP_LABEL` [#](#BUILDKITE_GROUP_LABEL) This value cannot be modified | The label/name of the [group step](https://buildkite.com/docs/pipelines/group-step) the job belongs to. This variable is only available if the job belongs to a group step.**Example:** `🔒 Audit` |
| `BUILDKITE_HOOKS_PATH` [#](#BUILDKITE_HOOKS_PATH) This value cannot be modified | The value of the `hooks-path` [agent configuration option](https://buildkite.com/docs/agent/v3/configuration).**Example:** `/etc/buildkite-agent/hooks/` |
| `BUILDKITE_IGNORED_ENV` [#](#BUILDKITE_IGNORED_ENV) This value cannot be modified | A list of environment variables that have been set in your pipeline that are protected and will be overridden, used internally to pass data from the bootstrap to the agent.**Example:** `BUILDKITE_GIT_CLEAN_FLAGS` |
| `BUILDKITE_JOB_ID` [#](#BUILDKITE_JOB_ID) This value cannot be modified | The internal UUID Buildkite uses for this job.**Example:** `e44f9784-e20e-4b93-a21d-f41fd5869db9` |
| `BUILDKITE_JOB_CANCELLED` [#](#BUILDKITE_JOB_CANCELLED) This value cannot be modified | Is initially undefined, but gets defined with the value `true` by the agent when the job has been canceled. This value can be used by subsequent hooks to opt out of executing.**Example:** `true` |
| `BUILDKITE_JOB_LOG_TMPFILE` [#](#BUILDKITE_JOB_LOG_TMPFILE) This value cannot be modified | The path to a temporary file containing the logs for this job. Requires enabling the `enable-job-log-tmpfile` [agent configuration option](https://buildkite.com/docs/agent/v3/configuration).**Example:** `/tmp/buildkite_job_log1931317484` |
| `BUILDKITE_LABEL` [#](#BUILDKITE_LABEL) This value cannot be modified | The label/name of the current job.**Example:** `🔨 Specs` |
| `BUILDKITE_LAST_HOOK_EXIT_STATUS` [#](#BUILDKITE_LAST_HOOK_EXIT_STATUS) This value cannot be modified | The exit code of the last hook that ran, used internally by the hooks.**Example:** `-1` |
| `BUILDKITE_LOCAL_HOOKS_ENABLED` [#](#BUILDKITE_LOCAL_HOOKS_ENABLED)- **Possible values:**- `true`- `false` This value cannot be modified | The opposite of the value of the `no-local-hooks` [agent configuration option](https://buildkite.com/docs/agent/v3/configuration). |
| `BUILDKITE_MERGE_QUEUE_BASE_BRANCH` [#](#BUILDKITE_MERGE_QUEUE_BASE_BRANCH) This value cannot be modified | The target branch which the merge queue build will be merged into. `""` if not a merge queue build.**Example:** `main` |
| `BUILDKITE_MERGE_QUEUE_BASE_COMMIT` [#](#BUILDKITE_MERGE_QUEUE_BASE_COMMIT) This value cannot be modified | The [merge base](https://git-scm.com/docs/git-merge-base) of the proposed merge commit (`BUILDKITE_COMMIT`) for a merge queue build. `""` if not a merge queue build.**Example:** `44af8aa0007898d08f1bec401df7c077c1df0722` |
| `BUILDKITE_MESSAGE` [#](#BUILDKITE_MESSAGE) This value cannot be modified | The message associated with the build, usually the commit message or the message provided when the build is triggered. The value is empty when a message is not set. For example, when a user triggers a build from the Buildkite dashboard without entering a message, the variable returns an empty value.**Example:** `Added a great new feature` |
| `BUILDKITE_ORGANIZATION_ID` [#](#BUILDKITE_ORGANIZATION_ID) This value cannot be modified | The UUID of the organization.**Example:** `6abcd532-f9b7-41e9-8717-40fb75a82b5d` |
| `BUILDKITE_ORGANIZATION_SLUG` [#](#BUILDKITE_ORGANIZATION_SLUG) This value cannot be modified | The organization name on Buildkite as used in URLs.**Example:** `acme-inc` |
| `BUILDKITE_PARALLEL_JOB` [#](#BUILDKITE_PARALLEL_JOB) This value cannot be modified | The index of each parallel job created from a parallel build step, starting from 0. For a build step with `parallelism: 5`, the value would be 0, 1, 2, 3, and 4 respectively.**Example:** `0` |
| `BUILDKITE_PARALLEL_JOB_COUNT` [#](#BUILDKITE_PARALLEL_JOB_COUNT) This value cannot be modified | The total number of parallel jobs created from a parallel build step. For a build step with `parallelism: 5`, the value is 5.**Example:** `5` |
| `BUILDKITE_PIPELINE_DEFAULT_BRANCH` [#](#BUILDKITE_PIPELINE_DEFAULT_BRANCH) This value cannot be modified | The default branch for this pipeline.**Example:** `main` |
| `BUILDKITE_PIPELINE_ID` [#](#BUILDKITE_PIPELINE_ID) This value cannot be modified | The UUID of the pipeline.**Example:** `d18439cc-df59-45b0-97cc-98d7fb69d983` |
| `BUILDKITE_PIPELINE_NAME` [#](#BUILDKITE_PIPELINE_NAME) This value cannot be modified | The displayed pipeline name on Buildkite.**Example:** `my_project` |
| `BUILDKITE_PIPELINE_PROVIDER` [#](#BUILDKITE_PIPELINE_PROVIDER) This value cannot be modified | The ID of the source code provider for the pipeline's repository.**Example:** `github` |
| `BUILDKITE_PIPELINE_SLUG` [#](#BUILDKITE_PIPELINE_SLUG) This value cannot be modified | The pipeline slug on Buildkite as used in URLs.**Example:** `my-project` |
| `BUILDKITE_PIPELINE_TEAMS` [#](#BUILDKITE_PIPELINE_TEAMS) This value cannot be modified | A colon separated list of the pipeline's non-private team slugs.**Example:** `deploy:ops:production` |
| `BUILDKITE_PLUGIN_CONFIGURATION` [#](#BUILDKITE_PLUGIN_CONFIGURATION) This value cannot be modified | A JSON string holding the current plugin's configuration (as opposed to all the plugin configurations in the `BUILDKITE_PLUGINS` environment variable).**Example:** `{"image":"node:lts-alpine3.14"}` |
| `BUILDKITE_PLUGIN_NAME` [#](#BUILDKITE_PLUGIN_NAME) This value cannot be modified | The current plugin's name, with all letters in uppercase and any spaces replaced with underscores.**Example:** `DOCKER` |
| `BUILDKITE_PLUGINS` [#](#BUILDKITE_PLUGINS) This value cannot be modified | A JSON object containing a list plugins used in the step, and their configuration.**Example:** `[{"github.com/buildkite-plugins/docker-buildkite-plugin#v3.7.0":{"image":"node:lts-alpine3.14"}}]` |
| `BUILDKITE_PLUGINS_ENABLED` [#](#BUILDKITE_PLUGINS_ENABLED)- **Possible values:**- `true`- `false` This value cannot be modified | The opposite of the value of the `no-plugins` [agent configuration option](https://buildkite.com/docs/agent/v3/configuration). |
| `BUILDKITE_PLUGINS_PATH` [#](#BUILDKITE_PLUGINS_PATH) This value cannot be modified | The value of the `plugins-path` [agent configuration option](https://buildkite.com/docs/agent/v3/configuration).**Example:** `/etc/buildkite-agent/plugins/` |
| `BUILDKITE_PLUGIN_VALIDATION` [#](#BUILDKITE_PLUGIN_VALIDATION)**Default**: `false` This value cannot be modified | Whether to validate plugin configuration and requirements. The value can be modified by exporting the environment variable in the `environment` or `pre-checkout` hooks, or in a `pipeline.yml` file. It can also be enabled using the `no-plugin-validation` [agent configuration option](https://buildkite.com/docs/agent/v3/configuration). |
| `BUILDKITE_PULL_REQUEST` [#](#BUILDKITE_PULL_REQUEST) This value cannot be modified | The number of the pull request or `false` if not a pull request.**Example:** `123` |
| `BUILDKITE_PULL_REQUEST_BASE_BRANCH` [#](#BUILDKITE_PULL_REQUEST_BASE_BRANCH) This value cannot be modified | The base branch that the pull request is targeting or `""` if not a pull request.**Example:** `main` |
| `BUILDKITE_PULL_REQUEST_DRAFT` [#](#BUILDKITE_PULL_REQUEST_DRAFT) This value cannot be modified | Set to `true` when the pull request is a draft. This variable is only available if a build contains a draft pull request.**Example:** `true` |
| `BUILDKITE_PULL_REQUEST_REPO` [#](#BUILDKITE_PULL_REQUEST_REPO) This value cannot be modified | The repository URL of the pull request or `""` if not a pull request.**Example:** `git://github.com/acme-inc/my-project.git` |
| `BUILDKITE_REBUILT_FROM_BUILD_ID` [#](#BUILDKITE_REBUILT_FROM_BUILD_ID) This value cannot be modified | The UUID of the original build this was rebuilt from or `""` if not a rebuild.**Example:** `4735ba57-80d0-46e2-8fa0-b28223a86586` |
| `BUILDKITE_REBUILT_FROM_BUILD_NUMBER` [#](#BUILDKITE_REBUILT_FROM_BUILD_NUMBER) This value cannot be modified | The number of the original build this was rebuilt from or `""` if not a rebuild.**Example:** `1514` |
| `BUILDKITE_REFSPEC` [#](#BUILDKITE_REFSPEC) | A custom refspec for the buildkite-agent bootstrap script to use when checking out code. This variable can be modified by exporting the environment variable in the `environment` or `pre-checkout` hooks.**Example:** `+refs/weird/123abc:refs/local/weird/456` |
| `BUILDKITE_REPO` [#](#BUILDKITE_REPO) | The repository of your pipeline. This variable can be set by exporting the environment variable in the `environment` or `pre-checkout` hooks.**Example:** `git@github.com:acme-inc/my-project.git` |
| `BUILDKITE_REPO_MIRROR` [#](#BUILDKITE_REPO_MIRROR) This value cannot be modified | The path to the shared git mirror. Introduced in [v3.47.0](https://github.com/buildkite/agent/releases/tag/v3.47.0).**Example:** `/tmp/buildkite-git-mirrors` |
| `BUILDKITE_RETRY_COUNT` [#](#BUILDKITE_RETRY_COUNT) This value cannot be modified | How many times this job has been retried.**Example:** `0` |
| `BUILDKITE_S3_ACCESS_KEY_ID` [#](#BUILDKITE_S3_ACCESS_KEY_ID) This value cannot be modified | The access key ID for your S3 IAM user, for use with [private S3 buckets](https://buildkite.com/docs/agent/v3/cli-artifact#using-your-private-aws-s3-bucket). The variable is read by the `buildkite-agent artifact upload` command, and during the artifact upload phase of [command steps](https://buildkite.com/docs/pipelines/command-step#command-step-attributes). The value can only be set by exporting the environment variable in the `environment`, `pre-checkout` or `pre-command` hooks.**Example:** `AKIAIOSFODNN7EXAMPLE` |
| `BUILDKITE_S3_ACCESS_URL` [#](#BUILDKITE_S3_ACCESS_URL) This value cannot be modified | The access URL for your [private S3 bucket](https://buildkite.com/docs/agent/v3/cli-artifact#using-your-private-aws-s3-bucket), if you are using a proxy. The variable is read by the `buildkite-agent artifact upload` command, as well as during the artifact upload phase of [command steps](https://buildkite.com/docs/pipelines/command-step#command-step-attributes). The value can only be set by exporting the environment variable in the `environment`, `pre-checkout` or `pre-command` hooks.**Example:** `https://buildkite-artifacts.example.com/` |
| `BUILDKITE_S3_ACL` [#](#BUILDKITE_S3_ACL)**Default**: `public-read`- **Possible values:**- `private`- `public-read-write`- `public-read`- `authenticated-read`- `bucket-owner-read`- `bucket-owner-full-control` This value cannot be modified | The Access Control List to be set on artifacts being uploaded to your [private S3 bucket](https://buildkite.com/docs/agent/v3/cli-artifact#using-your-private-aws-s3-bucket). The variable is read by the `buildkite-agent artifact upload` command, as well as during the artifact upload phase of [command steps](https://buildkite.com/docs/pipelines/command-step#command-step-attributes). The value can only be set by exporting the environment variable in the `environment`, `pre-checkout` or `pre-command` hooks. Must be one of the following values which map to [S3 Canned ACL grants](https://docs.aws.amazon.com/AmazonS3/latest/dev/acl-overview.html#canned-acl). |
| `BUILDKITE_S3_DEFAULT_REGION` [#](#BUILDKITE_S3_DEFAULT_REGION)**Default**: `us-east-1` This value cannot be modified | The region of your [private S3 bucket](https://buildkite.com/docs/agent/v3/cli-artifact#using-your-private-aws-s3-bucket). The variable is read by the `buildkite-agent artifact upload` command, as well as during the artifact upload phase of [command steps](https://buildkite.com/docs/pipelines/command-step#command-step-attributes). The value can only be set by exporting the environment variable in the `environment`, `pre-checkout` or `pre-command` hooks. |
| `BUILDKITE_S3_SECRET_ACCESS_KEY` [#](#BUILDKITE_S3_SECRET_ACCESS_KEY) This value cannot be modified | The secret access key for your S3 IAM user, for use with [private S3 buckets](https://buildkite.com/docs/agent/v3/cli-artifact#using-your-private-aws-s3-bucket). The variable is read by the `buildkite-agent artifact upload` command, as well as during the artifact upload phase of [command steps](https://buildkite.com/docs/pipelines/command-step#command-step-attributes). The value can only be set by exporting the environment variable in the `environment`, `pre-checkout` or `pre-command` hooks. Do not print or export this variable anywhere except your agent hooks.**Example:** `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `BUILDKITE_S3_SSE_ENABLED` [#](#BUILDKITE_S3_SSE_ENABLED)**Default**: `false` This value cannot be modified | Whether to enable encryption for the artifacts in your [private S3 bucket](https://buildkite.com/docs/agent/v3/cli-artifact#using-your-private-aws-s3-bucket). The variable is read by the `buildkite-agent artifact upload` command, as well as during the artifact upload phase of [command steps](https://buildkite.com/docs/pipelines/command-step#command-step-attributes). The value can only be set by exporting the environment variable in the `environment`, `pre-checkout` or `pre-command` hooks. |
| `BUILDKITE_SHELL` [#](#BUILDKITE_SHELL) This value cannot be modified | The value of the `shell` [agent configuration option](https://buildkite.com/docs/agent/v3/configuration).**Example:** `"/bin/bash -e -c"` |
| `BUILDKITE_SOURCE` [#](#BUILDKITE_SOURCE)- **Possible values:**- `webhook`- `api`- `ui`- `trigger_job`- `schedule`- `local` This value cannot be modified | The source of the event that created the build. |
| `BUILDKITE_SSH_KEYSCAN` [#](#BUILDKITE_SSH_KEYSCAN)- **Possible values:**- `true`- `false` This value cannot be modified | The opposite of the value of the `no-ssh-keyscan` [agent configuration option](https://buildkite.com/docs/agent/v3/configuration). |
| `BUILDKITE_STEP_ID` [#](#BUILDKITE_STEP_ID) This value cannot be modified | A unique string that identifies a step.**Example:** `080b7d73-986d-4a39-a510-b34f9faf4710` |
| `BUILDKITE_STEP_KEY` [#](#BUILDKITE_STEP_KEY) This value cannot be modified | The value of the `key` [command step attribute](https://buildkite.com/docs/pipelines/command-step#command-step-attributes), a unique string set by you to identify a step.**Example:** `tests-06` |
| `BUILDKITE_TAG` [#](#BUILDKITE_TAG) This value cannot be modified | The name of the tag being built, if this build was triggered from a tag. When a build is triggered by a GitHub webhook tag `push` event, `BUILDKITE_BRANCH` will also be set to the name of the tag being built.**Example:** `v1.2.3` |
| `BUILDKITE_TIMEOUT` [#](#BUILDKITE_TIMEOUT) This value cannot be modified | The number of minutes until Buildkite automatically cancels this job, if a timeout has been specified, otherwise it `false` if no timeout is set. Jobs that time out with an exit status of 0 are marked as "passed".**Example:** `15` |
| `BUILDKITE_TRACING_BACKEND` [#](#BUILDKITE_TRACING_BACKEND)**Default**: `` This value cannot be modified | Set to `"datadog"` to send metrics to the [Datadog APM](https://docs.datadoghq.com/tracing/) using `localhost:8126`, or `DD_AGENT_HOST:DD_AGENT_APM_PORT`. Also available as a [buildkite agent configuration option.](https://buildkite.com/docs/agent/v3/configuration#configuration-settings)**Example:** `datadog` |
| `BUILDKITE_TRIGGERED_FROM_BUILD_ID` [#](#BUILDKITE_TRIGGERED_FROM_BUILD_ID) This value cannot be modified | The UUID of the build that triggered this build. This will be empty if the build was not triggered from another build.**Example:** `5aa7c894-c8c0-435b-bc17-13923b90f163` |
| `BUILDKITE_TRIGGERED_FROM_BUILD_NUMBER` [#](#BUILDKITE_TRIGGERED_FROM_BUILD_NUMBER) This value cannot be modified | The number of the build that triggered this build or `""` if the build was not triggered from another build.**Example:** `1264` |
| `BUILDKITE_TRIGGERED_FROM_BUILD_PIPELINE_SLUG` [#](#BUILDKITE_TRIGGERED_FROM_BUILD_PIPELINE_SLUG) This value cannot be modified | The slug of the pipeline that was used to trigger this build or `""` if the build was not triggered from another build.**Example:** `build-and-test` |
| `BUILDKITE_UNBLOCKER` [#](#BUILDKITE_UNBLOCKER) This value cannot be modified | The name of the user who unblocked the build.**Example:** `Carol Danvers` |
| `BUILDKITE_UNBLOCKER_EMAIL` [#](#BUILDKITE_UNBLOCKER_EMAIL) This value cannot be modified | The notification email of the user who unblocked the build.**Example:** `carol@nasa.gov` |
| `BUILDKITE_UNBLOCKER_ID` [#](#BUILDKITE_UNBLOCKER_ID) This value cannot be modified | The UUID of the user who unblocked the build.**Example:** `4735ba57-80d0-46e2-8fa0-b28223a86586` |
| `BUILDKITE_UNBLOCKER_TEAMS` [#](#BUILDKITE_UNBLOCKER_TEAMS) This value cannot be modified | A colon separated list of non-private team slugs that the user who unblocked the build belongs to.**Example:** `everyone:platform` |
| `CI` [#](#CI) This value cannot be modified | Always `true`. |

## [Deprecated environment variables](#deprecated-environment-variables)

The following environment variables have been deprecated.

| `BUILDKITE_PROJECT_PROVIDER` | This has been renamed to `BUILDKITE_PIPELINE_PROVIDER`. |
| --- | --- |
| `BUILDKITE_PROJECT_SLUG` | This has been renamed to `BUILDKITE_PIPELINE_SLUG`. |
| `BUILDKITE_SCRIPT_PATH` | This has been renamed to `BUILDKITE_COMMAND` |
| `BUILDKITE_STEP_IDENTIFIER` | This has been renamed to `BUILDKITE_STEP_KEY` |
| `BUILDBOX_AGENT_ID` | This has been renamed to `BUILDKITE_AGENT_ID` |
| `BUILDBOX_AGENT_NAME` | This has been renamed to `BUILDKITE_AGENT_NAME` |
| `BUILDBOX_AGENT_META_DATA_*` | This has been renamed to `BUILDKITE_AGENT_META_DATA_*` |
| `BUILDBOX_AGENT_ACCESS_TOKEN` | This has been renamed to `BUILDKITE_AGENT_ACCESS_TOKEN` |
| `BUILDBOX_AGENT_API_URL` | This has been removed with no replacement |

## [Defining your own](#defining-your-own)

You can define environment variables in your jobs in a few ways, depending on the nature of the value being set:

- Pipeline settings — for values that are _not secret_.
- [Build pipeline configuration](https://buildkite.com/docs/pipelines/configure/step-types/command-step) — for values that are _not secret_.
- An `environment` or `pre-command` [agent hook](https://buildkite.com/docs/agent/v3/hooks) — for values that are secret or agent-specific.

[Secrets in environment variables](#secrets-in-environment-variables)

Do not print or export secrets in your pipelines. See the [Secrets](https://buildkite.com/docs/pipelines/security/secrets/managing) documentation for further information and best practices.

## [Variable interpolation](#variable-interpolation)

Any environment variables set by Buildkite will be interpolated by the Agent.

If you're using the YAML Steps editor to define your pipeline, only the following subset of the environment variables are available:

- `BUILDKITE_BRANCH`
- `BUILDKITE_TAG`
- `BUILDKITE_MESSAGE`
- `BUILDKITE_COMMIT`
- `BUILDKITE_PIPELINE_SLUG`
- `BUILDKITE_PIPELINE_NAME`
- `BUILDKITE_PIPELINE_ID`
- `BUILDKITE_ORGANIZATION_SLUG`
- `BUILDKITE_TRIGGERED_FROM_BUILD_PIPELINE_SLUG`
- `BUILDKITE_REPO`
- `BUILDKITE_PULL_REQUEST`
- `BUILDKITE_PULL_REQUEST_BASE_BRANCH`
- `BUILDKITE_PULL_REQUEST_REPO`
- `BUILDKITE_MERGE_QUEUE_BASE_BRANCH`
- `BUILDKITE_MERGE_QUEUE_BASE_COMMIT`

Some variables, for example `BUILDKITE_BUILD_NUMBER`, cannot be supported in the YAML Step editor as the interpolation happens before the build is created. In those cases, interpolate them at the [runtime](https://buildkite.com/docs/pipelines/configure/environment-variables#runtime-variable-interpolation).

Alternatively, You can also access the rest of the Buildkite [environment variables](https://buildkite.com/docs/pipelines/configure/environment-variables#buildkite-environment-variables) by using a `pipeline.yml` file. Either define your entire pipeline in the YAML file, or you do a [pipeline upload](https://buildkite.com/docs/agent/v3/cli-pipeline) part way through your build that adds only the steps that use environment variables. See the [dynamic pipelines](https://buildkite.com/docs/pipelines/configure/dynamic-pipelines) docs for more information about adding steps with pipeline uploads.

## [Runtime variable interpolation](#runtime-variable-interpolation)

When using environment variables that will be evaluated at run-time, make sure you escape the `$` character using `$$` or `\$`. For example:

```
- command: "deploy.sh $$SERVER"
  env:
    SERVER: "server-a"
```

Further details about environment variable interpolation can be found in the [pipeline upload](https://buildkite.com/docs/agent/v3/cli-pipeline#environment-variable-substitution) CLI guide.

## [Environment variable precedence](#environment-variable-precedence)

You can set environment variables in lots of different places, and which ones take precedence can get a little confusing. There are many different levels at which environment variables are merged together. The following walkthrough and examples demonstrate the order in which variables are combined, as if you had set variables in every available place.

### [Job environment](#environment-variable-precedence-job-environment)

When a job runs on an agent, the first combination of environment variables happens in the job environment itself. This is the environment you can see in a job's Environment tab in the Buildkite dashboard, and the one returned by the REST and GraphQL APIs.

If you are not using YAML Steps, the precedence of environment variables is different from the list below.

Please [migrate your pipelines](https://buildkite.com/docs/pipelines/tutorials/pipeline-upgrade) to use YAML steps.

The job environment is made by merging the following sets of values, where values in each successive set take precedence:

| _Pipeline_ | Optional variables set by you on a pipeline on the Pipeline Settings page |
| --- | --- |
| _Build_ | Optional variables set by you on the build when creating a new build in the UI or using the REST API |
| _Step_ | Optional variables set by you on a step in the YAML steps editor or a pipeline.yml file |
| _Standard_ | The set of variables provided by Buildkite to every job |

For example, if you had configured the following environment variables:

| _Pipeline_ | `MY_ENV1="a"` |
| --- | --- |
| _Build_ | `MY_ENV1="b"` |
| _Step_ | `MY_ENV1="c"` |

In the final job environment, the value of `MY_ENV1` would be `"c"`.

#### Setting variables in a pipeline.yml

There are two places in a pipeline.yml file that you can set environment variables:

1. In the `env` attribute of command and trigger steps.
2. In the `env` attribute at the top of the yaml file, before you define your pipeline's steps.

Defining an environment variable at the top of your yaml file will set that variable on each of the command steps in the pipeline that have not already started running, and is equivalent to setting the `env` attribute on every step. This includes further pipeline uploads through `buildkite-agent pipeline upload`.

[Concurrent pipeline uploads and environment variables](#concurrent-pipeline-uploads-and-environment-variables)

Concurrent pipeline uploads with build-level environment variables can cause unpredictable behavior by modifying the environment for steps that haven't started yet.

This affects steps running after pipeline uploads, signed pipeline steps (where environment variables affect signature verification), and jobs that depend on specific environment variable values.

Issues typically occur when multiple pipeline uploads that include build-level environment variables happen at the same time or set the same environment variable to different values.

#### Setting variables in a Trigger step

Environment variables are not automatically passed through to builds created with [trigger steps](https://buildkite.com/docs/pipelines/configure/step-types/trigger-step). To set build-level environment variables on triggered builds, set the trigger step's `env` attribute.

### [Agent environment](#environment-variable-precedence-agent-environment)

Separate to the job's base environment, your `buildkite-agent` process has an environment of its own. This is made up of:

- operating system environment variables
- any variables you set on your agent when you started it
- any environment variables that were inherited from how you started the process (for example, systemd sets some env vars for you)

For a list of variables and configuration flags, you can set on your agent, see the Buildkite agent's [start command documentation](https://buildkite.com/docs/agent/v3/cli-start).

When using the [Agent Stack for Kubernetes](https://buildkite.com/docs/agent/v3/agent-stack-k8s) controller, environment variables declared as part of a PodSpec will also take precedence when the Kubernetes job is created. Learn more about this in [Kubernetes PodSpec generation](https://buildkite.com/docs/agent/v3/agent-stack-k8s/podspec#kubernetes-podspec-generation).

### [Job runtime environment](#environment-variable-precedence-job-runtime-environment)

Once the job is accepted by an agent, more environment merging happens. Starting with the environment that we put together in the [Job Environment section](#environment-variable-precedence-job-environment), we merge in some of the variables from the agent environment.

Not all variables from the agent are available in the job runtime. For example, we remove the agent's registration token and replace it with a build session token that has limited permissions. This new session token is used when you run the `artifact`, `meta-data` and `pipeline` commands inside the job.

After the agent variables have been merged, the bootstrap script is run.

The bootstrap runs any hooks that have been defined by your [agent](https://buildkite.com/docs/agent/v3/hooks#hook-locations-agent-hooks), your [repository](https://buildkite.com/docs/agent/v3/hooks#hook-locations-repository-hooks) or [plugins](https://buildkite.com/docs/agent/v3/hooks#hook-locations-plugin-hooks). Variables that are set in these hooks will be merged into the runtime environment, and will override any previous values that are set.

[Take care with environment variables in hooks](#take-care-with-environment-variables-in-hooks)

Variables that are defined in hooks can override anything that exists in the environment.

This is the environment your command runs in 🎉

Finally, if your job's commands make any changes to the environment, those changes will only survive as long as the script is running.