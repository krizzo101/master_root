<!-- FILE_MAP_BEGIN 
<!--
{"file_metadata":{"title":"ROOT CAUSE ANALYSIS PROTOCOL","description":"Comprehensive protocol document detailing detection patterns, investigation workflows, execution steps, database tracking, automation integration, and startup integration for root cause analysis of persistent issues.","last_updated":"2025-07-31","type":"documentation"},"ai_instructions":"Analyze the document to identify logical sections based on headings and content themes. Extract key elements such as code blocks, tables, and important concepts with precise line references. Ensure sections do not overlap and cover the entire document. Provide clear, descriptive names and summaries for sections and key elements to facilitate navigation and comprehension.","sections":[{"name":"Introduction and Protocol Overview","description":"Introduces the root cause analysis protocol, its trigger conditions, and its purpose.","line_start":7,"line_end":11},{"name":"Detection Patterns","description":"Describes common patterns and queries used to detect recurring issues.","line_start":12,"line_end":16},{"name":"Root Cause Investigation Workflow","description":"Details the multi-step workflow for investigating root causes, including issue classification, source investigation, comprehensive scanning, and fix verification.","line_start":17,"line_end":50},{"name":"Execution Steps","description":"Step-by-step instructions for tracking fix history, performing comprehensive source searches, impact analysis, systematic correction, and prevention measures.","line_start":51,"line_end":91},{"name":"Database Tracking","description":"Defines the schema and example data structure for tracking fix history, root cause analysis details, comprehensive fixes, and monitoring metrics.","line_start":92,"line_end":128},{"name":"Automation Integration","description":"Describes workflow integration for automating root cause analysis steps and defines success criteria for the automation process.","line_start":129,"line_end":150},{"name":"Integration with Startup","description":"Explains how to integrate root cause analysis checks into the startup workflow to validate consistency and prevent recurring issues.","line_start":151,"line_end":163}],"key_elements":[{"name":"Trigger and Purpose Statement","description":"Defines the trigger condition for the protocol and its primary purpose.","line":8},{"name":"Detection Patterns List","description":"Bullet list of common phrases and query strategies used to detect recurring issues.","line":13},{"name":"Issue Classification Code Block","description":"Code block illustrating classification of persistent issues into categories.","line":20},{"name":"Source Investigation Protocol Code Block","description":"Code block describing the search strategy for different issue classifications.","line":25},{"name":"Comprehensive Source Scanning Instructions","description":"Numbered list describing the scanning approach for all relevant sources.","line":34},{"name":"Fix Verification Strategy Code Block","description":"Code block outlining the steps to fix all sources and validate the fix.","line":42},{"name":"AQL Query for Fix History","description":"Code block containing an AQL query to retrieve similar fixes from metrics database.","line":54},{"name":"Bash Commands for Source Search","description":"Shell commands demonstrating recursive grep searches for quality search issues.","line":64},{"name":"Impact Analysis Bullet List","description":"List of source types to analyze for impact assessment.","line":72},{"name":"Systematic Correction Steps","description":"Numbered list detailing corrective actions to fix and monitor issues.","line":78},{"name":"Prevention Measures Code Block","description":"Code block describing prevention strategies after root cause elimination.","line":84},{"name":"Fix History Schema JSON Block","description":"JSON formatted example schema illustrating database tracking of fixes and root cause analysis.","line":95},{"name":"Workflow Integration YAML Block","description":"YAML formatted workflow steps for automating root cause analysis and fix tracking.","line":132},{"name":"Success Criteria Checklist","description":"Bullet list of criteria indicating successful root cause analysis and prevention.","line":145},{"name":"Startup Validation Check Steps","description":"Numbered list describing integration of root cause checks into startup procedures.","line":154}]}
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
