import logging

import pytest
from backend.audit import log_audit, setup_audit_logging


@pytest.fixture
def caplog_setup(caplog):
    caplog.set_level(logging.INFO)
    return caplog


def test_setup_audit_logging_configures_logger():
    settings = {"audit_logging_enabled": True}
    setup_audit_logging(settings)
    # No exception means success


def test_log_audit_emits_log_message(caplog_setup):
    action = "create_task"
    user_id = "user123"
    entity = "task"
    entity_id = "task789"
    meta = {"priority": "high"}
    log_audit(action, user_id, entity, entity_id, meta)
    assert any(action in record.message for record in caplog_setup.records)
    assert any(user_id in record.message for record in caplog_setup.records)
