# YouTube

Hosts: `youtube.com`, `www.youtube.com`, `m.youtube.com`, `youtu.be`.

## Read

Default is the full pull: video, spoken transcript, and on-screen text (slides, infographics)
merged into one chronological document. Do not ask the user which mode.

```bash
OUT="$TMPDIR/yt-digest/<video-id>"
yt-digest --out-dir "$OUT" "<url>"
```

Then `Read` `$OUT/full_context.md` (transcript + on-screen text) and `$OUT/metadata.json`.

Fall back to `--transcript-only` (reads `$OUT/transcript.md`) only with a concrete reason, and say
which reason in your reply:

- the video is very long, so download and OCR cost outweighs the value
- the download fails or is blocked
- the content is evidently audio-only (podcast, talk over a static frame)

A talking head alone is not a reason: they still show slides, demos and screens.

**Requires** `uv` and a logged-in `claude` CLI (`yt-digest` runs as `uv run --script`; first run
downloads its dependencies). Use `$TMPDIR`, never the vault or the repo, for `--out-dir`.

## Frontmatter extras

Beside `source`, from `$OUT/metadata.json`:

```yaml
platform: youtube
channel: Some Channel
published: 2026-01-02
```

If `metadata.json` is missing, omit `channel` and `published` rather than guessing. It is written
only on a fresh run (not with `--skip-download`), and is best-effort even then.

## Failure mode

If `yt-digest` fails outright (not just the full-mode fallback above), stop and report the error
output. Do not write a note from the video title, the description, or someone else's summary.
