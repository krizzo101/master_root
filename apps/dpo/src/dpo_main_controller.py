#!/usr/bin/env python3
"""
Development Process Orchestrator (DPO) Main Controller

The central orchestration component that coordinates all DPO subsystems:
- Request analysis and classification
- Intelligence review and enhancement
- SDLC workflow generation
- Context injection
- Orchestrator execution

This controller provides:
- Unified development request processing pipeline
- Inter-component coordination and communication
- Configuration management
- Error handling and recovery
- Status monitoring and reporting
- CLI and API interfaces

Author: Agent Orchestrator Team
Date: September 2025
"""

import asyncio
import json
import logging
import os
import sys
import time
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# Import DPO components - handle both relative and absolute
try:
    from .context_injection import ContextInjectionSystem, get_context_system
    from .dpo_intelligence_integration import (
        DPOIntelligenceIntegration,
        DPORequest,
        EnhancedDPOWorkflow,
    )
    from .dpo_orchestrator_integration import (
        DPOOrchestrator,
        WorkflowStatus,
        WorkflowSubmission,
    )
    from .intelligence_review_engine_enhanced import EnhancementIntelligenceEngine
    from .sdlc_template_system import SDLCTemplateSystem
except ImportError:
    from context_injection import ContextInjectionSystem, get_context_system
    from dpo_intelligence_integration import (
        DPOIntelligenceIntegration,
        DPORequest,
        EnhancedDPOWorkflow,
    )
    from dpo_orchestrator_integration import (
        DPOOrchestrator,
        WorkflowStatus,
        WorkflowSubmission,
    )
    from intelligence_review_engine_enhanced import EnhancementIntelligenceEngine
    from sdlc_template_system import SDLCTemplateSystem
# Setup import paths
try:
    from ._path_setup import setup_paths
except ImportError:
    from _path_setup import setup_paths
setup_paths()

# Import from agent-orchestrator
from generic_orchestrator import AgentTask, GenericOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RequestType(Enum):
    """Types of development requests"""

    BUILD = "build"
    ENHANCE = "enhance"
    FIX = "fix"
    REFACTOR = "refactor"
    DOCUMENT = "document"
    ANALYZE = "analyze"
    INTEGRATE = "integrate"
    OPTIMIZE = "optimize"


@dataclass
class RequestAnalysis:
    """Analysis result for a development request"""

    request_type: RequestType
    project_type: str
    complexity: str
    key_requirements: List[str]
    suggested_technologies: List[str]
    risk_factors: List[str]
    estimated_effort: str
    confidence_score: float


@dataclass
class DPOConfiguration:
    """Configuration for the DPO system"""

    output_base_dir: str = "output/dpo_workflows"
    max_parallel_agents: int = 10
    enable_websocket: bool = True
    websocket_port: int = 8765
    enable_dashboard: bool = True
    enable_intelligence: bool = True
    enable_context_injection: bool = True
    auto_recovery: bool = True
    checkpoint_interval: int = 300  # seconds
    log_level: str = "INFO"
    template_library_path: str = "templates/"
    knowledge_base_path: str = "knowledge/"
    metrics_enabled: bool = True

    @classmethod
    def from_file(cls, config_path: str) -> "DPOConfiguration":
        """Load configuration from file"""
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, "r") as f:
                config_data = json.load(f)
                return cls(**config_data)
        return cls()

    def save(self, config_path: str):
        """Save configuration to file"""
        config_file = Path(config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file, "w") as f:
            json.dump(asdict(self), f, indent=2)


@dataclass
class DPOMetrics:
    """Metrics for DPO system performance"""

    total_requests: int = 0
    successful_workflows: int = 0
    failed_workflows: int = 0
    average_duration: float = 0.0
    total_agents_used: int = 0
    enhancements_applied: int = 0
    context_injections: int = 0
    errors_recovered: int = 0
    knowledge_extracted: int = 0

    def update_duration(self, new_duration: float):
        """Update average duration with new value"""
        if self.total_requests == 0:
            self.average_duration = new_duration
        else:
            self.average_duration = (
                self.average_duration * (self.total_requests - 1) + new_duration
            ) / self.total_requests


