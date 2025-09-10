"""Implementation strategy and orchestration for Git history adapter integration."""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

import structlog

from .adapters.enhanced_git_adapter import EnhancedGitAdapter, ProcessingStatus
from .base_adapter import AdapterConfig
from .monitoring import AdapterMonitoring

logger = structlog.get_logger(__name__)


class IntegrationPhase(Enum):
    """Git integration phases."""

    INITIALIZATION = "initialization"
    SCHEMA_VALIDATION = "schema_validation"
    INCREMENTAL_SETUP = "incremental_setup"
    BULK_INGESTION = "bulk_ingestion"
    REAL_TIME_PROCESSING = "real_time_processing"
    OPTIMIZATION = "optimization"
    MONITORING = "monitoring"


class ErrorRecoveryStrategy(Enum):
    """Error recovery strategies."""

    RETRY_EXPONENTIAL_BACKOFF = "retry_exponential_backoff"
    SKIP_AND_CONTINUE = "skip_and_continue"
    FALLBACK_TO_SIMPLE = "fallback_to_simple"
    PAUSE_AND_ALERT = "pause_and_alert"
    GRACEFUL_DEGRADATION = "graceful_degradation"


@dataclass
class IntegrationConfig:
    """Configuration for Git adapter integration."""

    # Repository settings
    repository_paths: List[str] = field(default_factory=list)
    primary_branches: List[str] = field(
        default_factory=lambda: ["main", "master", "develop"]
    )
    max_commit_age_days: Optional[int] = None

    # Processing configuration
    enable_incremental: bool = True
    enable_parallel_processing: bool = True
    max_parallel_repositories: int = 3
    max_parallel_branches: int = 5
    batch_size: int = 500
    checkpoint_interval: int = 100

    # Analysis configuration
    enable_semantic_analysis: bool = True
    enable_impact_scoring: bool = True
    enable_relationship_detection: bool = True
    enable_branch_topology: bool = True
    enable_merge_analysis: bool = True

    # Error handling configuration
    max_retries: int = 3
    retry_delay_base_seconds: float = 2.0
    retry_backoff_factor: float = 2.0
    error_threshold_per_hour: int = 50
    circuit_breaker_threshold: int = 10

    # Performance configuration
    memory_limit_mb: int = 2048
    processing_timeout_minutes: int = 60
    query_timeout_seconds: int = 30

    # Integration configuration
    correlate_with_chat: bool = True
    correlate_with_errors: bool = True
    temporal_correlation_window_hours: int = 48

    # Monitoring configuration
    enable_detailed_monitoring: bool = True
    monitoring_interval_seconds: int = 60
    performance_alert_threshold: float = 0.8


@dataclass
class ProcessingMetrics:
    """Processing metrics for monitoring."""

    phase: IntegrationPhase
    repositories_processed: int = 0
    total_repositories: int = 0
    commits_processed: int = 0
    commits_failed: int = 0
    branches_processed: int = 0
    processing_rate_per_second: float = 0.0
    current_memory_usage_mb: float = 0.0
    errors_last_hour: int = 0
    last_checkpoint_time: Optional[datetime] = None
    estimated_completion_time: Optional[datetime] = None


