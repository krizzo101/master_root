"""
EDA Orchestrator
================

Main orchestrator that coordinates all EDA components.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict, List

from eda.analysis import (
    analyze_dependencies,
    analyze_project_quality,
    build_module_graph,
    detect_code_smells,
    detect_entry_points,
    extract_functions_and_classes,
    scan_project,
)
from eda.config import EDAConfig
from eda.generation import build_document
from eda.qa import score_document, validate_document


class EDAOrchestrator:
    """Main orchestrator for Enhanced Documentation Agent."""

    def __init__(self, cfg: EDAConfig) -> None:
        """
        Initialize EDA orchestrator.

        Args:
            cfg: EDA configuration
        """
        self.cfg = cfg

    async def run(self) -> Dict[str, Any]:
        """
        Run the complete documentation generation pipeline.

        Returns:
            Complete documentation result
        """
        try:
            # Phase 1: Project Analysis
            analysis = await self._analyze_project()

            # Phase 2: Document Generation
            document = await build_document(self.cfg, analysis)

            # Phase 3: Quality Assurance
            document = await self._apply_quality_assurance(document)

            # Phase 4: Save Output
            if self.cfg.save_path:
                await self._save_output(document)

            return document

        except Exception as e:
            return {
                "error": str(e),
                "content": f"Error generating documentation: {e}",
                "diagrams": [],
                "metadata": {},
                "quality_score": 0.0,
                "generation_time_ms": 0,
                "errors": [str(e)],
                "warnings": [],
            }

    async def _analyze_project(self) -> Dict[str, Any]:
        """
        Perform comprehensive project analysis.

        Returns:
            Complete analysis results
        """
        # Scan project files
        files = scan_project(self.cfg)

        # Run analysis tasks in parallel
        analysis_tasks = {
            "module_graph": asyncio.to_thread(build_module_graph, files),
            "dependencies": asyncio.to_thread(
                analyze_dependencies, self.cfg.project_path
            ),
            "entry_points": asyncio.to_thread(detect_entry_points, files),
            "quality_analysis": asyncio.to_thread(analyze_project_quality, files),
            "code_smells": asyncio.to_thread(detect_code_smells, files),
            "functions_and_classes": asyncio.to_thread(
                extract_functions_and_classes, files
            ),
        }

        # Execute all analysis tasks
        results = await asyncio.gather(*analysis_tasks.values(), return_exceptions=True)

        # Process results and handle exceptions
        analysis = {"files": files, "project_path": str(self.cfg.project_path)}

        for i, (key, result) in enumerate(zip(analysis_tasks.keys(), results)):
            if isinstance(result, Exception):
                analysis[f"{key}_error"] = str(result)
                analysis[key] = {} if key == "module_graph" else []
            else:
                analysis[key] = result

        return analysis

    async def _apply_quality_assurance(
        self, document: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply quality assurance to generated document.

        Args:
            document: Generated document

        Returns:
            Document with QA applied
        """
        # Validate document
        validation_result = validate_document(document, self.cfg)
        if validation_result.get("errors"):
            document["errors"].extend(validation_result["errors"])

        if validation_result.get("warnings"):
            document["warnings"].extend(validation_result["warnings"])

        # Score document
        document["quality_score"] = score_document(document, self.cfg)

        # Apply review cycles if configured
        if self.cfg.review_cycles > 0:
            document = await self._apply_review_cycles(document)

        return document

    async def _apply_review_cycles(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply multiple review cycles to improve document quality.

        Args:
            document: Document to review

        Returns:
            Improved document
        """
        for cycle in range(self.cfg.review_cycles):
            # Validate current document
            validation = validate_document(document, self.cfg)

            # If no critical errors, continue
            if not validation.get("critical_errors"):
                break

            # Try to fix issues (simplified - in real implementation, this would be more sophisticated)
            document["warnings"].append(
                f"Review cycle {cycle + 1}: {len(validation.get('errors', []))} issues found"
            )

        return document

    async def _save_output(self, document: Dict[str, Any]) -> None:
        """
        Save generated documentation to files.

        Args:
            document: Generated document
        """
        try:
            save_path = Path(self.cfg.save_path)
            save_path.mkdir(parents=True, exist_ok=True)

            # Save main content
            content_path = save_path / f"{self.cfg.doc_type}_documentation.md"
            content_path.write_text(document["content"], encoding="utf-8")

            # Save diagrams
            if document["diagrams"]:
                diagrams_dir = save_path / "diagrams"
                diagrams_dir.mkdir(exist_ok=True)

                for i, diagram in enumerate(document["diagrams"], 1):
                    diagram_path = diagrams_dir / f"diagram_{i}.mmd"
                    diagram_path.write_text(diagram, encoding="utf-8")

            # Save metadata
            import json

            metadata_path = save_path / "metadata.json"
            metadata_path.write_text(
                json.dumps(document["metadata"], indent=2, default=str),
                encoding="utf-8",
            )

            # Save code examples if present
            if document.get("code_examples"):
                examples_dir = save_path / "examples"
                examples_dir.mkdir(exist_ok=True)

                for i, example in enumerate(
                    document["code_examples"][:10], 1
                ):  # Limit examples
                    example_path = examples_dir / f"example_{i}.py"
                    example_path.write_text(example.get("code", ""), encoding="utf-8")

        except Exception as e:
            document["errors"].append(f"Failed to save output: {e}")

    async def analyze_only(self) -> Dict[str, Any]:
        """
        Perform analysis only without generating documentation.

        Returns:
            Analysis results
        """
        return await self._analyze_project()

    async def generate_from_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate documentation from existing analysis.

        Args:
            analysis: Existing analysis results

        Returns:
            Generated documentation
        """
        document = await build_document(self.cfg, analysis)
        document = await self._apply_quality_assurance(document)

        if self.cfg.save_path:
            await self._save_output(document)

        return document
