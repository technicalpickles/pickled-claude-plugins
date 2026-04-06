# ECR Buildkite Plugin

**Source:** https://github.com/buildkite-plugins/ecr-buildkite-plugin
**Version documented:** v2.11.0

## Overview

Authenticates to Amazon ECR repositories before executing build steps. Leverages AWS credentials from environment variables, instance roles, or task roles to facilitate Docker login operations.

## Configuration Options

### Common Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `login` | boolean | true | Enable/disable ECR authentication |
| `account-ids` | string/array | current account | AWS account IDs for target ECR registries |
| `region` | string | `AWS_DEFAULT_REGION` or `us-east-1` | AWS region for ECR operations |
| `retries` | integer | 0 | Number of retry attempts on login failure |
| `profile` | string | - | AWS profile for authentication |

### Credential Helper Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `credential-helper` | boolean | false | Use Amazon ECR credential helper instead of AWS CLI |
| `credential-helper-ignore-creds-storage` | boolean | true | Suppress credential storage errors |

### Role Assumption

| Option | Type | Description |
|--------|------|-------------|
| `assume-role` | object | IAM role to assume before authentication |
| `assume-role.role-arn` | string | ARN of role to assume (required) |
| `assume-role.duration-seconds` | integer | Session duration |

## Examples

**Basic usage (current account):**
```yaml
steps:
  - command: "./run_build.sh"
    plugins:
      - ecr#v2.11.0: ~
```

**Cross-account login:**
```yaml
steps:
  - command: "./run_build.sh"
    plugins:
      - ecr#v2.11.0:
          account-ids: "123456789012"
          region: "us-west-2"
```

**Multiple accounts including public ECR:**
```yaml
steps:
  - command: "./run_build.sh"
    plugins:
      - ecr#v2.11.0:
          account-ids:
            - "123456789012"
            - "987654321098"
            - "public.ecr.aws"
```

**With role assumption:**
```yaml
steps:
  - command: "./run_build.sh"
    plugins:
      - ecr#v2.11.0:
          account-ids: "123456789012"
          assume-role:
            role-arn: "arn:aws:iam::123456789012:role/ecr-access"
```

**Using credential helper:**
```yaml
steps:
  - command: "./run_build.sh"
    plugins:
      - ecr#v2.11.0:
          credential-helper: true
```

## Version-Specific Docs

For specific versions: https://github.com/buildkite-plugins/ecr-buildkite-plugin/tree/{version}
