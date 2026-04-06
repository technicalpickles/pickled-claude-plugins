---
title: "Triggering notifications | Buildkite Documentation"
meta:
  "og:description": "The notify attribute allows you to trigger build notifications to different services. You can also choose to conditionally send notifications based on pipeline events like build state."
  "og:title": "Triggering notifications"
  description: "The notify attribute allows you to trigger build notifications to different services. You can also choose to conditionally send notifications based on pipeline events like build state."
---

# Triggering notifications

The `notify` attribute allows you to trigger build notifications to different services. You can also choose to conditionally send notifications based on pipeline events like build state.

Add notifications to your pipeline with the `notify` attribute. This sits at the same level as `steps` in your pipeline YAML.

For example, to send a notification email every time a build is created:

Available notification types:

- [Basecamp](#basecamp-campfire-message): Post a message to a Basecamp Campfire. Requires a Basecamp Chatbot to be configured in your Basecamp organization.
- [Email](#email): Send an email to the specified email address.
- [GitHub commit status](#github-commit-status): Create a GitHub commit status.
- [GitHub check](#github-check): Create a GitHub check status.
- [PagerDuty](#pagerduty-change-events)
- [Slack](#slack-channel-and-direct-messages): Post a message to the specified Slack Channel. Requires a Slack Workspace or individual Slack notification services to be enabled for each channel.
- [Webhooks](#webhooks): Send a notification to the specified webhook URL.

These types of notifications are available at the following levels.

| Build | Step |
| --- | --- |
| Basecamp | Basecamp |
| Email | |
| GitHub commit status | GitHub commit status |
| GitHub check | GitHub check |
| PagerDuty | |
| Slack | Slack |
| Webhook | |

## [Conditional notifications](#conditional-notifications)

To only trigger notifications under certain conditions, add the `if` attribute.

For example, the following email notification will only be triggered if the build passes:

`build.state` conditionals cannot be used on step-level notifications as a step cannot know the state of the entire build.

See [Supported variables](https://buildkite.com/docs/pipelines/configure/conditionals#variable-and-syntax-reference-variables) for more conditional variables that can be used in the `if` attribute.

### [Step-level conditional notifications](#conditional-notifications-step-level-conditional-notifications)

You can use conditional notifications at the step level to send notifications only when specific step outcomes occur. This is useful for immediate notifications when individual steps complete:

See [Supported variables](https://buildkite.com/docs/pipelines/configure/conditionals#variable-and-syntax-reference-variables) for more conditional variables that can be used in the `if` attribute.

To trigger conditional notifications to a Slack channel, you will first need to configure [Conditional notifications for Slack](https://buildkite.com/docs/pipelines/integrations/notifications/slack#conditional-notifications).

## [Basecamp Campfire message](#basecamp-campfire-message)

To send notifications to a Basecamp Campfire, you'll need to set up a chatbot in Basecamp as well as adding the notification to your `pipeline.yml` file. Basecamp admin permission is required to setup your chatbot.

Campfire messages can only be sent using Basecamp 3.

1. Add a [chatbot](https://m.signalvnoise.com/new-in-basecamp-3-chatbots/) to the Basecamp project or team that you'll be sending notifications to.
2. Set up your chatbot with a name and an optional URL. If you'd like to include an image, you can find the Buildkite logo in our [Brand assets](https://buildkite.com/brand-assets).
3. On the next page of the chatbot setup, copy the URL that Basecamp provides in the `curl` code snippet.
4. Add a Basecamp notification to your pipeline using the `basecamp_campfire` attribute of the `notify` YAML block and the URL copied from your Basecamp chatbot:

You can also add Basecamp notifications at the step level:

The `basecamp_campfire` attribute accepts a single URL as a string.

Build-level Basecamp notifications happen at the following [events](https://buildkite.com/docs/apis/webhooks/pipelines#events), unless you restrict them using [conditionals](https://buildkite.com/docs/pipelines/configure/notifications#conditional-notifications):

- `build created`
- `build started`
- `build blocked`
- `build finished`
- `build skipped`

Step-level Basecamp notifications happen at the following [events](https://buildkite.com/docs/apis/webhooks/pipelines#events):

- `step.finished`
- `step.failing`

## [Email](#email)

Add an email notification to your pipeline using the `email` attribute of the `notify` YAML block:

You can only send email notifications on entire pipeline [events](https://buildkite.com/docs/apis/webhooks/pipelines#events), specifically upon `build.failing` and `build.finished`.

Restrict notifications to finished builds by adding a [conditional](#conditional-notifications):

The `email` attribute accepts a single email address as a string. To send notifications to more than one address, add each address as a separate email notification attribute:

## [GitHub commit status](#github-commit-status)

Pipelines using [a GitHub repository](https://buildkite.com/docs/pipelines/source_control/github) have built-in [GitHub commit status](https://docs.github.com/en/rest/commits/statuses) integration. However, you can add custom commit statuses using notifications.

GitHub commit statuses appear as simple pass/fail indicators on commits and pull requests. For more advanced features like detailed output and annotations, consider using a [GitHub check](#github-check) instead.

[Requirements](#requirements)

GitHub notifications require a full 40-character commit SHA. Builds with short commit SHA values or `HEAD` references will not trigger notifications until the commit SHA is resolved.

For more information on customizing commit statuses, see [Customizing commit statuses](https://buildkite.com/docs/pipelines/source_control/github#customizing-commit-statuses) in the GitHub integration documentation.

Add a GitHub commit status notification to your pipeline using the `github_commit_status` attribute of the `notify` YAML block:

You can also add GitHub commit status notifications at the step level:

### [GitHub commit status attributes](#github-commit-status-github-commit-status-attributes)

The `github_commit_status` attribute supports the following options:

- `context`: A string label to differentiate this status from other statuses. Defaults to `buildkite/[pipeline-slug]` for build-level notifications. For step-level notifications, the context is automatically generated based on the step.
- `blocked_builds_as_pending`: A boolean value that determines how blocked builds are reported. When `true`, blocked builds are reported as "pending". When `false`, blocked builds are reported as "success". Defaults to `false`.

Build-level GitHub commit status notifications happen at the following [events](https://buildkite.com/docs/apis/webhooks/pipelines#events), unless you restrict them using [conditionals](https://buildkite.com/docs/pipelines/configure/notifications#conditional-notifications):

- `build.failing`
- `build.finished`

Step-level GitHub commit status notifications happen at the following [events](https://buildkite.com/docs/apis/webhooks/pipelines#events):

- `step.failing`
- `step.finished`

## [GitHub check](#github-check)

Create a [GitHub check](https://docs.github.com/en/rest/checks) to provide detailed feedback on builds and steps with rich formatting, annotations, and summaries. This requires the pipeline is configured to use [a GitHub repository](https://buildkite.com/docs/pipelines/source_control/github) with the GitHub App integration.

GitHub checks provide richer status information than commit statuses, including the ability to display detailed output, annotations, and custom formatting. Unlike commit statuses, GitHub checks can show step-by-step progress, include formatted text and links, and provide inline code annotations.

[Requirements](#requirements)

GitHub checks require the GitHub App integration. If you're using OAuth-based GitHub integration, use [GitHub commit status](#github-commit-status) notifications instead.

GitHub notifications require a full 40-character commit SHA. Builds with short commit SHA values or `HEAD` references will not trigger notifications until the commit SHA is resolved.

Add a GitHub check notification to your pipeline using the `github_check` attribute of the `notify` YAML block:

You can also add GitHub check notifications at the step level:

### [GitHub check attributes](#github-check-github-check-attributes)

The `github_check` attribute supports the following options:

- `name`: The name of the check. Defaults to the pipeline name for build-level notifications, or auto-generated based on the step label/key for step-level notifications.
- `output`: An object containing detailed output information: `title` (a short title for the check output), `summary` (a summary of the check results), `text` (detailed information about the check results, supports Markdown), and `annotations` (an array of annotation objects for inline code comments).

### [GitHub check annotations](#github-check-github-check-annotations)

For step-level notifications, you can include annotations that appear as inline comments on specific lines of code in pull requests:

Each annotation object supports:

- `path`: The file path relative to the repository root
- `start_line`: The line number where the annotation starts
- `end_line`: The line number where the annotation ends
- `annotation_level`: The level of the annotation (`notice`, `warning`, or `failure`)
- `message`: The annotation message
- `start_column` (optional): The column number where the annotation starts
- `end_column` (optional): The column number where the annotation ends

### [Dynamic GitHub check updates](#github-check-dynamic-github-check-updates)

For step-level GitHub check notifications, you can dynamically update the check output during step execution using the `buildkite-agent step update` command:

This is particularly useful for displaying test results, code analysis findings, or other dynamic content that becomes available during the build process.

Build-level GitHub check notifications happen at the following [events](https://buildkite.com/docs/apis/webhooks/pipelines#events), unless you restrict them using [conditionals](https://buildkite.com/docs/pipelines/configure/notifications#conditional-notifications):

- `build.finished`
- `build.failing`

Step-level GitHub check notifications happen at the following [events](https://buildkite.com/docs/apis/webhooks/pipelines#events):

- `step.failing`
- `step.finished`

## [PagerDuty change events](#pagerduty-change-events)

If you've set up a [PagerDuty integration](https://buildkite.com/docs/pipelines/integrations/notifications/pagerduty) you can send change events from your pipeline using the `pagerduty_change_event` attribute of the `notify` YAML block:

Email notifications happen at the following [event](https://buildkite.com/docs/apis/webhooks/pipelines#events):

- `build finished`

Restrict notifications to passed builds by adding a [conditional](#conditional-notifications):

## [Slack channel and direct messages](#slack-channel-and-direct-messages)

You can set notifications:

- On step status and other non-build events, by extending your Slack or Slack Workspace notification service with the `notify` attribute in your `pipeline.yml`.
- On build status events in the Buildkite interface, by using your Slack notification service's **Build state filtering** settings.

Before adding a `notify` attribute to your `pipeline.yml`, ensure a Buildkite organization admin has set up either the [Slack Workspace](https://buildkite.com/docs/pipelines/integrations/notifications/slack-workspace) notification service (a once-off configuration for each workspace), or the required [Slack](https://buildkite.com/docs/pipelines/integrations/notifications/slack) notification services, to send notifications to a channel or a user. Buildkite customers on the [Enterprise](https://buildkite.com/pricing) plan can also select the [**Manage Notifications Services**](https://buildkite.com/organizations/%7E/security/pipelines) checkbox to allow their users to create, edit, or delete notification services.

- The _Slack Workspace_ notification service requires a once-off configuration (only one per Slack workspace) in Buildkite, and then allows you to notify specific Slack channels or users, or both, directly within relevant pipeline steps.
- The _Slack_ notification service requires you to first configure one or more of these services for a channel or user, along with the pipelines, branches and build states that these channels or users receive notifications for. Once configured, your pipelines will generate automated notifications whenever the conditions in these notification services are met. You can also use the `notify` attribute in your `pipeline.yml` file for more fine grained control, by mentioning specific channels and users in these attributes, as long as Slack notification services have been created for these channels and users. If you mention any channels or users in a pipeline `notify` attribute for whom a Slack notification service has not yet been configured, the notification will not be sent. For a simplified configuration experience, use the [Slack Workspace](https://buildkite.com/docs/pipelines/integrations/notifications/slack-workspace) notification service instead.

Learn more about these different [Slack Workspace](https://buildkite.com/docs/pipelines/integrations/notifications/slack-workspace) and [Slack](https://buildkite.com/docs/pipelines/integrations/notifications/slack) notification services within [Other integrations](https://buildkite.com/docs/pipelines/integrations).

Once a Slack channel or workspace has been configured in your organization, add a Slack notification to your pipeline using the `slack` attribute of the `notify` YAML block.

When using only a channel name, you must specify this name in quotes. Otherwise, the `#` will cause the channel name to be treated as a comment.

If you have a Slack notification service configured for a given Slack channel and you either rename this channel, or change the channel's visibility from public to private, then you will need to set up a new Slack notification service to accommodate this modification. This issue does not affect the Slack Workspace notification service, since only one service needs to be configured for a given Slack workspace.

### [Notify a channel in all workspaces](#slack-channel-and-direct-messages-notify-a-channel-in-all-workspaces)

You can notify a channel in all workspaces by providing the channel name in the `pipeline.yml`.

Build-level notifications to the `#general` channel of all configured workspaces:

Step-level notifications to the `#general` channel of all configured workspaces:

[Step-level vs build-level notifications](#step-level-vs-build-level-notifications)

A step-level notify step will ignore the requirements of a build-level notification. If a build-level notification condition is that it runs only on `main`, a step-level notification without branch conditionals will run on all branches.

### [Notify a user in all workspaces](#slack-channel-and-direct-messages-notify-a-user-in-all-workspaces)

You can notify a user in all workspaces configured through your Slack or Slack Workspace notification services by providing their username or user ID, respectively, in the `pipeline.yml`.

Unlike Slack notification service notifications, which are sent directly to the user's Slack account, the Slack Workspace notification service sends notifications to the user's **Buildkite Builds** app in Slack.

#### Build-level notifications

When using [Slack notification services](https://buildkite.com/docs/pipelines/integrations/notifications/slack), specify the user's handle (for example, `@someuser`) to notify this user about a build. The user will receive a notification in all Slack workspaces they have been configured for with this service type. For example:

or:

```
notify:
  - slack:
      channels: ["@someuser"]
```

or:

```
notify:
  - slack:
      channels:
        - "@someuser"
```

When using the [Slack Workspace notification service](https://buildkite.com/docs/pipelines/integrations/notifications/slack-workspace), specify the user's user ID (for example, `U12AB3C456D`) instead of their user handle (`@someuser`), to notify this user about a build in the configured Slack workspace. For example:

or:

```
notify:
  - slack:
      channels: ["U12AB3C456D"]
```

or:

```
notify:
  - slack:
      channels:
        - "U12AB3C456D"
```

#### Step-level notifications

When using the [Slack notification services](https://buildkite.com/docs/pipelines/integrations/notifications/slack), specify the user's handle (for example, `@someuser`) to notify this user about this step's job. The user will receive a notification in all Slack workspaces they have been configured for with this service type. For example:

When using the [Slack Workspace notification service](https://buildkite.com/docs/pipelines/integrations/notifications/slack-workspace), specify the user's user ID (for example, `U12AB3C456D`) instead of their user handle (`@someuser`), to notify this user about this step's job in the configured Slack workspace. For example:

### [Notify a channel in one workspace](#slack-channel-and-direct-messages-notify-a-channel-in-one-workspace)

You can notify one particular workspace and channel by specifying the workspace name.

Build-level notifications:

Step-level notifications:

### [Notify multiple teams and channels](#slack-channel-and-direct-messages-notify-multiple-teams-and-channels)

You can specify multiple teams and channels by listing them in the `channels` attribute.

Build-level notifications:

Step-level notifications:

### [Custom messages](#slack-channel-and-direct-messages-custom-messages)

You can define a custom message to send in the notification using the `message` attribute.

Build-level notifications:

Step-level notifications:

You can also send notifications with custom messages to specific users with the relevant syntax mentioned in [Notify a user in all workspaces](#slack-channel-and-direct-messages-notify-a-user-in-all-workspaces). Employ the appropriate user notification syntax based on your configured the Slack or Slack Workspace notification service(s).

### [Custom messages with user mentions](#slack-channel-and-direct-messages-custom-messages-with-user-mentions)

To mention a specific user in a custom message within a notification, use the `<@user-id>` annotation, substituting `userid` with the Slack user ID of the person to mention. See the [Slack documentation on mentioning users](https://api.slack.com/reference/surfaces/formatting#mentioning-users) for more details, including how to find a particular user's user ID. You can even mention user groups using the `<!subteam^$subteam-id>` annotation (where the first `subteam` is literal text)! See the [Slack documentation on mentioning user groups](https://api.slack.com/reference/surfaces/formatting#mentioning-groups) for more information.

Build-level notifications:

Step-level notifications:

[Build creator environment variable](#build-creator-environment-variable)

You cannot substitute `user` with the build creator environment variable value.

### [Conditional Slack notifications](#slack-channel-and-direct-messages-conditional-slack-notifications)

You can also add [conditionals](https://buildkite.com/docs/pipelines/configure/notifications#conditional-notifications) to restrict the events on which notifications are sent:

See [Supported variables](https://buildkite.com/docs/pipelines/configure/conditionals#variable-and-syntax-reference-variables) for more conditional variables that can be used in the `if` attribute.

You are able to use `pipeline.started_passing` and `pipeline.started_failing` in your if statements if you are using the [Slack Workspace](https://buildkite.com/docs/pipelines/integrations/notifications/slack-workspace) integration.

Build-level Slack notifications happen at the following [event](https://buildkite.com/docs/apis/webhooks/pipelines#events):

- `build.finished`
- `build.failing`

Step-level Slack notifications happen at the following [events](https://buildkite.com/docs/apis/webhooks/pipelines#events):

- `step.finished`
- `step.failing`

An example to deliver slack notification when a step is soft-failed:

### [Notify only on first failure](#slack-channel-and-direct-messages-notify-only-on-first-failure)

The `pipeline.started_failing` conditional is designed to only send notifications when a pipeline transitions from a passing state to a failing state - not for every failed build. This prevents excessive notifications, while ensuring teams are immediately alerted when something goes wrong.

#### When to use

The `pipeline.started_failing` conditional might be valuable for teams that:

- Want immediate alerts when something breaks but don't want repeated notifications for consecutive failures.
- Have flaky tests or environments where builds might fail multiple times in a row.
- Implement workflows where quick feedback on state changes is more important than being notified about every individual failure.

### [Notify only on first pass](#slack-channel-and-direct-messages-notify-only-on-first-pass)

The `pipeline.started_passing` conditional is designed to only send notifications when a pipeline transitions from a failing state to a passing state - not for every successful build. This prevents excessive notifications, while ensuring teams are immediately alerted when issues are resolved.

#### When to use

The `pipeline.started_passing` conditional might be valuable for teams that:

- Need to track when build issues are resolved after failures.
- Prefer to avoid notifications for builds that were already passing.

### [Notify on all failures and first successful pass](#slack-channel-and-direct-messages-notify-on-all-failures-and-first-successful-pass)

This combined pattern sends notifications for all failed builds and the first successful build after failures. It provides comprehensive failure coverage, while avoiding excessive notifications for consecutive successful builds.

You can add a branch filter to this conditional pattern to target specific branches:

Different messages can also be used to differentiate between failures and recoveries:

#### When to use

These conditionals might be valuable for teams that want to be notified about each build failure but avoid notifications for consecutive successful builds.

## [Webhooks](#webhooks)

Send a notification to a webhook URL from your pipeline using the `webhook` attribute of the `notify` YAML block:

The `webhook` attribute accepts a single webhook URL as a string. To send notifications to more than one endpoint, add each URL as a separate webhook attribute:

Webhook notifications happen at the following [events](https://buildkite.com/docs/apis/webhooks/pipelines#events), unless you restrict them using [conditionals](https://buildkite.com/docs/pipelines/configure/notifications#conditional-notifications):

- `build created`
- `build started`
- `build blocked`
- `build finished`

## [Build states](#build-states)

A build state can be one of of the following values:

`creating`, `scheduled`, `running`, `passed`, `failing`, `failed`, `blocked`, `canceling`, `canceled`, `skipped`, `not_run`.

You can query for `finished` builds to return builds in any of the following states: `passed`, `failed`, `blocked`, or `canceled`.

When a [triggered build](https://buildkite.com/docs/pipelines/configure/step-types/trigger-step) fails, the step that triggered it will be stuck in the `running` state forever.

When all the steps in a build are skipped (either by using skip attribute or by using `if` condition), the build state will be marked as `not_run`.

Unlike the [`notify` attribute](https://buildkite.com/docs/pipelines/configure/notifications), the build state value for a [`steps` attribute](https://buildkite.com/docs/pipelines/configure/defining-steps) may differ depending on the state of a pipeline. For example, when a build is blocked within a `steps` section, the `state` value in the [API response for getting a build](https://buildkite.com/docs/apis/rest-api/builds#get-a-build) retains its last value (for example, `passed`), rather than having the value `blocked`, and instead, the response also returns a `blocked` field with a value of `true`.

See the full [build states diagram](https://buildkite.com/docs/pipelines/configure/defining-steps#build-states) for more information on how builds transition between states.