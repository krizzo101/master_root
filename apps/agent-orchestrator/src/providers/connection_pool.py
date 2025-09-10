"""
Provider Connection Pool with Keep-Alive, Retry, and Health Monitoring
Supports Claude (Anthropic) and OpenAI providers with enterprise-grade resilience
"""

import asyncio
import hashlib
import json
import logging
import os
import random
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import aiohttp
from aiohttp import ClientSession, ClientTimeout, TCPConnector

logger = logging.getLogger(__name__)


class ProviderType(Enum):
    """Supported AI Provider Types"""

    CLAUDE = "claude"
    OPENAI = "openai"
    CUSTOM = "custom"


class ConnectionState(Enum):
    """Connection Health States"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    DEAD = "dead"


@dataclass
class ConnectionMetrics:
    """Metrics for connection health monitoring"""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_latency: float = 0.0
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0

    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests

    @property
    def average_latency(self) -> float:
        """Calculate average latency in seconds"""
        if self.successful_requests == 0:
            return 0.0
        return self.total_latency / self.successful_requests

    def record_success(self, latency: float):
        """Record successful request"""
        self.total_requests += 1
        self.successful_requests += 1
        self.total_latency += latency
        self.last_success = datetime.now()
        self.consecutive_successes += 1
        self.consecutive_failures = 0

    def record_failure(self):
        """Record failed request"""
        self.total_requests += 1
        self.failed_requests += 1
        self.last_failure = datetime.now()
        self.consecutive_failures += 1
        self.consecutive_successes = 0


@dataclass
class PooledConnection:
    """Individual pooled connection with health tracking"""

    connection_id: str
    provider: ProviderType
    session: ClientSession
    metrics: ConnectionMetrics = field(default_factory=ConnectionMetrics)
    state: ConnectionState = ConnectionState.HEALTHY
    created_at: datetime = field(default_factory=datetime.now)
    last_used: datetime = field(default_factory=datetime.now)

    def update_state(self):
        """Update connection state based on metrics"""
        if self.metrics.consecutive_failures >= 5:
            self.state = ConnectionState.DEAD
        elif self.metrics.consecutive_failures >= 3:
            self.state = ConnectionState.UNHEALTHY
        elif self.metrics.success_rate < 0.7:
            self.state = ConnectionState.DEGRADED
        else:
            self.state = ConnectionState.HEALTHY

    async def close(self):
        """Close the connection"""
        if self.session and not self.session.closed:
            await self.session.close()


@dataclass
class RetryConfig:
    """Configuration for retry with exponential backoff"""

    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt with exponential backoff"""
        delay = min(
            self.initial_delay * (self.exponential_base**attempt), self.max_delay
        )
        if self.jitter:
            delay *= 0.5 + random.random()
        return delay


