# pickled-knowledge: Johnny Decimal map

Condensed from the vault's own `CLAUDE.md`. This is for guessing a **likely destination area**
to save Josh a step, and for picking tags that match how the vault already carves things up.
It is a guess, not a fact - nothing here can be confirmed without actually opening the vault, so
always present it as "probably `NN`", never as a done deal, and never as something already filed.

## Structural rules (the short version)

- **Status lives in frontmatter, never in a folder name.** No "Active"/"Done"/"Archive" folders.
- **Areas are record-heavy or thought-heavy.** Record-heavy areas (Family, Home, Work-projects,
  People) use numbered ID-folders per discrete thing. Thought-heavy areas (Software, Thinking)
  stay flat - loose timestamped notes plus tags. A fresh chat capture is almost always a *thought*
  (an idea, a concept, a tool note), so flat-area placement is the common case.
- **Tags carry overlapping axes**, not new folders. If a note could plausibly sit in two areas,
  say so and suggest a tag for the secondary one rather than picking a folder to force it into.

## The 9 areas

| Code | Area | What lives here | Notable sub-categories |
|------|------|------------------|-------------------------|
| `10-19` | System & Capture | Meta: inbox, vault config, PKM practice itself | `11` Inbox & triage (fresh captures land here) · `13` System config · `14` Knowledge management practice |
| `20-29` | Work | Employer-specific (Gusto) | `21` role/team/org/culture · `22` projects (ID-folders) · `23` cross-employer career dev · `24` eng tooling/infra/CI · `25` work-relationship process (interviews, 1:1s - **not** person notes, those go `86`) · `28` past employers (ID-folders) |
| `30-39` | Family | People you're responsible for | `31` Tracy · `32` Alex · `33` pets (one ID-folder per pet) · `36` family finances/estate · `39` other family (ID-folders) |
| `40-49` | Home & Property | Physical spaces, maintenance | `41` current house (system ID-folders: HVAC, plumbing, electrical, appliances...) · `42` rental property · `43` smart home · `44` home lab/network · `45` vehicles (ID-folder per car) · `49` sold/past properties |
| `50-59` | Self & Body | Yours specifically - body, health, mind, appearance | `51` physical/medical · `52` ADHD/autism/therapy/psych · `53` fitness · `56` clothes/grooming |
| `60-69` | Software & Engineering | The general discipline, not job-specific | `61` SE concepts/architecture/patterns · `62` Ruby/Rails · `63` JS/Node/frontend · `65` DevOps/infra/CI/datastores · `66` AI & agentic development · `67` tools & dev experience (dense ID-folders: `67.01` git, `67.02` github, `67.03` macos, `67.04` ssh, `67.05` neovim, `67.06` tmux, `67.07` fish, `67.08` ghostty, `67.09` pickles.dev, `67.10` obsidian) · `69` other/low-volume languages |
| `70-79` | Interests & Hobbies | Non-software | `71` shows/movies/anime · `72` books/comics/scifi · `73` video games · `74` RPGs & board games (general knowledge only - active campaigns live in a separate RPG vault) · `75` legos/making · `76` cooking/cocktails · `79` podcasts/misc |
| `80-89` | Community & People | Activity groups, social ties, PRM | `84` social groups/clubs (own ties, e.g. a pool membership) · `85` online communities · `86` People (flat name-notes, e.g. `Carl Hoover.md` - **any** person note, including coworkers, goes here) · `89` other community |
| `90-99` | Thinking & Concepts | Mental models, frameworks | `91` cognitive biases/mental models/named laws · `92` productivity/GTD/planning · `93` leadership/management · `94` social/cultural · `95` writing craft |

## Quick disambiguation

- **A tool config for *your own machine*** (dotfiles, tmux/fish/neovim setup, personal CLI habits)
  → `67`. **A tool/language *as it's used in projects*** (Ruby idioms, JS build tooling, Docker
  patterns) → `61`-`65` by ecosystem.
- **A person, even a coworker** → `86`, never `25` (`25` is the work-relationship *process*, not
  the person record).
- **A management/leadership/mentoring note** that surfaced while working → `93`, not `20-29`,
  unless it's specifically about *this* job's culture (`21`).
- **An X9 "Other" category** (`69`, `89`, `49`, `39`, `79`) is the catch-all for its area - suggest
  it only when nothing more specific fits, never invent a new mid-area "Other X" category.

## When you genuinely can't tell

Say so - "could go either `66` (AI concepts) or `92` (productivity) - your call" beats guessing
with false confidence. This map is a hint to save Josh a step, not a routing decision he doesn't
get to see.
