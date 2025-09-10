#!/usr/bin/env python3
"""
Demo script for ProviderConnectionPool
Shows connection pooling, retry, and health monitoring in action
"""

import asyncio
import json
import logging
import os
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add src to path
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.providers.connection_pool import (
    ProviderConnectionPool,
    ProviderType,
    RetryConfig,
)
from src.providers.provider_manager import ProviderManager, ProviderStrategy


async def demo_basic_pool():
    """Demonstrate basic connection pooling"""
    print("\n" + "=" * 60)
    print("DEMO: Basic Connection Pooling")
    print("=" * 60)

    # Create pool with custom configuration
    pool = ProviderConnectionPool(
        max_connections_per_provider=3,
        keepalive_timeout=300,
        connection_timeout=30,
        retry_config=RetryConfig(
            max_retries=2,
            initial_delay=0.5,
            exponential_base=2.0,
        ),
        health_check_interval=5,
    )

    await pool.start()
    print("✓ Connection pool started")

    try:
        # Acquire connections
        print("\n📊 Acquiring connections...")
        connections = []
        for i in range(3):
            conn = await pool.acquire_connection(ProviderType.CLAUDE)
            connections.append(conn)
            print(
                f"  - Connection {i+1}: {conn.connection_id} (state: {conn.state.value})"
            )

        # Simulate some work and metrics
        print("\n📈 Simulating requests...")
        for i, conn in enumerate(connections):
            # Simulate successful requests
            for j in range(3):
                conn.metrics.record_success(0.5 + j * 0.1)
            # Simulate a failure
            if i == 1:
                conn.metrics.record_failure()

            # Update and show state
            conn.update_state()
            print(f"  - Connection {conn.connection_id}:")
            print(f"    Success rate: {conn.metrics.success_rate:.1%}")
            print(f"    Avg latency: {conn.metrics.average_latency:.2f}s")
            print(f"    State: {conn.state.value}")

        # Release connections
        for conn in connections:
            await pool.release_connection(conn)

        # Get pool status
        print("\n📊 Pool Status:")
        status = await pool.get_pool_status()
        print(json.dumps(status, indent=2, default=str))

    finally:
        await pool.stop()
        print("\n✓ Connection pool stopped")


async def demo_retry_mechanism():
    """Demonstrate retry with exponential backoff"""
    print("\n" + "=" * 60)
    print("DEMO: Retry with Exponential Backoff")
    print("=" * 60)

    pool = ProviderConnectionPool(
        retry_config=RetryConfig(
            max_retries=3,
            initial_delay=1.0,
            exponential_base=2.0,
            jitter=True,
        )
    )

    await pool.start()

    try:
        # Simulate a request that fails then succeeds
        attempt_count = 0

        async def flaky_request(session):
            nonlocal attempt_count
            attempt_count += 1
            print(f"  Attempt {attempt_count}...")

            if attempt_count < 3:
                raise Exception(f"Simulated failure #{attempt_count}")

            return {"status": "success", "attempts": attempt_count}

        print("\n🔄 Executing request with retry...")
        result = await pool.execute_with_retry(ProviderType.OPENAI, flaky_request)

        print(f"\n✓ Request succeeded after {result['attempts']} attempts")
        print(f"  Result: {result}")

    except Exception as e:
        print(f"\n✗ Request failed: {e}")

    finally:
        await pool.stop()


async def demo_health_monitoring():
    """Demonstrate connection health monitoring"""
    print("\n" + "=" * 60)
    print("DEMO: Connection Health Monitoring")
    print("=" * 60)

    pool = ProviderConnectionPool(
        max_connections_per_provider=2,
        health_check_interval=2,  # Check every 2 seconds
        max_connection_age=10,  # Recycle after 10 seconds
    )

    await pool.start()

    try:
        # Create connections
        print("\n🏥 Creating connections for health monitoring...")
        conn1 = await pool.acquire_connection(ProviderType.CLAUDE)
        conn2 = await pool.acquire_connection(ProviderType.OPENAI)

        print(f"  - Claude connection: {conn1.connection_id}")
        print(f"  - OpenAI connection: {conn2.connection_id}")

        # Simulate degradation
        print("\n📉 Simulating connection degradation...")

        # Make conn1 unhealthy
        for _ in range(4):
            conn1.metrics.record_failure()
        conn1.update_state()

        # Make conn2 degraded
        for _ in range(3):
            conn2.metrics.record_success(1.0)
        for _ in range(2):
            conn2.metrics.record_failure()
        conn2.update_state()

        print(
            f"  - {conn1.connection_id}: {conn1.state.value} (failures: {conn1.metrics.consecutive_failures})"
        )
        print(
            f"  - {conn2.connection_id}: {conn2.state.value} (success rate: {conn2.metrics.success_rate:.1%})"
        )

        # Wait for health check
        print("\n⏳ Waiting for health check cycle...")
        await asyncio.sleep(3)

        # Check status after health monitoring
        print("\n📊 Status after health monitoring:")
        status = await pool.get_pool_status()

        for provider, stats in status["providers"].items():
            print(f"\n  {provider.upper()}:")
            print(f"    Total connections: {stats['total_connections']}")
            print(f"    Healthy: {stats['healthy_connections']}")
            print(f"    Degraded: {stats['degraded_connections']}")
            print(f"    Unhealthy: {stats['unhealthy_connections']}")

    finally:
        await pool.stop()


