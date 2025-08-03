<!-- FILE_MAP_BEGIN 
<!--
{"file_metadata":{"title":"DATABASE OPERATION PROTOCOL","description":"This document defines the protocol for detecting, verifying, correcting, executing, and tracking database operations to prevent failures and ensure data integrity.","last_updated":"2025-07-31","type":"documentation"},"ai_instructions":"Analyze the document to understand the database operation protocol including pattern detection, verification steps, execution flow, success criteria, tracking mechanisms, and integration points. Use the section divisions and key elements such as code blocks and lists to guide navigation and comprehension. Ensure line numbers are precise and sections do not overlap for accurate referencing.","sections":[{"name":"Introduction and Purpose","description":"Overview of the database operation protocol including trigger conditions and the primary purpose of preventing database failures through validation and error detection.","line_start":7,"line_end":11},{"name":"Detect Patterns","description":"Details the patterns and operations that trigger the protocol, including tool calls, AQL query construction, database connections, and error checking requirements.","line_start":12,"line_end":17},{"name":"Verify and Correct","description":"Step-by-step verification and correction procedures for connection parameters, AQL syntax, results validation, and error detection to ensure operation correctness.","line_start":18,"line_end":23},{"name":"Execution Flow","description":"Visual representation of the database operation process flow from validation through execution to outcome tracking.","line_start":24,"line_end":28},{"name":"Success Criteria","description":"Defines the conditions that must be met for a database operation to be considered successful, including connection validation, syntax correctness, result structure, and error absence.","line_start":29,"line_end":34},{"name":"Tracking","description":"Describes the tracking mechanism for database operations using an AQL insert statement to log operation details and validation results into a metrics collection.","line_start":35,"line_end":45},{"name":"Integration Points","description":"Lists the related rules and collections that integrate with the database operation protocol for automatic loading, mandatory triggers, and operation tracking.","line_start":46,"line_end":51}],"key_elements":[{"name":"Trigger and Purpose Statements","description":"Defines the trigger conditions for the protocol and its main purpose to prevent database failures.","line":8},{"name":"Pattern Detection List","description":"Bullet list of patterns and operations that initiate the protocol, including tool calls and query constructions.","line":13},{"name":"Verification Steps Numbered List","description":"Numbered instructions detailing verification and correction steps for connection, syntax, results, and errors.","line":19},{"name":"Execution Flow Diagram","description":"A flow diagram illustrating the sequence of database operation steps from validation to tracking.","line":25},{"name":"Success Criteria Checklist","description":"Checklist of conditions that define successful database operations.","line":30},{"name":"Tracking AQL Code Block","description":"AQL insert statement used to log database operation metrics including operation type, validation results, errors, and timestamp.","line":36},{"name":"Integration List","description":"Bullet list of rules and collections that the protocol integrates with for dispatching, triggering, and logging.","line":47}]}
-->
<!-- FILE_MAP_END -->

# DATABASE OPERATION PROTOCOL

**TRIGGER**: Any database operation or error detection needed
**PURPOSE**: Prevent database failures through systematic validation and error detection

## DETECT PATTERNS
- `mcp_cognitive_tools_arango_*` tool calls
- AQL query construction or execution
- Database connection operations
- Tool completion requiring error checking

## VERIFY & CORRECT
1. **Connection**: IF database operation → VERIFY host:port:8550, db:_system, auth:root/change_me → IF NOT fix parameters immediately
2. **AQL Syntax**: IF AQL query → VERIFY FOR→FILTER→SORT→LIMIT→RETURN order → IF NOT correct syntax before execution
3. **Results**: IF operation complete → VERIFY `_id` present, expected data structure → IF NOT investigate silent failure
4. **Errors**: IF tool result → VERIFY no `{"error": "MCP error"}`, `"success": false`, empty `[]` when data expected → IF NOT STOP and analyze

## EXECUTION FLOW
```
[DB_OPERATION] → [VALIDATE_CONNECTION] → [CHECK_SYNTAX] → [EXECUTE] → [VERIFY_RESULTS] → [TRACK_OUTCOME]
```

## SUCCESS CRITERIA
- ✅ Connection parameters validated
- ✅ AQL syntax follows required order
- ✅ Results contain expected structure
- ✅ No errors or silent failures detected

## TRACKING
```aql
INSERT {
  type: "database_operation",
  operation_type: @operation_type,
  validation_passed: @validation_result,
  errors_detected: @error_count,
  timestamp: DATE_NOW()
} INTO metrics
```

## INTEGRATES WITH
- **Rule 001**: Behavioral dispatcher automatic loading
- **Rule 002**: Mandatory protocol triggers
- **Collection metrics**: Operation tracking and failure logs
