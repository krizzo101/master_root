"""CLI commands for relationship analysis.

This module provides CLI commands for analyzing relationships between code and documentation.
"""

import os
import click
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

from proj_mapper.relationship.query import RelationshipQuery
from proj_mapper.cli.formatting import format_relationship

logger = logging.getLogger(__name__)

@click.command()
@click.option('--input-file', '-i', required=True, type=click.Path(exists=True, file_okay=True, dir_okay=False),
              help='Input JSON file containing relationships')
@click.option('--output-file', '-o', type=click.Path(),
              help='Output file path for filtered results (optional)')
@click.option('--source-type', type=str, multiple=True,
              help='Filter by source type')
@click.option('--target-type', type=str, multiple=True,
              help='Filter by target type')
@click.option('--relationship-type', type=str, multiple=True,
              help='Filter by relationship type')
@click.option('--min-confidence', type=float, default=0.0,
              help='Minimum confidence threshold')
@click.option('--source-id', type=str, multiple=True,
              help='Filter by source ID')
@click.option('--target-id', type=str, multiple=True,
              help='Filter by target ID')
@click.option('--format', type=click.Choice(['json', 'table', 'text']), default='text',
              help='Output format')
def query_relationships(
    input_file, output_file, source_type, target_type,
    relationship_type, min_confidence, source_id, target_id, format
):
    """Query and filter relationships from a relationship file."""
    try:
        # Load relationships
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        relationships = data.get("relationships", [])
        graph_data = data.get("graph", None)
        
        # Create query
        query = RelationshipQuery()
        
        # Apply filters
        if source_type:
            query.filter_source_type(list(source_type))
        if target_type:
            query.filter_target_type(list(target_type))
        if relationship_type:
            query.filter_relationship_type(list(relationship_type))
        if min_confidence > 0:
            query.filter_min_confidence(min_confidence)
        if source_id:
            query.filter_source_id(list(source_id))
        if target_id:
            query.filter_target_id(list(target_id))
        
        # Execute query
        filtered = query.execute(relationships)
        
        # Output results
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w') as f:
                json.dump({"relationships": filtered}, f, indent=2)
            
            logger.info(f"Results saved to: {output_file}")
        
        # Format output
        output = format_relationship(filtered, format_type=format)
        
        # Log output instead of printing to console
        if format == 'json':
            logger.info(output)
        else:
            logger.info(output)
        
        logger.info(f"Found {len(filtered)} matching relationships")
        
    except Exception as e:
        logger.error(f"Error querying relationships: {str(e)}")
        raise click.ClickException(str(e)) 