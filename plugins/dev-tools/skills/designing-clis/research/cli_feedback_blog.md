# How Modern CLI Tools Nail Feedback — and What We Can Learn From Them

The command line used to be a place of mystery and minimalism — you typed something, hit Enter, and hoped for the best.  

But the new generation of CLI tools has flipped that experience. Tools like **Claude Code**, **GitHub CLI**, **LazyGit**, **Broot**, and **Warp** have made the terminal *feel alive* again. They give feedback that’s immediate, visual, and — dare I say — pleasant.

Let’s take a quick tour through how each one “talks back” to its users, and what their approaches reveal about great developer UX.

---

## 🧩 Claude Code: The AI Assistant That Checks Off Its Own To-Do List

If most CLIs are command responders, **Claude Code** is more like a co-worker narrating what it’s doing.  
When you ask it to, say, clean up your codebase or fix a bug, it doesn’t just run silently in the background. It builds a visible **checklist** of subtasks — like “Analyze repo,” “Identify issues,” “Apply fixes” — and checks them off one by one as it works.

✅ **Visual Progress:** The checklist updates live, so you see exactly what it’s working on.  
🔒 **Safety by Design:** Before doing anything destructive, Claude asks permission (“Proceed with file edits?”).  
💬 **Conversational Feedback:** It explains what’s happening in plain English — no need to decipher cryptic logs.

It’s feedback as storytelling. You’re watching a process unfold in real time, and that makes automation *feel* understandable — and trustworthy.

*Suggested visual: screenshot of Claude’s terminal plan with tasks getting checked off.*

---

## 🤡 GitHub CLI (`gh`): Textbook Feedback Done Right

GitHub’s CLI is all about **minimalism and clarity**. No flash, just clean communication.

- Successes show up with a **green checkmark** (`✓ Pull request created at https://...`).
- Failures use a red `X` or a short, human-readable error message.
- Long operations (like `gh run watch`) display simple spinners.
- Interactive commands like `gh issue create` use Q&A-style prompts when flags aren’t provided.

The result? You always know what happened, but the tool never hogs your attention. It’s like a helpful coworker who gives concise status updates and moves on.

**UX takeaway:** Feedback doesn’t need to be fancy — just clear, consistent, and visible.

*Suggested visual: `gh pr status` showing ✓/× icons next to check results.*

---

## 🖥️ LazyGit: A Living, Breathing Git Dashboard

LazyGit transforms git commands into a **real-time interface**. Instead of typing `git status`, `git diff`, or `git log` repeatedly, you get all of it at once — in panels that update as you act.

You stage a file? It jumps from *Unstaged* to *Staged*.  
Commit something? The new commit appears instantly in the history panel.  
Try to do something risky? A confirmation dialog pops up asking if you’re sure.

Errors don’t scroll by unnoticed — they appear as modal dialogs you have to acknowledge, making them impossible to miss.  

It’s like using a mini Git GUI — only you never leave your terminal.

**UX takeaway:** Persistent visibility beats constant repetition. Show users what’s happening without making them ask.

*Suggested visual: LazyGit panel layout showing Status, Files, Branches, and Stashes.*

---

## 🌲 Broot: Calm, Context-Aware File Browsing

If LazyGit turns Git into a dashboard, **Broot** does the same for your filesystem.

Open it, and you’re instantly looking at a live, interactive tree view of your directories. Start typing, and it **filters in real time** — shrinking the view to only what matches your search.

Broot’s feedback is subtle but elegant:
- It shows “and 51 unlisted” when it truncates output, hinting there’s more below.  
- When you delete or move something, the change appears instantly in the tree.  
- Small status messages (“Error: Permission denied”) appear at the bottom — visible but never intrusive.

No beeps, no walls of text — just a steady stream of quiet confirmation. It’s feedback by *presence*, not by interruption.

*Suggested visual: Broot’s tree view with a live filter active.*

---

## 🧱 Warp: The Terminal That Treats Output Like LEGO Blocks

**Warp** reimagines the terminal interface itself. Every command you run becomes a separate **block**, complete with its own output, metadata, and controls.

Each block is:
- **Visually distinct** — collapsible, scrollable, and shareable.  
- **Annotated** — success/failure icons, timestamps, even exit codes.  
- **Interactive** — you can click paths, copy output, or rerun commands right from the UI.

The separation of commands into blocks means feedback never gets lost in scrolling chaos. You can instantly tell what succeeded, what failed, and what’s next. It feels organized — almost like an IDE for your shell.

**UX takeaway:** Sometimes the best feedback isn’t more text — it’s better structure.

*Suggested visual: Warp’s block interface, showing separate command blocks in green/red.*

---

## 🧠 The Bigger Picture: Five Different Voices, One Shared Goal

Despite wildly different designs, these tools share the same principle: **make the user feel in control**.

| Tool | Feedback Style | Key Strength |
|------|----------------|---------------|
| **Claude Code** | Conversational, structured checklist | Builds trust through transparency |
| **GitHub CLI** | Textual and symbolic | Clear, minimal, script-friendly |
| **LazyGit** | Visual, interactive panels | Continuous feedback, no guesswork |
| **Broot** | Contextual, adaptive | Calm, non-intrusive visibility |
| **Warp** | Visual block UI | Organized, explorable history |

Each one gives feedback that fits its audience — from AI-powered automation to power-user productivity. Together, they show that good CLI UX isn’t about adding flair; it’s about **closing the loop**. Every command should end with, “Yes, I know what just happened.”

---

**Bottom line:**  
Whether it’s a green checkmark, a changing panel, or a friendly “All done!”, great CLI feedback replaces uncertainty with confidence.  

And when a developer feels confident, they stay in flow — which is exactly where the best tools want them to be.

