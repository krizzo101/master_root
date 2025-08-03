# OPSVI Workspace Audit – 2025-08-03 18:44:43 UTC

## Structure

```tree
.
├── ADR
├── README.md
├── apps
│   ├── accf
│   ├── genfilemap
│   └── project-intel
├── docs
├── intake
├── justfile
├── labs
├── libs
│   ├── opsvi-agents
│   ├── opsvi-core
│   ├── opsvi-llm
│   └── opsvi-rag
├── mcp-shell.log
├── ops
├── platform
│   ├── mcp
│   ├── observability
│   └── rag
├── pyproject.toml
├── pyproject.toml.backup
├── pytest.ini
├── ruff.toml
├── scripts
│   └── new_agent_worktree.sh
├── status_report.txt
├── system.status.txt
├── systemd
│   ├── autosave@.service
│   ├── autosave@.timer
│   ├── snapshot@.service
│   └── snapshot@.timer
├── test_file.md
├── tools
│   ├── autosave.sh
│   ├── rag_init.py
│   └── snapshot.sh
└── uv.lock

22 directories, 19 files
```

## pyproject / uv workspace

```toml
[tool.uv.workspace]
members = [
    "libs/*",
    "apps/project-intel",
    "apps/accf",
    "apps/genfilemap",
]
exclude = [
    "platform/*",
    "tools/*",
    "scripts/*",
]
```

## Git

**Status**: On branch AUTOSAVE, up to date with 'origin/AUTOSAVE'
**Untracked files**: .cursor/mcp.json, apps/accf/.cursor/mcp.json

**Recent commits**:
- 0a1cdcd test: add test file to verify IDE Git configuration is working correctly
- c4439b7 Reinitialize repository after fixing .git/ tracking corruption

**Remote**: origin https://github.com/krizzo101/master_root.git

## Timers & Services

```text
Sun 2025-08-03 14:46:30 EDT 2min 12s Sun 2025-08-03 14:35:43 EDT     8min ago autosave@master_root.timer     autosave@master_root.service
Sun 2025-08-03 22:52:51 EDT       8h Sun 2025-08-03 10:40:50 EDT 3h 55min ago snapshot@master_root.timer     snapshot@master_root.service

Failed services:
● autosave@master_root.service loaded failed failed OPSVI Git Autosave Service for master_root
● autosave@opsvi.service       loaded failed failed OPSVI Git Autosave Service for opsvi
● snapshot@master_root.service loaded failed failed OPSVI Git Snapshot Service for master_root
● snapshot@opsvi.service       loaded failed failed OPSVI Git Snapshot Service for opsvi
```

## Docker

```text
Observability stack:
opsvi-grafana          /run.sh                          Up           0.0.0.0:3000->3000/tcp,:::3000->3000/tcp
opsvi-otel-collector   /otelcol --config=/etc/ote ...   Restarting                                           
opsvi-tempo            /tempo -config.file=/etc/t ...   Exit 255                                             

RAG stack:
opsvi-qdrant   ./entrypoint.sh   Up (unhealthy)   0.0.0.0:6333->6333/tcp,:::6333->6333/tcp, 0.0.0.0:6334->6334/tcp,:::6334->6334/tcp

Health check: Qdrant not up
```

## Cursor Rules Validation

```text
Cursor rules directory contains 7 .mdc files:
- 101-cursor-rules-generation-protocol.mdc
- autosave.mdc
- design-quality.mdc
- git-safety.mdc
- index.mdc
- platform-services.mdc
- python-standards.mdc
```

## Ruff & Pytest

```text
Ruff: Found issues (non-zero exit)
Pytest: 5 errors during collection - import issues with ACCF modules and missing dependencies
```

## Observations

* **Systemd services failing**: All autosave and snapshot services are in failed state, indicating timer/service configuration issues
* **Docker stack unhealthy**: Qdrant is unhealthy and Tempo has exited, suggesting platform stack needs attention
* **Test suite broken**: Multiple import errors in ACCF tests due to missing modules and path issues
* **Cursor rules present**: 7 .mdc files exist but validation command produced no output 