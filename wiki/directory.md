# Decyphertek.ai — Directory

Environment map. Lists folder paths and what each contains.

---

## Runtime — `~/.decyphertek.ai/`

| Path                              | Contents                                                  |
|-----------------------------------|-----------------------------------------------------------|
| `agent-store/adminotaur/`         | `adminotaur.agent` — supervisor agent (this one)          |
| `agent-store/agent-builder/`      | `agent-builder.agent` — builds new agents                 |
| `agent-store/mcp-builder/`        | `mcp-builder.agent` — builds new MCPs                     |
| `agent-store/workers.yaml`        | Agent registry: versions, release URLs, credential keys   |
| `mcp-store/rag-chat/`             | RAG chat MCP skill                                        |
| `mcp-store/web-search/`           | Web search MCP skill                                      |
| `mcp-store/worldnewsapi/`         | World News API MCP skill                                  |
| `mcp-store/skills.yaml`           | MCP skill registry                                        |
| `app-store/chromadb/`             | `chromadb.app` — vector DB for RAG / long-term memory     |
| `configs/ai-config.yaml`          | Model, provider, temperature                              |
| `configs/cdb-config.yaml`         | ChromaDB configuration                                    |
| `configs/slash-commands.yaml`     | CLI slash command definitions                             |
| `creds/`                          | Encrypted credentials (Ansible Vault `.vault` files)      |
| `keys/.vault_pass`                | Master vault password (chmod 600)                         |
| `bin/`                            | Installed binaries                                        |
| `versions.yaml`                   | Local installed versions of agents and MCPs               |
| `.password_hash`                  | Master password hash                                      |

## Source — `~/Documents/git/decyphertek-ai/`

| Path                  | Contents                                                              |
|-----------------------|-----------------------------------------------------------------------|
| `cli/cli-ai.py`       | Main CLI — slash commands, agent orchestration                        |
| `cli/configs/`        | Shipped default configs                                               |
| `wiki/soul.md`        | Agent identity and behavior contract                                  |
| `wiki/directory.md`   | This file — environment map                                           |
| `wiki/memory/`        | Per-turn conversation notes (`YYYY-MM-DD-HHMMSS-<slug>.md`)           |
| `wiki/projects/`      | Durable technical notes — commands, fixes, configs (`<topic>.md`)     |
| `wiki/research/`      | Broader findings, external references (`<topic>.md`)                  |
| `install.sh`          | Installer                                                             |
| `uninstall.sh`        | Uninstaller                                                           |
| `README.md`           | Project README                                                        |

## Related source repos — `~/Documents/git/`

| Path             | Contents                                                                |
|------------------|-------------------------------------------------------------------------|
| `agent-store/`   | Source for the `.agent` binaries (adminotaur, agent-builder, mcp-builder) |
| `mcp-store/`     | Source for MCP skills                                                   |
| `app-store/`     | Source for supporting apps (chromadb, etc.)                             |

---

## Learned paths

_Auto-appended by `lookup_path` and `remember_path` when a path is discovered
outside the map above. Future sessions find these without filesystem walks._
