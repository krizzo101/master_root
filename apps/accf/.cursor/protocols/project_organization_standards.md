<!-- FILE_MAP_BEGIN 
<!--
{"file_metadata":{"title":"PROJECT ORGANIZATION STANDARDS","description":"Defines mandatory directory structures, rules, enforcement mechanisms, migration strategies, and compliance monitoring to ensure consistent project organization.","last_updated":"2025-07-31","type":"documentation"},"ai_instructions":"Analyze the document to identify major thematic sections reflecting project organization standards, directory structures, rules, enforcement, migration, and compliance. Focus on grouping related subsections into broader logical sections for efficient navigation. Extract key elements such as directory structure examples, code blocks illustrating import standards, and lists of rules or criteria. Ensure line numbers are precise and sections do not overlap. Provide a clear, navigable map that aids understanding of the document's purpose and structure.","sections":[{"name":"Introduction and Objective","description":"Overview of the project organization standards including rule ID, priority, enforcement, last update, and the primary objective of the document.","line_start":7,"line_end":15},{"name":"Mandatory Directory Structure","description":"Detailed mandatory directory layout including root level restrictions, source code organization, configuration management, documentation organization, data and artifacts, and archive organization.","line_start":16,"line_end":93},{"name":"Mandatory Rules","description":"Rules governing file placement, naming conventions, import path standards, and cleanup requirements to enforce consistent project organization.","line_start":94,"line_end":125},{"name":"Enforcement Mechanisms","description":"Mechanisms to enforce the standards including pre-commit rules, agent operation rules, and migration safety rules.","line_start":126,"line_end":146},{"name":"Current State Analysis","description":"Analysis of the current project state highlighting identified problems and breaking dependencies that necessitate reorganization.","line_start":147,"line_end":161},{"name":"Migration Strategy","description":"Stepwise strategy for migrating to the new project organization including infrastructure preparation, stopping active processes, migrating core applications, reorganizing artifacts and documentation, and updating dependencies.","line_start":162,"line_end":193},{"name":"Compliance Monitoring","description":"Processes for ensuring ongoing compliance through automated checks and manual reviews.","line_start":194,"line_end":207},{"name":"Success Criteria","description":"Criteria defining successful adherence to the project organization standards and effective migration.","line_start":208,"line_end":218},{"name":"Closing Reminder","description":"Final mandatory reminder emphasizing the importance of compliance with the standards to prevent project failure.","line_start":219,"line_end":225}],"key_elements":[{"name":"Root Level Directory Structure Example","description":"Code block illustrating the restricted root level directory contents and prohibited file types.","line":18},{"name":"Source Code Directory Structure Example","description":"Code block showing the organization of source code under src/ with applications, shared libraries, and tools.","line":29},{"name":"Configuration Management Directory Structure Example","description":"Code block depicting configuration directories separated by environment and templates.","line":55},{"name":"Documentation Directory Structure Example","description":"Code block outlining the organization of documentation into API, architecture, deployment, development, user guides, and changelog.","line":64},{"name":"Data and Artifacts Directory Structure Example","description":"Code block showing data directories for artifacts, backups, logs, and temporary files with date-based organization.","line":75},{"name":"Archive Directory Structure Example","description":"Code block illustrating archive directories for projects, deprecated code, and migration history.","line":86},{"name":"Import Path Standards Code Block","description":"Python code block demonstrating correct relative imports from src/ and incorrect direct file imports.","line":110},{"name":"Mandatory File Placement Rules List","description":"Numbered list specifying where different types of files must be placed within the project structure.","line":96},{"name":"Naming Conventions List","description":"Bullet list detailing naming conventions for modules, files, artifacts, logs, and archives.","line":103},{"name":"Cleanup Requirements List","description":"Numbered list describing rules for auto-deletion and archiving of temporary files, logs, artifacts, and debug files.","line":120},{"name":"Pre-Commit Rules List","description":"Checklist of rules enforced before commits to ensure compliance with project organization standards.","line":128},{"name":"Agent Operation Rules List","description":"Numbered list of operational rules agents must follow regarding file creation, imports, cleanup, and file placement.","line":135},{"name":"Migration Safety Rules List","description":"Numbered list of safety checks and procedures to follow during file migration to maintain functionality and documentation.","line":141},{"name":"Identified Problems List","description":"Numbered list outlining key issues in the current project structure necessitating reorganization.","line":149},{"name":"Breaking Dependencies List","description":"Bullet list describing active processes and dependency issues complicating the current project structure.","line":156},{"name":"Migration Phases Lists","description":"Numbered lists detailing tasks for each phase of the migration strategy from infrastructure preparation to testing and validation.","line":164},{"name":"Automated Checks List","description":"Bullet list of automated compliance checks including git hooks and directory audits.","line":196},{"name":"Manual Reviews List","description":"Bullet list of manual compliance activities such as audits and architecture reviews.","line":202},{"name":"Success Criteria List","description":"Numbered list defining measurable outcomes for successful project organization and migration.","line":208}]}
-->
<!-- FILE_MAP_END -->

