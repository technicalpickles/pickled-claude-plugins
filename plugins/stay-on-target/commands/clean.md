---
name: clean
description: Remove temporary test fixtures
---

# Clean

Remove temporary test fixtures created by the self-test command.

## What Gets Removed

- `tmp/bktide` - Cloned test fixture from bktide repository
- `tmp/bktide-no-claude-md` - Test fixture without CLAUDE.md

## Process

1. **Check for tmp directory** at `${PLUGIN_ROOT}/tmp/`
2. **List contents** to show what will be removed
3. **Remove** the entire tmp directory
4. **Confirm** removal

## Example Output

```
Cleaning stay-on-target test fixtures...

Found:
- tmp/bktide (42 MB)
- tmp/bktide-no-claude-md (41 MB)

Removed 83 MB of test fixtures.
```

## Notes

- The tmp directory is gitignored, so these are local-only files
- Re-running self-test will recreate the fixtures as needed
- Safe to run multiple times (no error if tmp doesn't exist)
