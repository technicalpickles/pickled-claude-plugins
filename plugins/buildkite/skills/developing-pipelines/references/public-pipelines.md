---
title: "Public pipelines | Buildkite Documentation"
meta:
  "og:description": "If you&#39;re working on an open-source project, and want the whole world to be able to see your builds, you can make your pipeline public."
  "og:title": "Public pipelines"
  description: "If you&#39;re working on an open-source project, and want the whole world to be able to see your builds, you can make your pipeline public."
---

# Public pipelines

If you're working on an open-source project, and want the whole world to be able to see your builds, you can make your pipeline public.

Making a pipeline public provides read-only public/anonymous access to:

- Pipeline build pages
- Pipeline build logs
- Pipeline build artifacts
- Pipeline build environment config
- Agent version and name

## [Make a pipeline public using the UI](#make-a-pipeline-public-using-the-ui)

Make a pipeline public in the pipeline's **Settings** > **General** page:

![Public pipeline settings](https://buildkite.com/docs/assets/settings-49e05976.png)

## [Create a public pipeline using the GraphQL API](#create-a-public-pipeline-using-the-graphql-api)

Use the following mutation in the [GraphQL API](https://buildkite.com/docs/apis/graphql-api) to create a new public pipeline:

```
mutation {
  pipelineCreate(input: {
    organizationId: $organizationID,
    name: $pipelineName,
    visibility: PUBLIC,
    repository: {
      url: "git@github.com:blerp/goober.git"
    },
    steps: {
      yaml: "steps:\n- command: true"
    }
  }) {
    pipeline {
      public  # true
      visibility # PUBLIC
      organization {
        public # true
      }
    }
  }
}
```