# PROJECT ORGANIZATION STANDARDS
**Rule ID**: 001-project-organization-standards
**Priority**: CRITICAL
**Enforcement**: MANDATORY for all agent operations
**Last Updated**: 2025-06-28

## 🎯 **OBJECTIVE**
Establish and enforce consistent project organization standards to prevent the chaotic file distribution that has plagued this project.

## 📁 **MANDATORY DIRECTORY STRUCTURE**

### **Root Level - RESTRICTED**
```
agent_world/
├── README.md                    # Project overview ONLY
├── docker-compose.yml          # Primary orchestration ONLY
├── .gitignore                  # Git configuration ONLY
├── .editorconfig              # Editor configuration ONLY
└── package.json               # Node dependencies ONLY
```
**❌ PROHIBITED**: Python files, JSON artifacts, log files, debug scripts, temporary files

### **Source Code Organization**
```
src/
├── applications/              # Live production applications
│   ├── specstory_intelligence/  # SpecStory processing system
│   │   ├── __init__.py
│   │   ├── pipeline.py         # Main processing engine
│   │   ├── database.py         # Database integration
│   │   ├── config.py          # Configuration management
│   │   └── requirements.txt    # Dependencies
│   └── agent_hub/             # Agent hub system
│       ├── __init__.py
│       ├── server.py          # FastAPI server
│       ├── agents/            # Agent implementations
│       ├── schemas/           # Data schemas
│       └── requirements.txt   # Dependencies
├── shared/                    # Shared libraries and utilities
│   ├── database/              # Database utilities
│   ├── logging/               # Logging utilities
│   └── validation/            # Validation utilities
└── tools/                     # Development and maintenance tools
    ├── migration/             # Migration scripts
    ├── testing/               # Test utilities
    └── deployment/            # Deployment scripts
```

### **Configuration Management**
```
config/
├── production/                # Production configurations
├── development/               # Development configurations
├── testing/                   # Testing configurations
└── templates/                 # Configuration templates
```

### **Documentation Organization**
```
docs/
├── api/                       # API documentation
├── architecture/              # Architecture decisions and diagrams
├── deployment/                # Deployment guides
├── development/               # Development guides
├── user/                      # User guides and tutorials
└── CHANGELOG.md               # Project changelog
```

### **Data and Artifacts**
```
data/
├── artifacts/                 # Generated artifacts
│   └── YYYY-MM-DD/           # Date-organized artifacts
├── backups/                   # Database backups
├── logs/                      # Application logs
│   └── YYYY-MM-DD/           # Date-organized logs
└── tmp/                       # Temporary files (auto-cleanup)
```

### **Archive Organization**
```
archive/
├── YYYY-MM-DD_project-name/   # Archived projects by date
├── deprecated/                # Deprecated but referenced code
└── migration-history/         # Record of organizational changes
```

## 🔒 **MANDATORY RULES**

### **File Placement Rules**
1. **Source Code**: MUST go in `src/` with proper module structure
2. **Artifacts**: MUST go in `data/artifacts/YYYY-MM-DD/`
3. **Logs**: MUST go in `data/logs/YYYY-MM-DD/`
4. **Documentation**: MUST go in `docs/` with proper categorization
5. **Configuration**: MUST go in `config/` with environment separation

