# Designing Rich, Discoverable, and User-Friendly CLIs

Modern command-line interfaces (CLIs) are no longer just barebones text prompts; they can be smooth, intuitive, and even *delightful* to use. A great CLI feels like a friendly conversation with your computer rather than a cryptic monologue. This practical guide explores key principles for building CLIs that are rich in feedback, easy to discover, and a joy for users. It’s framework-agnostic and packed with examples, quotes, and a cheat sheet to help you design your own tools.

---

## 1. Embrace Familiarity and Consistency 🤝

**What it means:** Use conventions users already know. Follow standard flags like `--help`, `--version`, and use common patterns (e.g. `tool verb noun`).

**Tips:**
- Use long and short flag versions (`-v` and `--verbose`).
- Mirror known tools (e.g. GitHub CLI mimics Git).
- Avoid reinventing the wheel just to be clever.

**Example:** GitHub CLI (`gh`) adopts Git’s syntax and naming, so users feel at home.

> **Memorable:** *"Don’t make me think."* – Steve Krug

---

## 2. Make It Discoverable – Guide Your Users 🔍

**What it means:** Help users discover commands, options, and next steps through help text, examples, and prompts.

**Tips:**
- Provide `--help` for all commands/subcommands.
- Include usage examples.
- Prompt for inputs only when needed.
- Suggest next steps in CLI output.
- Offer shell autocompletion.

**Example:** `gh auth login` prompts interactively if run without flags.

> **Memorable:** *Like a good waiter, your CLI should anticipate needs but not interrupt.*

---

## 3. Always Provide Feedback – Don’t Keep Users in the Dark 📣

**What it means:** Show users what’s happening at all times. Provide progress, results, and confirmations.

**Tips:**
- Use spinners or progress bars for long tasks.
- Echo actions taken (“Item deleted”).
- Show state (e.g. branch name in lazygit).
- Use color and labels for status.

**Example:** Docker CLI shows detailed layer-by-layer download progress.

> **Memorable:** *A silent CLI is like a meeting with your mic muted — no one knows what’s going on.*

---

## 4. Structure Output for Readability 🗂️

**What it means:** Present information in a clean, skimmable format.

**Tips:**
- Use line breaks, indentation, and tables.
- Highlight important parts with labels and color.
- Avoid walls of text; chunk info into digestible bits.

**Example:** `broot` organizes directory listings visually and includes a live help bar.

> **Memorable:** *Good CLI output is like a well-organized workshop — everything in its place.*

---

## 5. Be Forgiving – Handle Errors Gracefully 🙏

**What it means:** Guide users through problems with clear, helpful error messages.

**Tips:**
- Write plain-language errors.
- Suggest fixes.
- Avoid blaming users.
- Catch typos and offer corrections.
- Include links or references to docs.

**Example:** Git suggests `git status` if you mistype `git statsu`.

> **Memorable:** *“Design for error.”* – Don Norman

---

## 6. Keep It Responsive and Fast – Maintain Flow ⏱️

**What it means:** Support fluid interaction. Keep performance snappy and avoid unnecessary interruptions.

**Tips:**
- Show signs of life during long tasks.
- Make scripts and chaining work (proper exit codes).
- Avoid forced interaction unless required.
- Allow canceling or aborting with Ctrl+C.

**Example:** `gh issue create` can run interactively or fully scripted with flags.

> **Memorable:** *“Easy things should be easy, and hard things possible.”* – Larry Wall

---

## 7. Be Inclusive – Accessible and Polished for All 🏳️‍🌈

**What it means:** Make your CLI usable by everyone, everywhere.

**Tips:**
- Don’t rely on color alone.
- Offer `--no-color` mode.
- Support UTF-8 gracefully.
- Use polite language.
- Add delightful touches (emojis, ASCII art) only where appropriate.

**Example:** Yarn and Cargo include emojis and friendly success messages.

> **Memorable:** *“Accessibility makes some people’s lives better, and everyone’s experience smoother.”*

---

## 📁 Appendix: CLI UX Design Checklist & Cheat Sheet

### ✅ CLI UX Design Checklist

| Area                     | Questions to Ask                                                               |
|--------------------------|----------------------------------------------------------------------------------|
| Familiarity              | Are standard flags and command structures used? |
| Discoverability          | Is `--help` complete? Are examples shown? |
| Feedback                 | Are results and progress clearly shown? |
| Interaction              | Are prompts used only when needed? Defaults provided? |
| Output Structure         | Is info readable, structured, and skimmable? |
| Error Handling           | Are errors helpful, polite, and fix-oriented? |
| Accessibility            | Is color optional? Output usable in scripts? |
| Power User Support       | Scripting, flags, and automation supported? |

### 🧠 UX Principles Cheat Sheet

| Principle               | What It Means                                  | How to Apply                                         |
|------------------------|--------------------------------------------------|------------------------------------------------------|
| Familiarity Wins       | Use known patterns and names                    | Stick to CLI norms (flags, structure, verbs, nouns)  |
| Show, Don’t Hide       | Make features easy to find                      | Help text, completions, examples, next-step hints    |
| Talk Back              | Confirm actions and show progress               | Spinners, logs, success/error messages               |
| Prompt When Needed     | Be interactive when helpful, not always         | Prompt only if info isn’t given; allow skipping      |
| Structure for Skimming | Make output legible and easy to scan            | Tables, spacing, short paragraphs, labels            |
| Friendly Failures      | Help users recover, don’t blame                 | Plain messages, suggestions, error codes             |
| Respect the Flow       | Don’t interrupt or slow the user down           | Support automation, quick input, responsive commands |
| Be Inclusive           | Consider accessibility and polish               | Avoid color-only cues, graceful fallbacks, UTF-8     |

---

**Final Thought:** A CLI is still a user interface — it deserves just as much care as a GUI. Build something thoughtful, responsive, and kind, and your users will thank you every time they open their terminal.

