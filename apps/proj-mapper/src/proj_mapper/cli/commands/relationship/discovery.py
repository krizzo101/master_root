"""CLI commands for relationship discovery.

This module provides CLI commands for detecting relationships between code and documentation.
"""

import os
import click
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from proj_mapper.analyzers.factory import AnalyzerFactory
from proj_mapper.relationship.mapper import RelationshipMapper
from proj_mapper.relationship.graph.graph import RelationshipGraph
from proj_mapper.analyzers.pipeline import AnalysisPipeline
from proj_mapper.models.analysis import AnalysisResult, CodeAnalysisResult, DocumentationAnalysisResult
from proj_mapper.models.code import CodeElement
from proj_mapper.models.documentation import DocumentationElement
from proj_mapper.core.project_manager import ProjectManager
from proj_mapper.core.file_discovery import FileDiscovery
from proj_mapper.models.relationship import RelationshipType

# Configure logger to write to file only, not console
logger = logging.getLogger(__name__)
# Remove any existing handlers
for handler in logger.handlers[:]:
    logger.removeHandler(handler)
# Create a file handler
log_file_path = Path('relationship_discovery.log')
file_handler = logging.FileHandler(log_file_path)
file_handler.setLevel(logging.INFO)
# Create formatter and add to handler
formatter = logging.Formatter('[%(asctime)s] %(levelname)-8s %(message)s', datefmt='%m/%d/%y %H:%M:%S')
file_handler.setFormatter(formatter)
# Add handler to logger
logger.addHandler(file_handler)

@click.command()
@click.option('--code-dir', '-c', required=True, type=click.Path(exists=True, file_okay=False, dir_okay=True),
              help='Directory containing code files to analyze')
@click.option('--docs-dir', '-d', required=True, type=click.Path(exists=True, file_okay=False, dir_okay=True),
              help='Directory containing documentation files to analyze')
@click.option('--output-file', '-o', required=True, type=click.Path(),
              help='Output file path for relationships JSON')
@click.option('--code-analyzers', multiple=True, default=['python'],
              help='Code analyzers to use (multiple allowed)')
@click.option('--doc-analyzers', multiple=True, default=['markdown'],
              help='Documentation analyzers to use (multiple allowed)')
@click.option('--include-code', multiple=True, default=[],
              help='Glob patterns for code files to include')
@click.option('--exclude-code', multiple=True, default=[],
              help='Glob patterns for code files to exclude')
@click.option('--include-docs', multiple=True, default=[],
              help='Glob patterns for documentation files to include')
@click.option('--exclude-docs', multiple=True, default=[],
              help='Glob patterns for documentation files to exclude')
@click.option('--min-confidence', '-m', type=float, default=0.5,
              help='Minimum confidence threshold for relationships')
@click.option('--export-graph/--no-export-graph', default=False,
              help='Export relationship graph alongside relationships')
def detect_relationships(
    code_dir, docs_dir, output_file, code_analyzers, doc_analyzers,
    include_code, exclude_code, include_docs, exclude_docs,
    min_confidence, export_graph
):
    """Detect relationships between code and documentation files."""
    try:
        # Prepare output directory
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Analyzing code in: {code_dir}")
        logger.info(f"Analyzing documentation in: {docs_dir}")
        logger.info(f"Using code analyzers: {', '.join(code_analyzers)}")
        logger.info(f"Using doc analyzers: {', '.join(doc_analyzers)}")
        
        # Process code files
        code_analysis = _analyze_code(
            code_dir, 
            analyzers=code_analyzers,
            include_patterns=include_code,
            exclude_patterns=exclude_code
        )
        
        # Process documentation files
        doc_analysis = _analyze_documentation(
            docs_dir, 
            analyzers=doc_analyzers,
            include_patterns=include_docs,
            exclude_patterns=exclude_docs
        )
        
        # Map relationships between code and documentation
        relationships = _map_relationships(
            code_analysis,
            doc_analysis,
            min_confidence=min_confidence
        )
        
        # Write output
        output_data = {"relationships": relationships}
        
        # Add relationship graph if requested
        if export_graph:
            graph = _build_relationship_graph(relationships)
            graph_data = {
                "nodes": [_node_to_dict(node) for node in graph.nodes.values()],
                "edges": [_edge_to_dict(edge) for edge in graph.edges]
            }
            output_data["graph"] = graph_data
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"Found {len(relationships)} relationships")
        logger.info(f"Results saved to: {output_file}")
        
        logger.info(f"Detected {len(relationships)} relationships with confidence >= {min_confidence}")
        logger.info(f"Results saved to: {output_file}")
        
    except Exception as e:
        logger.error(f"Error detecting relationships: {e}")
        logger.error(f"Error detecting relationships: {str(e)}")
        raise click.ClickException(str(e))


