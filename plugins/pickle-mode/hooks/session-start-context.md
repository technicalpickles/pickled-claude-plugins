<IMPORTANT>
You have pickle-mode, a layer over pstack's poteto-mode.

Invoke the `pickle-mode:pickle-mode` skill and follow its instructions when a task meets any of these:

- it touches more than one file, or changes a signature other files call
- it involves a design or architecture choice
- it is a bug whose cause is not yet known, or a performance issue

pickle-mode loads poteto-mode itself, then applies its own gates and playbook overlays. Wherever another session-start message says to invoke `pstack:poteto-mode`, invoke `pickle-mode:pickle-mode` instead.

For smaller tasks, such as a contained change to one file with an obvious test, a question, or a one-line edit, work directly and verify on the real artifact. When the intent is already specific, enter that pstack skill directly (`pstack:tdd`, `pstack:architect`, `pstack:how`, `pstack:why`, `pstack:arena`, `pstack:interrogate`).

User instructions (CLAUDE.md, AGENTS.md, direct requests) take precedence.
</IMPORTANT>
