from typing import Any, Dict, List

from src.applications.specstory_intelligence.agentic_review_schema import (
    AgenticAnnotation,
    Reviewer,
)


def add_annotation(log_object: Dict[str, Any], annotation: AgenticAnnotation):
    """Attach an annotation to the log object (session, turn, tool, event)."""
    if "annotations" not in log_object:
        log_object["annotations"] = []
    log_object["annotations"].append(annotation.to_dict())


def get_annotations(log_object: Dict[str, Any]) -> List[Dict[str, Any]]:
    return log_object.get("annotations", [])


def aggregate_annotations(
    log_object: Dict[str, Any], level: str = None
) -> List[Dict[str, Any]]:
    """Recursively collect all annotations at or below the given log object."""
    annotations = get_annotations(log_object)
    if level is None or (log_object.get("type") == level):
        return annotations
    # Recursively check children
    for key in ["turns", "tools", "events"]:
        if key in log_object:
            for child in log_object[key]:
                annotations.extend(aggregate_annotations(child, level))
    return annotations


def flag_turn_for_review(
    turn: Dict[str, Any],
    reviewer_id: str,
    summary: str,
    details: str,
    categories: List[str] = None,
):
    reviewer = Reviewer(type="human", id=reviewer_id)
    annotation = AgenticAnnotation.create(
        scope_level="turn",
        scope_ref=turn.get("turn_id", ""),
        reviewer=reviewer,
        review_status="flagged",
        categories=categories or ["needs_review"],
        summary=summary,
        details=details,
    )
    add_annotation(turn, annotation)
    return annotation
