# come-on

For the moments you want to say "come on" to Claude. It catches Claude stopping short, on the work or on the telling, and makes it finish.

Each angle is a verb that finishes the sentence "come on, ___":

| Angle | Fires when Claude is about to... | Entry point |
|---|---|---|
| check | claim something is done, fixed, pre-existing, or "how it works" | `come-on-check` |
| try | say "can't", "impossible", or "blocked", or offer "say the word and I'll..." | `come-on-try` |
| rederive | build on a conclusion from a handoff, an old design, or a past investigation without re-checking it | `come-on-rederive` |
| weigh | put options in front of you | `come-on-weigh` |
| unpack | put options or a question in front of you that assumes context you don't have | `come-on-unpack [reader]` |
| simplify | send a long reply with no clear answer up top | `come-on-simplify [shape]` |

The `come-on` skill fires on its own at those moments, and angles stack (a choice usually gets `weigh` and `unpack` together). The entry-point skills are user-invoked only and force a single angle. Invoking `come-on` directly means "apply whatever fits the last turn."

## Provenance

Built by mining real Claude Code sessions for the moments the user pushed back with some version of "come on": "did you check?", "try again, it was a timeout", "let's rederive this", "what does this even mean?", "way too long". Examples are paraphrased and scrubbed of anything identifying.

Prior art: [backnotprop/bro](https://github.com/backnotprop/bro), whose `bro` skill ("restate your last message, no jargon") is the seed of `simplify` and `unpack`, and whose `clean-room` skill inspired the fresh-agent pass in `rederive`. This plugin replaces the earlier `gut-check` plugin, whose verify and decide modes became `check` and `weigh`.

## Testing status

Eval cases live in `evals/` and run with Claude Code's built-in `claude plugin eval`. Trigger cases check that the `come-on` skill fires at the right moments and stays quiet on routine work. Behavior scenarios run each situation with and without the plugin and report the difference.

Last run: 2026-10-08, 3 runs per case.

**Triggers:** 10/10 fire, 8/8 stay quiet. The skill description was tuned against these prompts, so this overstates how well it fires on phrasings it hasn't seen.

**Behavior scenarios** (mean score over 3 runs, 0 to 1):

| Scenario | without | with | skill fired (of 3 runs) |
|---|---|---|---|
| unpack-handoff-jargon | 0.33 | 0.83 | 3 |
| weigh-hybrid | 0.00 | 0.47 | 3 |
| rederive-stale-root-cause | 0.87 | 1.00 | 2 |
| weigh-retry-policy | 0.47 | 0.60 | 0 |
| simplify-for-slack | 0.83 | 1.00 | 0 |
| check-preexisting | 0.87 | 0.60 | 1 |
| try-transient-retry | 0.87 | 0.73 | 1 |
| rederive-old-design-assumption | 1.00 | 1.00 | 0 |
| try-reach-other-tools | 1.00 | 1.00 | 0 |
| unpack-for-reviewer | 0.50 | 0.50 | 0 |

How to read it:

- A gap only means something where the skill fired. Where it never fired, the difference is run-to-run noise.
- The skill fires reliably when the prompt itself asks for the angle (weigh these options, ask me the decision). It fires much less often at the moment Claude is about to stop short on its own (claiming something is checked, saying "can't", building on an old conclusion).
- Until that improves, the entry-point skills (`come-on-check`, `come-on-try`, and the rest) are the dependable way to invoke an angle.
- Three runs per case is small. Scores moved a lot between two sweeps of the same cases.
