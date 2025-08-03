<!-- FILE_MAP_BEGIN 
<!--
{"file_metadata":{"title":"ACCF Codebase Migration Summary","description":"Summary of the migration of the ACCF codebase to a modular, standards-compliant structure including major changes, standards compliance, legacy files removed, and next steps.","last_updated":"2025-07-31","type":"documentation"},"ai_instructions":"Analyze the document to identify its purpose as a migration summary for developers and maintainers. Use the heading hierarchy to create logical, non-overlapping sections reflecting major topics: overview, major changes, standards compliance, legacy files removed, and next steps. Capture key elements such as code blocks listing directory names and files removed, bullet lists describing changes and compliance details, and references to legacy and new modules. Ensure line numbers are 1-indexed and precise, covering all content including blank lines. Provide descriptive section names and element descriptions to facilitate navigation and comprehension within the ACCF project context.","sections":[{"name":"Document Title","description":"Title of the document indicating the overall subject of the migration summary.","line_start":7,"line_end":7},{"name":"Overview","description":"Introduction summarizing the purpose and scope of the ACCF codebase migration.","line_start":9,"line_end":11},{"name":"Major Changes","description":"Detailed list of significant modifications made during the migration including file merges, integrations, and directory restructuring.","line_start":12,"line_end":24},{"name":"Standards Compliance","description":"Explanation of the coding and documentation standards adhered to in the migrated codebase.","line_start":26,"line_end":29},{"name":"Legacy Files Removed","description":"List of legacy files and directories that were removed as part of the migration process.","line_start":31,"line_end":33},{"name":"Next Steps","description":"Guidance on future development and reference to the migration document for historical context.","line_start":35,"line_end":37}],"key_elements":[{"name":"Directory List in Major Changes","description":"Bullet list enumerating the main directories in the new codebase structure.","line":22},{"name":"Legacy Agent Files Merge","description":"Bullet point describing the merging of legacy agent files into new modular capability agent modules.","line":13},{"name":"Event Routing and Intent Bus Integration","description":"Bullet point describing integration of event routing and intent bus logic into orchestrator module.","line":14},{"name":"Knowledge Graph Integration","description":"Bullet point describing integration of knowledge graph logic into capabilities.","line":15},{"name":"Security Logic Integration","description":"Bullet point describing integration of security logic into the security agent module.","line":16},{"name":"Feedback, Subscription, and Task Market Integration","description":"Bullet point describing integration of feedback, subscription, and task market logic into respective modules.","line":17},{"name":"Removal of Legacy Test Files","description":"Bullet point noting removal of all legacy test files and directories after migration.","line":18},{"name":"Standards Compliance Details","description":"Bullet points listing adherence to ACCF documentation, ADRs, PEP8 compliance, and Python package structure.","line":27},{"name":"Legacy Files Removed List","description":"Bullet list specifying legacy directories and standalone files removed during migration.","line":32},{"name":"Next Steps Guidance","description":"Bullet points outlining future development directions and reference usage of this document.","line":36}]}
-->
<!-- FILE_MAP_END -->

# ACCF Codebase Migration Summary

## Overview
This document summarizes the migration of the ACCF codebase to a modular, standards-compliant structure. All legacy files and directories have been reviewed, merged, refactored, or deleted as appropriate.

## Major Changes

- All legacy agent files in `agents/` have been merged into new modular capability agent modules in `capabilities/`.
- Event routing and intent bus logic from `event_router.py` and `intent_bus.py` have been integrated into `orchestrator/orchestrator.py`.
- Knowledge graph logic from `knowledge_graph.py` has been integrated into `capabilities/knowledge_agent.py`.
- Security logic from `security.py` has been integrated into `capabilities/security_agent.py`.
- Feedback, subscription, and task market logic have been integrated into `capabilities/feedback_agent.py`, `orchestrator/subscription_engine.py`, and `orchestrator/task_market.py` respectively.
- All legacy test files and directories have been removed after migration.
- The codebase now consists of the following main directories:
  - `agent_base/`
  - `capabilities/`
  - `orchestrator/`
  - `registry/`

## Standards Compliance
- All modules follow ACCF documentation, ADRs, and output templates.
- Python code is PEP8-compliant and uses snake_case naming.
- All directories are Python packages (`__init__.py` present).

## Legacy Files Removed
- All files in `agents/`, `tests/`, and other legacy directories.
- Standalone files: `event_router.py`, `intent_bus.py`, `knowledge_graph.py`, `security.py`, `feedback_agent.py`, `subscription_engine.py`, `task_market.py`.

## Next Steps
- Continue development using the new modular structure.
- Refer to this document for historical context on the migration.
