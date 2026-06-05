# Decyphertek.ai Wiki — Directory

**WIKI_ROOT (source):** `~/Documents/git/decyphertek-ai/wiki/`
**Runtime root:**       `~/.decyphertek.ai/`

> Read this map FIRST. Pick ONE targeted file. Do not glob `/**/*`. Do not walk the filesystem for paths already listed below.

---

## Read Order (every task, no exceptions)

1. `soul.md`       — identity + rules (read once at startup)
2. `directory.md`  — this file (the map)
3. ONE file from `projects/`, `memory/`, or `research/` matching the task keyword
4. Filesystem / codebase search = LAST resort

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

## Related repos (`~/Documents/git/`)

```
agent-store/                 ← source for the .agent binaries (adminotaur, agent-builder, mcp-builder)
mcp-store/                   ← source for MCP skills
app-store/                   ← source for supporting apps (chromadb, etc.)
```

---

## Folder Purpose (where notes go)

| Folder        | What goes there                                                     |
|---------------|---------------------------------------------------------------------|
| `memory/`     | Per-session conversation summaries — bullet points, decisions, outcomes. Filename: `YYYY-MM-DD-topic.md` |
| `projects/`   | Technical reference — commands, bug fixes, config snippets, architecture notes. Filename: `<topic>.md` |
| `research/`   | Broader findings, external links, brainstorming. Filename: `<topic>.md` |

---

## Search Discipline (token-saving)

- ✅ Read `soul.md` + `directory.md` once per session
- ✅ Read ONE file from one folder that matches the topic keyword
- ✅ Skip `memory/` entirely if no filename matches the keyword
- ✅ Skip memory files older than ~3 days unless explicitly relevant
- ❌ Never glob `wiki/**/*.md`
- ❌ Never read multiple memory files "just in case"
- ❌ Never run `list_directory` on paths listed in this map — answer from the map
- ❌ Never read empty/placeholder README files repeatedly

---

## Self-Update Rules

After each task, ask:
1. Learned a new command / fix / config? → write `projects/<topic>.md`
2. Decision or session summary worth keeping? → write `memory/YYYY-MM-DD-topic.md`
3. External finding / link? → write `research/<topic>.md`
4. Created a new folder? → update this file
