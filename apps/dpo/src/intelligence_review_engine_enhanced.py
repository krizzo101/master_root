#!/usr/bin/env python3
"""
Enhanced Intelligence Review Engine with Advanced Enhancement Algorithms

This module provides sophisticated enhancement intelligence including:
- Multi-phase enhancement strategies
- Cross-category synthesis
- Impact scoring algorithms
- Dependency analysis
- Cost-benefit optimization

Author: Agent Orchestrator Team
Date: September 2025
"""

import asyncio
import hashlib
import json
import logging
import re
import time
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Setup import paths
try:
    from ._path_setup import setup_paths
except ImportError:
    from _path_setup import setup_paths
setup_paths()

# Import from agent-orchestrator
from src.generic_orchestrator import AgentTask, GenericOrchestrator
from src.intelligence_review_engine import (
    EnhancementCategory,
    EnhancementResult,
    IntelligenceReviewEngine,
)
from src.specialist_agent_templates import (
    SpecialistAgentTemplate,
    SpecialistAgentTemplates,
)

logger = logging.getLogger(__name__)


@dataclass
class EnhancementScore:
    """Scoring model for enhancements"""

    impact_score: float  # 0-1: Business impact
    effort_score: float  # 0-1: Implementation effort (lower is better)
    innovation_score: float  # 0-1: Technical innovation level
    risk_score: float  # 0-1: Implementation risk (lower is better)
    dependency_score: float  # 0-1: How many other enhancements depend on this

    @property
    def composite_score(self) -> float:
        """Calculate composite score for prioritization"""
        # High impact, low effort, high innovation, low risk, high dependency = high score
        return (
            self.impact_score * 0.35
            + (1 - self.effort_score) * 0.25
            + self.innovation_score * 0.15
            + (1 - self.risk_score) * 0.15
            + self.dependency_score * 0.10
        )


@dataclass
class EnhancementNode:
    """Node in the enhancement dependency graph"""

    enhancement_id: str
    category: str
    title: str
    description: str
    score: EnhancementScore
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    technologies: List[str] = field(default_factory=list)
    implementation_phase: int = 0  # Which phase this belongs to

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "id": self.enhancement_id,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "score": asdict(self.score),
            "composite_score": self.score.composite_score,
            "dependencies": list(self.dependencies),
            "dependents": list(self.dependents),
            "technologies": self.technologies,
            "phase": self.implementation_phase,
        }