class GitIntegrationOrchestrator:
    """Orchestrates the complete Git history adapter integration."""

    def __init__(self, config: IntegrationConfig, database_connection):
        self.config = config
        self.db = database_connection
        self.logger = logger.bind(component="GitIntegrationOrchestrator")

        # State tracking
        self.current_phase = IntegrationPhase.INITIALIZATION
        self.processing_state: Dict[str, Any] = {}
        self.error_counts: Dict[str, int] = {}
        self.circuit_breakers: Dict[str, bool] = {}

        # Components
        self.adapters: Dict[str, EnhancedGitAdapter] = {}
        self.monitoring = AdapterMonitoring()

        # Metrics
        self.metrics = ProcessingMetrics(phase=IntegrationPhase.INITIALIZATION)

        # Error recovery
        self.error_recovery_strategies: Dict[str, ErrorRecoveryStrategy] = {
            "connection_error": ErrorRecoveryStrategy.RETRY_EXPONENTIAL_BACKOFF,
            "memory_error": ErrorRecoveryStrategy.GRACEFUL_DEGRADATION,
            "timeout_error": ErrorRecoveryStrategy.SKIP_AND_CONTINUE,
            "parse_error": ErrorRecoveryStrategy.SKIP_AND_CONTINUE,
            "critical_error": ErrorRecoveryStrategy.PAUSE_AND_ALERT,
        }

    async def execute_integration(self) -> bool:
        """Execute the complete Git integration strategy."""
        try:
            self.logger.info("Starting Git history adapter integration")

            # Phase 1: Initialization
            success = await self._execute_initialization_phase()
            if not success:
                return False

            # Phase 2: Schema Validation
            success = await self._execute_schema_validation_phase()
            if not success:
                return False

            # Phase 3: Incremental Setup
            success = await self._execute_incremental_setup_phase()
            if not success:
                return False

            # Phase 4: Bulk Ingestion
            success = await self._execute_bulk_ingestion_phase()
            if not success:
                return False

            # Phase 5: Real-time Processing Setup
            success = await self._execute_real_time_setup_phase()
            if not success:
                return False

            # Phase 6: Optimization
            success = await self._execute_optimization_phase()
            if not success:
                return False

            # Phase 7: Monitoring Setup
            success = await self._execute_monitoring_phase()
            if not success:
                return False

            self.logger.info("Git history adapter integration completed successfully")
            return True

        except Exception as e:
            await self._handle_critical_error("integration_failure", e)
            return False

    async def _execute_initialization_phase(self) -> bool:
        """Phase 1: Initialize components and validate configuration."""
        self.current_phase = IntegrationPhase.INITIALIZATION
        self.metrics.phase = IntegrationPhase.INITIALIZATION

        try:
            self.logger.info("Executing initialization phase")

            # Validate repository paths
            valid_repos = await self._validate_repositories()
            if not valid_repos:
                raise ValueError("No valid repositories found")

            # Initialize adapters for each repository
            for repo_path in valid_repos:
                adapter_config = self._create_adapter_config(repo_path)
                adapter = EnhancedGitAdapter(adapter_config, self.db)

                try:
                    await adapter.initialize()
                    self.adapters[repo_path] = adapter
                    self.logger.info("Adapter initialized", repo_path=repo_path)
                except Exception as e:
                    await self._handle_adapter_error(
                        repo_path, "initialization_error", e
                    )
                    continue

            if not self.adapters:
                raise ValueError("No adapters successfully initialized")

            self.metrics.total_repositories = len(self.adapters)
            self.logger.info(
                "Initialization phase completed", adapters_created=len(self.adapters)
            )
            return True

        except Exception as e:
            await self._handle_critical_error("initialization_failure", e)
            return False

    async def _execute_schema_validation_phase(self) -> bool:
        """Phase 2: Validate database schema and create missing components."""
        self.current_phase = IntegrationPhase.SCHEMA_VALIDATION
        self.metrics.phase = IntegrationPhase.SCHEMA_VALIDATION

        try:
            self.logger.info("Executing schema validation phase")

            # Check for required tables
            required_tables = [
                "git_processing_checkpoints",
                "git_commit_relationships",
                "git_file_impacts",
                "git_branches",
                "git_merge_analysis",
                "git_author_statistics",
            ]

            for table in required_tables:
                exists = await self._check_table_exists(table)
                if not exists:
                    self.logger.error("Required table missing", table=table)
                    return False

            # Validate git-specific indexes
            git_indexes = await self._validate_git_indexes()
            if not git_indexes:
                self.logger.warning(
                    "Some git indexes missing, performance may be impacted"
                )

            # Test git-specific functions
            functions_valid = await self._test_git_functions()
            if not functions_valid:
                self.logger.error(
                    "Git-specific database functions not working properly"
                )
                return False

            self.logger.info("Schema validation phase completed")
            return True

        except Exception as e:
            await self._handle_critical_error("schema_validation_failure", e)
            return False

    async def _execute_incremental_setup_phase(self) -> bool:
        """Phase 3: Set up incremental processing checkpoints."""
        self.current_phase = IntegrationPhase.INCREMENTAL_SETUP
        self.metrics.phase = IntegrationPhase.INCREMENTAL_SETUP

        try:
            self.logger.info("Executing incremental setup phase")

            if not self.config.enable_incremental:
                self.logger.info("Incremental processing disabled, skipping setup")
                return True

            # Initialize checkpoints for each repository
            for repo_path, adapter in self.adapters.items():
                try:
                    # Get existing checkpoints
                    branches = await self._get_repository_branches(repo_path)

                    for branch in branches:
                        checkpoint = (
                            await adapter.checkpoint_manager.get_processing_state(
                                branch
                            )
                        )
                        if not checkpoint:
                            # Create initial checkpoint
                            await self._create_initial_checkpoint(
                                repo_path, branch, adapter
                            )
                        else:
                            self.logger.info(
                                "Existing checkpoint found",
                                repo=repo_path,
                                branch=branch,
                                last_commit=checkpoint.last_processed_commit[:8],
                            )

                    self.logger.info(
                        "Incremental setup completed for repository",
                        repo_path=repo_path,
                    )

                except Exception as e:
                    await self._handle_adapter_error(
                        repo_path, "checkpoint_setup_error", e
                    )
                    continue

            self.logger.info("Incremental setup phase completed")
            return True

        except Exception as e:
            await self._handle_critical_error("incremental_setup_failure", e)
            return False

    async def _execute_bulk_ingestion_phase(self) -> bool:
        """Phase 4: Execute bulk ingestion of git history."""
        self.current_phase = IntegrationPhase.BULK_INGESTION
        self.metrics.phase = IntegrationPhase.BULK_INGESTION

        try:
            self.logger.info("Executing bulk ingestion phase")

            if self.config.enable_parallel_processing:
                success = await self._execute_parallel_bulk_ingestion()
            else:
                success = await self._execute_sequential_bulk_ingestion()

            if not success:
                self.logger.error("Bulk ingestion phase failed")
                return False

            # Validate ingestion results
            validation_success = await self._validate_ingestion_results()
            if not validation_success:
                self.logger.warning("Ingestion validation found issues, but continuing")

            self.logger.info(
                "Bulk ingestion phase completed",
                commits_processed=self.metrics.commits_processed,
                commits_failed=self.metrics.commits_failed,
            )
            return True

        except Exception as e:
            await self._handle_critical_error("bulk_ingestion_failure", e)
            return False

    async def _execute_parallel_bulk_ingestion(self) -> bool:
        """Execute bulk ingestion with parallel processing."""
        try:
            # Create semaphore for controlling concurrency
            repo_semaphore = asyncio.Semaphore(self.config.max_parallel_repositories)

            # Process repositories in parallel
            tasks = []
            for repo_path, adapter in self.adapters.items():
                task = asyncio.create_task(
                    self._process_repository_with_semaphore(
                        repo_semaphore, repo_path, adapter
                    )
                )
                tasks.append(task)

            # Wait for all repositories to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Check results
            successful_repos = 0
            for i, result in enumerate(results):
                repo_path = list(self.adapters.keys())[i]

                if isinstance(result, Exception):
                    await self._handle_adapter_error(
                        repo_path, "bulk_processing_error", result
                    )
                elif result:
                    successful_repos += 1
                    self.logger.info(
                        "Repository processing completed", repo_path=repo_path
                    )
                else:
                    self.logger.error(
                        "Repository processing failed", repo_path=repo_path
                    )

            return successful_repos > 0

        except Exception as e:
            self.logger.error("Parallel bulk ingestion failed", error=str(e))
            return False

    async def _process_repository_with_semaphore(
        self, semaphore: asyncio.Semaphore, repo_path: str, adapter: EnhancedGitAdapter
    ) -> bool:
        """Process a repository with semaphore control."""
        async with semaphore:
            return await self._process_single_repository(repo_path, adapter)

    async def _process_single_repository(
        self, repo_path: str, adapter: EnhancedGitAdapter
    ) -> bool:
        """Process a single repository for bulk ingestion."""
        try:
            self.logger.info("Starting repository processing", repo_path=repo_path)

            # Get branches to process
            branches = await self._get_repository_branches(repo_path)
            processed_branches = 0

            # Process branches
            for branch in branches:
                try:
                    branch_success = await self._process_branch(
                        repo_path, branch, adapter
                    )
                    if branch_success:
                        processed_branches += 1
                        self.metrics.branches_processed += 1

                    # Check memory usage and circuit breakers
                    if not await self._check_processing_health(repo_path):
                        self.logger.warning(
                            "Processing health check failed, pausing",
                            repo_path=repo_path,
                        )
                        break

                except Exception as e:
                    await self._handle_adapter_error(
                        repo_path, f"branch_processing_error_{branch}", e
                    )
                    continue

            # Update repository processing metrics
            self.metrics.repositories_processed += 1

            success_ratio = processed_branches / len(branches) if branches else 0
            return (
                success_ratio >= 0.5
            )  # Consider successful if at least 50% of branches processed

        except Exception as e:
            await self._handle_adapter_error(
                repo_path, "repository_processing_error", e
            )
            return False

    async def _process_branch(
        self, repo_path: str, branch: str, adapter: EnhancedGitAdapter
    ) -> bool:
        """Process a single branch."""
        try:
            processed_count = 0
            error_count = 0

            # Fetch and process commits
            async for raw_item in adapter.fetch_items(limit=self.config.batch_size):
                try:
                    # Transform item
                    context_item = await adapter.transform_item(raw_item)

                    # Store in database (this would be handled by the pipeline)
                    # For now, we just count successful transformations
                    processed_count += 1
                    self.metrics.commits_processed += 1

                    # Update processing rate
                    await self._update_processing_metrics()

                    # Check if we should save a checkpoint
                    if processed_count % self.config.checkpoint_interval == 0:
                        await self._save_processing_checkpoint(
                            repo_path, branch, raw_item, adapter
                        )

                except Exception as e:
                    error_count += 1
                    self.metrics.commits_failed += 1
                    await self._handle_item_processing_error(
                        repo_path, branch, raw_item, e
                    )

                    # Check error threshold
                    if error_count > self.config.circuit_breaker_threshold:
                        self.logger.error(
                            "Error threshold exceeded for branch",
                            repo_path=repo_path,
                            branch=branch,
                            errors=error_count,
                        )
                        return False

            self.logger.info(
                "Branch processing completed",
                repo_path=repo_path,
                branch=branch,
                processed=processed_count,
                errors=error_count,
            )
            return processed_count > 0

        except Exception as e:
            await self._handle_adapter_error(
                repo_path, f"branch_processing_error_{branch}", e
            )
            return False

    # Error Handling Methods

    async def _handle_critical_error(self, error_type: str, exception: Exception):
        """Handle critical errors that stop the entire process."""
        self.logger.error(
            "Critical error occurred",
            error_type=error_type,
            error=str(exception),
            phase=self.current_phase.value,
        )

        # Update error metrics
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1

        # Execute error recovery strategy
        strategy = self.error_recovery_strategies.get(
            error_type, ErrorRecoveryStrategy.PAUSE_AND_ALERT
        )
        await self._execute_error_recovery_strategy(error_type, exception, strategy)

    async def _handle_adapter_error(
        self, repo_path: str, error_type: str, exception: Exception
    ):
        """Handle adapter-specific errors."""
        self.logger.error(
            "Adapter error occurred",
            repo_path=repo_path,
            error_type=error_type,
            error=str(exception),
        )

        # Update error metrics
        error_key = f"{repo_path}_{error_type}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1

        # Check if we should open circuit breaker
        if self.error_counts[error_key] >= self.config.circuit_breaker_threshold:
            self.circuit_breakers[repo_path] = True
            self.logger.warning(
                "Circuit breaker opened for repository", repo_path=repo_path
            )

    async def _handle_item_processing_error(
        self,
        repo_path: str,
        branch: str,
        raw_item: Dict[str, Any],
        exception: Exception,
    ):
        """Handle individual item processing errors."""
        item_id = raw_item.get("hash", "unknown")

        self.logger.warning(
            "Item processing error",
            repo_path=repo_path,
            branch=branch,
            item_id=item_id,
            error=str(exception),
        )

        # For item-level errors, we typically skip and continue
        # but log for analysis

    async def _execute_error_recovery_strategy(
        self, error_type: str, exception: Exception, strategy: ErrorRecoveryStrategy
    ):
        """Execute the specified error recovery strategy."""
        if strategy == ErrorRecoveryStrategy.RETRY_EXPONENTIAL_BACKOFF:
            await self._retry_with_exponential_backoff(error_type)
        elif strategy == ErrorRecoveryStrategy.GRACEFUL_DEGRADATION:
            await self._enable_graceful_degradation()
        elif strategy == ErrorRecoveryStrategy.PAUSE_AND_ALERT:
            await self._pause_and_alert(error_type, exception)
        # Add other recovery strategies as needed

    async def _retry_with_exponential_backoff(self, error_type: str):
        """Implement exponential backoff retry."""
        retry_count = self.error_counts.get(f"{error_type}_retries", 0)
        if retry_count < self.config.max_retries:
            delay = self.config.retry_delay_base_seconds * (
                self.config.retry_backoff_factor**retry_count
            )
            self.logger.info(
                "Retrying after exponential backoff",
                error_type=error_type,
                retry_count=retry_count,
                delay=delay,
            )
            await asyncio.sleep(delay)
            self.error_counts[f"{error_type}_retries"] = retry_count + 1

    async def _enable_graceful_degradation(self):
        """Enable graceful degradation mode."""
        self.logger.warning("Enabling graceful degradation mode")

        # Reduce batch sizes
        self.config.batch_size = max(self.config.batch_size // 2, 50)

        # Disable resource-intensive features
        self.config.enable_semantic_analysis = False
        self.config.enable_relationship_detection = False

        # Reduce parallelism
        self.config.max_parallel_repositories = 1
        self.config.max_parallel_branches = 1

    async def _pause_and_alert(self, error_type: str, exception: Exception):
        """Pause processing and send alerts."""
        self.logger.critical(
            "Pausing processing due to critical error",
            error_type=error_type,
            error=str(exception),
        )

        # In a real implementation, this would send alerts to monitoring systems
        # For now, we just log

        # Pause all adapters
        for adapter in self.adapters.values():
            await adapter.pause()

    # Helper Methods

    async def _validate_repositories(self) -> List[str]:
        """Validate that repository paths are accessible git repositories."""
        valid_repos = []

        for repo_path in self.config.repository_paths:
            try:
                # Basic validation - in real implementation, would use git commands
                # For now, just check if path exists
                valid_repos.append(repo_path)
            except Exception as e:
                self.logger.warning(
                    "Invalid repository path", repo_path=repo_path, error=str(e)
                )

        return valid_repos

    def _create_adapter_config(self, repo_path: str) -> AdapterConfig:
        """Create adapter configuration for a specific repository."""
        return EnhancedGitAdapter.default_config()

    async def _check_table_exists(self, table_name: str) -> bool:
        """Check if a database table exists."""
        try:
            query = """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_name = %s
                );
            """
            result = await self.db.fetchrow(query, table_name)
            return result["exists"] if result else False
        except Exception:
            return False

    async def _validate_git_indexes(self) -> bool:
        """Validate git-specific database indexes."""
        # Implementation would check for specific git indexes
        return True

    async def _test_git_functions(self) -> bool:
        """Test git-specific database functions."""
        try:
            # Test search_git_history function
            query = "SELECT search_git_history('test') LIMIT 1"
            await self.db.fetchrow(query)
            return True
        except Exception:
            return False

    async def _get_repository_branches(self, repo_path: str) -> List[str]:
        """Get list of branches for a repository."""
        # In real implementation, would use git commands
        return self.config.primary_branches

    async def _create_initial_checkpoint(
        self, repo_path: str, branch: str, adapter: EnhancedGitAdapter
    ):
        """Create initial checkpoint for a branch."""
        # Implementation would create the initial checkpoint
        pass

    async def _check_processing_health(self, repo_path: str) -> bool:
        """Check processing health metrics."""
        # Check circuit breakers
        if self.circuit_breakers.get(repo_path, False):
            return False

        # Check memory usage
        if self.metrics.current_memory_usage_mb > self.config.memory_limit_mb:
            self.logger.warning(
                "Memory limit approaching",
                current=self.metrics.current_memory_usage_mb,
                limit=self.config.memory_limit_mb,
            )
            return False

        return True

    async def _update_processing_metrics(self):
        """Update processing rate and other metrics."""
        # Implementation would calculate actual processing rates
        pass

    async def _save_processing_checkpoint(
        self,
        repo_path: str,
        branch: str,
        raw_item: Dict[str, Any],
        adapter: EnhancedGitAdapter,
    ):
        """Save processing checkpoint."""
        commit_hash = raw_item.get("hash", "")
        if commit_hash:
            timestamp = (
                datetime.utcnow()
            )  # In real implementation, use commit timestamp
            await adapter.checkpoint_manager.save_checkpoint(
                branch, commit_hash, timestamp
            )

    # Additional phase implementations would go here...
    async def _execute_sequential_bulk_ingestion(self) -> bool:
        """Execute sequential bulk ingestion."""
        # Implementation for sequential processing
        return True

    async def _validate_ingestion_results(self) -> bool:
        """Validate ingestion results."""
        # Implementation would validate the ingested data
        return True

    async def _execute_real_time_setup_phase(self) -> bool:
        """Phase 5: Set up real-time processing."""
        self.current_phase = IntegrationPhase.REAL_TIME_PROCESSING
        # Implementation would set up webhooks or polling for new commits
        return True

    async def _execute_optimization_phase(self) -> bool:
        """Phase 6: Optimize performance and indexes."""
        self.current_phase = IntegrationPhase.OPTIMIZATION
        # Implementation would run ANALYZE, create additional indexes, etc.
        return True

    async def _execute_monitoring_phase(self) -> bool:
        """Phase 7: Set up monitoring and alerting."""
        self.current_phase = IntegrationPhase.MONITORING
        # Implementation would set up monitoring dashboards and alerts
        return True
