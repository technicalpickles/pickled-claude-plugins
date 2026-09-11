# claude.ai Skill Porting Guide

claude.ai Skills (Settings → Capabilities → Skills in the Claude chat app) are a
different product from this repo's Claude Code plugins. They're chat-only: no
filesystem, CLI, or MCP access, uploaded as a zip by hand instead of installed via
`/plugin install`. Some of this repo's Claude Code skills are worth porting there —
this doc covers where they live, how to build them, and what to watch for when
adapting one.

## Where they live

Each port lives inside the Claude Code plugin it's derived from, as a sibling to that
plugin's `skills/` and `hooks/` directories:

```
plugins/{plugin-name}/claude-ai-skills/{skill-name}/
  SKILL.md
  references/        # optional, same shape as Claude Code skills
```

A claude-ai-skills port is **not** a Claude Code plugin skill: it has no
`.claude-plugin/plugin.json` entry, isn't listed in `.claude-plugin/marketplace.json`,
and doesn't appear in the generated README plugin table. The only reason it's nested
inside `plugins/{name}/` is organizational — it sits next to the conventions it
mirrors, and a commit touching it naturally scopes to that plugin
(`feat(second-brain): add vault-capture claude.ai skill`), satisfying this repo's
existing commit-scope rule (see root `CLAUDE.md`'s Versioning section) with no
special-casing.

A plugin's `claude-ai-skills/` directory can hold more than one skill.

## Building

One shared script handles every plugin:

```bash
./scripts/build-claude-ai-skill.sh <plugin>                # build every skill under that plugin
./scripts/build-claude-ai-skill.sh <plugin> <skill-name>   # build just one
```

Output lands at `plugins/<plugin>/claude-ai-skills/dist/<skill-name>.zip`, gitignored.
`SKILL.md` sits at the zip root — that's the shape claude.ai's uploader expects.

## Uploading

claude.ai → Settings → Capabilities → Skills → upload the zip. Re-uploading the same
skill name replaces the previous version. There's no CLI for this; it's a manual step
after building.

## Porting checklist

When adapting a Claude Code skill into a claude.ai skill, start here:

**Does the source skill invoke tools, a CLI, MCP, or the filesystem?**

- **No** → straight port. The instructions carry over close to as-is. Review is
  lightweight — check the description still triggers correctly in a chat-only context,
  and that nothing in the body assumes Claude Code-specific mechanics (skill file
  paths, other installed plugins, etc.).
- **Yes** → adapted port. Do a capability-gap pass:
  1. Enumerate every capability the source skill relies on that claude.ai chat doesn't
     have (filesystem search, a CLI's dedup/validation logic, MCP calls, other
     installed skills it composes with).
  2. For each one, decide: disclose the gap plainly (tell the user this step can't be
     done and why), or find a chat-safe equivalent. Never fake it — don't have the
     skill claim to have deduplicated, searched, or validated something it structurally
     cannot.
  3. Check whether any reference data needs to be baked into `references/` because the
     source skill previously read it live from somewhere claude.ai can't reach (a
     vault's own `CLAUDE.md`, a database, another plugin's config). `vault-capture`'s
     `references/jd-map.md` is an example: it condenses the `pickled-knowledge` vault's
     Johnny Decimal layout, which the source `second-brain:capture` skill reads live
     from the vault's `CLAUDE.md` but a claude.ai skill can't.

**Either way**, the port goes through the full `superpowers:writing-skills` TDD process
(baseline subagent runs, rationalization tables) before being considered done. The
checklist above changes *what* needs adapting — it doesn't change whether the result
gets tested like any other skill.
