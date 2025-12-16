# Buildkite Plugin Knowledge Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extend developing-buildkite-pipelines skill with accurate, version-aware plugin configuration reference.

**Architecture:** Add plugin reference docs directory with cached docs for common plugins plus index for discovery. Update SKILL.md workflow to load plugin docs before modifying plugin configuration.

**Tech Stack:** Markdown reference docs, WebFetch for plugin documentation

---

## Task 1: Create Plugin Index Reference

**Files:**
- Create: `plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/plugins/index.md`

**Step 1: Create the plugins directory**

```bash
mkdir -p plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/plugins
```

**Step 2: Write the index file**

Create `references/plugins/index.md` with this content:

```markdown
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
| cache | gantry | ✓ | Dependency caching |
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
```

**Step 3: Verify file created**

```bash
cat plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/plugins/index.md | head -20
```

**Step 4: Commit**

```bash
git add plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/plugins/index.md
git commit -m "feat(ci-cd-tools): add plugin index reference"
```

---

## Task 2: Cache Docker Plugin Docs

**Files:**
- Create: `plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/plugins/docker.md`

**Step 1: Fetch current Docker plugin documentation**

Fetch from: `https://buildkite.com/resources/plugins/buildkite-plugins/docker-buildkite-plugin`

Also check GitHub for complete options: `https://github.com/buildkite-plugins/docker-buildkite-plugin`

**Step 2: Create the reference doc**

Write `references/plugins/docker.md` including:
- Header with GitHub URL and version documented
- Overview (what the plugin does)
- All configuration options with types and descriptions
- 2-3 common usage examples
- Link to version-specific docs

**Step 3: Commit**

```bash
git add plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/plugins/docker.md
git commit -m "feat(ci-cd-tools): add docker plugin reference"
```

---

## Task 3: Cache Docker Compose Plugin Docs

**Files:**
- Create: `plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/plugins/docker-compose.md`

**Step 1: Fetch current documentation**

Fetch from: `https://buildkite.com/resources/plugins/buildkite-plugins/docker-compose-buildkite-plugin`

**Step 2: Create the reference doc**

Write `references/plugins/docker-compose.md` with same structure as docker.md.

**Step 3: Commit**

```bash
git add plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/plugins/docker-compose.md
git commit -m "feat(ci-cd-tools): add docker-compose plugin reference"
```

---

## Task 4: Cache Artifacts Plugin Docs

**Files:**
- Create: `plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/plugins/artifacts.md`

**Step 1: Fetch current documentation**

Fetch from: `https://buildkite.com/resources/plugins/buildkite-plugins/artifacts-buildkite-plugin`

**Step 2: Create the reference doc**

Write `references/plugins/artifacts.md` with same structure.

**Step 3: Commit**

```bash
git add plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/plugins/artifacts.md
git commit -m "feat(ci-cd-tools): add artifacts plugin reference"
```

---

## Task 5: Cache ECR Plugin Docs

**Files:**
- Create: `plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/plugins/ecr.md`

**Step 1: Fetch current documentation**

Fetch from: `https://buildkite.com/resources/plugins/buildkite-plugins/ecr-buildkite-plugin`

**Step 2: Create the reference doc**

Write `references/plugins/ecr.md` with same structure.

**Step 3: Commit**

```bash
git add plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/plugins/ecr.md
git commit -m "feat(ci-cd-tools): add ecr plugin reference"
```

---

## Task 6: Cache Gantry Cache Plugin Docs

**Files:**
- Create: `plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/plugins/cache.md`

**Step 1: Fetch current documentation**

Fetch from: `https://buildkite.com/resources/plugins/gantry/cache-buildkite-plugin`

Also GitHub: `https://github.com/gantry/cache-buildkite-plugin`

**Step 2: Create the reference doc**

Write `references/plugins/cache.md` with same structure.

**Step 3: Commit**

```bash
git add plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/plugins/cache.md
git commit -m "feat(ci-cd-tools): add cache plugin reference"
```

