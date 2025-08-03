<!-- FILE_MAP_BEGIN 
<!--
{"file_metadata":{"title":"Operationalization Strategy Protocol","description":"A systematic approach document outlining criteria, methods, patterns, examples, and integration strategies for operationalizing tools, protocols, and workflows automatically versus keeping them manual or user-initiated.","last_updated":"2025-07-31","type":"documentation"},"ai_instructions":"Analyze the document to identify major thematic sections reflecting the operationalization strategy including decision frameworks, methods, implementation checklists, patterns, examples, success metrics, and integration guidance. Provide precise line ranges for each section without overlap. Highlight key elements such as criteria lists, example lists, code blocks illustrating methods and patterns, checklists, and integration instructions. Ensure the JSON output includes clear section names and descriptions to facilitate navigation and comprehension of the document's structure and content.","sections":[{"name":"Introduction and Purpose","description":"Introduces the operationalization strategy protocol, its purpose, and overall goal of automating tools and workflows versus manual operation.","line_start":7,"line_end":10},{"name":"Operationalization Decision Framework","description":"Defines criteria and examples for deciding which tools and protocols should be operationalized automatically and which should remain manual or user-initiated.","line_start":11,"line_end":44},{"name":"Operationalization Methods","description":"Describes five primary methods for operationalizing tools and workflows, including workflow integration, rule enforcement, event-driven activation, keyword triggers, and git hook integration, supported by code block examples.","line_start":45,"line_end":84},{"name":"Implementation Checklist","description":"Provides step-by-step checklists for operationalizing new tools/protocols and transitioning existing manual tools to automated operation.","line_start":85,"line_end":101},{"name":"Specific Operationalization Patterns","description":"Details four common operationalization patterns with code examples, including safety-critical validation, pattern detection and response, maintenance automation, and conditional tool integration.","line_start":102,"line_end":135},{"name":"Operationalization Examples","description":"Gives concrete examples of operationalized and non-operationalized tools such as dependency mappers, external tools, and root cause analysis, illustrating application of the decision framework.","line_start":136,"line_end":152},{"name":"Success Metrics","description":"Lists criteria and expectations for operationalized tools and manual tools to measure effectiveness and appropriate usage.","line_start":153,"line_end":168},{"name":"Integration with Core Automation","description":"Explains how to update the core automation framework to incorporate operationalization triggers and enforce the strategy across tools and workflows, including a code block example.","line_start":169,"line_end":184}],"key_elements":[{"name":"Criteria for Automatic Operationalization","description":"List of criteria defining when tools should be operationalized automatically, including safety-critical, pattern detection, quality gates, maintenance, and high frequency.","line":14},{"name":"Examples of Automatic Operationalization","description":"Examples illustrating automatic triggers such as recurring issue detection and security vulnerability scanning.","line":20},{"name":"Criteria for Manual/User-Initiated Tools","description":"List of criteria for tools that should remain manual, including exploratory, context-dependent, high-cost, experimental, and user-specific.","line":30},{"name":"Examples of Manual/User-Initiated Tools","description":"Examples such as deep architectural analysis and performance profiling that are better suited for manual operation.","line":36},{"name":"Workflow Integration Code Block","description":"YAML code snippet showing how to add operationalization to existing workflows with automatic, conditional, and scheduled execution.","line":48},{"name":"Rule Enforcement Code Block","description":"Markdown code block demonstrating automatic trigger conditions and mandatory checks within the core automation framework.","line":56},{"name":"Event-Driven Activation Code Block","description":"Code snippet illustrating event-driven triggers that load protocols and execute remediation steps.","line":63},{"name":"Keyword Triggers Code Block","description":"Example of automatic activation based on specific keywords or phrases linking to relevant protocols or workflows.","line":72},{"name":"Git Hook Integration Code Block","description":"Bash script example showing automatic execution of validation and analysis on git events like pre-commit and post-merge.","line":80},{"name":"Implementation Checklist for New Tools","description":"Stepwise checklist guiding decision, method selection, integration, testing, documentation, and monitoring for new operationalized tools.","line":87},{"name":"Implementation Checklist for Existing Manual Tools","description":"Checklist focusing on usage analysis, value assessment, cost analysis, integration planning, and rollout strategy for manual tools.","line":95},{"name":"Safety-Critical Validation Pattern Code","description":"YAML snippet enforcing mandatory quality gates before any change to ensure safety-critical validation.","line":107},{"name":"Pattern Detection & Response Pattern Code","description":"Markdown code block defining triggers and actions for automatic protocol execution upon pattern detection.","line":113},{"name":"Maintenance Automation Pattern Code","description":"YAML example scheduling regular maintenance operations with automatic status reporting.","line":123},{"name":"Tool Integration Pattern Code","description":"YAML snippet showing conditional execution based on tool availability with fallback strategies.","line":131},{"name":"Operationalization Examples - Dependency Mapper","description":"List of operationalized and non-operationalized use cases for the dependency mapper tool.","line":139},{"name":"Operationalization Examples - External Tools","description":"Examples of operationalized circular dependency detection and rule validation versus manual visualization.","line":144},{"name":"Operationalization Examples - Root Cause Analysis","description":"Examples of automatic triggering by recurring patterns versus manual deep investigation.","line":149},{"name":"Success Metrics for Operationalized Tools","description":"Criteria such as reducing manual effort, preventing problems, and generating insights automatically.","line":156},{"name":"Success Metrics for Manual Tools","description":"Criteria emphasizing deep insights, exploratory support, and flexibility for user-driven analysis.","line":163},{"name":"Core Automation Framework Update Code Block","description":"Markdown code block detailing operationalization enforcement rules to be added to the core automation framework.","line":172}]}
-->
<!-- FILE_MAP_END -->

