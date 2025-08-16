"""CLI commands for relationship output and visualization.

This module provides CLI commands for exporting and visualizing relationships.
"""

import json
import click
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from proj_mapper.cli.commands.relationship.utils import rebuild_graph_from_data, graph_to_dot

logger = logging.getLogger(__name__)

@click.command()
@click.option(
    "--relationships-file",
    "-r",
    required=True,
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    help="Path to JSON file containing relationships data."
)
@click.option(
    "--output-file",
    "-o",
    required=True,
    type=click.Path(file_okay=True, dir_okay=False),
    help="Path to output file."
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["graphviz", "json"]),
    default="graphviz",
    help="Format of the output graph."
)
@click.option(
    "--min-confidence",
    "-c",
    type=float,
    default=0.0,
    help="Minimum confidence threshold for relationships (0.0-1.0)."
)
def export_graph(
    relationships_file: str,
    output_file: str, 
    format: str,
    min_confidence: float
):
    """Export relationship data to a graph visualization format.
    
    This command takes relationship data and exports it in various formats
    for visualization or further processing.
    """
    try:
        # Load relationships data
        with open(relationships_file, "r") as f:
            data = json.load(f)
        
        # Rebuild graph from data
        logger.info(f"Rebuilding relationship graph from {relationships_file}")
        graph = rebuild_graph_from_data(data)
        
        # Export graph in the requested format
        if format == "graphviz":
            # Export as GraphViz DOT format
            dot_content = graph_to_dot(graph, min_confidence=min_confidence)
            
            with open(output_file, "w") as f:
                f.write(dot_content)
            
            logger.info(f"Exported graph in DOT format to {output_file}")
            click.echo(f"Graph exported to {output_file} in DOT format")
            click.echo("You can visualize this file with Graphviz tools like:")
            click.echo(f"  dot -Tpng {output_file} -o {output_file}.png")
            click.echo(f"  dot -Tsvg {output_file} -o {output_file}.svg")
            
        elif format == "json":
            # Export as JSON format
            # Filter edges by confidence
            filtered_edges = [
                {
                    "source": edge.source.id,
                    "target": edge.target.id,
                    "type": edge.relationship_type,
                    "confidence": edge.confidence
                }
                for edge in graph.edges
                if edge.confidence >= min_confidence
            ]
            
            # Create a JSON representation of the graph
            json_graph = {
                "nodes": [
                    {
                        "id": node_id,
                        "type": node.node_type,
                        "data": node.data
                    }
                    for node_id, node in graph.nodes.items()
                ],
                "edges": filtered_edges
            }
            
            with open(output_file, "w") as f:
                json.dump(json_graph, f, indent=2)
            
            logger.info(f"Exported graph in JSON format to {output_file}")
            click.echo(f"Graph exported to {output_file} in JSON format")
            
    except Exception as e:
        logger.error(f"Error exporting graph: {str(e)}")
        raise click.ClickException(f"Error exporting graph: {str(e)}") 