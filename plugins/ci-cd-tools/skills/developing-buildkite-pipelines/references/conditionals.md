---
title: "Using conditionals | Buildkite Documentation"
meta:
  "og:description": "Using conditionals, you can run builds or steps only when specific conditions are met. Define boolean conditions using C-like expressions."
  "og:title": "Using conditionals"
  description: "Using conditionals, you can run builds or steps only when specific conditions are met. Define boolean conditions using C-like expressions."
---

# Using conditionals

Using conditionals, you can run builds or steps only when specific conditions are met. Define [boolean conditions using C-like expressions](#variable-and-syntax-reference).

You can define conditionals at the step level in your `pipeline.yml` or at the pipeline level in your Buildkite version control provider settings.

## [Conditionals in pipelines](#conditionals-in-pipelines)

You can have complete control over when to trigger pipeline builds by using conditional expressions to filter incoming webhooks. You need to define conditionals in the pipeline's **Settings** page for your repository provider to run builds only when expressions evaluate to `true`. For example, to run only when a pull request is targeting the main branch:

![Conditional Filtering settings](https://buildkite.com/docs/assets/conditionals-9a7b2932.png)

Pipeline-level build conditionals are evaluated before any other build trigger settings. If both a conditional and a branch filter are present, both filters must pass for a build to be created – first the pipeline-level limiting filter and then the conditional filter.

Conditionals are supported in [Bitbucket](https://buildkite.com/docs/pipelines/source-control/bitbucket), [Bitbucket Server](https://buildkite.com/docs/pipelines/source-control/bitbucket-server), [GitHub](https://buildkite.com/docs/pipelines/source-control/github), [GitHub Enterprise](https://buildkite.com/docs/pipelines/source-control/github-enterprise), and [GitLab](https://buildkite.com/docs/pipelines/source-control/gitlab) (including GitLab Community and GitLab Enterprise). You can add a conditional on your pipeline's **Settings** page in the Buildkite interface or using the REST API.

[Evaluating conditionals](#evaluating-conditionals)

Conditional expressions are evaluated at pipeline upload, not at step runtime.

## [Conditionals in steps](#conditionals-in-steps)

Use the `if` attribute in your step definition to conditionally run a step.

In the below example, the `tests` step will only be run if the build message does not contain the string "skip tests".

The `if` attribute can be used in any type of step, and with any of the supported expressions and parameters. However, it cannot be used at the same time as the `branches` attribute.

Be careful when defining conditionals within YAML. Many symbols have special meaning in YAML and will change the type of a value. You can avoid this by quoting your conditional as a string.

Multi-line conditionals can be added with the `|` character, and avoid the need for quotes:

Since `if` conditions are evaluated at the time of the pipeline upload, it's not possible to use the `if` attribute to conditionally run a step based on the result of another step.

[Plugin execution and conditionals](#plugin-execution-and-conditionals)

Step-level `if` conditions only prevent commands from running but they _do not_ affect plugins. Plugins run during the job lifecycle, before the conditional is evaluated. To conditionally run plugins, use either [group steps](#conditionally-running-plugins-with-group-steps) or [dynamic pipeline uploads](#conditionally-running-plugins-with-dynamic-uploads).

To run a step based on the result of another step, upload a new pipeline based on the `if` condition set up in the [command step](https://buildkite.com/docs/pipelines/configure/step-types/command-step) like in the example below:

## [Conditional notifications](#conditional-notifications)

To trigger [Build notifications](https://buildkite.com/docs/pipelines/configure/notifications#conditional-notifications) only under certain conditions, use the same `if` syntax as in your [Steps](https://buildkite.com/docs/pipelines/configure/conditionals#conditionals-in-steps).

For example, the following email notification will only be triggered if the build passes:

Note that conditional expressions on the build state are only available at the pipeline level. You can't use them at the step level.

## [Conditionally running plugins with group steps](#conditionally-running-plugins-with-group-steps)

To conditionally run plugins, use [group steps](https://buildkite.com/docs/pipelines/configure/step-types/group-step) rather than step-level `if` conditions. Group's conditional is evaluated before any steps within the group are created, which prevents plugin from executing entirely:

## [Conditionally running plugins with dynamic uploads](#conditionally-running-plugins-with-dynamic-uploads)

For complex conditional logic, use dynamic pipeline uploads with conditional logic running in a shell script before the steps with plugins are uploaded:

## [Conditionals and the broken state](#conditionals-and-the-broken-state)

Jobs become `broken` when their configuration prevents them from running. This might be because their [branch configuration](https://buildkite.com/docs/pipelines/configure/workflows/branch-configuration) doesn't match the build's branch, or because a conditional returned `false`. This is distinct from `skipped` jobs, which might happen if a newer build is started and build skipping is enabled. A rough explanation is that jobs break because of something _inside_ the build and are skipped by something _outside_ the build.

## [Variable and syntax reference](#variable-and-syntax-reference)

Evaluate expressions made up of [boolean operators](#variable-and-syntax-reference-operator-syntax) and [variables](#variable-and-syntax-reference-variables).

### [Operator syntax](#variable-and-syntax-reference-operator-syntax)

The following expressions are supported by the `if` attribute.

| Comparators | `== != =~ !~` |
| --- | --- |
| Logical operators | `\|\| &&` |
| Array operators | `includes` |
| Integers | `12345` |
| Strings | `'feature-branch' "feature-branch"` |
| Literals | `true false null` |
| Parentheses | `( )` |
| Regular expressions | `/^v1.0/` |
| Prefixes | `!` |
| Comments | `// This is a comment` |

[Formatting regular expressions](#formatting-regular-expressions)

When using regular expressions in conditionals, the regular expression must be on the right hand side, and the use of the `$` anchor symbol must be escaped to avoid [environment variable substitution](https://buildkite.com/docs/agent/v3/cli-pipeline#environment-variable-substitution). For example, to match branches ending in `"/feature"` the conditional statement would be `build.branch =~ /\/feature$$/`.

### [Variables](#variable-and-syntax-reference-variables)

The following variables are supported by the `if` attribute. Note that you cannot use [Build Meta-data](https://buildkite.com/docs/pipelines/configure/build-meta-data) in conditional expressions.

[Unverified commits](#unverified-commits)

Note that GitHub accepts [unsigned commits](https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification), including information about the commit author and passes them along to webhooks, so you should not rely on these for authentication unless you are confident that all of your commits are trusted.

| `build.author.email` | `String` | The **[unverified](#unverified-commits)** email address of the user who authored the build's commit |
| --- | --- | --- |
| `build.author.id` | `String` | The **[unverified](#unverified-commits)** ID of the user who authored the build's commit |
| `build.author.name` | `String` | The **[unverified](#unverified-commits)** name of the user who authored the build's commit |
| `build.author.teams` | `Array` | An **[unverified](#unverified-commits)** array of the team/s which the user who authored the build's commit is a member of |
| `build.branch` | `String` | The branch on which this build is created from |
| `build.commit` | `String` | The commit number of the commit the current build is based on |
| `build.creator.email` | `String` | The email address of the user who created the build. The value differs depending on how the build was created:<ul><li>**Buildkite dashboard:** Set based on who manually created the build.</li><li>**GitHub webhook:** Set from the **[unverified](#unverified-commits)** HEAD commit.</li><li>**Webhook:** Set based on which user is attached to the API Key used.</li></ul>For conditionals to use this variable, the user set must be a verified Buildkite user. |
| `build.creator.id` | `String` | The ID of the user who created the build. The value differs depending on how the build was created:<ul><li>**Buildkite dashboard:** Set based on who manually created the build.</li><li>**GitHub webhook:** Set from the **[unverified](#unverified-commits)** HEAD commit.</li><li>**Webhook:** Set based on which user is attached to the API Key used.</li></ul>For conditionals to use this variable, the user set must be a verified Buildkite user. |
| `build.creator.name` | `String` | The name of the user who created the build. The value differs depending on how the build was created:<ul><li>**Buildkite dashboard:** Set based on who manually created the build.</li><li>**GitHub webhook:** Set from the **[unverified](#unverified-commits)** HEAD commit.</li><li>**Webhook:** Set based on which user is attached to the API Key used.</li></ul>For conditionals to use this variable, the user set must be a verified Buildkite user. |
| `build.creator.teams` | `Array` | An array of the teams which the user who created the build is a member of. The value differs depending on how the build was created:<ul><li>**Buildkite dashboard:** Set based on who manually created the build.</li><li>**GitHub webhook:** Set from the **[unverified](#unverified-commits)** HEAD commit.</li><li>**Webhook:** Set based on which user is attached to the API Key used.</li></ul>For conditionals to use this variable, the user set must be a verified Buildkite user. |
| `build.env()` | `String`, `null` | This function returns the value of the environment passed as the first argument if that variable is set, or `null` if the environment variable is not set.<br> `build.env()` works with variables you've defined, and the following `BUILDKITE_*` variables:<br> `BUILDKITE_BRANCH`<br> `BUILDKITE_TAG`<br> `BUILDKITE_MESSAGE`<br> `BUILDKITE_COMMIT`<br> `BUILDKITE_PIPELINE_SLUG`<br> `BUILDKITE_PIPELINE_NAME`<br> `BUILDKITE_PIPELINE_ID`<br> `BUILDKITE_ORGANIZATION_SLUG`<br> `BUILDKITE_TRIGGERED_FROM_BUILD_ID`<br> `BUILDKITE_TRIGGERED_FROM_BUILD_NUMBER`<br> `BUILDKITE_TRIGGERED_FROM_BUILD_PIPELINE_SLUG`<br> `BUILDKITE_REBUILT_FROM_BUILD_ID`<br> `BUILDKITE_REBUILT_FROM_BUILD_NUMBER`<br> `BUILDKITE_REPO`<br> `BUILDKITE_PULL_REQUEST`<br> `BUILDKITE_PULL_REQUEST_BASE_BRANCH`<br> `BUILDKITE_PULL_REQUEST_REPO`<br> `BUILDKITE_MERGE_QUEUE_BASE_BRANCH`<br> `BUILDKITE_MERGE_QUEUE_BASE_COMMIT`<br> `BUILDKITE_GITHUB_DEPLOYMENT_ID`<br> `BUILDKITE_GITHUB_DEPLOYMENT_TASK`<br> `BUILDKITE_GITHUB_DEPLOYMENT_ENVIRONMENT`<br> `BUILDKITE_GITHUB_DEPLOYMENT_PAYLOAD`<br> |
| `build.id` | `String` | The ID of the current build |
| `build.message` | `String`, `null` | The current build's message |
| `build.number` | `Integer` | The number of the current build |
| `build.pull_request.base_branch` | `String`, `null` | The base branch that the pull request is targeting, otherwise `null` if the branch is not a pull request |
| `build.pull_request.id` | `String`, `null` | The number of the pull request, otherwise `null` if the branch is not a pull request |
| `build.pull_request.draft` | `Boolean`, `null` | If the pull request is a draft, otherwise `null` if the branch is not a pull request or the provider doesn't support draft pull requests |
| `build.pull_request.labels` | `Array` | An array of label names attached to the pull request |
| `build.pull_request.repository` | `String`, `null` | The repository URL of the pull request, otherwise `null` if the branch is not a pull request |
| `build.pull_request.repository.fork` | `Boolean`, `null` | If the pull request comes from a forked repository, otherwise `null` if the branch is not a pull request |
| `build.merge_queue.base_branch` | `String`, `null` | If a merge queue build, the target branch which the merge queue build will be merged into |
| `build.merge_queue.base_commit` | `String`, `null` | If a merge queue build, the [merge base](https://git-scm.com/docs/git-merge-base) of the proposed merge commit (`build.commit`) |
| `build.source` | `String` | The source of the event that created the build<br>_Available sources:_ `ui`, `api`, `webhook`, `trigger_job`, `schedule` |
| `build.state` | `String` | The state the current build is in<br>_Available states:_ `started`, `scheduled`, `running`, `passed`, `failed`, `failing`, `started_failing`, `blocked`, `canceling`, `canceled`, `skipped`, `not_run` |
| `build.tag` | `String`, `null` | The tag associated with the commit the current build is based on |
| `pipeline.default_branch` | `String`, `null` | The default branch of the pipeline the current build is from |
| `pipeline.id` | `String` | The ID of the pipeline the current build is from |
| `pipeline.repository` | `String`, `null` | The repository of the pipeline the current build is from |
| `pipeline.slug` | `String` | The slug of the pipeline the current build is from |
| `organization.id` | `String` | The ID of the organization the current build is running in |
| `organization.slug` | `String` | The slug of the organization the current build is running in |

[Using `build.env()` with custom environment variables](#using-build-dot-env-with-custom-environment-variables)

To access custom environment variables with the `build.env()` function, ensure that the [YAML pipeline steps editor](https://buildkite.com/changelog/32-defining-pipeline-build-steps-with-yaml) has been enabled in the Pipeline Settings menu.

The following step variables are also available for [conditional notifications](#conditional-notifications) only.

| `step.id` | `String` | The ID of the current step |
| --- | --- | --- |
| `step.key` | `String`, `null` | The key of the current step |
| `step.label` | `String`, `null` | The label of the current step |
| `step.type` | `String` | The type of the current step<br>_Available types:_ `command`, `wait`, `input`, `trigger`, `group` |
| `step.state` | `String` | The state of the current step<br>_Available states:_ `ignored`, `waiting_for_dependencies`, `ready`, `running`, `failing`, `finished` |
| `step.outcome` | `String` | The outcome of the current step<br>_Available outcomes:_ `neutral`, `passed`, `soft_failed`, `hard_failed`, `errored` |

## [Example expressions](#example-expressions)

To run only when the branch is `main` or `production`:

```
build.branch == "main" || build.branch == "production"
```

To run only when the branch is not `production`:

```
build.branch != "production"
```

To run only when the branch starts with `features/`:

```
build.branch =~ /^features\//
```

To run only when the branch ends with `/release-123`, such as `feature/release-123`:

```
build.branch =~ /\/release-123\$/
```

To run only when building a tag:

```
build.tag != null
```

To run only when building a tag beginning with a `v` and ends with a `.0`, such as `v1.0`:

```
// Using the tag variable
build.tag =~ /^v[0-9]+\.0\$/

// Using the env function
build.env("BUILDKITE_TAG") =~ /^v[0-9]+\.0\$/
```

To run only if the message doesn't contain `[skip tests]`, case insensitive:

```
build.message !~ /\[skip tests\]/i
```

To run only if the build was created from a schedule:

```
build.source == "schedule"
```

To run when the value of `CUSTOM_ENVIRONMENT_VARIABLE` is `value`:

```
build.env("CUSTOM_ENVIRONMENT_VARIABLE") == "value"
```

To run when the **[unverified](#unverified-commits)** build creator is in the `deploy` team:

```
build.creator.teams includes "deploy"
```

To run only non-draft pull requests:

```
!build.pull_request.draft
```

To run only on merge queue builds targeting the `main` branch:

```
build.merge_queue.base_branch == "main"
```