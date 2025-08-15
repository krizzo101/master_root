"""
Health monitoring system for checking component status.
"""

import asyncio
import psutil
import time
from typing import Dict, Any, List, Optional, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
import aiohttp
from pathlib import Path

from ..utils.logger import get_logger

logger = get_logger(__name__)


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    
    @property
    def is_healthy(self) -> bool:
        """Check if status is healthy."""
        return self == self.HEALTHY
    
    @property
    def severity(self) -> int:
        """Get severity level (higher = worse)."""
        severities = {
            self.HEALTHY: 0,
            self.DEGRADED: 1,
            self.UNKNOWN: 2,
            self.UNHEALTHY: 3
        }
        return severities[self]


@dataclass
class ComponentHealth:
    """Health status of a component."""
    name: str
    status: HealthStatus
    message: str = ""
    last_check: Optional[datetime] = None
    response_time_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['status'] = self.status.value
        if self.last_check:
            data['last_check'] = self.last_check.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ComponentHealth':
        """Create from dictionary."""
        data = data.copy()
        data['status'] = HealthStatus(data['status'])
        if data.get('last_check'):
            data['last_check'] = datetime.fromisoformat(data['last_check'])
        return cls(**data)


@dataclass
class SystemHealth:
    """Overall system health."""
    status: HealthStatus
    components: Dict[str, ComponentHealth]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'status': self.status.value,
            'components': {
                name: comp.to_dict()
                for name, comp in self.components.items()
            },
            'timestamp': self.timestamp.isoformat()
        }
    
    @property
    def healthy_components(self) -> List[str]:
        """Get list of healthy components."""
        return [
            name for name, comp in self.components.items()
            if comp.status == HealthStatus.HEALTHY
        ]
    
    @property
    def unhealthy_components(self) -> List[str]:
        """Get list of unhealthy components."""
        return [
            name for name, comp in self.components.items()
            if comp.status == HealthStatus.UNHEALTHY
        ]


class HealthCheck:
    """Base class for health checks."""
    
    def __init__(self, name: str, critical: bool = False):
        self.name = name
        self.critical = critical  # If true, failure makes system unhealthy
    
    async def check(self) -> ComponentHealth:
        """Perform health check."""
        raise NotImplementedError


class SystemResourceCheck(HealthCheck):
    """Check system resource usage."""
    
    def __init__(self,
                 cpu_threshold: float = 90.0,
                 memory_threshold: float = 85.0,
                 disk_threshold: float = 90.0):
        super().__init__("system_resources", critical=True)
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.disk_threshold = disk_threshold
    
    async def check(self) -> ComponentHealth:
        """Check system resources."""
        start_time = time.time()
        issues = []
        metadata = {}
        
        try:
            # Check CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            metadata['cpu_usage'] = cpu_percent
            if cpu_percent > self.cpu_threshold:
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
            
            # Check memory
            memory = psutil.virtual_memory()
            metadata['memory_usage'] = memory.percent
            metadata['memory_available_gb'] = memory.available / (1024**3)
            if memory.percent > self.memory_threshold:
                issues.append(f"High memory usage: {memory.percent:.1f}%")
            
            # Check disk
            disk = psutil.disk_usage('/')
            metadata['disk_usage'] = disk.percent
            metadata['disk_free_gb'] = disk.free / (1024**3)
            if disk.percent > self.disk_threshold:
                issues.append(f"High disk usage: {disk.percent:.1f}%")
            
            # Determine status
            if issues:
                status = HealthStatus.DEGRADED if len(issues) == 1 else HealthStatus.UNHEALTHY
                message = "; ".join(issues)
            else:
                status = HealthStatus.HEALTHY
                message = "All resources within thresholds"
            
            response_time = (time.time() - start_time) * 1000
            
            return ComponentHealth(
                name=self.name,
                status=status,
                message=message,
                last_check=datetime.utcnow(),
                response_time_ms=response_time,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"System resource check failed: {e}")
            return ComponentHealth(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Check failed: {e}",
                last_check=datetime.utcnow()
            )


