"""
Capability Registry - Manages and organizes discovered capabilities
"""

import asyncio
import json
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum
import hashlib

from src.capabilities.discovery import Capability
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CapabilityStatus(Enum):
    """Status of a capability"""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    PENDING = "pending"
    FAILED = "failed"
    DEPRECATED = "deprecated"
    TESTING = "testing"


class CapabilityCategory(Enum):
    """Categories for organizing capabilities"""

    DATA_PROCESSING = "data_processing"
    WEB_OPERATIONS = "web_operations"
    FILE_OPERATIONS = "file_operations"
    SYSTEM_CONTROL = "system_control"
    COMMUNICATION = "communication"
    TESTING = "testing"
    MONITORING = "monitoring"
    MACHINE_LEARNING = "machine_learning"
    SECURITY = "security"
    UTILITIES = "utilities"


class CapabilityRegistry:
    """Central registry for all discovered and integrated capabilities"""

    def __init__(self, cache_dir: Optional[Path] = None):
        self.capabilities: Dict[str, Capability] = {}
        self.categories: Dict[CapabilityCategory, Set[str]] = defaultdict(set)
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.conflicts: Dict[str, Set[str]] = defaultdict(set)
        self.usage_stats: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "count": 0,
                "successes": 0,
                "failures": 0,
                "total_time": 0.0,
                "last_used": None,
                "error_types": defaultdict(int),
            }
        )
        self.cache_dir = cache_dir or Path.home() / ".autonomous_claude" / "capability_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()
        self._capability_index: Dict[str, Set[str]] = defaultdict(
            set
        )  # keyword -> capability names
        self._load_cache()

    def _load_cache(self):
        """Load cached registry data"""
        cache_file = self.cache_dir / "registry.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, "rb") as f:
                    data = pickle.load(f)
                    self.capabilities = data.get("capabilities", {})
                    self.categories = data.get("categories", defaultdict(set))
                    self.dependencies = data.get("dependencies", defaultdict(set))
                    self.conflicts = data.get("conflicts", defaultdict(set))
                    self.usage_stats = data.get(
                        "usage_stats",
                        defaultdict(
                            lambda: {
                                "count": 0,
                                "successes": 0,
                                "failures": 0,
                                "total_time": 0.0,
                                "last_used": None,
                                "error_types": defaultdict(int),
                            }
                        ),
                    )
                    self._rebuild_index()
                    logger.info(f"Loaded {len(self.capabilities)} capabilities from cache")
            except Exception as e:
                logger.error(f"Failed to load cache: {e}")

    def _save_cache(self):
        """Save registry data to cache"""
        cache_file = self.cache_dir / "registry.pkl"
        try:
            data = {
                "capabilities": self.capabilities,
                "categories": dict(self.categories),
                "dependencies": dict(self.dependencies),
                "conflicts": dict(self.conflicts),
                "usage_stats": dict(self.usage_stats),
            }
            with open(cache_file, "wb") as f:
                pickle.dump(data, f)
            logger.debug("Registry cache saved")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    def _rebuild_index(self):
        """Rebuild the keyword index for fast lookup"""
        self._capability_index.clear()
        for name, cap in self.capabilities.items():
            # Index by name components
            for word in name.lower().split("_"):
                self._capability_index[word].add(name)

            # Index by description words
            if cap.description:
                for word in cap.description.lower().split():
                    if len(word) > 3:  # Skip short words
                        self._capability_index[word].add(name)

            # Index by type
            self._capability_index[cap.type].add(name)

    async def register(
        self, capability: Capability, category: Optional[CapabilityCategory] = None
    ) -> bool:
        """Register a new capability"""
        async with self._lock:
            try:
                # Check for conflicts
                if capability.name in self.capabilities:
                    existing = self.capabilities[capability.name]
                    if existing.metadata.get("version") != capability.metadata.get("version"):
                        logger.warning(f"Updating existing capability: {capability.name}")

                # Register the capability
                self.capabilities[capability.name] = capability

                # Auto-categorize if not specified
                if category is None:
                    category = self._auto_categorize(capability)

                if category:
                    self.categories[category].add(capability.name)

                # Update index
                self._update_index_for_capability(capability)

                # Save to cache
                self._save_cache()

                logger.info(f"Registered capability: {capability.name} (category: {category})")
                return True

            except Exception as e:
                logger.error(f"Failed to register capability {capability.name}: {e}")
                return False

    async def unregister(self, capability_name: str) -> bool:
        """Unregister a capability"""
        async with self._lock:
            if capability_name not in self.capabilities:
                return False

            # Remove from all categories
            for category_set in self.categories.values():
                category_set.discard(capability_name)

            # Remove dependencies and conflicts
            self.dependencies.pop(capability_name, None)
            self.conflicts.pop(capability_name, None)

            # Remove from other capabilities' dependencies/conflicts
            for deps in self.dependencies.values():
                deps.discard(capability_name)
            for confs in self.conflicts.values():
                confs.discard(capability_name)

            # Remove capability
            del self.capabilities[capability_name]

            # Rebuild index
            self._rebuild_index()

            # Save cache
            self._save_cache()

            logger.info(f"Unregistered capability: {capability_name}")
            return True

    def _auto_categorize(self, capability: Capability) -> Optional[CapabilityCategory]:
        """Automatically determine category based on capability attributes"""
        name_lower = capability.name.lower()
        desc_lower = capability.description.lower() if capability.description else ""

        # Check for patterns
        if any(
            word in name_lower + desc_lower for word in ["web", "http", "scrape", "browse", "url"]
        ):
            return CapabilityCategory.WEB_OPERATIONS
        elif any(
            word in name_lower + desc_lower
            for word in ["file", "read", "write", "path", "directory"]
        ):
            return CapabilityCategory.FILE_OPERATIONS
        elif any(
            word in name_lower + desc_lower
            for word in ["data", "pandas", "numpy", "process", "analyze"]
        ):
            return CapabilityCategory.DATA_PROCESSING
        elif any(
            word in name_lower + desc_lower for word in ["test", "pytest", "unittest", "validate"]
        ):
            return CapabilityCategory.TESTING
        elif any(word in name_lower + desc_lower for word in ["monitor", "metric", "log", "trace"]):
            return CapabilityCategory.MONITORING
        elif any(
            word in name_lower + desc_lower for word in ["ml", "ai", "neural", "model", "train"]
        ):
            return CapabilityCategory.MACHINE_LEARNING
        elif any(
            word in name_lower + desc_lower for word in ["system", "process", "cpu", "memory"]
        ):
            return CapabilityCategory.SYSTEM_CONTROL
        elif any(
            word in name_lower + desc_lower for word in ["security", "auth", "encrypt", "hash"]
        ):
            return CapabilityCategory.SECURITY
        elif any(
            word in name_lower + desc_lower for word in ["email", "sms", "notification", "message"]
        ):
            return CapabilityCategory.COMMUNICATION
        else:
            return CapabilityCategory.UTILITIES

    def _update_index_for_capability(self, capability: Capability):
        """Update the search index for a single capability"""
        name = capability.name

        # Index by name components
        for word in name.lower().split("_"):
            self._capability_index[word].add(name)

        # Index by description
        if capability.description:
            for word in capability.description.lower().split():
                if len(word) > 3:
                    self._capability_index[word].add(name)

        # Index by type
        self._capability_index[capability.type].add(name)

    async def add_dependency(self, capability_name: str, depends_on: str) -> bool:
        """Add a dependency relationship"""
        async with self._lock:
            if capability_name not in self.capabilities or depends_on not in self.capabilities:
                return False

            # Check for circular dependencies
            if self._would_create_cycle(capability_name, depends_on):
                logger.error(f"Cannot add dependency: would create cycle")
                return False

            self.dependencies[capability_name].add(depends_on)
            self._save_cache()
            return True

    async def add_conflict(self, capability1: str, capability2: str) -> bool:
        """Mark two capabilities as conflicting"""
        async with self._lock:
            if capability1 not in self.capabilities or capability2 not in self.capabilities:
                return False

            self.conflicts[capability1].add(capability2)
            self.conflicts[capability2].add(capability1)
            self._save_cache()
            return True

    def _would_create_cycle(self, source: str, target: str) -> bool:
        """Check if adding a dependency would create a cycle"""
        visited = set()

        def dfs(node: str) -> bool:
            if node == source:
                return True
            if node in visited:
                return False
            visited.add(node)

            for dep in self.dependencies.get(node, []):
                if dfs(dep):
                    return True
            return False

        return dfs(target)

    def get_capability(self, name: str) -> Optional[Capability]:
        """Get a capability by name"""
        return self.capabilities.get(name)

    def get_by_category(self, category: CapabilityCategory) -> List[Capability]:
        """Get all capabilities in a category"""
        names = self.categories.get(category, set())
        return [self.capabilities[name] for name in names if name in self.capabilities]

    def get_available(self) -> List[Capability]:
        """Get all available capabilities"""
        return [cap for cap in self.capabilities.values() if cap.available]

    def search(self, query: str, limit: int = 10) -> List[Capability]:
        """Search for capabilities by keyword"""
        query_lower = query.lower()
        matches = set()

        # Search in index
        for word in query_lower.split():
            if word in self._capability_index:
                matches.update(self._capability_index[word])

        # Score and sort matches
        scored_matches = []
        for name in matches:
            if name in self.capabilities:
                cap = self.capabilities[name]
                score = self._calculate_relevance_score(cap, query_lower)
                scored_matches.append((score, cap))

        # Sort by score and return top matches
        scored_matches.sort(key=lambda x: x[0], reverse=True)
        return [cap for _, cap in scored_matches[:limit]]

    def _calculate_relevance_score(self, capability: Capability, query: str) -> float:
        """Calculate relevance score for a capability"""
        score = 0.0

        # Exact name match
        if query in capability.name.lower():
            score += 10.0

        # Word matches in name
        for word in query.split():
            if word in capability.name.lower():
                score += 5.0

        # Description matches
        if capability.description:
            desc_lower = capability.description.lower()
            if query in desc_lower:
                score += 3.0
            for word in query.split():
                if word in desc_lower:
                    score += 1.0

        # Usage-based scoring
        stats = self.usage_stats.get(capability.name, {})
        if stats.get("count", 0) > 0:
            success_rate = stats["successes"] / stats["count"]
            score += success_rate * 2.0

        # Recency bonus
        if stats.get("last_used"):
            days_since = (datetime.now() - stats["last_used"]).days
            if days_since < 1:
                score += 2.0
            elif days_since < 7:
                score += 1.0

        return score

    async def record_usage(
        self,
        capability_name: str,
        success: bool,
        execution_time: float,
        error_type: Optional[str] = None,
    ):
        """Record usage statistics for a capability"""
        async with self._lock:
            if capability_name not in self.capabilities:
                return

            stats = self.usage_stats[capability_name]
            stats["count"] += 1
            if success:
                stats["successes"] += 1
            else:
                stats["failures"] += 1
                if error_type:
                    stats["error_types"][error_type] += 1

            stats["total_time"] += execution_time
            stats["last_used"] = datetime.now()

            # Update capability success rate
            cap = self.capabilities[capability_name]
            cap.success_rate = stats["successes"] / stats["count"]
            cap.last_used = datetime.now()

            self._save_cache()

    def get_dependencies(self, capability_name: str, recursive: bool = True) -> Set[str]:
        """Get all dependencies for a capability"""
        if capability_name not in self.capabilities:
            return set()

        if not recursive:
            return self.dependencies.get(capability_name, set()).copy()

        # Recursive dependency resolution
        all_deps = set()
        to_process = [capability_name]
        processed = set()

        while to_process:
            current = to_process.pop()
            if current in processed:
                continue
            processed.add(current)

            deps = self.dependencies.get(current, set())
            all_deps.update(deps)
            to_process.extend(deps - processed)

        return all_deps

    def get_conflicts(self, capability_name: str) -> Set[str]:
        """Get all conflicting capabilities"""
        return self.conflicts.get(capability_name, set()).copy()

    def can_use_together(self, capabilities: List[str]) -> Tuple[bool, Optional[str]]:
        """Check if a set of capabilities can be used together"""
        # Check all capabilities exist
        for cap in capabilities:
            if cap not in self.capabilities:
                return False, f"Unknown capability: {cap}"

        # Check for conflicts
        for i, cap1 in enumerate(capabilities):
            for cap2 in capabilities[i + 1 :]:
                if cap2 in self.conflicts.get(cap1, set()):
                    return False, f"Conflict between {cap1} and {cap2}"

        # Check dependencies are satisfied
        required = set()
        for cap in capabilities:
            required.update(self.get_dependencies(cap))

        missing = required - set(capabilities)
        if missing:
            return False, f"Missing dependencies: {missing}"

        return True, None

    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics"""
        total_usage = sum(stats["count"] for stats in self.usage_stats.values())
        total_successes = sum(stats["successes"] for stats in self.usage_stats.values())

        most_used = sorted(
            [(name, stats["count"]) for name, stats in self.usage_stats.items()],
            key=lambda x: x[1],
            reverse=True,
        )[:5]

        by_category = {cat.value: len(names) for cat, names in self.categories.items()}

        return {
            "total_capabilities": len(self.capabilities),
            "available": len([c for c in self.capabilities.values() if c.available]),
            "total_usage": total_usage,
            "success_rate": total_successes / total_usage if total_usage > 0 else 0,
            "most_used": most_used,
            "by_category": by_category,
            "total_dependencies": sum(len(deps) for deps in self.dependencies.values()),
            "total_conflicts": sum(len(confs) for confs in self.conflicts.values()) // 2,
        }

    async def cleanup_stale(self, days: int = 30):
        """Remove capabilities not used in specified days"""
        async with self._lock:
            cutoff = datetime.now() - timedelta(days=days)
            to_remove = []

            for name, cap in self.capabilities.items():
                stats = self.usage_stats.get(name, {})
                last_used = stats.get("last_used")

                if last_used and last_used < cutoff:
                    # Check if it's not a dependency
                    is_dependency = any(name in deps for deps in self.dependencies.values())
                    if not is_dependency:
                        to_remove.append(name)

            for name in to_remove:
                await self.unregister(name)

            logger.info(f"Cleaned up {len(to_remove)} stale capabilities")
            return len(to_remove)

    def export_manifest(self) -> Dict[str, Any]:
        """Export a manifest of all capabilities"""
        manifest = {"version": "1.0", "generated": datetime.now().isoformat(), "capabilities": {}}

        for name, cap in self.capabilities.items():
            manifest["capabilities"][name] = {
                "type": cap.type,
                "description": cap.description,
                "available": cap.available,
                "category": None,
                "dependencies": list(self.dependencies.get(name, [])),
                "conflicts": list(self.conflicts.get(name, [])),
                "success_rate": cap.success_rate,
                "usage_count": self.usage_stats.get(name, {}).get("count", 0),
            }

            # Find category
            for cat, names in self.categories.items():
                if name in names:
                    manifest["capabilities"][name]["category"] = cat.value
                    break

        return manifest

    async def import_manifest(self, manifest: Dict[str, Any]) -> int:
        """Import capabilities from a manifest"""
        imported = 0

        for name, data in manifest.get("capabilities", {}).items():
            if name not in self.capabilities:
                cap = Capability(
                    name=name,
                    type=data["type"],
                    description=data["description"],
                    available=data["available"],
                    success_rate=data.get("success_rate", 1.0),
                )

                # Determine category
                category = None
                if data.get("category"):
                    try:
                        category = CapabilityCategory(data["category"])
                    except ValueError:
                        pass

                if await self.register(cap, category):
                    imported += 1

                    # Add dependencies
                    for dep in data.get("dependencies", []):
                        await self.add_dependency(name, dep)

                    # Add conflicts
                    for conf in data.get("conflicts", []):
                        await self.add_conflict(name, conf)

        logger.info(f"Imported {imported} capabilities from manifest")
        return imported
