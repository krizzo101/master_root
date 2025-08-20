from __future__ import annotations

from datetime import datetime


def calculate_freshness_score(snippet, freshness_days: int = 90) -> float:
    """Calculate freshness score for a snippet.

    Args:
        snippet: Snippet object
        freshness_days: Number of days to consider "fresh"

    Returns:
        Freshness score between 0.0 and 1.0
    """
    # For now, use a simplified freshness calculation
    # In a real implementation, you'd extract timestamps from snippets

    # Assume recent content has higher freshness
    # This is a placeholder - in practice you'd parse timestamps from metadata
    base_score = 0.7  # Default freshness score

    # If snippet has metadata with timestamp, use it
    if hasattr(snippet, "metadata") and snippet.metadata:
        timestamp_str = snippet.metadata.get("timestamp")
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
                days_old = (datetime.utcnow() - timestamp).days

                # Calculate freshness: newer content gets higher score
                if days_old <= freshness_days:
                    freshness_score = 1.0 - (days_old / freshness_days)
                else:
                    freshness_score = 0.1  # Very old content gets low score

                return max(0.1, freshness_score)

            except (ValueError, TypeError):
                pass

    # If no timestamp available, return base score
    return base_score


def is_recent_content(snippet, days_threshold: int = 30) -> bool:
    """Check if content is recent based on threshold."""
    freshness = calculate_freshness_score(snippet, days_threshold)
    return freshness > 0.5


def get_freshness_weight(age_days: int, max_days: int = 90) -> float:
    """Get freshness weight based on content age.

    Args:
        age_days: Age of content in days
        max_days: Maximum age to consider

    Returns:
        Weight between 0.0 and 1.0
    """
    if age_days <= 0:
        return 1.0
    elif age_days >= max_days:
        return 0.1
    else:
        # Exponential decay
        return 0.1 + 0.9 * (1.0 - (age_days / max_days) ** 2)