class ServiceCheck(HealthCheck):
    """Check if a service is running."""
    
    def __init__(self, 
                 name: str,
                 process_name: Optional[str] = None,
                 port: Optional[int] = None,
                 critical: bool = False):
        super().__init__(name, critical)
        self.process_name = process_name
        self.port = port
    
    async def check(self) -> ComponentHealth:
        """Check service status."""
        start_time = time.time()
        
        try:
            is_running = False
            message_parts = []
            
            # Check process
            if self.process_name:
                for proc in psutil.process_iter(['name']):
                    if proc.info['name'] == self.process_name:
                        is_running = True
                        message_parts.append(f"Process '{self.process_name}' is running")
                        break
                
                if not is_running:
                    message_parts.append(f"Process '{self.process_name}' not found")
            
            # Check port
            if self.port:
                connections = psutil.net_connections()
                port_listening = any(
                    conn.laddr.port == self.port and conn.status == 'LISTEN'
                    for conn in connections if conn.laddr
                )
                
                if port_listening:
                    is_running = True
                    message_parts.append(f"Port {self.port} is listening")
                else:
                    message_parts.append(f"Port {self.port} not listening")
            
            status = HealthStatus.HEALTHY if is_running else HealthStatus.UNHEALTHY
            message = "; ".join(message_parts) if message_parts else "Service check completed"
            response_time = (time.time() - start_time) * 1000
            
            return ComponentHealth(
                name=self.name,
                status=status,
                message=message,
                last_check=datetime.utcnow(),
                response_time_ms=response_time
            )
            
        except Exception as e:
            logger.error(f"Service check failed for {self.name}: {e}")
            return ComponentHealth(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Check failed: {e}",
                last_check=datetime.utcnow()
            )


class HTTPCheck(HealthCheck):
    """Check HTTP endpoint health."""
    
    def __init__(self,
                 name: str,
                 url: str,
                 timeout: float = 5.0,
                 expected_status: int = 200,
                 critical: bool = False):
        super().__init__(name, critical)
        self.url = url
        self.timeout = timeout
        self.expected_status = expected_status
    
    async def check(self) -> ComponentHealth:
        """Check HTTP endpoint."""
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.url,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status == self.expected_status:
                        return ComponentHealth(
                            name=self.name,
                            status=HealthStatus.HEALTHY,
                            message=f"Endpoint returned {response.status}",
                            last_check=datetime.utcnow(),
                            response_time_ms=response_time,
                            metadata={'status_code': response.status}
                        )
                    else:
                        return ComponentHealth(
                            name=self.name,
                            status=HealthStatus.UNHEALTHY,
                            message=f"Unexpected status: {response.status}",
                            last_check=datetime.utcnow(),
                            response_time_ms=response_time,
                            metadata={'status_code': response.status}
                        )
                        
        except asyncio.TimeoutError:
            return ComponentHealth(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Timeout after {self.timeout}s",
                last_check=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"HTTP check failed for {self.name}: {e}")
            return ComponentHealth(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Check failed: {e}",
                last_check=datetime.utcnow()
            )


class DatabaseCheck(HealthCheck):
    """Check database connectivity."""
    
    def __init__(self,
                 name: str,
                 connection_func: Callable,
                 query: str = "SELECT 1",
                 critical: bool = True):
        super().__init__(name, critical)
        self.connection_func = connection_func
        self.query = query
    
    async def check(self) -> ComponentHealth:
        """Check database connection."""
        start_time = time.time()
        
        try:
            # Get connection
            conn = await self.connection_func()
            
            # Execute test query
            if hasattr(conn, 'execute'):
                await conn.execute(self.query)
            elif hasattr(conn, 'fetch'):
                await conn.fetch(self.query)
            
            # Close connection
            if hasattr(conn, 'close'):
                await conn.close()
            
            response_time = (time.time() - start_time) * 1000
            
            return ComponentHealth(
                name=self.name,
                status=HealthStatus.HEALTHY,
                message="Database connection successful",
                last_check=datetime.utcnow(),
                response_time_ms=response_time
            )
            
        except Exception as e:
            logger.error(f"Database check failed for {self.name}: {e}")
            return ComponentHealth(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Connection failed: {e}",
                last_check=datetime.utcnow()
            )


class FileSystemCheck(HealthCheck):
    """Check file system accessibility."""
    
    def __init__(self,
                 name: str,
                 path: Path,
                 writable: bool = False,
                 critical: bool = False):
        super().__init__(name, critical)
        self.path = Path(path)
        self.writable = writable
    
    async def check(self) -> ComponentHealth:
        """Check file system."""
        try:
            # Check if path exists
            if not self.path.exists():
                return ComponentHealth(
                    name=self.name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Path does not exist: {self.path}",
                    last_check=datetime.utcnow()
                )
            
            # Check if readable
            if self.path.is_file():
                self.path.read_text()
            else:
                list(self.path.iterdir())
            
            # Check if writable (if required)
            if self.writable:
                test_file = self.path / ".health_check"
                test_file.write_text("test")
                test_file.unlink()
            
            return ComponentHealth(
                name=self.name,
                status=HealthStatus.HEALTHY,
                message=f"File system accessible: {self.path}",
                last_check=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"File system check failed for {self.name}: {e}")
            return ComponentHealth(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Access failed: {e}",
                last_check=datetime.utcnow()
            )


