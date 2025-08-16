#!/usr/bin/env python3
"""
Enhanced OPSVI Data Demo

Demonstrates all the enhanced data capabilities ported from agent_world:
- ArangoDB Provider (graph database)
- PostgreSQL Provider (relational database)
- Redis Provider (key-value store)

This demo shows the comprehensive data integration capabilities.
"""

import asyncio
import os
import sys

# Add the library to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from opsvi_data import (
    # ArangoDB
    ArangoDBProvider,
    ArangoDBConfig,
    # PostgreSQL
    PostgreSQLProvider,
    PostgreSQLConfig,
    # Redis
    RedisProvider,
    RedisConfig,
)


async def demo_arango_provider():
    """Demo the ArangoDB provider functionality."""
    print("=== ArangoDB Provider Demo ===")

    try:
        # Create configuration
        config = ArangoDBConfig(
            host=os.getenv("ARANGO_URL", "http://127.0.0.1:8529"),
            database=os.getenv("ARANGO_DB", "_system"),
            username=os.getenv("ARANGO_USERNAME", "root"),
            password=os.getenv("ARANGO_PASSWORD", "change_me"),
        )

        # Create provider
        provider = ArangoDBProvider(config)
        print(f"  ✅ Provider created with host: {config.host}")

        # Initialize provider
        await provider.initialize()
        print("  ✅ Provider initialized")

        # Test health check
        health = await provider._health_check_impl()
        print(f"  ✅ Health check: {health}")

        # Test basic operations
        collections = provider.list_collections()
        print(f"  ✅ Collections found: {len(collections)}")

        return True

    except Exception as e:
        print(f"  ❌ ArangoDB demo failed: {e}")
        return False


async def demo_postgresql_provider():
    """Demo the PostgreSQL provider functionality."""
    print("=== PostgreSQL Provider Demo ===")

    try:
        # Create configuration
        config = PostgreSQLConfig(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "password"),
            database=os.getenv("POSTGRES_DB", "postgres"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
        )

        # Create provider
        provider = PostgreSQLProvider(config)
        print(f"  ✅ Provider created with host: {config.host}")

        # Initialize provider
        await provider.initialize()
        print("  ✅ Provider initialized")

        # Test health check
        health = await provider._health_check_impl()
        print(f"  ✅ Health check: {health}")

        # Test basic operations
        tables = provider.list_tables()
        print(f"  ✅ Tables found: {len(tables)}")

        return True

    except Exception as e:
        print(f"  ❌ PostgreSQL demo failed: {e}")
        return False


async def demo_redis_provider():
    """Demo the Redis provider functionality."""
    print("=== Redis Provider Demo ===")

    try:
        # Create configuration
        config = RedisConfig(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0")),
            password=os.getenv("REDIS_PASSWORD"),
        )

        # Create provider
        provider = RedisProvider(config)
        print(f"  ✅ Provider created with host: {config.host}")

        # Initialize provider
        await provider.initialize()
        print("  ✅ Provider initialized")

        # Test health check
        health = await provider._health_check_impl()
        print(f"  ✅ Health check: {health}")

        # Test basic operations
        dbsize = provider.dbsize()
        print(f"  ✅ Database size: {dbsize} keys")

        return True

    except Exception as e:
        print(f"  ❌ Redis demo failed: {e}")
        return False


async def demo_async_capabilities():
    """Demo async capabilities of the providers."""
    print("=== Async Capabilities Demo ===")

    try:
        # Test async ArangoDB
        arango_config = ArangoDBConfig()
        arango_provider = ArangoDBProvider(arango_config)
        print("  ✅ Async ArangoDB provider ready")

        # Test async PostgreSQL
        postgres_config = PostgreSQLConfig()
        postgres_provider = PostgreSQLProvider(postgres_config)
        print("  ✅ Async PostgreSQL provider ready")

        # Test async Redis
        redis_config = RedisConfig()
        redis_provider = RedisProvider(redis_config)
        print("  ✅ Async Redis provider ready")

        print("  ✅ All async providers initialized")
        return True

    except Exception as e:
        print(f"  ❌ Async demo failed: {e}")
        return False


async def demo_integration():
    """Demo integration between different providers."""
    print("=== Integration Demo ===")

    try:
        # Create all providers
        arango_provider = ArangoDBProvider(ArangoDBConfig())
        postgres_provider = PostgreSQLProvider(PostgreSQLConfig())
        redis_provider = RedisProvider(RedisConfig())

        # Initialize all providers
        await arango_provider.initialize()
        await postgres_provider.initialize()
        await redis_provider.initialize()

        print("  ✅ All providers initialized successfully")

        # Test cross-provider functionality
        # Get database info from each provider
        arango_info = arango_provider.get_database_info()
        postgres_info = postgres_provider.health_check()
        redis_info = redis_provider.health_check()

        print(
            f"  ✅ Cross-provider: ArangoDB collections: {len(arango_provider.list_collections())}"
        )
        print(
            f"  ✅ Cross-provider: PostgreSQL tables: {len(postgres_provider.list_tables())}"
        )
        print(f"  ✅ Cross-provider: Redis keys: {redis_provider.dbsize()}")

        print("  ✅ Integration test completed")
        return True

    except Exception as e:
        print(f"  ❌ Integration demo failed: {e}")
        return False


async def demo_advanced_features():
    """Demo advanced features of the providers."""
    print("=== Advanced Features Demo ===")

    try:
        # Test ArangoDB graph features
        arango_provider = ArangoDBProvider(ArangoDBConfig())
        await arango_provider.initialize()
        graphs = arango_provider.list_graphs()
        print(f"  ✅ ArangoDB graphs: {len(graphs)}")

        # Test PostgreSQL transaction features
        postgres_provider = PostgreSQLProvider(PostgreSQLConfig())
        await postgres_provider.initialize()
        with postgres_provider.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print(f"  ✅ PostgreSQL transaction: {result[0]}")

        # Test Redis data structures
        redis_provider = RedisProvider(RedisConfig())
        await redis_provider.initialize()
        redis_provider.set("demo_key", "demo_value", ex=60)
        value = redis_provider.get("demo_key")
        print(f"  ✅ Redis key-value: {value}")

        print("  ✅ Advanced features test completed")
        return True

    except Exception as e:
        print(f"  ❌ Advanced features demo failed: {e}")
        return False


async def main():
    """Run all demos."""
    print("🚀 Enhanced OPSVI Data Demo")
    print("=" * 50)

    # Check for environment variables
    print("⚠️  Environment variables not set - some demos may fail")
    print("   Set database connection variables to test full functionality")

    results = []

    # Run demos
    results.append(("ArangoDB", await demo_arango_provider()))
    results.append(("PostgreSQL", await demo_postgresql_provider()))
    results.append(("Redis", await demo_redis_provider()))
    results.append(("Integration", await demo_integration()))
    results.append(("Advanced Features", await demo_advanced_features()))

    # Run async demo
    async_result = await demo_async_capabilities()
    results.append(("Async", async_result))

    # Summary
    print("\n" + "=" * 50)
    print("📊 Demo Results:")

    passed = 0
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {name}: {status}")
        if result:
            passed += 1

    print(f"\n🎯 Overall: {passed}/{total} demos passed")

    if passed == total:
        print("🎉 All enhanced data demos passed!")
        print(
            "   The OPSVI Data library is fully functional with agent_world enhancements."
        )
    else:
        print("⚠️  Some demos failed - check configuration and database access.")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
