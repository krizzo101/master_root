<!-- FILE_MAP_BEGIN 
<!--
{"file_metadata":{"title":"Rule Template","description":"Template documentation for defining rules with structured sections including pattern name, triggers, tools, success indicators, and guidelines.","last_updated":"2025-07-31","type":"documentation"},"ai_instructions":"Analyze the document by recognizing its hierarchical structure and thematic divisions. Focus on the main sections and their subsections to create logical, non-overlapping sections with precise line boundaries. Identify key elements such as code blocks, lists, and emphasized text that clarify the template's usage and structure. Ensure all line numbers are 1-indexed and accurately reflect the document's content including blank lines and formatting. Provide a clear, navigable map that aids understanding of the rule template's components and guidelines.","sections":[{"name":"Introduction and Structure Overview","description":"Introduces the Rule Template and provides an overview of its structure with an embedded markdown code block illustrating the template format.","line_start":7,"line_end":22},{"name":"Pattern Name Section","description":"Details the pattern name subsection including signature, implementation, and validation criteria for the rule.","line_start":23,"line_end":28},{"name":"Triggers Section","description":"Lists the keywords, observable conditions, and integration points that activate the rule.","line_start":29,"line_end":33},{"name":"Tools Section","description":"Describes the primary, validation, and fallback tools used in the rule implementation.","line_start":34,"line_end":38},{"name":"Success Indicators Section","description":"Specifies measurable outcomes, observable behaviors, and system state verifications that indicate rule success.","line_start":39,"line_end":43},{"name":"Guidelines Section","description":"Provides operational guidelines on length, density, focus, and references for creating effective rules.","line_start":44,"line_end":50}],"key_elements":[{"name":"Rule Template Title","description":"Main title of the document indicating the template purpose.","line":7},{"name":"Structure Markdown Code Block","description":"Code block illustrating the overall structure and format of the rule template including placeholders and section headers.","line":10},{"name":"Pattern Name Subsection","description":"Subsection defining the pattern name with signature, implementation, and validation fields.","line":23},{"name":"Triggers List","description":"Bullet list enumerating the trigger conditions that activate the rule.","line":29},{"name":"Tools List","description":"Bullet list describing primary, validation, and fallback tools for rule execution.","line":34},{"name":"Success Indicators List","description":"Bullet list outlining measurable outcomes and verification methods for rule success.","line":39},{"name":"Guidelines Bullet Points","description":"Bullet points specifying operational constraints and focus areas for rule creation.","line":44}]}
-->
<!-- FILE_MAP_END -->

# Rule Template

## Structure
```markdown
# [Number]-[descriptive-name]
**USE WHEN**: [trigger conditions]
**TO**: [specific outcome]

## [Pattern Name]
**Signature**: [recognition criteria]
**Implementation**: [actions/tools]
**Validation**: [success verification]

## Triggers
- [Keywords/contexts that activate rule]
- [Observable conditions]
- [Integration points]

## Tools
- **Primary**: [main tools]
- **Validation**: [verification tools]
- **Fallback**: [alternatives]

## Success Indicators
- [Measurable outcome]
- [Observable behavior]
- [System state verification]
```

## Guidelines
- **Length**: 50-70 lines maximum
- **Density**: Every line serves operational purpose
- **Focus**: Autonomous recognition over step-by-step instructions
- **References**: Use templates for extended examples
