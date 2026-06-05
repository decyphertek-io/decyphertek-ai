# projects/

**Technical reference notes** — commands, bug fixes, config snippets, architecture details.

## Filename convention
`<topic>.md` (no date prefix — these are evergreen references)

Examples:
- `adminotaur-tools.md`
- `chromadb-config.md`
- `slash-commands.md`
- `agent-builder-flow.md`

## What goes here
- Working shell commands
- Fixes for recurring bugs
- Config file examples / diffs
- Architecture / data flow notes
- API quirks, gotchas

## What does NOT go here
- Conversation summaries (→ `memory/`)
- Open-ended research / links (→ `research/`)

## Rules
- Group by topic, not by date
- Code blocks with language hints (```bash, ```python, ```yaml)
- Update existing files when you learn more — don't create duplicates
- Keep one topic per file

## Template

```markdown
# <Topic>

## Summary
What this file covers in one sentence.

## Commands / Config / Code
\`\`\`bash
# working commands here
\`\`\`

## Gotchas
- ...

## Related
- See also: `projects/<other>.md`
```
