<!-- FILE_MAP_BEGIN 
<!--
{"file_metadata":{"title":"Rule Template","description":"This document provides a structured template for defining operational rules including their triggers, tools, success indicators, and guidelines for effective rule creation.","last_updated":"2025-07-31","type":"documentation"},"ai_instructions":"Analyze the document by focusing on its hierarchical structure and content themes. Identify major sections based on headings and group related subsections logically. Extract key elements such as code blocks and lists that define the template's components. Ensure line numbers are accurate and sections do not overlap. Provide a clear, navigable map that aids understanding of the rule template structure and usage guidelines.","sections":[{"name":"Introduction and Structure Overview","description":"Introduces the Rule Template and presents the overall structure with a markdown code block illustrating the template format.","line_start":7,"line_end":18},{"name":"Rule Template Main Sections","description":"Details the main components of the rule template including Pattern Name, Triggers, Tools, and Success Indicators with their respective descriptions and lists.","line_start":19,"line_end":35},{"name":"Guidelines for Rule Creation","description":"Provides operational guidelines on length, density, focus, and references to ensure effective and autonomous rule definitions.","line_start":36,"line_end":43}],"key_elements":[{"name":"Markdown Code Block of Rule Template Structure","description":"A markdown formatted code block illustrating the overall structure of the rule template including placeholders and key sections.","line":10},{"name":"Pattern Name Section","description":"Defines the signature, implementation, and validation criteria for the rule pattern, essential for recognition and execution.","line":15},{"name":"Triggers List","description":"A bulleted list specifying keywords, observable conditions, and integration points that activate the rule.","line":20},{"name":"Tools List","description":"A categorized list of primary, validation, and fallback tools used in the rule implementation.","line":25},{"name":"Success Indicators List","description":"A bulleted list describing measurable outcomes, observable behaviors, and system state verifications to confirm rule success.","line":30},{"name":"Guidelines List","description":"A set of bullet points outlining best practices for rule length, density, focus, and referencing templates for examples.","line":37}]}
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
