# automic-vault Plugin

Teaches agents what `av` is and how to work with [Automic Vault](https://github.com/automic-vault/automic-vault) without reaching around it.

## Skills

### automic-vault-credentials

Use when a command mentions `av` or Automic Vault, a task needs a credential on a Mac that has it installed, or `gh`, `git push`, commit signing or an `av` command fails with an approval, sandbox, "agent refused operation" or `-25308` error.

**Covers:**
- What `av` is, and that it replaces `gh auth token`, `op read` and `.env` files as the way to get a credential
- Injecting secrets by name (`av inject`), checking names (`av list`), and handing `av save` to the user
- Finding presentation settings (`av settings list`) for quieting notifications, without the skill listing keys that would go stale
- Diagnosing a denial or slow approval with `av history` before guessing
- The error table: sandbox blocks the approval service, `Approval presentation interrupted`, locked Mac (`-25308`), ssh/signing `agent refused operation`
- What not to do to get unblocked (skip signing, swap SSH keys, extract tokens)

### automic-vault-upstream

User-invoked only (`/automic-vault:automic-vault-upstream [question]`). Answers a question about `av` from upstream's source and docs, citing the path and the version it describes, or with `drift` runs `bats tests/` to see whether the credentials skill still matches the CLI and source.

**Covers:**
- Finding the upstream remote (a clone's `origin` can be a stale fork) and fetching it
- Reporting installed, local-tree and latest-upstream versions before answering
- Where each kind of question is answered in upstream's repo
- Read-only: never runs `inject`, `save`, `harden` or other Approval-gated commands

## Provenance

Written from past session transcripts where agents guessed `av run`/`av set`, offered `GITHUB_TOKEN=$(gh auth token)`, or called an ssh refusal "deliberate policy" without reading `av history`. Checked with fresh-subagent scenarios with and without the skill (one sample each, so a signal and not proof).

Related upstream: [automic-vault/automic-vault#335](https://github.com/automic-vault/automic-vault/issues/335).
