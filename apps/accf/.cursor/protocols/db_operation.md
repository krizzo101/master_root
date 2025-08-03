<!-- FILE_MAP_BEGIN 
<!--
{"file_metadata":{"title":"DATABASE OPERATION PROTOCOL","description":"Documentation outlining the protocol for database operations including pattern detection, verification, execution flow, success criteria, tracking, and integration with other system rules.","last_updated":"2025-07-31","type":"documentation"},"ai_instructions":"Analyze the document by identifying its hierarchical structure and logical sections based on headings and content themes. Extract key elements such as code blocks, tables, and important concepts that aid comprehension. Ensure all line numbers are 1-indexed and precisely reflect the document layout including blank lines. Create non-overlapping sections that represent meaningful content divisions. Provide clear, concise descriptions for each section and key element to facilitate navigation and understanding of the database operation protocol.","sections":[{"name":"Introduction and Protocol Overview","description":"Introduces the database operation protocol, its trigger conditions, and primary purpose to prevent database failures through validation and error detection.","line_start":7,"line_end":11},{"name":"Detect Patterns","description":"Describes the specific patterns and tool calls that the protocol monitors to detect database operations and potential errors.","line_start":12,"line_end":17},{"name":"Verify and Correct","description":"Details the verification steps and corrective actions for connection parameters, AQL syntax, operation results, and error detection to ensure database operation integrity.","line_start":18,"line_end":23},{"name":"Execution Flow","description":"Outlines the sequential flow of database operation steps from validation to tracking, including a visual representation of the process.","line_start":24,"line_end":28},{"name":"Success Criteria","description":"Lists the conditions that must be met for a database operation to be considered successful, including validation and error checks.","line_start":29,"line_end":34},{"name":"Tracking Database Operations","description":"Provides the AQL code snippet used to log database operation metrics such as operation type, validation results, errors, and timestamps.","line_start":35,"line_end":44},{"name":"Integration with System Rules","description":"Describes how the database operation protocol integrates with other system components and rules for automatic loading and mandatory triggers.","line_start":45,"line_end":50}],"key_elements":[{"name":"Trigger and Purpose Statements","description":"Defines the trigger conditions for the protocol and its main goal to prevent database failures.","line":8},{"name":"Pattern Detection List","description":"Bullet list enumerating specific tool calls and operations monitored for pattern detection.","line":13},{"name":"Verification Steps List","description":"Numbered list detailing the verification and correction steps for connection, syntax, results, and errors.","line":19},{"name":"Execution Flow Diagram","description":"A linear flow diagram illustrating the sequence of database operation steps.","line":25},{"name":"Success Criteria Checklist","description":"Checklist of conditions that define successful database operations.","line":30},{"name":"Tracking AQL Code Block","description":"AQL query code block used to insert operation metrics into the metrics collection.","line":36},{"name":"Integration Rules List","description":"Bullet list describing related system rules and collections integrated with the protocol.","line":46}]}
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
