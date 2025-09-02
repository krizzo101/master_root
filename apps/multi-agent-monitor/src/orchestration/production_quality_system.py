"""
Production Quality System for Multi-Agent Development
Ensures agents create production-ready code through specifications, patterns, and validation
"""

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


class QualityLevel(Enum):
    """Quality levels for different environments"""

    PROTOTYPE = "prototype"  # Quick POC, minimal requirements
    DEVELOPMENT = "development"  # Dev environment, basic standards
    STAGING = "staging"  # Pre-prod, most standards enforced
    PRODUCTION = "production"  # Full production standards


@dataclass
class ProductionRequirements:
    """Defines what production quality means for a component"""

    # Core Requirements
    quality_level: QualityLevel = QualityLevel.PRODUCTION

    # Code Quality
    test_coverage_minimum: float = 80.0
    linting_enabled: bool = True
    type_checking_enabled: bool = True
    documentation_required: bool = True

    # Security
    authentication_required: bool = True
    authorization_required: bool = True
    encryption_required: bool = True
    secrets_management: bool = True
    input_validation: bool = True
    sql_injection_prevention: bool = True

    # Reliability
    error_handling_required: bool = True
    logging_required: bool = True
    monitoring_required: bool = True
    health_checks_required: bool = True
    graceful_degradation: bool = True
    retry_logic: bool = True
    circuit_breakers: bool = False

    # Performance
    caching_required: bool = False
    rate_limiting: bool = True
    async_operations: bool = True
    connection_pooling: bool = True
    pagination_required: bool = True

    # Data
    database_required: bool = True
    migrations_required: bool = True
    backup_strategy: bool = True
    data_validation: bool = True

    # Deployment
    containerization: bool = True
    orchestration_config: bool = True
    ci_cd_pipeline: bool = True
    environment_configs: bool = True

    # Observability
    structured_logging: bool = True
    metrics_collection: bool = True
    distributed_tracing: bool = False
    alerting_rules: bool = True


@dataclass
class CodePattern:
    """Reusable code pattern for agents to follow"""

    name: str
    category: str
    language: str
    description: str
    template: str
    example: str
    anti_patterns: List[str] = field(default_factory=list)
    when_to_use: str = ""
    when_not_to_use: str = ""


class PatternLibrary:
    """Library of production-ready code patterns"""

    def __init__(self):
        self.patterns: Dict[str, List[CodePattern]] = {
            "python": [],
            "javascript": [],
            "sql": [],
            "yaml": [],
        }
        self._load_patterns()

    def _load_patterns(self):
        """Load production code patterns"""

        # Python: Database connection with pooling
        self.patterns["python"].append(
            CodePattern(
                name="async_database_pool",
                category="database",
                language="python",
                description="Async PostgreSQL connection with pooling",
                template="""
import asyncpg
from contextlib import asynccontextmanager
from typing import Optional
import os

class DatabasePool:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def init(self):
        self.pool = await asyncpg.create_pool(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432)),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            min_size=10,
            max_size=20,
            command_timeout=60
        )

    @asynccontextmanager
    async def acquire(self):
        async with self.pool.acquire() as conn:
            yield conn

    async def close(self):
        if self.pool:
            await self.pool.close()

# Global instance
db_pool = DatabasePool()
""",
                example="""
# Usage in FastAPI
@app.on_event("startup")
async def startup():
    await db_pool.init()

@app.on_event("shutdown")
async def shutdown():
    await db_pool.close()

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT * FROM users WHERE id = $1", user_id
        )
        return user
""",
                anti_patterns=[
                    "Creating new connection per request",
                    "No connection pooling",
                    "Hardcoded credentials",
                ],
                when_to_use="Always for production database access",
                when_not_to_use="Simple scripts or one-time operations",
            )
        )

        # Python: Structured logging
        self.patterns["python"].append(
            CodePattern(
                name="structured_logging",
                category="observability",
                language="python",
                description="Production logging with context and correlation",
                template="""
import logging
import json
import sys
from datetime import datetime
from contextvars import ContextVar
from typing import Any, Dict
import traceback

correlation_id: ContextVar[str] = ContextVar('correlation_id', default='')

class StructuredLogger:
    def __init__(self, name: str, level: str = "INFO"):
        self.logger = logging.getLogger(name)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        self.logger.addHandler(handler)
        self.logger.setLevel(getattr(logging, level))

    def _log(self, level: str, message: str, **kwargs):
        extra = {
            'correlation_id': correlation_id.get(),
            'timestamp': datetime.utcnow().isoformat(),
            **kwargs
        }
        getattr(self.logger, level)(message, extra={'structured': extra})

    def info(self, message: str, **kwargs):
        self._log('info', message, **kwargs)

    def error(self, message: str, exception: Exception = None, **kwargs):
        if exception:
            kwargs['error_type'] = type(exception).__name__
            kwargs['error_message'] = str(exception)
            kwargs['stacktrace'] = traceback.format_exc()
        self._log('error', message, **kwargs)

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        if hasattr(record, 'structured'):
            log_obj.update(record.structured)
        return json.dumps(log_obj)

# Usage
logger = StructuredLogger(__name__)
""",
                example="""
# In your API endpoint
@app.post("/orders")
async def create_order(order: OrderInput):
    correlation_id.set(str(uuid4()))

    logger.info("Creating order",
                user_id=order.user_id,
                items=len(order.items),
                total=order.total)

    try:
        result = await process_order(order)
        logger.info("Order created successfully", order_id=result.id)
        return result
    except Exception as e:
        logger.error("Order creation failed", exception=e)
        raise
""",
                anti_patterns=[
                    "print() statements",
                    "Unstructured logs",
                    "No correlation IDs",
                ],
                when_to_use="All production services",
                when_not_to_use="Development debugging (where print is fine)",
            )
        )

        # Python: Retry with exponential backoff
        self.patterns["python"].append(
            CodePattern(
                name="retry_with_backoff",
                category="reliability",
                language="python",
                description="Retry failed operations with exponential backoff",
                template="""
import asyncio
import random
from functools import wraps
from typing import TypeVar, Callable, Optional, Tuple, Type

T = TypeVar('T')

def async_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            attempt = 0
            delay = base_delay

            while attempt < max_attempts:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1

                    if attempt >= max_attempts:
                        logger.error(f"Max retries exceeded for {func.__name__}",
                                   exception=e, attempts=attempt)
                        raise

                    if jitter:
                        delay = delay * (1 + random.random())

                    logger.warning(f"Retry {attempt}/{max_attempts} for {func.__name__}",
                                 delay=delay, error=str(e))

                    await asyncio.sleep(min(delay, max_delay))
                    delay *= exponential_base

            return None  # Should never reach here

        return wrapper
    return decorator
""",
                example="""
@async_retry(max_attempts=3, exceptions=(aiohttp.ClientError,))
async def call_external_api(url: str, data: dict):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data) as response:
            response.raise_for_status()
            return await response.json()
""",
                anti_patterns=[
                    "Infinite retries",
                    "No backoff",
                    "Retry on all exceptions",
                ],
                when_to_use="External API calls, transient failures",
                when_not_to_use="User input validation errors",
            )
        )

    def get_pattern(self, name: str, language: str) -> Optional[CodePattern]:
        """Get a specific pattern"""
        for pattern in self.patterns.get(language, []):
            if pattern.name == name:
                return pattern
        return None

    def get_patterns_for_requirement(self, requirement: str) -> List[CodePattern]:
        """Get all patterns relevant to a requirement"""
        relevant = []
        for lang_patterns in self.patterns.values():
            for pattern in lang_patterns:
                if requirement.lower() in pattern.category.lower():
                    relevant.append(pattern)
        return relevant


