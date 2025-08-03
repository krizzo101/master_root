<!-- FILE_MAP_BEGIN 
<!--
{"file_metadata":{"title":"ROOT CAUSE ANALYSIS PROTOCOL","description":"Comprehensive protocol document detailing detection patterns, investigation workflows, execution steps, database tracking, automation integration, and startup integration for identifying and eliminating root causes of persistent issues.","last_updated":"2025-07-31","type":"documentation"},"ai_instructions":"Analyze the document to extract a structured file map that reflects the logical organization of the root cause analysis protocol. Identify major thematic sections and subsections based on headings, ensuring line ranges are precise and non-overlapping. Capture key elements such as code blocks, tables, and important concepts that aid navigation and understanding. Provide clear, descriptive names and explanations for each section and key element to facilitate efficient document comprehension and navigation.","sections":[{"name":"Introduction and Protocol Overview","description":"Introduces the root cause analysis protocol, its trigger conditions, and primary purpose.","line_start":7,"line_end":11},{"name":"Detection Patterns","description":"Describes common patterns and database queries used to detect recurring issues.","line_start":12,"line_end":16},{"name":"Root Cause Investigation Workflow","description":"Details the step-by-step workflow for investigating root causes, including issue classification, source investigation, comprehensive scanning, and fix verification.","line_start":17,"line_end":50},{"name":"Execution Steps","description":"Outlines practical steps to execute the root cause analysis, including tracking fix history and conducting comprehensive source searches.","line_start":51,"line_end":64},{"name":"Example for \"quality search\" issue","description":"Provides a detailed example workflow for addressing a 'quality search' issue, including impact analysis, systematic correction, and prevention measures.","line_start":65,"line_end":91},{"name":"Database Tracking","description":"Defines the schema and structure for tracking fix history and root cause analysis data in the database.","line_start":92,"line_end":128},{"name":"Automation Integration","description":"Describes how the root cause analysis protocol integrates with automation workflows, including workflow steps and success criteria.","line_start":129,"line_end":150},{"name":"Integration with Startup","description":"Explains the integration of root cause analysis checks into the startup workflow to validate consistency and prevent recurring issues.","line_start":151,"line_end":163}],"key_elements":[{"name":"Trigger and Purpose Statement","description":"Defines the trigger conditions for the protocol and its main purpose to identify and eliminate root causes.","line":8},{"name":"Detection Patterns List","description":"Lists common phrases and database query strategies used to detect recurring issues.","line":13},{"name":"Issue Classification Code Block","description":"Code block illustrating classification of persistent issues into categories.","line":20},{"name":"Source Investigation Protocol Diagram","description":"Code block showing the search strategy for different issue classifications.","line":25},{"name":"Comprehensive Source Scanning Steps","description":"Enumerated list describing the scanning process across various sources for persistent issues.","line":32},{"name":"Fix Verification Strategy Diagram","description":"Code block outlining the steps to verify fixes and prevent recurrence.","line":42},{"name":"AQL Query for Fix History","description":"Code block containing an AQL query to retrieve similar fixes from the metrics database.","line":54},{"name":"Bash Commands for Source Search","description":"Shell commands demonstrating how to search for 'quality search' related patterns in various file types.","line":64},{"name":"Impact Analysis List","description":"Bullet list categorizing sources by authority and type for impact analysis.","line":71},{"name":"Systematic Correction Steps","description":"Numbered list detailing the correction process to fix all sources and monitor recurrence.","line":77},{"name":"Prevention Measures Diagram","description":"Code block illustrating prevention strategies after root cause elimination.","line":84},{"name":"Fix History Schema JSON Block","description":"JSON formatted schema showing the structure of database tracking for fix history and root cause analysis.","line":95},{"name":"Workflow Integration YAML Block","description":"YAML formatted workflow steps for automation integration of the root cause analysis protocol.","line":132},{"name":"Success Criteria Checklist","description":"Checklist of criteria to determine successful root cause analysis and prevention implementation.","line":145},{"name":"Startup Validation Check Steps","description":"Numbered list describing validation checks integrated into startup to prevent recurring issues.","line":154}]}
-->
<!-- FILE_MAP_END -->

# ROOT CAUSE ANALYSIS PROTOCOL

**TRIGGER**: Same fix applied ≥2 times OR recurring issue detected
**PURPOSE**: Identify and eliminate root causes of persistent problems

## DETECTION PATTERNS
- "Fixed again", "Same issue", "Still happening", "Keeps returning"
- Database query: Recent fixes with same symptoms
- Pattern recognition: Similar error types or fix patterns

## ROOT CAUSE INVESTIGATION WORKFLOW

### 1. Issue Classification
```
PERSISTENT_ISSUE_DETECTED → CLASSIFY → [CONFIG_DRIFT, DOCUMENTATION_CONFLICT, TRAINING_CONTAMINATION, SYSTEM_INCONSISTENCY]
```

