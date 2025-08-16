import pytest
from ai_collab_task_manager.audit_log import audit_log_event
from ai_collab_task_manager.models import AuditLog


def test_audit_log_event_creates_entry(db_session):
    event = "Test Event"
    user_id = 1
    audit_log_event(event, user_id)
    logs = (
        db_session.query(AuditLog)
        .filter(AuditLog.user_id == user_id, AuditLog.event == event)
        .all()
    )
    assert len(logs) >= 1
    assert logs[-1].event == event
    assert logs[-1].user_id == user_id
