"""Project Mapper output generation subsystem.

This package contains components for generating maps, visualizations, and other outputs.
"""

# Core configuration
from proj_mapper.output.config import GeneratorConfig, MapFormatType

# Core generators
from proj_mapper.output.generator import (
    MapTemplate,
    MapGenerator
)

# Adapters
from proj_mapper.output.adapters import OutputAdapter
from proj_mapper.output.adapters.json_adapter import JSONAdapter
from proj_mapper.output.adapters.markdown_adapter import MarkdownAdapter

# Templates
from proj_mapper.output.templates.project_overview import ProjectOverviewTemplate

# Storage
from proj_mapper.output.storage import StorageManager, MapStorageProvider, LocalFileSystemStorage

# AI Optimization
from proj_mapper.output.ai_optimization import (
    TokenizationEstimator,
    AIOptimizer
)

# Chunking
from proj_mapper.output.chunking import (
    ChunkingStrategy,
    HierarchicalChunkingStrategy,
    ChunkingEngine
)

# Pipeline Integration
from proj_mapper.output.pipeline_stages import (
    MapGenerationStage,
    VisualizationGenerationStage
)

# Visualization
from proj_mapper.output.visualization import (
    VisualizationGenerator,
    VisualizationConfig,
    VisualizationType,
    VisualizationFormat,
    DotRenderer,
    GraphRenderer
)

# Formatters
from proj_mapper.output.formatters import JSONFormatter

__all__ = [
    # Core configuration
    'GeneratorConfig',
    'MapFormatType',
    
    # Core generators
    'MapTemplate',
    'MapGenerator',
    
    # Adapters
    'OutputAdapter',
    'JSONAdapter',
    'MarkdownAdapter',
    
    # Templates
    'ProjectOverviewTemplate',
    
    # Storage
    'StorageManager',
    'MapStorageProvider',
    'LocalFileSystemStorage',
    
    # AI Optimization
    'TokenizationEstimator',
    'AIOptimizer',
    
    # Chunking
    'ChunkingStrategy',
    'HierarchicalChunkingStrategy',
    'ChunkingEngine',
    
    # Pipeline Integration
    'MapGenerationStage',
    'VisualizationGenerationStage',
    
    # Visualization
    'VisualizationGenerator',
    'VisualizationConfig',
    'VisualizationType',
    'VisualizationFormat',
    'DotRenderer',
    'GraphRenderer',
    
    # Formatters
    'JSONFormatter'
]
