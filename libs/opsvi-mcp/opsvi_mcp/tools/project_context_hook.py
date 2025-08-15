#!/usr/bin/env python3
"""
Project Context Hook - Automatically injects monorepo standards and SDLC requirements
Triggers on project-related commands to ensure agents follow established patterns
"""

import re
from typing import Dict, Any, Optional

class ProjectContextHook:
    """
    Automatically enriches simple project commands with full context.
    
    When user says: "build a payment service"
    Hook injects: All SDLC requirements, monorepo standards, resource discovery, etc.
    """
    
    # Patterns that trigger context injection
    TRIGGER_PATTERNS = [
        r'\b(build|create|implement|develop|make|start|design|add)\b.*\b(app|service|api|system|feature|component|module|project)\b',
        r'\b(new|another)\s+(app|service|api|system|feature|component|module|project)\b',
        r'\b(need|want|require)\s+.*\b(app|service|api|system|feature|component|module)\b',
        r'^(build|create|implement|develop|make)\s+',
    ]
    
    @classmethod
    def should_inject_context(cls, user_message: str) -> bool:
        """Check if message should trigger context injection."""
        message_lower = user_message.lower()
        return any(re.search(pattern, message_lower) for pattern in cls.TRIGGER_PATTERNS)
    
    @classmethod
    def inject_context(cls, user_message: str) -> str:
        """
        Inject full project context into simple user message.
        
        Args:
            user_message: Original user message
            
        Returns:
            Enhanced message with full context
        """
        if not cls.should_inject_context(user_message):
            return user_message
        
        context_injection = """
[SYSTEM CONTEXT INJECTION - MANDATORY REQUIREMENTS]

BEFORE PROCEEDING WITH THIS REQUEST, YOU MUST:

1. MANDATORY READING (if not already read this session):
   - /home/opsvi/master_root/CLAUDE.md (behavioral directives)
   - /docs/guidelines/AGENT_SDLC_GUIDELINES.md (SDLC phases)
   - /docs/standards/MONOREPO_PROJECT_STANDARDS.md (structure)
   - /docs/standards/AGENT_INVOCATION_STANDARDS.md (Claude Code first)

2. KNOWLEDGE SYSTEM CHECK:
   - Query for existing solutions: knowledge_query("search", "[relevant terms]")
   - Check for similar patterns already implemented
   - Store new patterns after successful implementation

3. RESOURCE DISCOVERY:
   - Run resource_discovery.py to find existing components in libs/
   - DO NOT reinvent existing functionality
   - Create new shared resources in libs/ for reusable components

4. SDLC ENFORCEMENT (MANDATORY PHASES):
   ✓ DISCOVERY: Research current tech (web_search, tech_docs)
   ✓ DESIGN: Architecture before code
   ✓ PLANNING: Break down tasks, define tests
   ✓ DEVELOPMENT: Only after above phases
   ✓ TESTING: Comprehensive tests required
   ✓ DEPLOYMENT: Monitoring and rollback plans
   ✓ PRODUCTION: Verify readiness

5. PROJECT STRUCTURE:
   - Shared/reusable → libs/opsvi-<name>/
   - Applications → apps/<app-name>/
   - Use project_initializer.py for scaffolding
   - Over-modularize by default (many small modules)
   - Centralized configuration
   - Comprehensive logging

6. AGENT STRATEGY:
   - You are Claude Code - handle everything yourself
   - Don't orchestrate other agents (95% of tasks)
   - Only use specialized agents for: batch >1000, realtime <1s, domain-specific

7. DEVELOPMENT STANDARDS:
   - Module execution: python -m <module>
   - Test coverage: >80% required
   - Documentation: README, API docs, inline
   - Git commits: Frequent, after each logical unit
   - Current tech: Research 2025 best practices

[END SYSTEM CONTEXT]

USER REQUEST: """ + user_message
        
        return context_injection
    
    @classmethod
    def get_quick_reminders(cls) -> str:
        """Get quick reminder checklist for ongoing work."""
        return """
[QUICK REMINDERS]
□ Checked knowledge system?
□ Searched libs/ for existing resources?
□ Following SDLC phases?
□ Researched current tech?
□ Tests written?
□ Documentation updated?
□ Ready to commit?
"""


# MCP Hook Registration
def register_hook():
    """Register this hook with the MCP system."""
    return {
        "name": "project_context_hook",
        "type": "pre_request",
        "triggers": ProjectContextHook.TRIGGER_PATTERNS,
        "handler": ProjectContextHook.inject_context,
        "priority": 100,  # High priority to run first
        "description": "Injects project standards and SDLC requirements into project-related requests"
    }