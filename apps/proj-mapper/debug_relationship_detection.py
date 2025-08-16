#!/usr/bin/env python3
"""Diagnostic script for relationship detection issues."""

import sys
import json
import logging
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional

# Setup logging to file
log_dir = Path("./log")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "debug_relationship_detection.log"

# Configure file logger
file_handler = logging.FileHandler(filename=log_file, mode="w", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
file_handler.setFormatter(formatter)

# Configure console logger (INFO only)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter("%(levelname)s: %(message)s")
console_handler.setFormatter(console_formatter)

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

# Get logger for this module
logger = logging.getLogger(__name__)
logger.info(f"Logging to {log_file}")

# Original excepthook
original_excepthook = sys.excepthook

def enhanced_excepthook(exc_type, exc_value, exc_traceback):
    """Enhanced exception hook with detailed logging of attribute errors."""
    # Format the exception and traceback
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    
    # Log the exception
    logger.error("Exception caught by enhanced excepthook:")
    for line in tb_lines:
        logger.error(line.rstrip())
    
    # Enhanced debug for attribute errors
    if exc_type is AttributeError and "'str' object has no attribute" in str(exc_value):
        logger.error(f"DETECTED STRING ATTRIBUTE ERROR: {exc_value}")
        
        # Extract frames from the traceback
        frames = traceback.extract_tb(exc_traceback)
        if frames:
            last_frame = frames[-1]
            filename, lineno, funcname, line = last_frame
            logger.error(f"Error occurred in {filename} at line {lineno} in function {funcname}")
            if line:
                logger.error(f"Code: {line}")
                
            # Try to get variable values
            frame_obj = None
            for frame, _ in traceback.walk_tb(exc_traceback):
                if frame.f_code.co_filename == filename and frame.f_lineno == lineno:
                    frame_obj = frame
                    break
                    
            if frame_obj:
                logger.error("Local variables in the frame:")
                for var_name, var_value in frame_obj.f_locals.items():
                    logger.error(f"  {var_name} = {repr(var_value)}")
                    
                    # Inspect relationship_type more closely
                    if "relationship_type" in var_name.lower() or "node_type" in var_name.lower() or "type" in var_name.lower():
                        logger.error(f"  -> Type: {type(var_value)}")
                        logger.error(f"  -> Dir: {dir(var_value)}")
                        if hasattr(var_value, "__dict__"):
                            logger.error(f"  -> Dict: {var_value.__dict__}")
    
    # Call the original excepthook
    original_excepthook(exc_type, exc_value, exc_traceback)

# Install enhanced excepthook
sys.excepthook = enhanced_excepthook

def run_code_analysis(code_dir: str, include_patterns: Optional[List[str]] = None, exclude_patterns: Optional[List[str]] = None) -> Dict[str, Any]:
    """Run code analysis on the specified directory."""
    logger.info(f"Analyzing code in {code_dir}...")
    
    from proj_mapper.analyzers.code.python import PythonCodeAnalyzer
    from proj_mapper.core.file_discovery import FileDiscovery
    
    # Create file discovery instance
    file_discovery = FileDiscovery(
        include_patterns=include_patterns or ["*.py"],
        exclude_patterns=exclude_patterns or ["__pycache__", "venv"]
    )
    
    # Discover Python files
    logger.debug(f"Discovering Python files in {code_dir}...")
    discovered_files = file_discovery.discover_files(code_dir)
    logger.info(f"Found {len(discovered_files)} Python files")
    
    # Create Python code analyzer
    analyzer = PythonCodeAnalyzer()
    
    # Analyze each file
    code_elements = []
    for file in discovered_files:
        logger.debug(f"Analyzing file: {file.path}")
        try:
            elements = analyzer.analyze_file(file)
            code_elements.extend(elements)
            logger.debug(f"Found {len(elements)} code elements in {file.path}")
        except Exception as e:
            logger.error(f"Error analyzing {file.path}: {e}")
            logger.debug("Traceback:", exc_info=True)
    
    logger.info(f"Found {len(code_elements)} total code elements")
    
    # Log code element types for debugging
    for element in code_elements[:5]:  # Log just the first few
        logger.debug(f"Code element: {element.id}, type: {element.element_type}, name: {element.name}")
    
    return {"code_elements": code_elements}

def run_docs_analysis(docs_dir: str, include_patterns: Optional[List[str]] = None, exclude_patterns: Optional[List[str]] = None) -> Dict[str, Any]:
    """Run documentation analysis on the specified directory."""
    logger.info(f"Analyzing documentation in {docs_dir}...")
    
    from proj_mapper.analyzers.documentation.markdown import MarkdownAnalyzer
    from proj_mapper.core.file_discovery import FileDiscovery
    
    # Create file discovery instance
    file_discovery = FileDiscovery(
        include_patterns=include_patterns or ["*.md", "*.rst"],
        exclude_patterns=exclude_patterns or []
    )
    
    # Discover documentation files
    logger.debug(f"Discovering documentation files in {docs_dir}...")
    discovered_files = file_discovery.discover_files(docs_dir)
    logger.info(f"Found {len(discovered_files)} documentation files")
    
    # Create documentation analyzer
    analyzer = MarkdownAnalyzer()
    
    # Analyze each file
    doc_elements = []
    for file in discovered_files:
        logger.debug(f"Analyzing file: {file.path}")
        try:
            elements = analyzer.analyze_file(file)
            doc_elements.extend(elements)
            logger.debug(f"Found {len(elements)} documentation elements in {file.path}")
        except Exception as e:
            logger.error(f"Error analyzing {file.path}: {e}")
            logger.debug("Traceback:", exc_info=True)
    
    logger.info(f"Found {len(doc_elements)} total documentation elements")
    
    # Log documentation element types for debugging
    for element in doc_elements[:5]:  # Log just the first few
        logger.debug(f"Doc element: {element.id}, type: {element.element_type}, title: {element.title if hasattr(element, 'title') else 'N/A'}")
    
    return {"doc_elements": doc_elements}

def detect_relationships(code_elements: List[Any], doc_elements: List[Any]) -> List[Dict[str, Any]]:
    """Detect relationships between code and documentation elements."""
    logger.info("Detecting relationships between code and documentation elements...")
    
    from proj_mapper.relationship.detector.content_similarity import ContentSimilarityDetector
    from proj_mapper.relationship.detector.name_matching import NameMatchingDetector
    
    # Create relationship detectors
    detectors = [
        ContentSimilarityDetector(),
        NameMatchingDetector()
    ]
    
    # Detect relationships using each detector
    all_relationships = []
    for detector in detectors:
        logger.debug(f"Using detector: {detector.__class__.__name__}")
        try:
            relationships = detector.detect_relationships(code_elements, doc_elements)
            all_relationships.extend(relationships)
            logger.debug(f"Found {len(relationships)} relationships with {detector.__class__.__name__}")
            
            # Log relationship types for debugging
            for rel in relationships[:5]:  # Log just the first few
                logger.debug(f"Relationship: {rel.source_id} -> {rel.target_id}, "
                           f"type: {rel.relationship_type} (type: {type(rel.relationship_type)}), "
                           f"confidence: {rel.confidence}")
                           
                # Log detailed attributes
                logger.debug(f"  source_type: {rel.source_type} (type: {type(rel.source_type)})")
                logger.debug(f"  target_type: {rel.target_type} (type: {type(rel.target_type)})")
                
        except Exception as e:
            logger.error(f"Error with detector {detector.__class__.__name__}: {e}")
            logger.debug("Traceback:", exc_info=True)
    
    logger.info(f"Found {len(all_relationships)} total relationships")
    return all_relationships

def build_graph(relationships: List[Any]) -> Dict[str, Any]:
    """Build a relationship graph from the detected relationships."""
    logger.info("Building relationship graph...")
    
    from proj_mapper.relationship.graph.graph import RelationshipGraph
    from proj_mapper.relationship.pipeline_stages.discovery import _build_relationship_graph
    
    try:
        # First, try with the original function
        logger.debug("Attempting to build graph with original function...")
        graph = _build_relationship_graph(relationships)
        logger.info("Graph built successfully!")
        
        # Try to serialize the graph
        logger.debug("Serializing graph...")
        serialized = graph.serialize()
        logger.debug("Graph serialized successfully!")
        
        return serialized
        
    except Exception as e:
        logger.error(f"Error building relationship graph: {e}")
        logger.debug("Traceback:", exc_info=True)
        
        # Try with our own implementation
        logger.debug("Attempting to build graph with direct implementation...")
        graph = RelationshipGraph()
        
        # Add nodes and edges
        for rel in relationships:
            try:
                # Add source and target nodes
                source_type = rel.source_type
                target_type = rel.target_type
                
                logger.debug(f"Adding source node: {rel.source_id}, type: {source_type}")
                graph.add_node(rel.source_id, source_type)
                
                logger.debug(f"Adding target node: {rel.target_id}, type: {target_type}")
                graph.add_node(rel.target_id, target_type)
                
                # Add edge
                logger.debug(f"Adding edge: {rel.source_id} -> {rel.target_id}, type: {rel.relationship_type}")
                graph.add_edge(
                    rel.source_id, 
                    rel.target_id, 
                    rel.relationship_type,
                    rel.confidence,
                    rel.metadata
                )
            except Exception as e:
                logger.error(f"Error adding relationship to graph: {e}")
                logger.debug(f"Relationship: {rel.source_id} -> {rel.target_id}")
                continue
        
        logger.info(f"Graph built with {len(graph.nodes)} nodes and {len(graph.edges)} edges")
        
        # Try to serialize the graph
        try:
            logger.debug("Serializing graph...")
            serialized = graph.serialize()
            logger.debug("Graph serialized successfully!")
            return serialized
        except Exception as e:
            logger.error(f"Error serializing graph: {e}")
            logger.debug("Traceback:", exc_info=True)
            return {"error": str(e)}

def main():
    """Run the relationship detection process with step-by-step logging."""
    try:
        # Parse arguments
        code_dir = "src"
        docs_dir = "docs"
        output_file = "debug_relationships.json"
        include_code = ["*.py"]
        exclude_code = ["__pycache__", "venv"]
        
        logger.info("Starting relationship detection diagnostic...")
        logger.info(f"Code directory: {code_dir}")
        logger.info(f"Docs directory: {docs_dir}")
        
        # Step 1: Analyze code
        code_analysis = run_code_analysis(code_dir, include_code, exclude_code)
        code_elements = code_analysis.get("code_elements", [])
        
        # Step 2: Analyze documentation
        docs_analysis = run_docs_analysis(docs_dir)
        doc_elements = docs_analysis.get("doc_elements", [])
        
        # Step 3: Detect relationships
        relationships = detect_relationships(code_elements, doc_elements)
        
        # Step 4: Build relationship graph
        graph_data = build_graph(relationships)
        
        # Step 5: Save output
        output = {
            "relationships": [rel.__dict__ for rel in relationships],
            "graph": graph_data
        }
        
        with open(output_file, "w") as f:
            json.dump(output, f, indent=2, default=str)
        
        logger.info(f"Saved results to {output_file}")
        logger.info("Diagnostic completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Error in relationship detection: {e}")
        logger.debug("Traceback:", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 