---

## Task 7: Update SKILL.md with Plugin Workflow

**Files:**
- Modify: `plugins/ci-cd-tools/skills/developing-buildkite-pipelines/SKILL.md`

**Step 1: Add "Working with Plugins" section after "Detecting buildkite-builder"**

Insert after line 42 (after the buildkite-builder detection section):

```markdown
## Working with Plugins

### Before Modifying Plugin Configuration

When editing pipeline steps that use plugins:

1. **Identify plugins** - Note all `plugins:` entries in the step
2. **Determine source:**
   - Default org `buildkite-plugins` if no org specified
   - Parse explicit org from `{org}/{plugin}#version` format
3. **Load documentation:**
   - **Cached:** Check `@references/plugins/{plugin-name}.md`
   - **Official (not cached):** Fetch from Buildkite directory or GitHub
   - **Internal:** Fetch README from `github.com/{org}/{plugin}-buildkite-plugin`
4. **Match versions** - If pipeline specifies version, fetch that version's docs from GitHub tag

### Fetching Plugin Documentation

**Buildkite directory (latest):**
```
https://buildkite.com/resources/plugins/{org}/{plugin-name}-buildkite-plugin
```

**GitHub README (version-specific):**
```
https://github.com/{org}/{plugin-name}-buildkite-plugin/tree/{version}
```

### Plugin Discovery

**"Is there a plugin for X?"**

1. Check `@references/plugins/index.md` for common plugins by category
2. Fetch Buildkite directory: `https://buildkite.com/resources/plugins/`
3. Search by task type (caching, docker, secrets, etc.)

**Internal plugins:**

Search org's GitHub for repos matching `*-buildkite-plugin`
```

**Step 2: Update the Workflow section**

Modify "### 2. Read Official Docs FIRST" to add plugin checkpoint.

After the existing references list (around line 84), add:

```markdown
**Plugin references (see @references/plugins/index.md for full list):**
- `plugins/docker.md` - Docker container execution
- `plugins/docker-compose.md` - Multi-container environments
- `plugins/artifacts.md` - Artifact upload/download
- `plugins/ecr.md` - AWS ECR authentication
- `plugins/cache.md` - Dependency caching
```

**Step 3: Replace "### 4. Check for Official Plugins" section**

Replace the current section (lines 135-146) with:

```markdown
### 4. Load Plugin Documentation

Before modifying any step with plugins:

1. **Identify all plugins** in the step's `plugins:` block
2. **For each plugin:**
   - Check `@references/plugins/{name}.md` for cached docs
   - If not cached, fetch from Buildkite directory or GitHub
   - If version specified, fetch version-specific docs
3. **Then proceed** with changes using accurate configuration reference

See `@references/plugins/index.md` for lookup workflow and common plugins.
```

**Step 4: Update "When to Use" section**

Add to the list (around line 20):
```markdown
- Configuring or debugging Buildkite plugins
```

**Step 5: Verify changes**

```bash
grep -n "Working with Plugins" plugins/ci-cd-tools/skills/developing-buildkite-pipelines/SKILL.md
grep -n "Load Plugin Documentation" plugins/ci-cd-tools/skills/developing-buildkite-pipelines/SKILL.md
```

**Step 6: Validate plugin**

```bash
claude plugin validate plugins/ci-cd-tools
```

**Step 7: Commit**

```bash
git add plugins/ci-cd-tools/skills/developing-buildkite-pipelines/SKILL.md
git commit -m "feat(ci-cd-tools): add plugin workflow to developing-buildkite-pipelines skill"
```

---

## Task 8: Final Validation

**Step 1: Verify all files exist**

```bash
ls -la plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/plugins/
```

Expected: index.md, docker.md, docker-compose.md, artifacts.md, ecr.md, cache.md

**Step 2: Validate plugin structure**

```bash
claude plugin validate plugins/ci-cd-tools
```

Expected: "Validation passed"

**Step 3: Review git log**

```bash
git log --oneline -10
```

Expected: 7 commits for this feature
