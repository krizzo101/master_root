import logging

try:
    # Bridge to current ACCF orchestrator until full migration
    from accf.orchestrator.core.orchestrator import ConsultFlow  # type: ignore

    logging.getLogger(__name__).info(
        "opsvi_agents.orchestrator: using ACCF ConsultFlow (shim)"
    )
except Exception as e:  # pragma: no cover
    logging.getLogger(__name__).warning(f"opsvi_agents.orchestrator shim failed: {e}")
    raise
