# memory/

Per-session **conversation summaries**. High-level, not transcripts.

## Filename convention
`YYYY-MM-DD-<short-topic>.md`

Example: `2026-06-04-wiki-setup.md`

## What goes here
- What the user asked
- What was decided / built / fixed
- Key file paths touched
- Open questions / next steps

## What does NOT go here
- Full conversation transcripts
- Technical reference (that goes in `projects/`)
- Research links (that goes in `research/`)

## Rules
- Keep each file under ~50 lines — bullet points only
- One file per session/topic
- Skip reading memory files older than ~3 days unless directly relevant
- Never glob `memory/*.md` — only read the ONE file whose name matches the current topic

## Template

```markdown
# <Topic>

**Date:** YYYY-MM-DD

## Summary
One sentence describing what this session was about.

## Decisions
- ...

## Files touched
- `path/to/file` — what changed

## Next steps
- ...
```
