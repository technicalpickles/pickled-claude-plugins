# The Art of Scannable Writing

A practical guide to formatting prose so readers can both skim and read deeply - drawn from thirty years of usability research, the journalism tradition that came before it, and the grammar move that quietly does most of the work.

## Why this matters (the empirical case)

The foundational claim is that people don't read web pages - they scan them. The headline finding comes from a 1997 study by John Morkes and Jakob Nielsen at the Nielsen Norman Group, which found that [79% of test users always scanned any new page they came across, and only 16% read word-by-word](https://www.nngroup.com/articles/how-users-read-on-the-web/). The same study found that rewriting Sun Microsystems' web pages to be [concise, scannable, and objective improved measured usability by 124%](https://www.nngroup.com/articles/concise-scannable-and-objective-how-to-write-for-the-web/) - far more than any single intervention alone.

Subsequent research confirmed and tightened the picture. [2006 eye-tracking research](https://www.nngroup.com/articles/website-reading/) showed readers scanning pages in an F-shape: across the top, then a partial second line, then down the left margin. [2008 research quantified that users have time to read at most 28% of the words on an average page view](https://www.nngroup.com/articles/website-reading/). And in 2020, NN/g published a [400-page synthesis of three large eye-tracking studies spanning 13 years and over 500 participants](https://www.parentcenterhub.org/web-reading/) which concluded: the more things change, the more they stay the same. People still scan.

Two cognitive principles converge to produce this behavior. The first is what Herbert Simon called **satisficing** - taking the first reasonable option rather than the optimal one - popularized for web design by [Steve Krug's *Don't Make Me Think*](https://en.wikipedia.org/wiki/Don't_Make_Me_Think). Readers don't optimize their reading; they hunt for "good enough" matches to what they came looking for and move on. The second is cognitive load: screen reading is [roughly 25% slower than paper](https://www.nngroup.com/articles/be-succinct-writing-for-the-web/), so readers compensate by reading less.

The practical implication isn't "write shorter." It's: **format so the scanner gets the gist and the reader gets the depth, without writing two versions.**

## A short history of the idea

The pattern of front-loading important information is older than the web. The **inverted pyramid** - leading with the most essential facts, then descending in importance - emerged in American journalism in [the mid-19th century alongside the spread of the telegraph](https://en.wikipedia.org/wiki/Inverted_pyramid_(journalism)). One persuasive origin story traces its first clear use to [Secretary of War Edwin Stanton's April 15, 1865 telegram announcing Lincoln's assassination](https://www.poynter.org/reporting-editing/2003/birth-of-the-inverted-pyramid-a-child-of-technology-commerce-and-history/), which newspapers printed almost verbatim. Telegraphy made the structure necessary: transmission was expensive and unreliable, so the most important facts had to come first in case the wire was cut mid-message. The structure outlived the telegraph because it solves a deeper problem - it lets readers stop at any point and still walk away with the gist.

The web inherited this directly. Nielsen's 1997 guidelines are essentially the inverted pyramid plus visual chunking: [highlighted keywords, meaningful sub-headings, bulleted lists, one idea per paragraph, conclusion first, half the word count of print](https://www.nngroup.com/articles/how-users-read-on-the-web/). Krug's 2000 book *Don't Make Me Think* added the user-side framing - readers don't read, they [scan, satisfice, and muddle through](https://en.wikipedia.org/wiki/Don't_Make_Me_Think) - and the matching design directive: design for scanning, not reading. The technical writing community then formalized the patterns into [explicit rules](https://developers.google.com/tech-writing/one/lists-and-tables): when to use a numbered list, when to bullet, how to keep items parallel.

So the modern guidance is the convergence of three traditions: journalism's inverted pyramid, usability research, and technical communication practice. They all point in the same direction.

## The core techniques

### 1. Convert prose to a list when the structure is already there

The first move is recognizing **latent structure** - prose that has list-shape hidden inside paragraph form. Each of these signals means a list is trying to escape:

- **Parallel sentence shapes** - *"X is A. Y is B."* Each sentence has the same skeleton, signaling the items are siblings.
- **Contrast markers** - *"that's distinct from"*, *"as opposed to"*, *"versus"*, *"on the other hand"*. These are arrows pointing at a contrast that bullets display better than prose.
- **Bold terms followed by colons** - you've already written a definition list in prose. Marina Hurley calls these [statement-plus-examples paragraphs](https://www.writingclearscience.com.au/bullet-point-lists-versus-paragraphs/) and notes they convert almost mechanically.
- **Three or more parallel items** - the rule of three. Two parallel items can stay in prose (*"she came, she saw, she conquered"* doesn't want bullets). Three or more usually do.
- **Embedded series** - Google's tech-writing guide calls these [run-in lists](https://developers.google.com/tech-writing/one/lists-and-tables): *"the API enables callers to create X, query Y, and delete Z"*. Generally promote them to real lists.

### 2. Keep prose when the connective tissue matters

Bullets are lossy. They strip out the words that explain *why* items are next to each other. Keep prose when:

- **Connectives carry argument** - *counterintuitively*, *and as a result*, *but only when*. These do real work that bullets can't represent.
- **The flow is causal or narrative** - *"we tried X, which failed because Y, so we pivoted to Z"* is a story, not a list.
- **The audience expects sustained reading** - long-form essays, narratives, persuasion. [UXmatters notes that increasing scannability isn't always the right move and can hurt long-form journalism](https://www.uxmatters.com/mt/archives/2015/06/scannability-principle-and-practice.php).
- **The items are two and short** - naturally part of a sentence's rhythm.

Luke Gearing's ["Bullet Points vs Prose"](https://lukegearing.blot.im/bullet-points-vs-prose) is a useful corrective: he rewrites his own bulleted text into prose and demonstrates how the bullets had been hiding voice and connective meaning.

**Rule of thumb:** if the prose is doing list work, let it be a list. If the prose is doing argument work, leave it.

### 3. Use parallel structure

Once items are bullets, they must be **parallel** - same grammatical form. This is the grammar move underneath the visual one, and it's where most lists fall apart. The [*Perspectives on Medical Education* guide](https://pmc.ncbi.nlm.nih.gov/articles/PMC4673060/) gives the cleanest summary: each idea in a series should be written in a similar grammatical and stylistic form.

What "parallel" actually means in practice:

- **Same part of speech** - all nouns, all gerunds, all infinitives. *I like running, swimming, and cycling* (parallel) vs *I like running, to swim, and cycling* (mixed).
- **Same tense and voice** - don't mix *reduces* (active present) with *improving* (gerund).
- **Same opening shape** - when one bullet leads with a bolded term, every bullet should lead with a bolded term.
- **Roughly the same weight** - one-word items shouldn't share a list with multi-sentence items.

[Google's guide enforces this strictly](https://developers.google.com/tech-writing/one/lists-and-tables): items must be parallel in grammar, logical category, capitalization, and punctuation. Numbered lists in particular should [start with imperative verbs](https://developers.google.com/tech-writing/one/lists-and-tables): *Stop the server. Edit the config. Restart it.*

The check is auditory as much as logical. [Faulty parallelism sounds wrong even when you can't articulate why](https://www.rabbitwitharedpen.com/blog/parallel-structure). Reading bullets out loud surfaces the breaks fast.

### 4. Front-load the load-bearing word

[Eye-tracking research shows readers scan in an F](https://www.nngroup.com/articles/f-shaped-pattern-reading-web-content/) - across the top of the page, then a shorter horizontal pass, then down the left margin. The implication for writing is that **the leftmost word of every bullet, heading, and paragraph is the most-seen word on the page**.

Practical applications:

- **Lead with the term, not the explanation** - *Workflow methodology - how a coding agent runs through...* rather than *How a coding agent runs through the stages is the workflow methodology...*
- **Bold the term, not the definition** - bolding is for the load-bearing concept the scanner needs to find the right item, not the supporting text around it.
- **Don't over-bold** - if everything is emphasized, nothing is. NN/g's research treats highlighted keywords [as one technique among several, not the whole strategy](https://www.nngroup.com/articles/how-users-read-on-the-web/).
- **One idea per paragraph** - Nielsen specifically warns that [users will skip over any additional ideas if they're not caught by the first few words](https://www.nngroup.com/articles/how-users-read-on-the-web/). Don't bury a second concept in sentence three.

### 5. Apply the inverted pyramid at every level

The journalism move scales. The same "most important first, then descending detail" structure should apply to:

- **The page** - conclusion in the opening paragraph; details follow.
- **The section** - topic sentence first; elaboration follows.
- **The paragraph** - main point in sentence one.
- **The bullet** - load-bearing term first; the rest after.

## A gallery of conversions

Different patterns, different conversions. Here are five common shapes worth recognizing on sight.

### Pattern 1: Labeled list (definitions in prose)

The shape your original example took - two parallel terms each followed by a definition.

> **Before:** Agent orchestration is overloaded. Engineers usually mean workflow methodology: how a coding agent runs through Understand, Plan, Execute, Deliver, and Monitor+React. That's distinct from surface: how an agent gets invoked, deployed, chained, or run in parallel.

> **After:** "Agent orchestration" is overloaded. Engineers usually mean one of two things:
> - **Workflow methodology** - how a coding agent runs through Understand, Plan, Execute, Deliver, and Monitor+React.
> - **Surface** - how an agent gets invoked, deployed, chained, or run in parallel.

Signals that fired: two parallel bolded terms with colons, *"that's distinct from"* contrast marker, two definitions with identical *"how an agent X"* structure.

### Pattern 2: Embedded series (list hiding in a sentence)

The "verb a, verb b, and verb c" shape inside a sentence. From [Google's tech-writing guide](https://developers.google.com/tech-writing/one/lists-and-tables):

> **Before:** The API enables callers to create llamas, query alpacas, delete vicunas, and track dromedaries.

> **After:** The API enables callers to:
> - Create llamas
> - Query alpacas
> - Delete vicunas
> - Track dromedaries

Four parallel verb-noun pairs in a sentence almost always wants to be a list. Each item shorter? Maybe leave inline. Four or more parallel verbs? Promote.

### Pattern 3: Steps (sequence matters)

> **Before:** To reconfigure the server, you first stop it, then edit the configuration file, and finally restart it.

> **After:** To reconfigure the server:
> 1. Stop the server.
> 2. Edit the configuration file.
> 3. Restart the server.

Numbered, not bulleted, because order matters. Each step is an imperative verb, matching Google's rule.

### Pattern 4: Contrast (A vs B)

> **Before:** While synchronous APIs block the caller until completion, asynchronous APIs return immediately and notify the caller via a callback or event.

> **After:** The two API styles differ in how they hand control back to the caller:
> - **Synchronous** - blocks the caller until the operation completes.
> - **Asynchronous** - returns immediately and notifies the caller via a callback or event.

The original *"while X, Y"* construction signals contrast. Bullets render the contrast visually.

### Pattern 5: The negative example (when NOT to convert)

> **Original (prose, correct as-is):** We initially tried a centralized gateway, but it became a bottleneck under load and, counterintuitively, made debugging harder because traces had to traverse it. So we moved to a peer-to-peer model.

> **Bad conversion to bullets:**
> - Initially tried centralized gateway
> - Became a bottleneck under load
> - Made debugging harder
> - Moved to peer-to-peer model

The bullet version loses *but*, *and*, *counterintuitively*, *because*, *so*. The relationships between items were the entire point. Leave it as prose.

## Anti-patterns to avoid

- **Bullet-bombing.** Pages of nothing but bullets become a wall just like prose does. [Bullets should be sprinkled into prose, not replace it](https://web.mit.edu/juggler/www/ocw/ocw_lectures/class01/lecture_lists.htm) - a mix of the two works best.
- **Single-item lists.** A list of one isn't a list. Either find more items or write it as a sentence.
- **Mixed grammatical forms within a list.** Audible immediately when read aloud.
- **Over-bolding.** [If everything is emphasized, nothing is.](https://www.nngroup.com/articles/how-users-read-on-the-web/) Bold the load-bearing term; let the supporting words be supporting words.
- **Clever sub-headings.** Nielsen specifically warns against [clever-rather-than-clear sub-headings](https://www.nngroup.com/articles/how-users-read-on-the-web/) - they fail readers scanning for keywords.
- **Burying the lede.** The inverted pyramid says: conclusion first. Resist the academic-essay impulse to build up to it.
- **Lists over 8 items.** [Technical writing guides converge on a 2-to-8 range](https://pressbooks.senecacollege.ca/technicalwriting/chapter/lists/). Past that, regroup into sub-lists or rethink the structure - emphasizing everything emphasizes nothing.

## A mantra

If the prose is doing list work, let it be a list. If the prose is doing argument work, leave it. Front-load the load-bearing word. Make every bullet parallel. Bold the term, not the definition. Conclude first; explain second.

---

## Further reading

**Foundational research**

- Nielsen, [How Users Read on the Web](https://www.nngroup.com/articles/how-users-read-on-the-web/) (1997) - the founding 79/16 study.
- Morkes & Nielsen, [Concise, SCANNABLE, and Objective: How to Write for the Web](https://www.nngroup.com/articles/concise-scannable-and-objective-how-to-write-for-the-web/) (1997) - the Sun Microsystems usability study, the 124% improvement finding.
- Nielsen, [F-Shaped Pattern of Reading on the Web](https://www.nngroup.com/articles/f-shaped-pattern-reading-web-content/) (2006) - the original eye-tracking research.
- Nielsen, [Website Reading: It (Sometimes) Does Happen](https://www.nngroup.com/articles/website-reading/) (2013) - the 28% finding and a useful corrective.
- Krug, [*Don't Make Me Think* (Revisited)](https://en.wikipedia.org/wiki/Don't_Make_Me_Think) (2014 ed.) - satisficing, scanning, billboard design.

**Practical guides**

- Google, [Lists and Tables](https://developers.google.com/tech-writing/one/lists-and-tables) - the clearest rule-set, with parallelism requirements.
- Hurley, [Bullet point lists versus paragraphs](https://www.writingclearscience.com.au/bullet-point-lists-versus-paragraphs/) - the statement-plus-examples heuristic.
- Seneca College, [Lists chapter, *Technical Writing Essentials*](https://pressbooks.senecacollege.ca/technicalwriting/chapter/lists/) - the five list types (bullet, numbered, in-sentence, labeled, nested).
- UXmatters, [Scannability: Principle and Practice](https://www.uxmatters.com/mt/archives/2015/06/scannability-principle-and-practice.php) - when scannability is and isn't the right move.

**The grammar move underneath**

- *Perspectives on Medical Education*, [The Power of Parallel Structure](https://pmc.ncbi.nlm.nih.gov/articles/PMC4673060/) - short, practical, the cleanest summary.
- Rabbit with a Red Pen, [Writing Parallel Structure](https://www.rabbitwitharedpen.com/blog/parallel-structure) - auditory heuristics and the four areas to check.

**Counterpoints and historical context**

- Gearing, [Bullet Points vs Prose](https://lukegearing.blot.im/bullet-points-vs-prose) - a writer rewriting his own bullets into prose.
- Wikipedia, [Inverted pyramid (journalism)](https://en.wikipedia.org/wiki/Inverted_pyramid_(journalism)) - the structural ancestor.
- Scanlan, [Birth of the Inverted Pyramid](https://www.poynter.org/reporting-editing/2003/birth-of-the-inverted-pyramid-a-child-of-technology-commerce-and-history/) (Poynter) - the Lincoln-telegram origin story and the telegraph context.
