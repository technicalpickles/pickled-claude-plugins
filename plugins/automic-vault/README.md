# automic-vault Plugin

Teaches agents what `av` is and how to work with [Automic Vault](https://github.com/automic-vault/automic-vault) without reaching around it.

## Skills

### automic-vault-credentials

Use when a command mentions `av` or Automic Vault, a task needs a credential on a Mac that has it installed, or `gh`, `git push`, commit signing or an `av` command fails with an approval, sandbox, "agent refused operation" or `-25308` error.

**Covers:**
- What `av` is, and that it replaces `gh auth token`, `op read` and `.env` files as the way to get a credential
- Injecting secrets by name (`av inject`), checking names (`av list`), and handing `av save` to the user
- Diagnosing a denial or slow approval with `av history` before guessing
- The error table: sandbox blocks the approval service, `Approval presentation interrupted`, locked Mac (`-25308`), ssh/signing `agent refused operation`
- What not to do to get unblocked (skip signing, swap SSH keys, extract tokens)

## Provenance

Written from past session transcripts where agents guessed `av run`/`av set`, offered `GITHUB_TOKEN=$(gh auth token)`, or called an ssh refusal "deliberate policy" without reading `av history`. Checked with fresh-subagent scenarios with and without the skill (one sample each, so a signal and not proof).

Related upstream: [automic-vault/automic-vault#335](https://github.com/automic-vault/automic-vault/issues/335).
