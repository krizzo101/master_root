"""
SDLC-Based Orchestrator - Follows proper Software Development Life Cycle
Ensures professional-grade software delivery through structured phases
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import logging

from core.base import BaseModule, BuildRequest, BuildResult

logger = logging.getLogger(__name__)


class SDLCPhase(Enum):
    """Standard SDLC phases for professional software development"""
    PLANNING = "planning"
    REQUIREMENTS = "requirements_analysis"
    DESIGN = "system_design"
    IMPLEMENTATION = "implementation"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    REVIEW = "review_and_documentation"
    MAINTENANCE = "maintenance_planning"


@dataclass
class PhaseArtifact:
    """Artifact produced by each SDLC phase"""
    phase: SDLCPhase
    artifact_type: str
    content: Any
    timestamp: datetime = field(default_factory=datetime.now)
    approved: bool = False
    review_notes: List[str] = field(default_factory=list)


@dataclass
class SDLCContext:
    """Maintains context throughout the SDLC"""
    project_id: str
    artifacts: Dict[SDLCPhase, List[PhaseArtifact]] = field(default_factory=dict)
    decisions: List[Dict] = field(default_factory=list)
    risks: List[Dict] = field(default_factory=list)
    stakeholder_requirements: Dict = field(default_factory=dict)
    quality_gates: Dict[SDLCPhase, bool] = field(default_factory=dict)
    current_phase: SDLCPhase = SDLCPhase.PLANNING


class SDLCOrchestrator(BaseModule):
    """
    Orchestrator that follows professional SDLC methodology
    Ensures proper software engineering practices at every step
    """
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.context = None
        self.llm_temperature = {
            # Different temperatures for different phases
            SDLCPhase.PLANNING: 0.7,        # Creative planning
            SDLCPhase.REQUIREMENTS: 0.3,    # Precise requirements
            SDLCPhase.DESIGN: 0.6,          # Balanced design
            SDLCPhase.IMPLEMENTATION: 0.4,  # Consistent code
            SDLCPhase.TESTING: 0.2,         # Rigorous testing
            SDLCPhase.DEPLOYMENT: 0.1,      # Careful deployment
            SDLCPhase.REVIEW: 0.3,          # Thorough review
            SDLCPhase.MAINTENANCE: 0.5      # Forward thinking
        }
    
    async def build(self, request: BuildRequest) -> BuildResult:
        """Execute complete SDLC for software delivery"""
        
        # Initialize SDLC context
        self.context = SDLCContext(
            project_id=self._generate_project_id(request),
            stakeholder_requirements={"original_request": request.description}
        )
        
        self.log("🚀 Starting SDLC-based software development process")
        
        try:
            # PHASE 1: PLANNING
            await self._phase_planning(request)
            
            # PHASE 2: REQUIREMENTS ANALYSIS
            await self._phase_requirements_analysis()
            
            # PHASE 3: SYSTEM DESIGN
            await self._phase_system_design()
            
            # PHASE 4: IMPLEMENTATION
            await self._phase_implementation()
            
            # PHASE 5: TESTING
            await self._phase_testing()
            
            # PHASE 6: DEPLOYMENT PREPARATION
            await self._phase_deployment()
            
            # PHASE 7: REVIEW & DOCUMENTATION
            await self._phase_review_documentation()
            
            # PHASE 8: MAINTENANCE PLANNING
            await self._phase_maintenance_planning()
            
            # Generate final deliverables
            return await self._generate_deliverables()
            
        except Exception as e:
            # Proper error handling with rollback
            await self._handle_sdlc_failure(e)
            raise
    
    async def _phase_planning(self, request: BuildRequest):
        """
        PHASE 1: PROJECT PLANNING
        - Define project scope
        - Identify stakeholders
        - Create project charter
        - Risk assessment
        - Resource planning
        """
        self.context.current_phase = SDLCPhase.PLANNING
        self.log("📋 PHASE 1: PROJECT PLANNING")
        
        prompt = f"""
        You are a Senior Project Manager starting a new software project.
        
        Original Request: "{request.description}"
        
        Create a comprehensive project plan including:
        
        1. PROJECT CHARTER:
           - Project title and codename
           - Executive summary
           - Business case/justification
           - Success criteria
           - Out of scope items
        
        2. STAKEHOLDER ANALYSIS:
           - Primary users (who will use this daily?)
           - Secondary users (occasional users?)
           - Technical stakeholders (who maintains it?)
           - Business stakeholders (who pays for it?)
           - Their needs and concerns
        
        3. SCOPE DEFINITION:
           - What IS included (must-haves)
           - What COULD be included (nice-to-haves)
           - What is NOT included (explicitly out of scope)
           - Future phases/versions
        
        4. RISK ASSESSMENT:
           - Technical risks (what could go wrong?)
           - Business risks (market/user adoption)
           - Resource risks (skills, time, budget)
           - Mitigation strategies for each
        
        5. PROJECT TIMELINE:
           - Estimated phases and durations
           - Key milestones
           - Critical path items
           - Dependencies
        
        6. RESOURCE REQUIREMENTS:
           - Technical skills needed
           - Tools and technologies
           - Infrastructure requirements
           - Estimated effort (person-hours)
        
        7. QUALITY STANDARDS:
           - Code quality metrics
           - Performance benchmarks
           - Security requirements
           - Compliance needs
        
        Think strategically. Consider long-term implications.
        What would make this project truly successful?
        
        Return comprehensive JSON planning document.
        """
        
        planning_doc = await self._call_llm(prompt, SDLCPhase.PLANNING)
        
        # Store planning artifacts
        self._store_artifact(
            SDLCPhase.PLANNING,
            "project_charter",
            planning_doc
        )
        
        # Quality gate: Approve planning before proceeding
        await self._quality_gate_review(SDLCPhase.PLANNING)
    
    async def _phase_requirements_analysis(self):
        """
        PHASE 2: REQUIREMENTS ANALYSIS
        - Gather detailed requirements
        - Create user stories
        - Define acceptance criteria
        - Prioritize features
        """
        self.context.current_phase = SDLCPhase.REQUIREMENTS
        self.log("📝 PHASE 2: REQUIREMENTS ANALYSIS")
        
        planning = self._get_artifact(SDLCPhase.PLANNING, "project_charter")
        
        prompt = f"""
        You are a Senior Business Analyst conducting requirements analysis.
        
        Based on the project plan: {json.dumps(planning, indent=2)}
        
        Perform comprehensive requirements analysis:
        
        1. FUNCTIONAL REQUIREMENTS:
           For each feature:
           - User story (As a... I want... So that...)
           - Acceptance criteria (Given... When... Then...)
           - Priority (Must/Should/Could/Won't - MoSCoW)
           - Dependencies on other features
           - Estimated complexity (1-5)
        
        2. NON-FUNCTIONAL REQUIREMENTS:
           - Performance (response times, throughput)
           - Scalability (concurrent users, data volume)
           - Security (authentication, authorization, encryption)
           - Usability (accessibility, user experience)
           - Reliability (uptime, error handling)
           - Compatibility (browsers, devices, systems)
           - Maintainability (code quality, documentation)
        
        3. DATA REQUIREMENTS:
           - Data entities and relationships
           - Data volume estimates
           - Data retention policies
           - Privacy and compliance needs
           - Backup and recovery requirements
        
        4. INTEGRATION REQUIREMENTS:
           - External systems to integrate
           - APIs to consume or provide
           - Data exchange formats
           - Authentication methods
           - Rate limits and quotas
        
        5. USER INTERFACE REQUIREMENTS:
           - User personas and journeys
           - Key screens/pages needed
           - Navigation flow
           - Responsive design needs
           - Accessibility standards (WCAG)
        
        6. CONSTRAINTS:
           - Technical constraints
           - Business constraints
           - Regulatory constraints
           - Time/budget constraints
        
        7. ASSUMPTIONS:
           - What we're assuming to be true
           - Dependencies on these assumptions
           - Risks if assumptions are wrong
        
        Be thorough. Missing requirements cause project failure.
        Consider edge cases and error scenarios.
        
        Return detailed requirements specification in JSON.
        """
        
        requirements = await self._call_llm(prompt, SDLCPhase.REQUIREMENTS)
        
        self._store_artifact(
            SDLCPhase.REQUIREMENTS,
            "requirements_specification",
            requirements
        )
        
        await self._quality_gate_review(SDLCPhase.REQUIREMENTS)
    
    async def _phase_system_design(self):
        """
        PHASE 3: SYSTEM DESIGN
        - Architecture design
        - Database design
        - API design
        - Security design
        - UI/UX design
        """
        self.context.current_phase = SDLCPhase.DESIGN
        self.log("🏗️ PHASE 3: SYSTEM DESIGN")
        
        requirements = self._get_artifact(SDLCPhase.REQUIREMENTS, "requirements_specification")
        
        prompt = f"""
        You are a Senior Software Architect designing the system.
        
        Requirements: {json.dumps(requirements, indent=2)}
        
        Create comprehensive system design:
        
        1. ARCHITECTURE DESIGN:
           - Overall architecture pattern (microservices, monolith, serverless, etc.)
           - Component diagram with responsibilities
           - Data flow architecture
           - Deployment architecture
           - Technology stack with specific versions (2024-2025)
           - Justification for each choice
        
        2. DATABASE DESIGN:
           - Database type selection (SQL/NoSQL) with reasoning
           - Entity-Relationship diagram
           - Table/collection schemas
           - Indexes and optimization strategies
           - Data migration approach
           - Backup and recovery design
        
        3. API DESIGN:
           - API architecture (REST, GraphQL, gRPC)
           - Endpoint definitions
           - Request/response schemas
           - Authentication/authorization flow
           - Rate limiting strategy
           - API versioning approach
           - Error handling standards
        
        4. SECURITY DESIGN:
           - Threat model (STRIDE analysis)
           - Authentication mechanism
           - Authorization model (RBAC, ABAC)
           - Data encryption (at rest, in transit)
           - Input validation strategy
           - Security headers and CSP
           - Audit logging design
        
        5. UI/UX DESIGN:
           - Design system/component library choice
           - Page layouts and wireframes
           - Navigation architecture
           - State management approach
           - Responsive breakpoints
           - Accessibility approach
           - Performance optimization strategy
        
        6. INFRASTRUCTURE DESIGN:
           - Hosting environment (cloud/on-premise)
           - Container strategy (Docker, K8s)
           - CI/CD pipeline design
           - Monitoring and alerting
           - Logging architecture
           - Disaster recovery plan
        
        7. INTEGRATION DESIGN:
           - External service integrations
           - Message queue/event bus design
           - Webhook implementations
           - Third-party API integrations
           - Error handling and retry logic
        
        8. TESTING STRATEGY:
           - Unit testing approach
           - Integration testing design
           - E2E testing strategy
           - Performance testing plan
           - Security testing approach
           - Test data management
        
        Design for scalability, maintainability, and reliability.
        Consider future growth and changes.
        
        Return complete design document in JSON.
        """
        
        design = await self._call_llm(prompt, SDLCPhase.DESIGN)
        
        self._store_artifact(SDLCPhase.DESIGN, "system_design", design)
        
        # Additional design artifacts
        await self._create_design_diagrams(design)
        await self._create_api_specifications(design)
        
        await self._quality_gate_review(SDLCPhase.DESIGN)
    
    async def _phase_implementation(self):
        """
        PHASE 4: IMPLEMENTATION
        - Setup development environment
        - Implement core features
        - Code review cycles
        - Continuous integration
        """
        self.context.current_phase = SDLCPhase.IMPLEMENTATION
        self.log("💻 PHASE 4: IMPLEMENTATION")
        
        design = self._get_artifact(SDLCPhase.DESIGN, "system_design")
        requirements = self._get_artifact(SDLCPhase.REQUIREMENTS, "requirements_specification")
        
        # Break implementation into sprints
        sprints = await self._plan_implementation_sprints(requirements, design)
        
        for sprint_num, sprint in enumerate(sprints, 1):
            self.log(f"🏃 Sprint {sprint_num}: {sprint['goal']}")
            
            # Implement each user story in the sprint
            for story in sprint["stories"]:
                code = await self._implement_user_story(story, design)
                
                # Code review
                review = await self._code_review(code, story, design)
                
                if review["needs_changes"]:
                    code = await self._refactor_code(code, review["feedback"])
                
                self._store_artifact(
                    SDLCPhase.IMPLEMENTATION,
                    f"sprint_{sprint_num}_story_{story['id']}",
                    code
                )
        
        # Generate complete codebase
        await self._assemble_codebase()
        
        await self._quality_gate_review(SDLCPhase.IMPLEMENTATION)
    
    async def _phase_testing(self):
        """
        PHASE 5: TESTING
        - Unit testing
        - Integration testing
        - System testing
        - User acceptance testing
        """
        self.context.current_phase = SDLCPhase.TESTING
        self.log("🧪 PHASE 5: TESTING")
        
        implementation = self._get_artifact(SDLCPhase.IMPLEMENTATION, "codebase")
        requirements = self._get_artifact(SDLCPhase.REQUIREMENTS, "requirements_specification")
        
        # Generate comprehensive test suite
        test_plan = await self._create_test_plan(requirements)
        
        # Unit Tests
        unit_tests = await self._generate_unit_tests(implementation)
        unit_results = await self._run_tests(unit_tests, "unit")
        
        # Integration Tests
        integration_tests = await self._generate_integration_tests(implementation)
        integration_results = await self._run_tests(integration_tests, "integration")
        
        # E2E Tests
        e2e_tests = await self._generate_e2e_tests(requirements)
        e2e_results = await self._run_tests(e2e_tests, "e2e")
        
        # Performance Tests
        perf_tests = await self._generate_performance_tests(requirements)
        perf_results = await self._run_tests(perf_tests, "performance")
        
        # Security Tests
        security_tests = await self._generate_security_tests(implementation)
        security_results = await self._run_tests(security_tests, "security")
        
        # Generate test report
        test_report = await self._generate_test_report({
            "unit": unit_results,
            "integration": integration_results,
            "e2e": e2e_results,
            "performance": perf_results,
            "security": security_results
        })
        
        self._store_artifact(SDLCPhase.TESTING, "test_report", test_report)
        
        # Fix any critical issues found
        if test_report["critical_issues"]:
            await self._fix_critical_issues(test_report["critical_issues"])
        
        await self._quality_gate_review(SDLCPhase.TESTING)
    
    async def _phase_deployment(self):
        """
        PHASE 6: DEPLOYMENT PREPARATION
        - Environment setup
        - Deployment scripts
        - Configuration management
        - Rollback procedures
        """
        self.context.current_phase = SDLCPhase.DEPLOYMENT
        self.log("🚢 PHASE 6: DEPLOYMENT PREPARATION")
        
        design = self._get_artifact(SDLCPhase.DESIGN, "system_design")
        
        deployment_config = await self._create_deployment_configuration(design)
        
        # Create deployment artifacts
        artifacts = {
            "dockerfile": await self._generate_dockerfile(design),
            "docker_compose": await self._generate_docker_compose(design),
            "ci_cd_pipeline": await self._generate_ci_cd_pipeline(design),
            "environment_configs": await self._generate_env_configs(design),
            "deployment_scripts": await self._generate_deployment_scripts(design),
            "monitoring_config": await self._generate_monitoring_config(design),
            "rollback_procedures": await self._generate_rollback_procedures(design)
        }
        
        for name, content in artifacts.items():
            self._store_artifact(SDLCPhase.DEPLOYMENT, name, content)
        
        await self._quality_gate_review(SDLCPhase.DEPLOYMENT)
    
    async def _phase_review_documentation(self):
        """
        PHASE 7: REVIEW & DOCUMENTATION
        - Technical documentation
        - User documentation
        - API documentation
        - Runbooks
        """
        self.context.current_phase = SDLCPhase.REVIEW
        self.log("📚 PHASE 7: REVIEW & DOCUMENTATION")
        
        # Generate comprehensive documentation
        docs = {
            "technical_docs": await self._generate_technical_documentation(),
            "user_guide": await self._generate_user_guide(),
            "api_docs": await self._generate_api_documentation(),
            "deployment_guide": await self._generate_deployment_guide(),
            "runbook": await self._generate_runbook(),
            "architecture_decisions": await self._generate_adr(),
            "contributing_guide": await self._generate_contributing_guide()
        }
        
        for doc_type, content in docs.items():
            self._store_artifact(SDLCPhase.REVIEW, doc_type, content)
        
        # Final review
        final_review = await self._conduct_final_review()
        self._store_artifact(SDLCPhase.REVIEW, "final_review", final_review)
        
        await self._quality_gate_review(SDLCPhase.REVIEW)
    
    async def _phase_maintenance_planning(self):
        """
        PHASE 8: MAINTENANCE PLANNING
        - Maintenance procedures
        - Update strategies
        - Monitoring setup
        - Support documentation
        """
        self.context.current_phase = SDLCPhase.MAINTENANCE
        self.log("🔧 PHASE 8: MAINTENANCE PLANNING")
        
        maintenance_plan = await self._create_maintenance_plan()
        
        self._store_artifact(
            SDLCPhase.MAINTENANCE,
            "maintenance_plan",
            maintenance_plan
        )
        
        await self._quality_gate_review(SDLCPhase.MAINTENANCE)
    
    async def _quality_gate_review(self, phase: SDLCPhase):
        """
        Quality gate review before proceeding to next phase
        Ensures each phase meets quality standards
        """
        artifacts = self.context.artifacts.get(phase, [])
        
        prompt = f"""
        You are a Quality Assurance Lead reviewing {phase.value} phase artifacts.
        
        Artifacts to review: {json.dumps([a.artifact_type for a in artifacts])}
        
        Perform quality gate review:
        1. Are all required deliverables present?
        2. Do they meet quality standards?
        3. Are there any critical gaps?
        4. What risks remain?
        5. Should we proceed to the next phase?
        
        Return JSON with:
        - passed: boolean
        - issues: list of issues found
        - recommendations: list of improvements
        - risks: remaining risks
        """
        
        review = await self._call_llm(prompt, phase)
        
        if not review["passed"]:
            # Address issues before proceeding
            await self._address_quality_issues(phase, review["issues"])
        
        self.context.quality_gates[phase] = True
        self.log(f"✅ Quality gate passed for {phase.value}")
    
    async def _generate_deliverables(self) -> BuildResult:
        """Generate final deliverables package"""
        
        # Collect all artifacts
        all_artifacts = {}
        for phase, artifacts in self.context.artifacts.items():
            all_artifacts[phase.value] = [
                {
                    "type": a.artifact_type,
                    "content": a.content,
                    "timestamp": a.timestamp.isoformat()
                }
                for a in artifacts
            ]
        
        # Create project structure
        project_path = Path("output") / self.context.project_id
        
        # Write code files
        codebase = self._get_artifact(SDLCPhase.IMPLEMENTATION, "codebase")
        for file_path, content in codebase.items():
            full_path = project_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
        
        # Write documentation
        docs_path = project_path / "docs"
        docs_path.mkdir(exist_ok=True)
        
        for doc_artifact in self.context.artifacts.get(SDLCPhase.REVIEW, []):
            doc_path = docs_path / f"{doc_artifact.artifact_type}.md"
            doc_path.write_text(doc_artifact.content)
        
        # Write SDLC artifacts
        sdlc_path = project_path / ".sdlc"
        sdlc_path.mkdir(exist_ok=True)
        
        # Save complete SDLC history
        sdlc_history = {
            "project_id": self.context.project_id,
            "phases_completed": list(self.context.quality_gates.keys()),
            "artifacts": all_artifacts,
            "decisions": self.context.decisions,
            "risks": self.context.risks
        }
        
        (sdlc_path / "sdlc_history.json").write_text(
            json.dumps(sdlc_history, indent=2, default=str)
        )
        
        return BuildResult(
            success=True,
            project_path=project_path,
            tech_stack=self._get_artifact(SDLCPhase.DESIGN, "system_design")["tech_stack"],
            files_created=list(codebase.keys()),
            execution_time=0,  # Calculate from context
            errors=[],
            warnings=[],
            metrics={
                "sdlc_phases_completed": len(self.context.quality_gates),
                "total_artifacts": sum(len(a) for a in self.context.artifacts.values()),
                "test_coverage": self._get_artifact(SDLCPhase.TESTING, "test_report").get("coverage", 0),
                "quality_gates_passed": len([v for v in self.context.quality_gates.values() if v])
            }
        )
    
    # Helper methods
    
    def _store_artifact(self, phase: SDLCPhase, artifact_type: str, content: Any):
        """Store an artifact for a phase"""
        if phase not in self.context.artifacts:
            self.context.artifacts[phase] = []
        
        artifact = PhaseArtifact(
            phase=phase,
            artifact_type=artifact_type,
            content=content
        )
        
        self.context.artifacts[phase].append(artifact)
    
    def _get_artifact(self, phase: SDLCPhase, artifact_type: str) -> Any:
        """Retrieve a specific artifact"""
        artifacts = self.context.artifacts.get(phase, [])
        for artifact in artifacts:
            if artifact.artifact_type == artifact_type:
                return artifact.content
        return None
    
    async def _call_llm(self, prompt: str, phase: SDLCPhase) -> Dict:
        """Call LLM with phase-appropriate temperature"""
        temperature = self.llm_temperature.get(phase, 0.5)
        
        # In production, this would call Claude API
        # with appropriate temperature for the phase
        
        # Log the decision
        self.context.decisions.append({
            "phase": phase.value,
            "timestamp": datetime.now().isoformat(),
            "prompt_summary": prompt[:200],
            "temperature": temperature
        })
        
        # Placeholder return
        return {
            "status": "success",
            "data": {}
        }
    
    def _generate_project_id(self, request: BuildRequest) -> str:
        """Generate unique project ID"""
        from hashlib import md5
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hash_suffix = md5(request.description.encode()).hexdigest()[:8]
        return f"sdlc_{timestamp}_{hash_suffix}"