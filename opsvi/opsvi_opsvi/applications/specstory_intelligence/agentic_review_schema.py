from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid


@dataclass
class Reviewer:
    type: str  # 'agent' or 'human'
    id: str
    role: Optional[str] = None


@dataclass
class AgenticAnnotation:
    annotation_id: str
    scope_level: str  # 'session', 'turn', 'tool', 'event'
    scope_ref: str
    reviewer: Reviewer
    timestamp: str
    review_status: str  # 'approved', 'flagged', etc.
    categories: List[str]
    summary: str
    details: str
    suggested_action: Optional[str] = None
    evidence_refs: List[str] = field(default_factory=list)
    child_annotations: List["AgenticAnnotation"] = field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self):
        d = asdict(self)
        d["reviewer"] = asdict(self.reviewer)
        d["child_annotations"] = [c.to_dict() for c in self.child_annotations]
        return d

    @staticmethod
    def create(
        scope_level: str,
        scope_ref: str,
        reviewer: Reviewer,
        review_status: str,
        categories: List[str],
        summary: str,
        details: str,
        suggested_action: Optional[str] = None,
        evidence_refs: Optional[List[str]] = None,
        child_annotations: Optional[List["AgenticAnnotation"]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        return AgenticAnnotation(
            annotation_id=str(uuid.uuid4()),
            scope_level=scope_level,
            scope_ref=scope_ref,
            reviewer=reviewer,
            timestamp=datetime.utcnow().isoformat() + "Z",
            review_status=review_status,
            categories=categories,
            summary=summary,
            details=details,
            suggested_action=suggested_action,
            evidence_refs=evidence_refs or [],
            child_annotations=child_annotations or [],
            metadata=metadata or {},
        )
