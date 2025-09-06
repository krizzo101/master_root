"""
SleuthIntelOrchestrator - Advanced Intelligence Workflow Management

Extends orchestration capabilities for intelligence gathering workflows with:
- Multi-agent coordination and workflow patterns
- Rate limit management and credit optimization
- Dynamic agent selection and load balancing
- Result aggregation and correlation analysis
- Integration with SecureAPILocker for credential management
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from threading import Lock, RLock
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from uuid import uuid4

from ..agents.base_agent import BaseIntelligenceAgent, RateLimitConfig
from ..core.secure_api_locker import APICredential, APILockerManager
from ..models.intelligence import IntelligenceResult
from ..models.query import IntelligenceQuery

try:
    from ...agent_orchestrator.src.orchestrator_integration import (
        OrchestratorIntegration,
    )
except ImportError:
    # Fallback if orchestrator integration not available
    class OrchestratorIntegration:
        def __init__(self, *args, **kwargs):
            pass

        def add_agent(self, *args, **kwargs):
            return False

        def complete_run(self, *args, **kwargs):
            return False


logger = logging.getLogger(__name__)


class WorkflowType(Enum):
    """Supported workflow patterns"""

    SINGLE_SOURCE = "single_source"
    MULTI_SOURCE_PARALLEL = "multi_source_parallel"
    INVESTIGATION_CHAIN = "investigation_chain"
    BULK_PROCESSING = "bulk_processing"
    ADAPTIVE_ENRICHMENT = "adaptive_enrichment"


class AgentStatus(Enum):
    """Agent execution status"""

    IDLE = "idle"
    RUNNING = "running"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"
    QUOTA_EXHAUSTED = "quota_exhausted"


@dataclass
class WorkflowConfig:
    """Configuration for workflow execution"""

    max_parallel_agents: int = 5
    timeout_seconds: int = 300
    enable_caching: bool = True
    cache_ttl: int = 3600
    retry_failed_queries: bool = True
    max_retries: int = 3
    correlation_threshold: float = 0.8
    cost_optimization: bool = True
    preferred_providers: List[str] = field(default_factory=list)


@dataclass
class AgentPool:
    """Pool of available agents by type"""

    agent_class: type
    instances: List[BaseIntelligenceAgent] = field(default_factory=list)
    max_instances: int = 3
    current_load: int = 0
    last_used: datetime = field(default_factory=datetime.now)
    provider_rotation_index: int = 0


@dataclass
class WorkflowExecution:
    """Tracking data for workflow execution"""

    workflow_id: str
    workflow_type: WorkflowType
    queries: List[IntelligenceQuery]
    results: List[IntelligenceResult] = field(default_factory=list)
    agent_assignments: Dict[str, str] = field(
        default_factory=dict
    )  # agent_id -> query_id
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    status: str = "running"
    errors: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CreditUsageTracker:
    """Track API credit usage across providers"""

    provider_usage: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    daily_limits: Dict[str, int] = field(default_factory=dict)
    last_reset: datetime = field(default_factory=datetime.now)
    cost_per_request: Dict[str, float] = field(default_factory=dict)

    def reset_if_needed(self):
        """Reset daily usage if day has changed"""
        now = datetime.now()
        if now.date() > self.last_reset.date():
            self.provider_usage.clear()
            self.last_reset = now

    def can_use_provider(self, provider: str) -> bool:
        """Check if provider can be used based on daily limits"""
        self.reset_if_needed()
        if provider in self.daily_limits:
            return self.provider_usage[provider] < self.daily_limits[provider]
        return True

    def record_usage(self, provider: str, cost: float = 1.0):
        """Record usage for a provider"""
        self.reset_if_needed()
        self.provider_usage[provider] += 1
        if provider in self.cost_per_request:
            self.cost_per_request[provider] += cost


class SleuthIntelOrchestrator:
    """
    Advanced Intelligence Orchestrator

    Coordinates multiple intelligence agents with sophisticated workflow patterns,
    load balancing, rate limiting, and result correlation.
    """

    def __init__(
        self,
        config: Optional[WorkflowConfig] = None,
        session_id: Optional[str] = None,
        output_dir: Optional[Path] = None,
    ):
        self.config = config or WorkflowConfig()
        self.session_id = session_id or str(uuid4())
        self.output_dir = output_dir or Path("./sleuth_intel_results")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Component initialization
        self.api_locker = APILockerManager.get_instance()
        self.credit_tracker = CreditUsageTracker()

        # Agent management
        self.agent_pools: Dict[str, AgentPool] = {}
        self.agent_registry: Dict[str, BaseIntelligenceAgent] = {}
        self.agent_status: Dict[str, AgentStatus] = {}
        self._agent_lock = RLock()

        # Workflow execution tracking
        self.active_workflows: Dict[str, WorkflowExecution] = {}
        self.workflow_history: List[WorkflowExecution] = []
        self._workflow_lock = Lock()

        # Rate limiting coordination
        self.global_rate_limiter = self._create_global_rate_limiter()
        self.provider_queues: Dict[str, deque] = defaultdict(deque)
        self._rate_limit_lock = Lock()

        # Result correlation and caching
        self.result_cache: Dict[str, Tuple[Any, datetime]] = {}
        self.correlation_index: Dict[str, Set[str]] = defaultdict(set)
        self._cache_lock = Lock()

        # Chat monitor integration
        self.chat_monitor_integration = OrchestratorIntegration(
            title="Sleuth Intelligence Orchestrator",
            orchestrator_session=self.session_id,
            orchestrator_location=str(self.output_dir),
            focus_areas=["intelligence", "data_gathering", "analysis"],
        )

        # Initialize logging
        self.logger = logging.getLogger(f"{__name__}.{self.session_id[:8]}")
        self.logger.info(
            f"Initialized SleuthIntelOrchestrator with session {self.session_id[:8]}"
        )

    def _create_global_rate_limiter(self) -> RateLimitConfig:
        """Create global rate limiting configuration"""
        return RateLimitConfig(
            requests_per_second=10.0,
            requests_per_minute=500,
            requests_per_hour=5000,
            requests_per_day=50000,
            burst_size=20,
        )

    def register_agent_pool(
        self,
        agent_type: str,
        agent_class: type,
        max_instances: int = 3,
        providers: Optional[List[str]] = None,
    ) -> None:
        """Register an agent pool for a specific intelligence type"""
        with self._agent_lock:
            pool = AgentPool(agent_class=agent_class, max_instances=max_instances)

            # Pre-create instances for different providers
            if providers:
                for provider in providers[:max_instances]:
                    if self.api_locker.get_credential(provider):
                        try:
                            agent = agent_class(
                                provider=provider,
                                agent_name=f"{agent_type}_{provider}_{len(pool.instances)}",
                                rate_limit_config=self.global_rate_limiter,
                            )
                            pool.instances.append(agent)
                            agent_id = f"{agent_type}_{provider}_{len(pool.instances)}"
                            self.agent_registry[agent_id] = agent
                            self.agent_status[agent_id] = AgentStatus.IDLE
                        except Exception as e:
                            self.logger.warning(
                                f"Failed to create {agent_type} agent for {provider}: {e}"
                            )

            self.agent_pools[agent_type] = pool
            self.logger.info(
                f"Registered agent pool '{agent_type}' with {len(pool.instances)} instances"
            )

    def get_optimal_agent(
        self,
        agent_type: str,
        query: IntelligenceQuery,
        exclude_providers: Optional[Set[str]] = None,
    ) -> Optional[BaseIntelligenceAgent]:
        """
        Select optimal agent based on current load, rate limits, and cost
        """
        exclude_providers = exclude_providers or set()

        with self._agent_lock:
            if agent_type not in self.agent_pools:
                self.logger.error(f"No agent pool registered for type: {agent_type}")
                return None

            pool = self.agent_pools[agent_type]
            available_agents = []

            for agent in pool.instances:
                agent_id = next(
                    (aid for aid, a in self.agent_registry.items() if a is agent), None
                )

                if (
                    agent_id
                    and self.agent_status[agent_id] == AgentStatus.IDLE
                    and agent.provider not in exclude_providers
                    and self.credit_tracker.can_use_provider(agent.provider)
                ):
                    # Calculate agent score based on multiple factors
                    metrics = agent.get_metrics()
                    score = self._calculate_agent_score(agent, metrics, query)
                    available_agents.append((agent, score))

            if not available_agents:
                self.logger.warning(f"No available agents for type {agent_type}")
                return None

            # Sort by score (higher is better) and return best agent
            available_agents.sort(key=lambda x: x[1], reverse=True)
            selected_agent = available_agents[0][0]

            # Update status
            agent_id = next(
                (aid for aid, a in self.agent_registry.items() if a is selected_agent)
            )
            if agent_id:
                self.agent_status[agent_id] = AgentStatus.RUNNING

            return selected_agent

    def _calculate_agent_score(
        self,
        agent: BaseIntelligenceAgent,
        metrics: Dict[str, Any],
        query: IntelligenceQuery,
    ) -> float:
        """Calculate agent selection score based on performance and costs"""
        score = 100.0  # Base score

        # Performance factors
        success_rate = metrics.get("success_rate", 0)
        score += success_rate * 0.3

        avg_response_time = metrics.get("average_response_time", 1.0)
        score -= min(avg_response_time * 10, 50)  # Penalize slow agents

        rate_limit_hits = metrics.get("rate_limit_hits", 0)
        score -= rate_limit_hits * 5  # Penalize frequently rate-limited agents

        # Cost optimization
        if self.config.cost_optimization:
            provider_usage = self.credit_tracker.provider_usage.get(agent.provider, 0)
            if provider_usage > 0:
                score -= provider_usage * 0.1  # Prefer less-used providers

        # Provider preferences
        if agent.provider in self.config.preferred_providers:
            score += 20

        return score

    def release_agent(self, agent: BaseIntelligenceAgent) -> None:
        """Release agent back to idle state"""
        with self._agent_lock:
            agent_id = next(
                (aid for aid, a in self.agent_registry.items() if a is agent), None
            )
            if agent_id:
                self.agent_status[agent_id] = AgentStatus.IDLE

    async def execute_workflow(
        self,
        workflow_type: WorkflowType,
        queries: List[IntelligenceQuery],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WorkflowExecution:
        """Execute intelligence workflow with specified pattern"""

        workflow_id = str(uuid4())
        execution = WorkflowExecution(
            workflow_id=workflow_id, workflow_type=workflow_type, queries=queries
        )

        with self._workflow_lock:
            self.active_workflows[workflow_id] = execution

        try:
            self.logger.info(
                f"Starting {workflow_type.value} workflow with {len(queries)} queries"
            )

            # Execute based on workflow type
            if workflow_type == WorkflowType.SINGLE_SOURCE:
                results = await self._execute_single_source(queries)
            elif workflow_type == WorkflowType.MULTI_SOURCE_PARALLEL:
                results = await self._execute_multi_source_parallel(queries)
            elif workflow_type == WorkflowType.INVESTIGATION_CHAIN:
                results = await self._execute_investigation_chain(queries)
            elif workflow_type == WorkflowType.BULK_PROCESSING:
                results = await self._execute_bulk_processing(queries)
            elif workflow_type == WorkflowType.ADAPTIVE_ENRICHMENT:
                results = await self._execute_adaptive_enrichment(queries)
            else:
                raise ValueError(f"Unknown workflow type: {workflow_type}")

            execution.results = results
            execution.end_time = datetime.now()
            execution.status = "completed"

            # Perform result correlation if multiple results
            if len(results) > 1:
                correlation_data = self._correlate_results(results)
                execution.metrics["correlation"] = correlation_data

            # Calculate execution metrics
            execution_time = (execution.end_time - execution.start_time).total_seconds()
            execution.metrics.update(
                {
                    "execution_time_seconds": execution_time,
                    "total_queries": len(queries),
                    "successful_results": len([r for r in results if r.success]),
                    "failed_results": len([r for r in results if not r.success]),
                    "unique_providers_used": len(
                        set(r.provider for r in results if r.provider)
                    ),
                    "cache_hits": len(
                        [r for r in results if getattr(r, "cached", False)]
                    ),
                }
            )

            self.logger.info(
                f"Completed workflow {workflow_id[:8]} in {execution_time:.2f}s"
            )

        except Exception as e:
            execution.end_time = datetime.now()
            execution.status = "failed"
            execution.errors.append(str(e))
            self.logger.error(f"Workflow {workflow_id[:8]} failed: {e}")

        finally:
            with self._workflow_lock:
                if workflow_id in self.active_workflows:
                    self.workflow_history.append(self.active_workflows.pop(workflow_id))

            # Complete chat monitor integration
            self.chat_monitor_integration.complete_run(
                f"Workflow {workflow_type.value} - {execution.status}"
            )

        return execution

    async def _execute_single_source(
        self, queries: List[IntelligenceQuery]
    ) -> List[IntelligenceResult]:
        """Execute queries using single best agent per query type"""
        results = []

        for query in queries:
            agent_type = self._determine_agent_type(query)
            agent = self.get_optimal_agent(agent_type, query)

            if not agent:
                results.append(
                    IntelligenceResult(
                        query=query,
                        success=False,
                        error="No available agents",
                        timestamp=datetime.now(),
                    )
                )
                continue

            try:
                # Register with chat monitor
                self.chat_monitor_integration.add_agent(
                    agent_session_id=agent.agent_name,
                    role=agent_type,
                    location=str(self.output_dir),
                )

                # Execute query
                result = await self._execute_query_with_agent(agent, query)
                results.append(result)

                # Record usage
                self.credit_tracker.record_usage(agent.provider)

            except Exception as e:
                results.append(
                    IntelligenceResult(
                        query=query,
                        success=False,
                        error=str(e),
                        timestamp=datetime.now(),
                    )
                )
                self.logger.error(f"Query execution failed: {e}")
            finally:
                self.release_agent(agent)

        return results

    async def _execute_multi_source_parallel(
        self, queries: List[IntelligenceQuery]
    ) -> List[IntelligenceResult]:
        """Execute queries across multiple providers in parallel"""
        tasks = []

        for query in queries:
            agent_type = self._determine_agent_type(query)

            # Try to get multiple agents from different providers
            agents = []
            used_providers = set()

            for _ in range(
                min(3, len(self.agent_pools.get(agent_type, AgentPool(type)).instances))
            ):
                agent = self.get_optimal_agent(agent_type, query, used_providers)
                if agent:
                    agents.append(agent)
                    used_providers.add(agent.provider)
                else:
                    break

            if not agents:
                # Fallback to single agent
                agent = self.get_optimal_agent(agent_type, query)
                if agent:
                    agents = [agent]

            for agent in agents:
                task = asyncio.create_task(self._execute_query_with_agent(agent, query))
                tasks.append((task, agent, query))

        # Wait for all tasks
        results = []
        for task, agent, query in tasks:
            try:
                result = await task
                results.append(result)
                self.credit_tracker.record_usage(agent.provider)
            except Exception as e:
                results.append(
                    IntelligenceResult(
                        query=query,
                        success=False,
                        error=str(e),
                        timestamp=datetime.now(),
                    )
                )
            finally:
                self.release_agent(agent)

        return results

    async def _execute_investigation_chain(
        self, queries: List[IntelligenceQuery]
    ) -> List[IntelligenceResult]:
        """Execute queries in sequence, using results to inform subsequent queries"""
        results = []
        enriched_queries = list(queries)  # Copy to modify

        for i, query in enumerate(enriched_queries):
            # Enrich query with previous results if applicable
            if i > 0 and results:
                query = self._enrich_query_with_context(
                    query, results[-3:]
                )  # Use last 3 results

            agent_type = self._determine_agent_type(query)
            agent = self.get_optimal_agent(agent_type, query)

            if not agent:
                results.append(
                    IntelligenceResult(
                        query=query,
                        success=False,
                        error="No available agents",
                        timestamp=datetime.now(),
                    )
                )
                continue

            try:
                result = await self._execute_query_with_agent(agent, query)
                results.append(result)

                # If result suggests additional queries, add them to the chain
                additional_queries = self._generate_followup_queries(result)
                if additional_queries:
                    enriched_queries.extend(additional_queries)
                    self.logger.info(
                        f"Added {len(additional_queries)} follow-up queries to chain"
                    )

                self.credit_tracker.record_usage(agent.provider)

            except Exception as e:
                results.append(
                    IntelligenceResult(
                        query=query,
                        success=False,
                        error=str(e),
                        timestamp=datetime.now(),
                    )
                )
            finally:
                self.release_agent(agent)

        return results

    async def _execute_bulk_processing(
        self, queries: List[IntelligenceQuery]
    ) -> List[IntelligenceResult]:
        """Execute large batches of queries with intelligent batching and throttling"""
        results = []
        batch_size = min(self.config.max_parallel_agents * 2, 10)

        # Process queries in batches
        for i in range(0, len(queries), batch_size):
            batch_queries = queries[i : i + batch_size]

            # Create semaphore for batch concurrency control
            semaphore = asyncio.Semaphore(self.config.max_parallel_agents)

            async def process_query_with_semaphore(query):
                async with semaphore:
                    agent_type = self._determine_agent_type(query)
                    agent = self.get_optimal_agent(agent_type, query)

                    if not agent:
                        return IntelligenceResult(
                            query=query,
                            success=False,
                            error="No available agents",
                            timestamp=datetime.now(),
                        )

                    try:
                        result = await self._execute_query_with_agent(agent, query)
                        self.credit_tracker.record_usage(agent.provider)
                        return result
                    except Exception as e:
                        return IntelligenceResult(
                            query=query,
                            success=False,
                            error=str(e),
                            timestamp=datetime.now(),
                        )
                    finally:
                        self.release_agent(agent)

            # Execute batch
            batch_tasks = [process_query_with_semaphore(q) for q in batch_queries]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            # Process results
            for result in batch_results:
                if isinstance(result, Exception):
                    results.append(
                        IntelligenceResult(
                            query=batch_queries[len(results) - i],
                            success=False,
                            error=str(result),
                            timestamp=datetime.now(),
                        )
                    )
                else:
                    results.append(result)

            # Brief pause between batches to respect rate limits
            if i + batch_size < len(queries):
                await asyncio.sleep(1.0)

            self.logger.info(
                f"Completed batch {i//batch_size + 1} of {(len(queries)-1)//batch_size + 1}"
            )

        return results

    async def _execute_adaptive_enrichment(
        self, queries: List[IntelligenceQuery]
    ) -> List[IntelligenceResult]:
        """Adaptively enrich queries based on initial results"""
        initial_results = []

        # First pass: Execute initial queries
        for query in queries:
            agent_type = self._determine_agent_type(query)
            agent = self.get_optimal_agent(agent_type, query)

            if agent:
                try:
                    result = await self._execute_query_with_agent(agent, query)
                    initial_results.append(result)
                    self.credit_tracker.record_usage(agent.provider)
                except Exception as e:
                    initial_results.append(
                        IntelligenceResult(
                            query=query,
                            success=False,
                            error=str(e),
                            timestamp=datetime.now(),
                        )
                    )
                finally:
                    self.release_agent(agent)

        # Second pass: Adaptive enrichment based on initial results
        enrichment_queries = []
        for result in initial_results:
            if result.success and result.data:
                additional_queries = self._generate_enrichment_queries(result)
                enrichment_queries.extend(additional_queries)

        # Execute enrichment queries
        enrichment_results = []
        if enrichment_queries:
            self.logger.info(
                f"Executing {len(enrichment_queries)} adaptive enrichment queries"
            )
            enrichment_results = await self._execute_multi_source_parallel(
                enrichment_queries
            )

        return initial_results + enrichment_results

    async def _execute_query_with_agent(
        self, agent: BaseIntelligenceAgent, query: IntelligenceQuery
    ) -> IntelligenceResult:
        """Execute single query with specific agent"""

        # Check cache first
        cache_key = self._generate_cache_key(agent.provider, query)
        if self.config.enable_caching:
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                self.logger.debug(f"Cache hit for query: {query.query_type}")
                cached_result.cached = True
                return cached_result

        try:
            # Execute query through agent
            start_time = datetime.now()
            raw_result = agent.query(query.to_dict())
            execution_time = (datetime.now() - start_time).total_seconds()

            # Create intelligence result
            result = IntelligenceResult(
                query=query,
                data=raw_result,
                success=True,
                provider=agent.provider,
                agent_name=agent.agent_name,
                timestamp=datetime.now(),
                execution_time_ms=int(execution_time * 1000),
            )

            # Cache successful results
            if self.config.enable_caching and result.success:
                self._cache_result(cache_key, result)

            return result

        except Exception as e:
            return IntelligenceResult(
                query=query,
                success=False,
                error=str(e),
                provider=agent.provider,
                agent_name=agent.agent_name,
                timestamp=datetime.now(),
            )

    def _determine_agent_type(self, query: IntelligenceQuery) -> str:
        """Determine which agent type should handle the query"""
        query_type = query.query_type.lower()

        type_mapping = {
            "person": "person_search",
            "phone": "phone_search",
            "email": "email_search",
            "business": "business_search",
            "address": "address_search",
            "analysis": "analysis",
        }

        for key, agent_type in type_mapping.items():
            if key in query_type:
                return agent_type

        return "person_search"  # Default fallback

    def _enrich_query_with_context(
        self, query: IntelligenceQuery, previous_results: List[IntelligenceResult]
    ) -> IntelligenceQuery:
        """Enrich query with context from previous results"""
        # Extract relevant context from previous results
        context_data = {}
        for result in previous_results:
            if result.success and result.data:
                # Extract useful information for context
                if hasattr(result.data, "get"):
                    for key in [
                        "full_name",
                        "email",
                        "phone",
                        "address",
                        "business_name",
                    ]:
                        if key in result.data:
                            context_data[key] = result.data[key]

        # Create enriched query
        enriched_params = dict(query.parameters)
        enriched_params.update({"context": context_data})

        return IntelligenceQuery(
            query_type=query.query_type,
            parameters=enriched_params,
            priority=query.priority,
        )

    def _generate_followup_queries(
        self, result: IntelligenceResult
    ) -> List[IntelligenceQuery]:
        """Generate follow-up queries based on result data"""
        followup_queries = []

        if not (result.success and result.data):
            return followup_queries

        # Generate follow-ups based on result type and content
        if hasattr(result.data, "get"):
            data = result.data

            # If we found a person, search for related businesses
            if "full_name" in data and result.query.query_type == "person":
                if "business_name" in data:
                    followup_queries.append(
                        IntelligenceQuery(
                            query_type="business",
                            parameters={"business_name": data["business_name"]},
                            priority=result.query.priority,
                        )
                    )

            # If we found a business, search for key personnel
            elif "business_name" in data and result.query.query_type == "business":
                if "executives" in data:
                    for exec_name in data.get("executives", [])[:3]:  # Limit to 3
                        followup_queries.append(
                            IntelligenceQuery(
                                query_type="person",
                                parameters={"full_name": exec_name},
                                priority=result.query.priority,
                            )
                        )

        return followup_queries

    def _generate_enrichment_queries(
        self, result: IntelligenceResult
    ) -> List[IntelligenceQuery]:
        """Generate enrichment queries to expand on result data"""
        enrichment_queries = []

        if not (result.success and result.data):
            return enrichment_queries

        # Similar to follow-up but focused on enrichment
        if hasattr(result.data, "get"):
            data = result.data

            # Enrich person data with additional searches
            if "email" in data and result.query.query_type != "email":
                enrichment_queries.append(
                    IntelligenceQuery(
                        query_type="email",
                        parameters={"email": data["email"]},
                        priority=max(1, result.query.priority - 1),  # Lower priority
                    )
                )

            if "phone" in data and result.query.query_type != "phone":
                enrichment_queries.append(
                    IntelligenceQuery(
                        query_type="phone",
                        parameters={"phone": data["phone"]},
                        priority=max(1, result.query.priority - 1),
                    )
                )

        return enrichment_queries

    def _correlate_results(self, results: List[IntelligenceResult]) -> Dict[str, Any]:
        """Correlate results to find connections and patterns"""
        correlation_data = {
            "connections": [],
            "confidence_scores": {},
            "data_overlap": {},
            "pattern_analysis": {},
        }

        # Find data overlaps between results
        for i, result1 in enumerate(results):
            for j, result2 in enumerate(results[i + 1 :], i + 1):
                if result1.success and result2.success:
                    overlap = self._calculate_data_overlap(result1.data, result2.data)
                    if overlap["score"] > self.config.correlation_threshold:
                        correlation_data["connections"].append(
                            {
                                "result_indices": [i, j],
                                "overlap_score": overlap["score"],
                                "shared_fields": overlap["fields"],
                                "confidence": overlap["confidence"],
                            }
                        )

        return correlation_data

    def _calculate_data_overlap(self, data1: Any, data2: Any) -> Dict[str, Any]:
        """Calculate overlap score between two data results"""
        if not (hasattr(data1, "get") and hasattr(data2, "get")):
            return {"score": 0.0, "fields": [], "confidence": 0.0}

        shared_fields = []
        total_fields = set(list(data1.keys()) + list(data2.keys()))

        for field in total_fields:
            if field in data1 and field in data2:
                if data1[field] == data2[field]:
                    shared_fields.append(field)

        score = len(shared_fields) / len(total_fields) if total_fields else 0.0
        confidence = min(score * 2, 1.0)  # Simple confidence calculation

        return {"score": score, "fields": shared_fields, "confidence": confidence}

    def _generate_cache_key(self, provider: str, query: IntelligenceQuery) -> str:
        """Generate cache key for query result"""
        import hashlib

        key_data = (
            f"{provider}_{query.query_type}_{str(sorted(query.parameters.items()))}"
        )
        return hashlib.sha256(key_data.encode()).hexdigest()

    def _get_cached_result(self, cache_key: str) -> Optional[IntelligenceResult]:
        """Get cached result if valid"""
        with self._cache_lock:
            if cache_key in self.result_cache:
                result, timestamp = self.result_cache[cache_key]
                if datetime.now() - timestamp < timedelta(
                    seconds=self.config.cache_ttl
                ):
                    return result
                else:
                    del self.result_cache[cache_key]
        return None

    def _cache_result(self, cache_key: str, result: IntelligenceResult) -> None:
        """Cache result with TTL"""
        with self._cache_lock:
            self.result_cache[cache_key] = (result, datetime.now())

            # Simple cache size management
            if len(self.result_cache) > 1000:
                # Remove oldest entries
                sorted_cache = sorted(self.result_cache.items(), key=lambda x: x[1][1])
                for key, _ in sorted_cache[:100]:
                    del self.result_cache[key]

    def get_workflow_metrics(self, workflow_id: Optional[str] = None) -> Dict[str, Any]:
        """Get metrics for specific workflow or all workflows"""
        with self._workflow_lock:
            if workflow_id:
                if workflow_id in self.active_workflows:
                    return self.active_workflows[workflow_id].metrics

                for execution in self.workflow_history:
                    if execution.workflow_id == workflow_id:
                        return execution.metrics

                return {}

            # Return aggregate metrics
            total_executions = len(self.workflow_history)
            if not total_executions:
                return {"total_executions": 0}

            successful_executions = len(
                [e for e in self.workflow_history if e.status == "completed"]
            )
            total_execution_time = sum(
                e.metrics.get("execution_time_seconds", 0)
                for e in self.workflow_history
            )

            return {
                "total_executions": total_executions,
                "successful_executions": successful_executions,
                "success_rate": successful_executions / total_executions * 100,
                "average_execution_time": total_execution_time / total_executions,
                "total_queries_processed": sum(
                    e.metrics.get("total_queries", 0) for e in self.workflow_history
                ),
                "cache_hit_rate": sum(
                    e.metrics.get("cache_hits", 0) for e in self.workflow_history
                )
                / max(
                    1,
                    sum(
                        e.metrics.get("total_queries", 0) for e in self.workflow_history
                    ),
                )
                * 100,
                "provider_usage": dict(self.credit_tracker.provider_usage),
            }

    def get_agent_status_summary(self) -> Dict[str, Any]:
        """Get summary of all agent statuses"""
        with self._agent_lock:
            status_counts = defaultdict(int)
            for status in self.agent_status.values():
                status_counts[status.value] += 1

            agent_metrics = {}
            for agent_id, agent in self.agent_registry.items():
                agent_metrics[agent_id] = agent.get_metrics()

            return {
                "total_agents": len(self.agent_registry),
                "status_distribution": dict(status_counts),
                "agent_pools": {
                    pool_name: {
                        "instances": len(pool.instances),
                        "max_instances": pool.max_instances,
                        "current_load": pool.current_load,
                    }
                    for pool_name, pool in self.agent_pools.items()
                },
                "individual_metrics": agent_metrics,
            }

    def reset_all_metrics(self) -> None:
        """Reset all metrics and caches"""
        with self._workflow_lock:
            self.workflow_history.clear()

        with self._cache_lock:
            self.result_cache.clear()

        with self._agent_lock:
            for agent in self.agent_registry.values():
                agent.reset_metrics()

        self.credit_tracker = CreditUsageTracker()
        self.logger.info("All metrics and caches reset")

    def shutdown(self) -> None:
        """Gracefully shutdown orchestrator"""
        self.logger.info("Shutting down SleuthIntelOrchestrator")

        # Complete any active workflows
        with self._workflow_lock:
            for workflow_id, execution in self.active_workflows.items():
                execution.status = "interrupted"
                execution.end_time = datetime.now()
                self.workflow_history.append(execution)
            self.active_workflows.clear()

        # Complete chat monitor integration
        self.chat_monitor_integration.complete_run("Orchestrator shutdown")

        self.logger.info("Orchestrator shutdown complete")
