## Structure Definition Overview

`recommended_structure.yaml` defines:
- Template system reference (registry file, engine label)
- Anchors for reusable template definitions (e.g., base_init)
- Project/category/library/component/file level contexts
- Library categories and responsibilities
- Library types with directory structures
- Library-specific files and their template keys

### Anchors
- base_init -> init_py
- base_core_init -> core_init_py
- base_config_init -> config_init_py
- base_exceptions_init -> exceptions_init_py
- base_pyproject -> pyproject_toml
- base_readme -> README_md

### Library types
- core: core, config, exceptions, utils, tests
- service: + providers, schemas
- rag: + datastores, embeddings, processors
- manager: + coordinators, schedulers

### Adding files
1) Add a new template key to `templates.yaml`
2) Reference it under the target library in `recommended_structure.yaml`
3) Run generator in strict mode to validate

### Validation
The generator validates template references up front. CI runs a sandbox generation to ensure all files are present.

