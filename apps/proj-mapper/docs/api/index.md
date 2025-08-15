# Project Mapper API Reference

This is the API reference for Project Mapper, organized by subsystem.

## Core API

- [Configuration](core/configuration.md) - Configuration management
- [Pipeline](core/pipeline.md) - Pipeline execution
- [File Discovery](core/file_discovery.md) - File discovery and filtering

## Analyzers

- [Python Analyzer](analyzers/python.md) - Python code analysis
- [Markdown Analyzer](analyzers/markdown.md) - Markdown document analysis
- [Analyzer Manager](analyzers/manager.md) - Analyzer registration and coordination

## Relationship Mapping

- [Relationship Detector](relationship/detector.md) - Relationship detection
- [Relationship Models](relationship/models.md) - Relationship data structures
- [Confidence Scoring](relationship/scoring.md) - Relationship confidence calculation

## Output Generation

- [Map Generator](output/generator.md) - Map generation
- [JSON Formatter](output/formatters.md) - Output formatting
- [Chunking](output/chunking.md) - Map chunking for large projects

## Interfaces

- [Command Line Interface](interfaces/cli.md) - CLI usage
- [Python API](interfaces/api.md) - Python API usage

## Models

- [Analysis Results](models/analysis.md) - Analysis result models
- [Relationship Models](models/relationship.md) - Relationship data models

## Using the Python API

Project Mapper can be used as a library in your Python code:

```python
from proj_mapper import ProjectMapper

# Create a Project Mapper instance
mapper = ProjectMapper(project_root="/path/to/project")

# Generate a map
result = mapper.generate_map()

# Access the map data
map_data = result.map_data

# Access specific nodes
nodes = map_data["nodes"]

# Access relationships
relationships = map_data["relationships"]

# Filter relationships by type
imports = [r for r in relationships if r["type"] == "imports"]
```

## Advanced Usage

For more complex usage scenarios, you can use the individual components:

```python
from proj_mapper.core.config import ConfigManager
from proj_mapper.analyzers.manager import AnalyzerManager
from proj_mapper.relationship.detector import RelationshipDetector
from proj_mapper.output.generator import MapGenerator
from proj_mapper.output.formatters import JSONFormatter

# Create configuration
config = ConfigManager()
config.load_dict({
    "project": {"name": "my_project", "root": "/path/to/project"},
    "analyzers": {"python": {"enabled": True}, "markdown": {"enabled": True}},
})

# Create components
analyzer_manager = AnalyzerManager(config)
relationship_detector = RelationshipDetector(config)
map_generator = MapGenerator(output_dir="/path/to/output")
map_generator.register_formatter(JSONFormatter())

# Run analysis
analysis_results = analyzer_manager.analyze()

# Detect relationships
relationship_map = relationship_detector.detect_relationships(analysis_results)

# Generate map
output = map_generator.generate(relationship_map, format="json")
```

## Next Steps

- Check the detailed documentation for each module
- See the [Examples](../examples/index.md) for more usage scenarios
- Read the [Developer Guide](../developer/index.md) for extending Project Mapper
