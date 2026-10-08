# Angles, in more detail

## try: the tool menu

Before saying "can't", go down this list and try whichever fits:

- **Session history** (e.g. a transcript search tool): "I can't find where you said that" is usually answerable.
- **Internal docs or chat search**: why something was reverted, who owns it, what was decided.
- **A SQL console or read replica** the user has access to: "how many rows still have X".
- **A browser tool**: sites that need JS or login.
- **`<cli> --help` / `<cli> <subcommand> --help`**: "the CLI can't do X" is often wrong.
- **The past sessions where the thing was built**: when you can't find the code for something the user built.

Retry policy for transient failures: one retry for timeouts, 403s, 5xx, and hook/API "failed to contact" errors. If the retry fails the same way, report the block with both error messages.

## rederive: the clean-room pass

For a decision that's expensive to reverse, a fresh agent with no inherited context gives a less biased answer than re-checking it yourself.

1. Frame one decision. Separate "should we" from "how should we".
2. Start a fresh agent with no inherited conversation (not a fork).
3. Brief it with verified facts, fixed constraints, open questions, and enough direct evidence to check the summary. Leave out the prior conclusion, opinions, and leading language. Test: could a reader guess the hoped-for answer from the brief? If yes, rewrite it.
4. Ask for one verdict, its reasons, the strongest opposing case, and what would change the verdict.
5. Report the verdict as-is, even if it disagrees with you or the user.

## weigh: an option, done right

> **Keep the fixed retry count (recommended).** You get no code change, and it matches the existing `sidekiq_options retry: 5` in `base_job.rb`. Tradeoff: the billing job isn't idempotent (`charge_job.rb:2` says so), so it needs `retry: 0` either way. Effort: one line. Holds up: yes, until retry storms show up in metrics.

What makes it work: what you get, the tradeoff, effort, durability, and a file or command behind each claim.

## unpack: a question, done right

Before:

> Should we go with run-b or redo grp-7 first?

After:

> We're picking which benchmark to fix first. **run-b** is the second A/B run (it failed on the auth step), and **grp-7** is the group of 4 flaky tasks from last week ([#456](https://example.com/pull/456)). Fix run-b first? It blocks the comparison; grp-7 doesn't.

## simplify: shapes

- **default:** answer in one or two sentences, then up to five bullets, then stop.
- **for slack:** under ~100 words, the point in the first sentence, no headers.
- **for a PR comment:** the ask or finding first, evidence second, no recap of the PR.
- **for a status update:** one line each for done, in flight, and blocked.
