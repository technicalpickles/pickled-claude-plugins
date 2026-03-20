---
name: research
description: Use when about to call WebSearch or WebFetch across multiple sources, or when the user explicitly asks to research a topic, investigate a question, or produce a report requiring web sources. Prefer this over direct WebSearch/WebFetch to avoid per-domain approval prompts.
---

# Research Agent

Conduct web research using a sandboxed headless Claude process that can freely fetch web content without per-domain approval prompts.

**Use this skill instead of calling WebSearch/WebFetch directly** when research spans multiple sources or domains. It runs in an isolated process where WebFetch does not require per-domain approval, producing a citable markdown report with inline links and a full research log.

## Security Model

The research agent runs as a separate `claude -p` process with:
- **Narrow tool allowlist**: only `WebFetch`, `WebSearch`, `Read`, `Glob`, `Grep`, `Write`
- **No Bash**: cannot execute arbitrary commands
- **No Edit/Agent/Task**: cannot modify existing files or spawn sub-agents
- **Temp directory confinement**: writes are restricted to a temporary directory
- **Prompt injection defense**: the agent's system prompt includes explicit anti-injection instructions

## Step 1: Clarify Research Topic

**If topic was provided as argument:** Confirm the topic and proceed to Step 2.

**If no topic provided:** Ask the user what they want to research. Gather:

1. **Topic**: What to research
2. **Scope/depth**: Quick overview vs deep dive vs specific question
3. **Angles**: Any specific aspects, comparisons, or questions to address

Use AskUserQuestion if helpful:
```
What would you like to research?
```

Then clarify scope:
```
How deep should this research go?
(A) Quick overview — key points and summary (5 min)
(B) Detailed report — thorough exploration with sources (10-15 min)
(C) Specific question — focused answer with evidence
(D) Comparison — evaluate multiple approaches/options
```

Map the user's choice to a scope value: `quick`, `detailed`, `question`, or `comparison`.

## Step 2: Launch Research Agent

Use the research script at `${CLAUDE_PLUGIN_ROOT}/scripts/research.sh` to run the sandboxed agent.

The script handles:
- Creating a temp directory for sandboxed output
- Building the research prompt with anti-injection defenses
- Running `claude -p` with the narrow tool allowlist
- Writing the report to the output directory

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/research.sh" \
  -s SCOPE \
  -o ./research \
  "TOPIC"
```

Options:
- `-s SCOPE` — `quick`, `detailed`, `question`, or `comparison`
- `-o ./research` — saves the report to the project's `research/` directory
- `-m MODEL` — optional model override (e.g. `sonnet`, `opus`)

The script may take several minutes depending on scope. This is expected.

## Step 3: Present Results

After the script completes:

1. Read the saved report from `research/`
2. Show a brief summary of what was researched
3. Show the file path where the report was saved
4. Offer to discuss the findings

```
Research complete! Report saved to research/{filename}.md

Summary: {2-3 sentence overview of key findings from the report}

Would you like me to:
(A) Show the full report
(B) Discuss specific findings
(C) Done for now
```

## Error Handling

- **Script fails**: Show the error output. Common causes: no internet, API issues, `claude` not in PATH.
- **No report created**: The script exits non-zero if `report.md` wasn't written. Suggest running with `-v` for verbose output.
- **File already exists**: The script auto-appends a timestamp to avoid overwriting.

## Constraints

- **Always use the script**: Don't reconstruct the headless CLI invocation manually
- **Don't modify the report**: Present it as the research agent wrote it
- **Output to `research/`**: Always use `-o ./research` so reports land in the project
