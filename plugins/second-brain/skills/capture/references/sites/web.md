# Web pages (default)

Used for any host without its own playbook.

## Read

- Preferred: `mcp__lightpanda__markdown {url}`
- Fallback: `WebFetch`

## Frontmatter extras

None. `source` is the URL.

## Failure mode

If neither tool returns the page (login wall, 4xx/5xx, empty body), stop and say so. Do not write
a note from the search snippet, the title, or background knowledge.
