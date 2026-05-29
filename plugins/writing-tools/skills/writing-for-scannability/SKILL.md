---
name: writing-for-scannability
description: Use when structuring prose so readers can skim it - drafting or restructuring READMEs, docs, PR or issue bodies, design docs, RFCs, or any long-form text where a wall of prose hides the structure. Also use when explicitly asked to make something scannable or skimmable, convert prose to a list, surface a buried list, fix a wall of text, or decide whether bullets or prose fit. Strong signal: text with parallel sentence shapes, contrast markers ("that's distinct from", "versus"), bolded terms followed by colons, or an embedded "X, Y, and Z" series. Composes with prose-clarity skills (concision) and voice skills (personality) rather than replacing them. Skip for source code and for casual one-line replies where formatting reads as overkill.
---

# Writing for Scannability

## Overview

Most people scan before they read. The job is to format prose so a scanner gets the gist and a committed reader gets the depth, without writing two versions. This is the structural axis of writing: when to surface a buried list, how to front-load for the eye, and how hard to lean on formatting per medium.

It is a different axis from concision (keeping prose tight) and from voice (keeping it human). Concision will happily leave a list buried inside a sentence; this skill decides when to pull it out. Voice keeps the result from reading like a corporate slide deck.

**Core principle:** if the prose is doing list work, let it be a list. If the prose is doing argument work, leave it.

## When to use

Reach for this when:

- A paragraph has parallel sentence shapes: *"X is A. Y is B."* or *"First... Second..."*
- You hit a contrast marker: *"that's distinct from"*, *"as opposed to"*, *"versus"*, *"on the other hand"*
- You have bolded terms each followed by a colon and a definition (a definition list hiding in prose)
- Three or more parallel items pile up
- A sentence carries an embedded series: *"create X, query Y, and delete Z"*
- Someone hands you a wall of text and asks you to make it skimmable, or to restructure a README / PR body / design doc

When NOT to use:

- Source code or code comments
- A casual one-line Slack reply or chat message where bullets would read as overkill
- Personal-voice writing (a stylistic essay, an apology) where the unbroken prose IS the point

## Convert prose to a list when the structure is already there

Each signal below means a list is trying to escape the paragraph. The shape to reach for: a one-sentence lead-in, then bullets, each starting with its load-bearing term.

| Signal | What it looks like |
|--------|--------------------|
| Parallel sentence shapes | *"X is A. Y is B."* repeated skeleton |
| Contrast markers | *"that's distinct from"*, *"versus"*, *"whereas"* |
| Bold term + colon | *"**Workflow**: how it runs. **Surface**: how it deploys."* |
| Rule of three | three or more siblings in a row |
| Embedded series | *"create X, query Y, and delete Z"* inside one sentence |

## Leave prose alone when the connective tissue matters

Bullets are lossy. They strip the words that say *why* items sit next to each other. Keep prose when:

- **Connectives carry argument** - *counterintuitively*, *and as a result*, *but only when*. These do real work bullets can't show.
- **The flow is causal or narrative** - *"we tried X, it failed because Y, so we pivoted to Z"* is a story, not a list.
- **The items are two and short** - they ride the sentence's rhythm fine.
- **The reader expects sustained reading** - long-form essays, persuasion, narrative.

If you bullet a passage and the words *but*, *because*, *so*, *counterintuitively* fall on the floor, the relationships were the point. Put it back as prose.

## Make every list item parallel

Once items are bullets, they must share grammatical shape, or the list reads as broken even when the reader can't say why. Reading the items aloud surfaces the break fast.

- **Same part of speech** - all nouns, all gerunds, or all infinitives. *running, swimming, cycling* (good) vs *running, to swim, cycling* (broken).
- **Same tense and voice** - don't mix *reduces* with *improving*.
- **Same opening shape** - if one bullet leads with a bolded term, all of them should.
- **Roughly the same weight** - a one-word item shouldn't share a list with a three-sentence one.

For steps where order matters, use a numbered list and start each item with an imperative verb: *Stop the server. Edit the config. Restart it.*

## Front-load the load-bearing word

