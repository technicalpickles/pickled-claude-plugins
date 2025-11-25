## 🧭 CLI UX Heuristic Checklist

A simple 10-point guide for evaluating the UX quality of any command-line interface. Each point reflects a key design principle drawn from modern CLI tools like Claude Code, GitHub CLI, LazyGit, Broot, and Warp.

---

### 1. Familiarity & Consistency
**Question:** Does it feel intuitive from the start?
- Follows common patterns (`--help`, `--version`, `verb noun`)
- Behaves predictably across commands
- Aligns with conventions from similar tools

---

### 2. Discoverability & Guidance
**Question:** Can users easily find what’s possible?
- Provides full `--help` for each command
- Shows examples or interactive prompts when input is missing
- Suggests next steps (e.g., “Try `tool deploy` next”)

---

### 3. Feedback & Visibility of State
**Question:** Does the tool “talk back” to the user?
- Shows progress, confirmations, or results clearly
- Highlights errors or successes with icons or color
- Reflects current state when relevant (e.g., LazyGit panels)

---

### 4. Readable Output & Structure
**Question:** Is the output easy to scan and understand?
- Uses spacing, indentation, and grouping
- Avoids clutter and unnecessary noise
- Highlights key info through alignment, labels, or hierarchy

---

### 5. Flow & Efficiency
**Question:** Does it keep users in the zone?
- Minimizes repetitive or blocking input
- Supports shortcuts, aliases, or autocomplete
- Balances interactivity with scriptability

---

### 6. Error Handling & Forgiveness
**Question:** Are errors clear, kind, and recoverable?
- Explains what went wrong and how to fix it
- Avoids blame; suggests solutions
- Allows safe exploration (undo, confirmation prompts)

---

### 7. Accessibility & Inclusivity
**Question:** Can everyone use it comfortably?
- Doesn’t rely solely on color
- Offers `--no-color` or plain output modes
- Uses readable symbols, UTF-8 support, and clear language

---

### 8. Responsiveness & Performance
**Question:** Does it feel fast and alive?
- Provides instant or progressive feedback
- Handles long tasks gracefully with spinners or logs
- Keeps latency low and flow intact

---

### 9. Tone & Personality
**Question:** Does it communicate with warmth and clarity?
- Uses human-friendly language, not jargon
- Adds subtle delight (emojis, humor) where appropriate
- Matches tone to its audience (developer, sysadmin, etc.)

---

### 10. Safety & Trust
**Question:** Does it feel reliable and transparent?
- Asks before destructive actions
- Makes automation understandable (visible plans, confirmations)
- Builds confidence through predictability and honesty

---

### 🧩 Using the Checklist
Score each item from **1 (poor)** to **5 (excellent)** to evaluate a CLI’s UX quality.  
A consistently high-scoring tool will feel modern, confident, and delightful to use.

