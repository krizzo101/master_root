<!-- FILE_MAP_BEGIN 
<!--
{"file_metadata":{"title":"KNOWLEDGE MANAGEMENT PROTOCOL","description":"This document outlines the protocol for capturing, verifying, correcting, and managing knowledge within the system. It details pattern detection, verification steps, execution flow, success criteria, tracking mechanisms, and integration points with other collections and protocols.","last_updated":"2025-07-31","type":"documentation"},"ai_instructions":"Analyze the document to understand the knowledge management workflow including pattern detection, verification, correction, execution flow, success criteria, tracking, and integration. Use the section divisions to navigate key procedural steps and code examples. Pay attention to the verification and correction logic, the AQL tracking query, and integration constraints. Ensure line numbers are accurate for precise referencing and avoid overlapping sections.","sections":[{"name":"Introduction and Purpose","description":"Introduces the knowledge management protocol, its trigger conditions, and the overall purpose of capturing and correcting user knowledge.","line_start":7,"line_end":11},{"name":"Pattern Detection","description":"Describes the specific phrases and patterns that trigger the knowledge capture or correction process.","line_start":12,"line_end":16},{"name":"Verification and Correction Process","description":"Details the step-by-step verification, classification, storage, conflict detection, correction, and integration procedures for managing knowledge.","line_start":17,"line_end":23},{"name":"Execution Flow Diagram","description":"Presents the sequential flow of the knowledge management process from remembering or correcting to tracking.","line_start":24,"line_end":28},{"name":"Success Criteria","description":"Lists the criteria that define successful knowledge management including extraction, storage, conflict resolution, application, and history preservation.","line_start":29,"line_end":35},{"name":"Tracking Mechanism","description":"Provides the AQL code block used to log knowledge management actions and metadata into the metrics collection.","line_start":36,"line_end":47},{"name":"Integration Points and Constraints","description":"Specifies the related collections and protocols integrated with the knowledge management process and highlights critical constraints on tool usage.","line_start":48,"line_end":56}],"key_elements":[{"name":"Trigger and Purpose Statements","description":"Defines the trigger keywords and the purpose of the knowledge management protocol, foundational for understanding the document's intent.","line":8},{"name":"Pattern Detection List","description":"Enumerates the key phrases that the system detects to initiate knowledge capture or correction.","line":13},{"name":"Verification and Correction Steps","description":"Numbered procedural instructions outlining how knowledge is captured, verified, stored, checked for conflicts, corrected, and integrated.","line":18},{"name":"Execution Flow Diagram","description":"A concise symbolic flowchart representing the sequential stages of the knowledge management process.","line":25},{"name":"Success Criteria Checklist","description":"Bullet points with checkmarks defining the conditions for successful knowledge management operations.","line":30},{"name":"AQL Tracking Code Block","description":"An ArangoDB Query Language code snippet used to insert tracking data about knowledge management actions into the metrics collection.","line":37},{"name":"Integration References and Critical Warning","description":"Lists the collections and protocols integrated with this process and includes a critical warning about tool usage restrictions.","line":49}]}
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
