<!-- FILE_MAP_BEGIN 
<!--
{"file_metadata":{"title":"PROJECT ORGANIZATION STANDARDS","description":"Defines mandatory directory structures, rules, enforcement mechanisms, migration strategies, and compliance monitoring to ensure consistent project organization and prevent chaotic file distribution.","last_updated":"2025-07-31","type":"documentation"},"ai_instructions":"Analyze the document by focusing on major thematic sections such as objectives, directory structures, mandatory rules, enforcement mechanisms, current state analysis, migration strategy, compliance monitoring, and success criteria. Use the heading hierarchy to group related subsections into broader logical sections. Identify key elements including code blocks illustrating directory layouts and import examples, lists of rules and procedures, and critical concepts like enforcement and migration phases. Ensure line numbers are precise and sections do not overlap. Provide a navigable structure that aids understanding of project organization standards and their enforcement.","sections":[{"name":"Introduction and Objective","description":"Introduces the project organization standards, including rule ID, priority, enforcement status, last update, and the primary objective of establishing consistent project organization.","line_start":7,"line_end":15},{"name":"Mandatory Directory Structure","description":"Details the required directory layout for the project, including root level restrictions, source code organization, configuration management, documentation organization, data and artifacts, and archive organization, supported by illustrative code blocks.","line_start":16,"line_end":92},{"name":"Mandatory Rules","description":"Specifies mandatory rules for file placement, naming conventions, import path standards with code examples, and cleanup requirements to maintain project organization integrity.","line_start":93,"line_end":124},{"name":"Enforcement Mechanisms","description":"Describes the mechanisms to enforce the standards including pre-commit rules, agent operation rules, and migration safety rules to ensure compliance and safe transitions.","line_start":125,"line_end":145},{"name":"Current State Analysis","description":"Analyzes the existing problems in the project structure such as root directory pollution, duplicate systems, scattered dependencies, and breaking dependencies affecting active processes and configurations.","line_start":146,"line_end":160},{"name":"Migration Strategy","description":"Outlines a phased approach to migrate the project to the new organization standards, including infrastructure preparation, stopping active processes, migrating core applications, reorganizing artifacts and documentation, and updating dependencies with testing.","line_start":161,"line_end":192},{"name":"Compliance Monitoring","description":"Defines automated and manual compliance checks such as git hooks, directory audits, import validation, and organizational reviews to ensure ongoing adherence to standards.","line_start":193,"line_end":206},{"name":"Success Criteria","description":"Lists the criteria for successful implementation of the standards, including proper source code organization, authorized root files, correct imports, artifact management, operational active processes, and clear documentation.","line_start":207,"line_end":218},{"name":"Closing Reminder","description":"Final mandatory reminder emphasizing the importance of compliance with the standards to avoid organizational chaos and project failure.","line_start":219,"line_end":224}],"key_elements":[{"name":"Root Level Directory Structure Code Block","description":"Code block illustrating the restricted root level directory contents and prohibited file types.","line":18},{"name":"Source Code Organization Code Block","description":"Code block showing the detailed source code directory layout including applications, shared libraries, and tools.","line":29},{"name":"Configuration Management Code Block","description":"Code block depicting the configuration directory structure separated by environment.","line":55},{"name":"Documentation Organization Code Block","description":"Code block outlining the documentation directory structure with categorized guides and changelog.","line":64},{"name":"Data and Artifacts Directory Code Block","description":"Code block showing the organization of data artifacts, backups, logs, and temporary files.","line":75},{"name":"Archive Organization Code Block","description":"Code block illustrating the archive directory structure for projects, deprecated code, and migration history.","line":86},{"name":"Import Path Standards Code Block","description":"Python code block demonstrating correct relative imports from src/ and incorrect direct file imports.","line":110},{"name":"Mandatory File Placement Rules List","description":"Numbered list specifying where different types of files must be placed within the project structure.","line":96},{"name":"Naming Conventions List","description":"Bullet list defining naming conventions for modules, files, artifacts, logs, and archives.","line":103},{"name":"Cleanup Requirements List","description":"Numbered list outlining rules for auto-deletion and archiving of temporary files, logs, artifacts, and debug files.","line":120},{"name":"Enforcement Rules Lists","description":"Lists under pre-commit, agent operation, and migration safety rules detailing mandatory checks and procedures.","line":128},{"name":"Current State Problems List","description":"Numbered list identifying major issues in the current project organization.","line":149},{"name":"Breaking Dependencies List","description":"Bullet list describing dependency challenges affecting active processes and configurations.","line":156},{"name":"Migration Phases Lists","description":"Numbered lists describing detailed steps for each migration phase from infrastructure preparation to testing and validation.","line":164},{"name":"Compliance Monitoring Lists","description":"Lists of automated checks and manual reviews to ensure ongoing compliance with standards.","line":196},{"name":"Success Criteria Checklist","description":"Numbered checklist of criteria defining successful adoption of the project organization standards.","line":208}]}
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
