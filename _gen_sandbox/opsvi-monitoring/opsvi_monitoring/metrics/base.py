"""Metrics base for opsvi-monitoring.

Provides an asynchronous, extensible in-memory metrics recorder with simple
aggregation and optional labels. This module defines a Metrics class that can
record numeric observations, retrieve aggregated snapshots, and export them
via registered exporter callbacks.
"""
from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Dict, Hashable, Mapping, MutableMapping, Tuple

LabelKey = Tuple[Tuple[str, str], ...]
Exporter = Callable[[Mapping[str, Mapping[str, float]]], None]


def _normalize_labels(labels: Mapping[str, str] | None) -> LabelKey:
    if not labels:
        return tuple()
    # stable ordering for dict -> tuple key
    return tuple(sorted(((k, v) for k, v in labels.items())))


@dataclass
class _Aggregation:
    count: int = 0
    sum: float = 0.0
    min: float = float("inf")
    max: float = float("-inf")

    def update(self, value: float) -> None:
        self.count += 1
        self.sum += value
        if value < self.min:
            self.min = value
        if value > self.max:
            self.max = value

    def snapshot(self) -> Dict[str, float]:
        if self.count == 0:
            return {"count": 0, "sum": 0.0, "min": 0.0, "max": 0.0, "avg": 0.0}
        return {
            "count": float(self.count),
            "sum": float(self.sum),
            "min": float(self.min),
            "max": float(self.max),
            "avg": float(self.sum) / self.count,
        }


class Metrics:
    """Thread-safe asynchronous in-memory metrics recorder.

    Use record(name, value, labels) to record observations. Callers can register
    async exporters (callables) that will be invoked on flush() with a snapshot
    of current aggregated metrics.
    """

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        # mapping: metric name -> labels key -> aggregation
        self._store: Dict[str, Dict[LabelKey, _Aggregation]] = defaultdict(dict)
        self._exporters: Dict[str, Exporter] = {}

    async def record(self, name: str, value: float, labels: Mapping[str, str] | None = None) -> None:
        """Record a numeric observation for a metric name with optional labels.

        This is safe to call concurrently from asyncio tasks.
        """
        key = _normalize_labels(labels)
        async with self._lock:
            bucket = self._store[name].get(key)
            if bucket is None:
                bucket = _Aggregation()
                self._store[name][key] = bucket
            bucket.update(float(value))

    async def snapshot(self) -> Dict[str, Dict[str, float]]:
        """Return a snapshot of aggregated metrics.

        The returned mapping flattens label tuples into a stable string key.
        """
        async with self._lock:
            out: Dict[str, Dict[str, float]] = {}
            for name, buckets in self._store.items():
                for labels_key, agg in buckets.items():
                    label_str = "" if not labels_key else ";".join(f"{k}={v}" for k, v in labels_key)
                    metric_key = name if label_str == "" else f"{name}|{label_str}"
                    out[metric_key] = agg.snapshot()
            return out

    def register_exporter(self, name: str, exporter: Exporter) -> None:
        """Register an exporter callable that will receive snapshots on flush.

        Exporter signature: Callable[[Mapping[str, Mapping[str, float]]], None]
        """
        if not callable(exporter):
            raise TypeError("exporter must be callable")
        self._exporters[name] = exporter

    def unregister_exporter(self, name: str) -> None:
        self._exporters.pop(name, None)

    async def flush(self) -> None:
        """Flush current metrics to all registered exporters and reset store.

        Exporters are invoked synchronously in the event loop; they should be
        fast. If an exporter raises, it will be ignored to avoid blocking other
        exporters.
        """
        snapshot = await self.snapshot()
        # reset store
        async with self._lock:
            self._store = defaultdict(dict)
        # invoke exporters outside lock
        for exporter in list(self._exporters.values()):
            try:
                exporter(snapshot)
            except Exception:
                # intentionally ignore exporter failures
                continue


# small synchronous convenience instance
_default_metrics: Metrics | None = None


def get_default_metrics() -> Metrics:
    """Get a module-level default Metrics instance.

    Lazily constructs a Metrics instance for simple use.
    """
    global _default_metrics
    if _default_metrics is None:
        _default_metrics = Metrics()
    return _default_metrics
