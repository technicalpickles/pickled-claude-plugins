---
name: automic-vault-credentials
description: Use when a command mentions `av`, Automic Vault or automic-vault, when a task needs a credential (GitHub token, API key, SSH key, GPG signing) on a Mac that has Automic Vault installed, or when gh, git push, git commit signing or an `av` command fails with an approval, sandbox, "agent refused operation" or -25308 error
---

# Using Automic Vault (`av`)

## Overview

`av` is the CLI for Automic Vault, a macOS app that holds credentials in the Keychain and makes a human approve each use. It is the credential manager here, not 1Password, not `gh auth token`, not a `.env` file. You never see secret values and shouldn't try to. You ask, a person approves in the app or on their phone, and the command runs.

## Quick Reference

| Need | Do |
|---|---|
| See what's available | `av list` (names only) |
| Run a command that needs a secret | `av inject +NAME -- cmd args` |
| Secret not saved yet | Ask the user to run `av save NAME` (or `av save --project-directory=. NAME`). You can't type it for them |
| Tool already hardened (`gh`, `aws`, `docker`, `ssh`, git signing) | Run the tool normally. Approval happens behind it |
| Why was something denied or slow | `av history --json --since 1h --no-pager` |
| Is hardening intact | `av doctor <tool>` |
| Does `av` cover tool X, or how do I do Y | `av hardeners --json` lists supported tools. Then `av help` and https://www.automicvault.com/docs/ (start at "Choosing a Mechanism"). Say "not sure yet" before "can't" |

## Errors

| You see | Cause | Do |
|---|---|---|
| `approval service is blocked by this process's sandbox` | Your Bash sandbox can't reach the approval service | Rerun that one command outside the sandbox |
| `gh` says token invalid or sends an empty auth header, but works in the user's terminal | Same sandbox block (older `gh` Isotope hides the message) | Rerun that one `gh` call outside the sandbox |
| `Approval presentation interrupted` in `av history` | Prompt couldn't be shown: sandbox, or app not running | Rerun outside the sandbox. If it persists, ask the user to run `av open` |
| `Secrets are unavailable from Keychain ... (-25308)` | Mac is locked | Ask the user to unlock and retry, or enable Available While Locked for that credential. Never skip signing |
| `agent refused operation` (ssh or signing) | Policy denied, prompt unanswered, or locked | Read `av history` for the request and its decision, then report that |

`human approval required` followed by `approved` is normal. Wait, don't retry in a loop.

## Rules

- Take a secret by name through `av inject`. Don't print, log, echo or export values to debug.
- Don't reach around it: `gh auth token`, `security find-generic-password`, `op read`, `GITHUB_TOKEN=$(...)`.
- Don't weaken the setup to get unblocked: `--no-gpg-sign`, other SSH keys, credential-helper edits, `av unharden`.
- Agents usually start at Read Only on hardened tools. A write that needs approval is a question for the user, not a bug.
- Report the real error and what you checked. Don't pick "policy" or "locked" without `av history`.
