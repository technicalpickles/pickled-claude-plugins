# Developing Buildkite Pipelines Skill

This skill ensures Claude references official Buildkite documentation when creating, modifying, or debugging pipeline configurations.

## Purpose

Prevents agents from:
- Writing pipeline YAML from memory/training data
- Using outdated or deprecated syntax
- Speculating about configuration errors
- Creating complex implementations without consulting best practices

## Structure

```
developing-buildkite-pipelines/
├── SKILL.md                 # Main skill document
├── README.md                # This file
├── update-docs.sh           # Script to refresh documentation
└── references/              # Official Buildkite docs (markdown)
    ├── index.md             # Navigation guide
    ├── step-types.md        # Step configuration reference
    ├── dynamic-pipelines.md # Dynamic pipeline patterns
    ├── dependencies.md      # Step dependencies
    ├── environment-variables.md
    ├── conditionals.md
    ├── artifacts.md
    └── ... (20+ additional reference files)
```

## Updating Documentation

The `references/` directory contains markdown versions of official Buildkite documentation. To refresh:

```bash
cd plugins/ci-cd-tools/skills/developing-buildkite-pipelines
./update-docs.sh
```

This fetches the latest docs from `buildkite.com/docs/pipelines/configure/**` using `@mdream/crawl`.

**When to update:**
- Buildkite releases new features
- Syntax changes or deprecations
- Every 3-6 months for general maintenance

## Testing Results

### Baseline (WITHOUT skill):
- Agent wrote 2,600+ line dynamic pipeline from memory
- No validation strategy mentioned
- Speculated about error causes
- Used patterns from training data

### With skill:
- ✅ Referenced official documentation explicitly
- ✅ Mentioned `--dry-run` validation
- ✅ Used current Buildkite patterns
- ✅ Cited specific doc files

See `.scratch/buildkite-*-results.md` for detailed testing documentation.

## Key Behaviors Enforced

1. **Read docs FIRST** - Before proposing YAML, check references
2. **Validate** - Always mention `buildkite-agent pipeline upload --dry-run`
3. **Check plugins** - Before custom scripts, check buildkite.com/plugins
4. **Don't speculate** - Look up actual validation rules

## Dependencies

For updating docs:
- Node.js (for `npx`)
- `@mdream/crawl` package (installed automatically by npx)

## References

- [Buildkite Pipeline Documentation](https://buildkite.com/docs/pipelines/configure)
- [Writing Skills Guide](../../superpowers/skills/writing-skills/SKILL.md)
