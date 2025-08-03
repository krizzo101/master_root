<!-- FILE_MAP_BEGIN 
<!--
{"file_metadata":{"title":"KNOWLEDGE MANAGEMENT PROTOCOL","description":"Documentation detailing the knowledge capture and management protocol including pattern detection, verification, execution flow, success criteria, tracking, and integration points.","last_updated":"2025-07-31","type":"documentation"},"ai_instructions":"Analyze the document by recognizing the hierarchical structure and thematic divisions. Focus on the main protocol steps: pattern detection, verification and correction, execution flow, success criteria, tracking, and integration. Identify key elements such as code blocks illustrating execution flow and tracking queries, and highlight critical warnings. Ensure line numbers are precise and sections do not overlap, providing clear, descriptive names and summaries to facilitate navigation and comprehension.","sections":[{"name":"Introduction and Protocol Overview","description":"Introduces the knowledge management protocol, its trigger conditions, and primary purpose for capturing and correcting user knowledge.","line_start":7,"line_end":11},{"name":"Pattern Detection","description":"Describes the patterns and keywords used to detect knowledge capture or correction triggers.","line_start":12,"line_end":16},{"name":"Verification and Correction Process","description":"Details the step-by-step verification and correction workflow including capture, storage, conflict checking, correction, and integration of knowledge.","line_start":17,"line_end":23},{"name":"Execution Flow Diagram","description":"Presents a visual flow of the knowledge management process from remembering or correcting to tracking.","line_start":24,"line_end":28},{"name":"Success Criteria","description":"Lists the criteria that define successful knowledge capture, storage, conflict resolution, application, and history preservation.","line_start":29,"line_end":35},{"name":"Tracking Implementation","description":"Provides the AQL code block used for tracking knowledge management actions and metrics.","line_start":36,"line_end":47},{"name":"Integration Points and Critical Notes","description":"Outlines the external collections and protocols integrated with the knowledge management system and highlights critical usage warnings.","line_start":48,"line_end":56}],"key_elements":[{"name":"Trigger and Purpose Statements","description":"Defines the trigger phrases and the overall purpose of the knowledge management protocol.","line":8},{"name":"Pattern Detection List","description":"Enumerates specific phrases and patterns that initiate knowledge capture or correction.","line":13},{"name":"Verification and Correction Steps","description":"Numbered list detailing the logical steps for verifying and correcting knowledge entries.","line":18},{"name":"Execution Flow Code Block","description":"Flow diagram illustrating the sequential process of knowledge management operations.","line":25},{"name":"Success Criteria Checklist","description":"Checklist of conditions that must be met for successful knowledge management.","line":30},{"name":"Tracking AQL Code Block","description":"ArangoDB query language code snippet used to log knowledge management actions and metrics.","line":37},{"name":"Integration References and Critical Warning","description":"Lists collections and protocols integrated with the system and emphasizes the critical instruction to avoid a specific tool.","line":49}]}
-->
<!-- FILE_MAP_END -->

# KNOWLEDGE MANAGEMENT PROTOCOL

**TRIGGER**: User says "remember" or corrects existing knowledge
**PURPOSE**: Capture user preferences and systematically correct outdated information

## DETECT PATTERNS
- "remember:", "remember that", "remember we"
- "This is outdated", "This is incorrect", "Our tools no longer"
- Direct contradiction of documented patterns

## VERIFY & CORRECT
1. **Capture**: IF "remember" keyword → VERIFY content extracted and classified (preference/pattern/decision/lesson) → IF NOT extract and categorize
2. **Storage**: IF knowledge classified → VERIFY stored in correct collection (rules/heuristics/research_docs/metrics) → IF NOT use mcp_cognitive_tools_arango_modify
3. **Conflicts**: IF new knowledge → VERIFY no conflicts with existing knowledge → IF NOT trigger systematic correction
4. **Correction**: IF outdated knowledge detected → VERIFY comprehensive search executed across all collections → IF NOT search all locations
5. **Integration**: IF knowledge stored → VERIFY applied immediately in current context → IF NOT demonstrate usage

## EXECUTION FLOW
```
[REMEMBER/CORRECT] → [EXTRACT] → [CLASSIFY] → [STORE] → [CHECK_CONFLICTS] → [APPLY] → [TRACK]
```

## SUCCESS CRITERIA
- ✅ Knowledge extracted and classified correctly
- ✅ Stored with validated `_id` in appropriate collection
- ✅ Conflicts detected and resolved systematically
- ✅ Knowledge applied immediately in current response
- ✅ Git commits preserve correction history

## TRACKING
```aql
INSERT {
  type: "knowledge_management",
  action: @capture_or_correct,
  knowledge_type: @classified_type,
  collection_used: @storage_location,
  conflicts_found: @conflict_count,
  timestamp: DATE_NOW()
} INTO metrics
```

## INTEGRATES WITH
- **Protocol database-operation**: For storage validation
- **Collection research_docs**: Primary knowledge storage
- **Collection heuristics**: Pattern and decision storage
- **Collection rules**: Preference and directive storage

**CRITICAL**: NEVER use update_memory tool - always use mcp_cognitive_tools_arango_modify
