---
title: "Build matrix | Buildkite Documentation"
meta:
  "og:description": "Build matrices help you simplify complex build configurations by expanding a step template and array of matrix elements into multiple jobs."
  "og:title": "Build matrix"
  description: "Build matrices help you simplify complex build configurations by expanding a step template and array of matrix elements into multiple jobs."
---

# Build matrix

Build matrices help you simplify complex build configurations by expanding a step template and array of matrix elements into multiple jobs.

The following [command step](https://buildkite.com/docs/pipelines/configure/step-types/command-step) attributes can contain matrix values for interpolation:

- [environment variables](https://buildkite.com/docs/pipelines/configure/environment-variables)
- [labels](https://buildkite.com/docs/pipelines/configure/step-types/command-step#label)
- [commands](https://buildkite.com/docs/pipelines/configure/step-types/command-step#command-step-attributes)
- [plugins](https://buildkite.com/docs/pipelines/configure/step-types/command-step#plugins)
- [agents](https://buildkite.com/docs/pipelines/configure/step-types/command-step#agents)

You can't use matrix values in other attributes, including step keys and [concurrency groups](https://buildkite.com/docs/pipelines/configure/workflows/controlling-concurrency#concurrency-groups).

For example, instead of writing three separate jobs for builds on macOS, Linux, and Windows, like the following build configuration (which does not use a build matrix):

Use a build matrix to expand a single step template into three steps by interpolating the matrix values into the following build configuration:

All jobs created by a build matrix are marked with the **Matrix** badge in the Buildkite interface.

[Matrix and Parallel steps](#matrix-and-parallel-steps)

Matrix builds are not compatible with explicit [parallelism in steps](https://buildkite.com/docs/pipelines/tutorials/parallel-builds#parallel-jobs). You can use a `matrix` and `parallelism` in the same build, as long as they are on separate steps.

For more complex builds, add multiple dimensions to `matrix.setup` instead of the `matrix` array:

Each dimension you add is multiplied by the other dimensions, so two architectures (`matrix.setup.arch`), two operating systems (`matrix.setup.os`), and two tests (`matrix.setup.test`) create an eight job build (`2 * 2 * 2 = 8`):

![Screenshot of an eight job matrix](https://buildkite.com/docs/assets/matrix_build-ddbb4c0e.jpg)

If you're using `matrix.setup`, you can also use the `adjustments` key to change specific entries in the build matrix, or add new combinations. You can set the `skip` attribute to exclude them from the matrix, or `soft_fail` attributes to allow them to fail without breaking the build.

## [Adding combinations to the build matrix](#adding-combinations-to-the-build-matrix)

To add an extra combination that isn't present in the `matrix.setup`, use the `adjustments` key and make sure to define all of the elements in the matrix. For example, to add a build for [Plan 9](https://en.wikipedia.org/wiki/Plan_9_from_Bell_Labs) (on `arm64`, and test suite `B`) to the previous example, use:

This results in nine jobs, (`2 * 2 * 2 + 1 = 9`).

## [Excluding combinations from the build matrix](#excluding-combinations-from-the-build-matrix)

To exclude a combination from the matrix, add it to the `adjustments` key and set `skip: true`:

## [Matrix limits](#matrix-limits)

Each build matrix has a limit of 6 dimensions, 20 elements in each dimension, and a total of 12 adjustments. The `matrix` configuration on a `command` has a limit of 50 jobs created.

## [Grouping matrix elements](#grouping-matrix-elements)

If you're using the [new build page experience](https://buildkite.com/docs/pipelines/build-page), matrix jobs are automatically grouped under the matrix step you define in your pipeline. This makes them easier to use and work with. However, if you're using the classic build page with many matrix jobs, then you may want to consider [grouping](https://buildkite.com/docs/pipelines/configure/step-types/group-step) them together manually with a group step, for a tidier view.

![Screenshot of an eight job matrix inside a group step](https://buildkite.com/docs/assets/grouped-03e11276.jpg)

To do that, indent the matrix steps inside a [group step](https://buildkite.com/docs/pipelines/configure/step-types/group-step):

```
steps:
  - group: "📦 Build"
    steps:
      - label: "💥 Matrix build with adjustments"
        command: "echo {{matrix.os}} {{matrix.arch}} {{matrix.test}}"
        matrix:
          setup:
            arch:
              - "amd64"
              - "arm64"
            os:
              - "windows"
              - "linux"
            test:
              - "A"
              - "B"
```