"""Orchestrator - Coordinates all modules to build projects autonomously."""

import asyncio
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from core.base import BaseModule, BuildRequest, BuildResult, Requirements, ProjectType
from modules.research_engine import ResearchEngine
from modules.generator import Generator


class Orchestrator(BaseModule):
    """Orchestrates the entire build process."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the orchestrator with all modules."""
        super().__init__(config)
        self.research_engine = ResearchEngine(config)
        self.generator = Generator(config)
        self.state = {}
        self.checkpoints = []
    
    async def build(self, request: BuildRequest) -> BuildResult:
        """Execute the complete build pipeline."""
        start_time = time.time()
        self.log(f"Starting build: {request.description}")
        
        try:
            # Phase 1: Understanding
            self.log("Phase 1: Understanding requirements")
            requirements = await self._analyze_requirements(request)
            self._create_checkpoint("requirements_analyzed", requirements)
            
            # Phase 2: Research
            self.log("Phase 2: Researching technologies")
            research_results = await self._research_phase(request, requirements)
            self._create_checkpoint("research_complete", research_results)
            
            # Phase 3: Planning
            self.log("Phase 3: Planning implementation")
            tech_stack = await self._select_tech_stack(requirements, research_results)
            self._create_checkpoint("planning_complete", tech_stack)
            
            # Phase 4: Implementation
            self.log("Phase 4: Generating code")
            generation_result = await self._generate_phase(request, requirements, tech_stack)
            self._create_checkpoint("generation_complete", generation_result)
            
            # Phase 5: Validation
            self.log("Phase 5: Validating output")
            validation_result = await self._validate_phase(generation_result)
            self._create_checkpoint("validation_complete", validation_result)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Build result
            result = BuildResult(
                success=True,
                project_path=generation_result["project_path"],
                tech_stack=tech_stack,
                files_created=generation_result["files_created"],
                execution_time=execution_time,
                errors=validation_result.get("errors", []),
                warnings=validation_result.get("warnings", []),
                metrics={
                    "phases_completed": 5,
                    "checkpoints_created": len(self.checkpoints),
                    "research_items": len(research_results),
                    "files_generated": len(generation_result["files_created"])
                }
            )
            
            self.log(f"Build completed successfully in {execution_time:.2f} seconds")
            self._report_summary(result)
            
            return result
            
        except Exception as e:
            self.log(f"Build failed: {str(e)}", "ERROR")
            
            # Attempt recovery
            recovery_result = await self._attempt_recovery(e, request)
            if recovery_result:
                return recovery_result
            
            # Return failure result
            return BuildResult(
                success=False,
                project_path=request.output_path,
                tech_stack={},
                files_created=[],
                execution_time=time.time() - start_time,
                errors=[str(e)],
                warnings=[],
                metrics={"error": str(e)}
            )
    
    async def _analyze_requirements(self, request: BuildRequest) -> Requirements:
        """Analyze the build request to extract requirements."""
        description_lower = request.description.lower()
        
        # Determine project type
        if "api" in description_lower or "rest" in description_lower:
            project_type = ProjectType.REST_API
        elif "cli" in description_lower or "command" in description_lower:
            project_type = ProjectType.CLI_TOOL
        elif "dashboard" in description_lower or "admin" in description_lower:
            project_type = ProjectType.DASHBOARD
        elif "mobile" in description_lower:
            project_type = ProjectType.MOBILE_APP
        elif "library" in description_lower or "package" in description_lower:
            project_type = ProjectType.LIBRARY
        elif "simple" in description_lower or "todo" in description_lower:
            project_type = ProjectType.SIMPLE_APP
        else:
            project_type = ProjectType.WEB_APP
        
        # Extract features
        features = []
        feature_keywords = {
            "auth": ["auth", "login", "user", "account"],
            "database": ["database", "db", "data", "storage"],
            "api": ["api", "endpoint", "rest", "graphql"],
            "ui": ["ui", "interface", "frontend", "design"],
            "testing": ["test", "testing", "tdd", "coverage"],
            "docker": ["docker", "container", "kubernetes"],
            "ci/cd": ["ci", "cd", "pipeline", "deploy"]
        }
        
        for feature, keywords in feature_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                features.append(feature)
        
        # Determine complexity
        if len(features) <= 2:
            complexity = "simple"
            estimated_time = 2
        elif len(features) <= 4:
            complexity = "medium"
            estimated_time = 5
        else:
            complexity = "complex"
            estimated_time = 10
        
        # Extract tech preferences from constraints
        tech_preferences = {}
        if request.constraints:
            tech_preferences.update(request.constraints)
        if request.preferences:
            tech_preferences.update(request.preferences)
        
        return Requirements(
            project_type=project_type,
            features=features,
            complexity=complexity,
            estimated_time=estimated_time,
            tech_preferences=tech_preferences,
            constraints=[]
        )
    
    async def _research_phase(self, request: BuildRequest, requirements: Requirements) -> Dict[str, Any]:
        """Perform research on required technologies."""
        research_results = {}
        
        # Research based on project type
        project_research = await self.research_engine.research_project_requirements(request.description)
        research_results["project"] = project_research
        
        # Research specific technologies mentioned
        if requirements.tech_preferences:
            for tech in requirements.tech_preferences.keys():
                tech_info = await self.research_engine.research_technology(tech)
                research_results[tech] = tech_info.__dict__
        
        # Get best practices
        best_practices = await self.research_engine.find_best_practices(requirements.project_type.value)
        research_results["best_practices"] = best_practices
        
        return research_results
    
    async def _select_tech_stack(self, requirements: Requirements, research: Dict[str, Any]) -> Dict[str, str]:
        """Select the technology stack based on requirements and research."""
        tech_stack = {}
        
        # Get recommended stack from research
        if "project" in research and "recommended_stack" in research["project"]:
            tech_stack.update(research["project"]["recommended_stack"])
        
        # Override with user preferences if specified
        if requirements.tech_preferences:
            for key, value in requirements.tech_preferences.items():
                # Get current version if not specified
                if "@" not in value:
                    tech_info = await self.research_engine.research_technology(value)
                    value = f"{value}@{tech_info.version}"
                tech_stack[key] = value
        
        # Ensure we have minimum required technologies
        if requirements.project_type in [ProjectType.WEB_APP, ProjectType.SIMPLE_APP]:
            if "framework" not in tech_stack:
                tech_stack["framework"] = "vite@7.1.1"
            if "language" not in tech_stack:
                tech_stack["language"] = "typescript@5.7.2"
        elif requirements.project_type == ProjectType.REST_API:
            if "framework" not in tech_stack:
                tech_stack["framework"] = "fastapi@0.117.1"
            if "language" not in tech_stack:
                tech_stack["language"] = "python@3.13.1"
        
        return tech_stack
    
    async def _generate_phase(self, request: BuildRequest, requirements: Requirements, tech_stack: Dict[str, str]) -> Dict[str, Any]:
        """Generate the project files."""
        return self.generator.generate_project(request, requirements, tech_stack)
    
    async def _validate_phase(self, generation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the generated project."""
        validation_result = {
            "errors": [],
            "warnings": []
        }
        
        project_path = generation_result["project_path"]
        
        # Check if essential files exist
        essential_files = {
            ProjectType.WEB_APP: ["package.json", "index.html"],
            ProjectType.REST_API: ["requirements.txt", "main.py"],
            ProjectType.CLI_TOOL: ["cli.py", "requirements.txt"],
            ProjectType.SIMPLE_APP: ["package.json", "index.html"]
        }
        
        # Get project type from the path structure
        if (project_path / "package.json").exists():
            project_type = ProjectType.WEB_APP
        elif (project_path / "requirements.txt").exists():
            project_type = ProjectType.REST_API
        else:
            project_type = ProjectType.SIMPLE_APP
        
        # Check for essential files
        for file in essential_files.get(project_type, []):
            if not (project_path / file).exists():
                validation_result["errors"].append(f"Missing essential file: {file}")
        
        # Check for deprecated technologies
        tech_stack = generation_result.get("tech_stack", {})
        deprecations = await self.research_engine.check_deprecations(tech_stack)
        validation_result["warnings"].extend(deprecations)
        
        # Validate file sizes
        for file_path in generation_result["files_created"]:
            file = Path(file_path)
            if file.exists() and file.stat().st_size > 1048576:  # 1MB
                validation_result["warnings"].append(f"Large file: {file_path}")
        
        return validation_result
    
    async def _attempt_recovery(self, error: Exception, request: BuildRequest) -> Optional[BuildResult]:
        """Attempt to recover from an error."""
        self.log(f"Attempting recovery from: {error}", "WARNING")
        
        # Check if we have checkpoints
        if self.checkpoints:
            last_checkpoint = self.checkpoints[-1]
            self.log(f"Resuming from checkpoint: {last_checkpoint['name']}")
            
            # Try to continue from the last successful phase
            # This is simplified - real implementation would be more sophisticated
            return None
        
        return None
    
    def _create_checkpoint(self, name: str, data: Any):
        """Create a checkpoint for recovery."""
        checkpoint = {
            "name": name,
            "timestamp": datetime.now().isoformat(),
            "data": data if isinstance(data, (dict, list, str, int, float)) else str(data)
        }
        self.checkpoints.append(checkpoint)
        self.log(f"Checkpoint created: {name}")
    
    def _report_summary(self, result: BuildResult):
        """Report a summary of the build."""
        print("\n" + "="*60)
        print("🎉 BUILD COMPLETE")
        print("="*60)
        print(f"✅ Success: {result.success}")
        print(f"📁 Project: {result.project_path}")
        print(f"⏱️  Time: {result.execution_time:.2f} seconds")
        print(f"📄 Files: {len(result.files_created)} created")
        
        if result.tech_stack:
            print(f"\n📦 Tech Stack:")
            for key, value in result.tech_stack.items():
                print(f"  • {key}: {value}")
        
        if result.warnings:
            print(f"\n⚠️  Warnings:")
            for warning in result.warnings:
                print(f"  • {warning}")
        
        if result.errors:
            print(f"\n❌ Errors:")
            for error in result.errors:
                print(f"  • {error}")
        
        print("="*60)
    
    def save_state(self, path: Path):
        """Save the current state for recovery."""
        state_data = {
            "checkpoints": self.checkpoints,
            "state": self.state,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(path, 'w') as f:
            json.dump(state_data, f, indent=2)
        
        self.log(f"State saved to {path}")
    
    def load_state(self, path: Path):
        """Load state for recovery."""
        if path.exists():
            with open(path, 'r') as f:
                state_data = json.load(f)
            
            self.checkpoints = state_data.get("checkpoints", [])
            self.state = state_data.get("state", {})
            
            self.log(f"State loaded from {path}")
            return True
        
        return False
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current progress of the build."""
        return {
            "checkpoints_completed": len(self.checkpoints),
            "current_phase": self.checkpoints[-1]["name"] if self.checkpoints else "starting",
            "state": self.state
        }