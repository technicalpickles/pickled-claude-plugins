---
title: "Controlling concurrency | Buildkite Documentation"
meta:
  "og:description": "Some tasks need to be run with very strict concurrency rules to ensure they don&#39;t collide with each other. Common examples for needing concurrency control are deployments, app releases and infrastructure tasks."
  "og:title": "Controlling concurrency"
  description: "Some tasks need to be run with very strict concurrency rules to ensure they don&#39;t collide with each other. Common examples for needing concurrency control are deployments, app releases and infrastructure tasks."
---

# Controlling concurrency

Some tasks need to be run with very strict concurrency rules to ensure they don't collide with each other. Common examples for needing concurrency control are deployments, app releases and infrastructure tasks.

To help you control concurrency, Buildkite provides two primitives: concurrency limits and concurrency groups. While these two primitives are closely linked and interdependent, they operate at different levels.

## [Concurrency limits](#concurrency-limits)

Concurrency limits define the number of jobs that are allowed to run at any one time. These limits are set per-step and only apply to jobs that are based on that step.

Setting a concurrency limit of `1` on a step in your pipeline will ensure that no two jobs created from that step will run at the same time, even if there are agents available.

You can add concurrency limits to steps either through Buildkite, or your `pipeline.yml` file by adding `concurrency` attributes with limit values to these steps. When adding a concurrency limit, you'll also need the `concurrency_group` attribute so that steps in other pipelines can use it as well.

[I'm seeing an error about a missing `concurrency_group_id` when I run my pipeline upload](#im-seeing-an-error-about-a-missing-concurrency-group-id-when-i-run-my-pipeline-upload)

This error is caused by a missing `concurrency_group` attribute. Add this attribute to the same step where you defined the `concurrency` attribute.

## [Concurrency groups](#concurrency-groups)

Concurrency groups are labels that group together Buildkite jobs when applying concurrency limits. When you add a group label to a step the label becomes available to all Pipelines in that organization. These group labels are checked at job runtime to determine which jobs are allowed to run in parallel. Although concurrency groups are created on individual steps, they represent concurrent access to shared resources and can be used by other pipelines.

A concurrency group works like a queue; it returns jobs in the order they entered the queue (oldest to newest). The concurrency group only cares about jobs in "active" states, and the group becomes "locked" when the concurrency limit for jobs in these states is reached. Once a job moves from an active state to a terminal state (`finished` or `canceled`), the job is removed from the queue, opening up a spot for another job to enter. If a job's state is `limited`, it is waiting for another job ahead of it in the same concurrency group to finish.

The full list of "active" [job states](https://buildkite.com/docs/pipelines/configure/defining-steps#job-states) is `limiting`, `limited`, `scheduled`, `waiting`, `assigned`, `accepted`, `running`, `canceling`, `timing out`.

The following is an example [command step](https://buildkite.com/docs/pipelines/configure/step-types/command-step) that ensures deployments run one at a time. If multiple builds are created with this step, each deployment job will be queued up and run one after the other in the order they were created.

Make sure your `concurrency_group` names are unique, unless they're accessing a shared resource like a deployment target.

For example, if you have two pipelines that each deploy to a different target but you give them both the `concurrency_group` label `deploy`, they will be part of the same concurrency group and will not be able to run at the same time, even though they're accessing separate deployment targets. Unique concurrency group names such as `our-payment-gateway/deployment`, `terraform/update-state`, or `my-mobile-app/app-store-release`, will ensure that each one is part of its own concurrency group.

Concurrency groups guarantee that jobs will be run in the order that they were created in. Jobs inherit the creation time of their parent. Parents of jobs can be either a build or a pipeline upload job. As pipeline uploads add more jobs to the build after it has started, the jobs that they add will inherit the creation time of the pipeline upload rather than the build.

[Troubleshooting and using `concurrency_group` with `block` / `input` steps](#troubleshooting-and-using-concurrency-group-with-block-slash-input-steps)

When a build is blocked by a concurrency group, you can check which jobs are in the queue and their state using the [`getConcurrency` GraphQL query](https://buildkite.com/docs/apis/graphql/cookbooks/jobs#get-all-jobs-in-a-particular-concurrency-group).

Be aware that both the [`block`](https://buildkite.com/docs/pipelines/configure/step-types/block-step) and [`input`](https://buildkite.com/docs/pipelines/configure/step-types/input-step) steps cause these steps to be uploaded and scheduled at the same time, which breaks concurrency groups. These two steps prevent jobs being added to the concurrency group, although these steps do not affect the jobs' ordering once they are allowed to continue. The concurrency group won't be added to the queue until the `block` or `input` step is allowed to continue, and once this happens, the timestamp will be from the pipeline upload step.

## [Concurrency and parallelism](#concurrency-and-parallelism)

Sometimes you need strict concurrency while also having jobs that would benefit from parallelism. In these situations, you can use _concurrency gates_ to control which jobs run in parallel and which jobs run one at a time. Concurrency gates come in pairs, so when you open a gate, you have to close it.

Since [`block`](https://buildkite.com/docs/pipelines/block-step) and [`input`](https://buildkite.com/docs/pipelines/input-step) steps [prevent jobs being added to concurrency groups](#troubleshooting-and-using-concurrency-group-with-block-slash-input-steps), you cannot use these two steps inside concurrency gates.

In the following setup, only one build at a time can _enter the concurrency gate_, but within that gate up to three e2e tests can run in parallel, subject to Agent availability. Putting the `stage-deploy` section in the gate as well ensures that every time there is a deployment made to the staging environment, the e2e tests are carried out on that deployment:

### [Controlling command order](#concurrency-and-parallelism-controlling-command-order)

By default, steps that belong to the same concurrency group are run in the order that they are added to the pipeline.

For example, if you have two steps:

- Step `A` in concurrency group `X` with a concurrency of `1` at time 0
- Step `B` with the same concurrency group `X` and also a concurrency of `1` at time 1

Step A will always run before step B. This is the default behavior (`ordered`), and most helpful for deployments.

However, in some cases concurrency groups are used to restrict access to a limited resource, such as a SaaS service like Sauce Labs. In that case, the default ordering of the jobs can work against you, as one step waits for the next before taking up another concurrency slot.

If your resource usage time is very different, for example if tests in pipeline A take 1 minute to run and tests in pipeline B take 10 minutes to run, the default ordering is not helpful because it means that the limited resource you're controlling concurrency for is not fully utilized.

In that case, setting the concurrency method to `eager`, removes the ordering condition for that resource.

### [Concurrency and prioritization](#concurrency-and-parallelism-concurrency-and-prioritization)

If you're using `eager` concurrency and [job prioritization](https://buildkite.com/docs/pipelines/configure/workflows/managing-priorities), higher priority jobs will always take precedence when a concurrency slot becomes available.