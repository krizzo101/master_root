<!-- FILE_MAP_BEGIN 
<!--
{"file_metadata":{"title":"AGENT-IDE DATABASE COMPATIBILITY PROTOCOL","description":"This document defines the protocol for ensuring database operations are compatible with the Agent-IDE environment by detecting, verifying, correcting patterns, and validating compatibility through testing and tracking.","last_updated":"2025-07-31","type":"documentation"},"ai_instructions":"Analyze the document to identify its hierarchical structure and logical sections based on headings and content themes. Extract key elements such as code blocks, tables, and important concepts that aid navigation and comprehension. Ensure all line numbers are 1-indexed and precisely mapped without overlap. Create descriptive section names reflecting content purpose and group related subsections logically. Provide a clear file map with sections and key elements to facilitate efficient navigation and understanding of the Agent-IDE database compatibility protocol.","sections":[{"name":"Introduction and Protocol Overview","description":"Introduces the Agent-IDE database compatibility protocol, its trigger conditions, and primary purpose.","line_start":7,"line_end":11},{"name":"Detect Patterns","description":"Describes the detection of database operation patterns, workflow files, protocol files, and deprecated schema references.","line_start":12,"line_end":17},{"name":"Verify and Correct","description":"Details the verification steps and correction rules for search types, parameters, collections, and tool references to ensure compatibility.","line_start":18,"line_end":23},{"name":"Execution Flow","description":"Outlines the sequential process of detection, compatibility checking, auto-correction, and validation testing.","line_start":24,"line_end":28},{"name":"Agent-IDE Compatibility Matrix","description":"Presents the compatibility matrix including supported operations, unsupported patterns, and conversion patterns for database operations.","line_start":29,"line_end":54},{"name":"Success Criteria","description":"Lists the criteria that define successful compatibility adherence for database operations and tool usage.","line_start":55,"line_end":60},{"name":"Testing Validation","description":"Provides runtime test commands to verify Agent-IDE startup compatibility and operation health.","line_start":61,"line_end":67},{"name":"Runtime Test - Verify Agent-IDE Startup Compatibility","description":"Introduces the runtime test section and its purpose for compatibility verification.","line_start":63,"line_end":63},{"name":"Tracking","description":"Defines the AQL insert statement used to track compatibility checks, validation targets, status, issues, corrections, and timestamps.","line_start":68,"line_end":79},{"name":"Integration References","description":"Lists related rules, protocols, workflows, and collections integrated with this compatibility protocol.","line_start":80,"line_end":87},{"name":"Protocol Summary","description":"Summarizes the protocol's purpose in ensuring compatibility through validation and automatic correction to prevent runtime failures.","line_start":88,"line_end":88}],"key_elements":[{"name":"Execution Flow Diagram","description":"A symbolic flow representation of the detection, compatibility check, auto-correction, and validation test steps.","line":25},{"name":"Supported Operations YAML Block","description":"YAML formatted list of supported search types, collections, operations, and tools compatible with Agent-IDE.","line":32},{"name":"Unsupported Patterns YAML Block","description":"YAML formatted list of unsupported search types, parameters, collections, and tools that are deprecated or incompatible.","line":40},{"name":"Conversion Patterns YAML Block","description":"YAML formatted mapping of deprecated search types and parameters to their compatible equivalents or conversions.","line":48},{"name":"Testing Validation Bash Commands","description":"Shell commands to perform runtime tests verifying Agent-IDE startup and search operation compatibility.","line":62},{"name":"Tracking AQL Insert Statement","description":"AQL query to insert compatibility check results, including validation targets, status, issues, corrections, and timestamps into metrics.","line":69},{"name":"Integration References List","description":"Bullet list of related rules, protocols, workflows, and collections integrated with the compatibility protocol.","line":80}]}
-->
<!-- FILE_MAP_END -->

# AGENT-IDE DATABASE COMPATIBILITY PROTOCOL

**TRIGGER**: Database operation development, workflow creation, tool integration
**PURPOSE**: Ensure all database operations use Agent-IDE compatible patterns

## DETECT PATTERNS
- Database operation definitions (search, modify, manage)
- Workflow files with mcp_cognitive_tools_arango operations
- Protocol files with database examples
- Any references to deprecated cognitive schema patterns

## VERIFY & CORRECT
1. **Search Type Validation**: IF database search → VERIFY search_type ∈ [content, type, tags, date_range, id, recent] → IF NOT replace with compatible type
2. **Parameter Compatibility**: IF search operation → VERIFY no [document_type, min_quality, quality_field] parameters → IF NOT remove/convert parameters
3. **Collection Validation**: IF database operation → VERIFY collection ∈ [research_docs, heuristics, metrics, rules, modules, tasks, branches, ide_state, user_prefs] → IF NOT update to Agent-IDE collections
4. **Tool Reference Check**: IF tool usage → VERIFY uses mcp_cognitive_tools_arango_* → IF NOT update from mcp_multi_modal_db_*

## EXECUTION FLOW
```
[OPERATION_DETECT] → [COMPATIBILITY_CHECK] → [AUTO_CORRECT] → [VALIDATION_TEST]
```

## AGENT-IDE COMPATIBILITY MATRIX

### ✅ SUPPORTED OPERATIONS
```yaml
Search Types: [content, type, tags, date_range, id, recent]
Collections: [research_docs, heuristics, metrics, rules, modules, tasks, branches, ide_state, user_prefs]
Operations: [insert, update, delete, upsert]
Tools: [mcp_cognitive_tools_arango_search, mcp_cognitive_tools_arango_modify, mcp_cognitive_tools_arango_manage]
```

### ❌ UNSUPPORTED PATTERNS
```yaml
Search Types: [quality, related, semantic]
Parameters: [document_type, min_quality, quality_field, reference_id]
Collections: [cognitive_concepts, agent_memory, semantic_relationships, intelligence_analytics]
Tools: [mcp_multi_modal_db_*, old cognitive tools]
```

### 🔄 CONVERSION PATTERNS
```yaml
search_type: "quality" → search_type: "content" + quality keywords
search_type: "related" → search_type: "content" + relationship keywords
document_type: "X" → content: "... X ..." (incorporate into content search)
min_quality: N → Use content-based filtering with quality keywords
```

## SUCCESS CRITERIA
- ✅ All database operations use supported Agent-IDE patterns
- ✅ No deprecated tool references in workflows or protocols
- ✅ Search operations use only supported search_type values
- ✅ Insert operations use content_type instead of document_type

## TESTING VALIDATION
```bash
# Runtime Test - Verify Agent-IDE startup compatibility
mcp_cognitive_tools_arango_manage --action health
mcp_cognitive_tools_arango_search --search_type content --collection research_docs --content "test" --limit 1
```

## TRACKING
```aql
INSERT {
  type: "compatibility_check",
  validation_target: @file_or_operation,
  compatibility_status: @pass_fail,
  issues_found: @issue_list,
  corrections_applied: @correction_list,
  timestamp: DATE_NOW()
} INTO metrics
```

## INTEGRATES WITH
- **Rule 600-graph-database-interaction**: Database operation standards
- **Protocol database-operation**: Core database usage patterns
- **Workflow 00-startup**: Startup compatibility validation
- **Collection research_docs**: Documentation of compatibility requirements

This protocol ensures Agent-IDE database compatibility through proactive validation and automatic correction of deprecated patterns, preventing runtime failures and ensuring seamless agent operation.
