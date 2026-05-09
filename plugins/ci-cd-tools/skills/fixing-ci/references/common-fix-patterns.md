# Common Fix Patterns

Detailed patterns for recurring CI failures. The `fixing-ci` SKILL.md links here for progressive disclosure — load this only when you've classified the failure into one of these categories.

## Gemfile.lock Checksum Issues

**Symptom:** `Your lockfile has an empty CHECKSUMS entry for "<gem>"`

**Fix:**
```bash
rm Gemfile.lock
git checkout origin/main -- Gemfile.lock
bundle lock
bundle install  # verify
git add Gemfile.lock
git commit -m "Regenerate Gemfile.lock with proper checksums"
```

## Merge Conflicts Blocking Push

**Fix:**
```bash
git stash push -m "WIP changes"
git fetch origin main
git merge origin/main --no-edit
# Resolve conflicts
git add <conflicted-files>
git commit
git stash pop
# Resolve any conflicts from stash
```

## Test Matcher/Helper Changes Breaking Tests

**Diagnosis:** Compare with main:
```bash
git diff origin/main -- spec/support/
git diff origin/main -- test/helpers/
```

**Fix:** Often need to restore original behavior for non-target tests while adding new behavior for new tests.

## Year Boundary Test Failures

**Symptom:** Tests involving dates fail around new year

**Fix:** Look for hardcoded years or date assumptions in tests.
