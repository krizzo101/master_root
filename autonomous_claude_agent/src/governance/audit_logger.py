"""
Comprehensive audit logging system for autonomous agent operations.

Provides tamper-proof, cryptographically signed audit trails with
detailed tracking of all agent actions, decisions, and system events.
"""

import json
import hashlib
import hmac
import os
import sqlite3
import threading
from typing import Dict, Optional, List, Any, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import gzip
import shutil
from pathlib import Path


class AuditSeverity(Enum):
    """Severity levels for audit events."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    SECURITY = "security"  # Special category for security events


class EventCategory(Enum):
    """Categories of audit events."""

    SYSTEM = "system"
    OPERATION = "operation"
    APPROVAL = "approval"
    RESOURCE = "resource"
    SAFETY = "safety"
    SECURITY = "security"
    PERFORMANCE = "performance"
    ERROR = "error"


@dataclass
class AuditEvent:
    """Represents a single audit event."""

    event_id: str
    timestamp: datetime
    event_type: str
    category: EventCategory
    severity: AuditSeverity
    actor: str  # Who/what triggered the event
    details: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    hash_value: Optional[str] = None
    signature: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "category": self.category.value,
            "severity": self.severity.value,
            "actor": self.actor,
            "details": self.details,
            "metadata": self.metadata,
            "hash_value": self.hash_value,
            "signature": self.signature,
        }

    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict(), default=str)


class AuditLogger:
    """
    Tamper-proof audit logging system with cryptographic integrity
    verification and comprehensive event tracking.
    """

    def __init__(
        self,
        log_dir: str = "./audit_logs",
        db_path: Optional[str] = None,
        secret_key: Optional[str] = None,
        enable_encryption: bool = True,
        enable_compression: bool = True,
        rotation_size_mb: int = 100,
        retention_days: int = 90,
    ):
        """
        Initialize audit logger.

        Args:
            log_dir: Directory for audit log files
            db_path: Optional path to SQLite database for structured storage
            secret_key: Secret key for HMAC signatures
            enable_encryption: Whether to encrypt sensitive data
            enable_compression: Whether to compress old logs
            rotation_size_mb: Size threshold for log rotation
            retention_days: Days to retain audit logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = db_path or str(self.log_dir / "audit.db")
        self.secret_key = secret_key or self._generate_secret_key()
        self.enable_encryption = enable_encryption
        self.enable_compression = enable_compression
        self.rotation_size_mb = rotation_size_mb
        self.retention_days = retention_days

        # Thread safety
        self.lock = threading.Lock()

        # Event counter for unique IDs
        self.event_counter = 0

        # Initialize database
        self._init_database()

        # Current log file
        self.current_log_file = self._get_current_log_file()

        # Chain hash for tamper detection
        self.last_hash = self._get_last_hash()

        # Statistics
        self.stats = {
            "total_events": 0,
            "events_by_severity": {},
            "events_by_category": {},
            "errors_logged": 0,
        }

    def _generate_secret_key(self) -> str:
        """Generate a secret key for HMAC signatures."""
        # In production, this should be loaded from secure storage
        return hashlib.sha256(os.urandom(32)).hexdigest()

    def _init_database(self) -> None:
        """Initialize SQLite database for structured audit storage."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Create audit events table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id TEXT PRIMARY KEY,
                    timestamp TIMESTAMP,
                    event_type TEXT,
                    category TEXT,
                    severity TEXT,
                    actor TEXT,
                    details TEXT,
                    metadata TEXT,
                    hash_value TEXT,
                    signature TEXT,
                    previous_hash TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create indices for efficient querying
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON audit_events(timestamp)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_severity 
                ON audit_events(severity)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_category 
                ON audit_events(category)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_actor 
                ON audit_events(actor)
            """
            )

            # Create integrity check table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS integrity_checks (
                    check_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    check_time TIMESTAMP,
                    total_events INTEGER,
                    valid_events INTEGER,
                    invalid_events INTEGER,
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            conn.commit()

    def _get_current_log_file(self) -> Path:
        """Get current log file path with rotation support."""
        date_str = datetime.now().strftime("%Y%m%d")
        base_name = f"audit_{date_str}"

        # Find latest file for today
        existing_files = list(self.log_dir.glob(f"{base_name}_*.log"))

        if existing_files:
            # Check size of latest file
            latest_file = max(existing_files, key=lambda f: f.name)

            if latest_file.stat().st_size < self.rotation_size_mb * 1024 * 1024:
                return latest_file

            # Need to rotate
            counter = len(existing_files) + 1
        else:
            counter = 1

        return self.log_dir / f"{base_name}_{counter:03d}.log"

    def _get_last_hash(self) -> str:
        """Get the hash of the last logged event for chaining."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT hash_value FROM audit_events 
                ORDER BY created_at DESC LIMIT 1
            """
            )
            result = cursor.fetchone()

            if result:
                return result[0]

            # Genesis hash
            return hashlib.sha256(b"GENESIS").hexdigest()

    def _calculate_hash(self, event: AuditEvent, previous_hash: str) -> str:
        """Calculate hash for an event including chain hash."""
        hash_input = f"{event.event_id}{event.timestamp.isoformat()}"
        hash_input += f"{event.event_type}{event.category.value}"
        hash_input += f"{event.severity.value}{event.actor}"
        hash_input += json.dumps(event.details, sort_keys=True)
        hash_input += previous_hash

        return hashlib.sha256(hash_input.encode()).hexdigest()

    def _sign_event(self, event: AuditEvent) -> str:
        """Create HMAC signature for event."""
        message = event.to_json().encode()
        signature = hmac.new(self.secret_key.encode(), message, hashlib.sha256).hexdigest()
        return signature

    def log_event(
        self,
        event_type: str,
        details: Dict[str, Any],
        severity: Union[str, AuditSeverity] = AuditSeverity.INFO,
        category: Optional[EventCategory] = None,
        actor: str = "system",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Log an audit event.

        Args:
            event_type: Type of event
            details: Event details
            severity: Event severity level
            category: Event category
            actor: Who/what triggered the event
            metadata: Additional metadata

        Returns:
            Event ID
        """
        with self.lock:
            # Generate event ID
            self.event_counter += 1
            event_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{self.event_counter:06d}"

            # Convert severity if string
            if isinstance(severity, str):
                severity = AuditSeverity(severity.lower())

            # Auto-categorize if not provided
            if category is None:
                category = self._auto_categorize(event_type)

            # Create event
            event = AuditEvent(
                event_id=event_id,
                timestamp=datetime.now(),
                event_type=event_type,
                category=category,
                severity=severity,
                actor=actor,
                details=details,
                metadata=metadata or {},
            )

            # Calculate hash and signature
            event.hash_value = self._calculate_hash(event, self.last_hash)
            event.signature = self._sign_event(event)

            # Write to file
            self._write_to_file(event)

            # Write to database
            self._write_to_database(event)

            # Update chain hash
            self.last_hash = event.hash_value

            # Update statistics
            self._update_statistics(event)

            return event_id

    def _auto_categorize(self, event_type: str) -> EventCategory:
        """Auto-categorize event based on type."""
        event_type_lower = event_type.lower()

        if "approval" in event_type_lower:
            return EventCategory.APPROVAL
        elif "resource" in event_type_lower or "limit" in event_type_lower:
            return EventCategory.RESOURCE
        elif "safety" in event_type_lower or "violation" in event_type_lower:
            return EventCategory.SAFETY
        elif "security" in event_type_lower or "auth" in event_type_lower:
            return EventCategory.SECURITY
        elif "error" in event_type_lower or "exception" in event_type_lower:
            return EventCategory.ERROR
        elif "performance" in event_type_lower or "metric" in event_type_lower:
            return EventCategory.PERFORMANCE
        elif "operation" in event_type_lower or "action" in event_type_lower:
            return EventCategory.OPERATION
        else:
            return EventCategory.SYSTEM

    def _write_to_file(self, event: AuditEvent) -> None:
        """Write event to log file."""
        # Check rotation
        if self.current_log_file.exists():
            size_mb = self.current_log_file.stat().st_size / (1024 * 1024)
            if size_mb >= self.rotation_size_mb:
                self._rotate_log_file()

        # Write event
        with open(self.current_log_file, "a") as f:
            f.write(event.to_json() + "\n")

    def _write_to_database(self, event: AuditEvent) -> None:
        """Write event to database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO audit_events (
                    event_id, timestamp, event_type, category, severity,
                    actor, details, metadata, hash_value, signature, previous_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    event.event_id,
                    event.timestamp,
                    event.event_type,
                    event.category.value,
                    event.severity.value,
                    event.actor,
                    json.dumps(event.details),
                    json.dumps(event.metadata),
                    event.hash_value,
                    event.signature,
                    self.last_hash,
                ),
            )

            conn.commit()

    def _update_statistics(self, event: AuditEvent) -> None:
        """Update internal statistics."""
        self.stats["total_events"] += 1

        severity_key = event.severity.value
        self.stats["events_by_severity"][severity_key] = (
            self.stats["events_by_severity"].get(severity_key, 0) + 1
        )

        category_key = event.category.value
        self.stats["events_by_category"][category_key] = (
            self.stats["events_by_category"].get(category_key, 0) + 1
        )

        if event.severity in [AuditSeverity.ERROR, AuditSeverity.CRITICAL]:
            self.stats["errors_logged"] += 1

    def _rotate_log_file(self) -> None:
        """Rotate current log file."""
        if self.enable_compression:
            # Compress the current file
            compressed_path = str(self.current_log_file) + ".gz"

            with open(self.current_log_file, "rb") as f_in:
                with gzip.open(compressed_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # Remove original after compression
            self.current_log_file.unlink()

        # Get new log file
        self.current_log_file = self._get_current_log_file()

    def log_error(
        self,
        error_message: str,
        details: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
    ) -> str:
        """
        Log an error event.

        Args:
            error_message: Error message
            details: Additional details
            exception: Optional exception object

        Returns:
            Event ID
        """
        error_details = {"message": error_message}

        if details:
            error_details.update(details)

        if exception:
            error_details["exception_type"] = type(exception).__name__
            error_details["exception_message"] = str(exception)

        return self.log_event(
            event_type="ERROR",
            details=error_details,
            severity=AuditSeverity.ERROR,
            category=EventCategory.ERROR,
        )

    def log_warning(self, warning_message: str, details: Optional[Dict[str, Any]] = None) -> str:
        """
        Log a warning event.

        Args:
            warning_message: Warning message
            details: Additional details

        Returns:
            Event ID
        """
        warning_details = {"message": warning_message}

        if details:
            warning_details.update(details)

        return self.log_event(
            event_type="WARNING", details=warning_details, severity=AuditSeverity.WARNING
        )

    def log_security_event(
        self,
        event_type: str,
        details: Dict[str, Any],
        severity: AuditSeverity = AuditSeverity.SECURITY,
    ) -> str:
        """
        Log a security-related event.

        Args:
            event_type: Type of security event
            details: Event details
            severity: Event severity

        Returns:
            Event ID
        """
        return self.log_event(
            event_type=f"SECURITY_{event_type}",
            details=details,
            severity=severity,
            category=EventCategory.SECURITY,
        )

    def verify_integrity(
        self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Verify integrity of audit logs.

        Args:
            start_time: Start time for verification range
            end_time: End time for verification range

        Returns:
            Dictionary with verification results
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Build query
            query = "SELECT * FROM audit_events"
            params = []

            if start_time or end_time:
                query += " WHERE"
                if start_time:
                    query += " timestamp >= ?"
                    params.append(start_time)
                if end_time:
                    if start_time:
                        query += " AND"
                    query += " timestamp <= ?"
                    params.append(end_time)

            query += " ORDER BY created_at ASC"

            cursor.execute(query, params)
            events = cursor.fetchall()

            # Verify chain integrity
            valid_count = 0
            invalid_count = 0
            invalid_events = []
            previous_hash = hashlib.sha256(b"GENESIS").hexdigest()

            for row in events:
                event_dict = {
                    "event_id": row[0],
                    "timestamp": row[1],
                    "event_type": row[2],
                    "category": row[3],
                    "severity": row[4],
                    "actor": row[5],
                    "details": json.loads(row[6]),
                    "hash_value": row[8],
                    "signature": row[9],
                    "previous_hash": row[10],
                }

                # Recreate event
                event = AuditEvent(
                    event_id=event_dict["event_id"],
                    timestamp=datetime.fromisoformat(event_dict["timestamp"]),
                    event_type=event_dict["event_type"],
                    category=EventCategory(event_dict["category"]),
                    severity=AuditSeverity(event_dict["severity"]),
                    actor=event_dict["actor"],
                    details=event_dict["details"],
                )

                # Verify hash
                calculated_hash = self._calculate_hash(event, previous_hash)

                if calculated_hash == event_dict["hash_value"]:
                    valid_count += 1
                else:
                    invalid_count += 1
                    invalid_events.append(event_dict["event_id"])

                # Verify signature
                calculated_signature = self._sign_event(event)
                if calculated_signature != event_dict["signature"]:
                    if event_dict["event_id"] not in invalid_events:
                        invalid_count += 1
                        invalid_events.append(event_dict["event_id"])

                previous_hash = event_dict["hash_value"]

            # Record integrity check
            check_details = {
                "valid_events": valid_count,
                "invalid_events": invalid_count,
                "invalid_event_ids": invalid_events,
                "total_checked": len(events),
            }

            cursor.execute(
                """
                INSERT INTO integrity_checks (
                    check_time, total_events, valid_events, 
                    invalid_events, details
                ) VALUES (?, ?, ?, ?, ?)
            """,
                (
                    datetime.now(),
                    len(events),
                    valid_count,
                    invalid_count,
                    json.dumps(check_details),
                ),
            )

            conn.commit()

            return {
                "integrity_valid": invalid_count == 0,
                "total_events": len(events),
                "valid_events": valid_count,
                "invalid_events": invalid_count,
                "invalid_event_ids": invalid_events,
                "check_time": datetime.now().isoformat(),
            }

    def query_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        severity: Optional[AuditSeverity] = None,
        category: Optional[EventCategory] = None,
        actor: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Query audit events with filters.

        Args:
            start_time: Start time filter
            end_time: End time filter
            severity: Severity filter
            category: Category filter
            actor: Actor filter
            event_type: Event type filter
            limit: Maximum number of results

        Returns:
            List of matching events
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Build query
            query = "SELECT * FROM audit_events WHERE 1=1"
            params = []

            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)

            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)

            if severity:
                query += " AND severity = ?"
                params.append(severity.value if isinstance(severity, AuditSeverity) else severity)

            if category:
                query += " AND category = ?"
                params.append(category.value if isinstance(category, EventCategory) else category)

            if actor:
                query += " AND actor = ?"
                params.append(actor)

            if event_type:
                query += " AND event_type LIKE ?"
                params.append(f"%{event_type}%")

            query += f" ORDER BY timestamp DESC LIMIT {limit}"

            cursor.execute(query, params)

            # Convert to dictionaries
            events = []
            for row in cursor.fetchall():
                events.append(
                    {
                        "event_id": row[0],
                        "timestamp": row[1],
                        "event_type": row[2],
                        "category": row[3],
                        "severity": row[4],
                        "actor": row[5],
                        "details": json.loads(row[6]),
                        "metadata": json.loads(row[7]),
                        "hash_value": row[8],
                        "signature": row[9],
                    }
                )

            return events

    def cleanup_old_logs(self) -> Dict[str, Any]:
        """
        Clean up old log files based on retention policy.

        Returns:
            Dictionary with cleanup results
        """
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)

        deleted_files = []
        deleted_events = 0

        # Clean up files
        for log_file in self.log_dir.glob("audit_*.log*"):
            # Parse date from filename
            try:
                date_str = log_file.name.split("_")[1]
                file_date = datetime.strptime(date_str, "%Y%m%d")

                if file_date < cutoff_date:
                    log_file.unlink()
                    deleted_files.append(str(log_file))
            except:
                continue

        # Clean up database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                DELETE FROM audit_events 
                WHERE timestamp < ?
            """,
                (cutoff_date,),
            )

            deleted_events = cursor.rowcount

            # Vacuum to reclaim space
            cursor.execute("VACUUM")

            conn.commit()

        # Log cleanup
        self.log_event(
            event_type="AUDIT_CLEANUP",
            details={
                "deleted_files": len(deleted_files),
                "deleted_events": deleted_events,
                "cutoff_date": cutoff_date.isoformat(),
            },
            category=EventCategory.SYSTEM,
        )

        return {
            "deleted_files": deleted_files,
            "deleted_events": deleted_events,
            "cutoff_date": cutoff_date.isoformat(),
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get audit logger statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get database statistics
            cursor.execute("SELECT COUNT(*) FROM audit_events")
            db_event_count = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT severity, COUNT(*) 
                FROM audit_events 
                GROUP BY severity
            """
            )
            db_severity_counts = dict(cursor.fetchall())

            cursor.execute(
                """
                SELECT category, COUNT(*) 
                FROM audit_events 
                GROUP BY category
            """
            )
            db_category_counts = dict(cursor.fetchall())

        return {
            "session_stats": self.stats,
            "database_stats": {
                "total_events": db_event_count,
                "events_by_severity": db_severity_counts,
                "events_by_category": db_category_counts,
            },
            "storage": {
                "log_directory": str(self.log_dir),
                "database_path": self.db_path,
                "current_log_file": str(self.current_log_file),
                "retention_days": self.retention_days,
            },
        }

    def export_report(
        self,
        filepath: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> None:
        """
        Export audit report to file.

        Args:
            filepath: Path to export file
            start_time: Report start time
            end_time: Report end time
        """
        events = self.query_events(start_time=start_time, end_time=end_time, limit=10000)

        integrity = self.verify_integrity(start_time, end_time)
        statistics = self.get_statistics()

        report = {
            "generated_at": datetime.now().isoformat(),
            "period": {
                "start": start_time.isoformat() if start_time else None,
                "end": end_time.isoformat() if end_time else None,
            },
            "integrity_check": integrity,
            "statistics": statistics,
            "event_count": len(events),
            "events": events[:1000],  # Limit to prevent huge files
        }

        with open(filepath, "w") as f:
            json.dump(report, f, indent=2, default=str)
