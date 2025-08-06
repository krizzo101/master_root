"""
Base RAG pipeline interface and data models.

Defines the common interface for all RAG pipelines and provides
data models for pipeline configuration, results, and stages.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any

from opsvi_foundation import BaseComponent, ComponentError, get_logger
from pydantic import BaseModel, Field


class PipelineError(ComponentError):
    """Base exception for pipeline errors."""

    pass


class PipelineStage(str, Enum):
    """Pipeline execution stages."""

    INITIALIZATION = "initialization"
    PROCESSING = "processing"
    VALIDATION = "validation"
    STORAGE = "storage"
    RETRIEVAL = "retrieval"
    GENERATION = "generation"
    COMPLETION = "completion"


class PipelineConfig(BaseModel):
    """Base configuration for RAG pipelines."""

    pipeline_name: str = Field(..., description="Name of the pipeline")
    timeout: float = Field(default=300.0, description="Pipeline timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    batch_size: int = Field(default=100, description="Batch size for processing")
    enable_monitoring: bool = Field(
        default=True, description="Enable pipeline monitoring"
    )

    class Config:
        extra = "allow"


class PipelineResult(BaseModel):
    """Result of pipeline execution."""

    success: bool = Field(..., description="Whether the pipeline succeeded")
    pipeline_name: str = Field(..., description="Name of the pipeline")
    start_time: datetime = Field(..., description="Pipeline start time")
    end_time: datetime | None = Field(default=None, description="Pipeline end time")
    duration: float | None = Field(
        default=None, description="Pipeline duration in seconds"
    )
    error_message: str | None = Field(
        default=None, description="Error message if failed"
    )
    stage_results: dict[str, Any] = Field(
        default_factory=dict, description="Results from each stage"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    class Config:
        extra = "allow"


class BaseRAGPipeline(BaseComponent, ABC):
    """
    Abstract base class for RAG pipelines.

    Provides a unified interface for executing RAG pipelines with
    proper error handling, monitoring, and stage management.
    """

    def __init__(self, config: PipelineConfig, **kwargs):
        """Initialize the RAG pipeline."""
        super().__init__(**kwargs)
        self.config = config
        self.logger = get_logger(__name__)

        # Pipeline state
        self._current_stage: PipelineStage | None = None
        self._stage_results: dict[str, Any] = {}
        self._start_time: datetime | None = None
        self._end_time: datetime | None = None

    @abstractmethod
    async def execute(self, **kwargs) -> PipelineResult:
        """
        Execute the pipeline.

        Args:
            **kwargs: Pipeline-specific arguments

        Returns:
            Pipeline execution result

        Raises:
            PipelineError: If pipeline execution fails
        """
        pass

    async def execute_with_timeout(self, **kwargs) -> PipelineResult:
        """
        Execute the pipeline with timeout.

        Args:
            **kwargs: Pipeline-specific arguments

        Returns:
            Pipeline execution result

        Raises:
            PipelineError: If pipeline execution fails or times out
        """
        try:
            return await asyncio.wait_for(
                self.execute(**kwargs),
                timeout=self.config.timeout,
            )
        except TimeoutError:
            raise PipelineError(
                f"Pipeline {self.config.pipeline_name} timed out after {self.config.timeout}s"
            )

    async def execute_with_retry(self, **kwargs) -> PipelineResult:
        """
        Execute the pipeline with retry logic.

        Args:
            **kwargs: Pipeline-specific arguments

        Returns:
            Pipeline execution result

        Raises:
            PipelineError: If pipeline execution fails after all retries
        """
        last_error = None

        for attempt in range(self.config.max_retries + 1):
            try:
                return await self.execute_with_timeout(**kwargs)
            except Exception as e:
                last_error = e
                if attempt < self.config.max_retries:
                    self.logger.warning(
                        f"Pipeline {self.config.pipeline_name} failed on attempt {attempt + 1}, "
                        f"retrying... Error: {e}"
                    )
                    await asyncio.sleep(2**attempt)  # Exponential backoff
                else:
                    self.logger.error(
                        f"Pipeline {self.config.pipeline_name} failed after {self.config.max_retries + 1} attempts"
                    )

        raise PipelineError(
            f"Pipeline failed after {self.config.max_retries + 1} attempts: {last_error}"
        )

    def _start_pipeline(self) -> None:
        """Start pipeline execution."""
        self._start_time = datetime.now()
        self._current_stage = PipelineStage.INITIALIZATION
        self._stage_results.clear()

        self.logger.info(f"Starting pipeline: {self.config.pipeline_name}")

    def _end_pipeline(
        self, success: bool, error_message: str | None = None
    ) -> PipelineResult:
        """End pipeline execution and create result."""
        self._end_time = datetime.now()
        self._current_stage = PipelineStage.COMPLETION

        duration = None
        if self._start_time and self._end_time:
            duration = (self._end_time - self._start_time).total_seconds()

        result = PipelineResult(
            success=success,
            pipeline_name=self.config.pipeline_name,
            start_time=self._start_time or datetime.now(),
            end_time=self._end_time,
            duration=duration,
            error_message=error_message,
            stage_results=self._stage_results.copy(),
            metadata=self._get_pipeline_metadata(),
        )

        if success:
            self.logger.info(
                f"Pipeline {self.config.pipeline_name} completed successfully in {duration:.2f}s"
            )
        else:
            self.logger.error(
                f"Pipeline {self.config.pipeline_name} failed: {error_message}"
            )

        return result

    def _set_stage(self, stage: PipelineStage) -> None:
        """Set the current pipeline stage."""
        self._current_stage = stage
        self.logger.debug(f"Pipeline {self.config.pipeline_name} stage: {stage.value}")

    def _add_stage_result(self, stage: str, result: Any) -> None:
        """Add result from a pipeline stage."""
        self._stage_results[stage] = result

    def _get_pipeline_metadata(self) -> dict[str, Any]:
        """Get pipeline metadata."""
        return {
            "pipeline_type": self.__class__.__name__,
            "config": self.config.dict(),
            "current_stage": self._current_stage.value if self._current_stage else None,
        }

    async def health_check(self) -> bool:
        """
        Perform a health check on the pipeline.

        Returns:
            True if the pipeline is healthy, False otherwise
        """
        try:
            # Basic health check - can be overridden by subclasses
            return True
        except Exception as e:
            self.logger.warning(f"Pipeline health check failed: {e}")
            return False

    def get_status(self) -> dict[str, Any]:
        """Get current pipeline status."""
        return {
            "pipeline_name": self.config.pipeline_name,
            "current_stage": self._current_stage.value if self._current_stage else None,
            "start_time": self._start_time.isoformat() if self._start_time else None,
            "duration": (datetime.now() - self._start_time).total_seconds()
            if self._start_time
            else None,
            "stage_results": list(self._stage_results.keys()),
        }
