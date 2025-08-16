from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

Strategy = Literal[
    "single", "self_consistency", "solver_verifier", "tot", "debate", "reflexion"
]


class RouteDecision(BaseModel):
    task_id: UUID
    strategy: Strategy = "single"
    model: str = "o4-mini"
    temperature: float = 0.1
    k_samples: int = 1
    max_thoughts: int = 0
    verifier_model: Optional[str] = None
    p_pass: float = 0.0
    confidence: float = 0.0
    reason: str = ""
    params: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Cost and latency tracking
    cost_actual_usd: float = 0.0
    latency_actual_ms: int = 0
    tokens_used: int = 0

    # Analysis metadata
    complexity: float = 0.0
    risk: float = 0.0
    expected_cost_usd: float = 0.0
    latency_target_ms: int = 30_000

    # Escalation tracking
    escalation_count: int = 0
    escalation_path: List[str] = Field(default_factory=list)

    # Performance tracking
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    success: bool = False
    error_message: Optional[str] = None


class Claim(BaseModel):
    id: Optional[str] = None
    text: str
    hash: Optional[str] = None


class Evidence(BaseModel):
    id: Optional[str] = None
    source_type: str  # file | web | code | test | note
    uri: Optional[str] = None
    sha256: Optional[str] = None
    span_start: Optional[int] = None
    span_end: Optional[int] = None
    score: float = 0.0
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)


class Verification(BaseModel):
    id: Optional[str] = None
    method: str  # schema | verifier_model | tests
    passed: bool = False
    score: float = 0.0
    details: str = ""
    agreement_rate: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Verification metadata
    verifier_model: Optional[str] = None
    verification_duration_ms: int = 0
    repair_attempts: int = 0


class DecisionRecord(BaseModel):
    decision: RouteDecision
    claims: List[Claim] = []
    evidence: List[Evidence] = []
    verifications: List[Verification] = []

    # Persistence metadata
    neo4j_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def to_neo4j_props(self) -> Dict[str, Any]:
        """Convert to Neo4j properties for persistence."""
        return {
            "task_id": str(self.decision.task_id),
            "strategy": self.decision.strategy,
            "model": self.decision.model,
            "temperature": self.decision.temperature,
            "k_samples": self.decision.k_samples,
            "max_thoughts": self.decision.max_thoughts,
            "verifier_model": self.decision.verifier_model,
            "p_pass": self.decision.p_pass,
            "confidence": self.decision.confidence,
            "reason": self.decision.reason,
            "cost_actual_usd": self.decision.cost_actual_usd,
            "latency_actual_ms": self.decision.latency_actual_ms,
            "tokens_used": self.decision.tokens_used,
            "complexity": self.decision.complexity,
            "risk": self.decision.risk,
            "expected_cost_usd": self.decision.expected_cost_usd,
            "latency_target_ms": self.decision.latency_target_ms,
            "escalation_count": self.decision.escalation_count,
            "escalation_path": self.decision.escalation_path,
            "success": self.decision.success,
            "error_message": self.decision.error_message,
            "start_time": self.decision.start_time.isoformat()
            if self.decision.start_time
            else None,
            "end_time": self.decision.end_time.isoformat()
            if self.decision.end_time
            else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_neo4j_props(cls, props: Dict[str, Any]) -> "DecisionRecord":
        """Create from Neo4j properties."""
        decision = RouteDecision(
            task_id=UUID(props["task_id"]),
            strategy=props["strategy"],
            model=props["model"],
            temperature=props["temperature"],
            k_samples=props["k_samples"],
            max_thoughts=props["max_thoughts"],
            verifier_model=props["verifier_model"],
            p_pass=props["p_pass"],
            confidence=props["confidence"],
            reason=props["reason"],
            cost_actual_usd=props["cost_actual_usd"],
            latency_actual_ms=props["latency_actual_ms"],
            tokens_used=props["tokens_used"],
            complexity=props["complexity"],
            risk=props["risk"],
            expected_cost_usd=props["expected_cost_usd"],
            latency_target_ms=props["latency_target_ms"],
            escalation_count=props["escalation_count"],
            escalation_path=props["escalation_path"],
            success=props["success"],
            error_message=props["error_message"],
            start_time=datetime.fromisoformat(props["start_time"])
            if props["start_time"]
            else None,
            end_time=datetime.fromisoformat(props["end_time"])
            if props["end_time"]
            else None,
        )

        return cls(
            decision=decision,
            neo4j_id=props.get("id"),
            created_at=datetime.fromisoformat(props["created_at"]),
            updated_at=datetime.fromisoformat(props["updated_at"]),
        )


class DecisionLifecycle:
    """Manages the complete lifecycle of a decision."""

    def __init__(self, decision: RouteDecision):
        """Initialize with a decision."""
        self.decision = decision
        self.record = DecisionRecord(decision=decision)
        self.start_time = None
        self.end_time = None

    def start_execution(self) -> None:
        """Mark the start of decision execution."""
        self.start_time = datetime.utcnow()
        self.decision.start_time = self.start_time

    def complete_execution(
        self,
        success: bool,
        cost_usd: float = 0.0,
        latency_ms: int = 0,
        tokens_used: int = 0,
        error_message: Optional[str] = None,
    ) -> None:
        """Mark the completion of decision execution."""
        self.end_time = datetime.utcnow()
        self.decision.end_time = self.end_time
        self.decision.success = success
        self.decision.cost_actual_usd = cost_usd
        self.decision.latency_actual_ms = latency_ms
        self.decision.tokens_used = tokens_used
        self.decision.error_message = error_message

        # Update record
        self.record.decision = self.decision
        self.record.updated_at = datetime.utcnow()

    def add_escalation(self, from_model: str, to_model: str) -> None:
        """Record an escalation event."""
        self.decision.escalation_count += 1
        self.decision.escalation_path.append(f"{from_model}->{to_model}")

    def add_verification(self, verification: Verification) -> None:
        """Add a verification result."""
        self.record.verifications.append(verification)

    def add_evidence(self, evidence: Evidence) -> None:
        """Add evidence to the decision."""
        self.record.evidence.append(evidence)

    def add_claim(self, claim: Claim) -> None:
        """Add a claim to the decision."""
        self.record.claims.append(claim)

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the decision."""
        return {
            "task_id": str(self.decision.task_id),
            "strategy": self.decision.strategy,
            "model": self.decision.model,
            "success": self.decision.success,
            "cost_actual_usd": self.decision.cost_actual_usd,
            "latency_actual_ms": self.decision.latency_actual_ms,
            "tokens_used": self.decision.tokens_used,
            "complexity": self.decision.complexity,
            "risk": self.decision.risk,
            "confidence": self.decision.confidence,
            "escalation_count": self.decision.escalation_count,
            "verification_count": len(self.record.verifications),
            "evidence_count": len(self.record.evidence),
            "claim_count": len(self.record.claims),
        }
