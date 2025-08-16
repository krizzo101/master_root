# Pipeline API

The Pipeline is the central component of Project Mapper that coordinates the execution of all analysis, relationship detection, and map generation steps.

## Pipeline Class

```python
from proj_mapper.core.pipeline import Pipeline
```

### Constructor

```python
def __init__(self,
             config_manager,
             analyzer_manager,
             relationship_detector,
             map_generator):
    """
    Initialize the Pipeline with its component subsystems.

    Args:
        config_manager: An instance of ConfigManager
        analyzer_manager: An instance of AnalyzerManager
        relationship_detector: An instance of RelationshipDetector
        map_generator: An instance of MapGenerator
    """
```

### Methods

#### run

```python
def run(self):
    """
    Execute the complete pipeline.

    The pipeline performs these steps:
    1. Validate configuration
    2. Run analyzers on the project
    3. Detect relationships between files
    4. Generate maps from relationship data

    Returns:
        dict: A result object containing:
            - success (bool): Whether the pipeline completed successfully
            - analysis_results (list): Results from analysis if successful
            - relationship_map (RelationshipMap): The relationship map if successful
            - output (dict): Output generation results if successful
            - error (str): Error message if unsuccessful
    """
```

#### run_analysis

```python
def run_analysis(self):
    """
    Run only the analysis phase of the pipeline.

    Returns:
        dict: A result object containing:
            - success (bool): Whether the analysis completed successfully
            - analysis_results (list): Results from analysis if successful
            - error (str): Error message if unsuccessful
    """
```

#### run_relationship_detection

```python
def run_relationship_detection(self, analysis_results):
    """
    Run only the relationship detection phase of the pipeline.

    Args:
        analysis_results (list): Results from the analysis phase

    Returns:
        dict: A result object containing:
            - success (bool): Whether relationship detection completed successfully
            - relationship_map (RelationshipMap): The relationship map if successful
            - error (str): Error message if unsuccessful
    """
```

#### run_map_generation

```python
def run_map_generation(self, relationship_map):
    """
    Run only the map generation phase of the pipeline.

    Args:
        relationship_map (RelationshipMap): The relationship map from detection phase

    Returns:
        dict: A result object containing:
            - success (bool): Whether map generation completed successfully
            - output (dict): Output generation results if successful
            - error (str): Error message if unsuccessful
    """
```

### Error Handling

The Pipeline provides comprehensive error handling with detailed error messages for each phase:

```python
try:
    result = pipeline.run()

    if result["success"]:
        print("Pipeline completed successfully")
        # Access results
        analysis_results = result["analysis_results"]
        relationship_map = result["relationship_map"]
        output = result["output"]
    else:
        print(f"Pipeline failed: {result['error']}")
except Exception as e:
    print(f"Unexpected error: {str(e)}")
```

### Events

The Pipeline emits events during execution that can be subscribed to:

```python
def on_analysis_complete(results):
    print(f"Analysis complete with {len(results)} files analyzed")

pipeline.events.subscribe("analysis_complete", on_analysis_complete)
```

Available events:

| Event Name                        | Description                              | Payload          |
| --------------------------------- | ---------------------------------------- | ---------------- |
| `pipeline_start`                  | Pipeline execution started               | None             |
| `analysis_start`                  | Analysis phase started                   | None             |
| `analysis_complete`               | Analysis phase completed                 | Analysis results |
| `relationship_detection_start`    | Relationship detection started           | None             |
| `relationship_detection_complete` | Relationship detection completed         | Relationship map |
| `map_generation_start`            | Map generation started                   | None             |
| `map_generation_complete`         | Map generation completed                 | Output results   |
| `pipeline_complete`               | Pipeline execution completed             | Complete results |
| `pipeline_error`                  | Error occurred during pipeline execution | Error details    |

## Example Usage

### Basic Pipeline Execution

```python
from proj_mapper.core.config import ConfigManager
from proj_mapper.core.pipeline import Pipeline
from proj_mapper.analyzers.manager import AnalyzerManager
from proj_mapper.relationship.detector import RelationshipDetector
from proj_mapper.output.generator import MapGenerator
from proj_mapper.output.formatters import JSONFormatter

# Create configuration
config = ConfigManager()
config.load_file("config.json")

# Create components
analyzer_manager = AnalyzerManager(config)
relationship_detector = RelationshipDetector(config)
map_generator = MapGenerator(output_dir="./maps")
map_generator.register_formatter(JSONFormatter())

# Create pipeline
pipeline = Pipeline(
    config_manager=config,
    analyzer_manager=analyzer_manager,
    relationship_detector=relationship_detector,
    map_generator=map_generator
)

# Run pipeline
result = pipeline.run()

if result["success"]:
    print(f"Generated map at: {result['output']['file_path']}")
else:
    print(f"Error: {result['error']}")
```

### Running Individual Phases

```python
# Run only analysis
analysis_result = pipeline.run_analysis()
if analysis_result["success"]:
    analysis_data = analysis_result["analysis_results"]

    # Process analysis data independently
    print(f"Analyzed {len(analysis_data)} files")

    # Then run relationship detection with the results
    relationship_result = pipeline.run_relationship_detection(analysis_data)
    if relationship_result["success"]:
        relationship_map = relationship_result["relationship_map"]

        # Generate map from relationship data
        output_result = pipeline.run_map_generation(relationship_map)
        if output_result["success"]:
            print(f"Map generated at: {output_result['output']['file_path']}")
```

## Performance Considerations

- For large projects, consider using the individual phase methods to process data in batches
- The pipeline is designed to be memory efficient, but very large projects may require chunking
- Progress can be monitored by subscribing to the events emitted during execution
