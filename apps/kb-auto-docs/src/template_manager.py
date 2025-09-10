#!/usr/bin/env python3
"""
KB Documentation Templates and Rules System
Stores documentation templates and generation rules in the KB itself,
making the documentation system configurable and self-improving.
"""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from neo4j import GraphDatabase


@dataclass
class DocumentTemplate:
    """Documentation template structure"""

    template_id: str
    name: str
    type: str  # markdown, diagram, html, mermaid
    purpose: str
    template_content: str
    variables: List[str]  # Variables to be filled from KB
    queries: Dict[str, str]  # Cypher queries to get data
    rules: List[str]  # Rules for using this template
    priority: int = 0
    active: bool = True


@dataclass
class DiagramRule:
    """Rules for diagram generation"""

    rule_id: str
    name: str
    condition: str  # When to apply this rule
    action: str  # What to do
    parameters: Dict[str, Any]
    priority: int = 0


class KBTemplateManager:
    """Manage documentation templates and rules in the KB"""

    def __init__(self):
        self.driver = GraphDatabase.driver(
            "bolt://localhost:7687", auth=("neo4j", "password")
        )

    def initialize_templates(self):
        """Store default templates and rules in the KB"""

        templates = [
            DocumentTemplate(
                template_id="system_overview",
                name="System Overview Template",
                type="markdown",
                purpose="Generate high-level system documentation",
                template_content="""# {title}

*Generated: {timestamp}*
*Source: Knowledge Base ({total_knowledge} entries)*

## System Purpose
{system_purpose}

## Architecture Overview
{architecture_summary}

## Key Components
{component_list}

## Statistics
- Total Knowledge Entries: {total_knowledge}
- Active Projects: {project_count}
- Knowledge Types: {knowledge_types}
- Vector Collections: {vector_collections}

## Component Relationships
{relationships_table}

## Recent Changes
{recent_changes}
""",
                variables=[
                    "title",
                    "timestamp",
                    "system_purpose",
                    "architecture_summary",
                    "component_list",
                    "total_knowledge",
                    "project_count",
                    "knowledge_types",
                    "vector_collections",
                    "relationships_table",
                    "recent_changes",
                ],
                queries={
                    "total_knowledge": "MATCH (k:Knowledge) RETURN count(k) as value",
                    "project_count": "MATCH (p:Project) RETURN count(p) as value",
                    "knowledge_types": """
                        MATCH (k:Knowledge)
                        WHERE k.knowledge_type IS NOT NULL
                        RETURN count(DISTINCT k.knowledge_type) as value
                    """,
                    "relationships_table": """
                        MATCH (p:Project)-[r]->(k:Knowledge)
                        RETURN type(r) as relationship, count(*) as count
                        ORDER BY count DESC
                    """,
                    "recent_changes": """
                        MATCH (k:Knowledge)
                        WHERE k.created_at > datetime() - duration('P1D')
                        RETURN k.knowledge_type as type, count(*) as count
                        ORDER BY count DESC
                        LIMIT 5
                    """,
                },
                rules=[
                    "Update at least daily",
                    "Include all active projects",
                    "Highlight recent changes",
                    "Show relationships between components",
                ],
                priority=1,
            ),
            DocumentTemplate(
                template_id="component_detail",
                name="Component Detail Template",
                type="markdown",
                purpose="Generate detailed documentation for a specific component",
                template_content="""# {component_name} Documentation

## Overview
{component_description}

## Location
- **Path**: {component_path}
- **Type**: {component_type}
- **Project**: {parent_project}

## Functionality
{functionality_list}

## Dependencies
{dependencies}

## Complexity Analysis
{complexity_metrics}

## Related Knowledge
{related_knowledge}

## Usage Examples
{usage_examples}

## Recent Updates
{recent_updates}
""",
                variables=[
                    "component_name",
                    "component_description",
                    "component_path",
                    "component_type",
                    "parent_project",
                    "functionality_list",
                    "dependencies",
                    "complexity_metrics",
                    "related_knowledge",
                    "usage_examples",
                    "recent_updates",
                ],
                queries={
                    "complexity_metrics": """
                        MATCH (k:Knowledge {knowledge_type: 'CODE_ANALYSIS'})
                        WHERE k.file_path CONTAINS $component
                        RETURN k.complexity as complexity, k.metrics as metrics
                    """,
                    "related_knowledge": """
                        MATCH (k:Knowledge)
                        WHERE k.content CONTAINS $component
                        RETURN k.knowledge_type as type, k.content as content
                        LIMIT 10
                    """,
                    "dependencies": """
                        MATCH (k:Knowledge)-[:DEPENDS_ON]->(d:Knowledge)
                        WHERE k.file_path CONTAINS $component
                        RETURN d.file_path as dependency
                    """,
                },
                rules=[
                    "Include all relevant metrics",
                    "Show code examples when available",
                    "Link to related components",
                    "Update when component changes",
                ],
                priority=2,
            ),
            DocumentTemplate(
                template_id="architecture_diagram",
                name="Architecture Diagram Template",
                type="diagram",
                purpose="Generate system architecture diagrams",
                template_content="""digraph Architecture {
    rankdir={rank_direction};
    bgcolor="{background_color}";

    // Style definitions
    node [shape=box, style=filled, fillcolor=lightblue];
    edge [color=gray];

    // Projects
    {project_nodes}

    // Components
    {component_nodes}

    // Relationships
    {relationship_edges}

    // Legend
    subgraph cluster_legend {
        label="Legend";
        style=solid;
        {legend_items}
    }
}""",
                variables=[
                    "rank_direction",
                    "background_color",
                    "project_nodes",
                    "component_nodes",
                    "relationship_edges",
                    "legend_items",
                ],
                queries={
                    "project_nodes": """
                        MATCH (p:Project)
                        RETURN p.path as id, p.name as label, p.type as type
                    """,
                    "component_nodes": """
                        MATCH (k:Knowledge)
                        WHERE k.knowledge_type IN ['APP_INSTRUCTIONS', 'CODE_ANALYSIS']
                        RETURN DISTINCT k.file_path as id, k.knowledge_type as type
                        LIMIT 20
                    """,
                    "relationship_edges": """
                        MATCH (p:Project)-[r]->(k:Knowledge)
                        RETURN p.path as from, k.id as to, type(r) as label
                        LIMIT 50
                    """,
                },
                rules=[
                    "Limit nodes to prevent clutter",
                    "Group related components",
                    "Use consistent color coding",
                    "Include legend for clarity",
                ],
                priority=1,
            ),
            DocumentTemplate(
                template_id="data_flow_diagram",
                name="Data Flow Diagram Template",
                type="mermaid",
                purpose="Generate data flow diagrams",
                template_content="""graph {flow_direction}
    %% Data Flow Diagram
    %% Generated: {timestamp}

    %% Style definitions
    classDef userStyle fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef serviceStyle fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef dataStyle fill:#fff3e0,stroke:#e65100,stroke-width:2px

    %% Nodes
    {data_nodes}

    %% Flows
    {data_flows}

    %% Apply styles
    {style_applications}
""",
                variables=[
                    "flow_direction",
                    "timestamp",
                    "data_nodes",
                    "data_flows",
                    "style_applications",
                ],
                queries={
                    "data_nodes": """
                        MATCH (k:Knowledge)
                        WHERE k.knowledge_type IN ['WORKFLOW', 'CODE_PATTERN']
                        RETURN DISTINCT k.id as id, k.knowledge_type as type
                        LIMIT 15
                    """,
                    "data_flows": """
                        MATCH (k1:Knowledge)-[r]->(k2:Knowledge)
                        WHERE type(r) IN ['CALLS', 'DEPENDS_ON', 'TRIGGERS']
                        RETURN k1.id as from, k2.id as to, type(r) as label
                        LIMIT 30
                    """,
                },
                rules=[
                    "Show data flow direction clearly",
                    "Group by data type",
                    "Highlight critical paths",
                    "Keep layout clean and readable",
                ],
                priority=2,
            ),
        ]

        diagram_rules = [
            DiagramRule(
                rule_id="complexity_coloring",
                name="Color by Complexity",
                condition="node.type == 'CODE_ANALYSIS'",
                action="set_color",
                parameters={"high": "red", "medium": "yellow", "low": "green"},
                priority=1,
            ),
            DiagramRule(
                rule_id="project_grouping",
                name="Group by Project",
                condition="node.project_path IS NOT NULL",
                action="create_subgraph",
                parameters={"style": "dotted", "label_prefix": "Project: "},
                priority=1,
            ),
            DiagramRule(
                rule_id="relationship_styling",
                name="Style Relationships",
                condition="edge.type IN ['HAS_KNOWLEDGE', 'HAS_INSTRUCTION']",
                action="set_edge_style",
                parameters={
                    "HAS_KNOWLEDGE": {"style": "dashed", "color": "blue"},
                    "HAS_INSTRUCTION": {"style": "bold", "color": "green"},
                    "HAS_ANALYSIS": {"style": "dotted", "color": "red"},
                },
                priority=2,
            ),
            DiagramRule(
                rule_id="node_sizing",
                name="Size by Importance",
                condition="node.metrics IS NOT NULL",
                action="set_size",
                parameters={
                    "metric": "lines_of_code",
                    "min_size": 10,
                    "max_size": 50,
                    "scale": "logarithmic",
                },
                priority=3,
            ),
            DiagramRule(
                rule_id="layout_optimization",
                name="Optimize Layout",
                condition="diagram.node_count > 20",
                action="apply_layout",
                parameters={
                    "algorithm": "hierarchical",
                    "direction": "top-bottom",
                    "node_separation": 50,
                    "rank_separation": 100,
                },
                priority=4,
            ),
        ]

        with self.driver.session() as session:
            # Store templates
            for template in templates:
                # Serialize complex fields
                props = asdict(template)
                props["variables"] = json.dumps(props["variables"])
                props["queries"] = json.dumps(props["queries"])
                props["rules"] = json.dumps(props["rules"])

                session.run(
                    """
                    MERGE (t:DocumentTemplate {template_id: $template_id})
                    SET t += $properties,
                        t.updated_at = datetime()
                """,
                    template_id=template.template_id,
                    properties=props,
                )
                print(f"✓ Stored template: {template.name}")

            # Store diagram rules
            for rule in diagram_rules:
                # Serialize complex fields
                props = asdict(rule)
                props["parameters"] = json.dumps(props["parameters"])

                session.run(
                    """
                    MERGE (r:DiagramRule {rule_id: $rule_id})
                    SET r += $properties,
                        r.updated_at = datetime()
                """,
                    rule_id=rule.rule_id,
                    properties=props,
                )
                print(f"✓ Stored rule: {rule.name}")

    def get_template(self, template_id: str) -> Optional[Dict]:
        """Retrieve a template from the KB"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (t:DocumentTemplate {template_id: $template_id})
                RETURN t
            """,
                template_id=template_id,
            ).single()

            if result:
                return dict(result["t"])
            return None

    def get_rules_for_diagram(self, diagram_type: str) -> List[Dict]:
        """Get applicable rules for a diagram type"""
        with self.driver.session() as session:
            results = session.run(
                """
                MATCH (r:DiagramRule)
                WHERE r.condition CONTAINS $diagram_type
                   OR r.condition = 'always'
                RETURN r
                ORDER BY r.priority
            """,
                diagram_type=diagram_type,
            )

            return [dict(r["r"]) for r in results]

    def execute_template_query(
        self, query: str, parameters: Optional[Dict] = None
    ) -> List[Dict]:
        """Execute a template's data query"""
        with self.driver.session() as session:
            if parameters:
                results = session.run(query, parameters)
            else:
                results = session.run(query)

            return [dict(r) for r in results]

    def render_template(self, template_id: str, context: Optional[Dict] = None) -> str:
        """Render a template with data from the KB"""
        template = self.get_template(template_id)
        if not template:
            return f"Template {template_id} not found"

        # Execute queries to get data
        data = {
            "timestamp": datetime.now().isoformat(),
            "title": "System Documentation",
        }

        if context:
            data.update(context)

        # Execute each query defined in the template
        queries = json.loads(template.get("queries", "{}"))
        for var_name, query in queries.items():
            try:
                results = self.execute_template_query(query, context)
                if results:
                    if len(results) == 1 and "value" in results[0]:
                        data[var_name] = results[0]["value"]
                    else:
                        data[var_name] = results
                else:
                    data[var_name] = "No data"
            except Exception as e:
                data[var_name] = f"Error: {e}"

        # Format complex data
        for key, value in data.items():
            if isinstance(value, list) and value and isinstance(value[0], dict):
                # Format as table
                if key.endswith("_table"):
                    table = ["| " + " | ".join(value[0].keys()) + " |"]
                    table.append("|" + "|".join(["---"] * len(value[0])) + "|")
                    for row in value:
                        table.append(
                            "| " + " | ".join(str(v) for v in row.values()) + " |"
                        )
                    data[key] = "\n".join(table)
                else:
                    # Format as list
                    items = []
                    for item in value:
                        items.append(
                            "- " + ", ".join(f"{k}: {v}" for k, v in item.items())
                        )
                    data[key] = "\n".join(items)

        # Render template
        template_content = template["template_content"]
        try:
            rendered = template_content.format(**data)
        except KeyError as e:
            rendered = template_content
            rendered += f"\n\n*Missing variable: {e}*"

        return rendered

    def update_template(self, template_id: str, updates: Dict):
        """Update a template based on usage feedback"""
        with self.driver.session() as session:
            session.run(
                """
                MATCH (t:DocumentTemplate {template_id: $template_id})
                SET t += $updates,
                    t.updated_at = datetime()
            """,
                template_id=template_id,
                updates=updates,
            )

    def add_template_usage_feedback(
        self, template_id: str, success: bool, feedback: str
    ):
        """Track template usage and effectiveness"""
        with self.driver.session() as session:
            session.run(
                """
                MATCH (t:DocumentTemplate {template_id: $template_id})
                CREATE (f:TemplateFeedback {
                    id: randomUUID(),
                    template_id: $template_id,
                    success: $success,
                    feedback: $feedback,
                    timestamp: datetime()
                })
                CREATE (t)-[:HAS_FEEDBACK]->(f)
            """,
                template_id=template_id,
                success=success,
                feedback=feedback,
            )

    def get_best_template_for_purpose(self, purpose: str) -> Optional[str]:
        """Find the best template for a given purpose"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (t:DocumentTemplate)
                WHERE t.purpose CONTAINS $purpose
                   AND t.active = true
                OPTIONAL MATCH (t)-[:HAS_FEEDBACK]->(f:TemplateFeedback)
                WITH t, avg(CASE WHEN f.success THEN 1 ELSE 0 END) as success_rate
                RETURN t.template_id as template_id
                ORDER BY t.priority DESC, success_rate DESC
                LIMIT 1
            """,
                purpose=purpose,
            ).single()

            if result:
                return result["template_id"]
            return None


