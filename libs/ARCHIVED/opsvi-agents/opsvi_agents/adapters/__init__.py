"""Agent adapters for compatibility."""

from .legacy import UniversalAgentAdapter, migrate_legacy_agent

__all__ = ["UniversalAgentAdapter", "migrate_legacy_agent"]
