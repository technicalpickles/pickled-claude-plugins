---
title: "Job prioritization | Buildkite Documentation"
meta:
  "og:description": "By default, jobs are dispatched (taken from the queue and assigned to an agent) on a first-in-first-out basis. However, job priority and pipeline upload time can affect that order."
  "og:title": "Job prioritization"
  description: "By default, jobs are dispatched (taken from the queue and assigned to an agent) on a first-in-first-out basis. However, job priority and pipeline upload time can affect that order."
---

# Job prioritization

By default, jobs are dispatched (taken from the queue and assigned to an agent) on a first-in-first-out basis. However, job priority and pipeline upload time can affect that order.

This is not the case for [Buildkite hosted agents](https://buildkite.com/docs/pipelines/hosted-agents), where jobs are assigned and dispatched at the time they are run.

## [Prioritizing specific jobs](#prioritizing-specific-jobs)

Job `priority` is 0 by default, you can prioritize or deprioritize jobs by assigning them a higher or lower integer value. For example:

Job priority is considered before jobs are dispatched to [agent queues](https://buildkite.com/docs/agent/v3/queues), so jobs with higher priority are assigned before jobs with lower priority, regardless of which has been longest in the queue. Priority only applies to command jobs, including plugin commands.

## [Prioritizing whole builds](#prioritizing-whole-builds)

The `priority` key can be set as a top-level value, which applies it to all steps in the pipeline that do not have their own `priority` key set. This is useful when an entire pipeline requires a higher priority than others. For example:

The `emergency fix` step runs before _any step of any other running pipeline_ within your organization, unless one of these other pipeline steps has a priority greater than 100. If all available agents are running jobs, an appropriate agent will run the `emergency fix` step _only_ after its current job completes running.

Prioritizing whole builds comes in handy when you need to reduce the number of agents (for example, to reduce costs over a weekend due to fewer available team members) but want to ensure any builds created on a critical pipeline are not left waiting for agents to run their jobs.

## [Job dispatch precedence](#job-dispatch-precedence)

Jobs are dispatched in the following order:

1. Job priority in descending order, highest number to lowest (`priority`)
2. Date and time scheduled in ascending order, oldest to most recent (`scheduled_at`). Note that jobs inherit `scheduled_at` from pipeline upload jobs, meaning jobs that are uploaded by a pipeline in an older build will be dispatched before builds created after that, and the value of `scheduled_at` cannot be modified.
3. Upload order in pipeline, first to last.
4. Internal id in ascending order, used as a tie breaker if all other value are the same, meaning older jobs will be dispatched first.

## [Example](#example)

Here's an example of prioritizing jobs running on a default branch before pull request jobs: