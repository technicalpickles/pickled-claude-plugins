## 🎨 CLI Visual Design Research – Master Prompt

### **Research Goal**
Explore how modern command-line interfaces (CLIs) — such as Claude Code, GitHub CLI (`gh`), `lazygit`, `broot`, and `warp` — use **visual language** to create interfaces that are not only functional but also *beautiful* and *emotionally engaging*.

The goal is to uncover **visual design principles** that make terminal interfaces expressive and readable: how they use color, spacing, alignment, symbols, and structure to enhance usability, clarity, and delight. Whenever possible, tie these insights back to the broader **CLI UX principles** established in the earlier research — feedback, flow, discoverability, and emotional tone.

---

### 🧠 **Phase 1: The Why — Understanding Visual Communication in the Terminal**
- Identify the visual techniques used in modern CLIs:
  - Color as meaning (status, hierarchy, mood)
  - UTF-8 and symbol usage (✓ ✗ ⚠️ arrows, lines, checkboxes)
  - Whitespace and alignment as layout
  - Grouping, contrast, and emphasis
- Explain **why** each technique works — draw on visual design and cognitive principles (e.g., preattentive processing, visual hierarchy, gestalt grouping).
- Include real-world examples:
  - Claude Code’s live checklists and task indicators
  - GitHub CLI’s consistent use of color and concise structure
  - Broot’s calm, indented directory view
  - Warp’s block-based terminal layout
  - LazyGit’s multi-panel live feedback

**Expected Output:**  
A readable analysis of visual techniques that make CLIs feel designed rather than purely functional. Use a friendly, design-blog tone with visual examples and analogies.

---

### ⚙️ **Phase 2: The How — Applying Visual Design in the Terminal**
- Translate these insights into **framework-agnostic design practices** developers can apply when building CLIs.
- Provide concrete guidance for:
  - Color use and theming (semantics, accessibility, emotional tone)
  - Layout via spacing, indentation, and grouping
  - UTF-8 and ASCII as micro-interactions (checkmarks, borders, arrows)
  - Readability and density management (chunking, contrast)
- Tie back to the original UX principles when relevant:
  - “Feedback through color reinforces confidence.”
  - “Whitespace supports flow and rhythm.”

**Expected Output:**  
A builder’s guide for creating visually expressive CLIs — practical, concise, and visually grounded.

---

### 📚 **Phase 3: The Reading & Reference List**
- Curate an **annotated reading list** on visual design and terminal aesthetics, including:
  - General UX design and visual communication theory (e.g., Tufte, Lidwell, Norman)
  - Articles on terminal color theory, Unicode typography, and TUI frameworks
  - Developer-facing resources (e.g., libraries like `rich`, `chalk`, `blessed`, or `curses`)
- For each, write 1–2 sentences explaining its relevance — connect it back to CLI design.

**Expected Output:**  
An approachable reading list bridging design thinking and terminal craft.

---

### 🧩 **Deliverables Summary**
- **Visual Design Principles for CLIs** → key techniques and examples  
- **Practical Builder’s Guide** → how to apply visual polish and clarity  
- **Annotated Reading List** → resources on design, typography, and terminal aesthetics  

---

### ✍️ **Tone & Style Notes for ChatGPT**
- Prioritize **clarity, warmth, and visual thinking** over formality.
- Use analogies (“Color in the CLI is like tone of voice in conversation”).
- Reference real tools naturally and descriptively.
- Write like a designer explaining their process to engineers.
- Format with short sections, clear subheads, and bullet lists.

---

### 🚀 **Optional Extensions (for Future Iterations)**
- Visual examples gallery with annotated screenshots.
- CLI color and typography checklist.
- Comparative study: *Minimalism vs Expressiveness* in CLI visual design.
- Cross-medium reflection: what GUI design can learn from terminal aesthetics.

---

### 🧭 **Workflow Checklist: Running This Research in ChatGPT**

**1. Create a Master Thread**  
Start a new conversation titled *“CLI Visual Design – Master Prompt”* and paste this document. Use it as a reference, not a working session.

**2. Phase 1 – Visual Principles (The Why)**  
Prompt:
```
Let’s start with Phase 1 of the CLI Visual Design research. Identify and explain the key visual techniques that modern CLIs use to create clarity and beauty — color, spacing, layout, and symbols. Include concrete examples from Claude Code, GitHub CLI, lazygit, broot, and warp. Keep it readable and design-forward.
```

**3. Phase 2 – Practical Guidance (The How)**  
Prompt:
```
Using the findings from Phase 1, write a practical, framework-agnostic guide for developers to apply visual design principles in terminal interfaces. Include clear examples, small implementation notes, and connections to UX principles.
```

**4. Phase 3 – Reading List (The Deep Dive)**  
Prompt:
```
Curate a short, annotated reading list of resources on visual design, typography, and terminal aesthetics. Explain why each source is relevant to CLI visual design.
```

**5. Optional – Future Work**  
Use new threads for:
- Comparative analysis between tools (e.g., Claude Code vs Warp)
- Creating a CLI visual design checklist
- Writing a blog-style synthesis or manifesto

Each phase should live in its own thread for clarity and focus. Keep outputs human-readable, image-friendly, and conversational.

