"""Unit tests for the pipeline coordinator module."""

import pytest
import time
from unittest.mock import MagicMock, patch

from proj_mapper.core.pipeline import (
    PipelineContext,
    PipelineStage,
    Pipeline,
    ConditionalPipelineStage
)


def test_pipeline_context_init():
    """Test PipelineContext initialization."""
    context = PipelineContext()
    assert context.data == {}
    assert context.metadata == {}
    assert context.start_time is not None


def test_pipeline_context_set_get_data():
    """Test setting and getting data from PipelineContext."""
    context = PipelineContext()
    
    # Set data
    context.set_data("key1", "value1")
    context.set_data("key2", {"nested": "value"})
    
    # Get data
    assert context.get_data("key1") == "value1"
    assert context.get_data("key2") == {"nested": "value"}
    
    # Get non-existent data with default
    assert context.get_data("non_existent") is None
    assert context.get_data("non_existent", "default") == "default"


def test_pipeline_context_set_get_metadata():
    """Test setting and getting metadata from PipelineContext."""
    context = PipelineContext()
    
    # Set metadata
    context.set_metadata("stage1", "completed")
    context.set_metadata("timing", {"stage1": 0.5})
    
    # Get metadata
    assert context.get_metadata("stage1") == "completed"
    assert context.get_metadata("timing") == {"stage1": 0.5}
    
    # Get non-existent metadata with default
    assert context.get_metadata("non_existent") is None
    assert context.get_metadata("non_existent", "default") == "default"


def test_pipeline_context_has_data():
    """Test checking if a key exists in the context data."""
    context = PipelineContext()
    context.set_data("key1", "value1")
    
    assert context.has_data("key1") is True
    assert context.has_data("non_existent") is False


def test_pipeline_context_has_metadata():
    """Test checking if a key exists in the context metadata."""
    context = PipelineContext()
    context.set_metadata("key1", "value1")
    
    assert context.has_metadata("key1") is True
    assert context.has_metadata("non_existent") is False


def test_pipeline_context_elapsed_time():
    """Test getting elapsed time from PipelineContext."""
    context = PipelineContext()
    
    # Sleep a tiny bit to ensure elapsed time is measurable
    time.sleep(0.01)
    
    elapsed = context.elapsed_time()
    assert elapsed > 0


class SimpleStage(PipelineStage):
    """A simple pipeline stage for testing."""
    
    def process(self, context: PipelineContext) -> PipelineContext:
        """Process the context data."""
        data = context.get_data("input", "default")
        
        # For multiple stage tests, check if output already exists and build on it
        existing_output = context.get_data("output")
        if existing_output:
            data = existing_output
        
        context.set_data("output", f"processed_{data}")
        return context


class ErrorStage(PipelineStage):
    """A pipeline stage that raises an error for testing."""
    
    def process(self, context):
        """Raise an error during processing."""
        raise ValueError("Test error")


def test_pipeline_stage_abstract():
    """Test that PipelineStage is an abstract class."""
    with pytest.raises(TypeError):
        PipelineStage()


def test_pipeline_init():
    """Test Pipeline initialization."""
    pipeline = Pipeline()
    assert pipeline.stages == []
    assert pipeline.context is None
    assert pipeline.on_error is not None  # Default error handler


def test_pipeline_add_stage():
    """Test adding stages to a Pipeline."""
    pipeline = Pipeline()
    stage1 = SimpleStage()
    stage2 = SimpleStage()
    
    pipeline.add_stage(stage1)
    pipeline.add_stage(stage2)
    
    assert len(pipeline.stages) == 2
    assert pipeline.stages[0] == stage1
    assert pipeline.stages[1] == stage2


def test_pipeline_run():
    """Test running a Pipeline with stages."""
    pipeline = Pipeline()
    stage = SimpleStage()
    pipeline.add_stage(stage)
    
    # Create a context with input data
    context = PipelineContext()
    context.set_data("input", "test")
    
    # Run the pipeline
    result = pipeline.run(context)
    
    # Check that the stage processed the data
    assert result.get_data("output") == "processed_test"
    
    # Check that the pipeline stored the context
    assert pipeline.context is result


def test_pipeline_run_without_context():
    """Test running a Pipeline without providing a context."""
    pipeline = Pipeline()
    stage = SimpleStage()
    pipeline.add_stage(stage)
    
    # Run the pipeline without a context
    result = pipeline.run()
    
    # Check that the stage processed with default data
    assert result.get_data("output") == "processed_default"


def test_pipeline_error_handling():
    """Test Pipeline error handling."""
    # Create a mock error handler
    error_handler = MagicMock()
    
    pipeline = Pipeline(on_error=error_handler)
    stage = ErrorStage()
    pipeline.add_stage(stage)
    
    # Run the pipeline
    pipeline.run()
    
    # Check that the error handler was called
    error_handler.assert_called_once()
    args, _ = error_handler.call_args
    assert len(args) == 3
    assert isinstance(args[0], ValueError)  # Exception
    assert args[1] == stage  # Stage that failed
    assert isinstance(args[2], PipelineContext)  # Context


def test_pipeline_reset():
    """Test resetting a Pipeline."""
    pipeline = Pipeline()
    stage = SimpleStage()
    pipeline.add_stage(stage)
    
    # Run the pipeline to set the context
    context = pipeline.run()
    assert pipeline.context is context
    
    # Reset the pipeline
    pipeline.reset()
    assert pipeline.context is None


def test_conditional_pipeline_stage():
    """Test ConditionalPipelineStage processing based on a condition."""
    # Create a mock stage
    mock_stage = MagicMock(spec=PipelineStage)
    
    # Create a conditional stage that only runs if "run_stage" is True
    conditional_stage = ConditionalPipelineStage(
        stage=mock_stage,
        condition_key="run_stage"
    )
    
    # Create a context where the condition is True
    context_true = PipelineContext()
    context_true.set_data("run_stage", True)
    
    # Process the context
    conditional_stage.process(context_true)
    
    # Check that the mock stage was called
    mock_stage.process.assert_called_once_with(context_true)
    
    # Reset the mock
    mock_stage.reset_mock()
    
    # Create a context where the condition is False
    context_false = PipelineContext()
    context_false.set_data("run_stage", False)
    
    # Process the context
    result = conditional_stage.process(context_false)
    
    # Check that the mock stage was not called
    mock_stage.process.assert_not_called()
    
    # Check that the context was returned unchanged
    assert result is context_false


def test_conditional_pipeline_stage_missing_key():
    """Test ConditionalPipelineStage when the condition key is missing."""
    # Create a mock stage
    mock_stage = MagicMock(spec=PipelineStage)
    
    # Create a conditional stage
    conditional_stage = ConditionalPipelineStage(
        stage=mock_stage,
        condition_key="missing_key"
    )
    
    # Create a context without the condition key
    context = PipelineContext()
    
    # Process the context
    conditional_stage.process(context)
    
    # The stage should not be called when the key is missing
    mock_stage.process.assert_not_called()


def test_pipeline_multiple_stages():
    """Test a Pipeline with multiple stages in sequence."""
    # Create two simple stages
    stage1 = SimpleStage()
    stage2 = SimpleStage()
    
    # Create a pipeline with both stages
    pipeline = Pipeline()
    pipeline.add_stage(stage1)
    pipeline.add_stage(stage2)
    
    # Create a context with input data
    context = PipelineContext()
    context.set_data("input", "test")
    
    # Run the pipeline
    result = pipeline.run(context)
    
    # First stage should set output to "processed_test"
    # Second stage should set output to "processed_processed_test"
    assert result.get_data("output") == "processed_processed_test" 