"""
Provider Manager - Integration layer between ProviderConnectionPool and Orchestrator
Manages provider selection, load balancing, and fallback strategies
"""

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from .connection_pool import ProviderConnectionPool, ProviderType, RetryConfig
from .openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


class ProviderStrategy(Enum):
    """Provider selection strategies"""

    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    FAILOVER = "failover"
    COST_OPTIMIZED = "cost_optimized"
    PERFORMANCE_OPTIMIZED = "performance_optimized"


@dataclass
class ProviderCapabilities:
    """Provider capability definitions"""

    max_tokens: int
    supports_streaming: bool
    supports_functions: bool
    supports_vision: bool
    cost_per_1k_tokens: float
    average_latency: float
    models: List[str]


class ProviderManager:
    """
    Unified provider management with connection pooling
    Integrates with existing orchestrator patterns
    """

    # Provider capabilities registry
    PROVIDER_CAPABILITIES = {
        ProviderType.CLAUDE: ProviderCapabilities(
            max_tokens=200000,
            supports_streaming=True,
            supports_functions=False,
            supports_vision=True,
            cost_per_1k_tokens=0.015,
            average_latency=1.2,
            models=["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
        ),
        ProviderType.OPENAI: ProviderCapabilities(
            max_tokens=128000,
            supports_streaming=True,
            supports_functions=True,
            supports_vision=True,
            cost_per_1k_tokens=0.01,
            average_latency=0.8,
            models=["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
        ),
    }

    def __init__(
        self,
        strategy: ProviderStrategy = ProviderStrategy.LEAST_LOADED,
        enable_fallback: bool = True,
        pool_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize provider manager

        Args:
            strategy: Provider selection strategy
            enable_fallback: Enable automatic fallback to other providers
            pool_config: Configuration for connection pool
        """
        self.strategy = strategy
        self.enable_fallback = enable_fallback

        # Initialize connection pool
        pool_config = pool_config or {}
        self.pool = ProviderConnectionPool(
            max_connections_per_provider=pool_config.get("max_connections", 10),
            keepalive_timeout=pool_config.get("keepalive_timeout", 300),
            retry_config=RetryConfig(
                max_retries=pool_config.get("max_retries", 3),
                initial_delay=pool_config.get("retry_delay", 1.0),
            ),
            health_check_interval=pool_config.get("health_check_interval", 60),
        )

        # Legacy OpenAI provider for backward compatibility
        self.openai_provider = OpenAIProvider()

        # Provider usage tracking
        self.provider_usage = {
            ProviderType.CLAUDE: 0,
            ProviderType.OPENAI: 0,
        }

        # Round-robin index
        self.round_robin_index = 0

        # Provider priority for fallback
        self.provider_priority = [ProviderType.CLAUDE, ProviderType.OPENAI]

    async def start(self):
        """Start the provider manager and connection pool"""
        await self.pool.start()
        logger.info(f"ProviderManager started with strategy: {self.strategy.value}")

    async def stop(self):
        """Stop the provider manager and cleanup"""
        await self.pool.stop()
        logger.info("ProviderManager stopped")

    def select_provider(
        self,
        task_type: Optional[str] = None,
        requirements: Optional[Dict[str, Any]] = None,
    ) -> ProviderType:
        """
        Select optimal provider based on strategy and requirements

        Args:
            task_type: Type of task to execute
            requirements: Specific requirements (e.g., max_tokens, vision)

        Returns:
            Selected provider type
        """
        requirements = requirements or {}
        available_providers = self._get_available_providers(requirements)

        if not available_providers:
            raise ValueError("No providers available matching requirements")

        if self.strategy == ProviderStrategy.ROUND_ROBIN:
            provider = available_providers[
                self.round_robin_index % len(available_providers)
            ]
            self.round_robin_index += 1
            return provider

        elif self.strategy == ProviderStrategy.LEAST_LOADED:
            # Select provider with least usage
            return min(available_providers, key=lambda p: self.provider_usage.get(p, 0))

        elif self.strategy == ProviderStrategy.COST_OPTIMIZED:
            # Select cheapest provider
            return min(
                available_providers,
                key=lambda p: self.PROVIDER_CAPABILITIES[p].cost_per_1k_tokens,
            )

        elif self.strategy == ProviderStrategy.PERFORMANCE_OPTIMIZED:
            # Select fastest provider
            return min(
                available_providers,
                key=lambda p: self.PROVIDER_CAPABILITIES[p].average_latency,
            )

        else:  # FAILOVER
            # Use first available in priority order
            for provider in self.provider_priority:
                if provider in available_providers:
                    return provider
            return available_providers[0]

    def _get_available_providers(
        self, requirements: Dict[str, Any]
    ) -> List[ProviderType]:
        """Get providers that meet requirements"""
        available = []

        for provider_type, capabilities in self.PROVIDER_CAPABILITIES.items():
            # Check requirements
            if requirements.get("max_tokens", 0) > capabilities.max_tokens:
                continue
            if requirements.get("vision") and not capabilities.supports_vision:
                continue
            if requirements.get("functions") and not capabilities.supports_functions:
                continue
            if requirements.get("streaming") and not capabilities.supports_streaming:
                continue

            available.append(provider_type)

        return available

    async def execute_task(
        self, task: Any, provider_type: Optional[ProviderType] = None, **kwargs
    ) -> Dict[str, Any]:
        """
        Execute task with automatic provider selection and fallback

        Args:
            task: Task to execute
            provider_type: Optional specific provider to use
            **kwargs: Additional execution parameters

        Returns:
            Execution result with provider metadata
        """
        # Select provider if not specified
        if not provider_type:
            provider_type = self.select_provider(
                task_type=getattr(task, "task_type", None),
                requirements=kwargs.get("requirements", {}),
            )

        providers_to_try = [provider_type]
        if self.enable_fallback:
            # Add other providers for fallback
            providers_to_try.extend([p for p in ProviderType if p != provider_type])

        last_error = None
        for provider in providers_to_try:
            try:
                logger.info(f"Executing task with provider: {provider.value}")

                # Update usage tracking
                self.provider_usage[provider] += 1

                # Execute based on provider
                if provider == ProviderType.CLAUDE:
                    result = await self._execute_claude_task(task, **kwargs)
                elif provider == ProviderType.OPENAI:
                    result = await self._execute_openai_task(task, **kwargs)
                else:
                    raise ValueError(f"Unsupported provider: {provider}")

                # Add provider metadata
                result["provider_used"] = provider.value
                result["provider_capabilities"] = {
                    "max_tokens": self.PROVIDER_CAPABILITIES[provider].max_tokens,
                    "supports_vision": self.PROVIDER_CAPABILITIES[
                        provider
                    ].supports_vision,
                }

                return result

            except Exception as e:
                last_error = e
                logger.warning(f"Failed to execute with {provider.value}: {e}")
                if not self.enable_fallback:
                    raise
                continue

        # All providers failed
        raise last_error or Exception("All providers failed")

    async def _execute_claude_task(self, task: Any, **kwargs) -> Dict[str, Any]:
        """Execute task using Claude API via connection pool"""

        # Prepare request data
        messages = kwargs.get("messages", [])
        if not messages and hasattr(task, "prompt"):
            messages = [{"role": "user", "content": task.prompt}]

        data = {
            "model": kwargs.get("model", "claude-3-opus-20240229"),
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 4000),
            "temperature": kwargs.get("temperature", 0.1),
        }

        # Add system prompt if provided
        if hasattr(task, "system_prompt") and task.system_prompt:
            data["system"] = task.system_prompt

        # Execute via connection pool
        response = await self.pool.execute_claude_request("/messages", data)

        return {
            "status": "completed",
            "result": response.get("content", [{}])[0].get("text", ""),
            "usage": response.get("usage", {}),
            "model_used": data["model"],
        }

    async def _execute_openai_task(self, task: Any, **kwargs) -> Dict[str, Any]:
        """Execute task using OpenAI API via connection pool"""

        # Prepare request data
        messages = kwargs.get("messages", [])
        if not messages and hasattr(task, "prompt"):
            messages = [
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": task.prompt},
            ]

        # Add system prompt if provided
        if hasattr(task, "system_prompt") and task.system_prompt:
            messages[0] = {"role": "system", "content": task.system_prompt}

        data = {
            "model": kwargs.get("model", "gpt-4"),
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 4000),
            "temperature": kwargs.get("temperature", 0.1),
        }

        # Execute via connection pool
        response = await self.pool.execute_openai_request("/chat/completions", data)

        return {
            "status": "completed",
            "result": response["choices"][0]["message"]["content"],
            "usage": response.get("usage", {}),
            "model_used": data["model"],
        }

    async def get_status(self) -> Dict[str, Any]:
        """Get comprehensive provider status"""
        pool_status = await self.pool.get_pool_status()

        return {
            "strategy": self.strategy.value,
            "fallback_enabled": self.enable_fallback,
            "provider_usage": self.provider_usage,
            "pool_status": pool_status,
            "available_providers": [
                {
                    "type": provider.value,
                    "capabilities": {
                        "max_tokens": cap.max_tokens,
                        "supports_streaming": cap.supports_streaming,
                        "supports_functions": cap.supports_functions,
                        "supports_vision": cap.supports_vision,
                        "cost_per_1k_tokens": cap.cost_per_1k_tokens,
                        "average_latency": cap.average_latency,
                        "models": cap.models,
                    },
                }
                for provider, cap in self.PROVIDER_CAPABILITIES.items()
            ],
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all providers"""
        health_status = {}

        for provider_type in ProviderType:
            try:
                # Try to acquire a connection
                conn = await self.pool.acquire_connection(provider_type, timeout=5)
                await self.pool.release_connection(conn)

                health_status[provider_type.value] = {
                    "status": "healthy",
                    "connection_state": conn.state.value,
                    "metrics": {
                        "success_rate": conn.metrics.success_rate,
                        "average_latency": conn.metrics.average_latency,
                    },
                }
            except Exception as e:
                health_status[provider_type.value] = {
                    "status": "unhealthy",
                    "error": str(e),
                }

        return health_status


# Integration with existing orchestrator
class OrchestratorProviderAdapter:
    """
    Adapter to integrate ProviderManager with existing GenericOrchestrator
    Provides backward compatibility while adding new capabilities
    """

    def __init__(self, orchestrator: Any, provider_manager: ProviderManager):
        """
        Initialize adapter

        Args:
            orchestrator: Existing GenericOrchestrator instance
            provider_manager: ProviderManager instance
        """
        self.orchestrator = orchestrator
        self.provider_manager = provider_manager

    async def execute_with_provider(
        self,
        task: Any,
        preferred_provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute task using provider manager

        Args:
            task: Task to execute
            preferred_provider: Optional preferred provider name

        Returns:
            Execution result
        """
        # Map string to provider type
        provider_type = None
        if preferred_provider:
            provider_map = {
                "claude": ProviderType.CLAUDE,
                "anthropic": ProviderType.CLAUDE,
                "openai": ProviderType.OPENAI,
                "gpt": ProviderType.OPENAI,
            }
            provider_type = provider_map.get(preferred_provider.lower())

        # Execute via provider manager
        return await self.provider_manager.execute_task(
            task,
            provider_type=provider_type,
        )

    def get_provider_for_task(self, task: Any) -> str:
        """
        Get recommended provider for a task

        Args:
            task: Task to analyze

        Returns:
            Provider name
        """
        # Analyze task requirements
        requirements = {}

        if hasattr(task, "context"):
            context = task.context
            if context.get("requires_vision"):
                requirements["vision"] = True
            if context.get("requires_functions"):
                requirements["functions"] = True
            if context.get("max_tokens"):
                requirements["max_tokens"] = context["max_tokens"]

        # Select provider
        provider_type = self.provider_manager.select_provider(
            task_type=getattr(task, "task_type", None),
            requirements=requirements,
        )

        return provider_type.value


# Example usage
async def main():
    """Example integration"""

    # Initialize provider manager
    manager = ProviderManager(
        strategy=ProviderStrategy.LEAST_LOADED,
        enable_fallback=True,
        pool_config={
            "max_connections": 5,
            "keepalive_timeout": 300,
            "max_retries": 3,
        },
    )

    await manager.start()

    try:
        # Create a sample task
        from dataclasses import dataclass

        @dataclass
        class SampleTask:
            task_id: str
            task_type: str
            prompt: str
            system_prompt: str = None

        task = SampleTask(
            task_id="test-123",
            task_type="analysis",
            prompt="Analyze this code for security vulnerabilities",
            system_prompt="You are a security expert",
        )

        # Execute with automatic provider selection
        result = await manager.execute_task(task)
        print(f"Result: {result}")

        # Get status
        status = await manager.get_status()
        print(f"Status: {status}")

        # Health check
        health = await manager.health_check()
        print(f"Health: {health}")

    finally:
        await manager.stop()


if __name__ == "__main__":
    asyncio.run(main())