Eye-tracking shows readers scan in an F: across the top, then down the left margin. So the leftmost word of every bullet, heading, and paragraph is the most-seen word on the page.

- **Lead with the term, not the run-up.** *"Workflow methodology - how a coding agent runs through..."* beats *"How a coding agent runs through the stages is the workflow methodology..."*
- **Bold the term, not the definition.** Bold marks the concept a scanner hunts for, not the supporting words around it.
- **Don't over-bold.** If everything is emphasized, nothing is.
- **One idea per paragraph.** A second concept buried in sentence three won't be seen by anyone scanning the first few words.

## How hard to lean: the sliding scale

Formatting (bold, headers, lists, explicit inverted-pyramid sections) costs the writer time and costs the reader some warmth. Heavily formatted prose reads corporate. Whether it's worth it scales with two things, not with medium alone:

- **Reader-entry diversity** - how many modes hit this? Triage (5-second decision), browse (scrolling), deep-read (committed), reference (came back to find one thing)?
- **Durability** - read once and gone, or returned to over time?

High diversity x high durability = lean in hard. Low x low = dial it down.

| Surface | How hard to lean | Why |
|---------|------------------|-----|
| Tweets | Universal rules only | One entry mode (scroll); no formatting affordances. Front-load harder, there's no slack. |
| Slack / chat | Light | Ephemeral but searched. Front-load the first word (*"Blocker:"*, *"FYI:"*). Headers feel like a memo. |
| PR / inline review comments | Dialed down | Conversational. One clear *"blocker because X, suggest Y"* beats three bulleted sections. |
| GitHub issues | Heavy | Multi-audience: triager wants 5-second triage, assignee wants detail. Descriptive title, TL;DR, sections. |
| PR descriptions | Heavy | Reviewer orients before diving into the diff. Problem in one line, approach in a paragraph, then deeper sections. |
| READMEs | Heavy | Ten seconds to decide if the repo is relevant. Title, one-line what, install, minimal example, links. |
| Design docs / RFCs / ADRs | Highest | Durable, multi-mode, read months apart. Headers carry navigation; TL;DR up top; then prose can have all the connective tissue it needs. |

What's **universal** (every surface, no dialing): front-load the load-bearing word, don't bury the conclusion, keep list items parallel.

## Reconciling with voice skills

Voice guidance often flags "bold-first bullets" (every bullet `**term:** definition`) as a canned, AI-generated tell. That's not a contradiction with this skill, it's a boundary:

- Bold-led bullets are **right** when the list is genuinely a definition/labeled list AND the medium rewards scanning (READMEs, docs, design docs, issue/PR bodies).
- They become a **tell** when applied to a plain non-definition list, used as the reflexive shape for *every* list, or leaned on hard in casual mediums (Slack, a personal-voice blog) where they read corporate.

This skill owns *how to build a good list*. Voice owns *don't let it become a monotonous tic*. The sliding scale above is the dial that decides which.

## Common mistakes

- **Bullet-bombing** - a page of nothing but bullets is a wall too. Mix bullets into prose.
- **Single-item lists** - a list of one isn't a list. Make it a sentence.
- **Mixed grammatical forms** - audible the moment you read the list aloud.
- **Over-bolding** - bold the load-bearing term, let supporting words support.
- **Burying the lede** - conclusion first. Resist the academic build-up.
- **Lists over ~8 items** - regroup into sub-lists or rethink. Emphasizing everything emphasizes nothing.

## Going deeper

- [references/scannable-writing-cheatsheet.md](references/scannable-writing-cheatsheet.md) - the one-page version: signals, the parallelism check, the F-pattern, a worked before/after, citations.
- [references/scannable-writing-guide.md](references/scannable-writing-guide.md) - the full treatment: the empirical case (NN/g, F-pattern, satisficing), the inverted-pyramid history, five conversion patterns with before/afters, anti-patterns, and a reading list with inline citations. Read this when you want the *why* behind a rule or a richer set of examples.

## The mantra

If the prose is doing list work, let it be a list. If it's doing argument work, leave it. Front-load the load-bearing word. Make every bullet parallel. Bold the term, not the definition. Conclude first, explain second.
