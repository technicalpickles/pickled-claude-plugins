# Design: writing-tools plugin / writing-for-scannability skill

Date: 2026-05-29

## Problem

Prose-clarity guidance (Strunk-style concision) optimizes for tight prose. It happily leaves
run-in lists inline (`create X, query Y, delete Z`) and produces walls of prose where the
structure is buried. That's harder to skim. No skill covered the *structural* axis of writing:
when to surface a buried list, how to front-load for scanning, and how hard to lean on
formatting per medium.

This plugin captures that as a reusable technique, grounded in the NN/g scannable-writing
research, the inverted-pyramid tradition, parallel structure, the F-pattern, and a sliding
scale across digital mediums.

## Three-axis model

Writing splits into complementary axes, invoked independently or together:

- **Concision** (e.g. an elements-of-style / writing-clearly skill) - keeps prose tight. Tends
  to keep lists inline.
- **Scannability** (this skill) - structure and visual hierarchy. Decides *when* to promote a
  buried list, how to front-load, how much to format per medium.
- **Voice** (a personal writing-voice skill) - personality. Keeps the result human, not canned.

Concision and scannability pull opposite directions on purpose: tight vs. skimmable. Voice
referees the tone.

## The bold-bullet reconciliation

A voice skill's anti-AI-tells may flag "bold-first bullets" (`**term:** definition` on every
bullet) as a canned LLM tell. This skill says bold-leading is *correct* for labeled lists. The
resolution, stated in SKILL.md:

- Bold-led bullets are right for genuine definition/labeled lists in scanning-reward mediums
  (READMEs, docs, design docs, PR/issue bodies).
- They are a tell when applied to plain item lists, used as the default shape for every list, or
  leaned on in casual mediums (Slack, personal blog).
- The sliding scale (reader-entry-diversity x durability) is the dial.

This skill owns "how to build a good list"; voice owns "don't let it become a tic." Because the
voice skill lives outside this repo (personal `~/.claude/skills`), the reconciliation is stated
here and the voice skill is edited separately to point back at it.

## Layout

```
plugins/writing-tools/
  .claude-plugin/plugin.json   (no version; versions live in marketplace.json)
  README.md
  docs/DESIGN.md               (this file)
  skills/writing-for-scannability/
    SKILL.md
    references/
      scannable-writing-guide.md       (deep research, verbatim)
      scannable-writing-cheatsheet.md  (one-pager, verbatim)
```

Added to `.claude-plugin/marketplace.json` as `writing-tools` at version `0.1.0`.

## SKILL.md shape

Operational, follows the skill-authoring conventions (description = triggers only, no workflow
summary): overview + core principle, when to use / not, convert-to-list signals (table), when to
leave prose alone, parallelism check, front-load / F-pattern, sliding-scale-by-medium table,
voice reconciliation, common mistakes, pointers to the two reference files, the mantra.

## Out of scope / follow-ups

- Editing the personal writing-voice skill to soften the "bold-first bullets" tell and add a
  cross-ref. That's a separate change outside this repo.
- Future writing skills (e.g. a structure-only restructurer, headline writing) could join this
  plugin later.
