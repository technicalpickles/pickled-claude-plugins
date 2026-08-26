---
name: checking-for-undisclosed-context
description: Use when reviewing or drafting a doc, PR/issue description, design doc, code-review prompt, or subagent persona that's supposed to stand on its own, to check whether it leans on vocabulary, acronyms, or structure pulled from other documentation or conversation the reader hasn't seen. Read it cold, as the specific intended reader, and flag spots where following it depends on context they don't have access to. Trigger phrases: "cold read this", "does this stand alone", "check this doesn't assume context", "would someone without the design doc follow this", "self-contained doc/prompt", "audience-context check". Distinct from writing-for-scannability (structure) and writing-voice (tone) - this is about audience access, not readability or personality.
---

# Checking for Undisclosed Context

## Overview

Text written by someone deep in a project accumulates vocabulary, acronyms, and structural assumptions from whatever they've been reading and discussing - a design doc, a ticket thread, an earlier stage of the same pipeline. None of that is visible to a reader who wasn't there. The author can't tell the difference between "this term is obvious" and "I only find this obvious because I wrote the doc it came from" without deliberately stepping outside their own head.

This skill is that step: read the text as a specific named reader, not as its author, and find the places where understanding it secretly depends on a document or conversation that reader was never given.

There's a second version of this specific to text that passes through multiple model turns, drafts, or agent hops: a model can coin a term on the spot to name something in the moment - a workaround, a state, a recurring shape - and that term gets carried into later output simply because it appeared once, not because anyone deliberately chose it as shared vocabulary. A few hops later, the turn that coined it is gone, and the term now reads as established shorthand to whoever encounters it next, even though nothing ever defined it and it may not exist anywhere else at all. This is the same leak as human-authored undisclosed context, but the "document the reader never saw" is a vanished conversation turn instead of a doc that at least still exists somewhere.

Different axis from **writing-for-scannability** (can the reader find the structure) and **writing-voice** (does it sound human). This is about **access**: could this specific reader actually follow it, or does it quietly assume a tab they don't have open.

## When to use

- Reviewing a design doc, code-review prompt, PR/issue description, or subagent persona/prompt that's meant to stand alone
- Someone asks for a "cold read," or to check whether a doc is self-contained
- Writing something for a reader who explicitly hasn't seen the predecessor material - a follow-up proposal that shouldn't require the first one, a skill extracted out of a larger multi-stage protocol, a persona dispatched with a fresh context window
- Authoring a subagent prompt that has to work without inheriting the dispatching session's context
- Reviewing content that passed through multiple drafts, turns, or agent hops, where a term coined once earlier may have been carried forward as if it were established vocabulary

Skip when the text is genuinely written for people who already share the context - an internal status update where "the RFC" is common ground doesn't need this. The check is for text that claims (or needs) to stand alone.

## The check

1. **Name the reader, concretely.** "Someone who hasn't read the source code" is a different bar than "someone who hasn't seen this specific ticket." Pin down what they have and haven't seen before you start reading.
2. **Read it as that reader, not as the author.** For every term, acronym, or reference: would *this* reader already know what it means, or do you only find it obvious because you read the thing it came from?
3. **Flag three shapes of leak:**
   - **Undefined vocabulary** - a domain term, acronym, or internal name used without being introduced (a system's internal stage names, a field with a project-specific meaning). Includes terms a model coined ad hoc in an earlier turn or draft and that got carried forward as if established - confident usage isn't evidence the term has a real, shared definition anywhere.
   - **Borrowed structure** - the text's organization only makes sense if you already know the shape of the thing it describes (a section is legible only if you know the pipeline has five stages, because it's silently structured around them). **This is the shape a plain "assume the reader has no context" read tends to miss** - there's no single sentence to flag, just an absent one (a doc that opens at "Phase 3" and never says what the thing even is, or "As with Phase 2" with Phase 1 never described). Check explicitly: does this doc ever state what it's about before it starts arguing from that timeline/hierarchy/process?
   - **Silent reference** - "as discussed above," "per the design doc," "following the usual convention" pointing at something the reader was never handed.
4. **Calibrate: flag inaccessibility, not precision.** A well-chosen domain term used correctly isn't the problem. The same term used as if its meaning is self-evident, when the reader has no way to have learned it, is. Precise names for real things are fine - vague qualifiers, unexplained acronyms on first use, and load-bearing terms that are never defined are what to flag.
5. **Jargon-heavy isn't the same failure as context-leaking.** A doc can be dense with well-defined domain terms and still be fully self-contained. A short, plain-language doc can still assume something un-stated. The test is always "could this specific reader follow it," never "is this easy to read" (that's a different skill's job).

## Worked pattern

A doc for a "someone who hasn't read the predecessor doc" audience should open by re-establishing the minimum ground truth that reader needs - what the thing is, why it exists, the handful of names it will keep using - before it does any argument. If a doc jumps straight into "Story A vs. Story B" or "Phase 3 of the rollout" without ever saying what the subject even is, that's the leak: the author front-loaded conclusions that only land for someone who already has the setup in their head.

A persona or prompt written to be dispatched fresh (no shared context with whoever wrote it) should be auditable the same way: read it start to finish as if you're the dispatched agent with nothing but this text, and check whether any instruction only makes sense if you already know what the outer process looks like.

## Common mistakes

- **Confusing "I explained it once" with "the reader will remember."** A term defined in paragraph two and used unexplained in paragraph twenty, for a reader who may have started reading at paragraph twenty (skimmers, search hits, anyone who got linked mid-doc).
- **Treating internal shorthand as universal.** Stage names, internal flags, or team-specific abbreviations feel load-bearing to the author and are opaque to everyone else.
- **Assuming reference material is symmetric.** "See the design doc" only works if the reader has it. If they don't, restate the load-bearing fact instead of pointing at it.
- **Over-flagging real domain vocabulary.** Don't turn this into "remove all jargon." A correctly used, precise term is not the failure mode; an *undefined* one is.
- **Trusting confidence as a proxy for a shared definition.** A term used with total certainty might be one a model (or a human echoing a model's earlier output) coined once and then just kept reusing - propagation isn't agreement. If you can't point to where a term was actually defined, don't assume it has a definition somewhere; restate the underlying idea in plain language instead of citing the term.

## Mantra

Read it as the reader who wasn't in the room. If understanding a sentence secretly requires a document they don't have, that's the leak - name it, don't just note that the doc is "jargon-heavy."