class AgentSpecificationBuilder:
    """Builds detailed specifications for agents based on requirements"""

    def __init__(
        self, requirements: ProductionRequirements, pattern_library: PatternLibrary
    ):
        self.requirements = requirements
        self.patterns = pattern_library

    def build_specification(self, agent_type: str, task: str) -> Dict[str, Any]:
        """Build a complete specification for an agent"""

        spec = {
            "agent_type": agent_type,
            "task": task,
            "quality_level": self.requirements.quality_level.value,
            "requirements": {},
            "patterns_to_use": [],
            "validation_criteria": [],
            "examples": [],
        }

        # Add requirements based on agent type
        if agent_type == "backend_developer":
            spec["requirements"] = {
                "database": {
                    "required": self.requirements.database_required,
                    "connection_pooling": self.requirements.connection_pooling,
                    "async_operations": self.requirements.async_operations,
                    "pattern": "async_database_pool",
                },
                "api": {
                    "authentication": self.requirements.authentication_required,
                    "rate_limiting": self.requirements.rate_limiting,
                    "input_validation": self.requirements.input_validation,
                    "error_handling": self.requirements.error_handling_required,
                },
                "observability": {
                    "logging": self.requirements.logging_required,
                    "structured": self.requirements.structured_logging,
                    "pattern": "structured_logging",
                },
                "reliability": {
                    "retry_logic": self.requirements.retry_logic,
                    "pattern": "retry_with_backoff",
                },
            }

            # Add relevant patterns
            spec["patterns_to_use"] = [
                self.patterns.get_pattern("async_database_pool", "python"),
                self.patterns.get_pattern("structured_logging", "python"),
                self.patterns.get_pattern("retry_with_backoff", "python"),
            ]

            # Add validation criteria
            spec["validation_criteria"] = [
                "No hardcoded credentials",
                "All database operations use connection pool",
                "All endpoints have error handling",
                "Structured logging used throughout",
                "Input validation on all endpoints",
                "Async operations for I/O",
                "Environment variables for configuration",
            ]

        elif agent_type == "test_engineer":
            spec["requirements"] = {
                "coverage": {
                    "minimum": self.requirements.test_coverage_minimum,
                    "unit_tests": True,
                    "integration_tests": True,
                    "edge_cases": True,
                },
                "test_types": {
                    "happy_path": True,
                    "error_cases": True,
                    "boundary_conditions": True,
                    "security_tests": self.requirements.authentication_required,
                },
            }

            spec["validation_criteria"] = [
                f"Test coverage >= {self.requirements.test_coverage_minimum}%",
                "All endpoints tested",
                "Error cases covered",
                "Fixtures for test data",
                "Mocked external dependencies",
                "Async test support",
            ]

        return spec

    def generate_agent_prompt(self, spec: Dict[str, Any]) -> str:
        """Generate detailed prompt for agent"""

        prompt = f"""
You are a {spec['agent_type']} creating {spec['quality_level']}-quality code.

TASK: {spec['task']}

MANDATORY REQUIREMENTS:
"""

        # Add requirements
        for category, reqs in spec.get("requirements", {}).items():
            prompt += f"\n{category.upper()}:\n"
            for req, value in reqs.items():
                if value and value != "pattern":
                    prompt += f"  - {req}: {value}\n"

        # Add patterns
        if spec.get("patterns_to_use"):
            prompt += "\n\nUSE THESE PATTERNS:\n"
            for pattern in spec["patterns_to_use"]:
                if pattern:
                    prompt += f"\n{pattern.name}:\n{pattern.template}\n"

        # Add validation criteria
        if spec.get("validation_criteria"):
            prompt += "\n\nYOUR CODE MUST:\n"
            for criteria in spec["validation_criteria"]:
                prompt += f"  ✓ {criteria}\n"

        prompt += "\n\nDO NOT:\n"
        prompt += "  ✗ Use print() for logging\n"
        prompt += "  ✗ Hardcode credentials or secrets\n"
        prompt += "  ✗ Skip error handling\n"
        prompt += "  ✗ Create synchronous database operations\n"
        prompt += "  ✗ Ignore input validation\n"

        return prompt


