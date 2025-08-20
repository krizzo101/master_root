"""Quality policies for critic evaluation."""

import logging
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from opsvi_auto_forge.config.models import Artifact, Result
from opsvi_auto_forge.infrastructure.memory.graph.client import Neo4jClient
from opsvi_auto_forge.infrastructure.monitoring.metrics.decision_metrics import (
    cost_per_pass_gate,
)
from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger(__name__)


class PolicyResult(BaseModel):
    """Result of a policy evaluation."""

    policy_name: str
    score: float = Field(..., ge=0.0, le=1.0)
    passed: bool
    reasons: List[str] = Field(default_factory=list)
    patch_plan: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        json_encoders={
            UUID: lambda v: str(v),
        }
    )

    @field_validator("score")
    @classmethod
    def validate_score(cls, v: float) -> float:
        """Validate score is between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Score must be between 0 and 1")
        return v


class PolicyDefinition(BaseModel):
    """Definition of a quality policy."""

    name: str
    description: str
    weight: float = Field(..., ge=0.0, le=1.0)
    threshold: float = Field(0.90, ge=0.0, le=1.0)
    enabled: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        json_encoders={
            UUID: lambda v: str(v),
        }
    )

    @field_validator("weight", "threshold")
    @classmethod
    def validate_values(cls, v: float) -> float:
        """Validate weight and threshold values."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Value must be between 0 and 1")
        return v


class PolicyBundle(BaseModel):
    """Bundle of quality policies."""

    name: str
    description: str
    policies: Dict[str, PolicyDefinition] = Field(default_factory=dict)
    overall_threshold: float = Field(0.95, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        json_encoders={
            UUID: lambda v: str(v),
        }
    )

    @field_validator("overall_threshold")
    @classmethod
    def validate_overall_threshold(cls, v: float) -> float:
        """Validate overall threshold."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Overall threshold must be between 0 and 1")
        return v


class QualityGateResult(BaseModel):
    """Result of a quality gate evaluation."""

    gate_name: str
    passed: bool
    overall_score: float
    policy_results: List[PolicyResult]
    repair_attempts: int = 0
    max_repair_attempts: int = 3
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        json_encoders={
            UUID: lambda v: str(v),
        }
    )


class BasePolicy:
    """Base class for quality policies."""

    def __init__(
        self,
        name: str,
        description: str = "",
        weight: float = 1.0,
        enabled: bool = True,
    ):
        self.name = name
        self.description = description
        self.weight = weight
        self.enabled = enabled

    async def evaluate(
        self, artifact: Artifact, result: Result, context: dict
    ) -> PolicyResult:
        """Evaluate the artifact against this policy."""
        raise NotImplementedError

    def _extract_content(self, artifact: Artifact) -> str:
        """Extract content from artifact metadata."""
        content = artifact.metadata.get("content", "")
        if isinstance(content, (dict, list)):
            content = str(content)
        return str(content)


class SpecQualityPolicy(BasePolicy):
    """Policy for evaluating specification quality."""

    def __init__(self):
        super().__init__(
            "spec_quality",
            "Evaluates specification quality including API endpoints, auth, error handling, rate limiting, and performance SLOs",
            weight=0.15,
            enabled=True,
        )

    async def evaluate(
        self, artifact: Artifact, result: Result, context: dict
    ) -> PolicyResult:
        """Evaluate specification quality."""
        content = self._extract_content(artifact)

        # Check for specification indicators
        score = 0.0
        reasons = []
        patch_plan = []

        # Check for API endpoints
        if "endpoint" in content.lower() or "route" in content.lower():
            score += 0.2
            reasons.append("Contains API endpoint definitions")
        else:
            patch_plan.append("Add API endpoint definitions")

        # Check for authentication
        if "auth" in content.lower() or "authentication" in content.lower():
            score += 0.2
            reasons.append("Includes authentication mechanisms")
        else:
            patch_plan.append("Add authentication specifications")

        # Check for error handling
        if "error" in content.lower() or "exception" in content.lower():
            score += 0.2
            reasons.append("Includes error handling")
        else:
            patch_plan.append("Add error handling specifications")

        # Check for rate limiting
        if "rate" in content.lower() or "limit" in content.lower():
            score += 0.2
            reasons.append("Includes rate limiting")
        else:
            patch_plan.append("Add rate limiting specifications")

        # Check for performance SLOs
        if "performance" in content.lower() or "latency" in content.lower():
            score += 0.2
            reasons.append("Includes performance SLOs")
        else:
            patch_plan.append("Add performance SLOs")

        passed = score >= 0.8

        return PolicyResult(
            policy_name=self.name,
            score=score,
            passed=passed,
            reasons=reasons,
            patch_plan=patch_plan,
        )


class ArchitectureQualityPolicy(BasePolicy):
    """Policy for evaluating architecture quality."""

    def __init__(self):
        super().__init__(
            "architecture_quality",
            "Evaluates architecture quality including layered design, dependency injection, observability, and CI/CD",
            weight=0.20,
            enabled=True,
        )

    async def evaluate(
        self, artifact: Artifact, result: Result, context: dict
    ) -> PolicyResult:
        """Evaluate architecture quality."""
        content = self._extract_content(artifact)

        score = 0.0
        reasons = []
        patch_plan = []

        # Check for layered architecture
        if "layer" in content.lower() or "tier" in content.lower():
            score += 0.25
            reasons.append("Defines layered architecture")
        else:
            patch_plan.append("Define layered architecture")

        # Check for dependency injection
        if "di" in content.lower() or "dependency" in content.lower():
            score += 0.25
            reasons.append("Includes dependency injection")
        else:
            patch_plan.append("Add dependency injection")

        # Check for observability
        if (
            "log" in content.lower()
            or "metric" in content.lower()
            or "trace" in content.lower()
        ):
            score += 0.25
            reasons.append("Includes observability")
        else:
            patch_plan.append("Add observability (logs, metrics, traces)")

        # Check for CI/CD
        if (
            "ci" in content.lower()
            or "cd" in content.lower()
            or "pipeline" in content.lower()
        ):
            score += 0.25
            reasons.append("Includes CI/CD considerations")
        else:
            patch_plan.append("Add CI/CD pipeline specifications")

        passed = score >= 0.8

        return PolicyResult(
            policy_name=self.name,
            score=score,
            passed=passed,
            reasons=reasons,
            patch_plan=patch_plan,
        )


class CodeQualityPolicy(BasePolicy):
    """Policy for evaluating code quality."""

    def __init__(self):
        super().__init__(
            "code_quality",
            "Evaluates code quality including type annotations, error handling, documentation, and logging",
            weight=0.20,
            enabled=True,
        )

    async def evaluate(
        self, artifact: Artifact, result: Result, context: dict
    ) -> PolicyResult:
        """Evaluate code quality."""
        content = self._extract_content(artifact)

        score = 0.0
        reasons = []
        patch_plan = []

        # Check for type annotations
        if ":" in content and ("def " in content or "class " in content):
            score += 0.25
            reasons.append("Uses type annotations")
        else:
            patch_plan.append("Add type annotations")

        # Check for error handling
        if "try:" in content or "except" in content:
            score += 0.25
            reasons.append("Includes error handling")
        else:
            patch_plan.append("Add try-except blocks")

        # Check for documentation
        if '"""' in content or "'''" in content:
            score += 0.25
            reasons.append("Includes documentation")
        else:
            patch_plan.append("Add docstrings")

        # Check for logging
        if "log" in content.lower():
            score += 0.25
            reasons.append("Includes logging")
        else:
            patch_plan.append("Add logging statements")

        passed = score >= 0.8

        return PolicyResult(
            policy_name=self.name,
            score=score,
            passed=passed,
            reasons=reasons,
            patch_plan=patch_plan,
        )


