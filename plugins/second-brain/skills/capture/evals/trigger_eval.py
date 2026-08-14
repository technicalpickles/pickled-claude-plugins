#!/usr/bin/env python3
"""Measure whether a *plugin* skill actually triggers on real user prompts.

Why this exists instead of skill-creator's scripts/run_eval.py
-------------------------------------------------------------
run_eval.py injects the skill under test by writing a stub into
`<project_root>/.claude/commands/<name>.md`, on the premise that it will "appear
in Claude's available_skills list." That premise is false on current Claude Code:
project commands are *user*-invocable slash commands, not model-invocable skills.
Verified 2026-08-14 - asked directly, the model reports it cannot see such a
command, and instead reaches for whatever real skills are installed. So every
query scores as "not triggered" no matter how good the description is, which is
the false-negative behavior that makes run_eval useless for plugin skills.

This harness instead loads the *real* skill via `claude --plugin-dir`, so what
gets measured is the artifact that will actually ship.

One gotcha it handles: `--plugin-dir` loses to an already-installed plugin of the
same name. Pointing at a directory that contains a plugin named `second-brain`
while `second-brain` is installed silently gives you the *installed* version.
So the plugin tree is copied to a temp dir per variant, which also gives a clean
place to patch the description for A/B runs.

Usage
-----
  ./trigger_eval.py --eval-set trigger-evals.json \\
      --plugin-src /path/to/plugins/second-brain \\
      --skill capture --namespace second-brain \\
      --cwd /path/to/vault-like-dir --runs 3

  # A/B a candidate description without touching the real SKILL.md
  ./trigger_eval.py ... --description "$(cat candidate.txt)" --label candidate
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


def patch_description(skill_md: Path, new_description: str) -> None:
    """Replace the `description:` field in a SKILL.md's YAML frontmatter.

    Uses a single-line flow scalar with quotes escaped, which is enough for the
    descriptions we generate and avoids a YAML dependency.
    """
    text = skill_md.read_text()
    if not text.startswith("---"):
        raise ValueError(f"{skill_md} has no frontmatter")
    end = text.index("\n---", 3)
    fm, body = text[3:end], text[end:]

    out, i, replaced = [], 0, False
    lines = fm.split("\n")
    while i < len(lines):
        line = lines[i]
        if line.startswith("description:"):
            escaped = new_description.replace("\\", "\\\\").replace('"', '\\"')
            out.append(f'description: "{escaped}"')
            i += 1
            # skip continuation lines of the old value (indented or block scalar)
            while i < len(lines) and (lines[i].startswith((" ", "\t")) or lines[i] == ""):
                i += 1
            replaced = True
            continue
        out.append(line)
        i += 1

    if not replaced:
        raise ValueError(f"no description: field in {skill_md}")
    skill_md.write_text("---" + "\n".join(out) + body)


def stage_plugin(plugin_src: Path, skill: str, description: str | None) -> Path:
    """Copy the plugin to a temp dir so --plugin-dir can't lose to the installed copy."""
    tmp = Path(tempfile.mkdtemp(prefix="trigeval-"))
    dest = tmp / plugin_src.name
    shutil.copytree(plugin_src, dest)
    if description:
        patch_description(dest / "skills" / skill / "SKILL.md", description)
    return tmp


def ran_skill(events: str, target: str) -> bool:
    """True if any assistant turn invoked the Skill tool with our target skill."""
    for line in events.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") != "assistant":
            continue
        for item in event.get("message", {}).get("content", []) or []:
            if item.get("type") != "tool_use":
                continue
            if item.get("name") == "Skill" and item.get("input", {}).get("skill") == target:
                return True
    return False


def one_run(query: str, plugin_dir: Path, target: str, cwd: Path, turns: int, timeout: int) -> bool:
    cmd = [
        "claude", "-p", query,
        "--plugin-dir", str(plugin_dir),
        "--max-turns", str(turns),
        "--output-format", "stream-json", "--verbose",
    ]
    try:
        proc = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout,
            env={k: v for k, v in __import__("os").environ.items() if k != "CLAUDECODE"},
        )
    except subprocess.TimeoutExpired:
        return False
    return ran_skill(proc.stdout, target)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval-set", required=True, type=Path)
    ap.add_argument("--plugin-src", required=True, type=Path)
    ap.add_argument("--skill", required=True, help="skill dir name, e.g. capture")
    ap.add_argument("--namespace", required=True, help="plugin namespace, e.g. second-brain")
    ap.add_argument("--cwd", required=True, type=Path, help="dir to run claude in")
    ap.add_argument("--description", default=None, help="override description for A/B")
    ap.add_argument("--label", default="current")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--turns", type=int, default=3)
    ap.add_argument("--timeout", type=int, default=200)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    evals = json.loads(args.eval_set.read_text())
    target = f"{args.namespace}:{args.skill}"
    plugin_dir = stage_plugin(args.plugin_src, args.skill, args.description)

    jobs = [(idx, r) for idx, _ in enumerate(evals) for r in range(args.runs)]
    triggers: dict[int, int] = {i: 0 for i in range(len(evals))}

    print(f"[{args.label}] {len(evals)} queries x {args.runs} runs -> {len(jobs)} invocations",
          file=sys.stderr)

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(one_run, evals[i]["query"], plugin_dir, target,
                        args.cwd, args.turns, args.timeout): i
            for i, _ in jobs
        }
        done = 0
        for fut in as_completed(futures):
            i = futures[fut]
            if fut.result():
                triggers[i] += 1
            done += 1
            if done % 10 == 0:
                print(f"  {done}/{len(jobs)}", file=sys.stderr)

    results, tp = [], 0
    for i, item in enumerate(evals):
        rate = triggers[i] / args.runs
        fired = rate >= 0.5
        ok = fired == item["should_trigger"]
        tp += ok
        results.append({
            "query": item["query"],
            "should_trigger": item["should_trigger"],
            "trigger_rate": rate,
            "triggers": triggers[i],
            "runs": args.runs,
            "pass": ok,
        })

    pos = [r for r in results if r["should_trigger"]]
    neg = [r for r in results if not r["should_trigger"]]
    summary = {
        "label": args.label,
        "accuracy": tp / len(results),
        "recall_on_should_trigger": sum(r["pass"] for r in pos) / len(pos) if pos else None,
        "specificity_on_should_not": sum(r["pass"] for r in neg) / len(neg) if neg else None,
        "passed": tp,
        "total": len(results),
    }
    out = {"summary": summary, "results": results,
           "description": args.description or "(from SKILL.md)"}

    print(json.dumps(out, indent=2))
    if args.out:
        args.out.write_text(json.dumps(out, indent=2))

    print(f"\n[{args.label}] accuracy {summary['passed']}/{summary['total']}"
          f"  recall={summary['recall_on_should_trigger']}"
          f"  specificity={summary['specificity_on_should_not']}", file=sys.stderr)
    for r in results:
        mark = "PASS" if r["pass"] else "FAIL"
        print(f"  [{mark}] {r['triggers']}/{r['runs']} want={r['should_trigger']}: {r['query'][:70]}",
              file=sys.stderr)

    shutil.rmtree(plugin_dir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
