"""
RAG pipeline orchestration and execution.

Provides end-to-end RAG pipelines for document ingestion, retrieval,
and generation with proper error handling and monitoring.
"""

from .base import (
    BaseRAGPipeline,
    PipelineConfig,
    PipelineResult,
    PipelineStage,
)
from .generation import GenerationConfig, GenerationPipeline
from .ingestion import IngestionConfig, IngestionPipeline
from .retrieval import RetrievalConfig, RetrievalPipeline

__all__ = [
    # Base classes
    "BaseRAGPipeline",
    "PipelineConfig",
    "PipelineResult",
    "PipelineStage",
    # Pipeline implementations
    "IngestionPipeline",
    "IngestionConfig",
    "RetrievalPipeline",
    "RetrievalConfig",
    "GenerationPipeline",
    "GenerationConfig",
]
