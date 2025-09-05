# DiagramMaster Project Structure

## Directory Organization

### `/profiles/`
Agent profiles, capabilities, and configuration files
- `agent-profile.md` - Complete DiagramMaster specification
- `color-schemes.md` - High-contrast visual design system
- `syntax-reference.md` - Mermaid technical mastery guide

### `/templates/`
Reusable diagram templates and patterns
- `process-flows/` - Standard workflow templates
- `architectures/` - System design patterns
- `decision-trees/` - Choice frameworks
- `data-flows/` - Information movement patterns

### `/output/`
Generated diagrams organized by context

#### `/output/conversations/`
Live conversation diagrams (session-based)
- `YYYY-MM-DD/` - Daily folders
- `session-{id}/` - Individual conversation threads

#### `/output/references/`
Study-quality reference diagrams
- `by-topic/` - Subject matter organization
- `by-type/` - Diagram type classification
- `high-value/` - Most referenced/useful diagrams

#### `/output/archives/`
Historical diagrams and deprecated versions
- Maintaining diagram evolution history
- Version control for iterative improvements

### `/docs/`
Documentation and guides
- Usage examples
- Best practices
- Integration guides

## Naming Conventions

### File Names
- `YYYY-MM-DD_topic-name_diagram-type.md`
- Example: `2025-09-05_api-architecture_sequence.md`

### Session Organization
- Conversation diagrams grouped by date and session
- Reference diagrams categorized by subject matter
- Templates organized by use case patterns

## Quality Standards
- All diagrams must render without syntax errors
- High-contrast color schemes enforced
- Information density optimized for reference use
- Autonomous generation with zero administrative overhead