class ProductionValidator:
    """Validates agent output meets production standards"""

    def __init__(self, requirements: ProductionRequirements):
        self.requirements = requirements
        self.validation_results = []

    def validate_code(self, code: str, language: str) -> Dict[str, Any]:
        """Validate code meets production standards"""

        results = {"valid": True, "issues": [], "warnings": [], "score": 100.0}

        if language == "python":
            # Check for anti-patterns
            if "print(" in code and self.requirements.logging_required:
                results["issues"].append("Uses print() instead of logging")
                results["score"] -= 10

            if "password=" in code or "api_key=" in code:
                if not "os.getenv" in code and not "os.environ" in code:
                    results["issues"].append("Hardcoded credentials detected")
                    results["score"] -= 25
                    results["valid"] = False

            if "except:" in code or "except Exception:" in code:
                results["warnings"].append("Broad exception handling")
                results["score"] -= 5

            if self.requirements.async_operations:
                if "def " in code and not "async def" in code:
                    results["warnings"].append(
                        "Synchronous operations in async context"
                    )
                    results["score"] -= 10

            if self.requirements.database_required:
                if "SELECT" in code or "INSERT" in code:
                    if "$1" not in code and "%s" not in code and "?" not in code:
                        results["issues"].append(
                            "Potential SQL injection vulnerability"
                        )
                        results["score"] -= 20
                        results["valid"] = False

        return results

    def validate_deployment(self, dockerfile: str, k8s_config: str) -> Dict[str, Any]:
        """Validate deployment configurations"""

        results = {"valid": True, "issues": [], "warnings": []}

        # Dockerfile checks
        if dockerfile:
            if "USER" not in dockerfile:
                results["warnings"].append("Container runs as root")

            if "HEALTHCHECK" not in dockerfile:
                results["issues"].append("No health check defined")

            if "FROM" in dockerfile and ":latest" in dockerfile:
                results["warnings"].append("Using :latest tag")

        # K8s checks
        if k8s_config:
            if "limits:" not in k8s_config:
                results["issues"].append("No resource limits defined")

            if "livenessProbe:" not in k8s_config:
                results["issues"].append("No liveness probe")

            if "readinessProbe:" not in k8s_config:
                results["issues"].append("No readiness probe")

        return results


def create_production_system(quality_level: QualityLevel = QualityLevel.PRODUCTION):
    """Create a complete production quality system"""

    # Create requirements based on quality level
    requirements = ProductionRequirements(quality_level=quality_level)

    # Adjust requirements based on level
    if quality_level == QualityLevel.PROTOTYPE:
        requirements.test_coverage_minimum = 0
        requirements.authentication_required = False
        requirements.monitoring_required = False
        requirements.database_required = False
    elif quality_level == QualityLevel.DEVELOPMENT:
        requirements.test_coverage_minimum = 60
        requirements.authentication_required = False
        requirements.circuit_breakers = False
    elif quality_level == QualityLevel.STAGING:
        requirements.test_coverage_minimum = 70
        requirements.distributed_tracing = False

    # Create components
    pattern_library = PatternLibrary()
    spec_builder = AgentSpecificationBuilder(requirements, pattern_library)
    validator = ProductionValidator(requirements)

    return {
        "requirements": requirements,
        "patterns": pattern_library,
        "spec_builder": spec_builder,
        "validator": validator,
    }
