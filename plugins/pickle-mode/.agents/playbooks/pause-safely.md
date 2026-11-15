---
extends: pause-safely
when: Pausing in-flight work in a session that has the agent-meta plugin.
---

# Pause safely, through agent-meta:park

Handoffs go where the project already keeps them, so they are committed, searchable, and visible to tools that read handoffs. pstack's `resume.mjs` store under the Git directory is never committed and does not survive a reclone, so it is skipped.

- **In** "Make the work durable." Follow the repository's commit rules first. In a working tree other sessions share, scope the commit to the paths you touched (`git commit -- <paths>`), never a bare commit.
- **Replace** "Write the resume note off-context." Invoke `agent-meta:park` through the Skill tool in continuation mode, or idle-checkpoint mode when an automated trigger caused the pause. Park resolves the location and template. Link an existing show-me-your-work trail from the handoff instead of duplicating it.
- **Replace** "Publish the checkpoint through `resume.mjs`" Save requested artifacts beside the handoff, or reuse the existing artifact, and link each from the handoff. Then read the handoff back and confirm every requested artifact is reachable from it with its exact wording, completeness, and order. Skip `resume.mjs` entirely.
