<!-- FILE_MAP_BEGIN 
<!--
{"file_metadata":{"title":"Operationalization Strategy Protocol","description":"A systematic approach to deciding when and how tools, protocols, and workflows should be operationalized automatically versus kept manual or user-initiated, including decision frameworks, methods, patterns, examples, and integration guidance.","last_updated":"2025-07-31","type":"documentation"},"ai_instructions":"Analyze the document to identify major thematic sections reflecting the operationalization strategy including decision criteria, methods, implementation guidance, patterns, examples, success metrics, and integration. Focus on grouping related headings into broader logical sections to maintain manageable navigation. Extract key elements such as decision criteria lists, code blocks illustrating methods and patterns, example tool operationalization cases, and integration instructions. Ensure all line numbers are precise and sections do not overlap. Provide clear, descriptive section names and concise descriptions to facilitate efficient document comprehension and navigation.","sections":[{"name":"Introduction and Purpose","description":"Overview of the operationalization strategy protocol and its purpose in guiding automatic versus manual tool operations.","line_start":7,"line_end":10},{"name":"Operationalization Decision Framework","description":"Criteria and examples defining when tools and protocols should or should not be operationalized automatically.","line_start":11,"line_end":44},{"name":"Operationalization Methods","description":"Descriptions and code examples of various methods to operationalize tools and protocols including workflow integration, rule enforcement, event-driven activation, keyword triggers, and git hook integration.","line_start":45,"line_end":84},{"name":"Implementation Checklist","description":"Step-by-step checklist for operationalizing new tools and protocols as well as transitioning existing manual tools to automated workflows.","line_start":85,"line_end":101},{"name":"Specific Operationalization Patterns","description":"Predefined patterns with code examples illustrating common operationalization scenarios such as safety-critical validation, pattern detection, maintenance automation, and tool integration.","line_start":102,"line_end":135},{"name":"Operationalization Examples","description":"Concrete examples of tools and their operationalization status, highlighting which are automated and which remain manual.","line_start":136,"line_end":152},{"name":"Success Metrics","description":"Criteria and expectations for evaluating the effectiveness of operationalized versus manual tools.","line_start":153,"line_end":168},{"name":"Integration with Core Automation","description":"Guidance and code snippet for updating the core automation framework to incorporate operationalization triggers and enforcement.","line_start":169,"line_end":184}],"key_elements":[{"name":"Decision Criteria for Operationalization","description":"Lists of criteria defining when tools should or should not be operationalized automatically, including safety, pattern detection, and user-initiated factors.","line":13},{"name":"Examples of Operationalized vs Manual Tools","description":"Examples illustrating specific tools and their operationalization status to clarify decision framework application.","line":21},{"name":"Workflow Integration Code Block","description":"YAML code snippet showing how to add operationalization triggers to existing workflows.","line":47},{"name":"Rule Enforcement Code Block","description":"Markdown code snippet demonstrating rule enforcement within the core automation framework.","line":55},{"name":"Event-Driven Activation Code Block","description":"Code snippet illustrating activation of protocols based on specific events or patterns.","line":62},{"name":"Keyword Triggers Code Block","description":"Code snippet showing automatic activation based on keywords or phrases.","line":69},{"name":"Git Hook Integration Code Block","description":"Bash script snippet demonstrating automatic execution of protocols on git events.","line":77},{"name":"Implementation Checklist Steps","description":"Enumerated steps for operationalizing new and existing tools to ensure systematic adoption.","line":87},{"name":"Safety-Critical Validation Pattern","description":"YAML code example for always operationalizing safety checks to block unsafe operations.","line":104},{"name":"Pattern Detection & Response Pattern","description":"Markdown code example for operationalizing recurring problem detection and automatic response.","line":112},{"name":"Maintenance Automation Pattern","description":"YAML code snippet illustrating scheduled maintenance automation tasks.","line":120},{"name":"Tool Integration Pattern","description":"YAML code example showing conditional operationalization based on tool availability with fallback strategies.","line":128},{"name":"Operationalization Examples for Tools","description":"Lists detailing operationalized and non-operationalized status for Dependency Mapper, external tools, and root cause analysis.","line":138},{"name":"Success Metrics for Operationalized and Manual Tools","description":"Lists of expected outcomes and benefits for both operationalized and manual tools.","line":155},{"name":"Core Automation Framework Update Code Block","description":"Markdown snippet detailing how to update the core automation framework with operationalization enforcement rules.","line":171}]}
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
