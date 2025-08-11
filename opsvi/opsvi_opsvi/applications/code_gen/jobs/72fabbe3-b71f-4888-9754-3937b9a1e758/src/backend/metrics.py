import asyncio
from datetime import datetime, timedelta
import psutil
from sqlmodel import select, Session
from typing import Any
from backend.models import MetricSample, MetricType
from backend.db import engine
from backend.websocket_manager import ws_manager
from backend.config import settings
import logging

_metrics_state: dict[str, Any] = {"current": {}, "history": {}}
history_length_sec = 3600  # keep 1 hour history in memory for chart querying


async def metrics_collector_task() -> None:
    """Background task for collecting system metrics and storing them in the DB and broadcasting live to websockets."""
    interval = settings.METRICS_COLLECTION_INTERVAL_SEC
    logger = logging.getLogger("metrics_collector")
    while True:
        try:
            now = datetime.utcnow()
            cpu = float(psutil.cpu_percent())
            memory = float(psutil.virtual_memory().percent)
            disk = float(psutil.disk_usage("/").percent)
            net = psutil.net_io_counters()
            network_value = float(net.bytes_sent + net.bytes_recv)

            # Use memory for real-time value
            _metrics_state["current"] = {
                "cpu": cpu,
                "memory": memory,
                "disk": disk,
                "network": network_value,
                "ts": now.isoformat(),
            }
            for mtype, value in [
                (MetricType.cpu, cpu),
                (MetricType.memory, memory),
                (MetricType.disk, disk),
                (MetricType.network, network_value),
            ]:
                msample = MetricSample(metric_type=mtype, value=value, ts=now)
                # Store to DB
                with Session(engine) as session:
                    session.add(msample)
                    session.commit()

                # Simple in-memory history for fast access
                if mtype.value not in _metrics_state["history"]:
                    _metrics_state["history"][mtype.value] = []
                _metrics_state["history"][mtype.value].append(
                    {"ts": now, "value": value}
                )
                # Keep only last N seconds
                _metrics_state["history"][mtype.value] = [
                    item
                    for item in _metrics_state["history"][mtype.value]
                    if item["ts"] > now - timedelta(seconds=history_length_sec)
                ]
            # Broadcast via WebSockets
            await ws_manager.broadcast(
                {"type": "metrics_update", "data": _metrics_state["current"]}
            )
            logger.debug(
                f"Collected metrics at {now.isoformat()}: {_metrics_state['current']}"
            )
        except Exception as exc:
            logger.error(f"Metrics collection error: {exc}")
        await asyncio.sleep(interval)


def get_realtime_metrics() -> dict:
    return _metrics_state["current"]


def get_historical_metrics(
    metric_type: MetricType, start_ts: datetime, end_ts: datetime
) -> list[dict]:
    """Query historical data from DB (TimescaleDB/Postgres)."""
    try:
        with Session(engine) as session:
            stmt = (
                select(MetricSample)
                .where(
                    (MetricSample.metric_type == metric_type)
                    & (MetricSample.ts >= start_ts)
                    & (MetricSample.ts <= end_ts)
                )
                .order_by(MetricSample.ts)
            )
            result = session.exec(stmt).all()
            return [r.dict() for r in result]
    except Exception as exc:
        logging.getLogger("metrics").error(f"Historical metric query failed: {exc}")
        return []
