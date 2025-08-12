from .models import db, AuditLog
from datetime import datetime
import logging


def audit_log_event(event: str, user_id: int) -> None:
    try:
        l = AuditLog(event=event, user_id=user_id, timestamp=datetime.utcnow())
        db.session.add(l)
        db.session.commit()
    except Exception as e:
        logging.getLogger("audit").error(f"Audit log failed: {e}")
