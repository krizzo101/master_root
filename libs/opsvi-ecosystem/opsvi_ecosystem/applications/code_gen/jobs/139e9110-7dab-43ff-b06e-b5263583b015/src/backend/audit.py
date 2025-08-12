"""
Audit logging with Python (using Winston-like splitting via RotatingFileHandler and DB)
"""
import logging
from backend.models import AuditLog
from backend.database import get_db
from datetime import datetime


def setup_audit_logging(settings):
    logger = logging.getLogger("taskmgmt.audit")
    logger.setLevel(logging.INFO)
    handler = logging.handlers.RotatingFileHandler(
        "audit.log", maxBytes=1048576, backupCount=10
    )
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def log_audit(action: str, user_id: str, entity: str, entity_id: str, meta: str = ""):
    logger = logging.getLogger("taskmgmt.audit")
    logger.info(f"{action} by {user_id} on {entity}:{entity_id} -- {meta}")
    # Optionally write to DB for persistent log
    db = next(get_db())
    audit = AuditLog(
        action=action, user_id=user_id, entity=entity, entity_id=entity_id, meta=meta
    )
    db.add(audit)
    db.commit()
