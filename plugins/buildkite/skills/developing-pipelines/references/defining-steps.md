---
title: "Defining your pipeline steps | Buildkite Documentation"
meta:
  "og:description": "Pipeline steps are defined in YAML and are either stored in Buildkite or in your repository using a pipeline.yml file."
  "og:title": "Defining your pipeline steps"
  description: "Pipeline steps are defined in YAML and are either stored in Buildkite or in your repository using a pipeline.yml file."
---

# Defining your pipeline steps

Pipeline steps are defined in YAML and are either stored in Buildkite or in your repository using a `pipeline.yml` file.

Defining your pipeline steps in a `pipeline.yml` file gives you access to more configuration options and environment variables than the web interface, and allows you to version, audit and review your build pipelines alongside your source code.

## [Getting started](#getting-started)

On the **Pipelines** page, select **New pipeline** to begin creating a new pipeline.

The required fields are **Name** and **Git Repository**.

![Screenshot of the 'New Pipeline' setup form](https://buildkite.com/docs/assets/new-pipeline-setup-040defe3.png)

You can set up webhooks at this point, but this step is optional. These webhook setup instructions can be found in pipeline settings on your specific repository provider page.

Both the REST API and GraphQL API can be used to create a pipeline programmatically. See the [Pipelines REST API](https://buildkite.com/docs/apis/rest-api/pipelines) and the [GraphQL API](https://buildkite.com/docs/apis/graphql-api) for details and examples.

## [Adding steps](#adding-steps)

There are two ways to define steps in your pipeline: using the YAML step editor in Buildkite or with a `pipeline.yml` file. The web steps visual editor is still available if you haven't migrated to [YAML steps](https://buildkite.com/changelog/99-introducing-the-yaml-steps-editor) but will be deprecated in the future.

If you have not yet migrated to YAML Steps, you can do so on your pipeline's settings page. See the [Migrating to YAML steps guide](https://buildkite.com/docs/pipelines/tutorials/pipeline-upgrade) for more information about the changes and the migration process.

However you add steps to your pipeline, keep in mind that steps may run on different agents. It is good practice to install your dependencies in the same step that you run them.

## [Step defaults](#step-defaults)

If you're using [YAML steps](https://buildkite.com/docs/pipelines/tutorials/pipeline-upgrade), you can set defaults which will be applied to every command step in a pipeline unless they are overridden by the step itself. You can set default agent properties and default environment variables:

- `agents` - A map of agent characteristics such as `os` or `queue` that restrict what agents the command will run on
- `env` - A map of [environment variables](https://buildkite.com/docs/pipelines/configure/environment-variables) to apply to all steps

[Environment variable precedence](#environment-variable-precedence)

Because you can set environment variables in many different places, be sure to check [environment variable precedence](https://buildkite.com/docs/pipelines/configure/environment-variables#environment-variable-precedence) to ensure your environment variables work as expected.

For example, to set steps `do-something.sh` and `do-something-else.sh` to use the `something` queue and the step `do-another-thing.sh` to use the `another` queue:

### [YAML steps editor](#step-defaults-yaml-steps-editor)

To add steps using the YAML editor, click the 'Edit Pipeline' button on the Pipeline Settings page.

Starting your YAML with the `steps` object, you can add as many steps as you require of each different type. Quick reference documentation and examples for each step type can be found in the sidebar on the right.

### [pipeline.yml file](#step-defaults-pipeline-dot-yml-file)

Before getting started with a `pipeline.yml` file, you'll need to tell Buildkite where it will be able to find your steps.

In the YAML steps editor in your Buildkite dashboard, add the following YAML:

```
steps:
  - label: ":pipeline: Pipeline upload"
    command: buildkite-agent pipeline upload
```

When you eventually run a build from this pipeline, this step will look for a directory called `.buildkite` containing a file named `pipeline.yml`. Any steps it finds inside that file will be [uploaded to Buildkite](https://buildkite.com/docs/agent/v3/cli-pipeline#uploading-pipelines) and will appear during the build.

When using WSL2 or PowerShell Core, you cannot add a `buildkite-agent pipeline upload` command step directly in the YAML steps editor. To work around this, there are two options:

- Use the YAML steps editor alone

- Place the `buildkite-agent pipeline upload` command in a script file. In the YAML steps editor, add a command to run that script file. It will upload your pipeline.

Create your `pipeline.yml` file in a `.buildkite` directory in your repo.

If you're using any tools that ignore hidden directories, you can store your `pipeline.yml` file either in the top level of your repository, or in a non-hidden directory called `buildkite`. The upload command will search these places if it doesn't find a `.buildkite` directory.

The following example YAML defines a pipeline with one command step that will echo 'Hello' into your build log:

With the above example code in a `pipeline.yml` file, commit and push the file up to your repository. If you have set up webhooks, this will automatically create a new build. You can also create a new build using the 'New Build' button on the pipeline page.

![Screenshot of the build passing with pipeline upload step first, and then the example step](https://buildkite.com/docs/assets/show-example-test-6d6a2b0d.png)

For more example steps and detailed configuration options, see the example `pipeline.yml` below, or the step type specific documentation:

- [command steps](https://buildkite.com/docs/pipelines/configure/step-types/command-step)
- [wait steps](https://buildkite.com/docs/pipelines/configure/step-types/wait-step)
- [block steps](https://buildkite.com/docs/pipelines/configure/step-types/block-step)
- [input steps](https://buildkite.com/docs/pipelines/configure/step-types/input-step)
- [trigger steps](https://buildkite.com/docs/pipelines/configure/step-types/trigger-step)
- [group steps](https://buildkite.com/docs/pipelines/configure/step-types/group-step)

If your pipeline has more than one step and you have multiple agents available to run them, they will automatically run at the same time. If your steps rely on running in sequence, you can separate them with [wait steps](https://buildkite.com/docs/pipelines/configure/step-types/wait-step). This will ensure that any steps before the 'wait' are completed before steps after the 'wait' are run.

[Explicit dependencies in uploaded steps](#explicit-dependencies-in-uploaded-steps)

If a step [depends](https://buildkite.com/docs/pipelines/configure/dependencies) on an upload step, then all steps uploaded by that step become dependencies of the original step. For example, if step B depends on step A, and step A uploads step C, then step B will also depend on step C.

When a step is run by an agent, it will be run with a clean checkout of the pipeline's repository. If your commands or scripts rely on the output from previous steps, you will need to either combine them into a single script or use [artifacts](https://buildkite.com/docs/pipelines/configure/artifacts) to pass data between steps. This enables any step to be picked up by any agent and run steps in parallel to speed up your build.

## [Build states](#build-states)

When you run a pipeline, a build is created. The following diagram shows you how builds progress from start to end.

![Build state diagram](https://buildkite.com/docs/assets/build-states-d2fbd4e7.png)

A build state can be one of of the following values:

`creating`, `scheduled`, `running`, `passed`, `failing`, `failed`, `blocked`, `canceling`, `canceled`, `skipped`, `not_run`.

You can query for `finished` builds to return builds in any of the following states: `passed`, `failed`, `blocked`, or `canceled`.

When a [triggered build](https://buildkite.com/docs/pipelines/configure/step-types/trigger-step) fails, the step that triggered it will be stuck in the `running` state forever.

When all the steps in a build are skipped (either by using skip attribute or by using `if` condition), the build state will be marked as `not_run`.

Unlike the [`notify` attribute](https://buildkite.com/docs/pipelines/configure/notifications), the build state value for a [`steps` attribute](https://buildkite.com/docs/pipelines/configure/defining-steps) may differ depending on the state of a pipeline. For example, when a build is blocked within a `steps` section, the `state` value in the [API response for getting a build](https://buildkite.com/docs/apis/rest-api/builds#get-a-build) retains its last value (for example, `passed`), rather than having the value `blocked`, and instead, the response also returns a `blocked` field with a value of `true`.

### [Build timestamps](#build-states-build-timestamps)

Each build has several timestamps that track its lifecycle from creation to completion. The expected chronological order is: `created_at` → `scheduled_at` → `started_at` → `finished_at`.

| Timestamp | Description |
| --- | --- |
| `created_at` | When the build record was initially created in the database. This happens when a build is first triggered (via API, webhook, UI, etc.) and the build enters the `creating` state. |
| `scheduled_at` | When the build is scheduled to run. For scheduled builds (triggered from pipeline schedules), this represents the intended execution time. |
| `started_at` | When the build begins executing (transitions from `scheduled` to `started` state). This occurs when the first job starts running, marking the build as active. |
| `finished_at` | When the build reaches a terminal state (`passed`, `failed`, `canceled`, `skipped`, or `not_run`). This is set when all jobs are complete and the build's final state is determined. |

[Builds with job retries](#builds-with-job-retries)

A build's `started_at` timestamp can be more recent than some of its job's `started_at` timestamps. This occurs when builds move from terminal states back to non-terminal states when failed jobs are retried.

## [Job states](#job-states)

When you run a pipeline, a build is created. Each of the steps in the pipeline ends up as a job in the build, which then get distributed to available agents. Job states have a similar flow to [build states](#build-states) but with a few extra states. The following diagram shows you how jobs progress from start to end.

[API state differences](#api-state-differences)

The table of job states below describes the internal lifecycle states, where `finished` is the terminal state. The [REST API](https://buildkite.com/docs/apis/rest-api) flattens `finished` into `passed` or `failed` based on the job's exit status, so `jobs[].state` will be `passed` or `failed` rather than `finished`. The [GraphQL API](https://buildkite.com/docs/apis/graphql-api) uses `finished` for all completed jobs, regardless of exit status.

![Job state diagram](https://buildkite.com/docs/assets/job-states-df6e80de.png)

| Job state | Description |
| --- | --- |
| `pending` | The job has just been created and doesn't have a state yet. |
| `waiting` | The job is waiting on a wait step to finish. |
| `waiting_failed` | The job was in a `waiting` state when the build failed. |
| `blocked` | The job is waiting on a block step to finish. |
| `blocked_failed` | The job was in a `blocked` state when the build failed. |
| `unblocked` | This block job has been manually unblocked. |
| `unblocked_failed` | This block job was in an `unblocked` state when the build failed. |
| `limiting` | The job is waiting on a concurrency group check before becoming either `limited` or `scheduled`. |
| `limited` | The job is waiting for jobs with the same concurrency group to finish. |
| `scheduled` | The job is scheduled and waiting for an agent. |
| `assigned` | The job has been assigned to an agent, and it's waiting for it to accept. |
| `accepted` | The job was accepted by the agent, and now it's waiting to start running. |
| `running` | The job is running. |
| `finished` | The job has finished (internal lifecycle state; REST API returns `passed` or `failed` instead). |
| `passed` | The job finished successfully (REST API only; returned instead of `finished` for successful jobs). |
| `failed` | The job finished with a failure (REST API only; returned instead of `finished` for failed jobs). |
| `canceling` | The job is currently canceling. |
| `canceled` | The job was canceled. |
| `timing_out` | The job is timing out for taking too long. |
| `timed_out` | The job timed out. |
| `skipped` | The job was skipped. |
| `broken` | The job's configuration means that it can't be run. |
| `expired` | The job expired before it was started on an agent. |
| `platform_limiting` | The job is waiting for limits imposed by Buildkite to be checked before moving to `platform_limited` or `scheduled`. |
| `platform_limited` | The job is waiting for capacity within limits imposed by Buildkite to become available before moving to `scheduled`. |

As well as the states shown in the diagram, the following progressions can occur:

| can progress to `skipped` | can progress to `canceling` or `canceled` |
| --- | --- |
| `pending` | `accepted` |
| `waiting` | `pending` |
| `blocked` | `limiting` |
| `limiting` | `limited` |
| `limited` | `blocked` |
| `accepted` | `unblocked` |
| `broken` | `platform_limiting` |
| `platform_limiting` | `platform_limited` |
| `platform_limited` | |

Differentiating between `broken`, `skipped` and `canceled` states:

- Jobs become `broken` when their configuration prevents them from running. This might be because their branch configuration doesn't match the build's branch, or because a conditional returned false.
- This is distinct from `skipped` jobs, which might happen if a newer build is started and [build skipping](https://buildkite.com/docs/apis/rest-api/pipelines#create-a-yaml-pipeline) is enabled. Broadly, jobs break because of something inside the build, and are skipped by something outside the build.
- Jobs can be `canceled` intentionally, either using the Buildkite interface or one of the APIs.

Differentiating between `timing_out`, `timed_out`, and `expired` states:

- Jobs become `timing_out`, `timed_out` when a job starts running on an agent but doesn't complete within the timeout period.
- Jobs become `expired` when they reach the scheduled job expiry timeout before being picked up by an agent.

See [Build timeouts](https://buildkite.com/docs/pipelines/configure/build-timeouts) for information about setting timeout values.

[REST API state mapping](#rest-api-state-mapping)

The [REST API](https://buildkite.com/docs/apis/rest-api) maps the internal `finished` state to `passed` or `failed` based on the job's exit status. When querying job states via the REST API, you'll see `passed` or `failed` instead of `finished`. The REST API also lists `limiting` and `limited` as `scheduled` for legacy compatibility.

A job state can be one of the following values:

`pending`, `waiting`, `waiting_failed`, `blocked`, `blocked_failed`, `unblocked`, `unblocked_failed`, `limiting`, `limited`, `scheduled`, `assigned`, `accepted`, `running`, `finished`, `passed`, `failed`, `canceling`, `canceled`, `expired`, `timing_out`, `timed_out`, `skipped`, `broken`, `platform_limiting`, or `platform_limited`.

Note: `finished` is an internal lifecycle terminal state. The REST API maps `finished` to `passed` or `failed` based on the job's exit status, so REST API responses will display `passed` or `failed` instead of `finished`. The GraphQL API uses `finished` for all completed jobs, regardless of the exit status.

Each job in a build also has a footer that displays exit status information. It may include an exit signal reason, which indicates whether the Buildkite agent stopped or the job was canceled.

Exit status information is available in the [GraphQL API](https://buildkite.com/docs/apis/graphql-api) but not the [REST API](https://buildkite.com/docs/apis/rest-api).

### [Job timestamps](#job-states-job-timestamps)

Each job has several timestamps that track its lifecycle from creation to completion. The expected chronological order is: `created_at` → `scheduled_at` → `runnable_at` → `started_at` → `finished_at`.

| Timestamp | Description |
| --- | --- |
| `created_at` | When the job record was first created in the database. This happens when a build's pipeline is processed and jobs are created in the `pending` state. |
| `scheduled_at` | When the job was intended to run. This is set during initial job creation and defaults to the job's `created_at` timestamp. |
| `runnable_at` | When the job became ready for agent assignment and eligible to run. This is set when the job transitions to the `scheduled` state after resolving dependencies (for example, wait steps, manual blocks, concurrency limits, or other dependencies). |
| `started_at` | When an agent confirmed it had started running the job (and the job transitions to the `running` state). This occurs after the job has been `assigned` to an agent, `accepted` by the agent, and the agent sends the first log output indicating that the execution has begun. |
| `finished_at` | When the job reaches a terminal state (`finished`, `canceled`, `timed_out`, `skipped`, or `expired`). Transitioning to this state marks the completion of the job's execution, whether successful or not. |

### [Platform limits](#job-states-platform-limits)

Platform limits are restrictions imposed by Buildkite on usage within your Buildkite organization. Jobs will enter the `platform_limiting` and `platform_limited` states when these limits are being evaluated or enforced.

The following platform limits may apply:

- **Job concurrency limits**: A Buildkite organization on the [Personal](https://buildkite.com/pricing/) plan has a total concurrency limit of three jobs that applies across both [Buildkite hosted agents](https://buildkite.com/docs/pipelines/hosted-agents) and [self-hosted agents](https://buildkite.com/docs/pipelines/architecture). When jobs are scheduled beyond this limit, they will be queued using the platform limiting states. To remove or increase this limit for your Buildkite organization, at least [upgrade to the Pro plan](https://buildkite.com/organizations/%7E/billing/plan_changes/new?plan_id=platform_pro_monthly_plan) or reach out to Buildkite support at [support@buildkite.com](https://buildkite.com/mailto:support@buildkite.com) for help.

## [Example pipeline](#example-pipeline)

Here's a more complete example based on [the Buildkite agent's build pipeline](https://github.com/buildkite/agent/blob/main/.buildkite/pipeline.yml). It contains script commands, wait steps, block steps, and automatic artifact uploading:

## [Step types](#step-types)

Buildkite pipelines are made up of the following step types:

- [Command step](https://buildkite.com/docs/pipelines/configure/step-types/command-step)
- [Wait step](https://buildkite.com/docs/pipelines/configure/step-types/wait-step)
- [Block step](https://buildkite.com/docs/pipelines/configure/step-types/block-step)
- [Input step](https://buildkite.com/docs/pipelines/configure/step-types/input-step)
- [Trigger step](https://buildkite.com/docs/pipelines/configure/step-types/trigger-step)
- [Group step](https://buildkite.com/docs/pipelines/configure/step-types/group-step)

## [Customizing the pipeline upload path](#customizing-the-pipeline-upload-path)

By default the pipeline upload step reads your pipeline definition from `.buildkite/pipeline.yml` in your repository. You can specify a different file path by adding it as the first argument:

```
steps:
  - label: ":pipeline: Pipeline upload"
    command: buildkite-agent pipeline upload .buildkite/deploy.yml
```

A common use for custom file paths is when separating test and deployment steps into two separate pipelines. Both `pipeline.yml` files are stored in the same repo and both Buildkite pipelines use the same repo URL. For example, your test pipeline's upload command could be:

```
buildkite-agent pipeline upload .buildkite/pipeline.yml
```

And your deployment pipeline's upload command could be:

```
buildkite-agent pipeline upload .buildkite/pipeline.deploy.yml
```

For a list of all command line options, see the [buildkite-agent pipeline upload](https://buildkite.com/docs/agent/v3/cli-pipeline#uploading-pipelines) documentation.

## [Targeting specific agents](#targeting-specific-agents)

To run [command steps](https://buildkite.com/docs/pipelines/configure/step-types/command-step) only on specific agents:

1. In the agent configuration file, [tag the agent](https://buildkite.com/docs/agent/v3/cli-start#setting-tags)
2. In the pipeline command step, [set the agent property](https://buildkite.com/docs/agent/v3/cli-start#agent-targeting) in the command step

For example to run commands only on agents running on macOS:

## [Further documentation](#further-documentation)

You can also upload pipelines from the command line using the `buildkite-agent` command line tool. See the [buildkite-agent pipeline documentation](https://buildkite.com/docs/agent/v3/cli-pipeline) for a full list of the available parameters.