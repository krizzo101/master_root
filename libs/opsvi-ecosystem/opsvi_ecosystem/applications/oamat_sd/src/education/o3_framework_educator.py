"""
O3 Framework Educator

Provides O3 with comprehensive framework knowledge for dynamic generation.
Extracted from o3_master_agent.py for better modularity.
"""

from typing import Any


class O3FrameworkEducator:
    """Provides O3 with comprehensive framework knowledge for dynamic generation"""

    @staticmethod
    def get_tool_catalog() -> dict[str, dict[str, str]]:
        """Complete catalog of available MCP tools with capabilities"""
        return {
            "write_file": {
                "capability": "Create and edit files with any content type",
                "parameters": "target_file, code_edit, instructions",
                "use_cases": "Source code, configuration files, documentation, templates",
                "output_types": "Any file format (.py, .js, .tsx, .json, .md, .txt, etc.)",
            },
            "mcp_shell_exec": {
                "capability": "Execute shell commands and scripts with output capture",
                "parameters": "command, workingDir",
                "use_cases": "Package installation, compilation, testing, deployment, file operations",
                "security": "Commands run in controlled environment",
            },
            "read_file": {
                "capability": "Read file contents with line range support",
                "parameters": "target_file, start_line_one_indexed, end_line_one_indexed",
                "use_cases": "Code analysis, template reading, configuration inspection",
                "output": "File contents with context",
            },
            "edit_file": {
                "capability": "Precise file editing with structured changes",
                "parameters": "target_file, instructions, code_edit",
                "use_cases": "Code modification, configuration updates, targeted fixes",
                "features": "Surgical edits, preserve existing code",
            },
            "search_replace": {
                "capability": "Exact text replacement in files",
                "parameters": "file_path, old_string, new_string",
                "use_cases": "Targeted code changes, configuration updates",
                "features": "Precise replacement, maintains file structure",
            },
            "list_dir": {
                "capability": "Directory listing with detailed file information",
                "parameters": "relative_workspace_path",
                "use_cases": "Project structure analysis, file discovery",
                "output": "Comprehensive directory information",
            },
            "codebase_search": {
                "capability": "Semantic code search and analysis",
                "parameters": "query, target_directories, explanation",
                "use_cases": "Understanding code patterns, finding implementations",
                "intelligence": "Semantic understanding, not just text matching",
            },
            "grep_search": {
                "capability": "Fast regex-based text search",
                "parameters": "query, include_pattern, exclude_pattern",
                "use_cases": "Pattern matching, symbol finding, text location",
                "performance": "High-speed text search across large codebases",
            },
            "web_search": {
                "capability": "Research and information gathering",
                "parameters": "search_term",
                "use_cases": "Documentation lookup, best practices, troubleshooting",
                "knowledge": "Current information, community knowledge",
            },
        }

    @staticmethod
    def get_framework_architecture() -> dict[str, Any]:
        """LangGraph framework architecture knowledge for O3"""
        return {
            "langgraph_fundamentals": {
                "agent_creation": {
                    "pattern": "create_react_agent(model, tools, prompt)",
                    "requirements": "Model, tools list, prompt template",
                    "capabilities": "ReAct reasoning, tool usage, state management",
                    "integration": "Seamless with LangGraph workflows",
                },
                "state_management": {
                    "approach": "Typed state objects with Pydantic validation",
                    "flow": "State passed between agents, modified incrementally",
                    "persistence": "Automatic state persistence and recovery",
                    "validation": "Type safety and data integrity",
                },
                "coordination": {
                    "patterns": [
                        "sequential",
                        "parallel",
                        "conditional",
                        "hierarchical",
                    ],
                    "mechanisms": ["Send API", "message passing", "state sharing"],
                    "optimization": "Parallel execution where dependencies allow",
                },
            },
            "mcp_integration": {
                "tool_binding": {
                    "process": "Tools converted to LangChain tool format",
                    "parameters": "MCP tool parameters mapped to function signatures",
                    "execution": "Asynchronous tool execution with error handling",
                    "results": "Structured results returned to agent context",
                },
                "tool_categories": {
                    "file_operations": [
                        "write_file",
                        "read_file",
                        "edit_file",
                        "search_replace",
                    ],
                    "system_operations": ["mcp_shell_exec", "list_dir"],
                    "search_operations": [
                        "codebase_search",
                        "grep_search",
                        "web_search",
                    ],
                    "research_operations": ["web_search", "codebase_search"],
                },
                "tool_selection": {
                    "criteria": "Match tool capabilities to task requirements",
                    "optimization": "Prefer specialized tools over generic ones",
                    "combinations": "Chain tools for complex operations",
                },
            },
            "execution_patterns": {
                "simple": {
                    "description": "Single agent with minimal coordination",
                    "agent_count": 1,
                    "coordination": "None required",
                    "tools": "Basic set (read, write, search)",
                    "use_cases": "Simple implementations, single-file projects",
                },
                "multi_agent": {
                    "description": "Multiple specialized agents with coordination",
                    "agent_count": "2-4",
                    "coordination": "Sequential with handoffs",
                    "tools": "Specialized tool sets per agent",
                    "use_cases": "Complex projects, multiple deliverables",
                },
                "orchestrated": {
                    "description": "Complex workflow with sophisticated coordination",
                    "agent_count": "4+",
                    "coordination": "Mixed parallel and sequential",
                    "tools": "Full tool catalog access",
                    "use_cases": "Enterprise projects, system integration",
                },
            },
        }

    @staticmethod
    def get_prompt_engineering_guidelines() -> dict[str, Any]:
        """Guidelines for creating effective agent prompts"""
        return {
            "prompt_structure": {
                "system_role": {
                    "purpose": "Define agent expertise and behavior",
                    "pattern": "You are a [ROLE] specializing in [DOMAIN]",
                    "examples": [
                        "You are a Senior Software Architect specializing in distributed systems",
                        "You are a Full-Stack Developer with expertise in React and Node.js",
                        "You are a DevOps Engineer focused on containerization and CI/CD",
                    ],
                },
                "task_specification": {
                    "clarity": "Clear, specific task description",
                    "context": "Relevant background information",
                    "constraints": "Technical and business constraints",
                    "deliverables": "Specific output requirements",
                },
                "tool_guidance": {
                    "tool_awareness": "Agent knows available tools",
                    "tool_selection": "Guidance on when to use which tools",
                    "tool_chaining": "How to combine tools effectively",
                    "error_handling": "How to handle tool failures",
                },
            },
            "coordination_prompts": {
                "handoff_patterns": {
                    "context_transfer": "How to pass context to next agent",
                    "dependency_management": "Understanding task dependencies",
                    "quality_standards": "Maintaining consistency across agents",
                },
                "parallel_execution": {
                    "independence": "Ensuring parallel tasks don't conflict",
                    "synchronization": "Coordination points for parallel streams",
                    "resource_sharing": "Managing shared resources",
                },
            },
            "quality_patterns": {
                "validation": "How agents should validate their outputs",
                "error_recovery": "Strategies for handling failures",
                "optimization": "Performance and efficiency considerations",
                "documentation": "Self-documenting outputs and processes",
            },
        }

    @staticmethod
    def get_best_practices() -> dict[str, Any]:
        """Best practices for O3-generated workflows"""
        return {
            "dynamic_generation": {
                "principles": [
                    "Analyze request complexity before designing workflow",
                    "Match agent specialization to specific requirements",
                    "Optimize for parallel execution where possible",
                    "Design for failure recovery and error handling",
                ],
                "anti_patterns": [
                    "Using hardcoded workflow templates",
                    "Over-engineering simple requests",
                    "Ignoring dependency constraints",
                    "Creating agents without clear specialization",
                ],
            },
            "tool_usage": {
                "optimization": [
                    "Use most specific tool for each task",
                    "Chain tools efficiently for complex operations",
                    "Validate tool outputs before proceeding",
                    "Handle tool failures gracefully",
                ],
                "common_patterns": [
                    "read_file → analyze → edit_file (modification pattern)",
                    "codebase_search → read_file → write_file (implementation pattern)",
                    "web_search → research → write_file (documentation pattern)",
                ],
            },
            "quality_assurance": {
                "validation": [
                    "Validate all outputs against requirements",
                    "Ensure consistency across deliverables",
                    "Test generated code for functionality",
                    "Review documentation for accuracy",
                ],
                "monitoring": [
                    "Track agent performance and success rates",
                    "Monitor tool usage and efficiency",
                    "Identify bottlenecks and optimization opportunities",
                    "Maintain quality metrics and improvement feedback",
                ],
            },
        }

    @classmethod
    def get_comprehensive_framework_knowledge(cls) -> dict[str, Any]:
        """Complete framework knowledge package for O3 education"""
        return {
            "tool_catalog": cls.get_tool_catalog(),
            "framework_architecture": cls.get_framework_architecture(),
            "prompt_engineering": cls.get_prompt_engineering_guidelines(),
            "best_practices": cls.get_best_practices(),
            "integration_notes": {
                "o3_optimization": "O3 excels at understanding complex requirements and generating optimal workflows",
                "dynamic_adaptation": "Workflows should adapt to specific request characteristics",
                "context_management": "Maintain context flow throughout complex multi-agent workflows",
                "performance_focus": "Optimize for parallel execution and efficient tool usage",
            },
        }
