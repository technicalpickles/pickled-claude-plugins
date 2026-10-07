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

Filled in by Task 7.
