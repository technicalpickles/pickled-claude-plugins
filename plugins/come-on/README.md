# come-on

For the moments you want to say "come on" to Claude. It catches Claude stopping short, on the work or on the telling, and makes it finish.

Each angle is a verb that finishes the sentence "come on, ___":

| Angle | Fires when Claude is about to... | Invoke directly |
|---|---|---|
| check | claim something is done, fixed, pre-existing, or "how it works" | `/come-on check [claim]` |
| try | say "can't", "impossible", or "blocked", or offer "say the word and I'll..." | `/come-on try` |
| rederive | build on a conclusion from a handoff, an old design, or a past investigation without re-checking it | `/come-on rederive` |
| weigh | put options in front of you | `/come-on weigh` |
| unpack | put options or a question in front of you that assumes context you don't have | `/come-on unpack [for reader]` |
| simplify | send a long reply with no clear answer up top | `/come-on simplify [for shape]` |

The skill fires on its own at those moments, and angles stack (a choice usually gets `weigh` and `unpack` together). `/come-on` with no mode means "apply whatever fits the last turn". It's one skill on purpose: every manual use counts toward the skill that has to auto-fire, and Claude Code keeps descriptions for the skills you use most when the skill listing runs out of room.

## Provenance

Built by mining real Claude Code sessions for the moments the user pushed back with some version of "come on": "did you check?", "try again, it was a timeout", "let's rederive this", "what does this even mean?", "way too long". Examples are paraphrased and scrubbed of anything identifying.

Prior art: [backnotprop/bro](https://github.com/backnotprop/bro), whose `bro` skill ("restate your last message, no jargon") is the seed of `simplify` and `unpack`, and whose `clean-room` skill inspired the fresh-agent pass in `rederive`. This plugin replaces the earlier `gut-check` plugin, whose verify and decide modes became `check` and `weigh`.

## Testing status

Eval cases live in `evals/` and run with Claude Code's built-in `claude plugin eval`:

- `tune-*`: trigger cases the description was tuned against.
- `holdout-*`: trigger cases it was never tuned against. These are the honest firing number.
- `scn-*`: behavior scenarios, each run with and without the plugin.
- `mode-*`: `/come-on <mode>` routing.

Last run: 2026-10-12, 3 runs per case (5 on the noisiest scenarios). The old skill is the previous version of this plugin (separate entry-point skills, old description), run on the same cases.

**Firing** (holdout):

| | old skill | this version |
|---|---|---|
| fires when it should (of 18) | 1 | 13 |
| fires when it shouldn't (of 12) | 0 | 0 |

Of the 18 should-fire runs, 12 are situations where Claude is about to stop short on its own and 6 are you pushing back. This version fires on 7 of the 12 and all 6 of the 6.

**Behavior scenarios** (mean score 0 to 1, and how many runs the skill fired in):

| Scenario | without | with | skill fired |
|---|---|---|---|
| weigh-hybrid | 0.00 | 0.73 | 3 of 3 |
| unpack-for-reviewer | 0.40 | 0.80 | 5 of 5 |
| unpack-handoff-jargon | 0.33 | 0.67 | 3 of 3 |
| weigh-retry-policy | 0.28 | 0.52 | 5 of 5 |
| check-preexisting | 0.84 | 0.92 | 5 of 5 |
| rederive-stale-root-cause | 1.00 | 1.00 | 5 of 5 |
| try-reach-other-tools | 0.87 | 0.87 | 3 of 3 |
| try-transient-retry | 1.00 | 0.84 | 2 of 5 |
| rederive-old-design-assumption | 0.60 | 0.60 | 0 of 3 |
| simplify-for-slack | 0.67 | 0.67 | 0 of 3 |

`/come-on check`, `/come-on unpack`, and `/come-on weigh` each passed 2 of 3 runs.

How to read it:

- A with/without gap only means something where the skill fired.
- The big change from the old skill is firing: 31 of 40 scenario runs now load it, up from 13. The description now names the kinds of requests where stopping short happens (status reports, handoffs, "X or Y?", summaries, pushback) instead of the internal moment of stopping short, which Claude doesn't notice in itself.
- The average lift from firing hasn't moved much, and the no-plugin scores swung by up to 0.33 between two sweeps of the same cases, so treat single-scenario gaps as noise. `try-transient-retry` still scores a bit worse with the plugin, and two scenarios never fire.
