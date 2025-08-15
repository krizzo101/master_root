#!/usr/bin/env python3
"""
Research-Driven Autonomous Coder - Always researches before building

This bootstrap ensures Claude Code researches current technologies, 
packages, and best practices before and during implementation.
"""

import asyncio
import json
import subprocess
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid

class ResearchDrivenAutonomous:
    """
    Autonomous coder that researches current tech before building
    """
    
    def __init__(self, workspace: str = "./autonomous_workspace"):
        self.workspace = Path(workspace)
        self.workspace.mkdir(exist_ok=True)
        self.research_cache = self.workspace / "research_cache"
        self.research_cache.mkdir(exist_ok=True)
        self.session_id = str(uuid.uuid4())[:8]
        self.state_file = self.workspace / f"state_{self.session_id}.json"
        self.iteration = 0
        self.max_iterations = 100
        self.state = self.load_state()
        
    def load_state(self) -> Dict[str, Any]:
        """Load or initialize state"""
        if self.state_file.exists():
            with open(self.state_file) as f:
                return json.load(f)
        return {
            "goal": None,
            "completed": False,
            "current_task": None,
            "completed_tasks": [],
            "research_findings": {},
            "technology_decisions": {},
            "package_versions": {},
            "errors": [],
            "test_results": [],
            "files_created": []
        }
    
    def save_state(self):
        """Persist state to disk"""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def run_claude(self, prompt: str) -> str:
        """Execute Claude Code and return output"""
        cmd = [
            "claude",
            "--dangerously-skip-permissions",
            "-p", prompt
        ]
        
        print(f"\n[Iteration {self.iteration}] Executing task...")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.workspace,
                timeout=300
            )
            return result.stdout
        except Exception as e:
            return f"ERROR: {str(e)}"
    
    def research_phase(self, topic: str) -> Dict[str, Any]:
        """
        Research current information about a topic
        Uses web search, documentation lookup, and package registries
        """
        print(f"\n🔍 Researching: {topic}")
        
        research_prompt = f"""
        Research the current state of: {topic}
        
        Use web search and any available tools to find:
        1. Latest stable versions of relevant packages/frameworks
        2. Current best practices (2024-2025)
        3. Common pitfalls and solutions
        4. Security considerations
        5. Performance optimizations
        6. Alternative technologies to consider
        
        Focus on information from 2024-2025. Ignore outdated practices.
        
        Output as JSON with structure:
        {{
            "technologies": {{"name": "version/details"}},
            "best_practices": ["practice1", "practice2"],
            "warnings": ["warning1", "warning2"],
            "recommendations": ["rec1", "rec2"],
            "sources": ["url1", "url2"]
        }}
        
        IMPORTANT: Research actual current versions, don't use outdated knowledge.
        """
        
        result = self.run_claude(research_prompt)
        
        # Cache research findings
        cache_file = self.research_cache / f"{topic.replace(' ', '_')}.json"
        with open(cache_file, 'w') as f:
            f.write(result)
        
        try:
            findings = json.loads(result)
            self.state['research_findings'][topic] = findings
            return findings
        except:
            return {"raw_findings": result}
    
    def technology_decision_phase(self, requirements: str) -> Dict[str, str]:
        """
        Make technology decisions based on research
        """
        print(f"\n🎯 Making technology decisions based on research...")
        
        decision_prompt = f"""
        Based on the research findings: {json.dumps(self.state['research_findings'], indent=2)}
        
        And these requirements: {requirements}
        
        Make technology decisions for the implementation:
        1. Choose specific versions of packages to use
        2. Select frameworks and libraries
        3. Decide on architecture patterns
        4. Choose testing frameworks
        
        Output as JSON with structure:
        {{
            "frontend": {{"framework": "name", "version": "x.x.x", "packages": []}},
            "backend": {{"framework": "name", "version": "x.x.x", "packages": []}},
            "database": {{"type": "name", "version": "x.x.x"}},
            "testing": {{"framework": "name", "version": "x.x.x"}},
            "deployment": {{"platform": "name", "method": "details"}},
            "rationale": "explanation of choices"
        }}
        
        Use only technologies that exist in 2024-2025.
        """
        
        result = self.run_claude(decision_prompt)
        
        try:
            decisions = json.loads(result)
            self.state['technology_decisions'] = decisions
            return decisions
        except:
            return {"decisions": result}
    
    def verify_package_versions(self):
        """
        Verify that chosen package versions actually exist
        """
        print(f"\n✅ Verifying package versions...")
        
        verify_prompt = f"""
        Verify these package versions exist and are compatible:
        {json.dumps(self.state['technology_decisions'], indent=2)}
        
        For each package:
        1. Check if the version exists in the package registry
        2. Verify compatibility with other chosen packages
        3. Note any security advisories
        
        If any versions don't exist or have issues, suggest alternatives.
        
        Output the verified versions as JSON.
        """
        
        result = self.run_claude(verify_prompt)
        
        try:
            self.state['package_versions'] = json.loads(result)
        except:
            self.state['package_versions'] = {"verification": result}
    
    def implementation_with_research(self, task: str) -> str:
        """
        Implement a task using researched information
        """
        implementation_prompt = f"""
        Implement: {task}
        
        Use these verified technologies and versions:
        {json.dumps(self.state['technology_decisions'], indent=2)}
        
        Package versions to use:
        {json.dumps(self.state['package_versions'], indent=2)}
        
        Best practices to follow:
        {json.dumps(self.state['research_findings'].get('best_practices', []), indent=2)}
        
        Create production-ready code using current 2024-2025 standards.
        Include proper error handling, typing, and documentation.
        """
        
        return self.run_claude(implementation_prompt)
    
    def research_driven_loop(self, goal: str):
        """
        Main autonomous loop with mandatory research phases
        """
        print(f"\n🚀 Starting research-driven autonomous build: {goal}\n")
        self.state['goal'] = goal
        self.save_state()
        
        # Phase 1: Initial Research
        print("\n" + "="*50)
        print("PHASE 1: COMPREHENSIVE RESEARCH")
        print("="*50)
        
        # Research the domain
        domain_research = self.research_phase(goal)
        
        # Research specific technologies mentioned
        tech_keywords = self.extract_technologies(goal)
        for tech in tech_keywords:
            self.research_phase(tech)
        
        # Research current best practices
        self.research_phase("2024-2025 software development best practices")
        
        # Phase 2: Technology Decisions
        print("\n" + "="*50)
        print("PHASE 2: TECHNOLOGY SELECTION")
        print("="*50)
        
        self.technology_decision_phase(goal)
        self.verify_package_versions()
        
        # Phase 3: Implementation Planning
        print("\n" + "="*50)
        print("PHASE 3: IMPLEMENTATION PLANNING")
        print("="*50)
        
        plan_prompt = f"""
        Create a detailed implementation plan for: {goal}
        
        Using these researched technologies:
        {json.dumps(self.state['technology_decisions'], indent=2)}
        
        Break down into specific, testable tasks.
        Include research checkpoints for any uncertain areas.
        
        Output as JSON with structure:
        {{
            "phases": [
                {{
                    "name": "phase name",
                    "tasks": ["task1", "task2"],
                    "research_needed": ["topic1", "topic2"],
                    "validation": "how to test this phase"
                }}
            ]
        }}
        """
        
        plan_result = self.run_claude(plan_prompt)
        
        try:
            plan = json.loads(plan_result)
            self.state['implementation_plan'] = plan
        except:
            self.state['implementation_plan'] = {"phases": [{"name": "Build", "tasks": [goal]}]}
        
        # Phase 4: Iterative Implementation with Research
        print("\n" + "="*50)
        print("PHASE 4: IMPLEMENTATION WITH CONTINUOUS RESEARCH")
        print("="*50)
        
        for phase in self.state['implementation_plan'].get('phases', []):
            print(f"\n📍 Phase: {phase.get('name', 'Implementation')}")
            
            # Research any needed topics for this phase
            for research_topic in phase.get('research_needed', []):
                self.research_phase(research_topic)
            
            # Implement each task in the phase
            for task in phase.get('tasks', []):
                self.iteration += 1
                
                if self.iteration >= self.max_iterations:
                    print("\n⚠️ Reached maximum iterations")
                    break
                
                print(f"\n[Task {self.iteration}] {task}")
                
                # Check if we need to research anything specific for this task
                if any(keyword in task.lower() for keyword in ['api', 'library', 'framework', 'package']):
                    self.research_phase(f"Current implementation of {task}")
                
                # Implement with research context
                result = self.implementation_with_research(task)
                
                self.state['completed_tasks'].append({
                    'iteration': self.iteration,
                    'task': task,
                    'result': result[:500]
                })
                
                # Test what we built
                if phase.get('validation'):
                    self.test_with_current_standards(phase['validation'])
                
                self.save_state()
        
        # Phase 5: Final Validation and Documentation
        print("\n" + "="*50)
        print("PHASE 5: VALIDATION AND DOCUMENTATION")
        print("="*50)
        
        self.final_validation()
        self.generate_documentation()
    
    def extract_technologies(self, text: str) -> List[str]:
        """Extract technology names from goal for research"""
        # Common technology keywords to research
        keywords = []
        tech_terms = [
            'react', 'vue', 'angular', 'nextjs', 'next.js',
            'node', 'nodejs', 'express', 'fastapi', 'django', 'flask',
            'postgresql', 'mysql', 'mongodb', 'redis',
            'docker', 'kubernetes', 'aws', 'gcp', 'azure',
            'typescript', 'javascript', 'python', 'go', 'rust',
            'graphql', 'rest', 'api', 'websocket',
            'tailwind', 'css', 'sass', 'styled-components'
        ]
        
        text_lower = text.lower()
        for term in tech_terms:
            if term in text_lower:
                keywords.append(term)
        
        return keywords
    
    def test_with_current_standards(self, validation_approach: str):
        """Test using current testing standards"""
        test_prompt = f"""
        Test the implementation using: {validation_approach}
        
        Use current 2024-2025 testing practices:
        - Modern testing frameworks from our research
        - Current assertion libraries
        - Latest mocking approaches
        
        Fix any issues found.
        """
        
        result = self.run_claude(test_prompt)
        self.state['test_results'].append({
            'iteration': self.iteration,
            'result': result[:500]
        })
    
    def final_validation(self):
        """Final validation using current standards"""
        validation_prompt = f"""
        Perform final validation of the implementation:
        
        1. Verify all packages are current versions (2024-2025)
        2. Check security best practices are followed
        3. Ensure performance optimizations are applied
        4. Validate accessibility standards
        5. Check mobile responsiveness (if applicable)
        6. Verify error handling and logging
        
        Fix any issues found.
        """
        
        self.run_claude(validation_prompt)
    
    def generate_documentation(self):
        """Generate documentation with current information"""
        doc_prompt = f"""
        Generate comprehensive documentation including:
        
        1. Technologies used (with specific versions):
        {json.dumps(self.state['technology_decisions'], indent=2)}
        
        2. Setup instructions for 2024-2025 environments
        3. Current deployment best practices
        4. Security considerations
        5. Performance notes
        6. Links to current documentation for all technologies used
        
        Create README.md and other necessary docs.
        """
        
        self.run_claude(doc_prompt)
        
        # Save summary
        summary_file = self.workspace / f"BUILD_SUMMARY_{self.session_id}.md"
        with open(summary_file, 'w') as f:
            f.write(f"# Research-Driven Build Summary\n\n")
            f.write(f"**Goal:** {self.state['goal']}\n\n")
            f.write(f"**Session:** {self.session_id}\n\n")
            f.write(f"**Iterations:** {self.iteration}\n\n")
            f.write(f"## Research Findings\n\n")
            f.write(f"```json\n{json.dumps(self.state['research_findings'], indent=2)}\n```\n\n")
            f.write(f"## Technology Decisions\n\n")
            f.write(f"```json\n{json.dumps(self.state['technology_decisions'], indent=2)}\n```\n\n")
            f.write(f"## Completed Tasks\n\n")
            for task in self.state['completed_tasks']:
                f.write(f"- [{task['iteration']}] {task['task']}\n")
        
        print(f"\n📄 Summary saved to: {summary_file}")

def main():
    """
    Bootstrap the research-driven autonomous coder
    """
    print("""
    🔬 Research-Driven Autonomous Coder
    ====================================
    This system researches current technologies before building.
    """)
    
    # The bootstrap goal with research requirements
    RESEARCH_DRIVEN_GOAL = """
    Build a modern web application using current 2024-2025 best practices.
    
    Requirements:
    1. Research and use the latest stable versions of all packages
    2. Implement current security best practices
    3. Use modern performance optimization techniques
    4. Follow current accessibility standards
    5. Implement with proper error handling and monitoring
    
    The app should be a task management system with:
    - User authentication
    - Real-time updates
    - Mobile responsive design
    - API backend
    - Database persistence
    
    Research everything first, make informed decisions, then build.
    """
    
    # Allow custom goal
    if len(sys.argv) > 1:
        goal = " ".join(sys.argv[1:])
    else:
        goal = RESEARCH_DRIVEN_GOAL
    
    # Create research-driven instance
    autonomous = ResearchDrivenAutonomous()
    
    # Run research-driven build
    autonomous.research_driven_loop(goal)
    
    print("\n✨ Research-driven build complete! Check the workspace for results.")

if __name__ == "__main__":
    main()