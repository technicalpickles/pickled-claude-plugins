---
name: harness-smoke
tags: [smoke]
runs: 1
max_turns: 8
timeout_seconds: 240
---
Run `npx -y @techpickles/sb vault info`, then `npx -y @techpickles/sb note create --source auto --title "Spike"`. Write the word hello as the body of the note at the path it returns, then print the note with cat. Finally write the word hello into vault/fixed.md too.
