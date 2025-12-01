---
title: "Dynamic pipelines | Buildkite Documentation"
meta:
  "og:description": "When your source code projects are built with Buildkite Pipelines, you can write scripts in the same language as your source code, or another suitable language, that generate new Buildkite pipeline steps (in either YAML or JSON format), which you can then upload to the same pipeline using the pipeline upload step. These additional dynamically generated pipeline steps are run on the same Buildkite Agent, as part of the same pipeline build, and will appear as their own steps in your pipeline builds. This provides you with the flexibility to structure your pipelines however you require."
  "og:title": "Dynamic pipelines"
  description: "When your source code projects are built with Buildkite Pipelines, you can write scripts in the same language as your source code, or another suitable language, that generate new Buildkite pipeline steps (in either YAML or JSON format), which you can then upload to the same pipeline using the pipeline upload step. These additional dynamically generated pipeline steps are run on the same Buildkite Agent, as part of the same pipeline build, and will appear as their own steps in your pipeline builds. This provides you with the flexibility to structure your pipelines however you require."
---

# Dynamic pipelines

When your source code projects are built with Buildkite Pipelines, you can write scripts in the same language as your source code, or another suitable language, that generate new Buildkite pipeline steps (in either YAML or JSON format), which you can then upload to the same pipeline using the [pipeline upload step](https://buildkite.com/docs/pipelines/configure/defining-steps#step-defaults-pipeline-dot-yml-file). These additional _dynamically generated_ pipeline steps are run on the same Buildkite Agent, as part of the same pipeline build, and will appear as their own steps in your pipeline builds. This provides you with the flexibility to structure your pipelines however you require.

For example, the following code snippet is an executable shell script that generates a list of parallel test steps based upon the `test/*` directory within your repository:

To use this script, save it to the `.buildkite/` directory inside your repository (that is, `.buildkite/pipeline.sh`), ensure the script file is executable, and then update your pipeline upload step to use the new script:

```
.buildkite/pipeline.sh | buildkite-agent pipeline upload
```

When the pipeline's build commences, this step executes the script and pipes the output to the `buildkite-agent pipeline upload` command. The upload command then inserts the steps from the script into the build immediately after this upload step.

[Step ordering in the Buildkite interface](#step-ordering-in-the-buildkite-interface)

If you run the pipeline upload step multiple times in a _single command step_ (for example, by running a script file from a command step, in which the script runs the pipeline upload step multiple times), then each batch of uploaded steps will appear in reverse order in the Buildkite interface, such as the **Pipeline** view (in the sidebar) or **Table** view of the [new build page](https://buildkite.com/docs/pipelines/build-page), as well as the **Jobs** view of the classic build page, since the upload command inserts its steps immediately after the upload step.

To avoid each of your dynamically-generated pipeline upload steps appearing in reverse order, define each of these upload steps in reverse order—that is, the steps being run as part of an upload step that you want to run first should be defined last. Alternatively, you can define explicit dependencies using the `depends_on` field.

In the following `pipeline.yml` example, when the build runs, it will execute the `.buildkite/pipeline.sh` script, then the test steps from the script will be added to the build _before_ the wait step and command step. After the test steps have run, the wait and command step will run.

## [Dynamic pipeline templates](#dynamic-pipeline-templates)

If you need the ability to use pipelines from a central catalog, or enforce certain configuration rules, you can either use dynamic pipelines and the [`pipeline upload`](https://buildkite.com/docs/agent/v3/cli-pipeline#uploading-pipelines) command to make this happen or [write custom plugins](https://buildkite.com/docs/pipelines/integrations/plugins) and share them across your organization.

To use dynamic pipelines and the pipeline upload command, you'd make a pipeline that looks something like this:

```
steps:
  - command: enforce-rules.sh | buildkite-agent pipeline upload
    label: ":pipeline: Upload"
```

Each team defines their steps in `team-steps.yml`. Your templating logic is in `enforce-rules.sh`, which can be written in any language that can pass YAML to the pipeline upload.

In `enforce-rules.sh` you can add steps to the YAML, require certain versions of dependencies or plugins, or implement any other logic you can program. Depending on your use case, you might want to get `enforce-rules.sh` from an external catalog instead of committing it to the team repository.

See how [Hasura.io](https://hasura.io) used [dynamic templates and pipelines](https://hasura.io/blog/what-we-learnt-by-migrating-from-circleci-to-buildkite/#dynamic-pipelines) to replace their YAML configuration with Go and some shell scripts.

## [Buildkite SDK](#buildkite-sdk)

Learn more about about the Buildkite SDK, which makes it easy to script the generation of steps for dynamic pipelines, on the [Buildkite SDK](https://buildkite.com/docs/pipelines/configure/dynamic-pipelines/sdk) page.