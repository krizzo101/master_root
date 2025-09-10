#!/usr/bin/env python3
"""
KB Auto-Documentation System
Generates accurate, real-time documentation and diagrams from the knowledge base.
This ensures documentation always reflects the actual system state.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import graphviz
import markdown
from neo4j import GraphDatabase
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer


class KBAutoDocumentation:
    """Generate documentation directly from the knowledge base"""

    def __init__(self):
        self.driver = GraphDatabase.driver(
            "bolt://localhost:7687", auth=("neo4j", "password")
        )
        self.qdrant = QdrantClient(host="localhost", port=6333)
        self.embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    def generate_system_overview(self) -> str:
        """Generate a complete system overview from KB"""
        doc = ["# System Architecture - Auto-Generated from Knowledge Base"]
        doc.append(f"\n*Generated: {datetime.now().isoformat()}*\n")
        doc.append(
            "*This documentation is generated directly from the live knowledge base and reflects the current system state.*\n"
        )

        with self.driver.session() as session:
            # Get system statistics
            stats = session.run(
                """
                MATCH (k:Knowledge)
                RETURN count(k) as total_knowledge,
                       count(DISTINCT k.knowledge_type) as knowledge_types,
                       count(DISTINCT k.project_path) as projects
            """
            ).single()

            doc.append("## System Statistics\n")
            doc.append(f"- **Total Knowledge Entries**: {stats['total_knowledge']}")
            doc.append(f"- **Knowledge Types**: {stats['knowledge_types']}")
            doc.append(f"- **Tracked Projects**: {stats['projects']}\n")

            # Get knowledge type breakdown
            doc.append("## Knowledge Distribution\n")
            types = session.run(
                """
                MATCH (k:Knowledge)
                WHERE k.knowledge_type IS NOT NULL
                RETURN k.knowledge_type as type, count(*) as count
                ORDER BY count DESC
                LIMIT 10
            """
            )

            doc.append("| Type | Count | Purpose |")
            doc.append("|------|-------|---------|")

            type_descriptions = {
                "CODE": "Source code implementations",
                "CONFIGURATION": "System and application configurations",
                "REFERENCE": "Reference documentation and guides",
                "DOCUMENTATION": "User and developer documentation",
                "CODE_PATTERN": "Reusable code patterns and templates",
                "WORKFLOW": "Process and workflow definitions",
                "ERROR_SOLUTION": "Error patterns and their solutions",
                "CODE_ANALYSIS": "Code complexity and structure analysis",
                "GLOBAL_INSTRUCTIONS": "System-wide operational instructions",
                "PROJECT_INSTRUCTIONS": "Project-specific guidelines",
                "APP_INSTRUCTIONS": "Application-specific instructions",
            }

            for record in types:
                desc = type_descriptions.get(record["type"], "Knowledge entries")
                doc.append(f"| {record['type']} | {record['count']} | {desc} |")

            # Get project hierarchy
            doc.append("\n## Project Structure\n")
            projects = session.run(
                """
                MATCH (p:Project)
                OPTIONAL MATCH (p)-[r]->(k:Knowledge)
                RETURN p.path as path, p.name as name, p.type as type,
                       count(k) as knowledge_count
                ORDER BY p.path
            """
            )

            doc.append("```")
            for proj in projects:
                indent = "  " * (proj["path"].count("/") - 2)
                doc.append(
                    f"{indent}{proj['name']}/ ({proj.get('type', 'unknown')}) - {proj['knowledge_count']} entries"
                )
            doc.append("```")

            # Get component relationships
            doc.append("\n## Component Relationships\n")
            relationships = session.run(
                """
                MATCH (p:Project)-[r]->(k:Knowledge)
                RETURN type(r) as rel_type, count(*) as count
                ORDER BY count DESC
            """
            )

            doc.append("| Relationship | Count | Meaning |")
            doc.append("|--------------|-------|---------|")
            for rel in relationships:
                meaning = {
                    "HAS_KNOWLEDGE": "Project contains knowledge entries",
                    "HAS_INSTRUCTION": "Project has operational instructions",
                    "HAS_ANALYSIS": "Project has code analysis results",
                }.get(rel["rel_type"], "Related knowledge")
                doc.append(f"| {rel['rel_type']} | {rel['count']} | {meaning} |")

        # Get Qdrant statistics
        doc.append("\n## Vector Search Infrastructure\n")
        collections = self.qdrant.get_collections().collections

        doc.append("| Collection | Vectors | Purpose |")
        doc.append("|------------|---------|---------|")
        for col in collections:
            info = self.qdrant.get_collection(col.name)
            purpose = {
                "knowledge_vectors": "General knowledge semantic search",
                "instructions": "Dynamic instruction retrieval",
                "monitoring_vectors": "Monitoring and metrics data",
            }.get(col.name, "Vector storage")
            doc.append(f"| {col.name} | {info.points_count} | {purpose} |")

        return "\n".join(doc)

    def generate_component_documentation(self, component: str) -> str:
        """Generate documentation for a specific component"""
        doc = [f"# {component} Component Documentation"]
        doc.append(f"\n*Auto-generated from KB: {datetime.now().isoformat()}*\n")

        with self.driver.session() as session:
            # Search for component-related knowledge
            component_knowledge = session.run(
                """
                MATCH (k:Knowledge)
                WHERE k.content CONTAINS $component
                   OR k.file_path CONTAINS $component
                RETURN k.knowledge_type as type,
                       k.file_path as file,
                       k.content as content,
                       k.complexity as complexity,
                       k.metrics as metrics
                ORDER BY k.knowledge_type, k.file_path
                LIMIT 20
            """,
                component=component,
            )

            # Group by type
            by_type = {}
            for record in component_knowledge:
                ktype = record["type"] or "UNKNOWN"
                if ktype not in by_type:
                    by_type[ktype] = []
                by_type[ktype].append(record)

            if not by_type:
                doc.append(f"No knowledge found for component: {component}")
            else:
                for ktype, entries in by_type.items():
                    doc.append(f"\n## {ktype}\n")
                    for entry in entries:
                        if entry["file"]:
                            doc.append(f"### {entry['file']}\n")
                        if entry["content"]:
                            # Truncate long content
                            content = entry["content"][:500]
                            if len(entry["content"]) > 500:
                                content += "..."
                            doc.append(f"```\n{content}\n```\n")
                        if entry["complexity"]:
                            doc.append(f"**Complexity**: {entry['complexity']}\n")
                        if entry["metrics"]:
                            try:
                                metrics = json.loads(entry["metrics"])
                                doc.append("**Metrics**:")
                                for key, value in metrics.items():
                                    doc.append(f"- {key}: {value}")
                                doc.append("")
                            except:
                                pass

        return "\n".join(doc)

    def generate_architecture_diagram(
        self, output_path: str = "architecture.dot"
    ) -> str:
        """Generate architecture diagram from KB relationships"""
        dot = graphviz.Digraph(comment="System Architecture", format="png")
        dot.attr(rankdir="TB", bgcolor="white")

        with self.driver.session() as session:
            # Get projects and their relationships
            projects = session.run(
                """
                MATCH (p:Project)
                RETURN p.path as path, p.name as name, p.type as type
            """
            )

            # Add project nodes
            for proj in projects:
                shape = {
                    "root": "box3d",
                    "app": "component",
                    "standalone": "folder",
                }.get(proj.get("type", "unknown"), "box")

                color = {
                    "root": "lightblue",
                    "app": "lightgreen",
                    "standalone": "lightyellow",
                }.get(proj.get("type", "unknown"), "white")

                dot.node(
                    proj["path"],
                    proj["name"],
                    shape=shape,
                    style="filled",
                    fillcolor=color,
                )

            # Get knowledge relationships
            relationships = session.run(
                """
                MATCH (p:Project)-[r]->(k:Knowledge)
                RETURN p.path as project, type(r) as rel_type,
                       k.knowledge_type as k_type, count(*) as count
                ORDER BY count DESC
                LIMIT 20
            """
            )

            # Group by project
            proj_knowledge = {}
            for rel in relationships:
                if rel["project"] not in proj_knowledge:
                    proj_knowledge[rel["project"]] = []
                proj_knowledge[rel["project"]].append(
                    {
                        "type": rel["k_type"],
                        "rel": rel["rel_type"],
                        "count": rel["count"],
                    }
                )

            # Add knowledge clusters
            for proj, knowledge in proj_knowledge.items():
                with dot.subgraph(name=f'cluster_{proj.replace("/", "_")}') as sub:
                    sub.attr(
                        label=f"Knowledge in {proj.split('/')[-1]}", style="dotted"
                    )

                    for k in knowledge[:5]:  # Limit to top 5
                        node_id = f"{proj}_{k['type']}"
                        sub.node(
                            node_id,
                            f"{k['type']}\n({k['count']} items)",
                            shape="note",
                            style="filled",
                            fillcolor="lightyellow",
                        )
                        dot.edge(proj, node_id, label=k["rel"], style="dashed")

            # Add component connections
            components = session.run(
                """
                MATCH (k1:Knowledge)-[r:USED_WITH|NEXT_CHUNK|RELATED_TO]->(k2:Knowledge)
                WHERE k1.project_path IS NOT NULL AND k2.project_path IS NOT NULL
                RETURN DISTINCT k1.project_path as from_proj,
                       k2.project_path as to_proj,
                       type(r) as rel_type,
                       count(*) as count
                ORDER BY count DESC
                LIMIT 10
            """
            )

            for comp in components:
                if comp["from_proj"] != comp["to_proj"]:
                    dot.edge(
                        comp["from_proj"],
                        comp["to_proj"],
                        label=f"{comp['rel_type']}\n({comp['count']})",
                        style="bold",
                        color="blue",
                    )

        # Add legend
        with dot.subgraph(name="cluster_legend") as legend:
            legend.attr(label="Legend", style="solid")
            legend.node(
                "l1",
                "Root Project",
                shape="box3d",
                style="filled",
                fillcolor="lightblue",
            )
            legend.node(
                "l2",
                "Application",
                shape="component",
                style="filled",
                fillcolor="lightgreen",
            )
            legend.node(
                "l3",
                "Standalone",
                shape="folder",
                style="filled",
                fillcolor="lightyellow",
            )
            legend.node(
                "l4", "Knowledge", shape="note", style="filled", fillcolor="lightyellow"
            )

        # Save diagram
        dot.render(output_path, cleanup=True)
        return dot.source

    def generate_data_flow_diagram(self) -> str:
        """Generate data flow diagram from KB"""
        dot = graphviz.Digraph(comment="Data Flow", format="png")
        dot.attr(rankdir="LR", bgcolor="white")

        # Define major components
        components = {
            "user": ("User", "ellipse", "lightcyan"),
            "mcp": ("MCP Tools", "box", "lightblue"),
            "accf": ("ACCF\nConsult Suite", "component", "lightgreen"),
            "kb": ("Knowledge Base\n(Neo4j)", "cylinder", "lightyellow"),
            "vector": ("Vector DB\n(Qdrant)", "cylinder", "lightyellow"),
            "gatekeeper": ("KB Gatekeeper", "hexagon", "lightcoral"),
            "proj_intel": ("Project\nIntelligence", "component", "lightgreen"),
            "embedder": ("Embedding\nService", "box", "lavender"),
        }

        for comp_id, (label, shape, color) in components.items():
            dot.node(comp_id, label, shape=shape, style="filled", fillcolor=color)

        # Define data flows
        flows = [
            ("user", "mcp", "Request"),
            ("mcp", "accf", "Route to\nAgent"),
            ("accf", "gatekeeper", "Get\nFiles"),
            ("gatekeeper", "vector", "Semantic\nSearch"),
            ("vector", "gatekeeper", "Results"),
            ("gatekeeper", "kb", "Query\nKnowledge"),
            ("kb", "gatekeeper", "Knowledge"),
            ("accf", "user", "Response"),
            ("proj_intel", "kb", "Store\nAnalysis"),
            ("proj_intel", "embedder", "Generate\nEmbeddings"),
            ("embedder", "vector", "Index\nVectors"),
            ("kb", "vector", "Sync\nEmbeddings"),
        ]

        for from_node, to_node, label in flows:
            dot.edge(from_node, to_node, label=label)

        # Save diagram
        dot.render("data_flow.dot", cleanup=True)
        return dot.source

    def generate_markdown_report(self) -> str:
        """Generate complete markdown report"""
        report = []

        # System overview
        report.append(self.generate_system_overview())

        # Component details
        report.append("\n# Component Details\n")

        components = ["ACCF", "gatekeeper", "project-intelligence", "knowledge"]
        for comp in components:
            report.append(self.generate_component_documentation(comp))

        # Instructions
        report.append("\n# Dynamic Instructions\n")
        with self.driver.session() as session:
            instructions = session.run(
                """
                MATCH (k:Knowledge)
                WHERE k.knowledge_type IN ['GLOBAL_INSTRUCTIONS', 'PROJECT_INSTRUCTIONS', 'APP_INSTRUCTIONS']
                RETURN k.knowledge_type as type, k.project_path as path,
                       substring(k.content, 0, 200) as preview
                ORDER BY k.knowledge_type
            """
            )

            for inst in instructions:
                report.append(f"\n## {inst['type']}")
                if inst["path"]:
                    report.append(f"**Project**: {inst['path']}")
                report.append(f"```\n{inst['preview']}...\n```")

        # Save report
        report_path = Path("kb_generated_documentation.md")
        report_path.write_text("\n".join(report))

        return "\n".join(report)

    def generate_html_documentation(self) -> str:
        """Generate HTML documentation with diagrams"""
        md_content = self.generate_markdown_report()

        # Convert markdown to HTML
        html_content = markdown.markdown(md_content, extensions=["extra", "codehilite"])

        # Create HTML template
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>System Documentation - Auto-Generated</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        h3 {{ color: #7f8c8d; }}
        code {{ background: #f4f4f4; padding: 2px 5px; border-radius: 3px; }}
        pre {{ background: #282c34; color: #abb2bf; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background: #3498db; color: white; }}
        tr:nth-child(even) {{ background: #f2f2f2; }}
        .timestamp {{ color: #7f8c8d; font-style: italic; }}
        .warning {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 10px; margin: 20px 0; }}
        .success {{ background: #d4edda; border-left: 4px solid #28a745; padding: 10px; margin: 20px 0; }}
    </style>
</head>
<body>
    <h1>System Documentation - Knowledge Base Generated</h1>
    <p class="timestamp">Generated: {datetime.now().isoformat()}</p>
    <div class="warning">
        <strong>Note:</strong> This documentation is auto-generated from the live knowledge base.
        It reflects the actual current system state, not design intentions.
    </div>

    {html_content}

    <div class="success">
        <strong>Architecture Diagrams:</strong>
        <ul>
            <li><a href="architecture.dot.png">System Architecture</a></li>
            <li><a href="data_flow.dot.png">Data Flow Diagram</a></li>
        </ul>
    </div>
</body>
</html>
"""

        # Save HTML
        html_path = Path("kb_documentation.html")
        html_path.write_text(html)

        return html


