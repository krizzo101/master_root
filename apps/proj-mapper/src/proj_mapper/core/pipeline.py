"""Pipeline module.

This module provides the core pipeline functionality for processing projects.
"""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Generic, List, Optional, TypeVar, Callable

logger = logging.getLogger(__name__)

# Type variables for pipeline input and output
T = TypeVar('T')
U = TypeVar('U')


@dataclass
class PipelineContext:
    """Context object for sharing data between pipeline stages."""
    
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)
    
    def set_data(self, key: str, value: Any) -> None:
        """Set a value in the context data.
        
        Args:
            key: The key to set
            value: The value to set
        """
        self.data[key] = value
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """Get a value from the context data.
        
        Args:
            key: The key to get
            default: Default value if key doesn't exist
            
        Returns:
            The value or default
        """
        return self.data.get(key, default)
    
    def has_data(self, key: str) -> bool:
        """Check if a key exists in the context data.
        
        Args:
            key: The key to check
            
        Returns:
            True if the key exists, False otherwise
        """
        return key in self.data
    
    def set_metadata(self, key: str, value: Any) -> None:
        """Set a metadata value.
        
        Args:
            key: The key to set
            value: The value to set
        """
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get a metadata value.
        
        Args:
            key: The key to get
            default: Default value if key doesn't exist
            
        Returns:
            The value or default
        """
        return self.metadata.get(key, default)
    
    def has_metadata(self, key: str) -> bool:
        """Check if a key exists in the metadata.
        
        Args:
            key: The key to check
            
        Returns:
            True if the key exists, False otherwise
        """
        return key in self.metadata
    
    def elapsed_time(self) -> float:
        """Get the elapsed time since the context was created.
        
        Returns:
            Elapsed time in seconds
        """
        return time.time() - self.start_time


class PipelineStage(ABC):
    """Base class for pipeline stages."""
    
    @abstractmethod
    def process(self, context: PipelineContext) -> PipelineContext:
        """Process data through the pipeline stage.
        
        Args:
            context: The pipeline context
            
        Returns:
            The updated context
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Pipeline stages must implement process()")


class ConditionalPipelineStage(PipelineStage):
    """Pipeline stage that only processes if a condition is met."""
    
    def __init__(self, stage: PipelineStage, condition_key: str, condition_value: Any = True):
        """Initialize the conditional pipeline stage.
        
        Args:
            stage: The stage to conditionally process
            condition_key: The key to check in the context data
            condition_value: The value to compare against (default: True)
        """
        self.stage = stage
        self.condition_key = condition_key
        self.condition_value = condition_value
    
    def process(self, context: PipelineContext) -> PipelineContext:
        """Process data if the condition is met.
        
        Args:
            context: The pipeline context
            
        Returns:
            The updated context
        """
        # Get the value to check
        value = context.get_data(self.condition_key)
        
        # Process if the condition is met
        if value == self.condition_value:
            return self.stage.process(context)
        
        # Otherwise, pass through unchanged
        return context


class Pipeline:
    """Pipeline for processing data through a series of stages."""
    
    def __init__(self, on_error: Optional[Callable] = None):
        """Initialize the pipeline.
        
        Args:
            on_error: Optional error handler function
        """
        self.stages: List[PipelineStage] = []
        self.context: Optional[PipelineContext] = None
        self.on_error = on_error or self._default_error_handler
        logger.debug("Pipeline instance created")
    
    def add_stage(self, stage: PipelineStage) -> None:
        """Add a stage to the pipeline.
        
        Args:
            stage: The stage to add
        """
        self.stages.append(stage)
        logger.debug(f"Added pipeline stage: {stage.__class__.__name__}")
    
    def run(self, context: Optional[PipelineContext] = None) -> PipelineContext:
        """Run data through the pipeline.
        
        Args:
            context: Optional initial context
            
        Returns:
            The pipeline context with results
        """
        logger.info("Starting pipeline execution")
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Pipeline contains {len(self.stages)} stages")
            for i, stage in enumerate(self.stages):
                logger.debug(f"Stage {i+1}: {stage.__class__.__name__}")
        
        # Initialize context
        self.context = context or PipelineContext()
        current_context = self.context
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Initial context data keys: {list(current_context.data.keys())}")
            logger.debug(f"Initial context metadata keys: {list(current_context.metadata.keys())}")
        
        # Process each stage
        for i, stage in enumerate(self.stages):
            stage_name = stage.__class__.__name__
            logger.info(f"Running stage {i+1}/{len(self.stages)}: {stage_name}")
            
            # Time the stage execution
            start_time = time.time()
            
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Entering stage {stage_name} with context data keys: {list(current_context.data.keys())}")
                for key in current_context.data.keys():
                    value = current_context.get_data(key)
                    if isinstance(value, (str, int, float, bool)) or value is None:
                        logger.debug(f"Context data {key}: {value}")
                    elif hasattr(value, '__len__'):
                        try:
                            length = len(value)
                            logger.debug(f"Context data {key}: (type: {type(value).__name__}, length: {length})")
                        except:
                            logger.debug(f"Context data {key}: (type: {type(value).__name__})")
                    else:
                        logger.debug(f"Context data {key}: (type: {type(value).__name__})")
            
            try:
                # Process the stage - use the context from the previous stage
                logger.debug(f"Executing stage {stage_name}")
                current_context = stage.process(current_context)
                
                # Record timing
                elapsed = time.time() - start_time
                current_context.set_metadata(f"timing_{stage_name}", elapsed)
                
                logger.info(f"Completed stage {stage_name} in {elapsed:.2f}s")
                
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"Stage {stage_name} completed, resulting context data keys: {list(current_context.data.keys())}")
                    new_keys = set(current_context.data.keys()) - set(self.context.data.keys())
                    if new_keys:
                        logger.debug(f"New data keys added by stage {stage_name}: {list(new_keys)}")
                    
                    modified_data = []
                    for key in self.context.data.keys():
                        if key in current_context.data and self.context.data[key] != current_context.data[key]:
                            modified_data.append(key)
                    if modified_data:
                        logger.debug(f"Modified data keys by stage {stage_name}: {modified_data}")
                
            except Exception as e:
                logger.error(f"Error in stage {stage_name}: {e}")
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"Exception details for stage {stage_name}:", exc_info=True)
                    logger.debug(f"Context data at time of error: {list(current_context.data.keys())}")
                self.on_error(e, stage, current_context)
        
        # Update the stored context
        self.context = current_context
        
        total_time = current_context.elapsed_time()
        logger.info(f"Pipeline execution completed in {total_time:.2f}s")
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Pipeline timing summary:")
            timing_keys = [k for k in current_context.metadata.keys() if k.startswith("timing_")]
            for key in timing_keys:
                stage_name = key.replace("timing_", "")
                time_value = current_context.get_metadata(key)
                percentage = (time_value / total_time) * 100 if total_time > 0 else 0
                logger.debug(f"  {stage_name}: {time_value:.2f}s ({percentage:.1f}%)")
        
        return self.context
    
    def reset(self) -> None:
        """Reset the pipeline context."""
        self.context = None
        logger.debug("Pipeline context reset")
    
    def _default_error_handler(self, exception: Exception, stage: PipelineStage, context: PipelineContext) -> None:
        """Default error handler for pipeline stages.
        
        Args:
            exception: The exception that occurred
            stage: The stage that raised the exception
            context: The pipeline context
        """
        logger.error(f"Pipeline error in {stage.__class__.__name__}: {exception}")
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Pipeline error details for {stage.__class__.__name__}:", exc_info=True)
        # By default, re-raise the exception
        raise exception 