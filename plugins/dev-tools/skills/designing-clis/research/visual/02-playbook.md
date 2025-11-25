# 🧰 The Visual Design Playbook for CLIs  
### Practical Guidance for Creating Clarity, Readability, and Flow in the Terminal

Modern CLIs prove that a terminal can be expressive and even beautiful. Tools like **Claude Code**, **GitHub CLI**, **LazyGit**, **Broot**, and **Warp** all use visual techniques — color, spacing, layout, and symbols — to communicate meaning faster and make users feel confident.  
This guide shows how to apply those ideas step by step.

---

## 🎨 1. Use Color as a Visual Language

### Why It Works  
Color isn’t decoration — it’s a *preattentive cue* that directs the eye in milliseconds.  
Used intentionally, it builds hierarchy and reduces cognitive load.  

- **Green = success,** **red = failure,** **yellow = caution,** **blue = neutral/info.**  
- Keep colors consistent across your CLI so users build a mental map of what each means.  

> *Think of color as your CLI’s tone of voice — calm, confident, and consistent.*

### How to Apply It
- Use a color library like `chalk`, `rich`, or `colorama` for cross-platform reliability.  
- Always include a `--no-color` or environment fallback for accessibility.  
- Don’t overload the palette — 3–5 meaningful colors is plenty.  
- Consider brightness contrast for dark vs. light terminals.

### Example
```python
print(f"{green('✓ Success:')} All tests passed.")
print(f"{red('✗ Error:')} Missing configuration file.")
```

🧩 **Real-World Model:**  
- **GitHub CLI** shows success with a green ✓, failure with a red ✗.  
- **Warp** tints entire command blocks green or red for instant visual scanning.  
- **Broot** uses muted tones for calm, legible contrast.

---

## 🧱 2. Structure Information with Whitespace and Alignment

### Why It Works  
Whitespace is design’s simplest signal for grouping and rhythm. In terminals, line breaks and indentation *are layout*.  
As Gestalt theory tells us, things spaced closely together feel related.

### How to Apply It
- Add blank lines between logical sections of output.  
- Indent sub-items or nested structures.  
- Align text into columns or tables for comparability.  
- Use monospace padding (`ljust()`, `rjust()`) for clean edges.

### Example
```text
Issues for owner/repo

#14  Update remote URL if it changed   (bug)
#13  Support GitHub Enterprise         (wontfix)
```

🧩 **Real-World Model:**  
- **Broot**’s indented directory tree shows hierarchy clearly.  
- **Warp** separates command blocks with subtle padding or borders.  
- **LazyGit** spaces and outlines each panel so your eyes can rest.

---

## 🪟 3. Lay Out the Screen for Context and Memory

### Why It Works  
Structured layout leverages spatial memory — users remember *where* things live.  
Panels, sections, or blocks give persistent context, just like dashboards.

### How to Apply It
- Reserve screen areas for specific info (e.g., header, status, footer).  
- Keep prompts and messages in consistent positions.  
- For TUIs, use frameworks like `curses`, `blessed`, or `textual` to manage regions.  
- If you output sequentially, visually separate each command’s block.

### Example
```text
[Status]   main ↑ origin/main
[Files]    staged: 2  unstaged: 1
[Commits]  show log →
```

🧩 **Real-World Model:**  
- **LazyGit**’s multi-panel layout shows files, branches, and commits side by side.  
- **Warp** treats every command as a collapsible *block* with metadata.  
- **Claude Code**’s checklist is a *temporal layout* — tasks appear in sequence and get checked off.

---

## 🔣 4. Use Symbols as Fast Signifiers

### Why It Works  
Symbols compress meaning — a checkmark communicates success faster than the word “Success.”  
They also add personality and rhythm to otherwise uniform text.

### How to Apply It
- Use UTF-8 glyphs or emojis (`✓`, `✗`, `⚠`, `🔒`, `→`) to represent common states.  
- Always pair symbols with text for accessibility (“⚠ Warning: …”).  
- Choose a consistent set of icons and reuse them throughout.

### Example
```text
✓ Deployed successfully
⚠ Skipped 1 optional step
✗ Failed: Missing token
```

🧩 **Real-World Model:**  
- **Claude Code** uses checkboxes and locks to show safe progress steps.  
- **LazyGit** draws commit graphs with Unicode lines and circles.  
- **Broot** uses box-drawing characters (├─, └─) for directory structure.

---

## 🔁 5. Design Feedback as a Narrative

### Why It Works  
Feedback isn’t just output — it’s how your tool communicates process and progress.  
A good CLI *tells a story* of what’s happening now, what’s next, and what finished.

### How to Apply It
- Break complex actions into visible steps (“1. Fetching… 2. Installing…”).  
- Summarize at the end (“3 changes applied, 1 warning”).  
- Include next-step hints (“Run `tool view` to open result”).  
- Use spinners or step markers for long tasks.

### Example
```text
[1/3] Checking prerequisites… ✓
[2/3] Installing packages…    ✓
[3/3] Post-install setup…      ✗ Failed (see log)
```

🧩 **Real-World Model:**  
- **Claude Code**’s live checklist is a masterclass in structured feedback.  
- **GitHub CLI** appends actionable hints to errors (“Run `gh auth login` to fix”).  
- **Warp** embeds success/fail metadata in each block header.

---

## 💡 Implementation Notes & Libraries

| Goal | Helpful Libraries | Notes |
|------|--------------------|-------|
| Color & Styling | `chalk`, `rich`, `colorama` | Use semantic color constants |
| Tables & Alignment | `tabulate`, `textual`, `prettytable` | Align numerically where possible |
| Layout / Panels | `curses`, `urwid`, `textual` | Manage regions & focus states |
| Symbols & Unicode | Built-in UTF-8 | Test across platforms; provide ASCII fallback |
| Spinners / Progress | `tqdm`, `halo`, `yaspin` | Reinforce sense of progress |

---

## 🧭 6. Tie It All Back to UX Principles

| Visual Technique | UX Principle Reinforced | Why It Matters |
|------------------|------------------------|----------------|
| **Color** | Feedback & Emotion | Reinforces state and confidence |
| **Spacing & Layout** | Flow & Discoverability | Makes output scannable and calm |
| **Symbols** | Feedback & Personality | Adds fast recognition and human tone |
| **Structured Feedback** | Visibility of System Status | Builds trust and guides users |
| **Consistency** | Learnability | Reduces cognitive load |

---

## 🪞 In Short: Think Like a Designer, Speak Like a CLI

A well-designed CLI *shows* what’s happening instead of making users deduce it.  
Visual polish isn’t fluff — it’s cognitive scaffolding.  

> “The terminal can be a canvas for expressive, human-centered design.”

Start small:  
- Color your feedback.  
- Add a blank line where your output feels cramped.  
- Align a few columns.  
- Add a checkmark when something goes right.  

Those details add up to flow, clarity, and confidence — the hallmarks of great UX, even in a text-only world.

