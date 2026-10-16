# second-brain evals

End-to-end eval cases for second-brain skills, run with Claude Code's built-in
`claude plugin eval`. Each case runs a real `claude` session against a
scaffolded fake vault, then grades the note it wrote.

## Where to run them

Not on the Mac: `claude plugin eval` refuses to grant Bash when `~/.ssh` holds
symlinks, and dotfiles symlinks `~/.ssh/config.d/*`. Run them in the
`capture-evals` OrbStack VM (Ubuntu, with node 22, Claude Code, lightpanda,
bubblewrap and socat installed, logged in to claude.ai). The VM sees the Mac's
home directory, so it runs straight from this checkout:

```bash
orb -m capture-evals bash plugins/second-brain/evals/_shared/run-in-vm.sh <case>
orb -m capture-evals env RUNS=3 JOBS=3 bash plugins/second-brain/evals/_shared/run-in-vm.sh <case>
```

`RUNS`/`JOBS` set on the Mac side don't cross into the VM (you silently get 1 run); pass them with `env` as above.

Results land in `/tmp/<case>.json` inside the VM (`orb -m capture-evals cat` it
back) and as an HTML report under `evals/results/` (git-ignored).

## How the harness works (learned 2026-10-16)

- **Scaffold.** `case.yaml`'s `scaffold_script` must sit inside the case dir, so
  each case has a two-line `scaffold.sh` that sources `_shared/scaffold-vault.sh`.
  It runs with the run's own HOME and cwd, and with network.
- **sb.** The agent's sandbox blocks the npm registry, and `npx -y` re-checks it
  even with a warm cache, so the scaffold `npm install`s sb into the run cwd.
- **Fixed path to the new note.** File graders take fixed paths relative to the
  run cwd; globs don't work. The scaffold wraps `node_modules/.bin/sb` so each
  `note create` symlinks `.eval/latest-note.md` to the note it made.
- **Regex graders are JavaScript.** No inline `(?m)`; use a `flags: m` field.
  On `target: trace` (stream-json lines), match within one tool input with
  `[^}]*`, not `[^"]*` - JSON-escaped quotes end a `[^"]` run early.
- **Plugin hooks fire** (the devlog SessionStart hook shows in the trace).
- **qmd isn't available** in the run; the skill falls back to Grep.
- **Fixtures.** `WITH_SAME_SUBJECT_NOTE=1` adds a note on the same subject as
  the source. Leave it off unless the case tests that path: it trips capture's
  strong-match stop and the run ends before writing anything.
- **Cost.** About $0.25 per capture run (12-13 turns, Opus).

## Cases

Baselines ran against the 1.17.0 skill text; "After" is the text on this branch.
A run that skips `references/note-format.md` (1 in 9 before Step 3 inlined the
note skeleton) copies a neighbor note's shape and invents a use-case section -
the skeleton in SKILL.md Step 3 is there so a skipped reference can't do that.

| Case | Pins | Baseline (1.17.0 text, 3 runs) | After |
|------|------|------|------|
| `harness-smoke` | sb resolves the scaffold vault; file graders work | pass | - |
| `capture-frontmatter` | seedling/created/real source; no sb placeholders; no copied legacy shape; no `--dry-run`; breadcrumb under `## Links` | frontmatter 3/3 correct; `--dry-run` 3/3; breadcrumb to `Notes` 3/3 | 3/3 pass |
| `capture-note-shape` | outbound links kept; 3+ parallel items as bullets; `**Why I saved this:**` line; no facts beyond the source (LLM judge) | bullets 0/3, why-line 0/3, invented use-case speculation 2/3 (links 3/3) | 3/3 pass |
| `capture-no-other-note-edits` | same-subject note is never edited (no reciprocal link); closing block of `[high|medium|low]` proposals in plain words | closing-proposals 0/3 (weak-link question, no labels); roc note untouched 3/3 already | 3/3 pass |