# OPERATIONALIZATION STRATEGY PROTOCOL

**PURPOSE**: Systematic approach to making tools, protocols, and workflows part of automatic operations vs. keeping them manual/user-initiated.

## OPERATIONALIZATION DECISION FRAMEWORK

### **SHOULD BE OPERATIONALIZED** (Automatic Triggers)

**Criteria**:
- ✅ **Safety-Critical**: Prevents known problems or regressions
- ✅ **Pattern Detection**: Identifies recurring issues automatically
- ✅ **Quality Gates**: Validates against established standards
- ✅ **Maintenance**: Prevents technical debt accumulation
- ✅ **High Frequency**: Used regularly in normal operations

**Examples**:
- Recurring issue detection → Automatic root cause analysis
- File change validation → Dependency impact analysis
- Circular dependency detection → Automatic validation
- Security vulnerability scanning → Continuous monitoring
- Code quality checks → Pre-commit validation

### **SHOULD NOT BE OPERATIONALIZED** (Manual/User-Initiated)

**Criteria**:
- ❌ **Exploratory**: Ad-hoc analysis or investigation
- ❌ **Context-Dependent**: Requires human judgment
- ❌ **High-Cost**: Expensive operations that shouldn't run continuously
- ❌ **Experimental**: New tools being evaluated
- ❌ **User-Specific**: Depends on user goals or preferences

**Examples**:
- Deep architectural analysis → Manual investigation
- Performance profiling → User-initiated when needed
- Experimental tool evaluation → Manual testing
- Custom visualization → User-driven analysis
- One-off data migration → Manual execution

## OPERATIONALIZATION METHODS

### **1. Workflow Integration**
```yaml
# Add to existing workflows (startup, validation, etc.)
- automatic_trigger: "on_startup"
- conditional_execution: "if_conditions_met"
- scheduled_execution: "daily/weekly/monthly"
```

### **2. Rule Enforcement**
```mdc
# Add to core automation framework
**AUTOMATIC TRIGGER**: condition → action
**MANDATORY CHECK**: validation_required → execute_protocol
```

### **3. Event-Driven Activation**
```
# Triggered by specific events/patterns
PATTERN_DETECTED → LOAD_PROTOCOL → EXECUTE_STEPS
ERROR_THRESHOLD_EXCEEDED → AUTOMATIC_ANALYSIS → REMEDIATION
```

