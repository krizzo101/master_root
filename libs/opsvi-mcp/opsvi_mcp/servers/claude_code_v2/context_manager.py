"""
Context Management for Multi-Agent Claude Systems

Handles:
- Custom system prompt generation for specialized agents
- Context inheritance between parent and child processes
- Session management and conversation continuity
- Task-specific agent specialization
"""

import json
import uuid
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class AgentContext:
    """Context information for an agent"""
    job_id: str
    parent_id: Optional[str] = None
    session_id: Optional[str] = None
    parent_session_id: Optional[str] = None
    task: str = ""
    role: str = "general"  # general, analyzer, debugger, documenter, etc.
    system_prompt_additions: List[str] = field(default_factory=list)
    inherited_context: Dict[str, Any] = field(default_factory=dict)
    results_from_siblings: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class SystemPromptGenerator:
    """Generates tailored system prompts for specialized agents"""
    
    # Role-specific prompt templates
    ROLE_PROMPTS = {
        "general": "",  # No additions for general agents
        
        "analyzer": """You are a code analysis specialist. Focus on:
- Understanding code structure and patterns
- Identifying potential issues and improvements
- Providing detailed technical analysis
- Documenting your findings clearly""",
        
        "debugger": """You are a debugging expert. Your priorities:
- Identify root causes of issues
- Provide clear explanations of problems
- Suggest specific fixes with code examples
- Test your solutions thoroughly""",
        
        "optimizer": """You are a performance optimization specialist. Focus on:
- Identifying performance bottlenecks
- Suggesting efficient algorithms and data structures
- Reducing time and space complexity
- Measuring and proving improvements""",
        
        "documenter": """You are a documentation expert. Ensure:
- Clear and comprehensive documentation
- Code examples and usage guides
- API references with type hints
- Best practices and common pitfalls""",
        
        "tester": """You are a testing specialist. Focus on:
- Writing comprehensive test cases
- Edge cases and error conditions
- Test coverage and quality metrics
- Both unit and integration testing""",
        
        "reviewer": """You are a code review expert. Evaluate:
- Code quality and maintainability
- Security vulnerabilities
- Performance implications
- Adherence to best practices""",
        
        "architect": """You are a system architect. Consider:
- System design and scalability
- Component interactions and dependencies
- Design patterns and architectural principles
- Future extensibility and maintenance""",
        
        "security": """You are a security specialist. Focus on:
- Identifying security vulnerabilities
- Implementing secure coding practices
- Data protection and encryption
- Authentication and authorization""",
    }
    
    @classmethod
    def generate_system_prompt(cls, context: AgentContext) -> str:
        """Generate a custom system prompt based on agent context"""
        
        prompt_parts = []
        
        # Add role-specific prompt
        if context.role in cls.ROLE_PROMPTS:
            role_prompt = cls.ROLE_PROMPTS[context.role]
            if role_prompt:
                prompt_parts.append(role_prompt)
        
        # Add task-specific context
        if context.task:
            task_prompt = cls._generate_task_prompt(context.task)
            if task_prompt:
                prompt_parts.append(task_prompt)
        
        # Add inherited context summary
        if context.inherited_context:
            context_prompt = cls._generate_context_prompt(context.inherited_context)
            if context_prompt:
                prompt_parts.append(context_prompt)
        
        # Add sibling results summary
        if context.results_from_siblings:
            sibling_prompt = cls._generate_sibling_prompt(context.results_from_siblings)
            if sibling_prompt:
                prompt_parts.append(sibling_prompt)
        
        # Add any custom additions
        prompt_parts.extend(context.system_prompt_additions)
        
        # Combine all parts
        return "\n\n".join(prompt_parts)
    
    @classmethod
    def _generate_task_prompt(cls, task: str) -> str:
        """Generate task-specific prompt additions"""
        
        task_lower = task.lower()
        prompts = []
        
        # Git-related tasks
        if any(word in task_lower for word in ["git", "commit", "merge", "branch"]):
            prompts.append("Follow Git best practices: atomic commits, clear messages, branch hygiene.")
        
        # Testing tasks
        if any(word in task_lower for word in ["test", "pytest", "unittest"]):
            prompts.append("Ensure comprehensive test coverage, including edge cases.")
        
        # Performance tasks
        if any(word in task_lower for word in ["optimize", "performance", "speed", "efficiency"]):
            prompts.append("Measure performance before and after changes. Provide metrics.")
        
        # Documentation tasks
        if any(word in task_lower for word in ["document", "readme", "docstring"]):
            prompts.append("Write clear, example-driven documentation suitable for the target audience.")
        
        # Security tasks
        if any(word in task_lower for word in ["security", "vulnerability", "auth", "encryption"]):
            prompts.append("Apply security best practices and consider OWASP guidelines.")
        
        return "\n".join(prompts) if prompts else ""
    
    @classmethod
    def _generate_context_prompt(cls, inherited_context: Dict[str, Any]) -> str:
        """Generate prompt based on inherited context"""
        
        prompts = []
        
        if "previous_errors" in inherited_context:
            prompts.append(f"Previous attempts encountered these errors: {inherited_context['previous_errors']}. Avoid these issues.")
        
        if "constraints" in inherited_context:
            prompts.append(f"Work within these constraints: {inherited_context['constraints']}")
        
        if "goals" in inherited_context:
            prompts.append(f"Primary goals: {inherited_context['goals']}")
        
        if "style_guide" in inherited_context:
            prompts.append(f"Follow this style guide: {inherited_context['style_guide']}")
        
        return "\n".join(prompts) if prompts else ""
    
    @classmethod
    def _generate_sibling_prompt(cls, sibling_results: List[Dict[str, Any]]) -> str:
        """Generate prompt based on sibling agent results"""
        
        if not sibling_results:
            return ""
        
        summary = "Previous agents in this workflow have completed:\n"
        for result in sibling_results[:3]:  # Limit to avoid token overflow
            agent_id = result.get("agent_id", "Unknown")
            task = result.get("task", "Unknown task")
            status = result.get("status", "Unknown")
            summary += f"- Agent {agent_id}: {task[:50]}... (Status: {status})\n"
        
        summary += "\nBuild upon their work and avoid duplicating efforts."
        return summary


