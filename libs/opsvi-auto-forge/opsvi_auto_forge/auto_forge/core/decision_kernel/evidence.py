"""
Evidence Graph Implementation for Decision Kernel

Handles evidence normalization, SHA-256 computation, and Claim/Evidence DTOs.
Cited in AUDIT_action_plan.md: A4 steps & acceptance.
"""

from __future__ import annotations
import hashlib
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from opsvi_auto_forge.infrastructure.monitoring.metrics.decision_metrics import (
    ro_evidence_retrieval_success_total,
)


class EvidenceSpan(BaseModel):
    """Represents a text span within evidence content."""

    start: int = Field(..., description="Start position (0-indexed)")
    end: int = Field(..., description="End position (exclusive)")
    score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")


class Evidence(BaseModel):
    """Evidence item supporting a claim."""

    id: str = Field(..., description="Unique evidence identifier")
    source_type: str = Field(..., description="file, web, code, test, etc.")
    uri: str = Field(..., description="Source URI or path")
    sha256: str = Field(..., description="SHA-256 hash of content")
    score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    span_start: Optional[int] = Field(None, description="Start position in source")
    span_end: Optional[int] = Field(None, description="End position in source")
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Claim(BaseModel):
    """Claim asserted by a decision."""

    id: str = Field(..., description="Unique claim identifier")
    text: str = Field(..., description="Claim text")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    evidence: List[Evidence] = Field(default_factory=list)


def normalize_evidence(content: str, source_type: str, uri: str) -> str:
    """
    Normalize evidence content for consistent hashing.

    Args:
        content: Raw evidence content
        source_type: Type of evidence source
        uri: Source URI

    Returns:
        Normalized content string
    """
    # Remove extra whitespace and normalize line endings
    normalized = content.strip().replace("\r\n", "\n").replace("\r", "\n")

    # Add source metadata for context
    metadata = {
        "source_type": source_type,
        "uri": uri,
        "normalized_at": datetime.utcnow().isoformat(),
    }

    # Combine content with metadata for consistent hashing
    combined = json.dumps(metadata, sort_keys=True) + "\n" + normalized
    return combined


def compute_sha256(content: str) -> str:
    """
    Compute SHA-256 hash of content.

    Args:
        content: Content to hash

    Returns:
        SHA-256 hash string
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def create_evidence(
    id: str,
    content: str,
    source_type: str,
    uri: str,
    score: float,
    span_start: Optional[int] = None,
    span_end: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Evidence:
    """
    Create an evidence item with normalized content and SHA-256 hash.

    Args:
        id: Unique evidence identifier
        content: Raw evidence content
        source_type: Type of evidence source
        uri: Source URI
        score: Relevance score (0.0-1.0)
        span_start: Start position in source
        span_end: End position in source
        metadata: Additional metadata

    Returns:
        Evidence item with computed SHA-256
    """
    # Normalize content for consistent hashing
    normalized_content = normalize_evidence(content, source_type, uri)

    # Compute SHA-256 hash
    sha256_hash = compute_sha256(normalized_content)

    # Create evidence item
    evidence = Evidence(
        id=id,
        source_type=source_type,
        uri=uri,
        sha256=sha256_hash,
        score=score,
        span_start=span_start,
        span_end=span_end,
        metadata=metadata or {},
    )

    # Emit metrics
    try:
        ro_evidence_retrieval_success_total.labels(source_type=source_type).inc()
    except Exception:
        # Metrics may not be initialized in all contexts
        pass

    return evidence


def create_claim(
    id: str, text: str, evidence: Optional[List[Evidence]] = None
) -> Claim:
    """
    Create a claim with optional evidence.

    Args:
        id: Unique claim identifier
        text: Claim text
        evidence: List of supporting evidence

    Returns:
        Claim with evidence
    """
    return Claim(id=id, text=text, evidence=evidence or [])


def validate_evidence_span(evidence: Evidence, content: str) -> bool:
    """
    Validate that evidence spans are within content bounds.

    Args:
        evidence: Evidence item to validate
        content: Content string

    Returns:
        True if spans are valid
    """
    if evidence.span_start is None or evidence.span_end is None:
        return True  # No spans to validate

    if evidence.span_start < 0 or evidence.span_end > len(content):
        return False

    if evidence.span_start >= evidence.span_end:
        return False

    return True


def deduplicate_evidence(evidence_list: List[Evidence]) -> List[Evidence]:
    """
    Remove duplicate evidence items based on SHA-256 hash.

    Args:
        evidence_list: List of evidence items

    Returns:
        Deduplicated list, keeping highest score for duplicates
    """
    seen_hashes = {}
    deduplicated = []

    for evidence in evidence_list:
        if evidence.sha256 in seen_hashes:
            # Keep the one with higher score
            existing = seen_hashes[evidence.sha256]
            if evidence.score > existing.score:
                # Replace existing with higher score
                deduplicated.remove(existing)
                deduplicated.append(evidence)
                seen_hashes[evidence.sha256] = evidence
        else:
            deduplicated.append(evidence)
            seen_hashes[evidence.sha256] = evidence

    return deduplicated
