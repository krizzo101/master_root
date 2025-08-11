"""DAG loader for pipeline execution."""

import logging
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, ConfigDict

from opsvi_auto_forge.config.models import Project, Run, TaskRecord, TaskStatus
from opsvi_auto_forge.infrastructure.memory.graph.client import Neo4jClient

logger = logging.getLogger(__name__)


class DSLConfig(BaseModel):
    """DSL configuration model."""

    reasoning: Dict[str, Any] = Field(default_factory=dict)
    knowledge: Dict[str, Any] = Field(default_factory=dict)
    quality_gates: Dict[str, float] = Field(default_factory=dict)
    auto_repair: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        json_encoders={
            UUID: lambda v: str(v),
        }
    )


class PipelineConfig(BaseModel):
    """Pipeline configuration model."""

    name: str = Field(..., min_length=1, description="Pipeline name cannot be empty")
    description: Optional[str] = None
    version: str = "1.0.0"
    stages: List[Union[Dict[str, Any], "PipelineStage"]] = Field(default_factory=list)
    quality_gates: Dict[str, float] = Field(default_factory=dict)
    auto_repair: Dict[str, Any] = Field(default_factory=dict)
    dsl_config: Optional[DSLConfig] = None

    model_config = ConfigDict(
        json_encoders={
            UUID: lambda v: str(v),
        }
    )

    @field_validator("quality_gates")
    @classmethod
    def validate_quality_gates(cls, v: Dict[str, float]) -> Dict[str, float]:
        """Validate quality gate thresholds."""
        for gate, threshold in v.items():
            if not 0.0 <= threshold <= 1.0:
                raise ValueError(
                    f"Quality gate threshold must be between 0 and 1: {gate}={threshold}"
                )
        return v


class ExecutionDAG(BaseModel):
    """Execution DAG model."""

    id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None
    nodes: List["DAGNode"] = Field(default_factory=list)
    edges: List["DAGEdge"] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    quality_gates: Dict[str, float] = Field(default_factory=dict)
    auto_repair: Dict[str, Any] = Field(default_factory=dict)
    dsl_config: Optional[DSLConfig] = None

    model_config = ConfigDict(
        json_encoders={
            UUID: lambda v: str(v),
        }
    )


class DAGNode(BaseModel):
    """DAG node model."""

    id: Union[str, UUID]
    name: str
    agent: str
    task_type: str
    dependencies: List[str] = Field(default_factory=list)
    config: Dict[str, Any] = Field(default_factory=dict)
    quality_gates: Dict[str, float] = Field(default_factory=dict)
    auto_repair: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        json_encoders={
            UUID: lambda v: str(v),
        }
    )


class PipelineStage(BaseModel):
    """Pipeline stage model."""

    name: str = Field(..., min_length=1, description="Stage name cannot be empty")
    description: Optional[str] = None
    agent: str = Field(..., min_length=1, description="Agent name cannot be empty")
    task_type: str = Field(
        default="generic", min_length=1, description="Task type cannot be empty"
    )
    dependencies: List[str] = Field(default_factory=list)
    config: Dict[str, Any] = Field(default_factory=dict)
    quality_gates: Dict[str, float] = Field(default_factory=dict)
    auto_repair: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        json_encoders={
            UUID: lambda v: str(v),
        }
    )


class DAGEdge(BaseModel):
    """DAG edge model."""

    source: str
    target: str
    condition: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        json_encoders={
            UUID: lambda v: str(v),
        }
    )


