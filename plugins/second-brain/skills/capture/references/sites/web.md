# Web pages (default)

Used for any host without its own playbook, and for PDFs, local files and connector sources.

## Read

Follow the ladder in [../fetch-ladder.md](../fetch-ladder.md): lightpanda first, then the browser
pane, then a fetcher built for the source, with WebFetch last.

## Frontmatter extras

None. `source` is the URL. A note built from WebFetch also gets `fetched-via: webfetch`, per the
ladder.

## Failure mode

If no rung returns the page (login wall, 4xx/5xx, empty body), stop and say so. Do not write a
note from the search snippet, the title, or background knowledge.
