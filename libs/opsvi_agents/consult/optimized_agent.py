import logging

try:
    # Reuse existing implementation (shim). Later we will move the class here.
    from accf.agents.consult_agent_optimized import OptimizedConsultAgent  # type: ignore

    logging.getLogger(__name__).info(
        "opsvi_agents.consult: using ACCF OptimizedConsultAgent (shim)"
    )
except Exception as e:  # pragma: no cover
    logging.getLogger(__name__).warning(f"opsvi_agents.consult shim failed: {e}")
    raise