### **4. Keyword Triggers**
```
# Automatic activation on specific keywords/phrases
"recurring issue" → root-cause-analysis.md
"dependency change" → validate.yml
"performance problem" → performance-analysis.yml
```

### **5. Git Hook Integration**
```bash
# Automatic execution on git events
pre-commit: dependency validation
post-merge: impact analysis
pre-push: quality gates
```

## IMPLEMENTATION CHECKLIST

### **For New Tools/Protocols**:
1. **Decision**: Should this be operationalized? (Use criteria above)
2. **Method**: Which operationalization method fits best?
3. **Integration**: Update appropriate workflow/rule/protocol files
4. **Testing**: Verify automatic triggers work correctly
5. **Documentation**: Update operational procedures
6. **Monitoring**: Track effectiveness and adjust triggers

### **For Existing Manual Tools**:
1. **Usage Analysis**: How often is this used?
2. **Value Assessment**: Does it prevent known problems?
3. **Cost Analysis**: Can we afford to run it automatically?
4. **Integration Plan**: Which workflows should include it?
5. **Rollout Strategy**: Gradual vs. immediate operationalization

## SPECIFIC OPERATIONALIZATION PATTERNS

### **Pattern 1: Safety-Critical Validation**
```yaml
# Always operationalize safety checks
trigger: "before_any_change"
validation: "mandatory_quality_gates"
failure_action: "block_operation"
```

### **Pattern 2: Pattern Detection & Response**
```mdc
# Operationalize recurring problem detection
**TRIGGER**: pattern_detected ≥ threshold
**ACTION**: automatic_protocol_execution
**FOLLOW-UP**: prevention_measures_implementation
```

### **Pattern 3: Maintenance Automation**
```yaml
# Operationalize regular maintenance
schedule: "daily/weekly/monthly"
operations: ["cleanup", "validation", "optimization"]
reporting: "automatic_status_updates"
```

### **Pattern 4: Tool Integration**
```yaml
# Conditional operationalization based on tool availability
check_availability: ["tool1", "tool2", "tool3"]
conditional_execution: "if_available_then_execute"
fallback_strategy: "alternative_approach"
```

## OPERATIONALIZATION EXAMPLES

### **Dependency Mapper**
- ✅ **OPERATIONALIZED**: Run on file changes (validates references)
- ✅ **OPERATIONALIZED**: Pre-commit hook (prevents broken references)
- ❌ **NOT OPERATIONALIZED**: Full project analysis (expensive, user-initiated)

### **External Tools (madge, dependency-cruiser)**
- ✅ **OPERATIONALIZED**: Circular dependency detection (safety-critical)
- ✅ **OPERATIONALIZED**: Rule validation (quality gates)
- ❌ **NOT OPERATIONALIZED**: Full visualization (user-initiated analysis)

### **Root Cause Analysis**
- ✅ **OPERATIONALIZED**: Triggered by recurring patterns (pattern detection)
- ✅ **OPERATIONALIZED**: Automatic source scanning (prevents regressions)
- ❌ **NOT OPERATIONALIZED**: Deep manual investigation (context-dependent)

## SUCCESS METRICS

### **Operationalized Tools Should**:
- ✅ Reduce manual effort for repetitive tasks
- ✅ Prevent known problems from recurring
- ✅ Provide early warning of issues
- ✅ Maintain consistent quality standards
- ✅ Generate actionable insights automatically

### **Manual Tools Should**:
- ✅ Provide deep insights when needed
- ✅ Support exploratory analysis
- ✅ Enable context-specific investigations
- ✅ Offer flexibility for custom use cases
- ✅ Remain available for user-initiated analysis

## INTEGRATION WITH CORE AUTOMATION

### **Update Core Framework**:
Add operationalization triggers to `000-core-automation-framework.mdc`:
```mdc
**OPERATIONALIZATION ENFORCEMENT**:
- New tools → Apply operationalization-strategy.md
- Safety-critical patterns → IMMEDIATE operationalization
- Quality gates → AUTOMATIC integration
- Pattern detection → EVENT-DRIVEN activation
```

This protocol ensures systematic operationalization decisions and prevents the gap between creating tools and making them automatically useful.
