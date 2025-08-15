# Relationship Mapping Subsystem

This package provides functionality for mapping relationships between code and documentation elements. It identifies, scores, and manages these relationships to help understand the connections between code and documentation.

## Overview

The Relationship Mapping Subsystem consists of the following components:

1. **Relationship Detector**: Detects relationships between code and documentation elements using various rules and heuristics.
2. **Confidence Scorer**: Scores the confidence of detected relationships based on various criteria.
3. **Cross-Reference Resolver**: Finds and resolves references between code and documentation elements.
4. **Relationship Graph**: Provides a graph representation of relationships between elements.
5. **Relationship Service**: High-level API for accessing and querying relationships.
6. **Pipeline Integration**: Stages for integrating with the pipeline architecture.

## Component Descriptions

### Relationship Detector

The detector analyzes code and documentation elements to identify potential relationships between them. It uses different detection rules to identify specific types of relationships like:

- Import relationships
- Inheritance relationships
- Documentation references
- Name matching
- And more

Each rule evaluates specific characteristics of the elements to determine if a relationship exists.

### Confidence Scorer

The scorer evaluates the confidence of detected relationships based on various strategies:

- Relationship type scoring: Different relationship types have different base confidence scores.
- Contextual proximity scoring: Relationships between elements in similar contexts have higher confidence.
- Multiple detection scoring: Relationships detected by multiple rules have higher confidence.

### Cross-Reference Resolver

The resolver finds references between code and documentation elements by:

- Extracting potential code references from documentation text
- Matching documentation elements to referenced code elements
- Using both direct and fuzzy matching to increase accuracy

### Relationship Graph

The graph provides a structured representation of elements and their relationships:

- Nodes represent code and documentation elements
- Edges represent relationships between elements
- Supports querying, filtering, and traversing the graph
- Finds paths between elements

### Relationship Service

The service provides a high-level API for working with relationships:

- Query related elements for a specific element
- Filter relationships by type, confidence, etc.
- Find paths between elements
- Access relationship statistics

## Pipeline Integration

The subsystem integrates with the pipeline architecture through the following stages:

1. **RelationshipDetectionStage**: Detects relationships between elements
2. **RelationshipScoringStage**: Scores the confidence of relationships
3. **CrossReferenceResolutionStage**: Resolves references between elements
4. **RelationshipGraphBuildingStage**: Builds the relationship graph
5. **RelationshipServiceStage**: Creates the relationship service

## Command-Line Interface

The subsystem provides several CLI commands:

### Detect Relationships

```bash
proj_mapper relationship detect -a analysis_results.json -o relationships.json
```

Options:

- `--analysis-file, -a`: Path to JSON file containing analysis results (required)
- `--output-file, -o`: Path to output JSON file for relationships (required)
- `--min-confidence, -c`: Minimum confidence score for relationships (default: 0.5)
- `--include-graph/--no-graph`: Include relationship graph in output (default: true)
- `--fuzzy-threshold`: Minimum similarity score for fuzzy matching (default: 0.7)
- `--debug/--no-debug`: Enable debug logging (default: false)

### Query Relationships

```bash
proj_mapper relationship query -r relationships.json -e element_id
```

Options:

- `--relationships-file, -r`: Path to JSON file containing relationships data (required)
- `--element-id, -e`: ID of the element to query relationships for (required)
- `--relationship-type, -t`: Type of relationships to include (can be specified multiple times)
- `--min-confidence, -c`: Minimum confidence score for relationships (default: 0.5)
- `--max-depth, -d`: Maximum relationship depth (default: 1)
- `--output-format, -f`: Output format for results (json or text, default: text)

### Export Graph

```bash
proj_mapper relationship export-graph -r relationships.json -o graph.dot
```

Options:

- `--relationships-file, -r`: Path to JSON file containing relationships data (required)
- `--output-file, -o`: Path to output file for graph visualization (required)
- `--format, -f`: Output format for graph visualization (graphviz or json, default: graphviz)
- `--min-confidence, -c`: Minimum confidence score for relationships to include (default: 0.0)

## Usage Example

```python
from proj_mapper.core.pipeline import Pipeline, PipelineContext
from proj_mapper.relationship.pipeline_stages import (
    RelationshipDetectionStage,
    RelationshipScoringStage,
    CrossReferenceResolutionStage,
    RelationshipGraphBuildingStage,
    RelationshipServiceStage
)

# Create pipeline
pipeline = Pipeline(name="relationship_mapping")

# Add stages
pipeline.add_stage("detection", RelationshipDetectionStage())
pipeline.add_stage("scoring", RelationshipScoringStage())
pipeline.add_stage("cross_ref", CrossReferenceResolutionStage())
pipeline.add_stage("graph", RelationshipGraphBuildingStage())
pipeline.add_stage("service", RelationshipServiceStage())

# Create context with analysis results
context = PipelineContext()
context.set("analysis_results", analysis_results)

# Execute pipeline
service = pipeline.execute(context)

# Query related elements
related_elements = service.get_related_elements(
    element_id="my_element_id",
    relationship_types=["IMPLEMENTS", "REFERENCES"],
    min_confidence=0.7,
    max_depth=2
)
```
