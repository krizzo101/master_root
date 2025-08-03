<!-- FILE_MAP_BEGIN 
<!--
{"file_metadata":{"title":"INTELLIGENT THINKING WORKFLOW","description":"Documentation detailing the Intelligent Thinking Workflow, including automatic cognitive enhancement methods, dynamic method selection logic, and a cognitive operations framework with method definitions and implementation guidelines.","last_updated":"2025-07-31","type":"documentation"},"ai_instructions":"Analyze the document to understand the Intelligent Thinking Workflow, focusing on cognitive enhancement methods, dynamic selection logic, and the structured cognitive operations framework. Use the section divisions and key elements to facilitate navigation and comprehension of the workflow, method definitions, and implementation guidelines. Pay attention to code blocks illustrating method selection logic and the core cognitive process steps.","sections":[{"name":"INTELLIGENT THINKING WORKFLOW Overview","description":"Introduction to the Intelligent Thinking Workflow including trigger keywords and initial context for cognitive enhancement.","line_start":7,"line_end":12},{"name":"Automatic Cognitive Enhancement","description":"Details on automatic cognitive enhancement with a focus on cognitive method selection and related code implementation.","line_start":13,"line_end":20},{"name":"Dynamic Method Selection Logic","description":"Code block illustrating the logic for selecting cognitive methods dynamically based on problem characteristics.","line_start":21,"line_end":32},{"name":"Cognitive Operations Framework","description":"Explanation of the core cognitive operations framework including the main process steps and their significance.","line_start":33,"line_end":36},{"name":"Method Definitions","description":"Definitions and explanations of key cognitive methods used within the framework such as Meta Reasoning and Tree of Thoughts.","line_start":37,"line_end":48},{"name":"Implementation Guidelines","description":"Step-by-step guidelines for implementing the cognitive operations framework including problem assessment, method selection, and quality validation.","line_start":49,"line_end":59}],"key_elements":[{"name":"Trigger Keywords","description":"List of keywords that trigger the Intelligent Thinking Workflow.","line":8},{"name":"Cognitive Method Selection Code Block","description":"Python code demonstrating how cognitive methods are selected based on problem assessment.","line":14},{"name":"Dynamic Method Selection Logic Code","description":"Conditional logic within the code block that determines the appropriate cognitive method based on problem complexity and domain.","line":21},{"name":"Core Cognitive Process Steps","description":"The main cognitive operations framework steps: CLARIFY, DECOMPOSE, FILTER, RECOGNIZE, INTEGRATE, VALIDATE.","line":34},{"name":"Method Definitions List","description":"Descriptions of various cognitive methods such as Meta Reasoning, Tree of Thoughts, and Chain of Thought.","line":38},{"name":"Implementation Guidelines List","description":"Numbered list outlining the implementation steps for the cognitive operations framework.","line":49}]}
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