class EnhancementIntelligenceEngine:
    """
    Advanced enhancement intelligence engine with sophisticated algorithms
    """

    # Impact/Effort matrix for categorization
    ENHANCEMENT_QUADRANTS = {
        "quick_wins": {"impact": "high", "effort": "low"},
        "major_projects": {"impact": "high", "effort": "high"},
        "fill_ins": {"impact": "low", "effort": "low"},
        "thankless_tasks": {"impact": "low", "effort": "high"},
    }

    # Technology compatibility matrix
    TECH_COMPATIBILITY = {
        "react": ["next.js", "redux", "react-query", "tailwindcss", "vite"],
        "vue": ["nuxt.js", "vuex", "pinia", "tailwindcss", "vite"],
        "fastapi": ["sqlalchemy", "pydantic", "redis", "celery", "postgresql"],
        "django": ["django-rest-framework", "celery", "redis", "postgresql"],
        "kubernetes": ["helm", "istio", "prometheus", "grafana", "argocd"],
        "aws": ["terraform", "cloudformation", "cdk", "s3", "lambda", "dynamodb"],
    }

    def __init__(
        self,
        orchestrator: Optional[GenericOrchestrator] = None,
        parallel_agents: int = 6,
        output_dir: str = None,
    ):
        """Initialize the enhanced intelligence engine"""
        self.base_engine = IntelligenceReviewEngine(
            orchestrator=orchestrator,
            parallel_agents=parallel_agents,
            output_dir=output_dir,
        )
        self.templates = SpecialistAgentTemplates.get_all_templates()
        self.enhancement_graph: Dict[str, EnhancementNode] = {}
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        logger.info(
            f"Enhanced Intelligence Engine initialized - Session: {self.session_id}"
        )

    async def enhance_with_intelligence(
        self,
        original_request: str,
        project_context: Dict[str, Any] = None,
        optimization_goals: List[str] = None,
        constraints: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Enhance request with advanced intelligence algorithms

        Args:
            original_request: The original user request
            project_context: Project-specific context
            optimization_goals: Specific goals to optimize for
            constraints: Constraints like budget, timeline, team size

        Returns:
            Comprehensive enhancement package with prioritization
        """
        start_time = time.time()

        # Phase 1: Deploy specialist agents
        logger.info("Phase 1: Deploying specialist agents...")
        specialist_results = await self._deploy_specialists(
            original_request, project_context, optimization_goals
        )

        # Phase 2: Parse and score enhancements
        logger.info("Phase 2: Scoring and analyzing enhancements...")
        enhancements = self._parse_and_score_enhancements(
            specialist_results, constraints
        )

        # Phase 3: Build dependency graph
        logger.info("Phase 3: Building enhancement dependency graph...")
        self._build_dependency_graph(enhancements)

        # Phase 4: Optimize enhancement selection
        logger.info("Phase 4: Optimizing enhancement selection...")
        optimized_plan = self._optimize_enhancement_selection(
            constraints=constraints, optimization_goals=optimization_goals
        )

        # Phase 5: Generate implementation roadmap
        logger.info("Phase 5: Generating implementation roadmap...")
        roadmap = self._generate_implementation_roadmap(optimized_plan)

        # Phase 6: Synthesize final specification
        logger.info("Phase 6: Synthesizing enhanced specification...")
        enhanced_spec = self._synthesize_advanced_specification(
            original_request, optimized_plan, roadmap, project_context
        )

        # Phase 7: Generate metrics and insights
        logger.info("Phase 7: Generating metrics and insights...")
        metrics = self._generate_enhancement_metrics(optimized_plan)

        # Compile final result
        result = {
            "original_request": original_request,
            "enhanced_specification": enhanced_spec,
            "enhancement_plan": optimized_plan,
            "implementation_roadmap": roadmap,
            "metrics": metrics,
            "enhancements_by_category": self._group_enhancements_by_category(
                enhancements
            ),
            "quick_wins": self._identify_quick_wins(enhancements),
            "innovation_highlights": self._identify_innovations(enhancements),
            "risk_analysis": self._analyze_risks(enhancements),
            "cost_benefit_analysis": self._perform_cost_benefit_analysis(
                optimized_plan, constraints
            ),
            "metadata": {
                "session_id": self.session_id,
                "duration_seconds": time.time() - start_time,
                "total_enhancements_identified": len(enhancements),
                "enhancements_selected": len(optimized_plan),
                "estimated_impact_score": self._calculate_total_impact(optimized_plan),
                "timestamp": datetime.now().isoformat(),
            },
        }

        # Save comprehensive results
        self._save_enhanced_results(result)

        logger.info(
            f"Enhanced intelligence review complete - {len(optimized_plan)} enhancements selected"
        )

        return result

    async def _deploy_specialists(
        self, request: str, context: Dict, goals: List[str]
    ) -> Dict[str, Any]:
        """Deploy all specialist agents with enhanced templates"""
        tasks = []

        for agent_type, template in self.templates.items():
            # Customize prompt based on optimization goals
            prompt = template.prompt_template.format(
                request=request,
                context=json.dumps(context) if context else "No additional context",
            )

            # Add optimization goals to prompt if specified
            if goals:
                prompt += f"\n\nOPTIMIZATION PRIORITIES: {', '.join(goals)}"

            task = AgentTask(
                task_id=f"{agent_type}_{hashlib.md5(request.encode()).hexdigest()[:8]}",
                task_type=agent_type,
                prompt=prompt,
                context={
                    "template": template.name,
                    "expertise_areas": template.expertise_areas,
                    "mcp_tools": template.mcp_tools,
                },
            )
            tasks.append(task)

        # Execute with orchestrator
        orchestrator = self.base_engine.orchestrator or GenericOrchestrator(
            max_parallel_agents=len(tasks), output_dir=str(self.base_engine.session_dir)
        )

        results = await orchestrator.execute_tasks(tasks)
        return results

    def _parse_and_score_enhancements(
        self, results: Dict, constraints: Dict
    ) -> List[EnhancementNode]:
        """Parse specialist results and score each enhancement"""
        enhancements = []
        enhancement_id = 0

        for task_id, result in results.items():
            if result["status"] != "completed" or not result.get("result"):
                continue

            # Extract category from task_id
            category = task_id.split("_")[0]

            try:
                # Parse JSON response
                parsed = self._parse_json_response(result["result"])

                # Process each enhancement
                for item in self._extract_enhancements_from_parsed(parsed):
                    enhancement_id += 1

                    # Calculate scores
                    score = self._calculate_enhancement_score(item, constraints)

                    # Create enhancement node
                    node = EnhancementNode(
                        enhancement_id=f"E{enhancement_id:03d}",
                        category=category,
                        title=item.get(
                            "title",
                            item.get("feature", item.get("pattern", "Enhancement")),
                        ),
                        description=item.get("description", ""),
                        score=score,
                        technologies=item.get("technologies", []),
                    )

                    enhancements.append(node)
                    self.enhancement_graph[node.enhancement_id] = node

            except Exception as e:
                logger.error(f"Failed to parse {category} results: {e}")

        return enhancements

    def _calculate_enhancement_score(
        self, item: Dict, constraints: Dict
    ) -> EnhancementScore:
        """Calculate multi-dimensional score for an enhancement"""
        # Impact scoring
        impact_map = {"High": 0.9, "Medium": 0.5, "Low": 0.2}
        impact_score = impact_map.get(item.get("impact", "Medium"), 0.5)

        # Effort scoring (inverted - low effort = high score)
        effort_map = {"Low": 0.2, "Medium": 0.5, "High": 0.8}
        effort_score = effort_map.get(item.get("effort", "Medium"), 0.5)

        # Innovation scoring
        innovation_score = (
            item.get("innovation_score", 5) / 10.0
            if "innovation_score" in item
            else 0.5
        )

        # Risk scoring
        risk_factors = len(item.get("risks", [])) + len(item.get("challenges", []))
        risk_score = min(risk_factors * 0.15, 1.0)

        # Dependency will be calculated later in graph building
        dependency_score = 0.0

        # Adjust scores based on constraints
        if constraints:
            if constraints.get("budget") == "low" and item.get("cost"):
                if "high" in str(item["cost"]).lower():
                    effort_score = min(effort_score + 0.3, 1.0)

            if constraints.get("timeline") == "aggressive":
                if item.get("effort") == "High":
                    effort_score = min(effort_score + 0.2, 1.0)

        return EnhancementScore(
            impact_score=impact_score,
            effort_score=effort_score,
            innovation_score=innovation_score,
            risk_score=risk_score,
            dependency_score=dependency_score,
        )

    def _build_dependency_graph(self, enhancements: List[EnhancementNode]):
        """Build dependency relationships between enhancements"""
        # Identify dependencies based on technologies and categories
        for i, node1 in enumerate(enhancements):
            for j, node2 in enumerate(enhancements):
                if i >= j:
                    continue

                # Check technology dependencies
                tech_overlap = set(node1.technologies) & set(node2.technologies)
                if tech_overlap:
                    # Determine dependency direction based on categories
                    if self._is_foundational(node1.category, node2.category):
                        node2.dependencies.add(node1.enhancement_id)
                        node1.dependents.add(node2.enhancement_id)
                    elif self._is_foundational(node2.category, node1.category):
                        node1.dependencies.add(node2.enhancement_id)
                        node2.dependents.add(node1.enhancement_id)

        # Update dependency scores
        for node in enhancements:
            node.score.dependency_score = len(node.dependents) / max(
                len(enhancements), 1
            )

    def _is_foundational(self, cat1: str, cat2: str) -> bool:
        """Determine if cat1 is foundational to cat2"""
        foundational_order = [
            "solution-architect",  # Architecture comes first
            "performance-optimizer",  # Then optimization
            "integration-specialist",  # Then integrations
            "development-accelerator",  # Then dev tools
            "innovation-analyst",  # Then innovations
            "research-genius",  # Research supports all
        ]

        try:
            idx1 = foundational_order.index(cat1)
            idx2 = foundational_order.index(cat2)
            return idx1 < idx2
        except ValueError:
            return False

    def _optimize_enhancement_selection(
        self, constraints: Dict, optimization_goals: List[str]
    ) -> List[EnhancementNode]:
        """Optimize enhancement selection using constraint programming"""
        all_enhancements = list(self.enhancement_graph.values())

        # Sort by composite score
        all_enhancements.sort(key=lambda x: x.score.composite_score, reverse=True)

        selected = []
        remaining_budget = constraints.get("budget_units", 100) if constraints else 100
        max_selections = constraints.get("max_enhancements", 20) if constraints else 20

        # Greedy selection with dependency consideration
        for enhancement in all_enhancements:
            if len(selected) >= max_selections:
                break

            # Check if dependencies are met
            deps_met = all(
                dep_id in [s.enhancement_id for s in selected]
                for dep_id in enhancement.dependencies
            )

            if not deps_met:
                continue

            # Estimate cost (simplified)
            cost = self._estimate_enhancement_cost(enhancement)

            if cost <= remaining_budget:
                selected.append(enhancement)
                remaining_budget -= cost

        # Assign implementation phases
        self._assign_implementation_phases(selected)

        return selected

    def _estimate_enhancement_cost(self, enhancement: EnhancementNode) -> float:
        """Estimate relative cost of an enhancement"""
        base_cost = enhancement.score.effort_score * 10
        risk_multiplier = 1 + enhancement.score.risk_score
        return base_cost * risk_multiplier

    def _assign_implementation_phases(self, enhancements: List[EnhancementNode]):
        """Assign enhancements to implementation phases using topological sort"""
        phases = defaultdict(list)
        visited = set()

        def get_phase(node_id: str, memo: Dict[str, int]) -> int:
            if node_id in memo:
                return memo[node_id]

            node = self.enhancement_graph.get(node_id)
            if not node or not node.dependencies:
                phase = 0
            else:
                phase = max(get_phase(dep, memo) for dep in node.dependencies) + 1

            memo[node_id] = phase
            return phase

        phase_memo = {}
        for enhancement in enhancements:
            enhancement.implementation_phase = get_phase(
                enhancement.enhancement_id, phase_memo
            )
            phases[enhancement.implementation_phase].append(enhancement)

    def _generate_implementation_roadmap(
        self, enhancements: List[EnhancementNode]
    ) -> Dict[str, Any]:
        """Generate detailed implementation roadmap"""
        phases = defaultdict(list)

        for enhancement in enhancements:
            phases[enhancement.implementation_phase].append(enhancement)

        roadmap = {
            "phases": [],
            "critical_path": self._identify_critical_path(enhancements),
            "parallel_tracks": self._identify_parallel_tracks(phases),
            "milestones": [],
        }

        for phase_num in sorted(phases.keys()):
            phase_enhancements = phases[phase_num]

            phase_info = {
                "phase_number": phase_num + 1,
                "name": f"Phase {phase_num + 1}: {self._get_phase_theme(phase_enhancements)}",
                "enhancements": [e.to_dict() for e in phase_enhancements],
                "estimated_duration": self._estimate_phase_duration(phase_enhancements),
                "key_deliverables": self._extract_deliverables(phase_enhancements),
                "success_criteria": self._define_success_criteria(phase_enhancements),
            }

            roadmap["phases"].append(phase_info)

            # Add milestone
            roadmap["milestones"].append(
                {
                    "phase": phase_num + 1,
                    "name": f"Complete {phase_info['name']}",
                    "deliverables": phase_info["key_deliverables"][:3],
                }
            )

        return roadmap

    def _get_phase_theme(self, enhancements: List[EnhancementNode]) -> str:
        """Determine theme for a phase based on enhancements"""
        categories = [e.category for e in enhancements]

        if "solution-architect" in categories:
            return "Foundation & Architecture"
        elif "performance-optimizer" in categories:
            return "Optimization & Performance"
        elif "integration-specialist" in categories:
            return "Integration & Connectivity"
        elif "innovation-analyst" in categories:
            return "Innovation & Advanced Features"
        elif "development-accelerator" in categories:
            return "Development Acceleration"
        else:
            return "Implementation"

    def _estimate_phase_duration(self, enhancements: List[EnhancementNode]) -> str:
        """Estimate duration for a phase"""
        total_effort = sum(e.score.effort_score for e in enhancements)

        if total_effort < 1:
            return "1 week"
        elif total_effort < 3:
            return "2-3 weeks"
        elif total_effort < 5:
            return "3-4 weeks"
        else:
            return "4-6 weeks"

    def _extract_deliverables(self, enhancements: List[EnhancementNode]) -> List[str]:
        """Extract key deliverables from enhancements"""
        deliverables = []

        for e in enhancements:
            if "architecture" in e.category:
                deliverables.append(f"Implemented {e.title}")
            elif "performance" in e.category:
                deliverables.append(f"Optimized {e.title}")
            elif "integration" in e.category:
                deliverables.append(f"Integrated {e.title}")
            else:
                deliverables.append(e.title)

        return deliverables[:5]  # Top 5 deliverables

    def _define_success_criteria(
        self, enhancements: List[EnhancementNode]
    ) -> List[str]:
        """Define success criteria for phase"""
        criteria = []

        if any("performance" in e.category for e in enhancements):
            criteria.append("Performance metrics meet or exceed targets")

        if any("integration" in e.category for e in enhancements):
            criteria.append("All integrations tested and functional")

        if any("architecture" in e.category for e in enhancements):
            criteria.append("Architecture implemented and documented")

        criteria.append("All unit tests passing")
        criteria.append("Code review completed")

        return criteria[:3]

    def _identify_critical_path(self, enhancements: List[EnhancementNode]) -> List[str]:
        """Identify critical path through enhancements"""
        # Simplified critical path - longest dependency chain
        critical_path = []

        # Find nodes with no dependents (end nodes)
        end_nodes = [e for e in enhancements if not e.dependents]

        if end_nodes:
            # Trace back from highest impact end node
            end_nodes.sort(key=lambda x: x.score.impact_score, reverse=True)
            current = end_nodes[0]

            path = [current.enhancement_id]
            visited = {current.enhancement_id}

            while current.dependencies:
                # Choose highest impact dependency
                deps = [
                    self.enhancement_graph.get(d)
                    for d in current.dependencies
                    if d not in visited and self.enhancement_graph.get(d)
                ]
                if not deps:
                    break

                deps.sort(key=lambda x: x.score.impact_score if x else 0, reverse=True)
                current = deps[0]
                path.insert(0, current.enhancement_id)
                visited.add(current.enhancement_id)

            critical_path = path

        return critical_path

    def _identify_parallel_tracks(
        self, phases: Dict[int, List[EnhancementNode]]
    ) -> List[Dict]:
        """Identify work that can be done in parallel"""
        parallel_tracks = []

        for phase_num, phase_enhancements in phases.items():
            # Group by category for parallel work
            tracks_in_phase = defaultdict(list)

            for e in phase_enhancements:
                tracks_in_phase[e.category].append(e.enhancement_id)

            if len(tracks_in_phase) > 1:
                parallel_tracks.append(
                    {
                        "phase": phase_num + 1,
                        "parallel_work_streams": [
                            {"category": cat, "enhancements": ids}
                            for cat, ids in tracks_in_phase.items()
                        ],
                    }
                )

        return parallel_tracks

    def _synthesize_advanced_specification(
        self,
        request: str,
        enhancements: List[EnhancementNode],
        roadmap: Dict,
        context: Dict,
    ) -> str:
        """Generate comprehensive enhanced specification"""
        spec = [
            "# Enhanced Technical Specification\n",
            "## Executive Summary\n",
            f"This specification enhances the original request with {len(enhancements)} strategic improvements ",
            f"organized across {len(roadmap['phases'])} implementation phases.\n\n",
            "## Original Request\n",
            f"{request}\n\n",
            "## Strategic Enhancements Overview\n",
        ]

        # Group by impact/effort quadrant
        quadrants = self._categorize_by_quadrant(enhancements)

        if quadrants["quick_wins"]:
            spec.append(f"### 🚀 Quick Wins ({len(quadrants['quick_wins'])} items)\n")
            for e in quadrants["quick_wins"][:3]:
                spec.append(f"- **{e.title}**: {e.description[:100]}...\n")
            spec.append("\n")

        if quadrants["major_projects"]:
            spec.append(
                f"### 🎯 Major Projects ({len(quadrants['major_projects'])} items)\n"
            )
            for e in quadrants["major_projects"][:3]:
                spec.append(f"- **{e.title}**: {e.description[:100]}...\n")
            spec.append("\n")

        # Implementation approach
        spec.append("## Implementation Approach\n\n")

        for phase in roadmap["phases"]:
            spec.append(f"### {phase['name']}\n")
            spec.append(f"**Duration**: {phase['estimated_duration']}\n")
            spec.append(f"**Key Deliverables**:\n")
            for deliverable in phase["key_deliverables"][:3]:
                spec.append(f"- {deliverable}\n")
            spec.append("\n")

        # Technical architecture
        spec.append("## Technical Architecture\n\n")
        arch_enhancements = [e for e in enhancements if "architect" in e.category]
        if arch_enhancements:
            for e in arch_enhancements[:3]:
                spec.append(f"### {e.title}\n")
                spec.append(f"{e.description}\n\n")

        # Technology stack
        spec.append("## Technology Stack\n\n")
        all_techs = set()
        for e in enhancements:
            all_techs.update(e.technologies)

        if all_techs:
            spec.append("### Core Technologies\n")
            for tech in sorted(all_techs)[:15]:
                spec.append(f"- {tech}\n")
            spec.append("\n")

        # Success metrics
        spec.append("## Success Metrics\n")
        spec.append("- Implementation completed within timeline\n")
        spec.append("- All quick wins delivered in Phase 1\n")
        spec.append("- Performance targets achieved\n")
        spec.append("- Integration tests passing\n")
        spec.append("- Documentation complete\n\n")

        # Risk mitigation
        spec.append("## Risk Mitigation\n")
        high_risk = [e for e in enhancements if e.score.risk_score > 0.6]
        if high_risk:
            spec.append("### High-Risk Items Requiring Attention\n")
            for e in high_risk[:3]:
                spec.append(f"- **{e.title}**: Monitor implementation closely\n")

        return "".join(spec)

    def _categorize_by_quadrant(
        self, enhancements: List[EnhancementNode]
    ) -> Dict[str, List[EnhancementNode]]:
        """Categorize enhancements by impact/effort quadrant"""
        quadrants = {
            "quick_wins": [],
            "major_projects": [],
            "fill_ins": [],
            "thankless_tasks": [],
        }

        for e in enhancements:
            if e.score.impact_score > 0.6 and e.score.effort_score < 0.4:
                quadrants["quick_wins"].append(e)
            elif e.score.impact_score > 0.6 and e.score.effort_score >= 0.4:
                quadrants["major_projects"].append(e)
            elif e.score.impact_score <= 0.6 and e.score.effort_score < 0.4:
                quadrants["fill_ins"].append(e)
            else:
                quadrants["thankless_tasks"].append(e)

        return quadrants

    def _group_enhancements_by_category(
        self, enhancements: List[EnhancementNode]
    ) -> Dict[str, List[Dict]]:
        """Group enhancements by category"""
        grouped = defaultdict(list)

        for e in enhancements:
            grouped[e.category].append(e.to_dict())

        return dict(grouped)

    def _identify_quick_wins(self, enhancements: List[EnhancementNode]) -> List[Dict]:
        """Identify quick win enhancements"""
        quick_wins = [
            e
            for e in enhancements
            if e.score.impact_score > 0.6 and e.score.effort_score < 0.4
        ]
        quick_wins.sort(key=lambda x: x.score.composite_score, reverse=True)
        return [e.to_dict() for e in quick_wins[:10]]

    def _identify_innovations(self, enhancements: List[EnhancementNode]) -> List[Dict]:
        """Identify most innovative enhancements"""
        innovations = [e for e in enhancements if e.score.innovation_score > 0.7]
        innovations.sort(key=lambda x: x.score.innovation_score, reverse=True)
        return [e.to_dict() for e in innovations[:10]]

    def _analyze_risks(self, enhancements: List[EnhancementNode]) -> Dict[str, Any]:
        """Analyze risks across all enhancements"""
        risk_analysis = {
            "high_risk_items": [],
            "medium_risk_items": [],
            "low_risk_items": [],
            "mitigation_strategies": [],
            "overall_risk_level": "Low",
        }

        for e in enhancements:
            risk_item = {
                "enhancement": e.title,
                "risk_score": e.score.risk_score,
                "category": e.category,
            }

            if e.score.risk_score > 0.7:
                risk_analysis["high_risk_items"].append(risk_item)
            elif e.score.risk_score > 0.4:
                risk_analysis["medium_risk_items"].append(risk_item)
            else:
                risk_analysis["low_risk_items"].append(risk_item)

        # Overall risk assessment
        avg_risk = sum(e.score.risk_score for e in enhancements) / max(
            len(enhancements), 1
        )
        if avg_risk > 0.6:
            risk_analysis["overall_risk_level"] = "High"
        elif avg_risk > 0.3:
            risk_analysis["overall_risk_level"] = "Medium"

        # Mitigation strategies
        if risk_analysis["high_risk_items"]:
            risk_analysis["mitigation_strategies"].append(
                "Implement high-risk items in controlled phases with rollback plans"
            )
            risk_analysis["mitigation_strategies"].append(
                "Increase testing coverage for high-risk components"
            )
            risk_analysis["mitigation_strategies"].append(
                "Consider proof-of-concept implementations first"
            )

        return risk_analysis

    def _perform_cost_benefit_analysis(
        self, enhancements: List[EnhancementNode], constraints: Dict
    ) -> Dict[str, Any]:
        """Perform cost-benefit analysis"""
        total_cost = sum(self._estimate_enhancement_cost(e) for e in enhancements)
        total_benefit = sum(e.score.impact_score * 100 for e in enhancements)

        return {
            "estimated_total_cost_units": total_cost,
            "estimated_total_benefit_units": total_benefit,
            "roi_ratio": total_benefit / max(total_cost, 1),
            "payback_period_estimate": self._estimate_payback_period(enhancements),
            "value_drivers": self._identify_value_drivers(enhancements),
            "cost_breakdown": self._calculate_cost_breakdown(enhancements),
        }

    def _estimate_payback_period(self, enhancements: List[EnhancementNode]) -> str:
        """Estimate payback period for investments"""
        quick_wins = [e for e in enhancements if e.score.effort_score < 0.3]

        if len(quick_wins) > len(enhancements) * 0.5:
            return "1-2 months"
        elif len(quick_wins) > len(enhancements) * 0.3:
            return "2-3 months"
        else:
            return "3-6 months"

    def _identify_value_drivers(self, enhancements: List[EnhancementNode]) -> List[str]:
        """Identify key value drivers"""
        drivers = []

        categories = set(e.category for e in enhancements)

        if "performance-optimizer" in categories:
            drivers.append("Significant performance improvements")
        if "integration-specialist" in categories:
            drivers.append("Enhanced ecosystem connectivity")
        if "innovation-analyst" in categories:
            drivers.append("Competitive advantage through innovation")
        if "development-accelerator" in categories:
            drivers.append("Reduced development time and costs")

        return drivers

    def _calculate_cost_breakdown(
        self, enhancements: List[EnhancementNode]
    ) -> Dict[str, float]:
        """Calculate cost breakdown by category"""
        breakdown = defaultdict(float)

        for e in enhancements:
            cost = self._estimate_enhancement_cost(e)
            breakdown[e.category] += cost

        return dict(breakdown)

    def _calculate_total_impact(self, enhancements: List[EnhancementNode]) -> float:
        """Calculate total impact score"""
        if not enhancements:
            return 0.0

        return sum(e.score.impact_score for e in enhancements) / len(enhancements)

    def _generate_enhancement_metrics(
        self, enhancements: List[EnhancementNode]
    ) -> Dict[str, Any]:
        """Generate comprehensive metrics"""
        return {
            "enhancement_count": len(enhancements),
            "average_impact_score": self._calculate_total_impact(enhancements),
            "average_effort_score": sum(e.score.effort_score for e in enhancements)
            / max(len(enhancements), 1),
            "average_innovation_score": sum(
                e.score.innovation_score for e in enhancements
            )
            / max(len(enhancements), 1),
            "quick_win_percentage": len(
                [e for e in enhancements if e.score.effort_score < 0.3]
            )
            / max(len(enhancements), 1)
            * 100,
            "high_impact_percentage": len(
                [e for e in enhancements if e.score.impact_score > 0.7]
            )
            / max(len(enhancements), 1)
            * 100,
            "technology_diversity": len(
                set(tech for e in enhancements for tech in e.technologies)
            ),
            "implementation_phases": len(
                set(e.implementation_phase for e in enhancements)
            ),
        }

    def _parse_json_response(self, response: str) -> Dict:
        """Parse JSON from agent response"""
        # Try to extract JSON from response
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # Fallback to line parsing
        return {"items": []}

    def _extract_enhancements_from_parsed(self, parsed: Dict) -> List[Dict]:
        """Extract enhancement items from parsed response"""
        items = []

        # Try different keys where enhancements might be
        for key in [
            "optimizations",
            "innovations",
            "integrations",
            "accelerators",
            "architecture_recommendations",
            "research_findings",
            "items",
        ]:
            if key in parsed and isinstance(parsed[key], list):
                items.extend(parsed[key])

        # Also check for direct dict entries
        if not items and isinstance(parsed, dict):
            for value in parsed.values():
                if isinstance(value, list):
                    items.extend(value)

        return items

    def _save_enhanced_results(self, result: Dict):
        """Save enhanced results with full analysis"""
        output_dir = self.base_engine.session_dir / "enhanced_analysis"
        output_dir.mkdir(exist_ok=True)

        # Save complete JSON
        json_path = output_dir / "complete_enhancement_analysis.json"
        with open(json_path, "w") as f:
            # Convert any remaining dataclass instances
            json_safe = json.dumps(result, default=str, indent=2)
            f.write(json_safe)

        # Save markdown report
        report_path = output_dir / "enhancement_report.md"
        with open(report_path, "w") as f:
            f.write("# Enhanced Intelligence Review Report\n\n")
            f.write(f"**Session**: {result['metadata']['session_id']}\n")
            f.write(f"**Generated**: {result['metadata']['timestamp']}\n\n")

            f.write("## Executive Summary\n")
            f.write(
                f"- Total Enhancements Identified: {result['metadata']['total_enhancements_identified']}\n"
            )
            f.write(
                f"- Enhancements Selected: {result['metadata']['enhancements_selected']}\n"
            )
            f.write(
                f"- Estimated Impact Score: {result['metadata']['estimated_impact_score']:.2f}\n"
            )
            f.write(
                f"- Implementation Phases: {result['metrics']['implementation_phases']}\n\n"
            )

            f.write("## Quick Wins\n")
            for qw in result["quick_wins"][:5]:
                f.write(f"- **{qw['title']}** (Score: {qw['composite_score']:.2f})\n")
            f.write("\n")

            f.write("## Innovation Highlights\n")
            for inn in result["innovation_highlights"][:5]:
                f.write(
                    f"- **{inn['title']}** (Innovation Score: {inn['score']['innovation_score']:.2f})\n"
                )
            f.write("\n")

            f.write("## Implementation Roadmap\n")
            for phase in result["implementation_roadmap"]["phases"]:
                f.write(f"### {phase['name']}\n")
                f.write(f"- Duration: {phase['estimated_duration']}\n")
                f.write(f"- Enhancements: {len(phase['enhancements'])}\n")
                f.write("- Key Deliverables:\n")
                for deliverable in phase["key_deliverables"][:3]:
                    f.write(f"  - {deliverable}\n")
                f.write("\n")

        logger.info(f"Enhanced results saved to {output_dir}")

    async def process_request(
        self, request: str, analysis: Any = None
    ) -> Dict[str, Any]:
        """
        Process a request for enhancements - main entry point for workflow integration

        This method bridges the gap between the DPO controller and the enhanced intelligence engine.
        It accepts either a string request or a request dictionary and returns enhancements
        suitable for workflow generation.

        Args:
            request: Either a string request or a dictionary containing request details
            analysis: Optional analysis object (for compatibility, can be None)

        Returns:
            Dictionary containing enhancements and metadata for workflow generation
        """
        start_time = time.time()

        try:
            # Handle both string and dictionary inputs
            if isinstance(request, str):
                # Simple string request
                original_request = request
                project_context = {}
                optimization_goals = []
                constraints = {}
            elif isinstance(request, dict):
                # Dictionary request from DPO controller
                original_request = request.get("request", str(request))

                # Extract context information
                project_context = {
                    "project_type": request.get("project_type", "unknown"),
                    "complexity": request.get("complexity", "medium"),
                    "key_requirements": request.get("key_requirements", []),
                    "suggested_technologies": request.get("suggested_technologies", []),
                    "additional_context": request.get("context", {}),
                }

                # Map focus areas to optimization goals
                focus_areas = request.get("focus_areas", [])
                optimization_goals = []

                if "performance" in focus_areas or "optimization" in focus_areas:
                    optimization_goals.append("maximize_performance")
                if "quality" in focus_areas or "testing" in focus_areas:
                    optimization_goals.append("ensure_quality")
                if "innovation" in focus_areas or "advanced_features" in focus_areas:
                    optimization_goals.append("maximize_innovation")
                if not optimization_goals:
                    optimization_goals = ["maximize_performance", "ensure_scalability"]

                # Set reasonable constraints based on complexity
                complexity = request.get("complexity", "medium")
                if complexity == "high":
                    constraints = {
                        "budget_units": 150,
                        "max_enhancements": 25,
                        "timeline": "normal",
                    }
                elif complexity == "low":
                    constraints = {
                        "budget_units": 75,
                        "max_enhancements": 10,
                        "timeline": "aggressive",
                    }
                else:  # medium
                    constraints = {
                        "budget_units": 100,
                        "max_enhancements": 15,
                        "timeline": "normal",
                    }

            else:
                raise ValueError(
                    f"Invalid request type: {type(request)}. Expected string or dict."
                )

            # Validate inputs
            if not original_request or not original_request.strip():
                raise ValueError("Request cannot be empty")

            logger.info(f"Processing request: {original_request[:100]}...")
            logger.info(f"Optimization goals: {optimization_goals}")
            logger.info(f"Constraints: {constraints}")

            # Call the enhanced intelligence engine
            full_result = await self.enhance_with_intelligence(
                original_request=original_request,
                project_context=project_context,
                optimization_goals=optimization_goals,
                constraints=constraints,
            )

            # Transform the result for workflow consumption
            workflow_ready_result = self._transform_for_workflow_consumption(
                full_result, original_request
            )

            # Add processing metadata
            workflow_ready_result["processing_metadata"] = {
                "method": "process_request",
                "duration_seconds": time.time() - start_time,
                "input_type": "dict" if isinstance(request, dict) else "string",
                "timestamp": datetime.now().isoformat(),
                "engine_session_id": self.session_id,
            }

            logger.info(
                f"Request processed successfully in {time.time() - start_time:.2f}s - "
                f"{len(workflow_ready_result.get('enhancements', []))} enhancements generated"
            )

            return workflow_ready_result

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}", exc_info=True)

            # Return a fallback result to prevent workflow failures
            fallback_result = {
                "original_request": str(request)[:200]
                if request
                else "Unknown request",
                "enhanced_specification": f"Basic implementation for: {str(request)[:100]}",
                "enhancements": [],
                "quick_wins": [],
                "roadmap": {
                    "phases": [
                        {
                            "phase_number": 1,
                            "name": "Basic Implementation",
                            "enhancements": [],
                            "estimated_duration": "2-3 weeks",
                            "key_deliverables": ["Basic functionality implemented"],
                        }
                    ],
                    "milestones": [],
                },
                "error": {"occurred": True, "message": str(e), "fallback_mode": True},
                "processing_metadata": {
                    "method": "process_request",
                    "duration_seconds": time.time() - start_time,
                    "timestamp": datetime.now().isoformat(),
                    "status": "error_fallback",
                },
            }

            return fallback_result

    def _transform_for_workflow_consumption(
        self, full_result: Dict[str, Any], original_request: str
    ) -> Dict[str, Any]:
        """
        Transform the full enhancement result into a format optimized for workflow generation

        Args:
            full_result: The complete result from enhance_with_intelligence
            original_request: The original request string

        Returns:
            Simplified result optimized for workflow consumption
        """
        try:
            # Extract key components for workflow generation
            workflow_result = {
                "original_request": original_request,
                "enhanced_specification": full_result.get("enhanced_specification", ""),
                "enhancements": [],
                "quick_wins": full_result.get("quick_wins", []),
                "innovation_highlights": full_result.get("innovation_highlights", []),
                "roadmap": full_result.get("implementation_roadmap", {}),
                "risk_analysis": full_result.get("risk_analysis", {}),
                "cost_benefit_analysis": full_result.get("cost_benefit_analysis", {}),
                "metadata": full_result.get("metadata", {}),
            }

            # Flatten enhancement plan for easier workflow consumption
            enhancement_plan = full_result.get("enhancement_plan", [])
            for enhancement in enhancement_plan:
                if hasattr(enhancement, "to_dict"):
                    workflow_result["enhancements"].append(enhancement.to_dict())
                elif isinstance(enhancement, dict):
                    workflow_result["enhancements"].append(enhancement)
                else:
                    # Handle EnhancementNode objects or other formats
                    try:
                        enhancement_dict = {
                            "id": getattr(enhancement, "enhancement_id", "unknown"),
                            "title": getattr(enhancement, "title", "Enhancement"),
                            "description": getattr(enhancement, "description", ""),
                            "category": getattr(enhancement, "category", "general"),
                            "phase": getattr(enhancement, "implementation_phase", 1),
                            "composite_score": getattr(
                                getattr(enhancement, "score", None),
                                "composite_score",
                                0.5,
                            )
                            if hasattr(enhancement, "score")
                            else 0.5,
                        }
                        workflow_result["enhancements"].append(enhancement_dict)
                    except Exception as e:
                        logger.warning(
                            f"Could not process enhancement {enhancement}: {e}"
                        )

            # Ensure roadmap has required structure
            if not workflow_result["roadmap"]:
                workflow_result["roadmap"] = {"phases": [], "milestones": []}

            # Add summary metrics
            workflow_result["summary"] = {
                "total_enhancements": len(workflow_result["enhancements"]),
                "quick_wins_count": len(workflow_result["quick_wins"]),
                "innovation_count": len(workflow_result["innovation_highlights"]),
                "phases_count": len(workflow_result["roadmap"].get("phases", [])),
                "estimated_impact": workflow_result["metadata"].get(
                    "estimated_impact_score", 0.5
                ),
            }

            return workflow_result

        except Exception as e:
            logger.error(f"Error transforming result for workflow consumption: {e}")
            # Return minimal viable structure
            return {
                "original_request": original_request,
                "enhanced_specification": f"Enhanced implementation for: {original_request}",
                "enhancements": [],
                "quick_wins": [],
                "roadmap": {"phases": [], "milestones": []},
                "summary": {"total_enhancements": 0},
                "transformation_error": str(e),
            }


async def main():
    """Example usage of the enhanced intelligence engine"""
    request = """
    Build a scalable e-commerce platform with real-time inventory management,
    personalized recommendations, and multi-channel sales support.
    """

    context = {
        "expected_users": "100,000 monthly active users",
        "peak_load": "10,000 concurrent users",
        "product_catalog": "50,000 SKUs",
        "deployment": "AWS",
        "team_size": "5 developers",
    }

    constraints = {
        "budget_units": 100,
        "timeline": "aggressive",  # aggressive, normal, relaxed
        "max_enhancements": 15,
        "team_expertise": ["python", "react", "aws"],
    }

    optimization_goals = [
        "maximize_performance",
        "minimize_development_time",
        "ensure_scalability",
    ]

    # Initialize engine
    engine = EnhancementIntelligenceEngine(
        parallel_agents=6, output_dir="output/enhanced_intelligence"
    )

    # Run enhancement
    result = await engine.enhance_with_intelligence(
        original_request=request,
        project_context=context,
        optimization_goals=optimization_goals,
        constraints=constraints,
    )

    # Display results
    print("\n" + "=" * 80)
    print("ENHANCED INTELLIGENCE REVIEW COMPLETE")
    print("=" * 80)
    print(f"\nSession ID: {result['metadata']['session_id']}")
    print(f"Duration: {result['metadata']['duration_seconds']:.2f} seconds")
    print(
        f"Enhancements Selected: {result['metadata']['enhancements_selected']} of {result['metadata']['total_enhancements_identified']}"
    )
    print(f"Estimated Impact Score: {result['metadata']['estimated_impact_score']:.2%}")

    print("\n" + "-" * 80)
    print("QUICK WINS:")
    print("-" * 80)
    for qw in result["quick_wins"][:3]:
        print(f"• {qw['title']} (Impact: {qw['score']['impact_score']:.1%})")

    print("\n" + "-" * 80)
    print("COST-BENEFIT ANALYSIS:")
    print("-" * 80)
    cba = result["cost_benefit_analysis"]
    print(f"ROI Ratio: {cba['roi_ratio']:.2f}x")
    print(f"Payback Period: {cba['payback_period_estimate']}")
    print(f"Value Drivers: {', '.join(cba['value_drivers'][:3])}")


if __name__ == "__main__":
    asyncio.run(main())