class RequestAnalyzer:
    """Analyzes and classifies development requests"""

    COMPLEXITY_INDICATORS = {
        "simple": ["basic", "simple", "small", "quick", "minor"],
        "moderate": ["standard", "normal", "typical", "medium"],
        "complex": ["complex", "advanced", "large", "enterprise", "sophisticated"],
    }

    PROJECT_TYPE_KEYWORDS = {
        "web_app": ["web", "frontend", "ui", "react", "vue", "angular", "website"],
        "api": ["api", "rest", "graphql", "backend", "service", "endpoint"],
        "cli": ["cli", "command", "terminal", "console", "shell"],
        "library": ["library", "package", "module", "sdk", "framework"],
        "integration": ["integration", "connect", "sync", "webhook", "bridge"],
        "mobile": ["mobile", "ios", "android", "app", "react-native"],
        "desktop": ["desktop", "electron", "native", "windows", "mac", "linux"],
        "data": ["data", "pipeline", "etl", "analytics", "processing"],
    }

    def analyze(self, request: str, context: Optional[Dict] = None) -> RequestAnalysis:
        """Analyze a development request"""
        request_lower = request.lower()

        # Determine request type
        request_type = self._determine_request_type(request_lower)

        # Determine project type
        project_type = self._determine_project_type(request_lower, context)

        # Assess complexity
        complexity = self._assess_complexity(request_lower, context)

        # Extract key requirements
        key_requirements = self._extract_requirements(request, context)

        # Suggest technologies
        suggested_technologies = self._suggest_technologies(project_type, request_lower)

        # Identify risk factors
        risk_factors = self._identify_risks(request_lower, complexity)

        # Estimate effort
        estimated_effort = self._estimate_effort(complexity, len(key_requirements))

        # Calculate confidence score
        confidence_score = self._calculate_confidence(
            request_type, project_type, key_requirements
        )

        return RequestAnalysis(
            request_type=request_type,
            project_type=project_type,
            complexity=complexity,
            key_requirements=key_requirements,
            suggested_technologies=suggested_technologies,
            risk_factors=risk_factors,
            estimated_effort=estimated_effort,
            confidence_score=confidence_score,
        )

    def _determine_request_type(self, request: str) -> RequestType:
        """Determine the type of request"""
        if any(word in request for word in ["build", "create", "develop", "implement"]):
            return RequestType.BUILD
        elif any(word in request for word in ["enhance", "improve", "add", "extend"]):
            return RequestType.ENHANCE
        elif any(
            word in request for word in ["fix", "bug", "issue", "problem", "error"]
        ):
            return RequestType.FIX
        elif any(word in request for word in ["refactor", "restructure", "reorganize"]):
            return RequestType.REFACTOR
        elif any(word in request for word in ["document", "docs", "readme", "guide"]):
            return RequestType.DOCUMENT
        elif any(word in request for word in ["analyze", "review", "audit", "assess"]):
            return RequestType.ANALYZE
        elif any(word in request for word in ["integrate", "connect", "link", "sync"]):
            return RequestType.INTEGRATE
        elif any(
            word in request
            for word in ["optimize", "performance", "speed", "efficient"]
        ):
            return RequestType.OPTIMIZE
        else:
            return RequestType.BUILD

    def _determine_project_type(self, request: str, context: Optional[Dict]) -> str:
        """Determine the project type"""
        # Check context first
        if context and "project_type" in context:
            return context["project_type"]

        # Analyze request for keywords
        for project_type, keywords in self.PROJECT_TYPE_KEYWORDS.items():
            if any(keyword in request for keyword in keywords):
                return project_type

        return "web_app"  # default

    def _assess_complexity(self, request: str, context: Optional[Dict]) -> str:
        """Assess request complexity"""
        # Check context first
        if context and "complexity" in context:
            return context["complexity"]

        # Count feature mentions
        feature_count = request.count(",") + request.count("and") + 1

        # Check for complexity indicators
        for level, indicators in self.COMPLEXITY_INDICATORS.items():
            if any(indicator in request for indicator in indicators):
                return level

        # Default based on feature count
        if feature_count <= 3:
            return "simple"
        elif feature_count <= 7:
            return "moderate"
        else:
            return "complex"

    def _extract_requirements(self, request: str, context: Optional[Dict]) -> List[str]:
        """Extract key requirements from request"""
        requirements = []

        # Split by common delimiters
        parts = request.replace(",", ".").replace(" and ", ".").split(".")

        for part in parts:
            part = part.strip()
            if len(part) > 10:  # Filter out very short fragments
                requirements.append(part)

        # Add context requirements
        if context and "requirements" in context:
            requirements.extend(context["requirements"])

        return requirements[:10]  # Limit to top 10

    def _suggest_technologies(self, project_type: str, request: str) -> List[str]:
        """Suggest appropriate technologies"""
        tech_map = {
            "web_app": ["React", "Node.js", "PostgreSQL", "Docker"],
            "api": ["FastAPI", "PostgreSQL", "Redis", "Docker"],
            "cli": ["Python", "Click", "Rich"],
            "library": ["Python", "TypeScript", "pytest"],
            "integration": ["Python", "Celery", "RabbitMQ"],
            "mobile": ["React Native", "Expo", "Firebase"],
            "desktop": ["Electron", "React", "SQLite"],
            "data": ["Python", "Pandas", "Apache Spark", "PostgreSQL"],
        }

        base_tech = tech_map.get(project_type, ["Python"])

        # Add specific technologies mentioned in request
        if "typescript" in request.lower():
            base_tech.append("TypeScript")
        if "kubernetes" in request.lower():
            base_tech.append("Kubernetes")
        if "aws" in request.lower():
            base_tech.append("AWS")

        return list(set(base_tech))

    def _identify_risks(self, request: str, complexity: str) -> List[str]:
        """Identify potential risk factors"""
        risks = []

        if complexity == "complex":
            risks.append("High complexity may extend timeline")

        if "real-time" in request or "realtime" in request:
            risks.append("Real-time requirements need careful architecture")

        if "scale" in request or "performance" in request:
            risks.append("Performance requirements need optimization focus")

        if "security" in request or "auth" in request:
            risks.append("Security features require thorough testing")

        if "integration" in request:
            risks.append("External integrations may have dependencies")

        return risks

    def _estimate_effort(self, complexity: str, requirement_count: int) -> str:
        """Estimate development effort"""
        base_hours = {"simple": 8, "moderate": 40, "complex": 120}

        hours = base_hours.get(complexity, 40) + (requirement_count * 4)

        if hours <= 16:
            return "1-2 days"
        elif hours <= 40:
            return "3-5 days"
        elif hours <= 80:
            return "1-2 weeks"
        elif hours <= 160:
            return "2-4 weeks"
        else:
            return "1+ months"

    def _calculate_confidence(
        self, request_type: RequestType, project_type: str, requirements: List[str]
    ) -> float:
        """Calculate confidence score for the analysis"""
        score = 0.5  # Base score

        # Clear request type increases confidence
        if request_type != RequestType.BUILD:
            score += 0.1

        # Known project type increases confidence
        if project_type in self.PROJECT_TYPE_KEYWORDS:
            score += 0.15

        # Clear requirements increase confidence
        if len(requirements) >= 3:
            score += 0.15
        if len(requirements) >= 5:
            score += 0.1

        return min(1.0, score)


