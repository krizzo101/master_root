"""CLI commands for the output generation subsystem.

This module provides the CLI commands for generating, managing, and accessing
project maps.
"""

import os
import json
import logging
import click
from typing import Any, Dict, Optional

from proj_mapper.output.generator import GeneratorConfig, MapFormatType
from proj_mapper.output.storage import StorageManager
from proj_mapper.relationship.graph import RelationshipGraph
from proj_mapper.pipeline.pipeline import Pipeline
from proj_mapper.relationship.pipeline_stages import (
    RelationshipDetectionStage, 
    RelationshipScoringStage,
    CrossReferenceResolutionStage,
    RelationshipGraphBuildingStage,
    RelationshipServiceStage
)
from proj_mapper.output.pipeline_stages import MapGeneratorStage, MapStorageStage

# Configure logging
logger = logging.getLogger(__name__)


@click.group(name="output")
def output_group():
    """Commands for generating and managing project maps."""
    pass


@output_group.command(name="generate")
@click.option("--analysis-file", "-a", required=True, help="Path to the analysis results JSON file")
@click.option("--output-file", "-o", help="Path to save the generated map")
@click.option("--format", "-f", type=click.Choice(["json", "markdown", "yaml", "dot"]), default="json", help="Output format")
@click.option("--min-confidence", "-c", type=float, default=0.5, help="Minimum confidence threshold")
@click.option("--template", "-t", default="project_overview", help="Template to use for map generation")
@click.option("--include-code/--exclude-code", default=True, help="Include code elements in the map")
@click.option("--include-docs/--exclude-docs", default=True, help="Include documentation elements in the map")
@click.option("--include-metadata/--exclude-metadata", default=True, help="Include metadata in the map")
@click.option("--enable-chunking/--disable-chunking", default=False, help="Enable chunking for large maps")
@click.option("--max-tokens", type=int, default=0, help="Maximum token estimate (0 for no limit)")
@click.option("--ai-optimize/--no-ai-optimize", default=False, help="Apply AI optimization")
@click.option("--debug", is_flag=True, help="Enable debug logging")
def generate_map(
    analysis_file: str,
    output_file: Optional[str] = None,
    format: str = "json",
    min_confidence: float = 0.5,
    template: str = "project_overview",
    include_code: bool = True,
    include_docs: bool = True,
    include_metadata: bool = True,
    enable_chunking: bool = False,
    max_tokens: int = 0,
    ai_optimize: bool = False,
    debug: bool = False
):
    """Generate a project map from analysis results."""
    # Configure logging
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")
    
    # Create the generator configuration
    config = GeneratorConfig(
        output_format=MapFormatType(format),
        min_confidence=min_confidence,
        include_code=include_code,
        include_documentation=include_docs,
        include_metadata=include_metadata,
        chunking_enabled=enable_chunking,
        max_token_estimate=max_tokens,
        template_name=template,
        ai_optimization_enabled=ai_optimize
    )
    
    # Create a storage directory if output file is not specified
    if not output_file:
        # Create a default storage path
        project_name = os.path.basename(os.path.dirname(os.path.abspath(analysis_file)))
        output_dir = ".maps"
        os.makedirs(output_dir, exist_ok=True)
    
    # Check if analysis file exists
    if not os.path.exists(analysis_file):
        click.echo(f"Error: Analysis file '{analysis_file}' not found.", err=True)
        return
    
    # Load the analysis results
    try:
        with open(analysis_file, "r", encoding="utf-8") as f:
            analysis_data = json.load(f)
        
        click.echo(f"Loaded analysis data from {analysis_file}")
    except Exception as e:
        click.echo(f"Error loading analysis file: {e}", err=True)
        return
    
    # Create the pipeline for map generation
    try:
        pipeline = Pipeline()
        
        # Add relationship stages
        pipeline.add_stage(RelationshipDetectionStage())
        pipeline.add_stage(RelationshipScoringStage())
        pipeline.add_stage(CrossReferenceResolutionStage())
        pipeline.add_stage(RelationshipGraphBuildingStage())
        pipeline.add_stage(RelationshipServiceStage())
        
        # Add output stages
        pipeline.add_stage(MapGeneratorStage(config))
        
        if not output_file:
            pipeline.add_stage(MapStorageStage(output_dir, config))
        
        # Initialize the context with the analysis data
        context = pipeline.create_context()
        context.data["analysis_results"] = analysis_data
        
        # Extract project name for storage
        if "project_info" in analysis_data:
            context.data["project_name"] = analysis_data["project_info"].get("name", project_name)
        else:
            context.data["project_name"] = project_name
        
        # Execute the pipeline
        result_context = pipeline.execute(context)
        
        # Check if map was generated
        if "map" not in result_context.data and "map_chunks" not in result_context.data:
            click.echo("Error: Failed to generate map.", err=True)
            return
        
        # If output file is specified, write the map to it
        if output_file:
            is_chunked = result_context.data.get("map_is_chunked", False)
            
            if is_chunked:
                # Create directory for chunked map
                chunks_dir = os.path.splitext(output_file)[0] + "_chunks"
                os.makedirs(chunks_dir, exist_ok=True)
                
                # Write each chunk to a file
                chunks = result_context.data["map_chunks"]
                for chunk_id, chunk_data in chunks.items():
                    chunk_file = os.path.join(chunks_dir, f"{chunk_id}.{format}")
                    with open(chunk_file, "w", encoding="utf-8") as f:
                        json.dump(chunk_data, f, indent=2)
                
                click.echo(f"Map chunks written to {chunks_dir}")
            else:
                # Write the map to the output file
                with open(output_file, "w", encoding="utf-8") as f:
                    map_data = result_context.data["map"]
                    if isinstance(map_data, str):
                        f.write(map_data)
                    else:
                        json.dump(map_data, f, indent=2)
                
                click.echo(f"Map written to {output_file}")
        else:
            # Map was stored by the storage stage
            path = result_context.data.get("map_storage_path", "unknown")
            click.echo(f"Map stored at {path}")
    
    except Exception as e:
        click.echo(f"Error generating map: {e}", err=True)
        if debug:
            import traceback
            traceback.print_exc()


