<!-- FILE_MAP_BEGIN 
<!--
{"file_metadata":{"title":"AGENT-IDE DATABASE COMPATIBILITY PROTOCOL","description":"This document defines the protocol for ensuring database operations are compatible with Agent-IDE patterns, including detection, verification, correction, execution flow, compatibility matrix, success criteria, and testing validation.","last_updated":"2025-07-31","type":"documentation"},"ai_instructions":"Analyze the document to identify logical sections based on the heading hierarchy and content themes. Extract key elements such as code blocks, tables, and important concepts that aid navigation and understanding. Ensure line numbers are accurate and sections do not overlap. Provide clear, concise section names and descriptions that reflect the content. Capture all major headings and relevant subsections, grouping related content logically. Highlight critical code snippets, YAML tables, and query examples that are essential for comprehension and reference.","sections":[{"name":"Introduction and Protocol Overview","description":"Introduces the Agent-IDE database compatibility protocol, its trigger conditions, and primary purpose.","line_start":7,"line_end":11},{"name":"Detect Patterns","description":"Describes how to detect database operation patterns and references to deprecated cognitive schema patterns.","line_start":12,"line_end":17},{"name":"Verify and Correct","description":"Details verification steps and correction rules for search types, parameters, collections, and tool references to ensure compatibility.","line_start":18,"line_end":23},{"name":"Execution Flow","description":"Outlines the sequential process of detection, compatibility checking, auto-correction, and validation testing.","line_start":24,"line_end":28},{"name":"Agent-IDE Compatibility Matrix","description":"Presents supported operations, unsupported patterns, and conversion patterns in structured YAML format to guide compatibility enforcement.","line_start":29,"line_end":54},{"name":"Success Criteria","description":"Lists the criteria that define successful compliance with the Agent-IDE compatibility protocol.","line_start":55,"line_end":60},{"name":"Testing Validation","description":"Provides runtime test commands to verify Agent-IDE startup compatibility and operation correctness.","line_start":61,"line_end":67},{"name":"Runtime Test - Verify Agent-IDE Startup Compatibility","description":"Introduces the runtime test section including tracking and integration details for compatibility validation.","line_start":63,"line_end":87},{"name":"Tracking","description":"Defines the AQL query used to log compatibility checks, validation targets, status, issues, corrections, and timestamps.","line_start":68,"line_end":79},{"name":"Integrates With","description":"Lists related rules, protocols, workflows, and collections that integrate with this compatibility protocol.","line_start":80,"line_end":87}],"key_elements":[{"name":"Execution Flow Diagram","description":"A visual flow representation of the compatibility process steps: detection, checking, correction, and validation.","line":25},{"name":"Supported Operations YAML Table","description":"YAML formatted list of supported search types, collections, operations, and tools for Agent-IDE compatibility.","line":32},{"name":"Unsupported Patterns YAML Table","description":"YAML formatted list of unsupported search types, parameters, collections, and tools that must be avoided.","line":40},{"name":"Conversion Patterns YAML Table","description":"YAML formatted mapping of deprecated search types and parameters to their compatible equivalents.","line":48},{"name":"Testing Validation Bash Commands","description":"Shell commands to perform runtime tests verifying Agent-IDE startup and search operation compatibility.","line":62},{"name":"Tracking AQL Query","description":"AQL insert statement to log compatibility check results, issues, corrections, and timestamps into the metrics collection.","line":69},{"name":"Integration References List","description":"Bullet list of related rules, protocols, workflows, and collections that this protocol integrates with for comprehensive compatibility.","line":81}]}
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
