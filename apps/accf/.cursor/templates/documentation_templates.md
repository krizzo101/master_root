<!-- FILE_MAP_BEGIN 
<!--
{"file_metadata":{"title":"Documentation Templates","description":"A comprehensive collection of documentation templates covering API documentation, technical specifications, user guides, README templates, architecture documents, runbooks, and code documentation to standardize project documentation practices.","last_updated":"2025-07-31","type":"documentation"},"ai_instructions":"Analyze the document by focusing on major thematic sections that group related templates together, ensuring line numbers are precise and sections do not overlap. Prioritize capturing high-level navigation points such as API templates, technical specs, user guides, README, architecture, runbooks, and code documentation. Identify key code blocks, example commands, and important conceptual descriptions. Provide a structured JSON map with clear section boundaries and descriptions to facilitate efficient navigation and comprehension of the documentation templates.","sections":[{"name":"Introduction and API Documentation Templates","description":"Introduces the documentation templates and provides API documentation examples including service API base URL, authentication, and endpoint details.","line_start":7,"line_end":19},{"name":"Technical Specification Templates","description":"Contains templates for component technical specifications including purpose, requirements, architecture, testing, and deployment details.","line_start":20,"line_end":36},{"name":"User Guide Templates","description":"Provides user guide templates covering product features, troubleshooting steps, and support resources.","line_start":37,"line_end":53},{"name":"README Template","description":"Template for project README files including setup instructions, usage examples, configuration, and licensing information.","line_start":54,"line_end":73},{"name":"Architecture Document Templates","description":"Templates for system architecture documentation covering design diagrams, non-functional requirements, technology stack, and operational details.","line_start":74,"line_end":99},{"name":"Runbook Template","description":"Runbook template for service operations including health checks, deployment and scaling commands, monitoring metrics, troubleshooting, and contact information.","line_start":100,"line_end":132},{"name":"Code Documentation Examples","description":"Examples of code documentation including function and class comments with parameter descriptions and usage examples.","line_start":133,"line_end":153}],"key_elements":[{"name":"API Documentation Code Block","description":"Markdown code block illustrating a service API with base URL, authentication method, GET endpoint parameters, response, and error codes.","line":10},{"name":"Technical Specification Code Block","description":"Markdown code block detailing component specification including purpose, requirements, architecture, testing, and deployment.","line":21},{"name":"User Guide Code Block","description":"Markdown code block presenting product guide with quick start, features, troubleshooting, and support links.","line":38},{"name":"README Setup Bash Code Block","description":"Bash code snippet showing commands to clone repository, install dependencies, and start the project.","line":60},{"name":"README Usage Code Block","description":"Code block placeholder for key usage example in a specified programming language.","line":66},{"name":"Architecture Document Code Block","description":"Markdown code block describing system architecture including design context, components, interactions, data flow, and operational aspects.","line":75},{"name":"Runbook Operations Bash Code Block","description":"Bash commands for deploying and scaling services using kubectl.","line":110},{"name":"Runbook Troubleshooting Section","description":"Structured troubleshooting template with issue symptoms, investigation steps, and resolution actions.","line":121},{"name":"Code Documentation Function Example","description":"JavaScript function documentation with description, parameters, return type, and usage example.","line":134},{"name":"Code Documentation Class Example","description":"JavaScript class documentation including class description and constructor parameter details.","line":143}]}
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
