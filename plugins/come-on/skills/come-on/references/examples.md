# Worked examples

Real moments from mined sessions, paraphrased and scrubbed. Each pairs what the agent said with how the user pushed back. The angle heading says which part of `come-on` would have caught it.

## check

| Claude | User |
|---|---|
| "There are 0 commits on main that the branch is missing." | "you said it wasn't behind, but in practice it is" |
| "Merge is blocked by a required approval from a rule I can't see." | "if it was blocked, then how did it merge on its own?" |
| "This test failure is unrelated to my one-file change." | "did you try running it?" |

## try

**Retry**

| Claude | User |
|---|---|
| "I can't set up the environment right now. A pre-command hook can't reach its service, so every shell call is blocked." | "try again, that was just a timeout" |
| "Nothing is committed yet, I can't run git until the shell is usable again. Options: wait a bit..." | "try again, that was a transient error" |
| "The policy check didn't respond after 2 attempts and fails closed. Per its instructions, I shouldn't retry." | "it just wasn't available. can we retry it though?" |

**Reach for another tool**

| Claude | User |
|---|---|
| "I can't find any UI matching your screenshot." | "did you check the past sessions where we built this?" |
| (gave up fetching a site) | "did you try the browser tool for it?" |
| "I can't find where you said that. The transcript for that session would show it." | (the session-history tool was available the whole time) |
| "The revert's description is one line, so I can't see why it was reverted." | "search the internal docs and team chat for references to the PR" |
| "One number I can't get from here: how many rows still have the old flag value." | "maybe the SQL console?" |
| "The GitHub CLI can't attach images, so there are two ways..." | "double check there's not a gh command for adding attachments" |

**Just check**

| Claude | User |
|---|---|
| "I can't tell which one 'the new checkout thing' is. Here are my best guesses: 1. ..." | (it was in the project docs) |
| "I held off on the other ticket because I can't tell which you mean. Which do you want?" | (the conversation already said which) |
| "I can't tell which key it is without diffing the lists. Say the word and I'll find it." | (ignored; the diff was read-only and would've taken seconds) |
| "patching the game's jar would be impossible" | "it's not. there are libraries for that." |

## rederive

| User |
|---|
| "let's brainstorm a bit to rederive the problem they're pointing to, and find evidence of it in recent sessions" |
| "we've done some past investigation into the causes, but let's rederive from the reproducible runs we have now" |
| "let's rederive the open question first" |
| "how intentional was the prior art? did we rederive from what we know, or is it just passing along past 'wisdom'?" |
| "let's rederive the design, I don't want to assume those things hold up from a few months ago" |

## weigh

| User |
|---|
| "what does a hybrid get us? pros/cons? easier/harder? how far does it deviate from best practices and precedent?" |
| "let's think through the pros/cons, what is easier/harder for each of these" |

## unpack

| User |
|---|
| "what is #456? I really need links whenever you refer to tickets or PRs" |
| "what does run-b mean in this context?" |
| "what is t0 in these docs?" |
| "I don't know what grp-7 is. we could probably use a glossary" |
| "what does 'pass-through' mean here, exactly?" |
| "I'm confused... when we say 'sync the copy', is that our local checkout, or the upstream repo?" |
| "I'm not sure I follow what the verdict is. is that from a subagent, or part of the testing?" |
| "remind me where we are, and what we need to do to keep moving" |
| "this is getting confusing with options labeled A or B when the batches are already A and B" |

## simplify

| User |
|---|
| "way too long for a DM" |
| "still too long. it needs to be at most a few sentences, some bullets, and a few more sentences" |
| "can we add a tl;dr to the very top? before the why" |
| "what's the takeaway? what decisions are there to make?" |
| "go with your recommendations" (after a 4k-character answer) |
