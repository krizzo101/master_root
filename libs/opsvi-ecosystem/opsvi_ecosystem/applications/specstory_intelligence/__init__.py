"""
SpecStory Intelligence System
Real-time atomic decomposition and intelligence extraction for SpecStory files

This system provides:
- Real-time file monitoring for SpecStory conversation files
- Complete atomic decomposition into 15 component types with relationships
- ArangoDB storage with full graph capabilities
- Pattern detection and continuous learning
- Character-level granularity for unlimited analysis potential

Main Components:
- SpecStoryFileMonitor: Watches for new/changed SpecStory files
- AtomicSpecStoryParser: Parses files into atomic components and relationships
- SpecStoryDatabaseStorage: Stores and queries atomic data in ArangoDB
- SpecStoryIntelligencePipeline: Coordinates the complete real-time system
"""

# from .file_monitor import SpecStoryFileWatcher as SpecStoryFileMonitor
from .atomic_parser import (
    AtomicComponent,
    AtomicRelationship,
    AtomicSpecStoryParser,
    ComponentBoundaries,
    ComponentType,
    RelationshipType,
)
from .database_storage import SpecStoryDatabaseStorage
from .pipeline import ProcessingMetrics, SpecStoryIntelligencePipeline

__version__ = "1.0.0"
__author__ = "SpecStory Intelligence Team"

# Main classes for external use
__all__ = [
    # Core pipeline
    "SpecStoryIntelligencePipeline",
    # Individual components
    "SpecStoryFileMonitor",
    "AtomicSpecStoryParser",
    "SpecStoryDatabaseStorage",
    # Data structures
    "AtomicComponent",
    "AtomicRelationship",
    "ComponentBoundaries",
    "ProcessingMetrics",
    # Enums
    "ComponentType",
    "RelationshipType",
    # Utilities
    "create_pipeline",
    "run_pipeline_standalone",
]


def create_pipeline(config: dict = None) -> SpecStoryIntelligencePipeline:
    """
    Create a configured SpecStory Intelligence Pipeline

    Args:
        config: Optional configuration dictionary

    Returns:
        Configured pipeline ready to start

    Example:
        pipeline = create_pipeline({
            "watch_directory": ".specstory/history",
            "max_workers": 3,
            "enable_real_time_analysis": True
        })

        success = await pipeline.start()
    """
    return SpecStoryIntelligencePipeline(config)


async def run_pipeline_standalone(config: dict = None):
    """
    Run the pipeline in standalone mode (convenience function)

    Args:
        config: Optional configuration dictionary

    Example:
        import asyncio
        from specstory_intelligence import run_pipeline_standalone

        asyncio.run(run_pipeline_standalone({
            "watch_directory": ".specstory/history",
            "log_level": "INFO"
        }))
    """
    pipeline = create_pipeline(config)

    try:
        success = await pipeline.start()
        if not success:
            print("❌ Failed to start pipeline")
            return

        print("🚀 SpecStory Intelligence Pipeline is running!")
        print("Press Ctrl+C to stop gracefully...")

        # Keep running until interrupted
        while pipeline.is_running:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested...")

    finally:
        await pipeline.stop()
        print("✅ Pipeline stopped")


# Default configuration template
DEFAULT_CONFIG = {
    "watch_directory": ".specstory/history",
    "file_pattern": "*.md",
    "collection_prefix": "specstory",
    "max_workers": 3,
    "batch_size": 5,
    "processing_delay": 1.0,
    "enable_metrics": True,
    "enable_real_time_analysis": True,
    "enable_pattern_detection": True,
    "log_level": "INFO",
}


# Version information
def get_version_info():
    """Get detailed version information"""
    return {
        "version": __version__,
        "author": __author__,
        "description": "Real-time SpecStory intelligence extraction system",
        "capabilities": [
            "Real-time file monitoring",
            "Atomic component decomposition (15 types)",
            "Character-level granularity",
            "Graph relationship modeling",
            "ArangoDB storage optimization",
            "Pattern detection",
            "Continuous learning",
        ],
    }


if __name__ == "__main__":
    import asyncio

    print("🧠 SpecStory Intelligence System")
    print("=" * 50)

    version_info = get_version_info()
    print(f"Version: {version_info['version']}")
    print(f"Author: {version_info['author']}")
    print(f"Description: {version_info['description']}")
    print("\nCapabilities:")
    for capability in version_info["capabilities"]:
        print(f"  • {capability}")

    print("\n🚀 Starting pipeline with default configuration...")
    asyncio.run(run_pipeline_standalone(DEFAULT_CONFIG))
