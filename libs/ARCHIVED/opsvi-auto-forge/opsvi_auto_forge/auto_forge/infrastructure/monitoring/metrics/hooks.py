from __future__ import annotations

import time

from opsvi_auto_forge.infrastructure.monitoring.metrics.decision_metrics import (
    retrieval_latency,
)


def time_retriever(name: str):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            t0 = time.perf_counter()
            try:
                return fn(*args, **kwargs)
            finally:
                dt = (time.perf_counter() - t0) * 1000.0
                retrieval_latency.labels(retriever=name).observe(dt)

        return wrapper

    return decorator
