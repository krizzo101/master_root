"""
Workflow Examples for Multi-Agent Orchestration

This module provides pre-built workflow examples demonstrating various
orchestration patterns and agent collaboration scenarios.
"""

from typing import Any, Dict, List

from ..orchestrator.workflow_orchestrator import ExecutionPattern


def create_data_analysis_workflow() -> Dict[str, Any]:
    """
    Create a data analysis workflow demonstrating sequential processing.

    This workflow shows how to:
    1. Load and validate data
    2. Process and transform data
    3. Generate analysis results
    4. Create summary reports

    Returns:
        Workflow configuration
    """
    return {
        "name": "Data Analysis Pipeline",
        "execution_pattern": ExecutionPattern.SEQUENTIAL,
        "steps": [
            {
                "step_id": "load_data",
                "agent_id": "task_agent",
                "task_type": "file_operation",
                "task_data": {
                    "operation": "read",
                    "file_path": "sample_data.csv",
                    "format": "csv",
                },
                "dependencies": [],
                "timeout": 30.0,
            },
            {
                "step_id": "validate_data",
                "agent_id": "task_agent",
                "task_type": "data_validation",
                "task_data": {
                    "schema": {
                        "required": ["id", "name", "value"],
                        "types": {"id": "int", "name": "str", "value": "float"},
                    },
                    "rules": [
                        {"type": "range", "field": "value", "min": 0, "max": 1000}
                    ],
                },
                "dependencies": ["load_data"],
                "timeout": 20.0,
            },
            {
                "step_id": "process_data",
                "agent_id": "task_agent",
                "task_type": "data_processing",
                "task_data": {
                    "operation": "aggregate",
                    "options": {
                        "group_by": ["category"],
                        "aggregations": {"value": "sum", "count": "count"},
                    },
                },
                "dependencies": ["validate_data"],
                "timeout": 30.0,
            },
            {
                "step_id": "generate_statistics",
                "agent_id": "task_agent",
                "task_type": "computation",
                "task_data": {"operation": "statistics"},
                "dependencies": ["process_data"],
                "timeout": 15.0,
            },
            {
                "step_id": "create_report",
                "agent_id": "task_agent",
                "task_type": "file_operation",
                "task_data": {
                    "operation": "write",
                    "file_path": "analysis_report.json",
                    "format": "json",
                },
                "dependencies": ["generate_statistics"],
                "timeout": 10.0,
            },
        ],
        "max_retries": 2,
        "timeout": 300.0,
    }


def create_research_pipeline() -> Dict[str, Any]:
    """
    Create a research pipeline workflow demonstrating agent collaboration.

    This workflow shows how to:
    1. Conduct web research on multiple topics
    2. Analyze and synthesize research results
    3. Generate comprehensive research reports

    Returns:
        Workflow configuration
    """
    return {
        "name": "Research Pipeline",
        "execution_pattern": ExecutionPattern.PARALLEL,
        "steps": [
            {
                "step_id": "research_topic_1",
                "agent_id": "research_agent",
                "task_type": "web_research",
                "task_data": {
                    "query": "machine learning trends 2024",
                    "max_results": 10,
                    "analysis_depth": "comprehensive",
                },
                "dependencies": [],
                "timeout": 120.0,
            },
            {
                "step_id": "research_topic_2",
                "agent_id": "research_agent",
                "task_type": "web_research",
                "task_data": {
                    "query": "artificial intelligence applications",
                    "max_results": 10,
                    "analysis_depth": "comprehensive",
                },
                "dependencies": [],
                "timeout": 120.0,
            },
            {
                "step_id": "research_topic_3",
                "agent_id": "research_agent",
                "task_type": "web_research",
                "task_data": {
                    "query": "multi-agent systems architecture",
                    "max_results": 10,
                    "analysis_depth": "comprehensive",
                },
                "dependencies": [],
                "timeout": 120.0,
            },
            {
                "step_id": "synthesize_research",
                "agent_id": "research_agent",
                "task_type": "content_synthesis",
                "task_data": {
                    "synthesis_type": "comprehensive_analysis",
                    "focus_areas": [
                        "common_themes",
                        "emerging_trends",
                        "technical_insights",
                        "future_directions",
                    ],
                },
                "dependencies": [
                    "research_topic_1",
                    "research_topic_2",
                    "research_topic_3",
                ],
                "timeout": 180.0,
            },
            {
                "step_id": "generate_report",
                "agent_id": "task_agent",
                "task_type": "file_operation",
                "task_data": {
                    "operation": "write",
                    "file_path": "research_report.md",
                    "format": "txt",
                },
                "dependencies": ["synthesize_research"],
                "timeout": 30.0,
            },
        ],
        "max_retries": 2,
        "timeout": 600.0,
    }