async def demo_provider_manager():
    """Demonstrate ProviderManager with strategy selection"""
    print("\n" + "=" * 60)
    print("DEMO: Provider Manager with Strategies")
    print("=" * 60)

    # Create manager with different strategies
    strategies = [
        ProviderStrategy.ROUND_ROBIN,
        ProviderStrategy.LEAST_LOADED,
        ProviderStrategy.COST_OPTIMIZED,
        ProviderStrategy.PERFORMANCE_OPTIMIZED,
    ]

    for strategy in strategies:
        print(f"\n🎯 Strategy: {strategy.value}")

        manager = ProviderManager(
            strategy=strategy,
            enable_fallback=True,
        )

        await manager.start()

        try:
            # Select providers for different requirements
            requirements_list = [
                {},
                {"vision": True},
                {"functions": True},
                {"max_tokens": 150000},
            ]

            for i, requirements in enumerate(requirements_list):
                provider = manager.select_provider(requirements=requirements)
                print(
                    f"  Requirements {i+1}: {requirements or 'None'} → {provider.value}"
                )

        finally:
            await manager.stop()


async def demo_concurrent_requests():
    """Demonstrate handling concurrent requests"""
    print("\n" + "=" * 60)
    print("DEMO: Concurrent Request Handling")
    print("=" * 60)

    pool = ProviderConnectionPool(
        max_connections_per_provider=3,
    )

    await pool.start()

    try:
        print("\n🚀 Launching 10 concurrent requests...")

        async def simulated_request(session, request_id):
            await asyncio.sleep(0.1)  # Simulate work
            return {"request_id": request_id, "timestamp": datetime.now().isoformat()}

        # Launch concurrent requests
        tasks = []
        for i in range(10):
            task = pool.execute_with_retry(ProviderType.CLAUDE, simulated_request, i)
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        print(f"\n✓ Completed {len(results)} requests")

        # Show pool utilization
        status = await pool.get_pool_status()
        claude_stats = status["providers"]["claude"]
        print(f"\n📊 Pool utilization:")
        print(f"  - Connections created: {claude_stats['total_connections']}")
        print(f"  - Max connections: 3")
        print(f"  - Requests handled: 10")

        # Show connection metrics
        print(f"\n📈 Connection metrics:")
        for conn_info in claude_stats["connections"]:
            print(
                f"  - {conn_info['id']}: {conn_info['metrics']['total_requests']} requests"
            )

    finally:
        await pool.stop()


async def main():
    """Run all demos"""
    print("\n" + "=" * 60)
    print("PROVIDER CONNECTION POOL DEMONSTRATION")
    print("=" * 60)

    demos = [
        ("Basic Connection Pooling", demo_basic_pool),
        ("Retry Mechanism", demo_retry_mechanism),
        ("Health Monitoring", demo_health_monitoring),
        ("Provider Manager", demo_provider_manager),
        ("Concurrent Requests", demo_concurrent_requests),
    ]

    for name, demo_func in demos:
        try:
            await demo_func()
        except Exception as e:
            logger.error(f"Error in {name}: {e}")

        # Small delay between demos
        await asyncio.sleep(1)

    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)
    print("\n✨ Key Features Demonstrated:")
    print("  ✓ Connection pooling with keep-alive")
    print("  ✓ Automatic retry with exponential backoff")
    print("  ✓ Connection health monitoring")
    print("  ✓ Multiple provider support (Claude & OpenAI)")
    print("  ✓ Provider selection strategies")
    print("  ✓ Concurrent request handling")
    print("  ✓ Connection recycling and cleanup")


if __name__ == "__main__":
    asyncio.run(main())
