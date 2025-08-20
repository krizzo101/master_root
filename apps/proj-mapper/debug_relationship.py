import logging
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

try:
    from proj_mapper.analyzers.code.python_analyzer import PythonAnalyzer
    from proj_mapper.analyzers.documentation.markdown_analyzer import MarkdownAnalyzer
    from proj_mapper.claude_code_adapter import AnalyzerFactory
    from proj_mapper.cli.commands.relationship.discovery import (
        _build_relationship_graph,
        _map_relationships,
    )
    from proj_mapper.core.analysis_result import AnalysisResult
    from proj_mapper.models.relationship import RelationshipType

    # Monkey patch to address potential issues with Enum serialization
    # Add this to ensure we're using name instead of value
    def safe_to_dict(rel):
        return {
            "source_id": rel.source_id,
            "target_id": rel.target_id,
            "relationship_type": rel.relationship_type.name
            if hasattr(rel.relationship_type, "name")
            else str(rel.relationship_type),
            "confidence": rel.confidence,
            "metadata": rel.metadata,
        }

    # Try to run a simplified relationship detection
    python_analyzer = PythonAnalyzer()
    markdown_analyzer = MarkdownAnalyzer()

    # Create empty analysis results
    code_analysis = AnalysisResult()
    doc_analysis = AnalysisResult()

    # Add a code element
    file_path = str(Path("src/proj_mapper/models/relationship.py").absolute())
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    print(f"Analyzing {file_path}")
    code_elements = python_analyzer.analyze_file(file_path, content)
    for element in code_elements:
        code_analysis.add_element(element)

    # Add a documentation element
    file_path = str(Path("docs/developer/python_analyzer_implementation.md").absolute())
    if Path(file_path).exists():
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        print(f"Analyzing {file_path}")
        doc_elements = markdown_analyzer.analyze_file(file_path, content)
        for element in doc_elements:
            doc_analysis.add_element(element)
    else:
        print(f"File not found: {file_path}")
        # Create a dummy doc element for testing
        from proj_mapper.models.documentation import (
            DocumentationElement,
            DocumentationType,
        )

        doc_element = DocumentationElement(
            title="Test Document",
            content="Test content",
            file_path="test.md",
            element_type=DocumentationType.MARKDOWN_DOCUMENT,
        )
        doc_analysis.add_element(doc_element)

    # Map relationships
    print("Mapping relationships...")
    try:
        from proj_mapper.models.code import CodeElement
        from proj_mapper.models.documentation import DocumentationElement
        from proj_mapper.relationship.mapper import RelationshipMapper
        from proj_mapper.relationship.pipeline.pipeline import AnalysisPipeline

        # Create minimal pipeline
        pipeline = AnalysisPipeline()

        # Get elements
        code_elements = code_analysis.get_elements(CodeElement)
        doc_elements = doc_analysis.get_elements(DocumentationElement)

        print(
            f"Found {len(code_elements)} code elements and {len(doc_elements)} doc elements"
        )

        # Map relationships
        mapper = RelationshipMapper()
        relationships = mapper.map_relationships(
            code_elements=code_elements,
            doc_elements=doc_elements,
            pipeline=pipeline,
            min_confidence=0.5,
        )

        print(f"Generated {len(relationships)} relationships")

        # Build graph
        relationship_dicts = []
        for rel in relationships:
            # Use our safe dict converter
            rel_dict = safe_to_dict(rel)
            relationship_dicts.append(rel_dict)

        print("Successfully converted relationships to dictionaries")

        # Try to serialize to JSON
        import json

        from proj_mapper.utils.json_encoder import EnumEncoder

        json_data = json.dumps(relationship_dicts, indent=2, cls=EnumEncoder)
        print("Successfully serialized relationships to JSON")

        # Try to build the graph (this is where the error likely happens)
        graph = _build_relationship_graph(relationship_dicts)
        print("Successfully built relationship graph")

        # Export graph
        print("Exporting graph...")
        graph_dict = graph.serialize()
        print("Successfully serialized graph")

        # Output test data
        with open("debug_relationships.json", "w") as f:
            f.write(json_data)
        print("Wrote debug_relationships.json")

    except Exception as e:
        print(f"Error mapping relationships: {e}")
        traceback.print_exc()

except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
