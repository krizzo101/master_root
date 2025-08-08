## Template Registry Map

This document maps keys in `libs/templates.yaml` to their purpose and typical usage.

### Python files
- init_py: Package init and exports
- core_init_py: Core module exports
- core_base_py: Base component class template
- config_init_py: Config module exports
- config_settings_py: Pydantic settings for library
- exceptions_init_py: Exceptions module exports
- exceptions_base_py: Exception classes
- utils_helpers_py: Common async/retry/util helpers
- utils_helpers_py_alt: Alternate helper set (optional)
- test_base_py: Base pytest template

### Specialized
- core_services_py: Core service manager
- events_base_py: Event manager + subscription/publish
- state_manager_py: In-memory async state store
- providers_base_py: Provider abstract base
- providers_openai_py: OpenAI provider skeleton (env-driven)
- client_base_py: HTTP client base
- server_base_py: HTTP server base
- auth_base_py: Auth manager base
- datastores_base_py: Vector store interface
- embeddings_providers_py: Embeddings provider interface
- processors_base_py: Document processor interface
- agents_base_py: Agent base
- coordinators_base_py: Coordinator base
- communication_base_py: Communication base
- fs_providers_base_py: File system provider base
- fs_processors_base_py: File processor base
- data_providers_base_py: Data provider base
- orm_base_py: ORM base placeholder
- auth_providers_base_py: Auth provider base
- auth_models_user_py: User model dataclass
- memory_stores_base_py: Memory store base
- cache_manager_py: Cache manager skeleton
- communication_channels_base_py: Channel base
- messages_base_py: Message dataclass
- pipeline_stages_base_py: Pipeline stage base
- orchestrators_base_py: Orchestrator base
- monitoring_metrics_base_py: Metrics base
- tracing_base_py: Tracing base
- security_crypto_base_py: Crypto base
- audit_base_py: Audit base
- orchestration_workflows_base_py: Workflow base
- schedulers_base_py: Scheduler base
- deploy_infrastructure_base_py: Infra base
- environments_base_py: Environments base
- gateway_routers_base_py: Gateway router base
- gateway_middleware_base_py: Gateway middleware base
- prompts_manager_py: Prompt manager

### Config / Docs
- pyproject_toml: Build, deps, tooling
- README_md: Library README with usage and config

Notes
- All keys are rendered via the YAML registry; no .j2 files are used.
- Add new templates by extending `file_templates` in `templates.yaml` and referencing them in `recommended_structure.yaml`.