class TestQualityPolicy(BasePolicy):
    """Policy for evaluating test quality."""

    def __init__(self):
        super().__init__(
            "test_quality",
            "Evaluates test quality including test coverage, assertions, and test structure",
            weight=0.15,
            enabled=True,
        )

    async def evaluate(
        self, artifact: Artifact, result: Result, context: dict
    ) -> PolicyResult:
        """Evaluate test quality."""
        content = self._extract_content(artifact)

        score = 0.0
        reasons = []
        patch_plan = []

        # Check for test functions
        if "def test_" in content or "def test" in content:
            score += 0.33
            reasons.append("Contains test functions")
        else:
            patch_plan.append("Add test functions")

        # Check for assertions
        if "assert" in content:
            score += 0.33
            reasons.append("Includes assertions")
        else:
            patch_plan.append("Add assertions")

        # Check for test coverage
        if "coverage" in content.lower():
            score += 0.34
            reasons.append("Mentions test coverage")
        else:
            patch_plan.append("Add test coverage requirements")

        passed = score >= 0.8

        return PolicyResult(
            policy_name=self.name,
            score=score,
            passed=passed,
            reasons=reasons,
            patch_plan=patch_plan,
        )


class SecurityPolicy(BasePolicy):
    """Policy for evaluating security."""

    def __init__(self):
        super().__init__(
            "security",
            "Evaluates security quality including input validation, authentication, and authorization",
            weight=0.15,
            enabled=True,
        )

    async def evaluate(
        self, artifact: Artifact, result: Result, context: dict
    ) -> PolicyResult:
        """Evaluate security."""
        content = self._extract_content(artifact)

        score = 0.0
        reasons = []
        patch_plan = []

        # Check for input validation
        if "validate" in content.lower() or "sanitize" in content.lower():
            score += 0.33
            reasons.append("Includes input validation")
        else:
            patch_plan.append("Add input validation")

        # Check for authentication
        if "auth" in content.lower() or "login" in content.lower():
            score += 0.33
            reasons.append("Includes authentication")
        else:
            patch_plan.append("Add authentication")

        # Check for authorization
        if "permission" in content.lower() or "role" in content.lower():
            score += 0.34
            reasons.append("Includes authorization")
        else:
            patch_plan.append("Add authorization")

        passed = score >= 0.8

        return PolicyResult(
            policy_name=self.name,
            score=score,
            passed=passed,
            reasons=reasons,
            patch_plan=patch_plan,
        )