### 2. Source Investigation Protocol
```
CLASSIFY_COMPLETE → SEARCH_STRATEGY:
├── CONFIG_DRIFT → Check configuration files, environment variables, defaults
├── DOCUMENTATION_CONFLICT → Search all docs, examples, comments for conflicting info
├── TRAINING_CONTAMINATION → Search for authoritative sources teaching incorrect patterns
└── SYSTEM_INCONSISTENCY → Check implementation vs interface mismatches
```

### 3. Comprehensive Source Scanning
**For any persistent issue:**
1. **Grep Search**: Use broad patterns to find ALL references
2. **Documentation Scan**: Check all .md, .mdc files for conflicting information
3. **Code Analysis**: Search implementation files for pattern sources
4. **Configuration Review**: Check defaults, examples, templates
5. **Training Data Audit**: Identify what's teaching the agent wrong patterns

### 4. Fix Verification Strategy
```
ROOT_CAUSE_IDENTIFIED → FIX_ALL_SOURCES → VALIDATE → MONITOR
├── Update authoritative sources (rules, protocols, docs)
├── Fix implementation code and examples
├── Update training references and comments
├── Add validation checks to prevent recurrence
└── Track in database for future reference
```

## EXECUTION STEPS

### Step 1: Track Fix History
```aql
// Query for similar fixes
FOR fix IN metrics
  FILTER fix.type == "issue_fix"
  FILTER fix.issue_pattern LIKE @pattern
  FILTER fix.timestamp > DATE_SUBTRACT(DATE_NOW(), 30, "day")
  RETURN {fix: fix.description, count: fix.occurrence_count}
```

### Step 2: Comprehensive Source Search
```bash
# Example for "quality search" issue:
grep -r "search_type.*quality" . --include="*.md" --include="*.mdc" --include="*.py" --include="*.yml"
grep -r "quality.*search" . --include="*.md" --include="*.mdc" --include="*.py" --include="*.yml"
grep -r "min_quality" . --include="*.md" --include="*.mdc" --include="*.py" --include="*.yml"
```

### Step 3: Impact Analysis
- **High Authority Sources**: .cursor/rules/*.mdc, main documentation
- **Training Sources**: Examples, comments, docstrings
- **Implementation Sources**: Code that defines capabilities
- **Template Sources**: Workflow templates, protocol examples

### Step 4: Systematic Correction
1. **Fix All Sources**: Update every reference found
2. **Add Guardrails**: Implement validation to catch future occurrences
3. **Document Pattern**: Record in knowledge base for future reference
4. **Monitor Recurrence**: Track if issue returns after comprehensive fix

### Step 5: Prevention Measures
```
ROOT_CAUSE_ELIMINATED → PREVENTION:
├── Add validation rules to catch pattern in future
├── Update documentation standards to prevent conflict
├── Create consistency checks in CI/CD
└── Train pattern recognition for similar issues
```

## DATABASE TRACKING

### Fix History Schema
```json
{
  "type": "persistent_issue_investigation",
  "issue_id": "quality_search_persistence",
  "fix_history": [
    {
      "timestamp": "2024-01-15T10:30:00Z",
      "location": ".cursor/workflows/00-initialize.yml",
      "fix_description": "Removed quality search type",
      "investigator": "agent_session_123"
    }
  ],
  "root_cause_analysis": {
    "investigation_triggered": "2024-01-15T11:00:00Z",
    "sources_found": [
      ".cursor/rules/000-core-automation-framework.mdc:58",
      "development/cognitive_interface/mcp_consolidated_server.py:48",
      ".cursor/rules/800-development-best-practices.mdc:116"
    ],
    "root_cause_type": "TRAINING_CONTAMINATION",
    "authoritative_sources_teaching_wrong_pattern": true
  },
  "comprehensive_fix": {
    "all_sources_updated": true,
    "validation_added": true,
    "prevention_measures": ["source_consistency_check", "capability_validation"]
  },
  "monitoring": {
    "recurrence_check_frequency": "daily",
    "success_metrics": "zero_occurrences_30_days"
  }
}
```

## AUTOMATION INTEGRATION

### Workflow Integration
```yaml
fix_tracking_check:
  trigger: "After any fix operation"
  steps:
    - query_fix_history: Check for similar fixes in last 30 days
    - if_recurring: Trigger root cause investigation
    - comprehensive_search: Find all sources of the pattern
    - systematic_fix: Update all identified sources
    - add_prevention: Implement guardrails
    - monitor_success: Track fix effectiveness
```

### Success Criteria
- ✅ Root cause identified and documented
- ✅ All authoritative sources corrected
- ✅ Prevention measures implemented
- ✅ No recurrence for 30+ days
- ✅ Pattern added to prevention database

## INTEGRATION WITH STARTUP

### Startup Validation Check
Add to startup workflow:
1. **Check Known Issues**: Query database for patterns to avoid
2. **Validate Consistency**: Check for conflicts in authoritative sources
3. **Report Inconsistencies**: Surface any detected conflicts
4. **Prevention Alert**: Warn about patterns that have been problematic

This protocol ensures that when the same issue occurs repeatedly, we systematically identify and eliminate the root cause rather than just treating symptoms.
