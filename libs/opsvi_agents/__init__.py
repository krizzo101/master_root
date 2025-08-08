"""
opsvi_agents: Shared agents and orchestration for OPSVI projects.
"""

__version__ = "0.1.0"

# Convenience re-exports (shims)
try:
    from .consult.optimized_agent import OptimizedConsultAgent  # noqa: F401
except Exception:  # pragma: no cover
    pass