class PerformancePolicy(BasePolicy):
    """Policy for evaluating performance."""

    def __init__(self):
        super().__init__(
            "performance",
            "Evaluates performance quality including caching, async patterns, and monitoring",
            weight=0.10,
            enabled=True,
        )

    async def evaluate(
        self, artifact: Artifact, result: Result, context: dict
    ) -> PolicyResult:
        """Evaluate performance."""
        content = self._extract_content(artifact)

        score = 0.0
        reasons = []
        patch_plan = []

        # Check for caching
        if "cache" in content.lower():
            score += 0.33
            reasons.append("Includes caching")
        else:
            patch_plan.append("Add caching mechanisms")

        # Check for async/await
        if "async" in content or "await" in content:
            score += 0.33
            reasons.append("Uses async/await")
        else:
            patch_plan.append("Add async/await patterns")

        # Check for performance monitoring
        if "monitor" in content.lower() or "metric" in content.lower():
            score += 0.34
            reasons.append("Includes performance monitoring")
        else:
            patch_plan.append("Add performance monitoring")

        passed = score >= 0.8

        return PolicyResult(
            policy_name=self.name,
            score=score,
            passed=passed,
            reasons=reasons,
            patch_plan=patch_plan,
        )


class PolicyManager:
    """Manager for quality policies and gates."""

    def __init__(self, neo4j_client: Optional[Neo4jClient] = None):
        """Initialize the policy manager."""
        self.neo4j_client = neo4j_client
        self.policies: Dict[str, BasePolicy] = {}
        self._load_default_policies()

    def _load_default_policies(self) -> None:
        """Load default quality policies."""
        self.policies = {
            "spec_quality": SpecQualityPolicy(),
            "architecture_quality": ArchitectureQualityPolicy(),
            "code_quality": CodeQualityPolicy(),
            "test_quality": TestQualityPolicy(),
            "security": SecurityPolicy(),
            "performance": PerformancePolicy(),
        }

    async def evaluate_artifact(
        self, artifact: Artifact, result: Result, context: Dict[str, Any]
    ) -> List[PolicyResult]:
        """Evaluate an artifact against all enabled policies."""
        policy_results = []

        for policy_name, policy in self.policies.items():
            if policy.enabled:
                try:
                    result = await policy.evaluate(artifact, result, context)
                    policy_results.append(result)
                except Exception as e:
                    logger.error(f"Policy {policy_name} evaluation failed: {e}")
                    # Create failed result
                    failed_result = PolicyResult(
                        policy_name=policy_name,
                        score=0.0,
                        passed=False,
                        reasons=[f"Policy evaluation failed: {e}"],
                        patch_plan=[],
                    )
                    policy_results.append(failed_result)

        return policy_results

    async def calculate_overall_score(
        self, policy_results: List[PolicyResult]
    ) -> Tuple[float, bool]:
        """Calculate overall score from policy results."""
        if not policy_results:
            return 0.0, False

        total_weight = 0.0
        weighted_score = 0.0

        for result in policy_results:
            # Find corresponding policy for weight
            policy = self.policies.get(result.policy_name)
            weight = policy.weight if policy else 1.0

            total_weight += weight
            weighted_score += result.score * weight

        if total_weight == 0:
            return 0.0, False

        overall_score = weighted_score / total_weight
        passed = overall_score >= 0.95  # Overall threshold

        return overall_score, passed

    async def enforce_quality_gates(
        self,
        artifact: Artifact,
        result: Result,
        context: Dict[str, Any],
        quality_gates: Dict[str, float],
        max_repair_attempts: int = 3,
    ) -> QualityGateResult:
        """Enforce quality gates with auto-repair capability."""
        repair_attempts = 0
        policy_results = []

        while repair_attempts <= max_repair_attempts:
            # Evaluate policies
            policy_results = await self.evaluate_artifact(artifact, result, context)

            # Calculate overall score
            overall_score, passed = await self.calculate_overall_score(policy_results)

            # Check against quality gates
            gate_passed = True
            for gate_name, threshold in quality_gates.items():
                if overall_score < threshold:
                    gate_passed = False
                    break

            if gate_passed:
                # Quality gates passed
                # Emit cost metric for passed gates
                for gate_name, threshold in quality_gates.items():
                    cost_per_pass_gate.labels(gate=gate_name).set(
                        context.get("cost_usd", 0.0)
                    )

                return QualityGateResult(
                    gate_name="overall",
                    passed=True,
                    overall_score=overall_score,
                    policy_results=policy_results,
                    repair_attempts=repair_attempts,
                    max_repair_attempts=max_repair_attempts,
                )

            # Quality gates failed, attempt repair
            if repair_attempts < max_repair_attempts:
                repair_attempts += 1
                logger.info(
                    f"Quality gates failed, attempting repair {repair_attempts}/{max_repair_attempts}"
                )

                # Attempt auto-repair
                repair_success = await self._attempt_repair(
                    artifact, result, policy_results, context
                )
                if not repair_success:
                    logger.warning(f"Auto-repair attempt {repair_attempts} failed")
            else:
                # Max repair attempts reached
                logger.error(
                    f"Quality gates failed after {max_repair_attempts} repair attempts"
                )
                break

        # Quality gates failed
        return QualityGateResult(
            gate_name="overall",
            passed=False,
            overall_score=overall_score,
            policy_results=policy_results,
            repair_attempts=repair_attempts,
            max_repair_attempts=max_repair_attempts,
        )

    async def _attempt_repair(
        self,
        artifact: Artifact,
        result: Result,
        policy_results: List[PolicyResult],
        context: Dict[str, Any],
    ) -> bool:
        """Attempt to repair failed quality gates."""
        try:
            # Collect all patch plans
            all_patches = []
            for policy_result in policy_results:
                if not policy_result.passed:
                    all_patches.extend(policy_result.patch_plan)

            if not all_patches:
                return False

            # Apply patches (simplified - in real implementation, this would trigger agent repair)
            logger.info(f"Applying {len(all_patches)} patches for quality gate repair")

            # For now, just log the patches
            for patch in all_patches:
                logger.info(f"Patch: {patch}")

            # In a real implementation, this would:
            # 1. Create a repair task
            # 2. Send to appropriate agent
            # 3. Update artifact with repaired content
            # 4. Return success/failure

            return True  # Simplified - assume repair succeeds

        except Exception as e:
            logger.error(f"Repair attempt failed: {e}")
            return False

    async def _persist_policy_result(
        self, policy_result: PolicyResult, artifact_id: UUID
    ) -> None:
        """Persist policy result to Neo4j."""
        if not self.neo4j_client:
            return

        try:
            query = """
            MATCH (a:Artifact {id: $artifact_id})
            CREATE (pr:PolicyResult {
                policy_name: $policy_name,
                score: $score,
                passed: $passed,
                reasons: $reasons,
                patch_plan: $patch_plan,
                metadata: $metadata,
                created_at: datetime()
            })
            CREATE (pr)-[:EVALUATES]->(a)
            """

            await self.neo4j_client.execute_write_query(
                query,
                {
                    "artifact_id": str(artifact_id),
                    "policy_name": policy_result.policy_name,
                    "score": policy_result.score,
                    "passed": policy_result.passed,
                    "reasons": policy_result.reasons,
                    "patch_plan": policy_result.patch_plan,
                    "metadata": policy_result.metadata,
                },
            )

        except Exception as e:
            logger.error(f"Failed to persist policy result: {e}")

    async def get_policy_statistics(self) -> Dict[str, Any]:
        """Get policy evaluation statistics."""
        if not self.neo4j_client:
            return {}

        try:
            query = """
            MATCH (pr:PolicyResult)
            RETURN pr.policy_name as policy_name,
                   count(*) as total_evaluations,
                   avg(pr.score) as avg_score,
                   sum(CASE WHEN pr.passed THEN 1 ELSE 0 END) as passed_count
            """

            results = await self.neo4j_client.execute_read(query)

            stats = {}
            for result in results:
                policy_name = result["policy_name"]
                stats[policy_name] = {
                    "total_evaluations": result["total_evaluations"],
                    "avg_score": result["avg_score"],
                    "passed_count": result["passed_count"],
                    "pass_rate": result["passed_count"] / result["total_evaluations"]
                    if result["total_evaluations"] > 0
                    else 0,
                }

            return stats

        except Exception as e:
            logger.error(f"Failed to get policy statistics: {e}")
            return {}