def _discover_files(directory: str, file_filter: List[str], include_patterns: List[str] = None, exclude_patterns: List[str] = None) -> List[Path]:
    """Discover files in a directory using the FileDiscovery class.
    
    Args:
        directory: Directory to search in
        file_filter: List of glob patterns for file types to include
        include_patterns: Additional include patterns
        exclude_patterns: Exclude patterns
        
    Returns:
        List of discovered file paths
    """
    # Convert directory to Path
    dir_path = Path(directory)
    
    # Set up patterns
    all_include_patterns = set(file_filter)
    if include_patterns:
        all_include_patterns.update(include_patterns)
        
    exclude_set = set(exclude_patterns) if exclude_patterns else set()
    
    # Create file discovery
    file_discovery = FileDiscovery(
        include_patterns=all_include_patterns,
        exclude_patterns=exclude_set
    )
    
    # Discover files
    discovered_files = file_discovery.discover_files(dir_path)
    
    # Return paths
    return [Path(file.path) for file in discovered_files]


def _fix_discovered_file(file_path: Path) -> Dict[str, Any]:
    """Create a dictionary with all required DiscoveredFile fields.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary with required fields for DiscoveredFile
    """
    # Get file stat information
    stat_info = file_path.stat()
    
    return {
        "path": str(file_path),
        "relative_path": file_path.name,
        "size": stat_info.st_size,
        "is_binary": False,  # Assume text files for our analyzers
        "modified_time": datetime.fromtimestamp(stat_info.st_mtime)
    }


def _analyze_code(
    code_dir: str,
    analyzers: List[str] = None,
    include_patterns: List[str] = None,
    exclude_patterns: List[str] = None
) -> AnalysisResult:
    """Analyze code files and return analysis results."""
    analyzers = analyzers or ['python']
    
    # Create analyzer instances for each required analyzer
    analyzer_factory = AnalyzerFactory()
    code_analyzers = [analyzer_factory.create_analyzer(name) for name in analyzers]
    
    # Filter out None values (analyzers that couldn't be created)
    code_analyzers = [analyzer for analyzer in code_analyzers if analyzer is not None]
    
    if not code_analyzers:
        logger.warning(f"No valid analyzers found for types: {analyzers}. Analysis will be empty.")
    
    # Initialize result with a placeholder file_path
    result = AnalysisResult(file_path="code_analysis_result")
    
    for analyzer in code_analyzers:
        # Safety check before using the analyzer
        if analyzer is None:
            logger.warning("Skipping None analyzer")
            continue
            
        # Find all files that this analyzer can handle
        file_filter = analyzer.get_file_filter()
        files = _discover_files(code_dir, file_filter, include_patterns, exclude_patterns)
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract elements from the file
                file_elements = analyzer.analyze_file(file_path, content)
                
                # Add elements to the result
                for element in file_elements:
                    result.add_element(element)
                
                logger.debug(f"Analyzed {file_path} with {analyzer.__class__.__name__}, "
                            f"found {len(file_elements)} elements")
            except Exception as e:
                logger.warning(f"Error analyzing {file_path}: {str(e)}")
    
    return result


