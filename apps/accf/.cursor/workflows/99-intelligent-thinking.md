<!-- FILE_MAP_BEGIN 
<!--
{"file_metadata":{"title":"INTELLIGENT THINKING WORKFLOW","description":"Documentation detailing the Intelligent Thinking Workflow including automatic cognitive enhancement, method selection logic, and a cognitive operations framework with method definitions and implementation guidelines.","last_updated":"2025-07-31","type":"documentation"},"ai_instructions":"Analyze the document to identify its hierarchical structure and logical divisions, focusing on cognitive workflow concepts and method implementations. Extract key sections with precise line boundaries, capturing code blocks, definitions, and procedural guidelines. Ensure all line numbers are accurate and sections do not overlap. Highlight important elements such as the cognitive method selection code block, the core cognitive operations framework, and detailed method definitions to facilitate efficient navigation and understanding.","sections":[{"name":"INTELLIGENT THINKING WORKFLOW Overview","description":"Introduction to the Intelligent Thinking Workflow including trigger keywords and the initial context for cognitive enhancement.","line_start":7,"line_end":12},{"name":"Automatic Cognitive Enhancement","description":"Details on the automatic cognitive enhancement process and the cognitive method selection approach.","line_start":13,"line_end":15},{"name":"Cognitive Method Selection Code Block","description":"Python code implementing the automatic cognitive intelligence logic, including problem assessment, method selection, and application of cognitive operations.","line_start":16,"line_end":32},{"name":"Cognitive Operations Framework Overview","description":"Introduction to the core cognitive operations framework outlining the main process steps.","line_start":33,"line_end":36},{"name":"Method Definitions","description":"Definitions and explanations of various cognitive methods used within the framework.","line_start":37,"line_end":47},{"name":"Implementation Guidelines","description":"Step-by-step guidelines for implementing the cognitive operations framework including problem assessment, method selection, execution, validation, and integration.","line_start":48,"line_end":56}],"key_elements":[{"name":"Trigger Keywords","description":"Keywords that trigger the intelligent thinking workflow such as 'think', 'ACR', 'reflect', 'ponder', and 'consider'.","line":8},{"name":"Cognitive Method Selection Code Block","description":"Python code illustrating the logic for selecting cognitive methods based on problem characteristics and applying cognitive operations.","line":16},{"name":"Core Cognitive Operations Process","description":"The main cognitive process steps: CLARIFY \u2192 DECOMPOSE \u2192 FILTER \u2192 RECOGNIZE \u2192 INTEGRATE \u2192 VALIDATE.","line":34},{"name":"Method Definitions List","description":"Descriptions of key cognitive methods such as Meta Reasoning, Tree of Thoughts, Structured Analysis, Step Back Reasoning, and Chain of Thought.","line":38},{"name":"Implementation Guidelines List","description":"Numbered list detailing the implementation steps for the cognitive operations framework.","line":49}]}
-->
<!-- FILE_MAP_END -->

# INTELLIGENT THINKING WORKFLOW

**Triggered by**: `think`, `ACR`, `reflect`, `ponder`, `consider`

## AUTOMATIC COGNITIVE ENHANCEMENT

### Cognitive Method Selection

```python
# Automatic Cognitive Intelligence
problem_assessment = analyze_problem_characteristics(user_input)
optimal_method = select_reasoning_method(problem_assessment)
cognitive_operations = determine_cognitive_operations_needed(problem_assessment)

# Dynamic Method Selection Logic:
if problem_assessment.complexity == "high" and problem_assessment.stakeholders > 2:
    method = "meta_reasoning + cognitive_operations + tree_of_thoughts"
elif problem_assessment.complexity == "high":
    method = "cognitive_operations + tree_of_thoughts"
elif problem_assessment.domain == "analytical":
    method = "structured_analysis + cognitive_operations"
elif problem_assessment.domain == "planning":
    method = "cognitive_operations + step_back_reasoning"
else:
    method = "cognitive_operations + chain_of_thought"

# Apply: CLARIFY → DECOMPOSE → FILTER → RECOGNIZE → INTEGRATE → VALIDATE
enhanced_thinking = execute_with_cognitive_operations(method, user_input)
```

## COGNITIVE OPERATIONS FRAMEWORK

**Core Process**: CLARIFY → DECOMPOSE → FILTER → RECOGNIZE → INTEGRATE → VALIDATE

### Method Definitions

**Meta Reasoning**: Multi-level analysis with recursive self-examination
**Tree of Thoughts**: Parallel reasoning paths with branch evaluation
**Structured Analysis**: Systematic decomposition with evidence frameworks
**Step Back Reasoning**: High-level principle identification before detail work
**Chain of Thought**: Sequential logical progression with explicit steps

### Implementation Guidelines

1. **Problem Assessment**: Analyze complexity, domain, stakeholders, constraints
2. **Method Selection**: Apply decision logic to choose optimal cognitive approach
3. **Cognitive Operations**: Execute structured thinking framework
4. **Quality Validation**: Verify reasoning coherence and completeness
5. **Integration**: Synthesize insights into actionable understanding
