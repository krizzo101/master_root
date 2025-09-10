# Application Build Input Form

## Project Metadata
- **Project Name**: `[lowercase, alphanumeric, hyphens/underscores only]`
- **Description**: `[10-500 characters, clear description of what the application does]`
- **Version**: `[semantic version, e.g., 1.0.0]`
- **Type**: `[web_app|api|cli|library|service|desktop_app|mobile_app]`
- **Priority**: `[critical|high|medium|low]`
- **Tags**: `[comma-separated categorization tags]`

## Functional Requirements
For each requirement, provide:
- **ID**: `FR-001, FR-002, etc.`
- **Description**: `[clear description of what the system must do]`
- **Priority**: `[must_have|should_have|could_have]`
- **Acceptance Criteria**:
  - `[criterion 1]`
  - `[criterion 2]`
  - `[criterion 3]`
- **Dependencies**: `[other FR IDs this depends on]`

## Non-Functional Requirements
### Performance
- **Response Time**: `[e.g., <200ms for API calls]`
- **Throughput**: `[e.g., 1000 requests/second]`
- **Concurrent Users**: `[number]`

### Security
- **Authentication Required**: `[yes/no]`
- **Authorization Levels**: `[list of roles/permissions]`
- **Data Encryption**: `[yes/no]`
- **Compliance Requirements**: `[GDPR, HIPAA, etc.]`

### Scalability
- **Expected Growth**: `[description of growth expectations]`
- **Horizontal Scaling**: `[yes/no]`
- **Vertical Scaling**: `[yes/no]`

### Availability
- **Uptime Requirement**: `[e.g., 99.9%]`
- **Disaster Recovery**: `[yes/no]`
- **Backup Strategy**: `[description]`

## Architecture
- **Pattern**: `[monolith|microservices|serverless|layered|mvc|mvp|mvvm|event_driven]`
- **Components**:
  - `[Component Name]` - `[Type: service|controller|model|view|utility|middleware]` - `[Responsibility]`
  - `[Component Name]` - `[Type]` - `[Responsibility]`
- **Data Flow**: `[description of how data moves through the system]`

## Technology Stack
### Backend
- **Language**: `[python|javascript|typescript|java|csharp|go|rust]`
- **Framework**: `[specific framework name]`
- **Version**: `[version number]`
- **Additional Libraries**: `[comma-separated list]`

### Frontend (if applicable)
- **Framework**: `[react|vue|angular|svelte|vanilla|none]`
- **UI Library**: `[specific UI library]`
- **Styling**: `[css|scss|tailwind|styled-components|material-ui]`
- **Build Tool**: `[webpack|vite|rollup|etc.]`

### Database
- **Type**: `[postgresql|mysql|mongodb|redis|sqlite|none]`
- **Version**: `[version number]`
- **ORM**: `[specific ORM if applicable]`
- **Migration Strategy**: `[description]`

### Infrastructure
- **Cloud Provider**: `[aws|azure|gcp|local|hybrid]`
- **Container Platform**: `[docker|kubernetes|etc.]`
- **Monitoring**: `[list of monitoring tools]`
- **Logging**: `[logging solution]`
- **CI/CD**: `[CI/CD platform]`

## Quality Requirements
### Testing
- **Coverage Threshold**: `[percentage, e.g., 80%]`
- **Test Types**: `[unit|integration|e2e|performance|security]`
- **Testing Framework**: `[specific framework]`
- **Test Data Strategy**: `[description]`

### Documentation
- **Required Sections**: `[list of required documentation sections]`
- **Format**: `[markdown|rst|html|pdf]`
- **API Documentation**: `[yes/no]`
- **User Guides**: `[yes/no]`
- **Developer Guides**: `[yes/no]`

### Code Standards
- **Style Guide**: `[specific style guide]`
- **Linting Rules**: `[list of linting rules]`
- **Formatting**: `[specific formatter]`
- **Naming Conventions**: `[description]`
- **Complexity Limits**: `[cyclomatic complexity limits]`

## Constraints
### Timeline
- **Deadline**: `[date]`
- **Milestones**:
  - `[milestone 1]`
  - `[milestone 2]`

### Resources
- **Team Size**: `[number]`
- **Budget**: `[budget constraints]`
- **External Dependencies**: `[list of external dependencies]`

### Compatibility
- **Browser Support**: `[list of supported browsers]`
- **OS Support**: `[list of supported operating systems]`
- **Legacy Systems**: `[systems that must be compatible]`

---

**Validation Checklist**:
- [ ] All required fields completed
- [ ] Project name follows naming convention
- [ ] At least one functional requirement defined
- [ ] Technology stack is consistent and compatible
- [ ] Quality requirements are realistic and measurable
- [ ] Timeline is achievable with given resources