@output_group.command(name="list")
@click.option("--project", "-p", help="Project name (defaults to all projects)")
@click.option("--maps-dir", "-d", default=".maps", help="Maps directory")
def list_maps(project: Optional[str] = None, maps_dir: str = ".maps"):
    """List available maps."""
    # Check if maps directory exists
    if not os.path.exists(maps_dir):
        click.echo(f"Maps directory '{maps_dir}' not found.", err=True)
        return
    
    storage = StorageManager(maps_dir)
    
    if project:
        # List maps for a specific project
        history = storage.get_map_history(project)
        
        if not history:
            click.echo(f"No maps found for project '{project}'.")
            return
        
        click.echo(f"Maps for project '{project}':")
        for i, map_info in enumerate(history, 1):
            timestamp = map_info.get("timestamp", "unknown")
            format_type = map_info.get("format", "unknown")
            click.echo(f"{i}. {timestamp} - Format: {format_type}")
    else:
        # List all projects
        projects = []
        for item in os.listdir(maps_dir):
            item_path = os.path.join(maps_dir, item)
            if os.path.isdir(item_path):
                projects.append(item)
        
        if not projects:
            click.echo("No projects found.")
            return
        
        click.echo("Available projects:")
        for i, project_name in enumerate(sorted(projects), 1):
            # Get the latest map for each project
            latest = storage.get_latest_map(project_name)
            status = "Available" if latest else "No maps"
            click.echo(f"{i}. {project_name} - {status}")


@output_group.command(name="clean")
@click.option("--project", "-p", required=True, help="Project name")
@click.option("--keep", "-k", default=5, help="Number of maps to keep")
@click.option("--maps-dir", "-d", default=".maps", help="Maps directory")
@click.option("--force", "-f", is_flag=True, help="Force cleanup without confirmation")
def clean_maps(project: str, keep: int = 5, maps_dir: str = ".maps", force: bool = False):
    """Clean old maps for a project."""
    # Check if maps directory exists
    if not os.path.exists(maps_dir):
        click.echo(f"Maps directory '{maps_dir}' not found.", err=True)
        return
    
    storage = StorageManager(maps_dir)
    
    # Get the map history
    history = storage.get_map_history(project)
    
    if not history:
        click.echo(f"No maps found for project '{project}'.")
        return
    
    # Calculate how many maps will be deleted
    to_delete = len(history) - keep
    
    if to_delete <= 0:
        click.echo(f"No maps to clean (found {len(history)}, keeping {keep}).")
        return
    
    # Confirm the operation
    if not force:
        click.confirm(f"This will delete {to_delete} maps for project '{project}', leaving {keep}. Continue?", abort=True)
    
    # Clean the maps
    deleted = storage.clean_old_maps(project, keep)
    
    click.echo(f"Cleaned {deleted} maps for project '{project}'.")


@output_group.command(name="delete")
@click.option("--project", "-p", required=True, help="Project name")
@click.option("--maps-dir", "-d", default=".maps", help="Maps directory")
@click.option("--force", "-f", is_flag=True, help="Force deletion without confirmation")
def delete_project(project: str, maps_dir: str = ".maps", force: bool = False):
    """Delete all maps for a project."""
    # Check if maps directory exists
    if not os.path.exists(maps_dir):
        click.echo(f"Maps directory '{maps_dir}' not found.", err=True)
        return
    
    project_dir = os.path.join(maps_dir, project)
    
    if not os.path.exists(project_dir):
        click.echo(f"Project '{project}' not found.", err=True)
        return
    
    # Confirm the operation
    if not force:
        click.confirm(f"This will delete ALL maps for project '{project}'. This cannot be undone. Continue?", abort=True)
    
    # Delete the project directory
    import shutil
    shutil.rmtree(project_dir)
    
    click.echo(f"Deleted all maps for project '{project}'.") 