import asyncio
import logging
from datetime import datetime

from sqlmodel import Session, select

from backend.db import engine
from backend.metrics import _metrics_state
from backend.models import AlertEvent, MetricType, Threshold
from backend.websocket_manager import ws_manager

_active_alerts: dict[str, dict] = {}


async def alert_manager_task():
    """Background task to check metrics vs. thresholds and generate alerts as needed."""
    interval = 1  # seconds
    logger = logging.getLogger("alerts")
    while True:
        try:
            with Session(engine) as session:
                th = session.exec(select(Threshold)).first()
                if not th:
                    th = Threshold()
                    session.add(th)
                    session.commit()
                now = datetime.utcnow()
                metrics = _metrics_state.get("current", {})
                for metric in [
                    MetricType.cpu,
                    MetricType.memory,
                    MetricType.disk,
                    MetricType.network,
                ]:
                    value = float(metrics.get(metric.value, 0.0))
                    threshold = getattr(th, metric.value, None)
                    alert_key = metric.value
                    # Check if value exceeds threshold
                    if threshold is not None and value >= threshold:
                        # If not already active, create alert
                        if alert_key not in _active_alerts:
                            _active_alerts[alert_key] = {
                                "metric_type": metric,
                                "value": value,
                                "triggered_at": now,
                            }
                            event = AlertEvent(
                                metric_type=metric, value=value, triggered_at=now
                            )
                            session.add(event)
                            session.commit()
                            # Notify via WebSocket
                            await ws_manager.broadcast(
                                {
                                    "type": "alert_triggered",
                                    "data": {
                                        "metric_type": metric.value,
                                        "value": value,
                                        "time": now.isoformat(),
                                    },
                                }
                            )
                            logger.info(f"Alert triggered: {metric.value} {value}%")
                    else:
                        # Resolve active alert if value back to normal
                        if alert_key in _active_alerts:
                            alert = _active_alerts.pop(alert_key)
                            # Find and resolve the event
                            evt = session.exec(
                                select(AlertEvent)
                                .where(
                                    (AlertEvent.metric_type == metric)
                                    & (AlertEvent.resolved_at == None)
                                )
                                .order_by(AlertEvent.triggered_at.desc())
                            ).first()
                            if evt:
                                evt.resolved_at = now
                                evt.resolved_value = value
                                session.add(evt)
                                session.commit()
                            # Notify WebSocket clients
                            await ws_manager.broadcast(
                                {
                                    "type": "alert_resolved",
                                    "data": {
                                        "metric_type": metric.value,
                                        "value": value,
                                        "time": now.isoformat(),
                                    },
                                }
                            )
                            logger.info(f"Alert resolved: {metric.value} {value}%")
        except Exception as exc:
            logger.error(f"Alert manager error: {exc}")
        await asyncio.sleep(interval)


def get_active_alerts():
    ret = []
    for alert in _active_alerts.values():
        ret.append(
            {
                "metric_type": alert["metric_type"],
                "value": alert["value"],
                "triggered_at": alert["triggered_at"],
            }
        )
    return ret
