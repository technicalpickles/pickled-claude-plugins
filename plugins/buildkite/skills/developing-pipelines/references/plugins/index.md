# Buildkite Plugins Reference

## Lookup Workflow

When working with plugins in pipelines:

1. **Check cached docs** - `@references/plugins/{plugin-name}.md`
2. **Fetch if not cached:**
   - Buildkite directory: `https://buildkite.com/resources/plugins/{org}/{plugin-name}-buildkite-plugin`
   - GitHub README: `https://github.com/{org}/{plugin-name}-buildkite-plugin`
3. **For specific versions:** `https://github.com/{org}/{plugin-name}-buildkite-plugin/tree/{version}`

## Parsing Plugin References

From pipeline YAML:
```yaml
plugins:
  - docker-compose#v5.12.1:  # org defaults to buildkite-plugins
      run: app
  - seek-oss/docker-ecr-cache#v2.2.0:  # explicit org
      ...
```

Extract: `{org}/{plugin-name}#{version}`

## Common Plugins by Category

### Containers
| Plugin | Org | Cached | Purpose |
|--------|-----|--------|---------|
| docker | buildkite-plugins | ✓ | Run steps in Docker containers |
| docker-compose | buildkite-plugins | ✓ | Multi-container environments |
| ecr | buildkite-plugins | ✓ | AWS ECR authentication |

### Build Artifacts
| Plugin | Org | Cached | Purpose |
|--------|-----|--------|---------|
| artifacts | buildkite-plugins | ✓ | Upload/download artifacts |

### Caching
| Plugin | Org | Cached | Purpose |
|--------|-----|--------|---------|
| cache | buildkite-plugins | ✓ | Dependency caching |
| docker-ecr-cache | seek-oss | - | Docker layer caching with ECR |
| s3-cache | danthorpe | - | S3-based caching |

### Authentication
| Plugin | Org | Cached | Purpose |
|--------|-----|--------|---------|
| ecr | buildkite-plugins | ✓ | AWS ECR login |
| docker-login | buildkite-plugins | - | Docker Hub login |
| vault-secrets | buildkite-plugins | - | HashiCorp Vault secrets |

## Discovering Internal Plugins

For organization-specific plugins:

1. Search GitHub org for repos matching `*-buildkite-plugin`
2. Check repo README for configuration docs

## Plugin Directory

Full catalog: https://buildkite.com/resources/plugins/