def _analyze_documentation(
    docs_dir: str,
    analyzers: List[str] = None,
    include_patterns: List[str] = None,
    exclude_patterns: List[str] = None
) -> AnalysisResult:
    """Analyze documentation files and return analysis results."""
    analyzers = analyzers or ['markdown']
    
    # Create analyzer instances for each required analyzer
    analyzer_factory = AnalyzerFactory()
    doc_analyzers = [analyzer_factory.create_analyzer(name) for name in analyzers]
    
    # Filter out None values (analyzers that couldn't be created)
    doc_analyzers = [analyzer for analyzer in doc_analyzers if analyzer is not None]
    
    if not doc_analyzers:
        logger.warning(f"No valid analyzers found for types: {analyzers}. Analysis will be empty.")
    
    # Initialize result with a placeholder file_path
    result = AnalysisResult(file_path="documentation_analysis_result")
    
    for analyzer in doc_analyzers:
        # Safety check before using the analyzer
        if analyzer is None:
            logger.warning("Skipping None analyzer")
            continue
            
        # Find all files that this analyzer can handle
        file_filter = analyzer.get_file_filter()
        files = _discover_files(docs_dir, file_filter, include_patterns, exclude_patterns)
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract elements from the file
                file_elements = analyzer.analyze_file(file_path, content)
                
                # Add elements to the result
                if isinstance(file_elements, list):
                    # Handle case where analyze_file returns a list of elements
                    for element in file_elements:
                        if hasattr(result, 'add_element'):
                            result.add_element(element)
                        else:
                            result.elements.append(element)
                elif hasattr(file_elements, 'elements'):
                    # Handle case where analyze_file returns an AnalysisResult
                    for element in file_elements.elements:
                        result.elements.append(element)
                else:
                    # Handle unexpected return type
                    logger.warning(f"Unexpected return type from {analyzer.__class__.__name__}.analyze_file: {type(file_elements)}")
                
                logger.debug(f"Analyzed {file_path} with {analyzer.__class__.__name__}, "
                            f"found {len(file_elements) if isinstance(file_elements, list) else 0} elements")
            except Exception as e:
                logger.warning(f"Error analyzing {file_path}: {str(e)}")
    
    return result


def _map_relationships(
    code_analysis: AnalysisResult,
    doc_analysis: AnalysisResult,
    min_confidence: float = 0.5
) -> List[Dict[str, Any]]:
    """Map relationships between code and documentation elements."""
    # Create and configure the pipeline
    pipeline = AnalysisPipeline()
    
    # Extract code and documentation elements
    code_elements = []
    if hasattr(code_analysis, 'elements'):
        code_elements = [elem for elem in code_analysis.elements if isinstance(elem, CodeElement)]
    
    doc_elements = []
    if hasattr(doc_analysis, 'elements'):
        doc_elements = [elem for elem in doc_analysis.elements if isinstance(elem, DocumentationElement)]
    
    logger.info(f"Found {len(code_elements)} code elements and {len(doc_elements)} documentation elements")
    
    # Execute the mapping process
    mapper = RelationshipMapper()
    mapper.add_code_elements(code_elements)
    mapper.add_doc_elements(doc_elements)
    relationships = mapper.map_relationships()
    
    # Filter relationships by confidence
    relationships = [r for r in relationships if r.confidence >= min_confidence]
    
    # Convert to dictionaries
    return [relationship.to_dict() for relationship in relationships]


def _build_relationship_graph(relationships: List[Dict[str, Any]]) -> RelationshipGraph:
    """Build a relationship graph from the detected relationships."""
    graph = RelationshipGraph()
    
    # First, collect all unique element IDs
    element_ids = set()
    for rel in relationships:
        element_ids.add(rel["source_id"])
        element_ids.add(rel["target_id"])
    
    # Add nodes to the graph
    for element_id in element_ids:
        # Determine if this is likely a code or documentation element
        # (This is a heuristic - in a real system, you'd have better information)
        is_source = any(rel["source_id"] == element_id for rel in relationships)
        node_type = "code" if is_source else "documentation"
        
        graph.add_node(
            node_id=element_id,
            node_type=node_type,
            data={"id": element_id}
        )
    
    # Add edges to the graph
    for rel in relationships:
        # Process relationship type (could be string or enum name)
        rel_type = rel["relationship_type"]
        
        try:
            # Try to convert string to enum if it's a valid enum value
            if isinstance(rel_type, str) and hasattr(RelationshipType, rel_type):
                rel_type = getattr(RelationshipType, rel_type)
        except (AttributeError, ValueError):
            # If conversion fails, keep as string
            pass
            
        graph.add_edge(
            source_id=rel["source_id"],
            target_id=rel["target_id"],
            relationship_type=rel_type,
            confidence=rel["confidence"],
            metadata=rel.get("metadata", {})
        )
    
    return graph


def _node_to_dict(node) -> Dict[str, Any]:
    """Convert a Node object to a dictionary."""
    return {
        "id": node.id,
        "node_type": node.node_type,
        "data": node.data
    }


def _edge_to_dict(edge) -> Dict[str, Any]:
    """Convert an Edge object to a dictionary."""
    # Handle both string and enum relationship types
    rel_type = edge.relationship_type
    if hasattr(edge.relationship_type, 'name'):
        rel_type = edge.relationship_type.name
    
    return {
        "source_id": edge.source.id,
        "target_id": edge.target.id,
        "relationship_type": rel_type,
        "confidence": edge.confidence,
        "metadata": edge.metadata
    } 