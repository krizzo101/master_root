"""Prompt manager for opsvi-llm.

Manages prompt templates and generation.
"""

from typing import Dict, Any, Optional, List
import json
import logging
import asyncio
from dataclasses import dataclass, asdict
from pathlib import Path

from opsvi_llm.core.base import OpsviLlmManager
from opsvi_llm.config.settings import OpsviLlmConfig
from opsvi_llm.exceptions.base import OpsviLlmError

logger = logging.getLogger(__name__)


@dataclass
class PromptTemplate:
    """Prompt template data holder."""

    name: str
    template: str
    variables: List[str]
    version: int = 1

    def format(self, **kwargs) -> str:
        """Render the template with provided keyword arguments.

        Missing keys from kwargs will raise a KeyError coming from str.format.
        """
        return self.template.format(**kwargs)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "PromptTemplate":
        return PromptTemplate(
            name=d["name"],
            template=d["template"],
            variables=d.get("variables", []),
            version=int(d.get("version", 1)),
        )


class OpsviLlmPromptManager(OpsviLlmManager):
    """Prompt manager for opsvi-llm.

    Provides in-memory registry of templates and optional file persistence.
    """

    def __init__(self, config: OpsviLlmConfig):
        super().__init__(config=config)
        self.templates: Dict[str, PromptTemplate] = {}
        self._storage_path: Optional[Path] = None
        if getattr(config, "prompt_storage_path", None):
            self._storage_path = Path(config.prompt_storage_path)
            # ensure directory exists
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        # lightweight lock for async safety
        self._lock = asyncio.Lock()

    async def register_template(self, name: str, template: str,
                                variables: List[str] = None,
                                *, increment_version: bool = False) -> None:
        """Register or update a prompt template.

        If template exists and increment_version is True, bump version.
        """
        variables = variables or []
        async with self._lock:
            existing = self.templates.get(name)
            if existing:
                version = existing.version + 1 if increment_version else existing.version
                self.templates[name] = PromptTemplate(name=name, template=template,
                                                      variables=variables, version=version)
                logger.info("Updated prompt template: %s (v%d)", name, version)
            else:
                self.templates[name] = PromptTemplate(name=name, template=template,
                                                      variables=variables, version=1)
                logger.info("Registered prompt template: %s", name)
            await self._persist_one(name)

    async def get_template(self, name: str) -> Optional[PromptTemplate]:
        """Get a prompt template by name. Attempts to load from disk if missing."""
        async with self._lock:
            tmpl = self.templates.get(name)
            if tmpl is None and self._storage_path:
                await self._load_all()
                tmpl = self.templates.get(name)
            return tmpl

    async def format_prompt(self, name: str, **kwargs) -> str:
        """Format a prompt template by name with given kwargs."""
        template = await self.get_template(name)
        if not template:
            raise OpsviLlmError(f"Template not found: {name}")
        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise OpsviLlmError(f"Missing variable for template '{name}': {e}") from e
        except Exception as e:
            raise OpsviLlmError(f"Error formatting template '{name}': {e}") from e

    async def list_templates(self) -> List[Dict[str, Any]]:
        """Return metadata for all templates."""
        async with self._lock:
            return [t.to_dict() for t in self.templates.values()]

    # Persistence helpers
    async def _persist_one(self, name: str) -> None:
        if not self._storage_path:
            return
        async with self._lock:
            tmpl = self.templates.get(name)
            if not tmpl:
                return
            try:
                # write per-template JSON file
                path = self._storage_path.with_name(f"{name}.json")
                tmp = path.with_suffix(path.suffix + ".tmp")
                path.parent.mkdir(parents=True, exist_ok=True)
                data = tmpl.to_dict()
                # synchronous file IO inside async is fine for small files; keep simple
                with tmp.open("w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                tmp.replace(path)
            except Exception as e:
                logger.exception("Failed to persist template %s: %s", name, e)

    async def _load_all(self) -> None:
        if not self._storage_path:
            return
        async with self._lock:
            try:
                parent = self._storage_path.parent
                if not parent.exists():
                    return
                for file in parent.glob("*.json"):
                    try:
                        with file.open("r", encoding="utf-8") as f:
                            data = json.load(f)
                        tmpl = PromptTemplate.from_dict(data)
                        self.templates[tmpl.name] = tmpl
                    except Exception:
                        logger.exception("Failed to load template from %s", file)
            except Exception:
                logger.exception("Failed to load templates from storage")

    async def remove_template(self, name: str) -> None:
        """Remove a template from memory and disk if stored."""
        async with self._lock:
            if name in self.templates:
                del self.templates[name]
            if self._storage_path:
                path = self._storage_path.with_name(f"{name}.json")
                try:
                    if path.exists():
                        path.unlink()
                except Exception:
                    logger.exception("Failed to remove template file %s", path)
