"""File system watcher for cache invalidation."""

import asyncio
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Set

import structlog
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

logger = structlog.get_logger(__name__)


class CacheInvalidationHandler(FileSystemEventHandler):
    """Handle file system events for cache invalidation."""

    def __init__(self, cache_manager, invalidation_callback: Optional[Callable] = None):
        """Initialize the cache invalidation handler.

        Args:
            cache_manager: The CacheManager instance to invalidate
            invalidation_callback: Optional callback for custom invalidation logic
        """
        super().__init__()
        self.cache_manager = cache_manager
        self.invalidation_callback = invalidation_callback

        # File extensions that should trigger cache invalidation
        self.watched_extensions = {
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".java",
            ".cpp",
            ".c",
            ".h",
            ".go",
            ".rs",
            ".php",
            ".rb",
            ".scala",
            ".kt",
            ".swift",
            ".m",
            ".json",
            ".yaml",
            ".yml",
            ".toml",
            ".xml",
            ".ini",
            ".cfg",
            ".md",
            ".txt",
            ".rst",
            ".asciidoc",
        }

        # Directories to ignore
        self.ignore_dirs = {
            "__pycache__",
            ".git",
            ".svn",
            ".hg",
            ".bzr",
            "node_modules",
            ".pytest_cache",
            ".mypy_cache",
            ".coverage",
            "htmlcov",
            ".tox",
            "venv",
            ".venv",
            "env",
            ".env",
            "dist",
            "build",
            ".idea",
            ".vscode",
        }

    def _should_invalidate(self, file_path: str) -> bool:
        """Check if file changes should trigger cache invalidation."""
        path = Path(file_path)

        # Check if it's in an ignored directory
        if any(ignore_dir in path.parts for ignore_dir in self.ignore_dirs):
            return False

        # Check file extension
        if path.suffix.lower() in self.watched_extensions:
            return True

        # Check if it's a special file we care about
        special_files = {
            "requirements.txt",
            "setup.py",
            "pyproject.toml",
            "package.json",
            "Cargo.toml",
            "pom.xml",
            "build.gradle",
            "Makefile",
            "CMakeLists.txt",
        }

        return path.name.lower() in special_files

    async def _invalidate_file_cache(self, file_path: str, event_type: str) -> None:
        """Invalidate cache entries for a specific file."""
        try:
            if not self._should_invalidate(file_path):
                return

            # Invalidate the specific file cache
            await self.cache_manager.invalidate_file(file_path)

            # Call custom invalidation callback if provided
            if self.invalidation_callback:
                await self.invalidation_callback(
                    file_path, event_type, self.cache_manager
                )

            logger.info(
                "Cache invalidated for file", file_path=file_path, event_type=event_type
            )

        except Exception as e:
            logger.error("Cache invalidation error", file_path=file_path, error=str(e))

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification events."""
        if not event.is_directory:
            asyncio.create_task(self._invalidate_file_cache(event.src_path, "modified"))

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events."""
        if not event.is_directory:
            asyncio.create_task(self._invalidate_file_cache(event.src_path, "created"))

    def on_deleted(self, event: FileSystemEvent) -> None:
        """Handle file deletion events."""
        if not event.is_directory:
            asyncio.create_task(self._invalidate_file_cache(event.src_path, "deleted"))

    def on_moved(self, event: FileSystemEvent) -> None:
        """Handle file move events."""
        if not event.is_directory:
            # Invalidate both old and new paths
            if hasattr(event, "dest_path"):
                asyncio.create_task(
                    self._invalidate_file_cache(event.src_path, "moved_from")
                )
                asyncio.create_task(
                    self._invalidate_file_cache(event.dest_path, "moved_to")
                )
            else:
                asyncio.create_task(
                    self._invalidate_file_cache(event.src_path, "moved")
                )


