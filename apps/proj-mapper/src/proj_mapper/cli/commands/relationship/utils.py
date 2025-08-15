"""Utility functions for relationship CLI commands.

This module provides utility functions used by relationship CLI commands.
"""

from typing import Dict, Any, List


def relationship_to_dict(relationship) -> Dict[str, Any]:
    """Convert a Relationship object to a dictionary."""
    return {
        "source_id": relationship.source_id,
        "target_id": relationship.target_id,
        "relationship_type": relationship.relationship_type.name,
        "confidence": relationship.confidence,
        "metadata": relationship.metadata
    }


def node_to_dict(node) -> Dict[str, Any]:
    """Convert a Node object to a dictionary."""
    return {
        "id": node.id,
        "node_type": node.node_type,
        "data": node.data
    }


def edge_to_dict(edge) -> Dict[str, Any]:
    """Convert an Edge object to a dictionary."""
    return {
        "source_id": edge.source.id,
        "target_id": edge.target.id,
        "relationship_type": edge.relationship_type,
        "confidence": edge.confidence,
        "metadata": edge.metadata
    }


def rebuild_graph_from_data(data: Dict[str, Any]):
    """Rebuild a RelationshipGraph from exported data."""
    from proj_mapper.relationship.graph import RelationshipGraph
    
    graph = RelationshipGraph()
    
    # Add nodes first
    if "graph" in data and "nodes" in data["graph"]:
        for node_data in data["graph"]["nodes"]:
            graph.add_node(
                node_id=node_data["id"],
                node_type=node_data["node_type"],
                data=node_data["data"]
            )
    
    # Then add edges
    if "graph" in data and "edges" in data["graph"]:
        for edge_data in data["graph"]["edges"]:
            try:
                graph.add_edge(
                    source_id=edge_data["source_id"],
                    target_id=edge_data["target_id"],
                    relationship_type=edge_data["relationship_type"],
                    confidence=edge_data["confidence"],
                    metadata=edge_data.get("metadata", {})
                )
            except ValueError:
                # Skip if nodes don't exist
                pass
    
    # If there's no graph data, rebuild from relationships
    elif "relationships" in data:
        # First add all unique elements as nodes
        source_ids = set(r["source_id"] for r in data["relationships"])
        target_ids = set(r["target_id"] for r in data["relationships"])
        all_ids = source_ids.union(target_ids)
        
        for element_id in all_ids:
            # Determine node type (best guess)
            # Typically code elements are sources, doc elements are targets
            node_type = "code" if element_id in source_ids else "documentation"
            graph.add_node(element_id, node_type, {"id": element_id})
        
        # Then add relationships as edges
        for rel in data["relationships"]:
            try:
                graph.add_edge(
                    source_id=rel["source_id"],
                    target_id=rel["target_id"],
                    relationship_type=rel["relationship_type"],
                    confidence=rel["confidence"],
                    metadata=rel.get("metadata", {})
                )
            except ValueError:
                # Skip if nodes don't exist
                pass
    
    return graph


def graph_to_dot(graph, min_confidence: float = 0.0) -> str:
    """Convert a RelationshipGraph to GraphViz DOT format."""
    dot_lines = ["digraph RelationshipGraph {"]
    dot_lines.append("  // Graph styling")
    dot_lines.append("  graph [rankdir=LR, fontname=Arial, splines=true];")
    dot_lines.append("  node [shape=box, style=filled, fontname=Arial, margin=0.2];")
    dot_lines.append("  edge [fontname=Arial];")
    dot_lines.append("")
    
    # Add nodes
    dot_lines.append("  // Nodes")
    for node_id, node in graph.nodes.items():
        # Different colors for code and doc nodes
        if node.node_type == "code":
            color = "lightblue"
            label = f"{node_id}\\n({node.data.get('name', '')})"
        else:
            color = "lightgreen"
            label = f"{node_id}\\n({node.data.get('title', '')})"
        
        # Escape special characters in label
        label = label.replace('"', '\\"')
        
        dot_lines.append(f'  "{node_id}" [label="{label}", fillcolor="{color}"];')
    
    dot_lines.append("")
    
    # Add edges
    dot_lines.append("  // Edges")
    for edge in graph.edges:
        if edge.confidence < min_confidence:
            continue
        
        # Edge styling based on confidence
        if edge.confidence >= 0.8:
            style = "solid"
            penwidth = 2.0
        elif edge.confidence >= 0.5:
            style = "solid"
            penwidth = 1.0
        else:
            style = "dashed"
            penwidth = 1.0
        
        # Edge color based on relationship type
        color_map = {
            "IMPLEMENTS": "blue",
            "REFERENCES": "green",
            "DOCUMENTS": "darkgreen",
            "IMPORTS": "red",
            "INHERITS_FROM": "purple",
            "RELATES_TO": "gray"
        }
        color = color_map.get(edge.relationship_type, "black")
        
        # Label with type and confidence
        label = f"{edge.relationship_type}\\n({edge.confidence:.2f})"
        
        dot_lines.append(
            f'  "{edge.source.id}" -> "{edge.target.id}" '
            f'[label="{label}", color="{color}", style="{style}", penwidth={penwidth}];'
        )
    
    dot_lines.append("}")
    
    return "\n".join(dot_lines) 