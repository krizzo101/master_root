#!/usr/bin/env python3
"""
Generate comprehensive visualizations for all analyzed custom projects
Fixed to handle actual project intelligence data structure
"""
import json
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ProjectInfo:
    name: str
    purpose: str
    total_files: int
    main_technologies: List[str]
    architecture_type: str
    key_components: List[str]
    complexity_score: int


def read_project_intelligence(project_path: Path) -> Optional[Dict]:
    """Read project intelligence data from a project directory"""
    intel_file = project_path / ".proj-intel" / "project_analysis.pretty.json"

    if not intel_file.exists():
        print(f"⚠️  No project intelligence data found for {project_path.name}")
        return None

    try:
        with open(intel_file, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error reading {project_path.name}: {e}")
        return None


def extract_collector_data(data: Dict, collector_name: str) -> Optional[Dict]:
    """Extract data from a specific collector"""
    collectors = data.get("collectors", [])
    for collector in collectors:
        if collector.get("collector") == collector_name:
            return collector.get("data", {})
    return None


def analyze_project(project_path: Path, data: Dict) -> ProjectInfo:
    """Extract key information from project intelligence data"""

    # Extract purpose from ProjectPurposeCollector
    purpose_data = extract_collector_data(data, "ProjectPurposeCollector") or {}
    project_name = purpose_data.get("project_name", project_path.name)
    description = purpose_data.get("description", "Unknown purpose")
    purpose = (
        f"{project_name}: {description}"
        if project_name != project_path.name
        else description
    )

    # File count from DependenciesCollector or FileElementsCollector
    deps_data = extract_collector_data(data, "DependenciesCollector") or {}
    file_elements_data = extract_collector_data(data, "FileElementsCollector") or {}

    total_files = deps_data.get("file_count", file_elements_data.get("total_files", 0))

    # Technologies from dependencies
    technologies = []

    # Check Python packages from dependencies
    python_deps = deps_data.get("python_imports", [])
    external_deps = deps_data.get("external_dependencies", [])

    # Common tech mappings
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
        "anthropic": "Anthropic",
        "pydantic": "Pydantic",
        "sqlalchemy": "SQLAlchemy",
        "uvicorn": "Uvicorn",
        "gunicorn": "Gunicorn",
    }

    # Check imports and dependencies
    all_deps = python_deps + external_deps
    for dep in all_deps:
        dep_name = dep if isinstance(dep, str) else dep.get("name", "")
        dep_lower = dep_name.lower()
        for key, tech in tech_mapping.items():
            if key in dep_lower and tech not in technologies:
                technologies.append(tech)

    # Architecture analysis from AgentArchitectureCollector
    agent_arch_data = extract_collector_data(data, "AgentArchitectureCollector") or {}
    arch_type = "Unknown"

    if agent_arch_data.get("has_agents", False) or "agent" in purpose.lower():
        arch_type = "Multi-Agent System"
    elif any("api" in t.lower() for t in technologies) or "fastapi" in technologies:
        arch_type = "API Service"
    elif "streamlit" in technologies:
        arch_type = "Web Application"
    elif total_files > 50:
        arch_type = "Complex Application"
    elif total_files > 10:
        arch_type = "Application"
    else:
        arch_type = "Library/Tool"

    # Key components from most imported files
    components = []
    most_imported = deps_data.get("most_imported_files", [])
    for item in most_imported[:5]:
        if isinstance(item, dict) and "file_path" in item:
            # Extract meaningful component name from path
            path = item["file_path"]
            if "/" in path:
                component = (
                    path.split("/")[-2] if path.endswith(".py") else path.split("/")[-1]
                )
                if component not in components:
                    components.append(component)

    # Also check API endpoints if available
    api_data = extract_collector_data(data, "ApiEndpointsCollector") or {}
    if api_data.get("endpoints"):
        components.append("REST API")
        if arch_type == "Unknown":
            arch_type = "API Service"

    # Complexity score (simple heuristic)
    complexity = min(
        100, (total_files // 2) + len(technologies) * 8 + len(components) * 3
    )

    return ProjectInfo(
        name=project_path.name,
        purpose=purpose[:150] + "..." if len(purpose) > 150 else purpose,
        total_files=total_files,
        main_technologies=technologies[:6],  # Limit to 6 main techs
        architecture_type=arch_type,
        key_components=components[:5],  # Top 5 components
        complexity_score=complexity,
    )


def generate_comprehensive_overview() -> str:
    """Generate a comprehensive Mermaid diagram showing all projects"""

    return """graph TB
    classDef webapp fill:#e1f5fe,stroke:#01579b,stroke-width:2px,color:#000
    classDef api fill:#f3e5f5,stroke:#4a148c,stroke-width:2px,color:#000
    classDef agent fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000
    classDef library fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px,color:#000
    classDef complex fill:#fff8e1,stroke:#f57f17,stroke-width:2px,color:#000
    classDef unknown fill:#f5f5f5,stroke:#616161,stroke-width:2px,color:#000

    User[User/Developer]
    
    subgraph Custom_Projects["Custom Projects in intake/custom/"]
        
        subgraph AI_Agents["AI & Agent Systems"]
            agent_world["agent_world<br/>Multi-Agent Platform<br/>384 Python files"]:::agent
            asea["asea<br/>Autonomous Systems<br/>Enhanced Architecture"]:::agent
        end
        
        subgraph Knowledge_Systems["Knowledge & Graph Systems"]
            SKG_Cursor["SKG_Cursor<br/>Shared Knowledge Graph<br/>Cursor IDE Integration"]:::complex
            graphRAG["graphRAG<br/>Graph RAG Demo<br/>Knowledge Retrieval"]:::library
            graph_rag["graph_rag<br/>Simple Graph RAG<br/>Document Processing"]:::library
            graph_rag2["graph_rag2<br/>Advanced Graph RAG<br/>PDF Processing"]:::library
            graphiti["graphiti<br/>Graph Intelligence<br/>Memory Management"]:::complex
        end
        
        subgraph Development_Tools["Development & Automation Tools"]
            auto_forge["auto_forge<br/>Automated Development<br/>Code Generation"]:::complex
            docRuleGen["docRuleGen<br/>Documentation Rules<br/>Content Generation"]:::library
            master["master<br/>Master Control<br/>System Integration"]:::complex
        end
        
        subgraph Utilities["Utilities & Visualization"]
            ide_context["ide_contex_visualization<br/>IDE Context Visualization<br/>Development Support"]:::webapp
        end
    end
    
    User --> Custom_Projects
    agent_world --> SKG_Cursor
    asea --> graphiti
    auto_forge --> docRuleGen
    graphRAG --> graph_rag
    graph_rag --> graph_rag2"""


def main():
    custom_dir = Path("/home/opsvi/master_root/intake/custom")

    print("🔍 Reading project intelligence data with fixed parser...")

    projects = []
    for project_dir in custom_dir.iterdir():
        if (
            project_dir.is_dir()
            and project_dir.name != ".proj-intel"
            and project_dir.name != "visualizations"
        ):
            data = read_project_intelligence(project_dir)
            if data:
                project_info = analyze_project(project_dir, data)
                projects.append(project_info)
                print(
                    f"✅ {project_info.name}: {project_info.total_files} files, {project_info.architecture_type}"
                )
                if project_info.main_technologies:
                    print(
                        f"   Technologies: {', '.join(project_info.main_technologies)}"
                    )

    if not projects:
        print("❌ No project data found!")
        return

    print(f"\n📊 Generating comprehensive analysis for {len(projects)} projects...")

    # Sort projects by complexity
    projects.sort(key=lambda p: p.complexity_score, reverse=True)

    # Generate detailed analysis
    analysis = "# Custom Projects Comprehensive Analysis\n\n"

    for project in projects:
        analysis += f"## {project.name}\n\n"
        analysis += f"**Architecture:** {project.architecture_type}  \n"
        analysis += f"**Files:** {project.total_files}  \n"
        analysis += f"**Complexity Score:** {project.complexity_score}/100  \n"

        if project.main_technologies:
            analysis += f"**Technologies:** {', '.join(project.main_technologies)}  \n"

        if project.key_components:
            analysis += f"**Key Components:** {', '.join(project.key_components)}  \n"

        analysis += f"**Purpose:** {project.purpose}\n\n"
        analysis += "---\n\n"

    # Generate overview diagram
    overview_diagram = generate_comprehensive_overview()

    # Create outputs
    output_dir = custom_dir / "visualizations"
    output_dir.mkdir(exist_ok=True)

    # Save comprehensive analysis
    with open(output_dir / "comprehensive_analysis.md", "w") as f:
        f.write(analysis)

    # Save overview diagram
    with open(output_dir / "projects_overview.md", "w") as f:
        f.write(
            f"# Custom Projects Architecture Overview\n\n```mermaid\n{overview_diagram}\n```\n"
        )

    # Generate individual project diagrams for complex ones
    for project in projects:
        if project.complexity_score > 20 or project.total_files > 15:
            diagram = f"""graph LR
    classDef main fill:#fff,stroke:#000,stroke-width:2px,color:#000
    classDef tech fill:#e3f2fd,stroke:#1976d2,stroke-width:1px,color:#000
    classDef comp fill:#f3e5f5,stroke:#7b1fa2,stroke-width:1px,color:#000
    
    Main["{project.name}<br/>{project.total_files} files<br/>{project.architecture_type}"]:::main
"""

            # Add technology connections
            if project.main_technologies:
                for i, tech in enumerate(project.main_technologies):
                    tech_id = f"T{i}_{tech.replace(' ', '_').replace('-', '_')}"
                    diagram += f'    {tech_id}["{tech}"]:::tech\n'
                    diagram += f"    Main --> {tech_id}\n"

            # Add component connections
            if project.key_components:
                for i, comp in enumerate(project.key_components):
                    comp_id = f"C{i}_{comp.replace(' ', '_').replace('-', '_').replace('/', '_')}"
                    diagram += f'    {comp_id}["{comp}"]:::comp\n'
                    diagram += f"    Main --> {comp_id}\n"

            with open(output_dir / f"{project.name}_architecture.md", "w") as f:
                f.write(f"# {project.name} Architecture\n\n")
                f.write(f"**Type:** {project.architecture_type}  \n")
                f.write(f"**Files:** {project.total_files}  \n")
                f.write(f"**Complexity:** {project.complexity_score}/100  \n\n")
                f.write(f"**Purpose:** {project.purpose}\n\n")
                f.write(f"```mermaid\n{diagram}\n```\n")

    # Save machine-readable data
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

    print(f"\n✅ Analysis complete! Files saved to: {output_dir}/")
    print(
        f"📊 {len([p for p in projects if p.complexity_score > 20])} complex projects analyzed"
    )
    print(f"🏗️  Architecture types found: {set(p.architecture_type for p in projects)}")
    print(
        f"🔧 Technologies detected: {set(tech for p in projects for tech in p.main_technologies)}"
    )


if __name__ == "__main__":
    main()