class DAGLoader:
    """DAG loader for pipeline execution."""

    def __init__(self, neo4j_client: Optional[Neo4jClient] = None):
        """Initialize the DAG loader."""
        self.neo4j_client = neo4j_client
        self._dsl_config: Optional[DSLConfig] = None

    def load_dsl_config(
        self, config_path: str = "config/pipeline.schema.yml"
    ) -> DSLConfig:
        """Load DSL configuration from file."""
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                logger.warning(f"DSL config file not found: {config_path}")
                return DSLConfig()

            with open(config_file, "r") as f:
                config_data = yaml.safe_load(f)

            self._dsl_config = DSLConfig(**config_data)
            logger.info(f"Loaded DSL config from {config_path}")
            return self._dsl_config

        except Exception as e:
            logger.error(f"Failed to load DSL config: {e}")
            return DSLConfig()

    def process_dsl_knobs(self, pipeline_config: PipelineConfig) -> PipelineConfig:
        """Process DSL knobs and apply to pipeline configuration."""
        if not self._dsl_config:
            self.load_dsl_config()

        if not self._dsl_config:
            return pipeline_config

        # Apply reasoning knobs
        if self._dsl_config.reasoning:
            pipeline_config.auto_repair.update(
                {
                    "max_repair_attempts": self._dsl_config.reasoning.get(
                        "max_repair_attempts", 1
                    ),
                    "verifier_model": self._dsl_config.reasoning.get(
                        "verifier", "gpt-4.1-mini"
                    ),
                    "min_confidence": self._dsl_config.reasoning.get(
                        "min_confidence", 0.85
                    ),
                }
            )

        # Apply knowledge knobs
        if self._dsl_config.knowledge:
            pipeline_config.auto_repair.update(
                {
                    "cite_required": self._dsl_config.knowledge.get(
                        "cite_required", True
                    ),
                    "max_ctx_chars": self._dsl_config.knowledge.get(
                        "max_ctx_chars", 120000
                    ),
                    "freshness_days": self._dsl_config.knowledge.get(
                        "freshness_days", 90
                    ),
                }
            )

        # Apply quality gates
        if self._dsl_config.quality_gates:
            pipeline_config.quality_gates.update(self._dsl_config.quality_gates)

        # Apply auto-repair settings
        if self._dsl_config.auto_repair:
            pipeline_config.auto_repair.update(self._dsl_config.auto_repair)

        logger.info("Applied DSL knobs to pipeline configuration")
        return pipeline_config

    def load_pipeline(
        self, pipeline_name: str, config_path: Optional[str] = None
    ) -> ExecutionDAG:
        """Load pipeline configuration and create execution DAG."""
        try:
            # Load DSL configuration first
            self.load_dsl_config()

            # Load pipeline configuration
            if config_path is None:
                # Use the correct path relative to the current file
                # From dag_loader.py, go up to application/ and then to pipelines/
                config_path = str(
                    Path(__file__).parent.parent / "pipelines" / f"{pipeline_name}.yaml"
                )
                logger.info(f"Looking for pipeline file at: {config_path}")

            pipeline_file = Path(config_path)
            logger.info(f"Pipeline file exists: {pipeline_file.exists()}")
            if not pipeline_file.exists():
                raise FileNotFoundError(f"Pipeline file not found: {config_path}")

            with open(pipeline_file, "r") as f:
                pipeline_data = yaml.safe_load(f)

            # Create pipeline config
            pipeline_config = PipelineConfig(**pipeline_data)

            # Process DSL knobs
            pipeline_config = self.process_dsl_knobs(pipeline_config)

            # Convert to execution DAG
            dag = self._create_execution_dag(pipeline_config)

            logger.info(f"Loaded pipeline: {pipeline_name}")
            return dag

        except Exception as e:
            logger.error(f"Failed to load pipeline {pipeline_name}: {e}")
            raise

    async def validate_pipeline_tasks(
        self, dag: ExecutionDAG, registry_manager
    ) -> None:
        """Validate that all tasks referenced in the pipeline exist in the registry."""
        missing_tasks = []

        for node in dag.nodes:
            task = await registry_manager.get_task(node.name)
            if not task:
                missing_tasks.append(node.name)

        if missing_tasks:
            raise ValueError(f"Missing tasks in registry: {missing_tasks}")

        logger.info(
            f"Pipeline validation successful - all {len(dag.nodes)} tasks found in registry"
        )

    def _create_execution_dag(self, pipeline_config: PipelineConfig) -> ExecutionDAG:
        """Create execution DAG from pipeline configuration."""
        nodes = []
        edges = []

        # Create nodes from stages
        for i, stage in enumerate(pipeline_config.stages):
            # Handle both dictionary and PipelineStage objects
            if isinstance(stage, dict):
                stage_id = stage.get("id", f"stage_{i}")
                stage_name = stage["name"]
                stage_agent = stage["agent"]
                stage_task_type = stage.get("task_type", "generic")
                stage_dependencies = stage.get("dependencies", [])
                stage_config = stage.get("config", {})
            else:
                # PipelineStage object
                stage_id = getattr(stage, "id", f"stage_{i}")
                stage_name = stage.name
                stage_agent = stage.agent
                stage_task_type = stage.task_type
                stage_dependencies = stage.dependencies
                stage_config = stage.config

            node = DAGNode(
                id=stage_id,
                name=stage_name,
                agent=stage_agent,
                task_type=stage_task_type,
                dependencies=stage_dependencies,
                config=stage_config,
                quality_gates=pipeline_config.quality_gates,
                auto_repair=pipeline_config.auto_repair,
            )
            nodes.append(node)

            # Create edges from dependencies
            for dep in stage_dependencies:
                edge = DAGEdge(
                    source=dep,
                    target=stage_id,
                    condition=(
                        getattr(stage, "condition", None)
                        if not isinstance(stage, dict)
                        else stage.get("condition")
                    ),
                    metadata=(
                        getattr(stage, "edge_metadata", {})
                        if not isinstance(stage, dict)
                        else stage.get("edge_metadata", {})
                    ),
                )
                edges.append(edge)

        return ExecutionDAG(
            name=pipeline_config.name,
            description=pipeline_config.description,
            nodes=nodes,
            edges=edges,
            metadata=pipeline_config.model_dump(),
            quality_gates=pipeline_config.quality_gates,
            auto_repair=pipeline_config.auto_repair,
            dsl_config=self._dsl_config,
        )

    async def persist_pipeline(
        self, project_id: UUID, run_id: UUID, dag: ExecutionDAG
    ) -> None:
        """Persist pipeline configuration to Neo4j."""
        if not self.neo4j_client:
            return

        try:
            # Create pipeline node
            pipeline_query = """
            CREATE (p:Pipeline {
                id: $pipeline_id,
                name: $name,
                description: $description,
                project_id: $project_id,
                run_id: $run_id,
                quality_gates: $quality_gates,
                auto_repair: $auto_repair,
                dsl_config: $dsl_config,
                created_at: datetime()
            })
            """

            await self.neo4j_client.execute_write_query(
                pipeline_query,
                {
                    "pipeline_id": str(dag.id),
                    "name": dag.name,
                    "description": dag.description,
                    "project_id": str(project_id),
                    "run_id": str(run_id),
                    "quality_gates": dag.quality_gates,
                    "auto_repair": dag.auto_repair,
                    "dsl_config": dag.dsl_config.dict() if dag.dsl_config else {},
                },
            )

            # Create nodes
            for node in dag.nodes:
                node_query = """
                MATCH (p:Pipeline {id: $pipeline_id})
                CREATE (n:DAGNode {
                    id: $node_id,
                    name: $name,
                    agent: $agent,
                    task_type: $task_type,
                    dependencies: $dependencies,
                    config: $config,
                    quality_gates: $quality_gates,
                    auto_repair: $auto_repair
                })
                CREATE (n)-[:PART_OF]->(p)
                """

                await self.neo4j_client.execute_write_query(
                    node_query,
                    {
                        "pipeline_id": str(dag.id),
                        "node_id": node.id,
                        "name": node.name,
                        "agent": node.agent,
                        "task_type": node.task_type,
                        "dependencies": node.dependencies,
                        "config": node.config,
                        "quality_gates": node.quality_gates,
                        "auto_repair": node.auto_repair,
                    },
                )

            # Create edges
            for edge in dag.edges:
                edge_query = """
                MATCH (source:DAGNode {id: $source_id})
                MATCH (target:DAGNode {id: $target_id})
                CREATE (source)-[:DEPENDS_ON {condition: $condition, metadata: $metadata}]->(target)
                """

                await self.neo4j_client.execute_write_query(
                    edge_query,
                    {
                        "source_id": edge.source,
                        "target_id": edge.target,
                        "condition": edge.condition,
                        "metadata": edge.metadata,
                    },
                )

            logger.info(f"Persisted pipeline {dag.name} to Neo4j")

        except Exception as e:
            logger.error(f"Failed to persist pipeline: {e}")
            raise

    async def get_pipeline(self, pipeline_id: UUID) -> Optional[ExecutionDAG]:
        """Retrieve pipeline from Neo4j."""
        if not self.neo4j_client:
            return None

        try:
            query = """
            MATCH (p:Pipeline {id: $pipeline_id})
            OPTIONAL MATCH (n:DAGNode)-[:PART_OF]->(p)
            OPTIONAL MATCH (source:DAGNode)-[:DEPENDS_ON]->(target:DAGNode)
            WHERE source.id IN [n.id] AND target.id IN [n.id]
            
            WITH p, n, source, target
            ORDER BY n.id ASC, source.id ASC, target.id ASC
            
            WITH p, collect(n) as nodes, collect({source: source.id, target: target.id, condition: source.condition, metadata: source.metadata}) as edges
            
            RETURN p, nodes, edges
            """

            result = await self.neo4j_client.execute_read(
                query, {"pipeline_id": str(pipeline_id)}
            )

            if not result:
                return None

            # Reconstruct DAG from Neo4j data
            pipeline_data = result[0]["p"]
            nodes_data = result[0]["nodes"]
            edges_data = result[0]["edges"]

            nodes = []
            for node_data in nodes_data:
                if node_data:  # Skip None values
                    node = DAGNode(
                        id=node_data["id"],
                        name=node_data["name"],
                        agent=node_data["agent"],
                        task_type=node_data["task_type"],
                        dependencies=node_data.get("dependencies", []),
                        config=node_data.get("config", {}),
                        quality_gates=node_data.get("quality_gates", {}),
                        auto_repair=node_data.get("auto_repair", {}),
                    )
                    nodes.append(node)

            edges = []
            for edge_data in edges_data:
                if edge_data and edge_data["source"] and edge_data["target"]:
                    edge = DAGEdge(
                        source=edge_data["source"],
                        target=edge_data["target"],
                        condition=edge_data.get("condition"),
                        metadata=edge_data.get("metadata", {}),
                    )
                    edges.append(edge)

            return ExecutionDAG(
                id=pipeline_id,
                name=pipeline_data["name"],
                description=pipeline_data.get("description"),
                nodes=nodes,
                edges=edges,
                metadata=pipeline_data.get("metadata", {}),
                quality_gates=pipeline_data.get("quality_gates", {}),
                auto_repair=pipeline_data.get("auto_repair", {}),
                dsl_config=(
                    DSLConfig(**pipeline_data.get("dsl_config", {}))
                    if pipeline_data.get("dsl_config")
                    else None
                ),
            )

        except Exception as e:
            logger.error(f"Failed to retrieve pipeline {pipeline_id}: {e}")
            return None
