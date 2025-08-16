"""Database layer for code_gen using SQLModel (SQLite).

This abstracted module keeps DB logic isolated from the rest of the app.
The file is self-contained so we avoid scattering ORM helpers.
"""

from __future__ import annotations

import logging
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from sqlmodel import Field, Session, SQLModel, create_engine, select

from config import config

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Job model
# ---------------------------------------------------------------------------


class Job(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    """Persisted job metadata.  Represents one end-to-end generation run."""

    id: str = Field(primary_key=True, index=True)
    request_text: str
    status: str = Field(
        index=True, default="queued"
    )  # queued | in_progress | completed | failed
    phase: str | None = Field(default=None, index=True)
    progress: float = 0.0  # 0.0-1.0 normalized

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow}
    )

    error: str | None = None  # Truncated error message if failed
    artifacts_path: str | None = None  # Path to zip or S3 key


# ---------------------------------------------------------------------------
# Engine / Session helpers
# ---------------------------------------------------------------------------

# Use absolute path to ensure consistent database location regardless of working directory
_db_path = Path(__file__).parent.parent.parent / config.job_output_dir / "jobs.db"
_engine = create_engine(f"sqlite:///{_db_path}", echo=False)


def init_db() -> None:
    """Create tables if they don't exist yet."""

    SQLModel.metadata.create_all(_engine)
    logger.info("Database initialised at %s", _db_path)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Yield a Session with proper commit/close semantics."""

    session = Session(_engine)
    try:
        yield session
        session.commit()
    except Exception:  # noqa: BLE001
        session.rollback()
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------


def create_job(job_id: str, request_text: str) -> None:
    job = Job(id=job_id, request_text=request_text)
    with get_session() as s:
        s.add(job)
    logger.info("Job %s persisted to DB", job_id)


def update_job(job_id: str, **fields) -> None:
    with get_session() as s:
        stmt = select(Job).where(Job.id == job_id)
        job = s.exec(stmt).one()
        for k, v in fields.items():
            setattr(job, k, v)
        job.updated_at = datetime.utcnow()
        s.add(job)


def get_job(job_id: str) -> Job | None:
    with get_session() as s:
        stmt = select(Job).where(Job.id == job_id)
        return s.exec(stmt).first()


def get_job_data(job_id: str) -> dict | None:
    """Return job row as plain dict with session still open."""
    with get_session() as s:
        stmt = select(Job).where(Job.id == job_id)
        job = s.exec(stmt).first()
        if job:
            return job.model_dump()
        return None


# Run initialisation on import
init_db()
