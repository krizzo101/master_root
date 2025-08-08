"""Infrastructure base for opsvi-deploy.

Provides a minimal declarative resource model and an async provisioning
engine suitable for small deployments and unit testing. This module does
not perform any network I/O by itself; concrete Resource subclasses
should implement platform-specific actions.
"""
from __future__ import annotations

import abc
import asyncio
import dataclasses
import logging
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ResourceStatus(Enum):
    """High-level lifecycle status for a resource.

    - MISSING: resource does not exist but desired state is present
    - PRESENT: resource exists and matches desired state
    - DIFF: resource exists but diverges from desired state
    - ERROR: an error occurred while reconciling
    """

    MISSING = "missing"
    PRESENT = "present"
    DIFF = "diff"
    ERROR = "error"


class ResourceError(Exception):
    """Raised when a resource operation fails."""


@dataclasses.dataclass
class Resource:
    """Declarative resource description.

    Subclasses should override async methods to implement actual
    provisioning logic for create/update/delete and to report current
    state via `read_current_state`.
    """

    name: str
    type: str
    desired: Dict[str, Any]

    async def read_current_state(self) -> Optional[Dict[str, Any]]:
        """Return the current (observed) state, or None if not present.

        Default implementation reports "not present".
        """
        return None

    async def create(self) -> None:
        """Create the resource to match desired state.

        Implementations should raise ResourceError on failure.
        """
        raise NotImplementedError("create must be implemented by subclasses")

    async def update(self, diff: Dict[str, Tuple[Any, Any]]) -> None:
        """Update the resource given a diff mapping field -> (current, desired).

        Default implementation forwards to create().
        """
        await self.create()

    async def delete(self) -> None:
        """Delete the underlying resource.

        Default implementation is a no-op.
        """
        return

    def diff(self, current: Optional[Dict[str, Any]]) -> Dict[str, Tuple[Any, Any]]:
        """Compute a simple field-level diff between current and desired.

        Returns a mapping of key -> (current_value, desired_value) for keys
        that differ or are missing.
        """
        diffs: Dict[str, Tuple[Any, Any]] = {}
        if current is None:
            # Everything is missing
            for k, v in self.desired.items():
                diffs[k] = (None, v)
            return diffs

        for k, desired_v in self.desired.items():
            curr_v = current.get(k)
            if curr_v != desired_v:
                diffs[k] = (curr_v, desired_v)
        return diffs


class Infrastructure:
    """Manage a set of declarative resources and provision them asynchronously.

    Usage:
      infra = Infrastructure()
      infra.register(Resource(...))
      await infra.provision()
    """

    def __init__(self) -> None:
        self._resources: Dict[str, Resource] = {}
        # small default concurrency to avoid accidental thundering
        self.default_concurrency = 8

    def register(self, resource: Resource) -> None:
        """Register a resource with a unique name.

        Re-registering a name will replace the previous resource.
        """
        if resource.name in self._resources:
            logger.debug("Replacing resource %s", resource.name)
        self._resources[resource.name] = resource

    def unregister(self, name: str) -> None:
        """Remove a resource from the manifest. Does not delete underlying.

        To remove underlying resources, call provision() after updating the
        manifest and implementing deletion semantics in concrete classes.
        """
        self._resources.pop(name, None)

    def list_resources(self) -> List[Resource]:
        return list(self._resources.values())

    def get_resource(self, name: str) -> Optional[Resource]:
        return self._resources.get(name)

    async def plan(self) -> Dict[str, ResourceStatus]:
        """Inspect all registered resources and return a simple plan mapping
        resource name -> ResourceStatus.
        """
        results: Dict[str, ResourceStatus] = {}
        coros = [self._inspect(r) for r in self.list_resources()]
        for name, status in await asyncio.gather(*coros):
            results[name] = status
        return results

    async def _inspect(self, resource: Resource) -> Tuple[str, ResourceStatus]:
        try:
            current = await resource.read_current_state()
            diffs = resource.diff(current)
            if current is None:
                status = ResourceStatus.MISSING
            elif diffs:
                status = ResourceStatus.DIFF
            else:
                status = ResourceStatus.PRESENT
            return resource.name, status
        except Exception:
            logger.exception("Error inspecting resource %s", resource.name)
            return resource.name, ResourceStatus.ERROR

    async def provision(self, *, concurrency: Optional[int] = None, dry_run: bool = False) -> Dict[str, ResourceStatus]:
        """Provision all registered resources to match desired state.

        Returns a mapping of resource name -> final ResourceStatus.
        If dry_run is True, no create/update/delete methods will be invoked;
        the method will only return the plan.
        """
        if concurrency is None:
            concurrency = self.default_concurrency
        semaphore = asyncio.Semaphore(concurrency)

        async def worker(resource: Resource) -> Tuple[str, ResourceStatus]:
            async with semaphore:
                try:
                    current = await resource.read_current_state()
                    diffs = resource.diff(current)
                    if current is None and not diffs:
                        # no desired state (empty) and not present -> present
                        return resource.name, ResourceStatus.PRESENT
                    if dry_run:
                        # Do not modify anything during dry run
                        if current is None:
                            return resource.name, ResourceStatus.MISSING
                        if diffs:
                            return resource.name, ResourceStatus.DIFF
                        return resource.name, ResourceStatus.PRESENT

                    if current is None:
                        logger.info("Creating resource %s", resource.name)
                        await resource.create()
                    elif diffs:
                        logger.info("Updating resource %s: %s", resource.name, list(diffs.keys()))
                        await resource.update(diffs)
                    else:
                        logger.debug("Resource %s already present and up-to-date", resource.name)
                    # Re-inspect after operation to determine final status
                    new_current = await resource.read_current_state()
                    new_diffs = resource.diff(new_current)
                    if new_current is None:
                        return resource.name, ResourceStatus.MISSING
                    if new_diffs:
                        return resource.name, ResourceStatus.DIFF
                    return resource.name, ResourceStatus.PRESENT
                except Exception:
                    logger.exception("Error reconciling resource %s", resource.name)
                    return resource.name, ResourceStatus.ERROR

        tasks = [worker(r) for r in self.list_resources()]
        results: Dict[str, ResourceStatus] = {}
        for name, status in await asyncio.gather(*tasks):
            results[name] = status
        return results


# Small example concrete resource for tests and examples
class InMemoryResource(Resource):
    """A trivial resource that stores state in memory for unit tests.

    The InMemoryResource simulates a platform resource by keeping an
    internal dictionary representing the current state.
    """

    def __init__(self, name: str, type: str, desired: Dict[str, Any]) -> None:
        super().__init__(name=name, type=type, desired=desired)
        self._state: Optional[Dict[str, Any]] = None

    async def read_current_state(self) -> Optional[Dict[str, Any]]:
        # simulate small I/O latency
        await asyncio.sleep(0)
        return None if self._state is None else dict(self._state)

    async def create(self) -> None:
        await asyncio.sleep(0)
        self._state = dict(self.desired)

    async def update(self, diff: Dict[str, Tuple[Any, Any]]) -> None:
        await asyncio.sleep(0)
        if self._state is None:
            raise ResourceError("Cannot update missing resource")
        for k, (_curr, desired) in diff.items():
            self._state[k] = desired

    async def delete(self) -> None:
        await asyncio.sleep(0)
        self._state = None


__all__ = [
    "Infrastructure",
    "Resource",
    "ResourceStatus",
    "ResourceError",
    "InMemoryResource",
]