class ProviderConnectionPool:
    """
    Enterprise-grade connection pool for AI providers
    Features:
    - Keep-alive connections with persistent sessions
    - Automatic retry with exponential backoff
    - Connection health monitoring and circuit breaking
    - Support for multiple providers (Claude, OpenAI)
    - Connection recycling and cleanup
    """

    def __init__(
        self,
        max_connections_per_provider: int = 10,
        keepalive_timeout: int = 300,
        connection_timeout: int = 30,
        retry_config: Optional[RetryConfig] = None,
        health_check_interval: int = 60,
        max_connection_age: int = 3600,
    ):
        """
        Initialize connection pool

        Args:
            max_connections_per_provider: Maximum connections per provider
            keepalive_timeout: Keep-alive timeout in seconds
            connection_timeout: Request timeout in seconds
            retry_config: Retry configuration
            health_check_interval: Health check interval in seconds
            max_connection_age: Maximum connection age before recycling (seconds)
        """
        self.max_connections_per_provider = max_connections_per_provider
        self.keepalive_timeout = keepalive_timeout
        self.connection_timeout = connection_timeout
        self.retry_config = retry_config or RetryConfig()
        self.health_check_interval = health_check_interval
        self.max_connection_age = max_connection_age

        # Connection pools per provider
        self.pools: Dict[ProviderType, List[PooledConnection]] = defaultdict(list)
        self.available_connections: Dict[ProviderType, asyncio.Queue] = {}

        # Provider configurations
        self.provider_configs: Dict[ProviderType, Dict] = {}

        # Health monitoring
        self.health_monitor_task: Optional[asyncio.Task] = None
        self.is_running = False

        # Lock for thread-safe operations
        self.lock = asyncio.Lock()

        # Initialize provider configurations
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize provider configurations"""
        # Claude/Anthropic configuration
        self.provider_configs[ProviderType.CLAUDE] = {
            "base_url": "https://api.anthropic.com/v1",
            "headers": {
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            "api_key_env": "ANTHROPIC_API_KEY",
        }

        # OpenAI configuration
        self.provider_configs[ProviderType.OPENAI] = {
            "base_url": "https://api.openai.com/v1",
            "headers": {
                "content-type": "application/json",
            },
            "api_key_env": "OPENAI_API_KEY",
        }

        # Initialize connection queues
        for provider in ProviderType:
            self.available_connections[provider] = asyncio.Queue(
                maxsize=self.max_connections_per_provider
            )

    async def start(self):
        """Start the connection pool and health monitoring"""
        async with self.lock:
            if self.is_running:
                return

            self.is_running = True

            # Start health monitoring
            self.health_monitor_task = asyncio.create_task(self._health_monitor_loop())

            logger.info("ProviderConnectionPool started")

    async def stop(self):
        """Stop the connection pool and cleanup"""
        async with self.lock:
            if not self.is_running:
                return

            self.is_running = False

            # Cancel health monitoring
            if self.health_monitor_task:
                self.health_monitor_task.cancel()
                try:
                    await self.health_monitor_task
                except asyncio.CancelledError:
                    pass

            # Close all connections
            for provider_type, connections in self.pools.items():
                for conn in connections:
                    await conn.close()

            self.pools.clear()

            logger.info("ProviderConnectionPool stopped")

    async def _create_connection(self, provider: ProviderType) -> PooledConnection:
        """Create a new connection for the provider"""
        config = self.provider_configs.get(provider, {})

        # Create connector with keep-alive
        connector = TCPConnector(
            limit=1,
            keepalive_timeout=self.keepalive_timeout,
            force_close=False,
            enable_cleanup_closed=True,
        )

        # Create session with timeout
        timeout = ClientTimeout(total=self.connection_timeout)
        session = ClientSession(
            connector=connector,
            timeout=timeout,
            headers=config.get("headers", {}),
        )

        # Add API key if available
        api_key_env = config.get("api_key_env")
        if api_key_env:
            api_key = os.getenv(api_key_env)
            if api_key:
                if provider == ProviderType.CLAUDE:
                    session.headers["x-api-key"] = api_key
                elif provider == ProviderType.OPENAI:
                    session.headers["Authorization"] = f"Bearer {api_key}"

        # Create connection object
        connection = PooledConnection(
            connection_id=hashlib.md5(
                f"{provider.value}_{time.time()}".encode(), usedforsecurity=False
            ).hexdigest()[:8],
            provider=provider,
            session=session,
        )

        logger.debug(
            f"Created connection {connection.connection_id} for {provider.value}"
        )
        return connection

    async def acquire_connection(
        self, provider: ProviderType, timeout: Optional[float] = None
    ) -> PooledConnection:
        """
        Acquire a healthy connection from the pool

        Args:
            provider: Provider type
            timeout: Acquisition timeout in seconds

        Returns:
            Healthy pooled connection
        """
        timeout = timeout or self.connection_timeout

        async with self.lock:
            # First, try to get an existing healthy connection
            healthy_connections = [
                conn
                for conn in self.pools[provider]
                if conn.state in [ConnectionState.HEALTHY, ConnectionState.DEGRADED]
                and not conn.session.closed
            ]

            if healthy_connections:
                # Use least recently used connection
                conn = min(healthy_connections, key=lambda c: c.last_used)
                conn.last_used = datetime.now()

                # Check if connection needs recycling
                age = (datetime.now() - conn.created_at).total_seconds()
                if age > self.max_connection_age:
                    await conn.close()
                    self.pools[provider].remove(conn)
                    conn = await self._create_connection(provider)
                    self.pools[provider].append(conn)

                return conn

            # Create new connection if under limit
            if len(self.pools[provider]) < self.max_connections_per_provider:
                conn = await self._create_connection(provider)
                self.pools[provider].append(conn)
                return conn

            # Wait for a connection to become available
            logger.warning(
                f"All connections for {provider.value} are unhealthy or at limit"
            )

            # Try to revive dead connections
            dead_connections = [
                conn
                for conn in self.pools[provider]
                if conn.state == ConnectionState.DEAD
            ]

            if dead_connections:
                for conn in dead_connections:
                    await conn.close()
                    self.pools[provider].remove(conn)

                # Create replacement connection
                new_conn = await self._create_connection(provider)
                self.pools[provider].append(new_conn)
                return new_conn

            raise ConnectionError(
                f"No healthy connections available for {provider.value}"
            )

    async def release_connection(self, connection: PooledConnection):
        """
        Release a connection back to the pool

        Args:
            connection: Connection to release
        """
        connection.update_state()
        connection.last_used = datetime.now()

    async def execute_with_retry(
        self, provider: ProviderType, request_func: callable, *args, **kwargs
    ) -> Any:
        """
        Execute a request with automatic retry and connection management

        Args:
            provider: Provider type
            request_func: Async function to execute
            *args, **kwargs: Arguments for request function

        Returns:
            Response from request function
        """
        last_exception = None

        for attempt in range(self.retry_config.max_retries + 1):
            connection = None
            start_time = time.time()

            try:
                # Acquire connection
                connection = await self.acquire_connection(provider)

                # Execute request with connection's session
                response = await request_func(connection.session, *args, **kwargs)

                # Record success
                latency = time.time() - start_time
                connection.metrics.record_success(latency)

                return response

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_exception = e

                if connection:
                    connection.metrics.record_failure()

                # Log the error
                logger.warning(
                    f"Request failed for {provider.value} "
                    f"(attempt {attempt + 1}/{self.retry_config.max_retries + 1}): {e}"
                )

                # Don't retry on certain errors
                if isinstance(e, aiohttp.ClientResponseError):
                    if e.status in [400, 401, 403, 404]:
                        raise  # Don't retry client errors

                # Calculate retry delay
                if attempt < self.retry_config.max_retries:
                    delay = self.retry_config.get_delay(attempt)
                    logger.info(f"Retrying in {delay:.2f} seconds...")
                    await asyncio.sleep(delay)

            finally:
                if connection:
                    await self.release_connection(connection)

        # All retries exhausted
        raise last_exception or ConnectionError(
            f"Failed to execute request after {self.retry_config.max_retries + 1} attempts"
        )

    async def _health_monitor_loop(self):
        """Background task for monitoring connection health"""
        while self.is_running:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self._check_connection_health()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitor: {e}")

    async def _check_connection_health(self):
        """Check health of all connections"""
        async with self.lock:
            for provider_type, connections in self.pools.items():
                for conn in connections[
                    :
                ]:  # Use slice to avoid modification during iteration
                    # Check connection age
                    age = (datetime.now() - conn.created_at).total_seconds()
                    if age > self.max_connection_age:
                        logger.info(
                            f"Recycling aged connection {conn.connection_id} "
                            f"(age: {age:.0f}s)"
                        )
                        await conn.close()
                        self.pools[provider_type].remove(conn)
                        continue

                    # Check if session is closed
                    if conn.session.closed:
                        logger.warning(
                            f"Removing closed connection {conn.connection_id}"
                        )
                        self.pools[provider_type].remove(conn)
                        continue

                    # Update connection state based on metrics
                    conn.update_state()

                    # Log unhealthy connections
                    if conn.state in [ConnectionState.UNHEALTHY, ConnectionState.DEAD]:
                        logger.warning(
                            f"Connection {conn.connection_id} is {conn.state.value} "
                            f"(success_rate: {conn.metrics.success_rate:.2%}, "
                            f"consecutive_failures: {conn.metrics.consecutive_failures})"
                        )

    async def get_pool_status(self) -> Dict[str, Any]:
        """Get current pool status and metrics"""
        status = {
            "is_running": self.is_running,
            "providers": {},
        }

        async with self.lock:
            for provider_type, connections in self.pools.items():
                provider_stats = {
                    "total_connections": len(connections),
                    "healthy_connections": sum(
                        1 for c in connections if c.state == ConnectionState.HEALTHY
                    ),
                    "degraded_connections": sum(
                        1 for c in connections if c.state == ConnectionState.DEGRADED
                    ),
                    "unhealthy_connections": sum(
                        1 for c in connections if c.state == ConnectionState.UNHEALTHY
                    ),
                    "dead_connections": sum(
                        1 for c in connections if c.state == ConnectionState.DEAD
                    ),
                    "connections": [],
                }

                for conn in connections:
                    provider_stats["connections"].append(
                        {
                            "id": conn.connection_id,
                            "state": conn.state.value,
                            "age": (datetime.now() - conn.created_at).total_seconds(),
                            "last_used": (
                                datetime.now() - conn.last_used
                            ).total_seconds(),
                            "metrics": {
                                "total_requests": conn.metrics.total_requests,
                                "success_rate": conn.metrics.success_rate,
                                "average_latency": conn.metrics.average_latency,
                                "consecutive_failures": conn.metrics.consecutive_failures,
                            },
                        }
                    )

                status["providers"][provider_type.value] = provider_stats

        return status

    # Convenience methods for specific providers

    async def execute_claude_request(
        self, endpoint: str, data: Dict[str, Any], **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a Claude API request with retry and pooling

        Args:
            endpoint: API endpoint (e.g., "/messages")
            data: Request data
            **kwargs: Additional request parameters

        Returns:
            API response
        """
        config = self.provider_configs[ProviderType.CLAUDE]
        url = f"{config['base_url']}{endpoint}"

        async def _request(session: ClientSession):
            async with session.post(url, json=data, **kwargs) as response:
                response.raise_for_status()
                return await response.json()

        return await self.execute_with_retry(ProviderType.CLAUDE, _request)

    async def execute_openai_request(
        self, endpoint: str, data: Dict[str, Any], **kwargs
    ) -> Dict[str, Any]:
        """
        Execute an OpenAI API request with retry and pooling

        Args:
            endpoint: API endpoint (e.g., "/chat/completions")
            data: Request data
            **kwargs: Additional request parameters

        Returns:
            API response
        """
        config = self.provider_configs[ProviderType.OPENAI]
        url = f"{config['base_url']}{endpoint}"

        async def _request(session: ClientSession):
            async with session.post(url, json=data, **kwargs) as response:
                response.raise_for_status()
                return await response.json()

        return await self.execute_with_retry(ProviderType.OPENAI, _request)


# Example usage and integration
async def main():
    """Example usage of ProviderConnectionPool"""

    # Initialize pool
    pool = ProviderConnectionPool(
        max_connections_per_provider=5,
        keepalive_timeout=300,
        retry_config=RetryConfig(
            max_retries=3,
            initial_delay=1.0,
            exponential_base=2.0,
        ),
    )

    await pool.start()

    try:
        # Example Claude request
        claude_response = await pool.execute_claude_request(
            "/messages",
            {
                "model": "claude-3-opus-20240229",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 100,
            },
        )
        print(f"Claude response: {claude_response}")

        # Example OpenAI request
        openai_response = await pool.execute_openai_request(
            "/chat/completions",
            {
                "model": "gpt-4",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 100,
            },
        )
        print(f"OpenAI response: {openai_response}")

        # Get pool status
        status = await pool.get_pool_status()
        print(f"Pool status: {json.dumps(status, indent=2)}")

    finally:
        await pool.stop()


if __name__ == "__main__":
    asyncio.run(main())
