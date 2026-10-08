# come-on: one skill with modes, better auto-firing — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Collapse the `come-on` plugin to a single skill with modes, rewrite its description from the agent's own situation, and prove (against a held-out set, old skill vs new) that it fires more often at the moment Claude is about to stop short.

**Architecture:** Skill-authoring TDD (superpowers:writing-skills) using skill-creator's methods: realistic near-miss trigger queries, an old-skill baseline, and a human pass over outputs in skill-creator's viewer. Measurement stays on `claude plugin eval`, which loads the real plugin. skill-creator's `run_eval.py`/`run_loop.py` aren't used because their synthesized slash command isn't model-visible. Bash-granting runs happen in the colima `plugin-eval` VM.

**Tech Stack:** Claude Code skills (SKILL.md), `claude plugin eval` (claude 2.1.294 in the VM), colima, Python 3 (viewer converter), skill-creator's `eval-viewer/generate_review.py`.

**Spec:** `projects/come-on/design/2026-10-08-come-on-autofire-design.md`

---

## Conventions for every task

- `W` = `/Users/josh.nichols/pickleton/repos/pickled-claude-plugins/bare.git/.claude/worktrees/come-on-plugin` (branch `come-on-plugin`, draft PR https://github.com/technicalpickles/pickled-claude-plugins/pull/146). `P` = `$W/plugins/come-on`.
- **Public repo:** no internal tracker IDs in commits, branch names, files, or the PR body. Commit with the `git:commit` skill.
- **Pickleton root** (`/Users/josh.nichols/pickleton`) stays on `main`. Run `git branch --show-current` right before committing, and always scope commits: `git commit -m "..." -- <paths>`.
- **Scratch:** `projects/come-on/.scratch/` (gitignored, and visible inside the VM through the `/Users/josh.nichols` mount). `S` = `/Users/josh.nichols/pickleton/projects/come-on/.scratch`.
- **Results log:** `projects/come-on/evals-log.md` in pickleton (not the public repo). Every sweep appends a dated section there.
- **VM:** `colima ssh -p plugin-eval -- bash -lc '<cmd>'`. If bwrap fails with `loopback: Failed RTM_NEWADDR`, run `sudo sysctl -w kernel.apparmor_restrict_unprivileged_userns=0` in the VM (Josh does this, since it needs sudo).
- **Holdout discipline:** while tuning the description (Task 7), read and run only `tune-*` cases. Look at `holdout-*` and `scn-*` only when running them in Tasks 4 and 8.
- **Cost:** confirm with Josh before any sweep estimated above $5.

## File structure

| Path | Change | Responsibility |
|---|---|---|
| `$P/skills/come-on/SKILL.md` | rewrite | routing, core loop, one line per angle, under 500 words |
| `$P/skills/come-on/references/angles.md` | modify | full per-angle checklists (moved out of SKILL.md) |
| `$P/skills/come-on-{check,try,rederive,weigh,unpack,simplify}/` | delete | replaced by modes |
| `$P/evals/trigger-*`, `$P/evals/no-trigger-*` | delete | replaced by tune/holdout sets |
| `$P/evals/tune-*` (12) | create | trigger cases that may be iterated against |
| `$P/evals/holdout-*` (8) | create | trigger cases never tuned against |
| `$P/evals/mode-*` (3) | create | `/come-on <mode>` routing |
| `$P/README.md` | modify | modes table, Testing status |
| `pickleton/projects/come-on/tools/results_to_viewer.py` | create | `claude plugin eval` JSON → skill-creator viewer workspace |
| `pickleton/projects/come-on/evals-log.md` | create | per-sweep numbers |

---

### Task 0: Preflight

**Files:** none

- [ ] **Step 1: Confirm PR, branch, and VM state**

```bash
git -C $W branch --show-current        # expect: come-on-plugin
git -C $W status --short               # expect: empty
git -C $W log --oneline -1             # expect: ae629d7 docs(come-on): record eval results (or later)
gh pr view 146 -R technicalpickles/pickled-claude-plugins --json state,isDraft,reviews --jq '{state,isDraft,r:(.reviews|length)}'
colima list                             # plugin-eval Running
colima ssh -p plugin-eval -- sysctl kernel.apparmor_restrict_unprivileged_userns   # expect: = 0
colima ssh -p plugin-eval -- claude --version
```

If there are review comments on #146, handle them first with `git:pull-feedback`.

- [ ] **Step 2: Record the old-skill commit**

```bash
git -C $W rev-parse HEAD > /Users/josh.nichols/pickleton/projects/come-on/.scratch/old-skill-sha
```

This commit is the "old skill" for every baseline run. Tasks 1 to 3 change only `evals/`, so the SHA keeps pointing at the old skill code even after new eval cases land.

---

### Task 1: Write the trigger query set (tune + holdout)

**Files:**
- Create: `$P/evals/tune-trigger-0{1..6}/`, `$P/evals/tune-quiet-0{1..6}/`, `$P/evals/holdout-trigger-0{1..4}/`, `$P/evals/holdout-quiet-0{1..4}/` (each has `prompt.md` and `graders/fired.md` or `graders/quiet.md`)
- Delete: `$P/evals/trigger-*`, `$P/evals/no-trigger-*`

The should-trigger prompts avoid pushback words. Each one puts Claude in a spot where the natural move is to stop short. The quiet prompts are near-misses: they share come-on's vocabulary but don't need it.

- [ ] **Step 1: Write the generator script**

Create `$S/make_trigger_cases.py`:

```python
#!/usr/bin/env python3
"""Write tune/holdout trigger cases for the come-on plugin. Usage: make_trigger_cases.py <evals-dir>"""
import pathlib, sys

FRONT = "---\nruns: 3\nmax_turns: 3\nallowed_tools: [Read, Glob, Grep, Skill]\n---\n\n"
FIRED = """---
type: tool_used
tool: Skill
input_match: '"skill"\\s*:\\s*"(?:[\\w-]+:)?come-on"'
min: 1
---
The come-on skill fires on this prompt.
"""
QUIET = """---
type: tool_used
tool: Skill
input_match: '"skill"\\s*:\\s*"(?:[\\w-]+:)?come-on"'
min: 0
max: 0
---
The come-on skill stays quiet on this prompt.
"""

CASES = {
    # tune: should fire
    "tune-trigger-01": "here's the handoff from yesterday's session: \"root cause is the N+1 in OrdersController#index, fix is to add includes(:line_items)\". go ahead and implement the fix in app/controllers/orders_controller.rb",
    "tune-trigger-02": "the deploy script timed out hitting the artifact bucket (curl: (28) Connection timed out after 30001 milliseconds). just tell me if we're blocked or not, i need to tell my manager in 5",
    "tune-trigger-03": "tests are green on my machine now that you changed parse_date. write up the PR description and mention the CI failure in test_invoice_totals is pre-existing and unrelated",
    "tune-trigger-04": "we need to pick between sidekiq-unique-jobs and rolling our own lock with redis SETNX for the billing dedupe thing. which one",
    "tune-trigger-05": "draft the slack update for #payroll-eng on where INC-4411, PAYR-2291 and the flags migration stand. sarah's reading it and she hasn't been in any of this",
    "tune-trigger-06": "heading into a meeting in 2 min. did the 2.3 release include the tax-table fix or not? you were digging through the changelog earlier",
    # tune: should stay quiet (near-misses)
    "tune-quiet-01": "I just pushed the fix for the lint error. try again: run bin/lint and tell me if it passes",
    "tune-quiet-02": "tl;dr this for me, it's the README I wrote last night:\n\n# rates\nFetches FX rates hourly from the ECB feed and caches them in redis for 2h. Run `bin/rates sync` to force a refresh.",
    "tune-quiet-03": "did you check the 'docs updated' box in the PR template? it's the second checkbox, just tick it",
    "tune-quiet-04": "give me a pros and cons list of tabs vs spaces for a joke lightning talk slide, keep it silly",
    "tune-quiet-05": "come on in, the water's fine! write a 2-line welcome message for our new #team-rates channel",
    "tune-quiet-06": "explain what git rebase does to someone who's only ever used merge, short and friendly",
}
# Holdout cases are NOT in this plan on purpose. A separate agent writes them
# straight into evals/holdout-* (Step 2b) so whoever tunes the description
# never sees them.

root = pathlib.Path(sys.argv[1])
for name, prompt in CASES.items():
    d = root / name
    (d / "graders").mkdir(parents=True, exist_ok=True)
    (d / "prompt.md").write_text(FRONT + prompt + "\n")
    quiet = "-quiet-" in name
    (d / "graders" / ("quiet.md" if quiet else "fired.md")).write_text(QUIET if quiet else FIRED)
print(f"wrote {len(CASES)} cases to {root}")
```

- [ ] **Step 2: Generate the cases and delete the old ones**

```bash
python3 $S/make_trigger_cases.py $P/evals
git -C $W rm -rq plugins/come-on/evals/trigger-* plugins/come-on/evals/no-trigger-*
ls $P/evals | sort
```

Expected: `wrote 12 cases`, and the listing shows `tune-*` (12) and `scn-*` (10), with no `trigger-*` or `no-trigger-*`.

- [ ] **Step 2b: A separate agent writes the holdout cases**

Dispatch a fresh general-purpose subagent (`Agent` tool, `model: opus`). It gets only the brief below: not this plan, not the spec, and not `SKILL.md` or its description. Whoever runs Tasks 5 to 7 must not read `evals/holdout-*` or print their contents, and must not reuse this subagent.

```text
Write 8 eval cases for a Claude Code skill into <P>/evals/, one directory each:
holdout-trigger-01..04 and holdout-quiet-01..04. Each has prompt.md and one grader.
Do not read any other file under <P>; you don't need them.

What the skill is for: catching Claude at the moment it is about to stop short on
its own: claiming something is done/verified/pre-existing from memory or a weak
signal, giving up after one attempt, building on an old conclusion (handoff,
design doc) without re-checking, handing the user a choice or a message full of
unexplained IDs, or burying the answer in a long reply.

holdout-trigger-*: realistic prompts (casual, concrete, with file names, numbers,
backstory) where the natural reply would stop short in one of those ways. They
must NOT contain pushback phrases like "come on", "did you check", "try again",
"are you sure", "tl;dr". Cover four different situations.

holdout-quiet-*: near-misses. They share vocabulary with the above (retry,
blocked, check, short version, what does X mean) but a direct answer is correct
and nothing needs verifying. Not obviously unrelated tasks.

prompt.md format (exactly):
---
runs: 3
max_turns: 3
allowed_tools: [Read, Glob, Grep, Skill]
---

<the prompt>

Grader file graders/fired.md (trigger cases):
---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?come-on"'
min: 1
---
The come-on skill fires on this prompt.

Grader file graders/quiet.md (quiet cases): same frontmatter plus `max: 0`
after `min: 0` (min: 0 instead of 1), body "The come-on skill stays quiet on this prompt."

Reply only with "wrote 8 cases" and the 8 directory names. Do not echo the prompts.
```

Verify without reading the prompts:

```bash
ls -d $P/evals/holdout-* | wc -l                               # expect: 8
ls $P/evals/holdout-*/graders/                                  # fired.md x4, quiet.md x4
claude plugin validate $P 2>&1 | tail -3
```

- [ ] **Step 3: Josh reviews the set in skill-creator's review page**

```bash
SC=/Users/josh.nichols/.claude/plugins/cache/claude-plugins-official/skill-creator/315c4e48967d/skills/skill-creator
python3 - "$P/evals" "$SC/assets/eval_review.html" "$S/eval_review_come-on.html" "$P/skills/come-on/SKILL.md" <<'PY'
import json, pathlib, re, sys
evals, tmpl, out, skill = map(pathlib.Path, sys.argv[1:])
items = []
for d in sorted(evals.glob("tune-trigger-*")) + sorted(evals.glob("tune-quiet-*")):
    body = (d / "prompt.md").read_text().split("---\n", 2)[2].strip()
    items.append({"query": f"[{d.name}] {body}", "should_trigger": "-trigger-" in d.name})
desc = re.search(r"^description: (.*)$", skill.read_text(), re.M).group(1)
html = tmpl.read_text().replace("__EVAL_DATA_PLACEHOLDER__", json.dumps(items)) \
    .replace("__SKILL_NAME_PLACEHOLDER__", "come-on").replace("__SKILL_DESCRIPTION_PLACEHOLDER__", desc)
out.write_text(html); print(out)
PY
```

The sandbox blocks `open`, so tell Josh to run `! open /Users/josh.nichols/pickleton/projects/come-on/.scratch/eval_review_come-on.html`, edit or toggle queries, and click **Export Eval Set** (it saves to `~/Downloads/eval_set.json`). Apply his edits to `CASES` in `make_trigger_cases.py`: each exported query keeps its `[case-name]` prefix, so map edits back by name. Then re-run Step 2 with `rm -rf $P/evals/tune-* $P/evals/holdout-*` first. If he exports with no changes, move on. The page covers the tune set only. If Josh wants to vet the holdout prompts, he reads `evals/holdout-*/prompt.md` himself and sends any fixes to the holdout-writer subagent, not to the tuning agent.

**Known contamination:** the plan's draft description (Task 5 Step 2) was written by the same session that wrote the tune prompts, so treat the tune scores as optimistic. The holdout set is the only number that counts.

- [ ] **Step 4: Commit**

```bash
git -C $W add plugins/come-on/evals
git -C $W commit -m "test(come-on): split trigger evals into tune and holdout sets

Replace the trigger set the description was tuned against with realistic
prompts that carry no pushback cue, plus near-miss quiet cases. The holdout
cases are never used while tuning."
```

---

### Task 2: Mode-routing cases

**Files:**
- Create: `$P/evals/mode-weigh/`, `$P/evals/mode-check/`, `$P/evals/mode-unpack/` (each has `prompt.md` and `graders/expectations.md`)

These run in Task 8 against the new skill only, since the old skill has no modes.

- [ ] **Step 1: Write the three cases**

`$P/evals/mode-weigh/prompt.md`:

```markdown
---
runs: 3
max_turns: 4
allowed_tools: [Read, Glob, Grep, Skill]
---

/come-on weigh we're picking a job queue for the new rates service: sidekiq (we already run redis for caching) or good_job (postgres only, one less moving part). which one?
```

`$P/evals/mode-weigh/graders/expectations.md`:

```markdown
---
type: llm
weight: 1
---
- Lays out at least the two options, each with what you get and the main tradeoff
- Leads with a clear recommendation
- Leaves the decision to the user rather than declaring it settled
```

`$P/evals/mode-check/prompt.md`:

```markdown
---
runs: 3
max_turns: 4
allowed_tools: [Read, Glob, Grep, Skill]
---

/come-on check you said earlier that the cache TTL is already set to 2 hours in config/rates.yml
```

`$P/evals/mode-check/graders/expectations.md`:

```markdown
---
type: llm
weight: 1
---
- Treats the TTL claim as something to verify rather than restating it
- Tries to read config/rates.yml (or searches for it) this session
- Reports plainly that the file or the claim could not be confirmed, rather than asserting the TTL is 2 hours
```

`$P/evals/mode-unpack/prompt.md`:

```markdown
---
runs: 3
max_turns: 4
allowed_tools: [Read, Glob, Grep, Skill]
---

/come-on unpack for my skip-level: "PAYR-2291 is blocked on the FX-cache ADR; we'll do option B (warm-on-write) once INC-4411's postmortem lands, which unblocks the flags-v2 cutover."
```

`$P/evals/mode-unpack/graders/expectations.md`:

```markdown
---
type: llm
weight: 1
---
- Rewrites the message for a reader who has never seen these IDs or labels
- Each ticket/incident/label gets a plain one-line "this is..." or is replaced with plain words
- Says where things stand and why it matters, up top
- Flags any ID it can't explain rather than inventing what it means
```

- [ ] **Step 2: Commit**

```bash
git -C $W add plugins/come-on/evals/mode-*
git -C $W commit -m "test(come-on): add mode-routing eval cases"
```

---

### Task 3: Results-to-viewer converter

**Files:**
- Create: `/Users/josh.nichols/pickleton/projects/come-on/tools/results_to_viewer.py`

This converts `claude plugin eval --json` output into the workspace layout skill-creator's `eval-viewer/generate_review.py` reads. That layout is a directory per run containing `outputs/`, plus `eval_metadata.json` (with `prompt`) and `grading.json` (`expectations: [{text, passed, evidence}]`). The `--json` result has `cases[].{name, promptMarkdown, arms.{with,without}[]}`, and each run has `score`, `passed`, `tracePath`, and `graders[].{name, passed, explanation, evidence?}`. `tracePath` only survives with `--keep-temp`.

- [ ] **Step 1: Write the converter**

```python
#!/usr/bin/env python3
"""Convert `claude plugin eval --json` results into a skill-creator viewer workspace.

Usage: results_to_viewer.py <result.json> <workspace-dir> [--label old|new]
Layout: <ws>/<case>/<label>-<arm>-run<k>/{outputs/response.md, eval_metadata.json, grading.json}
"""
import argparse, json, pathlib


def final_text(trace_path):
    p = pathlib.Path(trace_path or "")
    if not p.is_file():
        return "(trace missing: re-run the sweep with --keep-temp)"
    last = ""
    for line in p.read_text().splitlines():
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        msg = ev.get("message") if isinstance(ev, dict) else None
        if ev.get("type") == "assistant" and isinstance(msg, dict):
            texts = [c.get("text", "") for c in msg.get("content", []) if isinstance(c, dict) and c.get("type") == "text"]
            if any(t.strip() for t in texts):
                last = "\n".join(texts)
    return last or "(no assistant text in trace)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("result")
    ap.add_argument("workspace")
    ap.add_argument("--label", default="run")
    a = ap.parse_args()
    data = json.loads(pathlib.Path(a.result).read_text())
    ws = pathlib.Path(a.workspace)
    n = 0
    for case in data["cases"]:
        for arm, runs in case.get("arms", {}).items():
            for k, run in enumerate(runs, 1):
                d = ws / case["name"] / f"{a.label}-{arm}-run{k}"
                (d / "outputs").mkdir(parents=True, exist_ok=True)
                (d / "outputs" / "response.md").write_text(final_text(run.get("tracePath")))
                (d / "eval_metadata.json").write_text(json.dumps(
                    {"eval_name": case["name"], "prompt": case.get("promptMarkdown", "")}, indent=2))
                (d / "grading.json").write_text(json.dumps({"expectations": [
                    {"text": g["name"], "passed": bool(g.get("passed")),
                     "evidence": g.get("evidence") or g.get("explanation", "")}
                    for g in run.get("graders", [])]}, indent=2))
                n += 1
    print(f"wrote {n} runs to {ws}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Test it against the last real sweep**

```bash
colima ssh -p plugin-eval -- cp /home/lima.guest/scenarios2.json /Users/josh.nichols/pickleton/projects/come-on/.scratch/
python3 /Users/josh.nichols/pickleton/projects/come-on/tools/results_to_viewer.py $S/scenarios2.json $S/viewer-smoke --label old
ls $S/viewer-smoke | head -3; ls $S/viewer-smoke/scn-check-preexisting
cat $S/viewer-smoke/scn-check-preexisting/old-with-run1/grading.json | head -12
```

Expected: `wrote 60 runs` (10 cases × 2 arms × 3 runs), run dirs named `old-with-run1` … `old-without-run3`, and a `grading.json` with `text`/`passed`/`evidence`. `response.md` will say "trace missing" because that sweep didn't use `--keep-temp`. That's expected and proves the fallback path works.

- [ ] **Step 3: Commit (pickleton)**

```bash
cd /Users/josh.nichols/pickleton && git branch --show-current   # main
git add projects/come-on/tools/results_to_viewer.py
git commit -m "come-on: eval-results-to-viewer converter" -- projects/come-on/tools/results_to_viewer.py
```

---

### Task 4: RED — old skill on holdout + scenarios

**Files:**
- Create: `/Users/josh.nichols/pickleton/projects/come-on/evals-log.md`

Runs the current (old) skill against the new holdout triggers and the 10 scenarios. Scenarios use 5 runs per case for the noisy ones. Estimated cost: holdout triggers (8 × 3 = 24 runs) about $1.50, scenarios about $8 to $10 at 3 to 5 runs. **Confirm the cost with Josh first.**

- [ ] **Step 1: Bump runs on the noisy scenarios**

The cases that swung between the two earlier sweeps get `runs: 5`: `scn-check-preexisting`, `scn-try-transient-retry`, `scn-weigh-retry-policy`, `scn-unpack-for-reviewer`, `scn-rederive-stale-root-cause`. Edit `runs: 3` → `runs: 5` in each `case.yaml` (or in `prompt.md` frontmatter, if the case has no `case.yaml`):

```bash
for c in scn-check-preexisting scn-try-transient-retry scn-weigh-retry-policy scn-unpack-for-reviewer scn-rederive-stale-root-cause; do
  f=$P/evals/$c/case.yaml; [ -f "$f" ] || f=$P/evals/$c/prompt.md
  sed -i '' 's/^runs: 3$/runs: 5/' "$f"; grep -H '^runs:' "$f"
done
git -C $W commit -qam "test(come-on): 5 runs on the noisy scenarios" && git -C $W log --oneline -1
```

- [ ] **Step 2: Build the old-skill copy with the new evals**

```bash
OLD=$(cat $S/old-skill-sha)
rm -rf $S/come-on-old && mkdir -p $S/come-on-old
git -C $W archive "$OLD" plugins/come-on | tar -x -C $S/come-on-old --strip-components=2
rm -rf $S/come-on-old/evals && cp -R $P/evals $S/come-on-old/evals && rm -rf $S/come-on-old/evals/results
ls $S/come-on-old/skills    # expect: come-on plus the six come-on-* entry points (old shape)
colima ssh -p plugin-eval -- bash -lc 'rm -rf ~/cp/come-on-old && cp -R /Users/josh.nichols/pickleton/projects/come-on/.scratch/come-on-old ~/cp/come-on-old'
```

- [ ] **Step 3: Run holdout triggers (old)**

```bash
colima ssh -p plugin-eval -- bash -lc 'cd ~ && claude plugin eval ~/cp/come-on-old --case "holdout-*" --ablation none \
  --trust-plugin --no-publish --keep-temp --max-cost-usd 3 --json ~/red-holdout.json'
```

Expected: 8 cases with a pass rate each. A trigger case passes when the skill fired, and a quiet case passes when it stayed quiet.

- [ ] **Step 4: Run scenarios (old)**

```bash
colima ssh -p plugin-eval -- bash -lc 'cd ~ && claude plugin eval ~/cp/come-on-old --case "scn-*" --scaffold --allow-tools Bash \
  --trust-plugin --no-publish --keep-temp --max-cost-usd 15 --json ~/red-scenarios.json'
```

Expected: per scenario, the with/without scores, the delta, and the `skill-fired` indicator. If bwrap fails, Josh re-runs the sysctl from Conventions and you re-run this step.

- [ ] **Step 5: Pull results and log them**

```bash
colima ssh -p plugin-eval -- bash -lc 'cp ~/red-holdout.json ~/red-scenarios.json /Users/josh.nichols/pickleton/projects/come-on/.scratch/'
python3 - $S/red-holdout.json $S/red-scenarios.json <<'PY'
import json, sys
for f in sys.argv[1:]:
    d = json.load(open(f)); print(f"\n## {f.split('/')[-1]}  cost ${d['costUsd']:.2f}")
    for c in d["cases"]:
        a = c["aggregates"]
        fired = sum(any(g["name"] in ("skill-fired", "fired") and g["passed"] for g in r["graders"]) for r in c["arms"].get("with", []))
        n = len(c["arms"].get("with", []))
        print(f"| {c['name']} | pass {a.get('passRate', 0):.2f} | with {a.get('score', 0):.2f} | without {a.get('scoreWithout', float('nan')):.2f} | fired {fired}/{n} |")
PY
```

Create `projects/come-on/evals-log.md` with a `## 2026-MM-DD RED (old skill, <sha>)` section, and paste the two tables plus the total holdout should-trigger firing count (sum of fired across `holdout-trigger-*`) and the false-fire count (fires across `holdout-quiet-*`). **These two numbers, plus scenario fired counts, are the baseline the success check compares against.**

- [ ] **Step 6: Commit the log (pickleton)**

```bash
cd /Users/josh.nichols/pickleton && git branch --show-current
git add projects/come-on/evals-log.md && git commit -m "come-on: RED baseline numbers" -- projects/come-on/evals-log.md
```

---

### Task 5: Consolidate to one skill with modes

**Files:**
- Delete: `$P/skills/come-on-{check,try,rederive,weigh,unpack,simplify}/`
- Rewrite: `$P/skills/come-on/SKILL.md`
- Modify: `$P/skills/come-on/references/angles.md` (prepend the per-angle checklists)

- [ ] **Step 1: Move the per-angle checklists into `references/angles.md`**

Prepend this block to `references/angles.md`, right under its `# Angles, in more detail` heading, keeping the existing content (tool menu, clean-room pass, shapes) below it:

```markdown
## Checklists

### check: before claiming done / fixed / found / pre-existing

- State the claim precisely, then verify it this session: read the file, run the command, grep the evidence. Memory and the handoff don't count.
- Report: confirmed, not true, or partial, with the evidence.
- Never call a failure pre-existing, unrelated, or flaky without reproducing it on a clean base this session (`main`, a WIP commit and re-run, or `git blame`). A guess here sends the user chasing the wrong cause.

### try: before "can't" / "impossible" / "blocked" / "say the word"

- Transient failure (timeout, 403, a hook's API unreachable)? Retry once before calling it a block.
- Before "can't": list the other tools that could answer, and try the likeliest (menu below).
- Read-only and cheap? Do it. Don't offer to.
- Before "impossible" or "weeks of work": actually attempt it for a few minutes.
- Still blocked: say what you tried.

### rederive: before building on an earlier conclusion

- Say where the conclusion came from (handoff, design doc, past investigation, "the usual way") and how old it is.
- Re-establish it from current evidence: runs, code, recent sessions, the data.
- Expensive to reverse? Offer a clean-room pass (below).
- Report what still holds, what doesn't, and what changed.

### weigh: before putting options in front of the user

- Drop options that aren't real.
- Find the prior art (ADRs, docs, code, earlier decisions), then check it still holds. Old and load-bearing means `rederive` it.
- Per real option: what you get, the main tradeoff, effort, durability, and the evidence for each.
- Lead with a recommendation. The user decides.

### unpack [reader]: before options or a question

The reader wasn't there for what you read. Default reader: the user in this session.

- Every ID (ticket, PR, internal label) gets a link and a one-line "this is…".
- Jargon and terms you coined: explain on first use, or use plain words.
- Before a question: one line on where things stand and why it matters now.
- Option labels never collide with labels already in play.

### simplify [shape]: before a long reply without an answer up top

- Answer first, then a few bullets, then stop.
- No new digging. Cut and restate plainly.
- Honor a requested shape (`for slack`, `for a PR comment`). See shapes below.
```

- [ ] **Step 2: Rewrite `SKILL.md`**

Replace the entire file with:

```markdown
---
name: come-on
description: Use when Claude is about to stop short. That means about to say something is done, fixed, found, pre-existing, unrelated, or "how it works" without evidence from this session; about to say "can't", "blocked", or "impossible" after one attempt, or offer "say the word and I'll check"; about to act on a conclusion from a handoff, old design doc, or earlier investigation without re-checking it; about to put options, a tradeoff, or a question in front of the user, especially one full of IDs or labels they never saw; or about to send a long reply with no clear answer up top. Also when the user pushes back: "come on", "did you check", "try again", "what does this mean", "tl;dr". Use even when confident; confidence is the symptom, not the all-clear.
argument-hint: "[check|try|rederive|weigh|unpack|simplify] [target]"
---

# come on

Don't stop short. Do the cheap work, then make it land.

## Mode

`$ARGUMENTS`

- **Empty:** you're here on your own or the user said "come on". Pick the angles that fit the turn you're about to send (or the one the user is reacting to).
- **Starts with a mode** (`check`, `try`, `rederive`, `weigh`, `unpack`, `simplify`): run that angle on the last reply, plus any other that obviously applies. The rest of the arguments name the target: a claim, a reader (`unpack for my skip-level`), or a shape (`simplify for slack`).

## The core (every angle)

1. **Name the thin basis** in one line: "I'm about to [claim / give up / build on / offer options / send this] based on [memory / one attempt / an old conclusion / an unweighed pick / what I read and the reader didn't]."
2. **Do the cheap work** for each angle that fired. Angles stack.
3. **Come back with the receipt**: what you ran, read, or found.

The reason this matters: the user can't see what you didn't check. A confident claim built on memory reads exactly like one built on evidence, so the cost lands on them later, as a wrong root cause, a give-up that wasn't real, or a choice they can't parse.

**Skip** when the step is trivial and easy to undo, or the claim rests on output from this same turn. If you're arguing with yourself about whether it's trivial, it isn't.

**If the work flips an earlier answer, say so plainly.** Flipping after checking means this worked.

## Angles

| Angle | Before you… | The cheap work |
|---|---|---|
| check | claim done / fixed / found / pre-existing | verify it this session; reproduce "pre-existing" on a clean base |
| try | say can't / blocked / "say the word" | retry transients once, try the next tool, just do read-only things |
| rederive | build on a handoff or old conclusion | say where it came from and how old, re-check against current evidence |
| weigh | put options in front of the user | drop fake options, find prior art, tradeoffs with evidence, recommend |
| unpack | ask a question or offer options | define every ID and label for a reader who wasn't there |
| simplify | send a long reply | answer first, a few bullets, stop |

Full checklist per angle, the tool menu, the clean-room pass, and reply shapes: `references/angles.md`. Read the section for each angle you're running.

## Red flags: stop and run the core

- "I'm confident I already did this" / "the handoff says it's done"
- "that failure is probably pre-existing / flaky"
- "I can't from here" (after one try), or "say the word and I'll..."
- "we already decided this" (when?)
- "here are the options" (researched? readable cold?)
- a reply that needs a scroll before the answer

Excuses and counters: `references/rationalizations.md`. Worked examples: `references/examples.md`.
```

- [ ] **Step 3: Delete the entry-point skills**

```bash
git -C $W rm -rq plugins/come-on/skills/come-on-check plugins/come-on/skills/come-on-try plugins/come-on/skills/come-on-rederive \
  plugins/come-on/skills/come-on-weigh plugins/come-on/skills/come-on-unpack plugins/come-on/skills/come-on-simplify
ls $P/skills    # expect: come-on
```

- [ ] **Step 4: Verify size, description length, and validity**

```bash
awk '/^---$/{n++; next} n>=2' $P/skills/come-on/SKILL.md | wc -w          # body: expect < 500
awk '/^description:/{sub(/^description: /,""); print length($0)}' $P/skills/come-on/SKILL.md   # expect < 1024
claude plugin validate $P
grep -rn "come-on-\(check\|try\|rederive\|weigh\|unpack\|simplify\)" $P --include=*.md | grep -v '/evals/results/'
```

Expected: body under 500 words, description under 1024 characters, validate passes, and the grep finds nothing outside the README (fixed in Task 11). If the body is over 500, trim the "reason this matters" paragraph first and leave the table alone.

- [ ] **Step 5: Smoke-test mode routing (1 run, host, no Bash)**

```bash
rm -rf $TMPDIR/cp && mkdir -p $TMPDIR/cp && cp -R $P $TMPDIR/cp/come-on && rm -rf $TMPDIR/cp/come-on/evals/results
claude plugin eval "$TMPDIR/cp/come-on" --case 'mode-weigh' --ablation none --trust-plugin --no-publish --max-cost-usd 1 --json $TMPDIR/mode-smoke.json
```

Expected: the case runs and the judge passes. **If the `/come-on weigh` slash prefix isn't expanded inside eval prompts** (the judge says the reply ignored the mode, or the trace shows a literal `/come-on` with no skill load), change all three `mode-*` prompts to start with `Use the come-on skill in weigh mode:` (and likewise for check/unpack), note that in the evals-log, and re-run.

- [ ] **Step 6: Commit**

```bash
git -C $W add -A plugins/come-on/skills plugins/come-on/evals/mode-*
git -C $W commit -m "feat(come-on): one skill with modes instead of entry-point skills

/come-on <mode> replaces come-on-check and friends. Manual uses now count
toward the skill that has to auto-fire, and there's no second Skill hop.
SKILL.md drops under 500 words with the per-angle checklists moved to
references/angles.md, and the description is rewritten around the moment
Claude is about to stop short."
```

---

### Task 6: GREEN check on tune set

**Files:** none (read-only run)

- [ ] **Step 1: Run tune set against the new skill (host, no Bash needed)**

```bash
rm -rf $TMPDIR/cp && mkdir -p $TMPDIR/cp && cp -R $P $TMPDIR/cp/come-on && rm -rf $TMPDIR/cp/come-on/evals/results
claude plugin eval "$TMPDIR/cp/come-on" --case 'tune-*' --ablation none --trust-plugin --no-publish --keep-temp \
  --max-cost-usd 3 --json $S/tune-iter1.json
```

If the sandbox blocks it (EPERM writing outside the worktree, or a proxy deny), retry the same command with `dangerouslyDisableSandbox: true`. If it refuses because of ~/.ssh symlinks, run it in the VM instead (copy to `~/cp/come-on`, same flags).

- [ ] **Step 2: Read the result**

Count should-trigger fires across `tune-trigger-*` (out of 18) and false fires across `tune-quiet-*` (out of 18). For each miss, open its trace (the `tracePath` in the JSON, kept by `--keep-temp`) and write one line on what Claude did instead, in the agent's own words where possible. Those lines are the RED rationalizations that Task 7 targets.

---

### Task 7: Tune the description (tune set only, max 3 passes)

**Files:**
- Modify: `$P/skills/come-on/SKILL.md` (frontmatter `description` only)

- [ ] **Step 1: Edit the description for the misses found in Task 6**

Rules (writing-skills + skill-creator):
- Start with "Use when", third person, under 1024 characters.
- Describe the situation, not the skill's steps.
- Generalize from the misses. Don't paste tune prompts or their nouns (`backfill`, `N+1`, `datadog`) into the description, because that's overfitting.
- Push harder on any situation type that missed ("about to report a status", "about to answer yes/no from a log line").
- A near-miss false fire calls for narrowing (e.g. "the user's own text" for simplify), not for adding more triggers.

- [ ] **Step 2: Re-run the tune set**

Same command as Task 6 Step 1, with `--json $S/tune-iter<N>.json`.

- [ ] **Step 3: Stop condition**

Stop when tune should-trigger fires are at or above 14/18 with at most 2/18 false fires, or after 3 passes, whichever comes first. Keep whichever pass scored best on the tune set. Then re-check the length (Task 5 Step 4's `awk` line).

- [ ] **Step 4: Commit**

```bash
git -C $W commit -qam "feat(come-on): tune description for situational triggers" && git -C $W log --oneline -1
```

---

### Task 8: GREEN measure — new skill on holdout, scenarios, and modes

**Files:**
- Modify: `/Users/josh.nichols/pickleton/projects/come-on/evals-log.md`

Same cases and run counts as Task 4, plus `mode-*`. Estimated cost is about $10 to $12. **Confirm with Josh first.**

- [ ] **Step 1: Copy the new plugin into the VM**

```bash
rm -rf $S/come-on-new && cp -R $P $S/come-on-new && rm -rf $S/come-on-new/evals/results
colima ssh -p plugin-eval -- bash -lc 'rm -rf ~/cp/come-on && cp -R /Users/josh.nichols/pickleton/projects/come-on/.scratch/come-on-new ~/cp/come-on'
```

- [ ] **Step 2: Run the three sweeps**

```bash
colima ssh -p plugin-eval -- bash -lc 'cd ~ && claude plugin eval ~/cp/come-on --case "holdout-*" --ablation none \
  --trust-plugin --no-publish --keep-temp --max-cost-usd 3 --json ~/green-holdout.json'
colima ssh -p plugin-eval -- bash -lc 'cd ~ && claude plugin eval ~/cp/come-on --case "scn-*" --scaffold --allow-tools Bash \
  --trust-plugin --no-publish --keep-temp --max-cost-usd 15 --json ~/green-scenarios.json'
colima ssh -p plugin-eval -- bash -lc 'cd ~ && claude plugin eval ~/cp/come-on --case "mode-*" --ablation none \
  --trust-plugin --no-publish --keep-temp --max-cost-usd 2 --json ~/green-modes.json'
colima ssh -p plugin-eval -- bash -lc 'cp ~/green-*.json /Users/josh.nichols/pickleton/projects/come-on/.scratch/'
```

- [ ] **Step 3: Log GREEN next to RED**

Re-run the summary snippet from Task 4 Step 5 on `$S/green-holdout.json $S/green-scenarios.json $S/green-modes.json`. Append a `## 2026-MM-DD GREEN (new skill, <sha>)` section to `evals-log.md` with the tables, plus a comparison block:

```markdown
| metric | RED (old) | GREEN (new) |
|---|---|---|
| holdout should-trigger fires (of 12) | | |
| holdout false fires (of 12) | | |
| scenarios where skill fired ≥1 run (of 10) | | |
| total scenario fires (of 40) | | |
| mode cases passing (of 3) | n/a | |
```

Fill every cell from the JSON. **Success** (from the spec): holdout fires clearly above RED, false fires at or below RED, and modes 3/3. Record which of these held.

- [ ] **Step 4: Commit the log (pickleton)**

```bash
cd /Users/josh.nichols/pickleton && git branch --show-current
git commit -m "come-on: GREEN numbers vs RED" -- projects/come-on/evals-log.md
```

---

### Task 9: Human pass in skill-creator's viewer

**Files:** none committed (viewer output lives in `.scratch`)

- [ ] **Step 1: Build the workspace (old vs new scenarios)**

```bash
T=/Users/josh.nichols/pickleton/projects/come-on/tools/results_to_viewer.py
rm -rf $S/viewer && python3 $T $S/red-scenarios.json $S/viewer --label old && python3 $T $S/green-scenarios.json $S/viewer --label new
```

Expected: `wrote N runs` twice, with real reply text in `outputs/response.md` (not "trace missing"). If the traces are gone because the VM cleaned `/tmp`, copy the trace files out of the VM right after each sweep next time; for now, note it in the log and use the grader evidence alone.

- [ ] **Step 2: Generate the static viewer**

```bash
SC=/Users/josh.nichols/.claude/plugins/cache/claude-plugins-official/skill-creator/315c4e48967d/skills/skill-creator
python3 $SC/eval-viewer/generate_review.py $S/viewer --skill-name come-on --static $S/viewer.html
```

The sandbox blocks `open`. Tell Josh to run `! open /Users/josh.nichols/pickleton/projects/come-on/.scratch/viewer.html`, read the old vs new replies per scenario, leave feedback, and click **Submit All Reviews** (saves `feedback.json` to `~/Downloads`).

- [ ] **Step 3: Read the feedback**

```bash
cp ~/Downloads/feedback.json $S/feedback-iter1.json && python3 -c "import json;[print(r['run_id'],'::',r['feedback']) for r in json.load(open('$S/feedback-iter1.json'))['reviews'] if r['feedback'].strip()]"
```

Any feedback that says the new skill made a reply worse goes into Task 10.

---

### Task 10: REFACTOR (only if holdout firing is still weak or the feedback flagged regressions)

**Files:**
- Modify: `$P/skills/come-on/SKILL.md`
- Modify: `$P/skills/come-on/references/rationalizations.md`

- [ ] **Step 1: Mine the misses**

For each holdout or scenario run where the skill should have fired and didn't, read the trace and write down, verbatim, the sentence where Claude stopped short ("the backfill finished", "we can't see the logs from here"). Add any new excuse to the `rationalizations.md` table as `| "<excuse>" | <counter> |`.

- [ ] **Step 2: One description pass, then one holdout re-run**

Make the edit on the tune set's terms (same rules as Task 7 Step 1), run the tune set once (Task 6 command), then run the holdout once (Task 8 Step 2, first command only, `--json ~/refactor-holdout.json`). Log the result and stop. Don't iterate further against the holdout. That would turn it into a tune set.

- [ ] **Step 3: If firing is still weak, file the hook follow-up**

File a follow-up issue for a plugin `UserPromptSubmit`/`Stop` hook nudge, linking the evals-log numbers. Also file the listing-budget simulation follow-up (VM run with about 200 filler skills) if it doesn't exist yet.

- [ ] **Step 4: Commit**

```bash
git -C $W add plugins/come-on/skills && git -C $W commit -m "fix(come-on): close gaps found in holdout traces"
```

---

### Task 11: README and PR

**Files:**
- Modify: `$P/README.md`

- [ ] **Step 1: Replace the angles table and the entry-points paragraph**

Replace the table and the paragraph after it ("The `come-on` skill fires on its own…") with:

```markdown
| Angle | Fires when Claude is about to... | Invoke directly |
|---|---|---|
| check | claim something is done, fixed, pre-existing, or "how it works" | `/come-on check [claim]` |
| try | say "can't", "impossible", or "blocked", or offer "say the word and I'll..." | `/come-on try` |
| rederive | build on a conclusion from a handoff, an old design, or a past investigation without re-checking it | `/come-on rederive` |
| weigh | put options in front of you | `/come-on weigh` |
| unpack | put options or a question in front of you that assumes context you don't have | `/come-on unpack [for reader]` |
| simplify | send a long reply with no clear answer up top | `/come-on simplify [for shape]` |

The skill fires on its own at those moments, and angles stack (a choice usually gets `weigh` and `unpack` together). `/come-on` with no mode means "apply whatever fits the last turn". It's one skill on purpose: every manual use counts toward the skill that has to auto-fire, and Claude Code keeps descriptions for the skills you use most when the skill listing runs out of room.
```

- [ ] **Step 2: Rewrite the Testing status section**

Replace everything under `## Testing status` with the real numbers from `evals-log.md`, using this structure (every cell comes from the GREEN JSON, and the "old" column from RED):

```markdown
Eval cases live in `evals/` and run with Claude Code's built-in `claude plugin eval`:

- `tune-*`: trigger cases the description was tuned against.
- `holdout-*`: trigger cases it was never tuned against. These are the honest firing number.
- `scn-*`: behavior scenarios, each run with and without the plugin.
- `mode-*`: `/come-on <mode>` routing.

Last run: <date>. The old skill is the previous version of this plugin (separate entry-point skills, old description), run on the same cases.

**Firing** (holdout, should fire / should stay quiet):

| | old skill | this version |
|---|---|---|
| fires when it should (of 12) | | |
| fires when it shouldn't (of 12) | | |

**Behavior scenarios** (mean score 0 to 1, and how many runs the skill fired in):

| Scenario | without | with | skill fired |
|---|---|---|---|
<one row per scn-* case>

How to read it:

- A with/without gap only means something where the skill fired.
- <one honest line on what changed vs the old skill>
- <one honest line on what's still weak, if anything>
```

- [ ] **Step 3: Check prose and commit**

Use the `writing-voice` skill on the README prose (it's outbound, so no em-dashes). Then:

```bash
grep -n "come-on-\(check\|try\|rederive\|weigh\|unpack\|simplify\)" $P/README.md    # expect: nothing
git -C $W add plugins/come-on/README.md && git -C $W commit -m "docs(come-on): modes table and new eval results"
```

- [ ] **Step 4: Push and update the PR**

Use the `git:push` skill, then `git:pull-request` + `writing-voice` to refresh the PR #146 body (summary of modes, the holdout numbers, and the remaining auto-fire caveat; no internal tracker IDs). Keep it a draft until Josh says otherwise.

- [ ] **Step 5: Close out**

Update the tracking issue with the evals-log link, the final numbers, and "Last verified: <date>". Mark it completed if success held, or leave it in-progress with the follow-ups from Task 10.