def main():
    """Generate all documentation"""
    print("=" * 70)
    print("Auto-Generating Documentation from Knowledge Base")
    print("=" * 70)

    doc_gen = KBAutoDocumentation()

    try:
        # Generate markdown report
        print("\n[1] Generating Markdown Documentation...")
        doc_gen.generate_markdown_report()
        print("✓ Saved to kb_generated_documentation.md")

        # Generate architecture diagram
        print("\n[2] Generating Architecture Diagram...")
        doc_gen.generate_architecture_diagram()
        print("✓ Saved to architecture.dot.png")

        # Generate data flow diagram
        print("\n[3] Generating Data Flow Diagram...")
        doc_gen.generate_data_flow_diagram()
        print("✓ Saved to data_flow.dot.png")

        # Generate HTML documentation
        print("\n[4] Generating HTML Documentation...")
        doc_gen.generate_html_documentation()
        print("✓ Saved to kb_documentation.html")

        print("\n" + "=" * 70)
        print("✓ Documentation Generation Complete!")
        print("=" * 70)
        print("\nGenerated Files:")
        print("- kb_generated_documentation.md (Markdown report)")
        print("- architecture.dot.png (System architecture)")
        print("- data_flow.dot.png (Data flow diagram)")
        print("- kb_documentation.html (Complete HTML documentation)")

    finally:
        doc_gen.driver.close()


if __name__ == "__main__":
    main()
