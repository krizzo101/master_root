"""State manager for opsvi-core.

Provides basic state persistence and synchronization.
"""

from typing import Any, Dict, Callable, Optional, Protocol, Tuple, List
import asyncio
import logging
import json
from pathlib import Path

from opsvi_core.core.base import OpsviCoreManager
from opsvi_core.config.settings import OpsviCoreConfig

logger = logging.getLogger(__name__)


class PersistenceBackend(Protocol):
    """Protocol for persistence backends.

    Backends should store a mapping of keys to values and optional version
    information. Implementations must be safe to call from asyncio contexts.
    """

    async def load(self) -> Tuple[Dict[str, Any], Dict[str, int]]:
        """Load persisted state.

        Returns a tuple (state, versions).
        """

    async def save(self, state: Dict[str, Any], versions: Dict[str, int]) -> None:
        """Persist the provided state and versions."""


class FileBackend:
    """Simple JSON file persistence backend.

    File format: {"state": {...}, "versions": {...}}
    """

    def __init__(self, path: Path):
        self._path = Path(path)
        # Ensure parent exists
        if not self._path.parent.exists():
            self._path.parent.mkdir(parents=True, exist_ok=True)

    async def load(self) -> Tuple[Dict[str, Any], Dict[str, int]]:
        if not self._path.exists():
            return {}, {}

        def _read() -> Tuple[Dict[str, Any], Dict[str, int]]:
            with self._path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            state = data.get("state", {})
            versions = data.get("versions", {})
            # normalize versions to int
            versions = {k: int(v) for k, v in versions.items()}
            return state, versions

        return await asyncio.to_thread(_read)

    async def save(self, state: Dict[str, Any], versions: Dict[str, int]) -> None:
        def _write() -> None:
            tmp = self._path.with_suffix(self._path.suffix + ".tmp")
            with tmp.open("w", encoding="utf-8") as fh:
                json.dump({"state": state, "versions": versions}, fh, ensure_ascii=False)
            tmp.replace(self._path)

        await asyncio.to_thread(_write)


class StateManager(OpsviCoreManager):
    """State management component.

    This manager holds an in-memory mapping and optional pluggable persistence.

    Features:
    - Async-safe get/set/delete with an asyncio.Lock
    - Per-key versioning for optimistic concurrency (compare-and-swap)
    - Optional persistence backend (e.g. FileBackend)
    - Simple subscriber callbacks for state changes
    """

    def __init__(self, config: OpsviCoreConfig, backend: Optional[PersistenceBackend] = None):
        super().__init__(config=config)
        self._state: Dict[str, Any] = {}
        self._versions: Dict[str, int] = {}
        self._lock = asyncio.Lock()
        self._backend: Optional[PersistenceBackend] = backend
        self._subscribers: List[Callable[[str, Any], None]] = []

    async def get(self, key: str, default: Any = None) -> Any:
        async with self._lock:
            return self._state.get(key, default)

    async def set(self, key: str, value: Any) -> None:
        async with self._lock:
            prev = self._state.get(key)
            self._state[key] = value
            self._versions[key] = self._versions.get(key, 0) + 1
            logger.debug("State set: %s (prev=%r)", key, prev)
            await self._maybe_persist()
            self._notify_subscribers(key, value)

    async def delete(self, key: str) -> None:
        async with self._lock:
            existed = key in self._state
            self._state.pop(key, None)
            self._versions.pop(key, None)
            logger.debug("State deleted: %s (existed=%s)", key, existed)
            await self._maybe_persist()
            self._notify_subscribers(key, None)

    async def snapshot(self) -> Dict[str, Any]:
        async with self._lock:
            return dict(self._state)

    async def version(self, key: str) -> int:
        """Return the current version for a key (0 if missing)."""
        async with self._lock:
            return self._versions.get(key, 0)

    async def compare_and_swap(self, key: str, expected_version: int, new_value: Any) -> bool:
        """Atomically set key to new_value only if its version equals expected_version.

        Returns True if the swap occurred, False otherwise.
        """
        async with self._lock:
            current_version = self._versions.get(key, 0)
            if current_version != expected_version:
                logger.debug("CAS failed for %s: expected %s, current %s", key, expected_version, current_version)
                return False
            self._state[key] = new_value
            self._versions[key] = current_version + 1
            logger.debug("CAS success for %s -> version %s", key, self._versions[key])
            await self._maybe_persist()
            self._notify_subscribers(key, new_value)
            return True

    async def load_from_backend(self, replace: bool = True) -> None:
        """Load state from the configured backend.

        If replace is True (default), the backend snapshot replaces current in-memory
        state. If False, backend entries are merged into in-memory state only for
        missing keys (no overwrite).
        """
        if self._backend is None:
            logger.debug("No backend configured; load skipped")
            return
        state, versions = await self._backend.load()
        async with self._lock:
            if replace:
                self._state = dict(state)
                self._versions = dict(versions)
                logger.debug("State loaded from backend (replaced), %d keys", len(self._state))
            else:
                # Merge: only fill missing keys
                for k, v in state.items():
                    if k not in self._state:
                        self._state[k] = v
                        self._versions[k] = versions.get(k, 0)
                logger.debug("State loaded from backend (merged), total %d keys", len(self._state))

    async def persist_now(self) -> None:
        """Force persisting current state to the backend (if configured)."""
        if self._backend is None:
            logger.debug("No backend configured; persist skipped")
            return
        async with self._lock:
            await self._backend.save(dict(self._state), dict(self._versions))
            logger.debug("State persisted to backend (%d keys)", len(self._state))

    async def _maybe_persist(self) -> None:
        """Persist in background if a backend exists. Called while holding lock.

        To avoid blocking callers we schedule persistence on the event loop but do
        not await it here. If callers want guaranteed persistence they should call
        persist_now().
        """
        if self._backend is None:
            return

        # schedule background save
        loop = asyncio.get_running_loop()

        async def _save_snapshot(state_copy: Dict[str, Any], versions_copy: Dict[str, int]) -> None:
            try:
                await self._backend.save(state_copy, versions_copy)
                logger.debug("Background persistence complete")
            except Exception:
                logger.exception("Background persistence failed")

        state_copy = dict(self._state)
        versions_copy = dict(self._versions)
        loop.create_task(_save_snapshot(state_copy, versions_copy))

    def subscribe(self, callback: Callable[[str, Any], None]) -> Callable[[], None]:
        """Register a subscriber callback to be called on key changes.

        Returns an unsubscribe callable.
        """
        self._subscribers.append(callback)

        def _unsubscribe() -> None:
            try:
                self._subscribers.remove(callback)
            except ValueError:
                pass

        return _unsubscribe

    def _notify_subscribers(self, key: str, value: Any) -> None:
        for cb in list(self._subscribers):
            try:
                cb(key, value)
            except Exception:
                logger.exception("Subscriber callback raised for key=%s", key)

    def set_backend(self, backend: Optional[PersistenceBackend]) -> None:
        """Attach or detach a persistence backend."""
        self._backend = backend

    async def close(self) -> None:
        """Flush state to backend (if any) and perform cleanup."""
        await self.persist_now()


# End of module
