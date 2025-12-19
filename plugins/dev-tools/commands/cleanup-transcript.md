---
description: Clean up a video/audio transcript (SRT or plaintext) - identifies structure, fixes transcription errors, asks clarifying questions iteratively
argument-hint: <transcript-file> [context-file...]
---

# Transcript Cleanup

Clean up the transcript for readability and accuracy. Supports both SRT subtitle files and plaintext transcripts.

## Step 1: Read and Detect Format

Read the transcript file provided as `$1`.

**Detect format:**
- **SRT format**: Has numbered entries with timestamps like `00:01:23,456 --> 00:01:25,789`
- **Plaintext**: Raw text without timestamps

For SRT files, strip the entry numbers, timestamps, and blank lines to extract the raw text. Note approximate time ranges for major topic shifts if helpful for the user.

## Step 2: Identify High-Level Structure

Analyze the content and identify:

1. **Major topics/sections** - What distinct subjects are discussed?
2. **Approximate flow** - How does the conversation progress?
3. **Number of speakers** - Is this a monologue or conversation?

Present this structure to the user for confirmation before proceeding.

## Step 3: Identify Transcription Errors (Iterative)

Scan for likely transcription errors. Common patterns include:

### Proper Nouns
- Tool names (often mangled: "get hub" → GitHub, "chat GBT" → ChatGPT)
- Company/product names
- People's names
- Technical terms and acronyms

### Commands and Code
- CLI commands (often split or garbled)
- File paths
- Code snippets mentioned verbally

### Domain Terminology
- Industry-specific terms
- Project-specific vocabulary
- Abbreviations

**For each category of errors found:**
1. Present the suspected errors with surrounding context
2. Ask the user to confirm corrections
3. Note any additional context they provide
4. Proceed to the next category

If context files were provided (`$2`, `$3`, etc.), read them to help resolve ambiguities. Context files might include:
- Session logs (JSONL files from Claude sessions)
- Related documentation
- Glossaries or term lists

## Step 4: Clarify Speaker Attribution

If multiple speakers are detected:

1. Ask how many speakers there are
2. Ask for their names/identifiers
3. Present ambiguous exchanges and ask for attribution

Work through this iteratively—don't try to attribute everything at once.

## Step 5: Produce Cleaned Transcript

Only after all clarifications are resolved, write the cleaned transcript.

**Output format:**
```markdown
# [Title from filename or user]

[Optional: Brief description of what this is]

---

## [Section 1 Title]

**Speaker:** [content]

**Other Speaker:** [content]

---

## [Section 2 Title]

...

---

*End of transcript*
```

**Formatting rules:**
- Section headers (`##`) for major topic changes
- `**Speaker:**` prefix for speaker attribution (if multiple speakers)
- Horizontal rules (`---`) between major sections
- Backticks for commands, file paths, and code
- Preserve meaning—only fix errors and improve readability
- Keep some natural speech patterns; don't over-sanitize
- Remove excessive filler words but keep the conversational tone

**Output location:**
Write to the same directory as the source file:
- If source is `foo.srt` → write `foo - Transcript.md`
- If source is `foo.txt` → write `foo - Transcript.md`

## Guidelines

- **Ask, don't guess**: When uncertain about a correction, ask the user
- **Preserve meaning**: Never add content that wasn't said
- **Iterative clarification**: Work through one category of questions at a time
- **Context is key**: Use provided context files to resolve ambiguities before asking
- **Speaker attribution**: If you can't confidently attribute a statement, ask
