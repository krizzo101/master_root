# Output Generation Subsystem

The Output Generation Subsystem transforms relationship graphs into structured maps optimized for AI consumption. This subsystem provides the final step in the Project Mapper pipeline, creating organized and accessible representations of the project structure.

## Key Components

### Map Generator Framework

- **MapGenerator**: Coordinates the map generation process, delegating to templates and adapters.
- **MapTemplate**: Base class for defining how maps are structured. Templates define the organizational logic for maps.
- **GeneratorConfig**: Configuration options for controlling map generation behavior.

### Output Format Adapters

- **OutputAdapter**: Base class for output format adapters, with concrete implementations:
  - **JSONAdapter**: Produces JSON-formatted output
  - **MarkdownAdapter**: Produces Markdown-formatted output

### AI Optimization

- **TokenizationEstimator**: Estimates token usage for AI models
- **AIOptimizer**: Applies optimization techniques to make maps more AI-friendly

### Chunking Engine

- **ChunkingEngine**: Breaks large maps into manageable chunks
- **ChunkingStrategy**: Base class for chunking strategies
- **HierarchicalChunkingStrategy**: Strategy that creates hierarchical chunk structures

### Storage Management

- **StorageManager**: Handles persistence, versioning, and retrieval of generated maps

### Pipeline Integration

- **MapGeneratorStage**: Pipeline stage for generating maps from relationship graphs
- **MapStorageStage**: Pipeline stage for storing generated maps

## Usage Examples

### Basic Map Generation

```python
from proj_mapper.output import MapGenerator, GeneratorConfig, MapFormatType
from proj_mapper.output import JSONAdapter, ProjectOverviewTemplate

# Create a generator
generator = MapGenerator()

# Register a template
generator.register_template(ProjectOverviewTemplate())

# Register an adapter
generator.register_adapter(MapFormatType.JSON, JSONAdapter())

# Configure generation options
config = GeneratorConfig(
    output_format=MapFormatType.JSON,
    min_confidence=0.7,
    include_code=True,
    include_documentation=True,
    include_metadata=True
)

# Generate a map from a relationship graph
map_output, is_chunked = generator.generate_map(relationship_graph, config)
```

### Using the Storage Manager

```python
from proj_mapper.output import StorageManager, GeneratorConfig

# Create a storage manager
storage = StorageManager(base_dir=".maps")

# Store a map
path = storage.store_map(map_data, project_name="my_project", config=config)

# Get map history
history = storage.get_map_history("my_project")

# Get the latest map
latest_path = storage.get_latest_map("my_project")

# Clean old maps
deleted_count = storage.clean_old_maps("my_project", keep_count=5)
```

### Using AI Optimization

```python
from proj_mapper.output import AIOptimizer, GeneratorConfig

# Create a config with AI optimization
config = GeneratorConfig(ai_optimization_enabled=True)

# Create an optimizer
optimizer = AIOptimizer(config)

# Optimize a map
optimized_map = optimizer.optimize_map(map_structure)
```

### Pipeline Integration

```python
from proj_mapper.pipeline import Pipeline
from proj_mapper.output import MapGeneratorStage, MapStorageStage, GeneratorConfig

# Create a pipeline
pipeline = Pipeline()

# Create config
config = GeneratorConfig(output_format=MapFormatType.JSON)

# Add output stages
pipeline.add_stage(MapGeneratorStage(config))
pipeline.add_stage(MapStorageStage(".maps", config))

# Execute the pipeline
result_context = pipeline.execute(context)

# Access the result
map_data = result_context.data.get("map")
map_path = result_context.data.get("map_storage_path")
```

## Command-Line Interface

The output subsystem provides CLI commands for generating and managing maps:

```bash
# Generate a map from analysis results
proj-mapper output generate --analysis-file results.json --output-file map.json

# List available maps
proj-mapper output list

# List maps for a specific project
proj-mapper output list --project my_project

# Clean old maps for a project
proj-mapper output clean --project my_project --keep 5

# Delete all maps for a project
proj-mapper output delete --project my_project
```

## Map Format Structure

The output maps are structured to provide efficient access to project elements and their relationships. The general structure includes:

- **Project metadata**: Basic information about the project
- **Code elements**: Structured representation of code components
- **Documentation elements**: Structured representation of documentation components
- **Relationships**: Connections between elements with confidence scores
- **Statistics**: Metrics about the project structure

Maps can be chunked for large projects, creating a hierarchy of smaller pieces with cross-references.
