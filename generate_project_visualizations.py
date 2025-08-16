#!/usr/bin/env python3
"""
Generate comprehensive visualizations for all analyzed custom projects
"""
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ProjectInfo:
    name: str
    purpose: str
    total_files: int
    main_technologies: list[str]
    architecture_type: str
    key_components: list[str]
    complexity_score: int


def read_project_intelligence(project_path: Path) -> dict | None:
    """Read project intelligence data from a project directory"""
    intel_file = project_path / ".proj-intel" / "project_analysis.pretty.json"

    if not intel_file.exists():
        print(f"⚠️  No project intelligence data found for {project_path.name}")
        return None

    try:
        with open(intel_file) as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error reading {project_path.name}: {e}")
        return None


def analyze_project(project_path: Path, data: dict) -> ProjectInfo:
    """Extract key information from project intelligence data"""

    # Extract purpose
    purpose_data = data.get("project_purpose", {})
    purpose = purpose_data.get("summary", "Unknown purpose")
    if not purpose or purpose == "Unknown purpose":
        purpose = purpose_data.get("description", "Multi-purpose development project")

    # File count
    file_elements = data.get("file_elements", {})
    total_files = file_elements.get("total_files", 0)

    # Technologies from dependencies
    deps = data.get("dependencies", {})
    technologies = []

    # Check for common frameworks/libraries
    dep_names = []
    if "python_packages" in deps:
        dep_names.extend(deps["python_packages"])
    if "requirements" in deps:
        dep_names.extend([req.get("name", "") for req in deps.get("requirements", [])])

    tech_mapping = {
        "fastapi": "FastAPI",
        "flask": "Flask",
        "django": "Django",
        "streamlit": "Streamlit",
        "neo4j": "Neo4j",
        "redis": "Redis",
        "celery": "Celery",
        "pytest": "PyTest",
        "numpy": "NumPy",
        "pandas": "Pandas",
        "torch": "PyTorch",
        "tensorflow": "TensorFlow",
        "openai": "OpenAI",
        "langchain": "LangChain",
        "chromadb": "ChromaDB",
        "pinecone": "Pinecone",
    }

    for dep in dep_names:
        dep_lower = dep.lower()
        for key, tech in tech_mapping.items():
            if key in dep_lower and tech not in technologies:
                technologies.append(tech)

    # Architecture analysis
    agent_arch = data.get("agent_architecture", {})
    arch_type = "Unknown"

    if agent_arch.get("has_agents", False):
        arch_type = "Multi-Agent System"
    elif "fastapi" in [t.lower() for t in technologies]:
        arch_type = "API Service"
    elif "streamlit" in [t.lower() for t in technologies]:
        arch_type = "Web Application"
    elif total_files > 50:
        arch_type = "Complex Application"
    else:
        arch_type = "Library/Tool"

    # Key components from file structure
    components = []
    if "directory_structure" in file_elements:
        dirs = file_elements["directory_structure"]
        for dir_info in dirs[:5]:  # Top 5 directories
            if isinstance(dir_info, dict) and "name" in dir_info:
                components.append(dir_info["name"])

    # Complexity score (simple heuristic)
    complexity = min(
        100, (total_files // 10) + len(technologies) * 5 + len(components) * 2
    )

    return ProjectInfo(
        name=project_path.name,
        purpose=purpose[:100] + "..." if len(purpose) > 100 else purpose,
        total_files=total_files,
        main_technologies=technologies[:6],  # Limit to 6 main techs
        architecture_type=arch_type,
        key_components=components[:5],  # Top 5 components
        complexity_score=complexity,
    )


def generate_mermaid_diagram(projects: list[ProjectInfo]) -> str:
    """Generate a comprehensive Mermaid diagram for all projects"""

    diagram = """graph TB
    classDef webapp fill:#e1f5fe,stroke:#01579b,stroke-width:2px,color:#000
    classDef api fill:#f3e5f5,stroke:#4a148c,stroke-width:2px,color:#000
    classDef agent fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000
    classDef library fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px,color:#000
    classDef complex fill:#fff8e1,stroke:#f57f17,stroke-width:2px,color:#000
    classDef unknown fill:#f5f5f5,stroke:#616161,stroke-width:2px,color:#000

    subgraph Custom_Projects["Custom Projects in intake/custom/"]
"""

    # Group projects by architecture type
    arch_groups = {}
    for project in projects:
        arch_type = project.architecture_type
        if arch_type not in arch_groups:
            arch_groups[arch_type] = []
        arch_groups[arch_type].append(project)

    # Generate nodes for each project
    for arch_type, project_list in arch_groups.items():
        diagram += f'\n        subgraph {arch_type.replace(" ", "_")}["{arch_type}"]\n'

        for project in project_list:
            # Create node ID (safe for Mermaid)
            node_id = project.name.replace("-", "_").replace(" ", "_")

            # Tech stack display
            tech_display = (
                ", ".join(project.main_technologies)
                if project.main_technologies
                else "No deps detected"
            )

            # Create node with details
            label = f"{project.name}<br/>{project.total_files} files<br/>{tech_display}"
            diagram += f'            {node_id}["{label}"]\n'

            # Apply styling based on architecture
            if "API" in arch_type:
                diagram += f"            {node_id}:::api\n"
            elif "Agent" in arch_type:
                diagram += f"            {node_id}:::agent\n"
            elif "Web" in arch_type:
                diagram += f"            {node_id}:::webapp\n"
            elif "Complex" in arch_type:
                diagram += f"            {node_id}:::complex\n"
            elif "Library" in arch_type:
                diagram += f"            {node_id}:::library\n"
            else:
                diagram += f"            {node_id}:::unknown\n"

        diagram += "        end\n"

    diagram += "\n    end"

    return diagram


def generate_project_summary_table(projects: list[ProjectInfo]) -> str:
    """Generate a markdown table summarizing all projects"""

    table = """# Custom Projects Analysis Summary

| Project | Architecture | Files | Technologies | Purpose |
|---------|--------------|-------|--------------|---------|
"""

    # Sort by complexity score (descending)
    sorted_projects = sorted(projects, key=lambda p: p.complexity_score, reverse=True)

    for project in sorted_projects:
        tech_str = (
            ", ".join(project.main_technologies)
            if project.main_technologies
            else "None detected"
        )
        tech_str = tech_str[:30] + "..." if len(tech_str) > 30 else tech_str

        purpose_str = (
            project.purpose[:60] + "..."
            if len(project.purpose) > 60
            else project.purpose
        )

        table += f"| **{project.name}** | {project.architecture_type} | {project.total_files} | {tech_str} | {purpose_str} |\n"

    return table


def generate_individual_diagrams(projects: list[ProjectInfo]) -> dict[str, str]:
    """Generate individual diagrams for complex projects"""

    individual_diagrams = {}

    for project in projects:
        if project.complexity_score > 30 or project.total_files > 20:
            diagram = f"""graph LR
    classDef main fill:#fff,stroke:#000,stroke-width:2px,color:#000
    
    subgraph {project.name.replace('-', '_')}["{project.name}"]
        Main["{project.name}<br/>{project.total_files} files<br/>{project.architecture_type}"]:::main
"""

            # Add technology nodes
            if project.main_technologies:
                diagram += '\n        subgraph Tech["Technologies"]\n'
                for i, tech in enumerate(project.main_technologies):
                    tech_id = f"T{i}"
                    diagram += f'            {tech_id}["{tech}"]\n'
                    diagram += f"            Main --> {tech_id}\n"
                diagram += "        end\n"

            # Add component nodes
            if project.key_components:
                diagram += '\n        subgraph Comp["Key Components"]\n'
                for i, comp in enumerate(project.key_components):
                    comp_id = f"C{i}"
                    comp_name = comp.replace("/", "_").replace("-", "_")
                    diagram += f'            {comp_id}["{comp}"]\n'
                    diagram += f"            Main --> {comp_id}\n"
                diagram += "        end\n"

            diagram += "    end"
            individual_diagrams[project.name] = diagram

    return individual_diagrams


def main():
    custom_dir = Path("/home/opsvi/master_root/intake/custom")

    print("🔍 Reading project intelligence data...")

    projects = []
    for project_dir in custom_dir.iterdir():
        if project_dir.is_dir() and project_dir.name != ".proj-intel":
            data = read_project_intelligence(project_dir)
            if data:
                project_info = analyze_project(project_dir, data)
                projects.append(project_info)
                print(
                    f"✅ Analyzed {project_info.name}: {project_info.total_files} files, {project_info.architecture_type}"
                )

    if not projects:
        print("❌ No project data found!")
        return

    print(f"\n📊 Generating visualizations for {len(projects)} projects...")

    # Generate comprehensive diagram
    main_diagram = generate_mermaid_diagram(projects)

    # Generate summary table
    summary_table = generate_project_summary_table(projects)

    # Generate individual diagrams
    individual_diagrams = generate_individual_diagrams(projects)

    # Save outputs
    output_dir = custom_dir / "visualizations"
    output_dir.mkdir(exist_ok=True)

    # Save main diagram
    with open(output_dir / "all_projects_diagram.md", "w") as f:
        f.write(f"# All Custom Projects Overview\n\n```mermaid\n{main_diagram}\n```\n")

    # Save summary table
    with open(output_dir / "projects_summary.md", "w") as f:
        f.write(summary_table)

    # Save individual diagrams
    for project_name, diagram in individual_diagrams.items():
        with open(output_dir / f"{project_name}_diagram.md", "w") as f:
            f.write(f"# {project_name} Architecture\n\n```mermaid\n{diagram}\n```\n")

    # Save JSON data for further processing
    projects_data = [
        {
            "name": p.name,
            "purpose": p.purpose,
            "total_files": p.total_files,
            "technologies": p.main_technologies,
            "architecture": p.architecture_type,
            "components": p.key_components,
            "complexity": p.complexity_score,
        }
        for p in projects
    ]

    with open(output_dir / "projects_data.json", "w") as f:
        json.dump(projects_data, f, indent=2)

    print(f"\n✅ Visualizations saved to: {output_dir}")
    print(f"📊 Generated {len(individual_diagrams)} individual project diagrams")
    print(f"📋 Main overview diagram covers {len(projects)} projects")


if __name__ == "__main__":
    main()
