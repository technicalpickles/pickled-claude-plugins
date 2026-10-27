# Probe contract

The pure core (`model`, `rules`, `templates`, `files`, `judge`) trusts the `Surface` it is handed. It never reads the filesystem, so its verdicts hold only if the v0.1 probe builds that `Surface` like this.

## Config entries

- **Encode a valueless key as `"true"`.** `[core] bare` with no `=` is true to git. Encoding it as `"true"` means `""` always stands for an explicit empty value, which git reads as false (so the WEAKEN rows treat it as false).
- **List every member that owns entries in `Surface.members`.** `include_path`, `worktree_path` and `restore_ops` only trust paths inside a listed member's git dir, and the remote views are built per member.
- **Document which member and scope include-target entries carry.** The remote views and the module `core.hooksPath` resolution key on the member. The core's tests assume the member whose config did the including.
  - Open question: a `remote.<r>.url` reached only through `includeIf` should not count toward the remotes a `branch.*.remote` may name, because the condition may not hold for every reader. This still needs a ruling.

## Paths

- **Hand over a realpath'd `Anchor.path`.** Finding ids, LKG link atoms and gitfile targets are all keyed by it, so two spellings of one repo would be two anchors.
- **Compute `tracked_dirs` from realpath'd targets.** `hooks_path` compares normalized paths, so a symlinked tracked dir would otherwise fail to match, or an untracked symlink target would match.

## File atoms

- **Check the symlinks and contents of each `worktrees/<name>` admin dir.** The core sees only the atoms it is given, and a symlinked admin dir redirects every file under it.
- **Emit no `absent` commondir atom for a plain repo.** An absent commondir passes only by LKG, so a plain repo would warn on first sight.
- **Set a symlink's `sha256` to the hash of its readlink target.** `lkg_equal` compares it, so retargeting a symlink must change the hash.

## Test coverage

- **The corpus proof covers config only.** `test_corpus.py` runs real-repo config entries. File atoms (hooks and link files) are covered by unit tests in `test_files.py` and `test_judge.py`, with no real-world corpus behind them yet.