def create_parallel_processing_workflow() -> Dict[str, Any]:
    """
    Create a parallel processing workflow for high-throughput tasks.

    This workflow demonstrates:
    1. Parallel data processing across multiple agents
    2. Load balancing and task distribution
    3. Result aggregation and consolidation

    Returns:
        Workflow configuration
    """
    return {
        "name": "Parallel Processing Pipeline",
        "execution_pattern": ExecutionPattern.PARALLEL,
        "steps": [
            {
                "step_id": "prepare_data",
                "agent_id": "task_agent",
                "task_type": "data_processing",
                "task_data": {
                    "operation": "split",
                    "options": {"chunks": 4, "method": "equal_size"},
                },
                "dependencies": [],
                "timeout": 30.0,
            },
            {
                "step_id": "process_chunk_1",
                "agent_id": "task_agent",
                "task_type": "batch_processing",
                "task_data": {
                    "batch_size": 100,
                    "operation": {"type": "computation", "operation": "statistics"},
                },
                "dependencies": ["prepare_data"],
                "timeout": 60.0,
            },
            {
                "step_id": "process_chunk_2",
                "agent_id": "task_agent",
                "task_type": "batch_processing",
                "task_data": {
                    "batch_size": 100,
                    "operation": {"type": "computation", "operation": "statistics"},
                },
                "dependencies": ["prepare_data"],
                "timeout": 60.0,
            },
            {
                "step_id": "process_chunk_3",
                "agent_id": "task_agent",
                "task_type": "batch_processing",
                "task_data": {
                    "batch_size": 100,
                    "operation": {"type": "computation", "operation": "statistics"},
                },
                "dependencies": ["prepare_data"],
                "timeout": 60.0,
            },
            {
                "step_id": "process_chunk_4",
                "agent_id": "task_agent",
                "task_type": "batch_processing",
                "task_data": {
                    "batch_size": 100,
                    "operation": {"type": "computation", "operation": "statistics"},
                },
                "dependencies": ["prepare_data"],
                "timeout": 60.0,
            },
            {
                "step_id": "aggregate_results",
                "agent_id": "task_agent",
                "task_type": "data_processing",
                "task_data": {
                    "operation": "merge",
                    "options": {"merge_strategy": "concatenate"},
                },
                "dependencies": [
                    "process_chunk_1",
                    "process_chunk_2",
                    "process_chunk_3",
                    "process_chunk_4",
                ],
                "timeout": 30.0,
            },
            {
                "step_id": "finalize_results",
                "agent_id": "task_agent",
                "task_type": "file_operation",
                "task_data": {
                    "operation": "write",
                    "file_path": "parallel_processing_results.json",
                    "format": "json",
                },
                "dependencies": ["aggregate_results"],
                "timeout": 20.0,
            },
        ],
        "max_retries": 1,
        "timeout": 400.0,
    }


def create_conditional_workflow() -> Dict[str, Any]:
    """
    Create a conditional workflow demonstrating decision-based execution.

    This workflow shows:
    1. Conditional step execution based on previous results
    2. Dynamic workflow branching
    3. Error handling and fallback scenarios

    Returns:
        Workflow configuration
    """
    return {
        "name": "Conditional Processing Workflow",
        "execution_pattern": ExecutionPattern.CONDITIONAL,
        "steps": [
            {
                "step_id": "initial_check",
                "agent_id": "task_agent",
                "task_type": "data_validation",
                "task_data": {"validation_type": "data_quality_check"},
                "dependencies": [],
                "timeout": 30.0,
            },
            {
                "step_id": "high_quality_processing",
                "agent_id": "task_agent",
                "task_type": "data_processing",
                "task_data": {
                    "operation": "advanced_analysis",
                    "options": {"algorithm": "complex", "precision": "high"},
                },
                "dependencies": ["initial_check"],
                "conditions": {"step_result": ["initial_check", "high_quality"]},
                "timeout": 120.0,
            },
            {
                "step_id": "standard_processing",
                "agent_id": "task_agent",
                "task_type": "data_processing",
                "task_data": {
                    "operation": "standard_analysis",
                    "options": {"algorithm": "standard", "precision": "medium"},
                },
                "dependencies": ["initial_check"],
                "conditions": {"step_result": ["initial_check", "medium_quality"]},
                "timeout": 60.0,
            },
            {
                "step_id": "basic_processing",
                "agent_id": "task_agent",
                "task_type": "data_processing",
                "task_data": {
                    "operation": "basic_analysis",
                    "options": {"algorithm": "simple", "precision": "low"},
                },
                "dependencies": ["initial_check"],
                "conditions": {"step_result": ["initial_check", "low_quality"]},
                "timeout": 30.0,
            },
            {
                "step_id": "quality_enhancement",
                "agent_id": "task_agent",
                "task_type": "data_transformation",
                "task_data": {
                    "transformations": [
                        {"type": "normalize", "params": {"method": "z_score"}},
                        {"type": "clean", "params": {"remove_outliers": True}},
                    ]
                },
                "dependencies": ["basic_processing"],
                "conditions": {"step_status": ["basic_processing", "completed"]},
                "timeout": 45.0,
            },
            {
                "step_id": "research_supplement",
                "agent_id": "research_agent",
                "task_type": "web_research",
                "task_data": {
                    "query": "data quality improvement techniques",
                    "max_results": 5,
                    "analysis_depth": "focused",
                },
                "dependencies": ["initial_check"],
                "conditions": {"step_result": ["initial_check", "needs_research"]},
                "timeout": 90.0,
            },
            {
                "step_id": "final_report",
                "agent_id": "task_agent",
                "task_type": "file_operation",
                "task_data": {
                    "operation": "write",
                    "file_path": "conditional_workflow_report.json",
                    "format": "json",
                },
                "dependencies": [
                    "high_quality_processing",
                    "standard_processing",
                    "quality_enhancement",
                ],
                "timeout": 20.0,
            },
        ],
        "max_retries": 2,
        "timeout": 500.0,
    }


