#!/usr/bin/env python3
"""
Gatekeeper Agent Module

Main gatekeeper agent that combines auto-attach and context analysis functionality.
Can be integrated into any agent that needs intelligent context management.
"""

import json
from dataclasses import asdict, dataclass
from typing import Any

from auto_attach import AutoAttach
from context_analyzer import ContextAnalysis, ContextAnalyzer


@dataclass
class GatekeeperResult:
    """Result of gatekeeper processing."""

    original_files: list[str]
    recommended_files: list[str]
    final_files: list[str]
    context_analysis: ContextAnalysis
    auto_attach_results: dict[str, Any]
    processing_summary: str
    confidence_score: float


class GatekeeperAgent:
    """Main gatekeeper agent for intelligent context management."""

    def __init__(self, dependencies_file: str = ".proj-intel/file_dependencies.json"):
        self.auto_attach = AutoAttach(dependencies_file)
        self.context_analyzer = ContextAnalyzer()
        self.verbose = False

    def set_verbose(self, verbose: bool = True):
        """Set verbose mode for detailed logging."""
        self.verbose = verbose

    def process_request(
        self,
        user_request: str,
        user_files: list[str] = None,
        max_files: int = 50,
        min_confidence: float = 0.5,
    ) -> GatekeeperResult:
        """
        Process a user request to determine optimal context.

        Args:
            user_request: The user's request/prompt
            user_files: Files provided by the user (optional)
            max_files: Maximum number of files to include in final result
            min_confidence: Minimum confidence threshold for recommendations

        Returns:
            GatekeeperResult with optimized file list and analysis
        """
        user_files = user_files or []

        if self.verbose:
            print(f"🔍 Gatekeeper processing request: {user_request[:100]}...")
            print(f"📁 User files: {user_files}")

        # Step 1: Analyze the request context
        context_analysis = self.context_analyzer.analyze_request(
            user_request, user_files
        )

        if self.verbose:
            print(f"📊 Context analysis: {context_analysis.analysis_summary}")
            print(f"🎯 Confidence: {context_analysis.confidence_score:.2f}")

        # Step 2: Auto-attach related files if user provided files
        auto_attach_results = {}
        recommended_files = list(user_files)  # Start with user files

        if user_files and self.auto_attach.is_loaded():
            auto_attach_results = self._perform_auto_attach(user_files)
            recommended_files.extend(auto_attach_results.get("related_files", []))

        # Step 3: Apply context analysis recommendations
        recommended_files = self._apply_context_recommendations(
            recommended_files, context_analysis, min_confidence
        )

        # Step 4: Filter and limit files
        final_files = self._filter_and_limit_files(
            recommended_files, max_files, context_analysis
        )

        # Step 5: Create processing summary
        processing_summary = self._create_processing_summary(
            user_files,
            recommended_files,
            final_files,
            context_analysis,
            auto_attach_results,
        )

        # Step 6: Calculate final confidence
        final_confidence = self._calculate_final_confidence(
            context_analysis, auto_attach_results, len(final_files)
        )

        return GatekeeperResult(
            original_files=user_files,
            recommended_files=recommended_files,
            final_files=final_files,
            context_analysis=context_analysis,
            auto_attach_results=auto_attach_results,
            processing_summary=processing_summary,
            confidence_score=final_confidence,
        )

    def _perform_auto_attach(self, user_files: list[str]) -> dict[str, Any]:
        """Perform auto-attach analysis on user files."""
        if not self.auto_attach.is_loaded():
            return {"error": "Dependencies not loaded"}

        related_files = self.auto_attach.find_related_files(
            user_files, verbose=self.verbose
        )

        # Analyze each file for detailed information
        file_analyses = {}
        for file_path in user_files:
            analysis = self.auto_attach.analyze_file_dependencies(file_path)
            if analysis:
                file_analyses[file_path] = analysis

        return {
            "related_files": related_files,
            "file_analyses": file_analyses,
            "total_related": len(related_files),
            "original_count": len(user_files),
        }

    def _apply_context_recommendations(
        self,
        current_files: list[str],
        context_analysis: ContextAnalysis,
        min_confidence: float,
    ) -> list[str]:
        """Apply context analysis recommendations to file list."""
        # Filter recommendations by confidence
        filtered_recommendations = (
            self.context_analyzer.filter_recommendations_by_confidence(
                context_analysis.recommended_context, min_confidence
            )
        )

        # Get high-priority recommendations
        priority_recommendations = self.context_analyzer.get_priority_recommendations(
            filtered_recommendations, max_priority=3
        )

        # Apply recommendations
        enhanced_files = list(current_files)

        for rec in priority_recommendations:
            if rec.context_type == "files" and rec.file_paths:
                enhanced_files.extend(rec.file_paths)
            elif rec.context_type == "tests":
                # Add test files if available
                test_files = self._find_test_files(current_files)
                enhanced_files.extend(test_files)
            elif rec.context_type == "config":
                # Add config files if available
                config_files = self._find_config_files(current_files)
                enhanced_files.extend(config_files)
            elif rec.context_type == "documentation":
                # Add documentation files if available
                doc_files = self._find_documentation_files(current_files)
                enhanced_files.extend(doc_files)

        # Remove duplicates while preserving order
        seen = set()
        unique_files = []
        for file_path in enhanced_files:
            if file_path not in seen:
                seen.add(file_path)
                unique_files.append(file_path)

        return unique_files

    def _filter_and_limit_files(
        self, files: list[str], max_files: int, context_analysis: ContextAnalysis
    ) -> list[str]:
        """Filter and limit files based on context analysis."""
        if len(files) <= max_files:
            return files

        # Prioritize files based on context analysis
        prioritized_files = self._prioritize_files(files, context_analysis)

        # Take the top files up to the limit
        return prioritized_files[:max_files]

    def _prioritize_files(
        self, files: list[str], context_analysis: ContextAnalysis
    ) -> list[str]:
        """Prioritize files based on context analysis."""
        # Simple prioritization: user files first, then by type
        user_files = set(context_analysis.user_files)

        def priority_key(file_path):
            # User files get highest priority
            if file_path in user_files:
                return (0, file_path)

            # Then prioritize by file type
            file_info = self.auto_attach.get_file_info(file_path)
            file_type = file_info.get("file_type", "unknown")

            # Priority order: source > config > test > documentation
            type_priority = {"source": 1, "config": 2, "test": 3, "documentation": 4}

            return (type_priority.get(file_type, 5), file_path)

        return sorted(files, key=priority_key)

    def _find_test_files(self, current_files: list[str]) -> list[str]:
        """Find test files related to current files."""
        if not self.auto_attach.is_loaded():
            return []

        test_files = []
        for file_path in current_files:
            file_info = self.auto_attach.get_file_info(file_path)
            if file_info.get("file_type") == "test":
                test_files.append(file_path)

        return test_files

    def _find_config_files(self, current_files: list[str]) -> list[str]:
        """Find config files related to current files."""
        if not self.auto_attach.is_loaded():
            return []

        config_files = []
        for file_path in current_files:
            file_info = self.auto_attach.get_file_info(file_path)
            if file_info.get("file_type") == "config":
                config_files.append(file_path)

        return config_files

    def _find_documentation_files(self, current_files: list[str]) -> list[str]:
        """Find documentation files related to current files."""
        if not self.auto_attach.is_loaded():
            return []

        doc_files = []
        for file_path in current_files:
            file_info = self.auto_attach.get_file_info(file_path)
            if file_info.get("file_type") == "documentation":
                doc_files.append(file_path)

        return doc_files

    def _create_processing_summary(
        self,
        user_files: list[str],
        recommended_files: list[str],
        final_files: list[str],
        context_analysis: ContextAnalysis,
        auto_attach_results: dict[str, Any],
    ) -> str:
        """Create a summary of the processing."""
        summary_parts = []

        summary_parts.append(f"User provided {len(user_files)} files")
        auto_attach_count = auto_attach_results.get("total_related", 0) - len(
            user_files
        )
        summary_parts.append(
            f"Auto-attach found {max(0, auto_attach_count)} related files"
        )
        summary_parts.append(f"Final selection: {len(final_files)} files")
        summary_parts.append(f"Context analysis: {context_analysis.analysis_summary}")

        return "; ".join(summary_parts)

    def _calculate_final_confidence(
        self,
        context_analysis: ContextAnalysis,
        auto_attach_results: dict[str, Any],
        final_file_count: int,
    ) -> float:
        """Calculate final confidence score."""
        # Start with context analysis confidence
        confidence = context_analysis.confidence_score

        # Boost confidence if auto-attach found relevant files
        if auto_attach_results.get("total_related", 0) > 0:
            confidence += 0.1

        # Reduce confidence if too many files (might be noise)
        if final_file_count > 30:
            confidence -= 0.1

        # Boost confidence if we have a good balance
        if 5 <= final_file_count <= 20:
            confidence += 0.1

        return max(0.0, min(1.0, confidence))

    def get_file_analysis(self, file_path: str) -> dict[str, Any]:
        """Get detailed analysis for a specific file."""
        if not self.auto_attach.is_loaded():
            return {}

        return self.auto_attach.analyze_file_dependencies(file_path)

    def export_result(self, result: GatekeeperResult, output_file: str):
        """Export gatekeeper result to JSON file."""
        try:
            # Convert dataclass to dict for JSON serialization
            result_dict = asdict(result)

            with open(output_file, "w") as f:
                json.dump(result_dict, f, indent=2)

            if self.verbose:
                print(f"💾 Result exported to: {output_file}")

        except Exception as e:
            if self.verbose:
                print(f"❌ Error exporting result: {e}")

    def load_dependencies(self) -> bool:
        """Load dependencies for auto-attach functionality."""
        return self.auto_attach.load_dependencies()

    def is_ready(self) -> bool:
        """Check if the gatekeeper is ready to process requests."""
        return self.auto_attach.is_loaded()
