"""
LLM-Driven Orchestrator - Leverages Claude's intelligence for all decision-making
Replaces keyword matching with intelligent analysis and reasoning
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import logging

from core.base import BaseModule, BuildRequest, BuildResult, Requirements, ProjectType, TechInfo

logger = logging.getLogger(__name__)


@dataclass
class LLMDecision:
    """Represents a decision made by the LLM"""
    decision_type: str
    reasoning: str
    confidence: float
    data: Dict[str, Any]
    alternatives: List[Dict[str, Any]] = None
    risks: List[str] = None


class LLMOrchestrator(BaseModule):
    """Orchestrator that uses LLM intelligence for all decisions"""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize with LLM-first approach"""
        super().__init__(config)
        self.llm_decisions = []
        self.context_history = []
        
    async def build(self, request: BuildRequest) -> BuildResult:
        """Execute build pipeline with LLM-driven decisions"""
        start_time = datetime.now()
        self.log(f"Starting intelligent build: {request.description}")
        
        try:
            # Phase 1: Deep Understanding via LLM
            self.log("Phase 1: LLM Requirements Analysis")
            requirements = await self._llm_analyze_requirements(request)
            
            # Phase 2: Intelligent Research
            self.log("Phase 2: LLM-Guided Research")
            research_strategy = await self._llm_plan_research(requirements)
            research_results = await self._execute_research(research_strategy)
            
            # Phase 3: Architectural Design via LLM
            self.log("Phase 3: LLM Architecture Design")
            architecture = await self._llm_design_architecture(requirements, research_results)
            
            # Phase 4: Implementation Strategy via LLM
            self.log("Phase 4: LLM Implementation Planning")
            implementation_plan = await self._llm_plan_implementation(architecture)
            
            # Phase 5: Code Generation with LLM Guidance
            self.log("Phase 5: LLM-Guided Code Generation")
            generated_code = await self._llm_generate_code(implementation_plan)
            
            # Phase 6: Intelligent Validation
            self.log("Phase 6: LLM Code Review")
            validation_result = await self._llm_validate_code(generated_code)
            
            return BuildResult(
                success=True,
                project_path=generated_code["project_path"],
                tech_stack=architecture["tech_stack"],
                files_created=generated_code["files"],
                execution_time=(datetime.now() - start_time).total_seconds(),
                errors=[],
                warnings=validation_result.get("warnings", []),
                metrics={
                    "llm_decisions": len(self.llm_decisions),
                    "confidence_avg": sum(d.confidence for d in self.llm_decisions) / len(self.llm_decisions)
                }
            )
            
        except Exception as e:
            self.log(f"Build failed: {str(e)}", "ERROR")
            # LLM-driven error recovery
            recovery_strategy = await self._llm_error_recovery(e, self.context_history)
            if recovery_strategy:
                return await self._execute_recovery(recovery_strategy)
            raise
    
    async def _llm_analyze_requirements(self, request: BuildRequest) -> Requirements:
        """Use LLM to deeply understand requirements"""
        
        prompt = f"""
        Analyze this software project request and provide a comprehensive understanding:
        
        Request: "{request.description}"
        
        Please analyze and return a JSON response with:
        1. project_type: The most appropriate type (web_app, api, cli, mobile, desktop, library, etc.)
        2. core_purpose: What is the main goal/problem this solves?
        3. target_users: Who will use this?
        4. technical_requirements: List of specific technical needs
        5. functional_requirements: List of features/capabilities needed
        6. non_functional_requirements: Performance, security, scalability needs
        7. implied_requirements: Things not explicitly stated but likely needed
        8. complexity_assessment: Simple/Medium/Complex with reasoning
        9. architectural_patterns: Suggested patterns (MVC, microservices, etc.)
        10. key_challenges: Main technical challenges to address
        11. success_criteria: How to measure if the project is successful
        
        Think step by step. Consider modern best practices and what would create the best user experience.
        Don't just match keywords - understand the intent and purpose.
        """
        
        # This would call Claude API in production
        llm_response = await self._call_llm(prompt)
        
        # Parse LLM response
        analysis = json.loads(llm_response)
        
        # Record decision
        self.llm_decisions.append(LLMDecision(
            decision_type="requirements_analysis",
            reasoning=analysis.get("reasoning", ""),
            confidence=analysis.get("confidence", 0.9),
            data=analysis
        ))
        
        # Convert to Requirements object with rich data
        return Requirements(
            project_type=self._map_project_type(analysis["project_type"]),
            features=analysis["functional_requirements"],
            complexity=analysis["complexity_assessment"]["level"],
            estimated_time=analysis["complexity_assessment"]["estimated_hours"],
            tech_preferences={},
            constraints=analysis["non_functional_requirements"],
            # Store full analysis for later use
            full_analysis=analysis
        )
    
    async def _llm_plan_research(self, requirements: Requirements) -> Dict[str, Any]:
        """LLM decides what needs to be researched"""
        
        prompt = f"""
        Based on these project requirements, determine what technical research is needed:
        
        Requirements: {json.dumps(requirements.full_analysis, indent=2)}
        
        Create a research strategy that includes:
        1. technologies_to_research: List of specific technologies/frameworks to investigate
        2. research_priorities: What's most important to get right?
        3. evaluation_criteria: How to evaluate technology choices
        4. alternative_stacks: At least 2 different tech stack options to consider
        5. information_gaps: What do we need to learn more about?
        6. risk_areas: Technical areas that could cause problems
        
        Consider:
        - Latest stable versions (2024-2025)
        - Community support and ecosystem
        - Learning curve vs project timeline
        - Long-term maintenance
        - Performance requirements
        
        Return a detailed research plan in JSON format.
        """
        
        research_plan = await self._call_llm(prompt)
        return json.loads(research_plan)
    
    async def _llm_design_architecture(self, requirements: Requirements, research: Dict) -> Dict[str, Any]:
        """LLM designs the system architecture"""
        
        prompt = f"""
        Design the architecture for this project based on requirements and research:
        
        Requirements: {json.dumps(requirements.full_analysis, indent=2)}
        Research Results: {json.dumps(research, indent=2)}
        
        Create a comprehensive architecture that includes:
        
        1. system_design:
           - overall_architecture: Description of the system design
           - components: List of major components and their responsibilities
           - data_flow: How data moves through the system
           - integration_points: External systems/APIs to integrate
        
        2. tech_stack:
           - frontend: Framework and key libraries with versions
           - backend: Framework and key libraries with versions
           - database: Type and specific product with version
           - infrastructure: Hosting, CI/CD, monitoring tools
           - development_tools: Build tools, linters, formatters
        
        3. project_structure:
           - directory_layout: Detailed folder structure
           - file_organization: How to organize code files
           - naming_conventions: Standards for naming
           - module_boundaries: How to separate concerns
        
        4. implementation_patterns:
           - design_patterns: Specific patterns to use (Observer, Factory, etc.)
           - state_management: How to handle application state
           - error_handling: Strategy for errors and exceptions
           - security_measures: Authentication, authorization, data protection
        
        5. quality_measures:
           - testing_strategy: Unit, integration, e2e testing approach
           - code_quality: Linting, formatting, review standards
           - documentation: What needs to be documented and how
           - monitoring: Logging, metrics, alerting
        
        Think architecturally. Consider scalability, maintainability, and developer experience.
        Make specific technology choices with exact versions where applicable.
        """
        
        architecture = await self._call_llm(prompt)
        return json.loads(architecture)
    
    async def _llm_plan_implementation(self, architecture: Dict) -> Dict[str, Any]:
        """LLM creates detailed implementation plan"""
        
        prompt = f"""
        Create a detailed implementation plan for building this project:
        
        Architecture: {json.dumps(architecture, indent=2)}
        
        Provide an implementation plan with:
        
        1. implementation_sequence:
           - Phase 1: Foundation (what to build first)
           - Phase 2: Core Features (main functionality)
           - Phase 3: Enhanced Features (additional capabilities)
           - Phase 4: Polish (optimization, UX improvements)
        
        2. file_specifications: For each file to create:
           - path: Exact file path
           - purpose: What this file does
           - dependencies: What it imports/requires
           - exports: What it provides to other modules
           - key_logic: Main algorithms/logic to implement
           - connections: How it connects to other files
        
        3. code_patterns:
           - How to structure each type of file
           - Common utilities to create
           - Shared types/interfaces
           - Configuration approach
        
        4. integration_plan:
           - How components connect
           - API contracts between modules
           - Data models and schemas
           - Event/message flows
        
        5. deployment_preparation:
           - Build configuration
           - Environment variables
           - Docker setup if applicable
           - Deployment scripts
        
        Be specific about implementation details. This plan will guide actual code generation.
        """
        
        implementation = await self._call_llm(prompt)
        return json.loads(implementation)
    
    async def _llm_generate_code(self, plan: Dict) -> Dict[str, Any]:
        """Generate actual code with LLM guidance"""
        
        generated_files = []
        project_path = Path("output") / self._generate_project_name(plan)
        project_path.mkdir(parents=True, exist_ok=True)
        
        # For each file in the plan, generate with LLM
        for file_spec in plan["file_specifications"]:
            code = await self._generate_single_file(file_spec, plan)
            file_path = project_path / file_spec["path"]
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(code)
            generated_files.append(str(file_path))
        
        return {
            "project_path": project_path,
            "files": generated_files
        }
    
    async def _generate_single_file(self, file_spec: Dict, context: Dict) -> str:
        """Generate a single file with LLM"""
        
        prompt = f"""
        Generate the complete code for this file:
        
        File Specification: {json.dumps(file_spec, indent=2)}
        Project Context: {json.dumps(context.get("code_patterns", {}), indent=2)}
        Architecture: {json.dumps(context.get("system_design", {}), indent=2)}
        
        Requirements:
        1. Generate production-ready code
        2. Include proper error handling
        3. Add helpful comments (but not excessive)
        4. Follow the specified patterns and conventions
        5. Ensure type safety where applicable
        6. Make it maintainable and testable
        
        Generate ONLY the code for this file, no explanations.
        """
        
        code = await self._call_llm(prompt)
        return code
    
    async def _llm_validate_code(self, generated_code: Dict) -> Dict[str, Any]:
        """LLM reviews and validates generated code"""
        
        prompt = f"""
        Review this generated project for quality and completeness:
        
        Project Path: {generated_code["project_path"]}
        Files Created: {json.dumps(generated_code["files"], indent=2)}
        
        Perform a comprehensive review checking for:
        
        1. completeness:
           - Are all necessary files present?
           - Are there any missing configurations?
           - Is the project ready to run?
        
        2. code_quality:
           - Are there any obvious bugs?
           - Is error handling adequate?
           - Are there security vulnerabilities?
        
        3. best_practices:
           - Does it follow modern standards?
           - Is the code maintainable?
           - Are there performance issues?
        
        4. improvements:
           - What could be enhanced?
           - What might cause problems in production?
           - What should be added for robustness?
        
        Return a JSON report with:
        - status: "ready" or "needs_fixes"
        - warnings: List of non-critical issues
        - errors: List of critical issues
        - suggestions: List of improvements
        - confidence: How confident in the code quality (0-1)
        """
        
        validation = await self._call_llm(prompt)
        return json.loads(validation)
    
    async def _llm_error_recovery(self, error: Exception, context: List) -> Optional[Dict]:
        """LLM analyzes error and suggests recovery"""
        
        prompt = f"""
        An error occurred during project generation. Analyze and suggest recovery:
        
        Error: {str(error)}
        Error Type: {type(error).__name__}
        Context History: {json.dumps(context[-5:], indent=2)}  # Last 5 decisions
        
        Analyze:
        1. What caused this error?
        2. Can it be automatically fixed?
        3. What's the recovery strategy?
        
        Provide a recovery plan with:
        - can_recover: boolean
        - recovery_steps: List of steps to take
        - alternative_approach: Different way to achieve the goal
        - required_changes: What needs to be modified
        - confidence: How likely the recovery will work (0-1)
        
        Be creative in finding solutions. Consider alternative approaches.
        """
        
        recovery = await self._call_llm(prompt)
        return json.loads(recovery)
    
    async def _call_llm(self, prompt: str) -> str:
        """
        Call Claude API for intelligent decision making
        In production, this would use the actual Claude API
        For now, it's a placeholder that would integrate with mcp__claude-code
        """
        
        # Record context for learning
        self.context_history.append({
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt[:200],  # Store truncated for history
            "type": "llm_call"
        })
        
        # In production:
        # from mcp__claude_code__claude_run import claude_run
        # response = await claude_run(task=prompt)
        
        # Placeholder for testing
        # This would be replaced with actual Claude API call
        return json.dumps({
            "status": "success",
            "reasoning": "LLM analysis complete",
            "confidence": 0.95,
            "data": {}
        })
    
    def _map_project_type(self, llm_type: str) -> ProjectType:
        """Map LLM's project type to enum (only place we need mapping)"""
        mapping = {
            "web_app": ProjectType.WEB_APP,
            "web_application": ProjectType.WEB_APP,
            "rest_api": ProjectType.REST_API,
            "api": ProjectType.REST_API,
            "cli": ProjectType.CLI_TOOL,
            "cli_tool": ProjectType.CLI_TOOL,
            "mobile": ProjectType.MOBILE_APP,
            "mobile_app": ProjectType.MOBILE_APP,
            "dashboard": ProjectType.DASHBOARD,
            "library": ProjectType.LIBRARY,
            "package": ProjectType.LIBRARY,
            "fullstack": ProjectType.FULLSTACK,
            "microservice": ProjectType.MICROSERVICE
        }
        return mapping.get(llm_type.lower(), ProjectType.WEB_APP)
    
    def _generate_project_name(self, plan: Dict) -> str:
        """Generate project name from plan"""
        # Use LLM-suggested name or generate from purpose
        if "project_name" in plan:
            return plan["project_name"]
        return f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


class LLMCodeGenerator:
    """Code generator that uses LLM for all generation logic"""
    
    async def generate_with_intelligence(self, spec: Dict) -> str:
        """Generate code using LLM intelligence, not templates"""
        
        prompt = f"""
        Generate code based on this specification:
        {json.dumps(spec, indent=2)}
        
        Requirements:
        - Modern, production-ready code
        - Follow best practices for {spec.get('language', 'the chosen language')}
        - Include proper error handling
        - Make it maintainable and testable
        - Use current library versions (2024-2025)
        
        Generate complete, working code.
        """
        
        # This would call Claude to generate actual code
        # No templates, no keyword matching - pure LLM intelligence
        return await self._call_llm(prompt)