class CacheWatcher:
    """File system watcher for automatic cache invalidation."""

    def __init__(
        self,
        cache_manager,
        watch_paths: Optional[Set[str]] = None,
        invalidation_callback: Optional[Callable] = None,
    ):
        """Initialize the cache watcher.

        Args:
            cache_manager: The CacheManager instance to invalidate
            watch_paths: Set of paths to watch (defaults to current directory)
            invalidation_callback: Optional callback for custom invalidation logic
        """
        self.cache_manager = cache_manager
        self.watch_paths = watch_paths or {"."}
        self.invalidation_callback = invalidation_callback

        self.observer: Optional[Observer] = None
        self.handler = CacheInvalidationHandler(cache_manager, invalidation_callback)

        self._running = False

    async def start(self) -> None:
        """Start watching for file changes."""
        if self._running:
            logger.warning("Cache watcher already running")
            return

        try:
            self.observer = Observer()

            for watch_path in self.watch_paths:
                path = Path(watch_path).resolve()
                if path.exists():
                    self.observer.schedule(self.handler, str(path), recursive=True)
                    logger.info("Started watching path", path=str(path))
                else:
                    logger.warning("Watch path does not exist", path=str(path))

            self.observer.start()
            self._running = True

            logger.info("Cache watcher started", paths=list(self.watch_paths))

        except Exception as e:
            logger.error("Failed to start cache watcher", error=str(e))
            raise

    async def stop(self) -> None:
        """Stop watching for file changes."""
        if not self._running or not self.observer:
            return

        try:
            self.observer.stop()
            self.observer.join(timeout=5.0)  # Wait up to 5 seconds for cleanup
            self._running = False

            logger.info("Cache watcher stopped")

        except Exception as e:
            logger.error("Error stopping cache watcher", error=str(e))

    def is_running(self) -> bool:
        """Check if the watcher is currently running."""
        return self._running

    async def add_watch_path(self, path: str) -> None:
        """Add a new path to watch."""
        path_obj = Path(path).resolve()
        if not path_obj.exists():
            logger.warning("Cannot add non-existent watch path", path=str(path_obj))
            return

        self.watch_paths.add(str(path_obj))

        if self._running and self.observer:
            self.observer.schedule(self.handler, str(path_obj), recursive=True)
            logger.info("Added watch path", path=str(path_obj))

    async def remove_watch_path(self, path: str) -> None:
        """Remove a path from watching."""
        path_obj = Path(path).resolve()
        path_str = str(path_obj)

        if path_str in self.watch_paths:
            self.watch_paths.remove(path_str)
            logger.info("Removed watch path", path=path_str)

            # Note: watchdog Observer doesn't have a direct way to unschedule
            # a specific path, so we'd need to restart the observer to fully
            # remove the path. For now, just log the removal.


async def project_invalidation_callback(
    file_path: str, event_type: str, cache_manager
) -> None:
    """Custom invalidation callback for project-specific logic."""
    try:
        path = Path(file_path)

        # Invalidate project stats cache when important files change
        important_files = {
            "pyproject.toml",
            "setup.py",
            "requirements.txt",
            "package.json",
            "Cargo.toml",
            "pom.xml",
            "build.gradle",
        }

        if path.name.lower() in important_files:
            # Invalidate all project stats
            await cache_manager.invalidate_pattern("stats:*")
            logger.info(
                "Project stats cache invalidated",
                trigger_file=file_path,
                event_type=event_type,
            )

        # Invalidate specific caches based on file patterns
        if path.suffix in {".py", ".js", ".ts", ".java", ".go"}:
            # Source code files might affect complexity metrics, call graphs, etc.
            stats_to_invalidate = [
                "complexity",
                "call_graph",
                "imports",
                "quality_metrics",
            ]
            for stat in stats_to_invalidate:
                await cache_manager.set_project_stats(stat, None)

        logger.debug(
            "Custom invalidation completed", file_path=file_path, event_type=event_type
        )

    except Exception as e:
        logger.error(
            "Custom invalidation callback error", file_path=file_path, error=str(e)
        )
