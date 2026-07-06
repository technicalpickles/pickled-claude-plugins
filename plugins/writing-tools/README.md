# writing-tools Plugin

Skills for structuring and formatting prose so it reads well, plus a send-time hook that keeps em-dashes out of content you author.

## Installation

Requires the [pickled-claude-plugins marketplace](../../README.md#installation). Then:

```bash
/plugin install writing-tools@pickled-claude-plugins
```

The em-dash hook additionally needs [`uv`](https://docs.astral.sh/uv/) on your PATH (same runtime the `tool-routing` and `buildkite` hooks use). Without `uv` the hook simply doesn't run; the skills are unaffected.

## Em-dash outbound enforcement (hook)

A `PreToolUse` hook that blocks an em-dash (—) when it appears in a send-time call for a tool you've opted in: Slack sends, `gh pr`/`gh issue` authoring, and the like. It never touches `Write`/`Edit` or arbitrary Bash, so docs, code, and your own `grep "—"` / `perl 's/—/:/'` cleanup commands are never blocked.

**Inert by default.** The shipped config (`hooks/emdash-outbound.yaml`) has empty lists, so a fresh install blocks nothing. Opt in by creating your own config at one of (first found wins):

1. `$EMDASH_OUTBOUND_CONFIG` (explicit override)
2. `${CLAUDE_PROJECT_DIR}/.claude/emdash-outbound.yaml` (per project)
3. `$HOME/.claude/emdash-outbound.yaml` (personal, all projects)

```yaml
# ~/.claude/emdash-outbound.yaml
mcpTools:
  - mcp__slack__slack_send_message   # your Slack MCP server name will differ
bashCommands:
  - gh pr create
  - gh pr edit
  - gh pr comment
  - gh issue comment
```

Bash commands are matched at the start of the command or after a shell separator (`;` `&&` `||` `|`). For gated `gh` commands, the hook also resolves `--body-file`/`-F` and scans that file. See `hooks/emdash-outbound.yaml` for the annotated default.

Blog and draft-time prose stay with the `writing-voice` skill (which already covers em-dashes) rather than the hook, since there's no clean "publish" call to gate.

## Skills

### writing-for-scannability

Use when structuring prose so readers can skim it - drafting or restructuring READMEs, docs, PR or issue bodies, design docs, or any long-form text where a wall of prose hides the structure. Covers when to surface a buried list, how to keep list items parallel, how to front-load the load-bearing word for the F-pattern, and a sliding scale for how hard to lean on formatting per medium. Composes with prose-clarity and voice skills rather than replacing them.

The full background, history, and worked examples live in the skill's [reference docs](skills/writing-for-scannability/references/).

## Resources

The skill is built on the scannable-writing research tradition. The sources it draws from:

**How people read on screens**

- Nielsen, [How Users Read on the Web](https://www.nngroup.com/articles/how-users-read-on-the-web/) (1997) - the founding finding that most readers scan rather than read.
- Morkes & Nielsen, [Concise, SCANNABLE, and Objective](https://www.nngroup.com/articles/concise-scannable-and-objective-how-to-write-for-the-web/) (1997) - the Sun Microsystems usability study.
- Nielsen, [F-Shaped Pattern of Reading](https://www.nngroup.com/articles/f-shaped-pattern-reading-web-content/) (2006) - the eye-tracking research behind front-loading.
- Nielsen, [Website Reading: It (Sometimes) Does Happen](https://www.nngroup.com/articles/website-reading/) (2013) - the corrective on when reading does happen.
- Krug, [Don't Make Me Think](https://en.wikipedia.org/wiki/Don't_Make_Me_Think) (2014 ed.) - satisficing and designing for scanning.

**When to bullet, when not to**

- Google, [Lists and Tables](https://developers.google.com/tech-writing/one/lists-and-tables) - the clearest practical rules, including parallelism.
- Hurley, [Bullet point lists versus paragraphs](https://www.writingclearscience.com.au/bullet-point-lists-versus-paragraphs/) - the statement-plus-examples heuristic.
- Seneca College, [Lists chapter](https://pressbooks.senecacollege.ca/technicalwriting/chapter/lists/) - the five list types.
- UXmatters, [Scannability: Principle and Practice](https://www.uxmatters.com/mt/archives/2015/06/scannability-principle-and-practice.php) - when scannability is not the right move.
- Gearing, [Bullet Points vs Prose](https://lukegearing.blot.im/bullet-points-vs-prose) - a counterpoint on when bullets lose meaning.

**Parallel structure**

- Perspectives on Medical Education, [The Power of Parallel Structure](https://pmc.ncbi.nlm.nih.gov/articles/PMC4673060/) - the cleanest summary of the grammar move.
- Rabbit with a Red Pen, [Writing Parallel Structure](https://www.rabbitwitharedpen.com/blog/parallel-structure) - auditory heuristics for catching breaks.

**The inverted pyramid (history)**

- Wikipedia, [Inverted pyramid (journalism)](https://en.wikipedia.org/wiki/Inverted_pyramid_(journalism)) - the structural ancestor.
- Scanlan, [Birth of the Inverted Pyramid](https://www.poynter.org/reporting-editing/2003/birth-of-the-inverted-pyramid-a-child-of-technology-commerce-and-history/) (Poynter) - the telegraph-era origin story.