### **Naming Conventions**
- **Modules**: snake_case (e.g., `specstory_intelligence`)
- **Files**: snake_case.py (e.g., `database_integration.py`)
- **Artifacts**: descriptive_name_YYYY-MM-DD_HH-MM.ext
- **Logs**: application_name_YYYY-MM-DD.log
- **Archives**: YYYY-MM-DD_descriptive-name

### **Import Path Standards**
```python
# ✅ CORRECT - Relative to src/
from applications.specstory_intelligence.pipeline import SpecStoryProcessor
from shared.database.client import DatabaseClient

# ❌ WRONG - Direct file imports
from specstory_intelligence_pipeline import SpecStoryProcessor
```

### **Cleanup Requirements**
1. **Temporary files**: Auto-delete after 24 hours
2. **Log files**: Auto-archive after 30 days
3. **Artifacts**: Keep versioned, archive old versions after 90 days
4. **Debug files**: NEVER commit to git

## 🚨 **ENFORCEMENT MECHANISMS**

### **Pre-Commit Rules**
- ✅ All source files in `src/`
- ✅ No Python files in root directory
- ✅ No artifacts in git (use .gitignore)
- ✅ Proper module structure
- ✅ Required `__init__.py` files

### **Agent Operation Rules**
1. **BEFORE creating files**: Check this standard for proper location
2. **BEFORE imports**: Use proper import paths from `src/`
3. **AFTER operations**: Clean up temporary files
4. **NEVER**: Place files outside designated directories

### **Migration Safety Rules**
1. **Check dependencies**: Before moving files, check import statements
2. **Update imports**: After moving files, update all import paths
3. **Test functionality**: Verify nothing breaks after reorganization
4. **Document changes**: Record all movements in migration log

## 📋 **CURRENT STATE ANALYSIS**

### **Identified Problems**
1. **Root Directory Pollution**: 47+ Python/JSON files in root
2. **Duplicate Systems**: Multiple versions of specstory and agent_hub
3. **Scattered Dependencies**: Import statements across multiple locations
4. **No Version Control**: Unclear which files are "current"
5. **Mixed Concerns**: Source, artifacts, and logs intermixed

### **Breaking Dependencies**
- **Active Processes**: MCP servers and pipeline currently running
- **Import Chains**: Files importing from current chaotic structure
- **Configuration**: Hardcoded paths in setup scripts
- **Documentation**: References to old file locations

## 🔄 **MIGRATION STRATEGY**

### **Phase 1: Prepare Infrastructure**
1. Create new directory structure
2. Update .gitignore for new organization
3. Create migration mapping document
4. Backup current state

### **Phase 2: Stop Active Processes**
1. Gracefully stop MCP servers
2. Stop SpecStory pipeline
3. Document running configurations

### **Phase 3: Migrate Core Applications**
1. Move SpecStory intelligence system to `src/applications/specstory_intelligence/`
2. Move agent_hub to `src/applications/agent_hub/`
3. Update import statements
4. Update configuration files

### **Phase 4: Reorganize Artifacts and Documentation**
1. Move artifacts to `data/artifacts/`
2. Organize documentation in `docs/`
3. Archive old versions in `archive/`
4. Clean up root directory

### **Phase 5: Update Dependencies and Test**
1. Update all import statements
2. Update setup scripts
3. Test all functionality
4. Restart services
5. Validate operations

## ⚖️ **COMPLIANCE MONITORING**

### **Automated Checks**
- Git pre-commit hooks for structure validation
- Periodic directory audits
- Import path validation
- File placement verification

### **Manual Reviews**
- Weekly organizational audits
- Quarterly architecture reviews
- Migration impact assessments
- Compliance reporting

## 🎯 **SUCCESS CRITERIA**
1. ✅ All source code properly organized in `src/`
2. ✅ No files in root except authorized ones
3. ✅ All imports using proper module paths
4. ✅ Artifacts properly timestamped and organized
5. ✅ Active processes working after migration
6. ✅ Clear documentation of all changes

---

**REMEMBER**: This standard is MANDATORY. All agents must consult and follow these rules before any file operations. Non-compliance will result in organizational chaos and project failure.