def create_pipeline_workflow() -> Dict[str, Any]:
    """
    Create a pipeline workflow demonstrating data flow between steps.

    This workflow shows:
    1. Sequential data processing with data flow
    2. Intermediate result passing
    3. Cumulative data transformation

    Returns:
        Workflow configuration
    """
    return {
        "name": "Data Processing Pipeline",
        "execution_pattern": ExecutionPattern.PIPELINE,
        "steps": [
            {
                "step_id": "data_ingestion",
                "agent_id": "task_agent",
                "task_type": "file_operation",
                "task_data": {
                    "operation": "read",
                    "file_path": "raw_data.csv",
                    "format": "csv",
                },
                "dependencies": [],
                "timeout": 30.0,
            },
            {
                "step_id": "data_cleaning",
                "agent_id": "task_agent",
                "task_type": "data_transformation",
                "task_data": {
                    "transformations": [
                        {"type": "remove_nulls", "params": {"strategy": "drop"}},
                        {"type": "deduplicate", "params": {"keep": "first"}},
                    ]
                },
                "dependencies": ["data_ingestion"],
                "timeout": 45.0,
            },
            {
                "step_id": "feature_engineering",
                "agent_id": "task_agent",
                "task_type": "data_transformation",
                "task_data": {
                    "transformations": [
                        {"type": "normalize", "params": {"method": "min_max"}},
                        {
                            "type": "feature_creation",
                            "params": {"features": ["ratio", "category"]},
                        },
                    ]
                },
                "dependencies": ["data_cleaning"],
                "timeout": 60.0,
            },
            {
                "step_id": "statistical_analysis",
                "agent_id": "task_agent",
                "task_type": "computation",
                "task_data": {"operation": "statistics"},
                "dependencies": ["feature_engineering"],
                "timeout": 30.0,
            },
            {
                "step_id": "trend_analysis",
                "agent_id": "research_agent",
                "task_type": "data_analysis",
                "task_data": {
                    "analysis_type": "trend_detection",
                    "parameters": {"window_size": 30, "significance_threshold": 0.05},
                },
                "dependencies": ["statistical_analysis"],
                "timeout": 90.0,
            },
            {
                "step_id": "export_results",
                "agent_id": "task_agent",
                "task_type": "file_operation",
                "task_data": {
                    "operation": "write",
                    "file_path": "pipeline_results.json",
                    "format": "json",
                },
                "dependencies": ["trend_analysis"],
                "timeout": 20.0,
            },
        ],
        "max_retries": 2,
        "timeout": 400.0,
    }


# Workflow factory function
def create_workflow_by_type(workflow_type: str) -> Dict[str, Any]:
    """
    Create a workflow by type.

    Args:
        workflow_type: Type of workflow to create

    Returns:
        Workflow configuration

    Raises:
        ValueError: If workflow type is not supported
    """
    workflow_factories = {
        "data_analysis": create_data_analysis_workflow,
        "research_pipeline": create_research_pipeline,
        "parallel_processing": create_parallel_processing_workflow,
        "conditional": create_conditional_workflow,
        "pipeline": create_pipeline_workflow,
    }

    if workflow_type not in workflow_factories:
        raise ValueError(f"Unsupported workflow type: {workflow_type}")

    return workflow_factories[workflow_type]()


def get_available_workflows() -> List[str]:
    """
    Get list of available workflow types.

    Returns:
        List of workflow type names
    """
    return [
        "data_analysis",
        "research_pipeline",
        "parallel_processing",
        "conditional",
        "pipeline",
    ]


def get_workflow_description(workflow_type: str) -> str:
    """
    Get description of a workflow type.

    Args:
        workflow_type: Type of workflow

    Returns:
        Workflow description
    """
    descriptions = {
        "data_analysis": "Sequential data analysis pipeline with validation and reporting",
        "research_pipeline": "Parallel research workflow with web scraping and synthesis",
        "parallel_processing": "High-throughput parallel processing with load balancing",
        "conditional": "Decision-based workflow with conditional execution paths",
        "pipeline": "Data processing pipeline with sequential transformations",
    }

    return descriptions.get(workflow_type, "Unknown workflow type")
