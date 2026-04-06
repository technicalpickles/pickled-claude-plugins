---
title: "Build retention | Buildkite Documentation"
meta:
  "og:description": "Each Buildkite plan has a maximum build retention period. Once builds reach the retention period, their data is removed from Buildkite."
  "og:title": "Build retention"
  description: "Each Buildkite plan has a maximum build retention period. Once builds reach the retention period, their data is removed from Buildkite."
---

# Build retention

Each [Buildkite plan](https://buildkite.com/pricing) has a maximum build retention period. Once builds reach the retention period, their data is removed from Buildkite.

The following diagram shows the lifecycle of build data by plan.

![Simplified flow chart of the build retention process](https://buildkite.com/docs/assets/build-retention-flow-chart-48aa402c.png)

## [Retention periods](#retention-periods)

| Plan | Retention period | Supports build exports |
| --- | --- | --- |
| Personal plan | 90 days | No |
| Pro plan | 1 year | No |
| Enterprise plan | 1 year | Yes |

Retention periods are set according to an organization's plan, as shown in the previous table. Per-pipeline retention settings are not supported.

## [Exporting build data](#exporting-build-data)

[Enterprise plan feature](#enterprise-plan-feature)

Exporting build data is only available on an [Enterprise](https://buildkite.com/pricing) plan.

If you need to retain build data beyond the retention period in your [Buildkite plan](https://buildkite.com/pricing), you can have Buildkite export the data to a private Amazon S3 bucket or Google Cloud Storage (GCS) bucket. As build data is removed, Buildkite exports JSON representations of the builds to the bucket you provide. To learn more, see [Build exports](https://buildkite.com/docs/pipelines/governance/build-exports).