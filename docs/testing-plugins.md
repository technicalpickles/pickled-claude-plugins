# Testing plugins

Plugins here are shell hooks, Python hooks, skills (prompts), and mods (TypeScript modules registered through `hooks/hooks.json` `modules`). Each needs a different kind of test, and a test at one layer says nothing about the next.

| What you changed | Check it with | Cost |
|---|---|---|
| A shell or Python hook | `bats` in the plugin's `tests/` | free, fast |
| A mod (`register.ts`) | `claude plugin test <plugin dir>` (a `*.test.ts` with a mocked engine), plus `claude plugin validate <plugin dir>` | free, fast |
| Anything that depends on what the real engine hands your code, or on what the model does with it | A headless end-to-end run with `claude -p` | real tokens, about a minute per session |

CI runs the first two for every plugin that has tests: per-plugin `*-plugin-tests.yml` workflows, and `plugin-tests.yml` for plugins that don't have one. When you add tests to a plugin that no workflow covers, add it there. The end-to-end layer is a manual pre-release check, because it needs auth and its model-behavior assertions can flake.

## Run local source without reinstalling

`claude -p --plugin-dir plugins/<name>` loads the checkout directly. No uninstall, reinstall or restart. Pass it once per plugin. Plugin settings for an inline plugin go in a settings file passed with `--settings`, under `pluginConfigs`, keyed `<name>@inline`:

```json
{ "pluginConfigs": { "second-brain@inline": { "options": { "devlog_mode": "sidechain" } } } }
```

## Probe the engine once, then encode what you learn

A mocked engine only knows what you told it. It cannot tell you the skill name a hook receives, the shape of a transcript, or the key a setting arrives under. Guesses about those were wrong in the park work, and only a real run showed it. Run the real thing once, look, and put the answer in a test.

## Headless end-to-end rules

- **Assert on the injected value, not the label.** A skill's own text often contains the words your hook injects. `grep "Park vault:"` passes with no hook at all. Match the value (`Park vault: /path`).
- **Read the on-disk transcript.** `--output-format stream-json` leaves out the expanded skill text. `~/.claude/projects/*/<session_id>.jsonl` has it. The session id is in the first stream message.
- **Allow `Skill` in `--allowedTools`.** Without it, a plain-words request fails with an opaque skill error that reads like a product bug.
- **Give directories outside the cwd with `--add-dir`, and keep scratch files inside the working directory.** Headless runs block `cat` and redirects elsewhere.
- **Separate deterministic checks from model-dependent ones.** "The line reached the model" is deterministic. "The file landed where the vault says" depends on the model, so rerun a failure once before calling it a regression.
- **Use a scratch vault, directory and settings.** Never point a test at your real data.

## Worked example

[`plugins/agent-meta/docs/verifying-park.md`](../plugins/agent-meta/docs/verifying-park.md) and `plugins/agent-meta/tests/e2e/park-vault.sh` cover all three layers for park and unpark.