def main():
    """Initialize templates and demonstrate usage"""
    print("=" * 70)
    print("Initializing Documentation Templates in Knowledge Base")
    print("=" * 70)

    manager = KBTemplateManager()

    try:
        # Initialize templates
        print("\n[1] Storing Templates and Rules...")
        manager.initialize_templates()

        # Demonstrate template rendering
        print("\n[2] Rendering System Overview...")
        overview = manager.render_template(
            "system_overview",
            {
                "system_purpose": "Multi-project knowledge management with intelligent code analysis",
                "architecture_summary": "Neo4j + Qdrant + Dynamic Instructions + Project Scoping",
            },
        )

        # Save rendered documentation
        with open("template_generated_overview.md", "w") as f:
            f.write(overview)
        print("✓ Saved to template_generated_overview.md")

        # Find best template for a purpose
        print("\n[3] Finding Best Template for 'component analysis'...")
        best = manager.get_best_template_for_purpose("component")
        if best:
            print(f"✓ Best template: {best}")

        # Get rules for diagram generation
        print("\n[4] Getting Diagram Generation Rules...")
        rules = manager.get_rules_for_diagram("architecture")
        for rule in rules:
            print(f"  - {rule['name']}: {rule['action']}")

        print("\n" + "=" * 70)
        print("✓ Template System Initialized!")
        print("=" * 70)
        print("\nKey Features:")
        print("1. Templates stored in KB (self-documenting)")
        print("2. Rules control diagram generation")
        print("3. Templates include data queries")
        print("4. Usage feedback improves templates")
        print("5. Best template selection based on purpose")

    finally:
        manager.driver.close()


if __name__ == "__main__":
    main()