class HealthChecker:
    """Main health checking system."""
    
    def __init__(self):
        self.checks: List[HealthCheck] = []
        self.last_check: Optional[SystemHealth] = None
        self.check_interval = timedelta(seconds=30)
        self.last_check_time: Optional[datetime] = None
        
        # Add default checks
        self._add_default_checks()
    
    def _add_default_checks(self):
        """Add default health checks."""
        # System resources
        self.add_check(SystemResourceCheck())
        
        # File system
        self.add_check(FileSystemCheck(
            name="data_directory",
            path=Path("./data"),
            writable=True
        ))
        
        self.add_check(FileSystemCheck(
            name="cache_directory",
            path=Path("./cache"),
            writable=True
        ))
    
    def add_check(self, check: HealthCheck):
        """Add a health check."""
        self.checks.append(check)
        logger.info(f"Added health check: {check.name}")
    
    async def check_component(self, name: str) -> Optional[ComponentHealth]:
        """Check a specific component."""
        for check in self.checks:
            if check.name == name:
                return await check.check()
        return None
    
    async def check_all(self, force: bool = False) -> SystemHealth:
        """Check all components."""
        # Use cached result if recent and not forced
        if not force and self.last_check_time:
            if datetime.utcnow() - self.last_check_time < self.check_interval:
                return self.last_check
        
        # Run all checks concurrently
        results = await asyncio.gather(
            *[check.check() for check in self.checks],
            return_exceptions=True
        )
        
        # Process results
        components = {}
        critical_failures = []
        
        for check, result in zip(self.checks, results):
            if isinstance(result, Exception):
                logger.error(f"Health check {check.name} failed with exception: {result}")
                components[check.name] = ComponentHealth(
                    name=check.name,
                    status=HealthStatus.UNKNOWN,
                    message=f"Check failed: {result}",
                    last_check=datetime.utcnow()
                )
            else:
                components[check.name] = result
                
                # Track critical failures
                if check.critical and result.status == HealthStatus.UNHEALTHY:
                    critical_failures.append(check.name)
        
        # Determine overall status
        if critical_failures:
            overall_status = HealthStatus.UNHEALTHY
        elif any(c.status == HealthStatus.UNHEALTHY for c in components.values()):
            overall_status = HealthStatus.DEGRADED
        elif any(c.status == HealthStatus.DEGRADED for c in components.values()):
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        
        # Create system health
        system_health = SystemHealth(
            status=overall_status,
            components=components,
            timestamp=datetime.utcnow()
        )
        
        # Cache result
        self.last_check = system_health
        self.last_check_time = datetime.utcnow()
        
        return system_health
    
    async def start_monitoring(self, interval: float = 30.0):
        """Start continuous health monitoring."""
        while True:
            try:
                health = await self.check_all()
                
                # Log status changes
                if health.status != HealthStatus.HEALTHY:
                    logger.warning(
                        f"System health: {health.status.value}. "
                        f"Unhealthy components: {health.unhealthy_components}"
                    )
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(interval)
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get a summary of current health status."""
        if not self.last_check:
            return {"status": "unknown", "message": "No health check performed yet"}
        
        return {
            "status": self.last_check.status.value,
            "timestamp": self.last_check.timestamp.isoformat(),
            "healthy_components": self.last_check.healthy_components,
            "unhealthy_components": self.last_check.unhealthy_components,
            "total_components": len(self.last_check.components)
        }


# Example usage
if __name__ == "__main__":
    async def example():
        # Create health checker
        checker = HealthChecker()
        
        # Add custom checks
        checker.add_check(HTTPCheck(
            name="api_endpoint",
            url="https://api.example.com/health",
            critical=True
        ))
        
        checker.add_check(ServiceCheck(
            name="redis",
            port=6379
        ))
        
        # Perform health check
        health = await checker.check_all()
        
        print(f"Overall status: {health.status.value}")
        print("\nComponent status:")
        for name, component in health.components.items():
            print(f"  - {name}: {component.status.value} - {component.message}")
        
        # Get summary
        print("\nStatus summary:")
        print(checker.get_status_summary())
    
    asyncio.run(example())