"""Async Postgres provider for opsvi-monitoring using SQLAlchemy 2.x."""
from typing import Any, Optional, Sequence
import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text

from opsvi_monitoring.providers.base import DataProvider  # type: ignore

logger = logging.getLogger(__name__)

def _env(key: str, default: Optional[str] = None) -> Optional[str]:
    return os.environ.get(key, default)

class PostgresProvider(DataProvider):
    def __init__(self, dsn: Optional[str] = None) -> None:
        super().__init__()
        self.dsn = dsn or _env("DATABASE_URL") or _env("OPSVI_OPSVI_MONITORING__DATABASE_URL")
        if not self.dsn:
            logger.warning("DATABASE_URL not set; PostgresProvider inactive")
        self._engine = None
        self._session_maker = None

    async def connect(self) -> bool:
        if not self.dsn:
            return False
        self._engine = create_async_engine(self.dsn, pool_pre_ping=True)
        self._session_maker = async_sessionmaker(self._engine, expire_on_commit=False)
        return True

    async def disconnect(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()
        self._engine = None
        self._session_maker = None

    async def execute(self, sql: str, **params: Any) -> None:
        if self._session_maker is None:
            ok = await self.connect()
            if not ok:
                raise RuntimeError("PostgresProvider not connected")
        async with self._session_maker() as session:  # type: ignore
            await session.execute(text(sql), params)
            await session.commit()

    async def fetch_all(self, sql: str, **params: Any) -> Sequence[tuple[Any, ...]]:
        if self._session_maker is None:
            ok = await self.connect()
            if not ok:
                raise RuntimeError("PostgresProvider not connected")
        async with self._session_maker() as session:  # type: ignore
            result = await session.execute(text(sql), params)
            return result.fetchall()

    async def fetch_one(self, sql: str, **params: Any) -> Optional[tuple[Any, ...]]:
        rows = await self.fetch_all(sql, **params)
        return rows[0] if rows else None