class DevelopmentProcessOrchestrator:
    """
    Main DPO Controller - Coordinates all subsystems for development process orchestration
    """

    def __init__(self, config: Optional[DPOConfiguration] = None):
        """
        Initialize the Development Process Orchestrator

        Args:
            config: Configuration object or None for defaults
        """
        self.config = config or DPOConfiguration()

        # Set up logging
        logging.getLogger().setLevel(getattr(logging, self.config.log_level))

        # Initialize components
        self.request_analyzer = RequestAnalyzer()

        # Initialize intelligence engine if enabled
        if self.config.enable_intelligence:
            self.intelligence_engine = EnhancementIntelligenceEngine(
                orchestrator=None, parallel_agents=6, output_dir=None
            )
        else:
            self.intelligence_engine = None

        # Initialize template system
        self.template_system = SDLCTemplateSystem()

        # Initialize context system if enabled
        if self.config.enable_context_injection:
            self.context_system = get_context_system()
        else:
            self.context_system = None

        # Initialize orchestrator integration
        self.orchestrator = DPOOrchestrator(
            output_base_dir=self.config.output_base_dir,
            max_parallel_agents=self.config.max_parallel_agents,
            enable_websocket=self.config.enable_websocket,
            websocket_port=self.config.websocket_port,
            dashboard_callback=self._handle_dashboard_event
            if self.config.enable_dashboard
            else None,
        )

        # Metrics tracking
        self.metrics = DPOMetrics()

        # Workflow tracking
        self.active_workflows: Dict[str, Dict] = {}
        self.workflow_history: List[Dict] = []

        # Error recovery
        self.recovery_handlers: Dict[str, Callable] = {}
        self._register_recovery_handlers()

        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=4)

        logger.info(
            f"DPO Main Controller initialized with config: {self.config.output_base_dir}"
        )

    async def process_development_request(
        self,
        request: str,
        project_type: Optional[str] = None,
        complexity: Optional[str] = None,
        context: Optional[Dict] = None,
        enhancement_prefs: Optional[Dict] = None,
    ) -> Dict:
        """
        Process a development request through the complete DPO pipeline

        Args:
            request: Natural language development request
            project_type: Override project type detection
            complexity: Override complexity assessment
            context: Additional project context
            enhancement_prefs: Enhancement preferences

        Returns:
            Dictionary with workflow ID and processing results
        """
        start_time = time.time()
        self.metrics.total_requests += 1

        try:
            # Step 1: Analyze and classify request
            logger.info("Step 1: Analyzing development request...")
            analysis = self.request_analyzer.analyze(request, context)

            # Override with provided values if any
            if project_type:
                analysis.project_type = project_type
            if complexity:
                analysis.complexity = complexity

            logger.info(
                f"Request analyzed - Type: {analysis.request_type.value}, "
                f"Project: {analysis.project_type}, Complexity: {analysis.complexity}"
            )

            # Step 2: Enhance through intelligence review (if enabled)
            enhancements = {}
            if self.config.enable_intelligence and self.intelligence_engine:
                logger.info("Step 2: Enhancing through intelligence review...")
                enhancement_result = await self._enhance_with_intelligence(
                    request, analysis, context, enhancement_prefs
                )
                enhancements = enhancement_result
                self.metrics.enhancements_applied += len(
                    enhancement_result.get("enhancements", [])
                )
                logger.info(
                    f"Applied {len(enhancement_result.get('enhancements', []))} enhancements"
                )
            else:
                logger.info("Step 2: Intelligence enhancement disabled, skipping...")

            # Step 3: Generate SDLC workflow
            logger.info("Step 3: Generating SDLC workflow...")
            workflow = await self._generate_workflow(
                request, analysis, enhancements, context
            )
            logger.info(
                f"Generated workflow with {len(workflow.get('phases', []))} phases"
            )

            # Step 4: Inject ecosystem context (if enabled)
            if self.config.enable_context_injection and self.context_system:
                logger.info("Step 4: Injecting ecosystem context...")
                contextualized_workflow = await self._inject_context(workflow)
                self.metrics.context_injections += 1
                logger.info("Context injection completed")
            else:
                logger.info("Step 4: Context injection disabled, skipping...")
                contextualized_workflow = workflow

            # Step 5: Execute through orchestrator
            logger.info("Step 5: Submitting to orchestrator for execution...")

            # Create workflow submission with proper format
            try:
                submission_result = await self._submit_to_orchestrator(
                    workflow=contextualized_workflow,
                    request=request,
                    analysis=analysis,
                    enhancements=enhancements,
                    context=context,
                )

                if not submission_result.get("success"):
                    raise Exception(
                        f"Orchestrator submission failed: {submission_result.get('error')}"
                    )

                workflow_id = submission_result["workflow_id"]

            except Exception as e:
                logger.error(f"Failed to submit to orchestrator: {str(e)}")
                # Try fallback submission
                workflow_id = await self._fallback_submission(
                    request, analysis, contextualized_workflow
                )

            # Track workflow
            workflow_record = {
                "workflow_id": workflow_id,
                "request": request,
                "analysis": asdict(analysis),
                "enhancements": enhancements,
                "start_time": datetime.now().isoformat(),
                "status": "running",
            }
            self.active_workflows[workflow_id] = workflow_record

            # Calculate metrics
            duration = time.time() - start_time
            self.metrics.update_duration(duration)

            logger.info(f"Workflow {workflow_id} submitted successfully")

            return {
                "success": True,
                "workflow_id": workflow_id,
                "analysis": asdict(analysis),
                "enhancements_count": len(enhancements.get("enhancements", [])),
                "phases_count": len(workflow.get("phases", [])),
                "estimated_effort": analysis.estimated_effort,
                "processing_time": duration,
                "message": f"Development workflow initiated successfully",
            }

        except Exception as e:
            logger.error(f"Error processing development request: {str(e)}")
            self.metrics.failed_workflows += 1

            # Attempt recovery if enabled
            if self.config.auto_recovery:
                recovery_result = await self._attempt_recovery(
                    "request_processing", e, {"request": request, "context": context}
                )
                if recovery_result.get("success"):
                    self.metrics.errors_recovered += 1
                    return recovery_result

            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "message": "Failed to process development request",
            }

    async def _enhance_with_intelligence(
        self,
        request: str,
        analysis: RequestAnalysis,
        context: Optional[Dict],
        enhancement_prefs: Optional[Dict],
    ) -> Dict:
        """Enhance request through intelligence review"""
        try:
            # Create a DPO request for intelligence engine
            dpo_request = DPORequest(
                request_id=str(uuid.uuid4()),
                request_text=request,
                project_type=analysis.project_type,
                complexity=analysis.complexity,
                priority="normal",
                metadata={
                    "key_requirements": analysis.key_requirements,
                    "suggested_technologies": analysis.suggested_technologies,
                    "context": context or {},
                    "enhancement_prefs": enhancement_prefs or {},
                },
            )

            # Apply enhancement preferences
            focus_areas = []
            if enhancement_prefs:
                if enhancement_prefs.get("prioritize_quality"):
                    focus_areas.extend(["quality", "testing", "documentation"])
                if enhancement_prefs.get("prioritize_innovation"):
                    focus_areas.extend(["innovation", "advanced_features"])
                if enhancement_prefs.get("prioritize_performance"):
                    focus_areas.extend(["performance", "optimization"])

            if focus_areas:
                dpo_request.metadata["focus_areas"] = focus_areas

            # Process through intelligence engine (synchronous call)
            enhancement_result = self.intelligence_engine.enhance_request(dpo_request)

            return {
                "enhancements": enhancement_result.enhancements
                if enhancement_result
                else [],
                "quality_score": enhancement_result.quality_score
                if enhancement_result
                else 0.0,
                "innovation_suggestions": enhancement_result.innovation_suggestions
                if enhancement_result
                else [],
                "risk_mitigations": enhancement_result.risk_mitigations
                if enhancement_result
                else [],
                "recommended_technologies": enhancement_result.recommended_technologies
                if enhancement_result
                else [],
            }
        except Exception as e:
            logger.warning(f"Intelligence enhancement failed: {str(e)}")
            return {
                "enhancements": [],
                "quality_score": 0.0,
                "innovation_suggestions": [],
                "risk_mitigations": [],
                "recommended_technologies": [],
            }

    async def _generate_workflow(
        self,
        request: str,
        analysis: RequestAnalysis,
        enhancements: Dict,
        context: Optional[Dict],
    ) -> Dict:
        """Generate SDLC workflow based on analysis and enhancements"""
        try:
            # Prepare project name
            project_name = (
                f"{analysis.project_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )

            # Prepare specifications for workflow generation
            specifications = {
                "requirements": analysis.key_requirements,
                "technologies": analysis.suggested_technologies
                + enhancements.get("recommended_technologies", []),
                "enhancements": enhancements.get("enhancements", []),
                "innovation_suggestions": enhancements.get(
                    "innovation_suggestions", []
                ),
                "risk_mitigations": enhancements.get("risk_mitigations", []),
                "quality_gates": self._generate_quality_gates(analysis, enhancements),
                "context": context or {},
            }

            # Generate workflow through template system (synchronous)
            workflow = self.template_system.generate_workflow(
                project_name=project_name,
                project_type=analysis.project_type,
                complexity=analysis.complexity,
                specifications=specifications,
            )

            # Convert workflow phases to orchestrator-compatible format
            orchestrator_tasks = []
            for phase in workflow.get("phases", []):
                for agent in phase.get("agents", []):
                    # Create multiple tasks based on agent count
                    agent_count = agent.get("count", 1)
                    for i in range(agent_count):
                        task = AgentTask(
                            task_id=f"{phase['phase_id']}_{agent['type']}_{i+1}",
                            task_type=agent["type"],
                            prompt=self._generate_agent_prompt(
                                agent["type"], phase, specifications, request
                            ),
                            context={
                                "phase": phase["phase_name"],
                                "phase_type": phase["phase_type"],
                                "requirements": specifications["requirements"],
                                "technologies": specifications["technologies"],
                                "enhancements": specifications["enhancements"],
                                "project_name": project_name,
                            },
                            dependencies=phase.get("dependencies", []),
                            quality_gates=phase.get("quality_gates", []),
                            project_location=f"/apps/{project_name}/",
                            deliverable_structure=self._get_deliverable_structure(
                                phase["phase_type"]
                            ),
                        )
                        orchestrator_tasks.append(task)

            workflow["orchestrator_tasks"] = orchestrator_tasks
            workflow["project_name"] = project_name
            workflow["total_agents"] = len(orchestrator_tasks)

            return workflow

        except Exception as e:
            logger.error(f"Workflow generation failed: {str(e)}")
            # Return minimal workflow on error
            return {
                "phases": [],
                "orchestrator_tasks": [],
                "project_name": f"fallback_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "error": str(e),
            }

    async def _inject_context(self, workflow: Dict) -> Dict:
        """Inject ecosystem context into workflow"""
        try:
            # Discover available tools and capabilities (synchronous call wrapped)
            loop = asyncio.get_event_loop()
            ecosystem_context = await loop.run_in_executor(
                None, self.context_system.discover_ecosystem
            )

            # Inject context into each workflow phase
            for phase in workflow.get("phases", []):
                phase["context"] = {
                    "available_tools": ecosystem_context.get("tools", []),
                    "available_libraries": ecosystem_context.get("libraries", []),
                    "best_practices": ecosystem_context.get("best_practices", []),
                    "existing_patterns": ecosystem_context.get("patterns", []),
                }

            # Also inject into orchestrator tasks
            for task in workflow.get("orchestrator_tasks", []):
                task.context.update({"ecosystem": ecosystem_context})

            workflow["context_injected"] = True
            return workflow

        except Exception as e:
            logger.warning(f"Context injection failed: {str(e)}")
            workflow["context_injected"] = False
            return workflow

    async def get_workflow_status(self, workflow_id: str) -> Dict:
        """Get current status of a workflow"""
        # Get status from orchestrator
        status = await self.orchestrator.get_workflow_status(workflow_id)

        # Enhance with local tracking
        if workflow_id in self.active_workflows:
            status["request_info"] = self.active_workflows[workflow_id]

        return status

    async def get_workflow_results(self, workflow_id: str) -> Dict:
        """Get results of a completed workflow"""
        results = await self.orchestrator.get_workflow_results(workflow_id)

        if results:
            # Update metrics
            self.metrics.successful_workflows += 1
            self.metrics.total_agents_used += len(results.task_results)
            self.metrics.knowledge_extracted += len(results.extracted_knowledge)

            # Move to history
            if workflow_id in self.active_workflows:
                workflow_record = self.active_workflows.pop(workflow_id)
                workflow_record["status"] = "completed"
                workflow_record["end_time"] = datetime.now().isoformat()
                workflow_record["results"] = results.to_dict()
                self.workflow_history.append(workflow_record)

            return results.to_dict()

        return {"error": "Workflow not found or not completed"}

    async def cancel_workflow(self, workflow_id: str) -> Dict:
        """Cancel a running workflow"""
        success = await self.orchestrator.cancel_workflow(workflow_id)

        if success:
            if workflow_id in self.active_workflows:
                workflow_record = self.active_workflows.pop(workflow_id)
                workflow_record["status"] = "cancelled"
                workflow_record["end_time"] = datetime.now().isoformat()
                self.workflow_history.append(workflow_record)

            return {
                "success": True,
                "message": f"Workflow {workflow_id} cancelled successfully",
            }

        return {"success": False, "message": f"Failed to cancel workflow {workflow_id}"}

    async def list_workflows(self, status_filter: Optional[str] = None) -> List[Dict]:
        """List all workflows with optional status filter"""
        workflows = []

        # Add active workflows
        for wf_id, wf_data in self.active_workflows.items():
            if not status_filter or wf_data["status"] == status_filter:
                workflows.append(
                    {
                        "workflow_id": wf_id,
                        "status": wf_data["status"],
                        "request": wf_data["request"][:100] + "..."
                        if len(wf_data["request"]) > 100
                        else wf_data["request"],
                        "start_time": wf_data["start_time"],
                        "project_type": wf_data["analysis"]["project_type"],
                    }
                )

        # Add historical workflows
        for wf_data in self.workflow_history[-20:]:  # Last 20
            if not status_filter or wf_data["status"] == status_filter:
                workflows.append(
                    {
                        "workflow_id": wf_data["workflow_id"],
                        "status": wf_data["status"],
                        "request": wf_data["request"][:100] + "..."
                        if len(wf_data["request"]) > 100
                        else wf_data["request"],
                        "start_time": wf_data["start_time"],
                        "end_time": wf_data.get("end_time"),
                        "project_type": wf_data["analysis"]["project_type"],
                    }
                )

        return workflows

    def get_metrics(self) -> Dict:
        """Get system metrics"""
        return asdict(self.metrics)

    def get_configuration(self) -> Dict:
        """Get current configuration"""
        return asdict(self.config)

    def update_configuration(self, updates: Dict) -> Dict:
        """Update configuration"""
        for key, value in updates.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

        # Save configuration
        self.config.save("config/dpo_config.json")

        return asdict(self.config)

    def _handle_dashboard_event(self, event: Dict):
        """Handle dashboard events"""
        logger.debug(f"Dashboard event: {event.get('event')}")
        # Can be extended to update UI, send notifications, etc.

    def _register_recovery_handlers(self):
        """Register error recovery handlers"""
        self.recovery_handlers["request_processing"] = self._recover_request_processing
        self.recovery_handlers["workflow_execution"] = self._recover_workflow_execution
        self.recovery_handlers["intelligence_enhancement"] = self._recover_intelligence

    async def _attempt_recovery(
        self, error_type: str, error: Exception, context: Dict
    ) -> Dict:
        """Attempt to recover from an error"""
        if error_type in self.recovery_handlers:
            try:
                logger.info(f"Attempting recovery for {error_type} error...")
                return await self.recovery_handlers[error_type](error, context)
            except Exception as recovery_error:
                logger.error(f"Recovery failed: {str(recovery_error)}")
                return {
                    "success": False,
                    "error": str(error),
                    "recovery_error": str(recovery_error),
                }

        return {
            "success": False,
            "error": str(error),
            "message": "No recovery handler available",
        }

    async def _submit_to_orchestrator(
        self,
        workflow: Dict,
        request: str,
        analysis: RequestAnalysis,
        enhancements: Dict,
        context: Optional[Dict],
    ) -> Dict:
        """Submit workflow to orchestrator with proper formatting"""
        try:
            # Extract orchestrator tasks from workflow
            orchestrator_tasks = workflow.get("orchestrator_tasks", [])

            if not orchestrator_tasks:
                # Generate fallback tasks if none exist
                orchestrator_tasks = self._generate_fallback_tasks(
                    request, analysis, workflow
                )

            # Submit using orchestrator's expected format
            workflow_id = await self.orchestrator.submit_workflow(
                tasks=orchestrator_tasks,
                workflow_name=workflow.get("project_name", "unnamed_workflow"),
                metadata={
                    "request": request,
                    "analysis": asdict(analysis),
                    "enhancements": enhancements,
                    "context": context or {},
                    "phases": len(workflow.get("phases", [])),
                    "total_agents": workflow.get(
                        "total_agents", len(orchestrator_tasks)
                    ),
                },
            )

            return {"success": True, "workflow_id": workflow_id}

        except AttributeError:
            # Fallback if orchestrator doesn't have submit_workflow method
            workflow_id = await self.orchestrator.submit_development_request(
                request=request,
                project_type=analysis.project_type,
                complexity=analysis.complexity,
                context={
                    **(context if context else {}),
                    "analysis": asdict(analysis),
                    "enhancements": enhancements,
                    "workflow": workflow,
                },
            )

            return {"success": True, "workflow_id": workflow_id}

        except Exception as e:
            logger.error(f"Orchestrator submission error: {str(e)}")
            return {"success": False, "error": str(e)}

    def _generate_fallback_tasks(
        self, request: str, analysis: RequestAnalysis, workflow: Dict
    ) -> List[AgentTask]:
        """Generate fallback tasks when workflow doesn't have orchestrator tasks"""
        tasks = []

        # Create a minimal set of tasks based on request type
        if analysis.request_type == RequestType.BUILD:
            tasks.extend(
                [
                    AgentTask(
                        task_id="requirements_1",
                        task_type="requirements-analyst",
                        prompt=f"Analyze requirements for: {request}",
                        context={"phase": "discovery"},
                    ),
                    AgentTask(
                        task_id="architect_1",
                        task_type="solution-architect",
                        prompt=f"Design architecture for: {request}",
                        context={"phase": "design"},
                        dependencies=["requirements_1"],
                    ),
                    AgentTask(
                        task_id="developer_1",
                        task_type="developer",
                        prompt=f"Implement solution for: {request}",
                        context={"phase": "implementation"},
                        dependencies=["architect_1"],
                    ),
                ]
            )
        elif analysis.request_type == RequestType.FIX:
            tasks.append(
                AgentTask(
                    task_id="debugger_1",
                    task_type="debugger",
                    prompt=f"Debug and fix: {request}",
                    context={"phase": "debugging"},
                )
            )
        else:
            # Generic fallback task
            tasks.append(
                AgentTask(
                    task_id="generic_1",
                    task_type="general-purpose",
                    prompt=f"Process request: {request}",
                    context={"phase": "processing"},
                )
            )

        return tasks

    async def _fallback_submission(
        self, request: str, analysis: RequestAnalysis, workflow: Dict
    ) -> str:
        """Fallback submission method when primary fails"""
        try:
            # Generate a unique workflow ID
            workflow_id = f"fallback_{uuid.uuid4().hex[:8]}"

            # Create a minimal workflow record
            workflow_record = {
                "workflow_id": workflow_id,
                "request": request,
                "analysis": asdict(analysis),
                "enhancements": {},
                "start_time": datetime.now().isoformat(),
                "status": "pending_fallback",
                "workflow": workflow,
            }

            # Store locally
            self.active_workflows[workflow_id] = workflow_record

            # Save to file for recovery
            fallback_dir = Path(self.config.output_base_dir) / "fallback_workflows"
            fallback_dir.mkdir(parents=True, exist_ok=True)

            with open(fallback_dir / f"{workflow_id}.json", "w") as f:
                json.dump(workflow_record, f, indent=2)

            logger.info(f"Created fallback workflow: {workflow_id}")
            return workflow_id

        except Exception as e:
            logger.error(f"Fallback submission also failed: {str(e)}")
            # Return a placeholder ID
            return f"error_{uuid.uuid4().hex[:8]}"

    async def _recover_request_processing(
        self, error: Exception, context: Dict
    ) -> Dict:
        """Recover from request processing errors"""
        request = context.get("request")
        if not request:
            return {"success": False, "error": "No request to recover"}

        logger.info("Attempting recovery with simplified workflow...")

        try:
            # Create simplified analysis
            simplified_analysis = RequestAnalysis(
                request_type=RequestType.BUILD,
                project_type="generic",
                complexity="simple",
                key_requirements=[request[:200]],  # Truncate if too long
                suggested_technologies=["Python"],
                risk_factors=[],
                estimated_effort="1-2 days",
                confidence_score=0.5,
            )

            # Create minimal workflow
            minimal_workflow = {
                "phases": [
                    {
                        "phase_id": "single_phase",
                        "phase_name": "Processing",
                        "phase_type": "implementation",
                        "agents": [{"type": "general-purpose", "count": 1}],
                    }
                ],
                "orchestrator_tasks": [
                    AgentTask(
                        task_id="recovery_task_1",
                        task_type="general-purpose",
                        prompt=f"Process this request with error recovery: {request}",
                        context={"recovery_mode": True, "original_error": str(error)},
                    )
                ],
                "project_name": f"recovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            }

            # Submit minimal workflow
            submission_result = await self._submit_to_orchestrator(
                workflow=minimal_workflow,
                request=request,
                analysis=simplified_analysis,
                enhancements={},
                context={"recovery_attempt": True},
            )

            if submission_result.get("success"):
                self.metrics.errors_recovered += 1
                return {
                    "success": True,
                    "workflow_id": submission_result["workflow_id"],
                    "analysis": asdict(simplified_analysis),
                    "message": "Recovered with simplified workflow",
                    "recovery_mode": True,
                }

        except Exception as recovery_error:
            logger.error(f"Recovery failed: {str(recovery_error)}")

        return {"success": False, "error": str(error), "recovery_failed": True}

    async def _recover_workflow_execution(
        self, error: Exception, context: Dict
    ) -> Dict:
        """Recover from workflow execution errors"""
        workflow_id = context.get("workflow_id")

        if not workflow_id:
            return {
                "success": False,
                "error": str(error),
                "message": "No workflow ID for recovery",
            }

        try:
            # Check if we have a checkpoint
            checkpoint_dir = Path(self.config.output_base_dir) / "checkpoints"
            checkpoint_file = checkpoint_dir / f"{workflow_id}.json"

            if checkpoint_file.exists():
                logger.info(
                    f"Found checkpoint for workflow {workflow_id}, attempting resume..."
                )

                with open(checkpoint_file, "r") as f:
                    checkpoint_data = json.load(f)

                # Resume from checkpoint
                resume_result = await self.orchestrator.resume_workflow(
                    workflow_id=workflow_id, checkpoint_data=checkpoint_data
                )

                if resume_result.get("success"):
                    self.metrics.errors_recovered += 1
                    return {
                        "success": True,
                        "workflow_id": workflow_id,
                        "message": "Workflow resumed from checkpoint",
                        "resumed_from": checkpoint_data.get("last_completed_task"),
                    }

            # No checkpoint available, try to restart with partial completion tracking
            logger.info(
                f"No checkpoint found, attempting partial restart for {workflow_id}..."
            )

            if workflow_id in self.active_workflows:
                workflow_data = self.active_workflows[workflow_id]

                # Get partial results if available
                partial_results = await self.orchestrator.get_partial_results(
                    workflow_id
                )

                if partial_results:
                    # Create new workflow continuing from partial results
                    continuation_id = f"{workflow_id}_cont_{uuid.uuid4().hex[:4]}"

                    # Filter out completed tasks
                    remaining_tasks = [
                        task
                        for task in workflow_data.get("workflow", {}).get(
                            "orchestrator_tasks", []
                        )
                        if task.task_id
                        not in partial_results.get("completed_tasks", [])
                    ]

                    if remaining_tasks:
                        # Submit remaining tasks
                        continuation_result = await self.orchestrator.submit_workflow(
                            tasks=remaining_tasks,
                            workflow_name=f"{workflow_data.get('workflow', {}).get('project_name', 'unnamed')}_continuation",
                            metadata={
                                "original_workflow_id": workflow_id,
                                "continuation": True,
                                "partial_results": partial_results,
                            },
                        )

                        if continuation_result:
                            return {
                                "success": True,
                                "workflow_id": continuation_id,
                                "message": "Workflow continued with remaining tasks",
                                "completed_tasks": len(
                                    partial_results.get("completed_tasks", [])
                                ),
                                "remaining_tasks": len(remaining_tasks),
                            }

        except Exception as recovery_error:
            logger.error(f"Workflow recovery failed: {str(recovery_error)}")

        return {
            "success": False,
            "error": str(error),
            "message": "Workflow recovery failed",
        }

    async def _recover_intelligence(self, error: Exception, context: Dict) -> Dict:
        """Recover from intelligence enhancement errors"""
        # Return empty enhancements and continue
        return {
            "success": True,
            "enhancements": {},
            "message": "Continued without intelligence enhancements",
        }

    def _generate_quality_gates(
        self, analysis: RequestAnalysis, enhancements: Dict
    ) -> List[str]:
        """Generate quality gates based on analysis and enhancements"""
        gates = []

        # Basic quality gates
        gates.append("code_review_passed")
        gates.append("unit_tests_passed")

        # Complexity-based gates
        if analysis.complexity in ["complex", "enterprise"]:
            gates.append("integration_tests_passed")
            gates.append("performance_benchmarks_met")
            gates.append("security_audit_passed")

        # Enhancement-based gates
        if enhancements.get("quality_score", 0) > 0.8:
            gates.append("advanced_quality_checks")

        # Risk-based gates
        if analysis.risk_factors:
            gates.append("risk_mitigation_verified")

        return gates

    def _generate_agent_prompt(
        self, agent_type: str, phase: Dict, specifications: Dict, original_request: str
    ) -> str:
        """Generate specific prompt for each agent based on type and phase"""
        base_prompt = f"""
You are a {agent_type} agent working on the {phase['phase_name']} phase.

Original Request: {original_request}

Your specific responsibilities in this phase:
- Phase Type: {phase['phase_type']}
- Expected Outputs: {', '.join(phase.get('expected_outputs', []))}

Project Requirements:
{json.dumps(specifications['requirements'], indent=2)}

Technologies to Use:
{json.dumps(specifications['technologies'], indent=2)}

Enhancements to Apply:
{json.dumps(specifications.get('enhancements', []), indent=2)}

Quality Gates to Meet:
{json.dumps(phase.get('quality_gates', []), indent=2)}

Please complete your assigned tasks following best practices and ensure all quality gates are met.
"""

        # Add agent-specific instructions
        agent_prompts = {
            "requirements-analyst": "Focus on detailed requirement analysis, user stories, and acceptance criteria.",
            "solution-architect": "Design the system architecture, define components, and create technical specifications.",
            "developer": "Implement the solution according to specifications, ensuring code quality and testing.",
            "qa-engineer": "Create and execute comprehensive test plans, ensure quality standards are met.",
            "documentation-specialist": "Create clear, comprehensive documentation for all aspects of the project.",
        }

        if agent_type in agent_prompts:
            base_prompt += f"\n\nSpecific Instructions: {agent_prompts[agent_type]}"

        return base_prompt

    def _get_deliverable_structure(self, phase_type: str) -> Dict[str, str]:
        """Get expected deliverable structure for a phase type"""
        structures = {
            "discovery": {
                "requirements.md": "Detailed requirements document",
                "user_stories.md": "User stories with acceptance criteria",
                "research_findings.md": "Research and feasibility analysis",
            },
            "design": {
                "architecture.md": "System architecture document",
                "api_design.md": "API specifications",
                "database_schema.sql": "Database design",
                "ui_mockups/": "UI/UX designs and mockups",
            },
            "implementation": {
                "src/": "Source code",
                "tests/": "Test files",
                "config/": "Configuration files",
                "scripts/": "Utility scripts",
            },
            "qa": {
                "test_plans/": "Test plans and strategies",
                "test_results/": "Test execution results",
                "bug_reports/": "Bug reports and issues",
                "performance_reports/": "Performance test results",
            },
            "documentation": {
                "README.md": "Project overview and setup",
                "docs/api/": "API documentation",
                "docs/user/": "User documentation",
                "docs/developer/": "Developer documentation",
            },
            "deployment": {
                "deployment/": "Deployment configurations",
                "kubernetes/": "Kubernetes manifests",
                "docker/": "Docker configurations",
                "ci_cd/": "CI/CD pipeline configurations",
            },
        }

        return structures.get(phase_type, {})

    async def shutdown(self):
        """Shutdown the DPO system gracefully"""
        logger.info("Shutting down DPO Main Controller...")

        # Cancel active workflows
        for workflow_id in list(self.active_workflows.keys()):
            await self.cancel_workflow(workflow_id)

        # Shutdown orchestrator
        await self.orchestrator.shutdown()

        # Shutdown executor
        self.executor.shutdown(wait=True)

        # Save metrics
        metrics_file = Path(self.config.output_base_dir) / "metrics.json"
        metrics_file.parent.mkdir(parents=True, exist_ok=True)
        with open(metrics_file, "w") as f:
            json.dump(asdict(self.metrics), f, indent=2)

        logger.info("DPO Main Controller shutdown complete")


# Example usage
async def main():
    """Example usage of the DPO Main Controller"""

    # Initialize with custom configuration
    config = DPOConfiguration(
        output_base_dir="output/dpo_main_test",
        max_parallel_agents=5,
        enable_intelligence=True,
        enable_context_injection=True,
    )

    dpo = DevelopmentProcessOrchestrator(config)

    try:
        # Process a development request
        result = await dpo.process_development_request(
            request="Build a task management API with user authentication, task CRUD operations, and real-time notifications",
            project_type="api",
            complexity="moderate",
            context={
                "framework": "FastAPI",
                "database": "PostgreSQL",
                "features": ["authentication", "crud", "notifications"],
            },
            enhancement_prefs={
                "prioritize_quality": True,
                "prioritize_performance": True,
            },
        )

        if result["success"]:
            workflow_id = result["workflow_id"]
            print(f"Workflow initiated: {workflow_id}")

            # Monitor progress
            for _ in range(30):
                await asyncio.sleep(2)
                status = await dpo.get_workflow_status(workflow_id)
                print(f"Status: {status.get('status')}")

                if status.get("status") in ["completed", "failed"]:
                    break

            # Get results
            results = await dpo.get_workflow_results(workflow_id)
            print(f"Results: {json.dumps(results, indent=2)}")

            # Show metrics
            metrics = dpo.get_metrics()
            print(f"Metrics: {json.dumps(metrics, indent=2)}")
        else:
            print(f"Request failed: {result.get('error')}")

    finally:
        await dpo.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
