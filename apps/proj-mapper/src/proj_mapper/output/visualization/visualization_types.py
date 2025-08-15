"""Specialized visualization type implementations.

This module provides specialized functions for generating different types of visualizations.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional
import os
import re

from proj_mapper.output.visualization.base import VisualizationConfig, VisualizationFormat
from proj_mapper.output.visualization.graph import DotRenderer, HtmlRenderer

# Configure logging
logger = logging.getLogger(__name__)


def _derive_module_name(relative_path: str) -> str:
    """Convert a relative file path like 'pkg/mod/file.py' to a module path 'pkg.mod.file'."""
    rel = relative_path
    if rel.endswith(".py"):
        rel = rel[:-3]
    rel = rel.lstrip("./")
    return rel.replace(os.sep, ".")


def _extract_imports(py_path: str) -> list[str]:
    """Naively extract imported module roots from a Python file.

    This is a lightweight heuristic (regex-based) for visualization purposes only.
    """
    imports: list[str] = []
    try:
        with open(py_path, encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line.startswith("import "):
                    # import a, b.c as c
                    rest = line[len("import "):]
                    parts = [p.strip() for p in rest.split(",")]
                    for p in parts:
                        root = p.split(" as ")[0].strip()
                        if root:
                            imports.append(root)
                elif line.startswith("from ") and " import " in line:
                    # from x.y import z
                    root = line[len("from "):].split(" import ")[0].strip()
                    if root:
                        imports.append(root)
    except Exception as e:  # noqa: BLE001
        logger.debug(f"Import extraction failed for {py_path}: {e}")
    return imports


def _build_basic_import_graph(map_data: Dict[str, Any]) -> Dict[str, Any]:
    """Build a basic graph of Python files and import relationships from map_data."""
    files = map_data.get("files") or []
    # Map module name to node id (use relative_path for id/label)
    module_to_node: dict[str, str] = {}
    nodes: list[dict[str, Any]] = []

    for f in files:
        if f.get("file_type") != "python":
            continue
        rel = f.get("relative_path") or f.get("path")
        if not rel:
            continue
        mod = _derive_module_name(rel)
        module_to_node[mod] = rel
        nodes.append({"id": rel, "label": rel, "type": "code"})

    edges: list[dict[str, Any]] = []
    for f in files:
        if f.get("file_type") != "python":
            continue
        rel = f.get("relative_path") or f.get("path")
        path = f.get("path")
        if not rel or not path:
            continue
        src_id = rel
        # Extract imports
        imported = _extract_imports(path)
        for imp in imported:
            # Try to resolve imported module to a known node by prefix matching
            # e.g., import proj_mapper.cli.main -> match module_to_node keys
            targets = [module_to_node[k] for k in module_to_node.keys() if k == imp or k.startswith(imp + ".")]
            for tgt in targets:
                if tgt != src_id:
                    edges.append({"source": src_id, "target": tgt, "label": "imports", "weight": 1.0})

    return {"nodes": nodes, "edges": edges}


def generate_relationship_visualization(
    map_data: Dict[str, Any],
    output_path: Path,
    project_name: str,
    config: VisualizationConfig
) -> Optional[Path]:
    """Generate a relationship graph visualization.

    Args:
        map_data: The map data to visualize
        output_path: The path to save the visualization
        project_name: Name of the project
        config: Visualization configuration

    Returns:
        Path to the generated visualization
    """
    # Get the relationship graph data
    graph_data = map_data.get("relationship_graph")
    if not graph_data:
        # Fallback: build a basic import graph between python files
        graph_data = _build_basic_import_graph(map_data)

    try:
        if config.output_format == VisualizationFormat.DOT:
            renderer = DotRenderer(config)
            renderer.render(graph_data, output_path)
            return output_path
        elif config.output_format == VisualizationFormat.HTML:
            renderer = HtmlRenderer(config)
            renderer.render(graph_data, output_path)
            return output_path
        else:
            logger.error(f"Unsupported output format: {config.output_format}")
            return None
    except Exception as e:
        logger.error(f"Error rendering relationship visualization: {e}")
        return None


def generate_dependency_visualization(
    map_data: Dict[str, Any],
    output_path: Path,
    project_name: str,
    config: VisualizationConfig
) -> Optional[Path]:
    """Generate a dependency graph visualization.

    Args:
        map_data: The map data to visualize
        output_path: The path to save the visualization
        project_name: Name of the project
        config: Visualization configuration

    Returns:
        Path to the generated visualization
    """
    # Extract dependency information from relationships
    dependencies = {
        "nodes": [],
        "edges": []
    }

    # Add modules as nodes
    if "project_map" in map_data:
        project = map_data["project_map"].get("project", {})
        for module in project.get("code_elements", []):
            if module.get("element_type") == "module":
                dependencies["nodes"].append({
                    "id": module["id"],
                    "label": module.get("name", module["id"]),
                    "type": "code"
                })

    # Add dependency relationships as edges
    if "relationship_graph" in map_data:
        graph = map_data["relationship_graph"]
        for edge in graph.get("edges", []):
            if edge.get("label") in ("imports", "depends_on"):
                dependencies["edges"].append(edge)

    try:
        if config.output_format == VisualizationFormat.DOT:
            renderer = DotRenderer(config)
            renderer.render(dependencies, output_path)
            return output_path
        elif config.output_format == VisualizationFormat.HTML:
            renderer = HtmlRenderer(config)
            renderer.render(dependencies, output_path)
            return output_path
        else:
            logger.error(f"Unsupported output format: {config.output_format}")
            return None
    except Exception as e:
        logger.error(f"Error rendering dependency visualization: {e}")
        return None


def generate_hierarchy_visualization(
    map_data: Dict[str, Any],
    output_path: Path,
    project_name: str,
    config: VisualizationConfig
) -> Optional[Path]:
    """Generate a hierarchy visualization.

    Args:
        map_data: The map data to visualize
        output_path: The path to save the visualization
        project_name: Name of the project
        config: Visualization configuration

    Returns:
        Path to the generated visualization
    """
    # Extract hierarchy information
    hierarchy = {
        "nodes": [],
        "edges": []
    }

    if "project_map" in map_data:
        project = map_data["project_map"].get("project", {})

        # Add project root node
        hierarchy["nodes"].append({
            "id": "root",
            "label": project.get("name", project_name),
            "type": "project"
        })

        # Add package/module nodes and edges
        for element in project.get("code_elements", []):
            if element.get("element_type") in ["package", "module"]:
                hierarchy["nodes"].append({
                    "id": element["id"],
                    "label": element.get("name", element["id"]),
                    "type": "code"
                })

                # Add edge from parent package or root
                parent_id = element.get("parent_id", "root")
                hierarchy["edges"].append({
                    "source": parent_id,
                    "target": element["id"],
                    "label": "contains"
                })

    try:
        if config.output_format == VisualizationFormat.DOT:
            renderer = DotRenderer(config)
            renderer.render(hierarchy, output_path)
            return output_path
        elif config.output_format == VisualizationFormat.HTML:
            renderer = HtmlRenderer(config)
            renderer.render(hierarchy, output_path)
            return output_path
        else:
            logger.error(f"Unsupported output format: {config.output_format}")
            return None
    except Exception as e:
        logger.error(f"Error rendering hierarchy visualization: {e}")
        return None


def generate_module_visualization(
    map_data: Dict[str, Any],
    output_path: Path,
    project_name: str,
    config: VisualizationConfig
) -> Optional[Path]:
    """Generate a module structure visualization.

    Args:
        map_data: The map data to visualize
        output_path: The path to save the visualization
        project_name: Name of the project
        config: Visualization configuration

    Returns:
        Path to the generated visualization
    """
    # Extract module structure information
    structure = {
        "nodes": [],
        "edges": []
    }

    if "project_map" in map_data:
        project = map_data["project_map"].get("project", {})

        # Process each module
        for element in project.get("code_elements", []):
            if element.get("element_type") == "module":
                # Add module node
                module_id = element["id"]
                structure["nodes"].append({
                    "id": module_id,
                    "label": element.get("name", module_id),
                    "type": "module"
                })

                # Add class nodes
                for class_elem in element.get("classes", []):
                    class_id = class_elem["id"]
                    structure["nodes"].append({
                        "id": class_id,
                        "label": class_elem.get("name", class_id),
                        "type": "class"
                    })
                    structure["edges"].append({
                        "source": module_id,
                        "target": class_id,
                        "label": "contains"
                    })

                # Add function nodes
                for func_elem in element.get("functions", []):
                    func_id = func_elem["id"]
                    structure["nodes"].append({
                        "id": func_id,
                        "label": func_elem.get("name", func_id),
                        "type": "function"
                    })
                    structure["edges"].append({
                        "source": module_id,
                        "target": func_id,
                        "label": "contains"
                    })

    try:
        if config.output_format == VisualizationFormat.DOT:
            renderer = DotRenderer(config)
            renderer.render(structure, output_path)
            return output_path
        elif config.output_format == VisualizationFormat.HTML:
            renderer = HtmlRenderer(config)
            renderer.render(structure, output_path)
            return output_path
        else:
            logger.error(f"Unsupported output format: {config.output_format}")
            return None
    except Exception as e:
        logger.error(f"Error rendering module visualization: {e}")
        return None


def generate_documentation_visualization(
    map_data: Dict[str, Any],
    output_path: Path,
    project_name: str,
    config: VisualizationConfig
) -> Optional[Path]:
    """Generate a documentation structure visualization.

    Args:
        map_data: The map data to visualize
        output_path: The path to save the visualization
        project_name: Name of the project
        config: Visualization configuration

    Returns:
        Path to the generated visualization
    """
    # Extract documentation structure
    structure = {
        "nodes": [],
        "edges": []
    }

    if "documentation_structure" in map_data:
        doc_structure = map_data["documentation_structure"]

        # Process each document
        for doc in doc_structure.get("documents", []):
            # Add document node
            doc_id = doc["path"]
            structure["nodes"].append({
                "id": doc_id,
                "label": doc.get("title", doc_id),
                "type": "document"
            })

            # Add section nodes
            for section in doc.get("sections", []):
                section_id = section["id"]
                structure["nodes"].append({
                    "id": section_id,
                    "label": section.get("title", section_id),
                    "type": "section"
                })
                structure["edges"].append({
                    "source": doc_id,
                    "target": section_id,
                    "label": "contains"
                })

            # Add references
            for ref in doc.get("references", []):
                if ref.get("type") == "code":
                    target_id = ref["target"]
                    structure["edges"].append({
                        "source": doc_id,
                        "target": target_id,
                        "label": "references",
                        "weight": ref.get("confidence", 1.0)
                    })

    try:
        if config.output_format == VisualizationFormat.DOT:
            renderer = DotRenderer(config)
            renderer.render(structure, output_path)
            return output_path
        elif config.output_format == VisualizationFormat.HTML:
            renderer = HtmlRenderer(config)
            renderer.render(structure, output_path)
            return output_path
        else:
            logger.error(f"Unsupported output format: {config.output_format}")
            return None
    except Exception as e:
        logger.error(f"Error rendering documentation visualization: {e}")
        return None