class SessionManager:
    """Manages Claude session IDs and conversation continuity"""
    
    def __init__(self, base_dir: str = "/tmp/claude_sessions"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.session_registry = self._load_registry()
    
    def _load_registry(self) -> Dict[str, Any]:
        """Load session registry from disk"""
        registry_path = self.base_dir / "session_registry.json"
        if registry_path.exists():
            with open(registry_path, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_registry(self):
        """Save session registry to disk"""
        registry_path = self.base_dir / "session_registry.json"
        with open(registry_path, 'w') as f:
            json.dump(self.session_registry, f, indent=2)
    
    def create_session(self, job_id: str, parent_session: Optional[str] = None) -> str:
        """Create a new session ID (valid UUID)"""
        
        # Generate valid UUID
        session_id = str(uuid.uuid4())
        
        # Register session
        self.session_registry[session_id] = {
            "job_id": job_id,
            "created_at": datetime.now().isoformat(),
            "parent_session": parent_session,
            "status": "active"
        }
        
        self._save_registry()
        logger.info(f"Created session {session_id} for job {job_id}")
        
        return session_id
    
    def get_resume_command(self, parent_session: str) -> Optional[str]:
        """Get the command to resume a parent session"""
        
        if parent_session in self.session_registry:
            # Can't use same session ID (will error "already in use")
            # Must use --resume with parent session
            return f"--resume {parent_session}"
        return None
    
    def mark_session_complete(self, session_id: str):
        """Mark a session as complete"""
        if session_id in self.session_registry:
            self.session_registry[session_id]["status"] = "complete"
            self.session_registry[session_id]["completed_at"] = datetime.now().isoformat()
            self._save_registry()


class ContextInheritanceManager:
    """Manages context inheritance between parent and child agents"""
    
    def __init__(self):
        self.context_store = {}
    
    def save_parent_context(self, job_id: str, context: Dict[str, Any]):
        """Save parent context for children to inherit"""
        
        context_file = f"/tmp/agent_context_{job_id}.json"
        with open(context_file, 'w') as f:
            json.dump(context, f, indent=2)
        
        self.context_store[job_id] = context
        logger.info(f"Saved context for {job_id}")
    
    def load_parent_context(self, parent_id: str) -> Dict[str, Any]:
        """Load context from parent"""
        
        # Try memory first
        if parent_id in self.context_store:
            return self.context_store[parent_id]
        
        # Try disk
        context_file = f"/tmp/agent_context_{parent_id}.json"
        if os.path.exists(context_file):
            with open(context_file, 'r') as f:
                return json.load(f)
        
        return {}
    
    def build_child_context(
        self,
        job_id: str,
        task: str,
        parent_id: Optional[str] = None,
        role: str = "general",
        custom_prompts: Optional[List[str]] = None
    ) -> AgentContext:
        """Build complete context for a child agent"""
        
        context = AgentContext(
            job_id=job_id,
            parent_id=parent_id,
            task=task,
            role=role,
            system_prompt_additions=custom_prompts or []
        )
        
        # Inherit from parent if available
        if parent_id:
            parent_context = self.load_parent_context(parent_id)
            context.inherited_context = parent_context
            context.parent_session_id = parent_context.get("session_id")
        
        return context


class AgentSpecializer:
    """Determines agent specialization based on task analysis"""
    
    @staticmethod
    def determine_role(task: str) -> str:
        """Determine the best role for an agent based on the task"""
        
        task_lower = task.lower()
        
        # Pattern matching for role determination
        if any(word in task_lower for word in ["analyze", "review", "examine", "inspect"]):
            return "analyzer"
        elif any(word in task_lower for word in ["debug", "fix", "error", "bug", "issue"]):
            return "debugger"
        elif any(word in task_lower for word in ["optimize", "performance", "speed", "efficiency"]):
            return "optimizer"
        elif any(word in task_lower for word in ["document", "readme", "docstring", "comment"]):
            return "documenter"
        elif any(word in task_lower for word in ["test", "pytest", "unittest", "coverage"]):
            return "tester"
        elif any(word in task_lower for word in ["review", "audit", "quality", "standards"]):
            return "reviewer"
        elif any(word in task_lower for word in ["design", "architect", "structure", "pattern"]):
            return "architect"
        elif any(word in task_lower for word in ["security", "vulnerability", "auth", "encrypt"]):
            return "security"
        else:
            return "general"


# Example usage
def prepare_specialized_agent(
    job_id: str,
    task: str,
    parent_id: Optional[str] = None,
    inherit_session: bool = False
) -> Dict[str, Any]:
    """Prepare a specialized agent with appropriate context and prompts"""
    
    # Initialize managers
    session_mgr = SessionManager()
    context_mgr = ContextInheritanceManager()
    
    # Determine agent role
    role = AgentSpecializer.determine_role(task)
    
    # Build context
    context = context_mgr.build_child_context(
        job_id=job_id,
        task=task,
        parent_id=parent_id,
        role=role
    )
    
    # Create or inherit session
    if inherit_session and context.parent_session_id:
        # Can't reuse same session ID, must use --resume
        context.session_id = session_mgr.create_session(job_id, context.parent_session_id)
        resume_cmd = session_mgr.get_resume_command(context.parent_session_id)
    else:
        context.session_id = session_mgr.create_session(job_id)
        resume_cmd = None
    
    # Generate system prompt
    system_prompt = SystemPromptGenerator.generate_system_prompt(context)
    
    return {
        "job_id": job_id,
        "session_id": context.session_id,
        "role": role,
        "system_prompt": system_prompt,
        "resume_command": resume_cmd,
        "parent_context": context.inherited_context,
        "command_args": {
            "--session-id": context.session_id,
            "--append-system-prompt": f'"{system_prompt}"' if system_prompt else None,
            "--resume": context.parent_session_id if inherit_session and context.parent_session_id else None,
        }
    }


if __name__ == "__main__":
    # Test example
    config = prepare_specialized_agent(
        job_id="test-job-123",
        task="Debug the authentication error and fix the security vulnerability",
        parent_id="parent-job-456",
        inherit_session=True
    )
    
    print(json.dumps(config, indent=2))