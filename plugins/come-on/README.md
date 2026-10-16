# come-on

Do any of these sound familiar?

- "That test failure is unrelated to my one-file change."
- "I can't from here."
- "The handoff says it's done."
- "Here are the options: A, B, or C?"
- "Go with option B, the grp-7 approach."
- _[four paragraphs of background]_ "...so yes, it works."

Each one is a moment where you'd say "come on," and Claude stops short in enough different ways that each gets its own flavor. This plugin is one way to give the nudge: it fires when it spots the moment, and you can throw it yourself when it doesn't.

## The angles

Six angles, each a verb that finishes the sentence "come on, ___":

<table>
  <tr>
    <td align="center" width="33%">
      <img src="https://media.giphy.com/media/bjB3gtFvREqqr5NAHW/giphy.gif" width="260" alt="Tim Robinson looking deeply skeptical, as if asking 'are you sure about that?'"><br>
      come on, <b>check</b>
    </td>
    <td align="center" width="33%">
      <img src="https://media.giphy.com/media/exQrMRVK2x9rW/giphy.gif" width="260" alt="Shia LaBeouf shouting 'Just do it!'"><br>
      come on, <b>try</b>
    </td>
    <td align="center" width="33%">
      <img src="https://media.giphy.com/media/WRQBXSCnEFJIuxktnw/giphy.gif" width="260" alt="The math lady meme: a woman looking suspicious as equations float around her, as if saying 'show me the math'"><br>
      come on, <b>rederive</b>
    </td>
  </tr>
  <tr>
    <td align="center">
      <img src="https://media.giphy.com/media/zbzNUbpFnlw8E/giphy.gif" width="260" alt="A little girl shrugging: 'why not both?'"><br>
      come on, <b>weigh</b>
    </td>
    <td align="center">
      <img src="https://media.giphy.com/media/xT77Y36ijyuwn58bja/giphy.gif" width="260" alt="Barack Obama at a podium pulling his head back with furrowed brows and a small shrug, as if saying 'I don't even know what that means'"><br>
      come on, <b>unpack</b>
    </td>
    <td align="center">
      <img src="https://media.giphy.com/media/bWM2eWYfN3r20/giphy.gif" width="260" alt="Sweet Brown: 'Ain't nobody got time for that'"><br>
      come on, <b>simplify</b>
    </td>
  </tr>
</table>

## Usage

The skill fires on its own when Claude is about to do what the middle column describes, and you can invoke any angle directly.

| Angle | Fires when Claude is about to... | Invoke directly |
|---|---|---|
| check | claim something is done, fixed, pre-existing, or "how it works" | `/come-on check [claim]` |
| try | say "can't", "impossible", or "blocked", or offer "say the word and I'll..." | `/come-on try` |
| rederive | build on a conclusion from a handoff, an old design, or a past investigation without re-checking it | `/come-on rederive` |
| weigh | put options in front of you | `/come-on weigh` |
| unpack | put options or a question in front of you that assumes context you don't have | `/come-on unpack [for reader]` |
| simplify | send a long reply with no clear answer up top | `/come-on simplify [for shape]` |

Angles stack (a choice usually gets `weigh` and `unpack` together). `/come-on` with no mode means "apply whatever fits the last turn". It's one skill on purpose: every manual use counts toward the skill that has to auto-fire, and Claude Code keeps descriptions for the skills you use most when the skill listing runs out of room.

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
