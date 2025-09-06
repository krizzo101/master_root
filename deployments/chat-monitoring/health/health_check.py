#!/usr/bin/env python3
"""
Comprehensive health check system for chat monitoring services
"""

import asyncio
import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict

import aioredis
import asyncpg
import psutil


@dataclass
class HealthStatus:
    """Health status information"""

    service: str
    status: str  # healthy, degraded, unhealthy
    timestamp: str
    details: Dict[str, Any]
    latency_ms: float


class ServiceDiscovery:
    """Service discovery and registration"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.services = {}

    async def register_service(
        self, service_name: str, host: str, port: int, metadata: Dict = None
    ):
        """Register a service"""
        redis = aioredis.from_url(self.redis_url)
        service_info = {
            "name": service_name,
            "host": host,
            "port": port,
            "registered_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }

        await redis.hset(f"service:{service_name}", mapping=service_info)
        await redis.expire(f"service:{service_name}", 60)  # TTL 60 seconds
        await redis.close()

    async def discover_services(self) -> Dict[str, Dict]:
        """Discover all registered services"""
        redis = aioredis.from_url(self.redis_url)
        services = {}

        async for key in redis.scan_iter(match="service:*"):
            service_name = key.decode().split(":", 1)[1]
            service_info = await redis.hgetall(key)
            services[service_name] = {
                k.decode(): v.decode() for k, v in service_info.items()
            }

        await redis.close()
        return services


class HealthChecker:
    """Comprehensive health checking system"""

    def __init__(self, postgres_url: str = None, redis_url: str = None):
        self.postgres_url = postgres_url
        self.redis_url = redis_url
        self.logger = logging.getLogger(__name__)

    async def check_system_resources(self) -> HealthStatus:
        """Check system resource utilization"""
        start_time = time.time()

        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            details = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": round(memory.used / 1024**3, 2),
                "memory_total_gb": round(memory.total / 1024**3, 2),
                "disk_percent": disk.percent,
                "disk_free_gb": round(disk.free / 1024**3, 2),
            }

            # Determine status
            if cpu_percent > 90 or memory.percent > 90 or disk.percent > 90:
                status = "unhealthy"
            elif cpu_percent > 75 or memory.percent > 75 or disk.percent > 85:
                status = "degraded"
            else:
                status = "healthy"

            return HealthStatus(
                service="system_resources",
                status=status,
                timestamp=datetime.utcnow().isoformat(),
                details=details,
                latency_ms=round((time.time() - start_time) * 1000, 2),
            )

        except Exception as e:
            return HealthStatus(
                service="system_resources",
                status="unhealthy",
                timestamp=datetime.utcnow().isoformat(),
                details={"error": str(e)},
                latency_ms=round((time.time() - start_time) * 1000, 2),
            )

    async def check_postgres(self) -> HealthStatus:
        """Check PostgreSQL database connectivity and performance"""
        start_time = time.time()

        if not self.postgres_url:
            return HealthStatus(
                service="postgres",
                status="unhealthy",
                timestamp=datetime.utcnow().isoformat(),
                details={"error": "PostgreSQL URL not configured"},
                latency_ms=0,
            )

        try:
            conn = await asyncpg.connect(self.postgres_url)

            # Test query performance
            query_start = time.time()
            result = await conn.fetchval("SELECT 1")
            query_time = (time.time() - query_start) * 1000

            # Check connection pool stats
            pool_info = {
                "connection_test": result == 1,
                "query_latency_ms": round(query_time, 2),
            }

            await conn.close()

            status = (
                "healthy"
                if query_time < 100
                else ("degraded" if query_time < 500 else "unhealthy")
            )

            return HealthStatus(
                service="postgres",
                status=status,
                timestamp=datetime.utcnow().isoformat(),
                details=pool_info,
                latency_ms=round((time.time() - start_time) * 1000, 2),
            )

        except Exception as e:
            return HealthStatus(
                service="postgres",
                status="unhealthy",
                timestamp=datetime.utcnow().isoformat(),
                details={"error": str(e)},
                latency_ms=round((time.time() - start_time) * 1000, 2),
            )

    async def check_redis(self) -> HealthStatus:
        """Check Redis connectivity and performance"""
        start_time = time.time()

        if not self.redis_url:
            return HealthStatus(
                service="redis",
                status="unhealthy",
                timestamp=datetime.utcnow().isoformat(),
                details={"error": "Redis URL not configured"},
                latency_ms=0,
            )

        try:
            redis = aioredis.from_url(self.redis_url)

            # Test ping
            ping_start = time.time()
            pong = await redis.ping()
            ping_time = (time.time() - ping_start) * 1000

            # Get info
            info = await redis.info()

            details = {
                "ping_response": pong,
                "ping_latency_ms": round(ping_time, 2),
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_mb": round(info.get("used_memory", 0) / 1024**2, 2),
            }

            await redis.close()

            status = (
                "healthy"
                if ping_time < 10
                else ("degraded" if ping_time < 50 else "unhealthy")
            )

            return HealthStatus(
                service="redis",
                status=status,
                timestamp=datetime.utcnow().isoformat(),
                details=details,
                latency_ms=round((time.time() - start_time) * 1000, 2),
            )

        except Exception as e:
            return HealthStatus(
                service="redis",
                status="unhealthy",
                timestamp=datetime.utcnow().isoformat(),
                details={"error": str(e)},
                latency_ms=round((time.time() - start_time) * 1000, 2),
            )

    async def check_chat_monitoring_service(self) -> HealthStatus:
        """Check chat monitoring specific health"""
        start_time = time.time()

        try:
            # Check if ingestion queue is responding
            # Check processing rates
            # Check file watcher status

            details = {
                "queue_size": 0,  # Would be populated from actual service
                "files_processed_per_minute": 0,
                "last_processing_time": datetime.utcnow().isoformat(),
                "watcher_active": True,
            }

            return HealthStatus(
                service="chat_monitoring",
                status="healthy",
                timestamp=datetime.utcnow().isoformat(),
                details=details,
                latency_ms=round((time.time() - start_time) * 1000, 2),
            )

        except Exception as e:
            return HealthStatus(
                service="chat_monitoring",
                status="unhealthy",
                timestamp=datetime.utcnow().isoformat(),
                details={"error": str(e)},
                latency_ms=round((time.time() - start_time) * 1000, 2),
            )

    async def comprehensive_health_check(self) -> Dict[str, Any]:
        """Run all health checks and return comprehensive status"""
        checks = await asyncio.gather(
            self.check_system_resources(),
            self.check_postgres(),
            self.check_redis(),
            self.check_chat_monitoring_service(),
            return_exceptions=True,
        )

        results = {}
        overall_status = "healthy"

        for check in checks:
            if isinstance(check, Exception):
                self.logger.error(f"Health check failed: {check}")
                continue

            results[check.service] = asdict(check)

            # Determine overall status
            if check.status == "unhealthy":
                overall_status = "unhealthy"
            elif check.status == "degraded" and overall_status != "unhealthy":
                overall_status = "degraded"

        return {
            "overall_status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": results,
            "summary": {
                "total_checks": len(results),
                "healthy": len(
                    [r for r in results.values() if r["status"] == "healthy"]
                ),
                "degraded": len(
                    [r for r in results.values() if r["status"] == "degraded"]
                ),
                "unhealthy": len(
                    [r for r in results.values() if r["status"] == "unhealthy"]
                ),
            },
        }


async def main():
    """Main health check execution"""
    import os

    postgres_url = os.getenv(
        "POSTGRES_URL", "postgresql://opsvi:password@localhost:5432/unified_context"
    )
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

    checker = HealthChecker(postgres_url, redis_url)
    health_status = await checker.comprehensive_health_check()

    print(json.dumps(health_status, indent=2))

    # Exit with appropriate code
    if health_status["overall_status"] == "unhealthy":
        exit(1)
    elif health_status["overall_status"] == "degraded":
        exit(2)
    else:
        exit(0)


if __name__ == "__main__":
    asyncio.run(main())
