# Decyphertek.ai Wiki — Directory

**WIKI_ROOT (source):** `~/Documents/git/decyphertek-ai/wiki/`
**Runtime root:**       `~/.decyphertek.ai/`

> READ THIS MAP FIRST. The runtime enforces it: discovery tools are blocked
> until you call `wiki_search(keyword)`. Do not glob `~/**`. Do not walk paths
> already listed below.

---

## Read order (every task, no exceptions)

1. `soul.md`           — identity + behavior (auto-injected each turn)
2. `directory.md`      — this map (auto-injected each turn)
3. `wiki_search(keyword)` — single tool call to grep the wiki for the topic
4. ONE `read_file` of the most relevant projects/, memory/, or research/ entry
5. Filesystem search — LAST resort, requires an explicit user-given path

---

## Runtime layout (`~/.decyphertek.ai/`)

```
~/.decyphertek.ai/
├── agent-store/         ← agents + registry
│   ├── adminotaur/          (adminotaur.agent — supervisor, this is YOU)
│   ├── agent-builder/       (agent-builder.agent — builds new agents)
│   ├── mcp-builder/         (mcp-builder.agent — builds new MCPs)
│   └── workers.yaml         (agent registry: versions, release URLs, creds mapping)
│
├── mcp-store/           ← MCP skills + registry
│   ├── rag-chat/
│   ├── web-search/
│   ├── worldnewsapi/
│   └── skills.yaml          (MCP registry)
│
├── app-store/           ← supporting apps
│   └── chromadb/            (vector DB for RAG / long-term memory)
│
├── configs/             ← runtime configs
│   ├── ai-config.yaml       (model, provider, temperature, etc.)
│   ├── cdb-config.yaml      (ChromaDB config)
│   └── slash-commands.yaml  (CLI slash command definitions)
│
├── creds/               ← encrypted credentials (do not read directly)
├── keys/                ← keypairs for credential encryption
├── bin/                 ← installed binaries
├── config/              ← reserved
├── versions.yaml        ← local installed versions of agents/mcps
└── .password_hash       ← master password hash (never touch)
```

## Source layout (`~/Documents/git/decyphertek-ai/`)

```
decyphertek-ai/
├── cli/
│   ├── cli-ai.py            (main CLI — slash commands, agent orchestration)
│   └── configs/             (shipped default configs)
├── wiki/                    (THIS WIKI — source of truth)
│   ├── soul.md
│   ├── directory.md
│   ├── memory/              (conversation summaries: YYYY-MM-DD-topic.md)
│   ├── projects/            (technical notes: commands, fixes, configs)
│   └── research/            (broader findings, external references)
├── install.sh
├── uninstall.sh
└── README.md
```

## Related source repos (`~/Documents/git/`)

```
agent-store/                 ← source for the .agent binaries (adminotaur, agent-builder, mcp-builder)
mcp-store/                   ← source for MCP skills
app-store/                   ← source for supporting apps (chromadb, etc.)
```

---

## Agent tools (priority order)

| Order | Tool             | Purpose                                                            |
|-------|------------------|--------------------------------------------------------------------|
| 1     | `wiki_search`    | Grep this wiki (directory.md + projects/ + memory/ + research/)   |
| 2     | `read_file`      | Read ONE specific file                                             |
| 3     | `write_file`     | Persist notes / edit files within `~/`                             |
| 4     | `remember_path`  | Append a newly-found external path to this directory.md            |
| 5     | `list_directory` | Only for paths NOT in this map; gated by wiki-first policy         |
| 6     | `execute_shell`  | Narrow ops only; broad `find`/`locate`/`ls ~`/`grep -r ~` BLOCKED  |

---

## Folder purpose (where notes go)

| Folder        | What goes there                                                     |
|---------------|---------------------------------------------------------------------|
| `memory/`     | Per-session conversation summaries — bullets, decisions, outcomes. Filename: `YYYY-MM-DD-topic.md` |
| `projects/`   | Technical reference — commands, bug fixes, config snippets, architecture notes. Filename: `<topic>.md` |
| `research/`   | Broader findings, external links, brainstorming. Filename: `<topic>.md` |

---

## Search discipline (enforced at runtime)

- ✅ `wiki_search(keyword)` is the FIRST tool call for any discovery question
- ✅ ONE follow-up `read_file` if you need more depth — never more
- ✅ Skip `memory/` files older than ~3 days unless the keyword matches
- ❌ Never glob `wiki/**/*.md`
- ❌ Never `list_directory` on paths listed above — quote the map
- ❌ Never run `find ~` / `locate` / `ls ~` / `grep -r ~` — the runtime BLOCKS these
- ❌ Never re-read soul.md or directory.md — they are auto-injected each turn

---

## Self-update rules

After each task, ask yourself:
1. Learned a new command / fix / config? → `write_file` to `projects/<topic>.md`
2. Decision or session summary worth keeping? → `write_file` to `memory/YYYY-MM-DD-topic.md`
3. External finding / link? → `write_file` to `research/<topic>.md`
4. Found a new external path the wiki didn't know? → `remember_path(path, note)`
5. Created a new wiki folder? → update this file

---

## Learned paths

_Auto-appended by `remember_path` when `wiki_search` misses and the user
points the agent at a new location. Future sessions should find these via
`wiki_search` without filesystem walks._
