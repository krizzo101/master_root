"""ORM base for opsvi-data.

Provides a lightweight in-memory async-friendly ORM base suitable for testing and
simple applications. It includes a BaseModel, an async Session for unit-of-work
semantics, a central ORM registry, and simple migration hook registration and
execution.
"""
from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Awaitable, Callable, Coroutine, Dict, Generic, List, Optional, Type, TypeVar
from uuid import uuid4

T = TypeVar("T", bound="BaseModel")

MigrationCallable = Callable[[], Awaitable[None]]


@dataclass
class BaseModel:
    """Base for models. Subclass to create simple data models.

    Fields:
        id: unique identifier (string). Assigned automatically if None when saved.
        created_at: timestamp when first saved.
        updated_at: timestamp when last saved.
    """

    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def as_dict(self) -> Dict[str, Any]:
        """Return a dictionary representation of the model."""
        return asdict(self)

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create an instance from a dictionary produced by as_dict."""
        return cls(**data)  # type: ignore[arg-type]

    def touch(self) -> None:
        """Update the updated_at timestamp; set created_at if missing."""
        now = datetime.utcnow()
        if self.created_at is None:
            self.created_at = now
        self.updated_at = now

    async def save(self, session: "Session") -> None:
        """Persist model in the provided session (staged until commit).

        Usage: async with orm.create_session() as sess: await model.save(sess)
        """
        await session.add(self)

    async def delete(self, session: "Session") -> None:
        """Mark model for deletion in the provided session."""
        await session.delete(self)


class _InMemoryStore:
    """Simple in-memory storage for models keyed by model name and id."""

    def __init__(self) -> None:
        self._data: Dict[str, Dict[str, Dict[str, Any]]] = {}

    def ensure_model(self, model_name: str) -> None:
        if model_name not in self._data:
            self._data[model_name] = {}

    def apply_add(self, model_name: str, obj_dict: Dict[str, Any]) -> None:
        self.ensure_model(model_name)
        self._data[model_name][obj_dict["id"]] = obj_dict

    def apply_delete(self, model_name: str, obj_id: str) -> None:
        if model_name in self._data and obj_id in self._data[model_name]:
            del self._data[model_name][obj_id]

    def get(self, model_name: str, obj_id: str) -> Optional[Dict[str, Any]]:
        return self._data.get(model_name, {}).get(obj_id)

    def list_all(self, model_name: str) -> List[Dict[str, Any]]:
        return list(self._data.get(model_name, {}).values())


@dataclass
class Session:
    """Async session providing unit-of-work semantics against an in-memory store.

    The session is an async context manager: it commits on normal exit and
    rolls back on exception.
    """

    orm: "ORM"

    _pending_adds: Dict[str, Dict[str, Dict[str, Any]]] = field(default_factory=dict)
    _pending_deletes: Dict[str, List[str]] = field(default_factory=dict)
    _closed: bool = False

    def __post_init__(self) -> None:
        self._lock = asyncio.Lock()

    async def add(self, obj: BaseModel) -> None:
        """Stage an object for insertion/update.

        The object's id will be assigned if missing and timestamps updated.
        """
        async with self._lock:
            if self._closed:
                raise RuntimeError("Session is closed")
            if obj.id is None:
                obj.id = str(uuid4())
            obj.touch()
            model_name = self.orm._name_for_model(type(obj))
            self._pending_adds.setdefault(model_name, {})[obj.id] = obj.as_dict()

    async def delete(self, obj: BaseModel) -> None:
        """Stage an object for deletion by id."""
        async with self._lock:
            if self._closed:
                raise RuntimeError("Session is closed")
            if obj.id is None:
                return
            model_name = self.orm._name_for_model(type(obj))
            self._pending_deletes.setdefault(model_name, []).append(obj.id)

    async def get(self, model_cls: Type[T], obj_id: str) -> Optional[T]:
        """Retrieve an object by id, considering pending changes in this session."""
        async with self._lock:
            model_name = self.orm._name_for_model(model_cls)
            # check pending deletes
            if obj_id in self._pending_deletes.get(model_name, []):
                return None
            # check pending adds/updates
            if obj_id in self._pending_adds.get(model_name, {}):
                return model_cls.from_dict(self._pending_adds[model_name][obj_id])
            # fallback to store
            stored = self.orm._store.get(model_name, {}).get(obj_id)
            if stored is None:
                return None
            return model_cls.from_dict(stored)

    async def list_all(self, model_cls: Type[T]) -> List[T]:
        """List all objects of a model, including pending session changes."""
        async with self._lock:
            model_name = self.orm._name_for_model(model_cls)
            ids_deleted = set(self._pending_deletes.get(model_name, []))
            results: Dict[str, Dict[str, Any]] = {}
            # start from store
            for item in self.orm._store.get(model_name, {}).values():
                results[item["id"]] = item
            # apply pending adds/updates
            for k, v in self._pending_adds.get(model_name, {}).items():
                results[k] = v
            # remove deletes
            for did in ids_deleted:
                results.pop(did, None)
            return [self.orm._model_classes[model_name].from_dict(d) for d in results.values()]

    async def commit(self) -> None:
        """Apply staged changes to the global store."""
        async with self._lock:
            if self._closed:
                raise RuntimeError("Session is closed")
            # apply adds
            for model_name, items in self._pending_adds.items():
                for obj in items.values():
                    self.orm._store.apply_add(model_name, obj)
            # apply deletes
            for model_name, ids in self._pending_deletes.items():
                for obj_id in ids:
                    self.orm._store.apply_delete(model_name, obj_id)
            self._pending_adds.clear()
            self._pending_deletes.clear()

    async def rollback(self) -> None:
        """Clear staged changes."""
        async with self._lock:
            self._pending_adds.clear()
            self._pending_deletes.clear()

    async def close(self) -> None:
        async with self._lock:
            self._closed = True

    async def __aenter__(self) -> "Session":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if exc is None:
            await self.commit()
        else:
            await self.rollback()
        await self.close()


@dataclass
class _Migration:
    name: str
    up: MigrationCallable
    down: Optional[MigrationCallable] = None


class ORM:
    """Central registry and factory for sessions and migrations.

    This class intentionally keeps things simple: it is an in-memory manager
    that allows registering model classes and migration hooks.
    """

    def __init__(self) -> None:
        self._model_classes: Dict[str, Type[BaseModel]] = {}
        self._store = _InMemoryStore()
        self._migrations: List[_Migration] = []
        self._applied_migrations: List[str] = []

    def register_model(self, model_cls: Type[T], name: Optional[str] = None) -> Type[T]:
        """Register a model class with an optional name. Returns the class.

        Typical usage:
            @orm.register_model
            class MyModel(BaseModel): ...
        """
        model_name = name or model_cls.__name__
        if model_name in self._model_classes:
            raise ValueError(f"Model name already registered: {model_name}")
        self._model_classes[model_name] = model_cls
        return model_cls

    def _name_for_model(self, model_cls: Type[BaseModel]) -> str:
        for name, cls in self._model_classes.items():
            if cls is model_cls or issubclass(model_cls, cls):
                return name
        # fallback
        return model_cls.__name__

    def create_session(self) -> Session:
        """Create a new async Session bound to this ORM."""
        return Session(self)

    def register_migration(self, name: str, up: MigrationCallable, down: Optional[MigrationCallable] = None) -> None:
        """Register an async migration (up and optional down)."""
        if any(m.name == name for m in self._migrations):
            raise ValueError(f"Migration already registered: {name}")
        self._migrations.append(_Migration(name=name, up=up, down=down))

    async def run_migrations(self, to: Optional[str] = None) -> None:
        """Run migrations in order. If 'to' is provided, run up migrations until that
        migration name (inclusive). Migrations already applied are skipped.
        """
        for migration in self._migrations:
            if migration.name in self._applied_migrations:
                continue
            await migration.up()
            self._applied_migrations.append(migration.name)
            if to is not None and migration.name == to:
                break

    def list_migrations(self) -> List[str]:
        return [m.name for m in self._migrations]


# expose a default singleton ORM instance for convenience
orm = ORM()

__all__ = ["BaseModel", "Session", "ORM", "orm"]
