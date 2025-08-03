<!-- FILE_MAP_BEGIN 
<!--
{"file_metadata":{"title":"Documentation Templates","description":"A comprehensive collection of templates for various documentation types including API docs, technical specs, user guides, architecture documents, runbooks, and code documentation to standardize project documentation.","last_updated":"2025-07-31","type":"documentation"},"ai_instructions":"Analyze the document by focusing on major thematic sections rather than every subheading due to the high number of headings. Group related content into broader logical sections to facilitate navigation and comprehension. Identify key code blocks, templates, and example snippets as important elements. Ensure line numbers are accurate and sections do not overlap. Provide clear, descriptive section names that reflect the content themes such as API documentation, technical specifications, user guides, setup instructions, architecture, runbooks, and code documentation. Highlight key elements like code blocks, example commands, diagrams, and troubleshooting templates for quick reference.","sections":[{"name":"Introduction and API Documentation","description":"Introduces the documentation templates and provides API documentation examples including service base URLs, authentication, and endpoint details.","line_start":7,"line_end":19},{"name":"Technical Specification Templates","description":"Contains templates for component technical specifications covering purpose, requirements, architecture, testing, and deployment details.","line_start":20,"line_end":36},{"name":"User Guide Templates","description":"Provides user guide templates including product features, troubleshooting steps, and support resources.","line_start":37,"line_end":53},{"name":"Project README Template","description":"Template for project README files including setup instructions, usage examples, configuration, and license information.","line_start":54,"line_end":73},{"name":"System Architecture Documentation","description":"Templates for system architecture documents covering design diagrams, non-functional requirements, technology choices, and operational details.","line_start":74,"line_end":99},{"name":"Service Runbook Template","description":"Runbook template for services including health checks, operational commands, monitoring metrics, troubleshooting issues, and contact information.","line_start":100,"line_end":108},{"name":"Deployment and Scaling Guidance","description":"Sections covering deployment and scaling strategies, monitoring, troubleshooting, contacts, and code documentation references.","line_start":109,"line_end":140},{"name":"Code Documentation Examples","description":"Examples of code documentation including function and class annotations with usage and configuration details.","line_start":141,"line_end":159}],"key_elements":[{"name":"API Documentation Code Block","description":"Markdown code block illustrating a sample service API with base URL, authentication, GET endpoint, parameters, response, and error codes.","line":10},{"name":"Technical Specification Code Block","description":"Markdown code block template for component specifications including purpose, requirements, architecture, testing, and deployment.","line":21},{"name":"User Guide Code Block","description":"Markdown code block template for product user guides covering quick start, features, troubleshooting, and support links.","line":38},{"name":"README Setup Bash Script","description":"Bash code block demonstrating project setup commands including cloning, installing dependencies, and starting the project.","line":60},{"name":"Architecture Document Code Block","description":"Markdown code block template for system architecture including design diagrams, non-functional requirements, technology stack, and operations.","line":75},{"name":"Runbook Operations Bash Commands","description":"Bash code block with commands for deploying and scaling a service using kubectl.","line":108},{"name":"Runbook Troubleshooting Section","description":"Structured troubleshooting template with issue name, symptoms, investigation steps, and resolution actions.","line":120},{"name":"Code Documentation JavaScript Examples","description":"JavaScript code blocks showing function and class documentation with annotations for parameters, returns, examples, and class configuration.","line":142}]}
-->
<!-- FILE_MAP_END -->

# Documentation Templates

## API Documentation
```markdown
# [Service] API
**Base**: `https://api.example.com/v1` | **Auth**: [method]

### GET /resource
- **Params**: `param` (type, required/optional): description
- **Response**: `{"success": true, "data": {...}}`
- **Errors**: 400/401/404 with description
```

## Technical Specification
```markdown
# [Component] Specification
**Purpose**: [Brief component description]

## Requirements
- **Functional**: [Feature list]
- **Performance**: [Metrics and targets]
- **Tech Stack**: [Key technologies]

## Architecture
- **Design**: [Diagram references]
- **Data Models**: [Key interfaces/schemas]
- **Testing**: [Strategy summary]
- **Deployment**: [Environment and CI/CD]
```

## User Guide
```markdown
# [Product] Guide
**Quick Start**: [Minimal setup steps]

## Features
- **[Feature]**: [Usage overview]

## Troubleshooting
- **[Issue]**: [Solution steps]

## Support
- Docs: [link] | Issues: [link] | Community: [link]
```

## README Template
```markdown
# [Project]
[One-line description]

## Setup
**Requirements**: [Prerequisites]
```bash
git clone [repo] && cd [project] && npm install && npm start
```

## Usage
```[language]
// Key usage example
```

**Config**: [Environment variables]
**License**: [Type]
```

## Architecture Document
```markdown
# [System] Architecture
**Purpose**: [System overview]

## Design
- **Context**: [C4 context diagram]
- **Components**: [C4 container diagram]
- **Interactions**: [Sequence diagrams]
- **Data**: [Flow and storage]

## Non-Functional
- **Performance**: [Targets]
- **Security**: [Measures]
- **Scalability**: [Strategy]

## Technology
- **Stack**: [Choices and rationale]
- **Trade-offs**: [Key decisions]

## Operations
- **Infrastructure**: [Cloud/services]
- **CI/CD**: [Pipeline overview]
- **Monitoring**: [Metrics and alerts]
```

## Runbook Template
```markdown
# [Service] Runbook
**Repository**: [URL] | **Owner**: [Team] | **Environment**: [Prod/Staging]

## Health
- **Endpoint**: `/health` → 200 OK
- **Dependencies**: [Database, APIs]

## Operations
```bash
# Deploy
kubectl apply -f deployment.yaml
# Scale
kubectl scale deployment [name] --replicas=5
```

## Monitoring
- **Metrics**: Response time, error rate, throughput
- **Dashboards**: [Grafana URLs]

## Troubleshooting
### [Issue Name]
**Symptoms**: [Observable problems]
**Investigation**: [Check steps]
**Resolution**: [Fix actions]

## Contacts
- **On-Call**: [Primary] | [Secondary]
- **Escalation**: [Manager]
```

## Code Documentation
```javascript
/**
 * [Brief function description]
 * @param {type} param - Description
 * @returns {type} Description
 * @example const result = func(param);
 */
function example(param) { /* implementation */ }

/**
 * [Class description]
 * @class ClassName
 * @param {Object} config - Configuration options
 */
class ClassName {
  constructor(config) { /* implementation */ }
}
```
