Agent Onboarding Guide for Project Intelligence Artifacts

            Purpose
            - This file instructs an agent how to consume the generated context package quickly and safely.

            Core artifacts
            - Primary JSONL: .proj-intel/project_analysis.jsonl
              - Newline-delimited JSON with three record kinds: metadata, collector, collector_item
              - Each line has minimal stable keys; items include a checksum and valid flag
            - Index: .proj-intel/project_analysis.index.json
              - records: line, byte_offset, byte_size, kind, collector, optional identifiers (file_path, name)
              - summary: counts per collector and collector_item
            - Project map (fast): .proj-intel/project_map.yaml
              - One-line-per-file list honoring .gitignore; use for scoping/navigation

            Agent-optimized helpers
            - Reverse index: .proj-intel/reverse_index.json
              - O(1) path -> list of JSONL byte ranges for items about that path
            - Symbol index: .proj-intel/symbol_index.json
              - O(1) symbol/class -> file/offset hint for selective reads
            - Blocks index: .proj-intel/blocks.index.json
              - Merge adjacent byte ranges to minimize random seeks
            - Shards:
              - File elements (min): .proj-intel/file_elements.min.jsonl  (path, line_count, fn_count, class_count, import_count, content_hash)
              - File elements (full items): .proj-intel/file_elements.jsonl
              - Agent architecture items: .proj-intel/agent_architecture.jsonl
            - Manifest: proj_intel_manifest.json (lists primary, shards, indices)

            Recommended ingestion order
            1) Read proj_intel_manifest.json; verify schema_version and list of shards/indices
            2) Load project_analysis.index.json to build in-memory maps for selective reads
            3) For quick triage, stream file_elements.min.jsonl and rank files by fn/class/import counts
            4) Use reverse_index.json for O(1) path -> JSONL byte range; read only those ranges from project_analysis.jsonl
            5) To enumerate classes/agents, stream agent_architecture.jsonl or use the index to pull only agent items
            6) Use symbol_index.json for symbol -> file/path lookup, then reverse_index/JSONL offsets for details
            7) Use blocks.index.json to group adjacent reads when fetching many items

            Performance guidance
            - Always stream; do not load project_analysis.jsonl entirely into memory
            - Prefer byte_offset/byte_size from the index for direct seeks
            - Batch nearby offsets to reduce I/O; respect blocks.index.json
            - Parse lines independently; skip any with valid=false or checksum mismatch

            Collector semantics (high level)
            - FileElementsCollector: per-file functions/classes/imports with content_hash
            - AgentArchitectureCollector: per discovered class/agent (file_path, name, bases, methods, docstring head)
            - EntryPointsCollector: CLI/module entries (cli.py, __main__.py, main/run/app)
            - DependenciesCollector: intra-project import edges summary (edge_count, most_imported, cycles)
            - ApiEndpointsCollector: HTTP endpoints (FastAPI/Flask) when present
            - DataModelsCollector: Pydantic/SQLAlchemy/dataclass models and fields
            - ConfigEnvCollector: config files list and extracted env var names
            - TestsTopologyCollector: test files and heuristic target mapping
            - DepsExtendedCollector: third-party imports summary and version constraints (from requirements)
            - QualityQuickCollector: metrics/complexity/lint summary (best-effort)
            - CallGraphCollector: coarse function-call names per file and imports
            - ChangesetCollector: added/removed/modified since previous build (uses min file elements + manifest)

            Safety & assumptions
            - .gitignore and dot-directories were honored during collection
            - Some collectors may set data.partial=true if internal time budgets were reached
            - JSONL items include a checksum for integrity; verify when needed
            - Logs are in pi.debug.log; do not print them to your console context

            Minimal access patterns (examples)
            - Fetch all FileElements items by line: filter index.records for collector=="FileElementsCollector" then read only those lines
            - Fetch by path: read reverse_index.json[path] -> seek project_analysis.jsonl at byte_offset/size for each entry
            - Fetch agent classes: stream agent_architecture.jsonl or pull collector_item lines for AgentArchitectureCollector via index
