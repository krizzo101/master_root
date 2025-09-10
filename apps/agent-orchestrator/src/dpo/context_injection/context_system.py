#!/usr/bin/env python3
"""
Context Injection System
Provides agents with relevant ecosystem knowledge without overwhelming them
"""

import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class ToolCapability:
    """Represents a discovered tool/application capability"""

    name: str
    path: str
    type: str  # app, library, tool, integration
    description: str
    capabilities: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    api_endpoints: List[str] = field(default_factory=list)
    integration_points: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    best_practices: List[str] = field(default_factory=list)


@dataclass
class AgentContext:
    """Context package for an agent"""

    core_identity: str
    task_context: Dict[str, Any]
    available_tools: List[ToolCapability]
    integration_opportunities: List[str]
    performance_targets: Dict[str, Any]
    reusable_components: List[Dict[str, str]]
    best_practices: List[str]
    constraints: List[str]

    def to_prompt_enhancement(self) -> str:
        """Convert context to prompt enhancement text"""
        sections = []

        # Core identity
        sections.append(f"ECOSYSTEM CONTEXT:\n{self.core_identity}")

        # Task-specific context
        if self.task_context:
            sections.append(
                f"\nTASK CONTEXT:\n{json.dumps(self.task_context, indent=2)}"
            )

        # Available tools
        if self.available_tools:
            tool_list = []
            for tool in self.available_tools[:5]:  # Limit to top 5 most relevant
                tool_list.append(f"- {tool.name} ({tool.type}): {tool.description}")
                if tool.capabilities:
                    tool_list.append(
                        f"  Capabilities: {', '.join(tool.capabilities[:3])}"
                    )
            sections.append(f"\nAVAILABLE TOOLS:\n" + "\n".join(tool_list))

        # Integration opportunities
        if self.integration_opportunities:
            sections.append(
                f"\nINTEGRATION OPPORTUNITIES:\n"
                + "\n".join(f"- {opp}" for opp in self.integration_opportunities[:3])
            )

        # Performance targets
        if self.performance_targets:
            sections.append(
                f"\nPERFORMANCE TARGETS:\n"
                + "\n".join(f"- {k}: {v}" for k, v in self.performance_targets.items())
            )

        # Best practices
        if self.best_practices:
            sections.append(
                f"\nBEST PRACTICES:\n"
                + "\n".join(f"- {bp}" for bp in self.best_practices[:3])
            )

        return "\n".join(sections)


class EcosystemDiscovery:
    """Discovers and catalogs ecosystem capabilities"""

    def __init__(self, master_root: str = "/home/opsvi/master_root"):
        self.master_root = Path(master_root)
        self.capabilities_cache: Dict[str, ToolCapability] = {}
        self.last_scan: Optional[datetime] = None

    def scan_ecosystem(self, force_refresh: bool = False) -> Dict[str, ToolCapability]:
        """Scan the ecosystem for available tools and capabilities"""

        # Use cache if available and recent
        if not force_refresh and self.capabilities_cache and self.last_scan:
            cache_age = (datetime.now() - self.last_scan).seconds
            if cache_age < 3600:  # Cache for 1 hour
                return self.capabilities_cache

        logger.info("Scanning ecosystem for capabilities...")
        capabilities = {}

        # Scan apps directory
        apps_dir = self.master_root / "apps"
        if apps_dir.exists():
            for app_path in apps_dir.iterdir():
                if app_path.is_dir() and not app_path.name.startswith("."):
                    capability = self._analyze_application(app_path)
                    if capability:
                        capabilities[capability.name] = capability

        # Scan libraries
        lib_patterns = ["**/lib", "**/libs", "**/libraries", "**/packages"]
        for pattern in lib_patterns:
            for lib_path in self.master_root.glob(pattern):
                if lib_path.is_dir():
                    libs = self._scan_libraries(lib_path)
                    capabilities.update(libs)

        # Scan integration points
        integration_capabilities = self._discover_integrations()
        capabilities.update(integration_capabilities)

        self.capabilities_cache = capabilities
        self.last_scan = datetime.now()

        logger.info(f"Discovered {len(capabilities)} capabilities")
        return capabilities

    def _analyze_application(self, app_path: Path) -> Optional[ToolCapability]:
        """Analyze an application directory for capabilities"""

        cap = ToolCapability(
            name=app_path.name,
            path=str(app_path),
            type="app",
            description="",
            capabilities=[],
            api_endpoints=[],
            integration_points=[],
        )

        # Check for README or documentation
        for doc_file in ["README.md", "readme.md", "README.txt", "docs/README.md"]:
            doc_path = app_path / doc_file
            if doc_path.exists():
                try:
                    content = doc_path.read_text()[:500]  # First 500 chars
                    # Extract description from first paragraph
                    lines = content.split("\n")
                    for line in lines:
                        if line.strip() and not line.startswith("#"):
                            cap.description = line.strip()[:200]
                            break
                except:
                    pass

        # Detect capabilities based on file patterns
        patterns = {
            "api": ["api.py", "server.py", "app.py", "main.py"],
            "cli": ["cli.py", "__main__.py", "run.py"],
            "orchestrator": ["orchestrator.py", "orchestrate.py"],
            "monitoring": ["monitor.py", "metrics.py", "dashboard.py"],
            "database": ["database.py", "db.py", "models.py"],
            "ml": ["model.py", "train.py", "predict.py"],
            "websocket": ["websocket.py", "ws.py", "realtime.py"],
        }

        for capability, file_patterns in patterns.items():
            for pattern in file_patterns:
                if list(app_path.rglob(pattern)):
                    cap.capabilities.append(capability)
                    break

        # Detect API endpoints
        api_files = list(app_path.rglob("*api*.py")) + list(
            app_path.rglob("*server*.py")
        )
        for api_file in api_files[:3]:  # Limit scanning
            try:
                content = api_file.read_text()
                # Simple regex to find route definitions
                routes = re.findall(r'@.*route\(["\']([^"\']+)', content)
                routes.extend(re.findall(r'app\.\w+\(["\']([^"\']+)', content))
                cap.api_endpoints.extend(routes[:5])  # Limit endpoints
            except:
                pass

        # Detect performance characteristics
        if "async" in str(app_path) or list(app_path.rglob("*async*.py")):
            cap.performance_metrics["async"] = True

        if list(app_path.rglob("*parallel*.py")) or list(
            app_path.rglob("*concurrent*.py")
        ):
            cap.performance_metrics["parallel"] = True

        # Detect dependencies
        requirements = app_path / "requirements.txt"
        if requirements.exists():
            try:
                deps = requirements.read_text().split("\n")
                cap.dependencies = [
                    d.split("==")[0].strip() for d in deps if d.strip()
                ][:5]
            except:
                pass

        return cap if cap.capabilities else None

    def _scan_libraries(self, lib_path: Path) -> Dict[str, ToolCapability]:
        """Scan a libraries directory"""
        libs = {}

        for item in lib_path.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                cap = ToolCapability(
                    name=f"lib_{item.name}",
                    path=str(item),
                    type="library",
                    description=f"Reusable library: {item.name}",
                    capabilities=["reusable", "importable"],
                )

                # Check for Python modules
                if list(item.glob("*.py")):
                    cap.capabilities.append("python_module")

                libs[cap.name] = cap

        return libs

    def _discover_integrations(self) -> Dict[str, ToolCapability]:
        """Discover integration points in the ecosystem"""
        integrations = {}

        # Look for MCP configurations
        mcp_configs = list(self.master_root.rglob(".mcp.json"))
        for config_path in mcp_configs:
            try:
                config = json.loads(config_path.read_text())
                if "servers" in config:
                    for server_name, server_config in config.get("servers", {}).items():
                        cap = ToolCapability(
                            name=f"mcp_{server_name}",
                            path=str(config_path.parent),
                            type="integration",
                            description=f"MCP Server: {server_name}",
                            capabilities=["mcp_integration"],
                            integration_points=[f"mcp://{server_name}"],
                        )
                        integrations[cap.name] = cap
            except:
                pass

        # Look for Docker configurations
        docker_files = list(self.master_root.rglob("docker-compose*.yml"))
        for docker_file in docker_files:
            cap = ToolCapability(
                name=f"docker_{docker_file.parent.name}",
                path=str(docker_file),
                type="integration",
                description="Docker service configuration",
                capabilities=["containerized"],
                integration_points=["docker"],
            )
            integrations[cap.name] = cap

        return integrations


class ContextFilter:
    """Filters and targets context based on agent type and task"""

    def __init__(self):
        self.agent_type_mappings = {
            "documentation": ["app", "library", "integration"],
            "development": ["app", "library", "tool"],
            "integration": ["integration", "app"],
            "monitoring": ["app", "tool"],
            "analysis": ["app", "library", "tool", "integration"],
            "orchestration": ["app", "tool", "integration"],
        }

        self.task_keyword_mappings = {
            "api": ["api", "server", "endpoint", "rest", "graphql"],
            "database": ["database", "db", "sql", "nosql", "orm"],
            "frontend": ["ui", "frontend", "react", "vue", "html"],
            "backend": ["backend", "server", "api", "service"],
            "ml": ["ml", "ai", "model", "training", "prediction"],
            "monitoring": ["monitor", "metrics", "dashboard", "logging"],
            "testing": ["test", "qa", "validation", "quality"],
        }

    def filter_for_agent(
        self,
        agent_type: str,
        task_description: str,
        all_capabilities: Dict[str, ToolCapability],
        max_tools: int = 10,
    ) -> List[ToolCapability]:
        """Filter capabilities relevant to specific agent and task"""

        relevant_tools = []

        # Get tool types relevant to agent
        relevant_types = self.agent_type_mappings.get(
            agent_type.lower(), ["app", "library", "tool"]
        )

        # Extract keywords from task description
        task_keywords = set()
        task_lower = task_description.lower()
        for category, keywords in self.task_keyword_mappings.items():
            if any(kw in task_lower for kw in keywords):
                task_keywords.update(keywords)

        # Score and filter capabilities
        scored_capabilities = []
        for name, cap in all_capabilities.items():
            score = 0

            # Type relevance
            if cap.type in relevant_types:
                score += 10

            # Keyword relevance
            cap_text = (
                f"{cap.name} {cap.description} {' '.join(cap.capabilities)}".lower()
            )
            for keyword in task_keywords:
                if keyword in cap_text:
                    score += 5

            # API endpoint relevance
            if "api" in task_keywords and cap.api_endpoints:
                score += 8

            # Performance characteristics
            if cap.performance_metrics:
                score += 3

            if score > 0:
                scored_capabilities.append((score, cap))

        # Sort by score and return top N
        scored_capabilities.sort(key=lambda x: x[0], reverse=True)
        relevant_tools = [cap for _, cap in scored_capabilities[:max_tools]]

        return relevant_tools

    def identify_integration_opportunities(
        self,
        task_tools: List[ToolCapability],
        all_capabilities: Dict[str, ToolCapability],
    ) -> List[str]:
        """Identify integration opportunities between tools"""

        opportunities = []

        # Check for common dependencies
        all_deps = set()
        for tool in task_tools:
            all_deps.update(tool.dependencies)

        if all_deps:
            opportunities.append(
                f"Shared dependencies: {', '.join(list(all_deps)[:3])}"
            )

        # Check for API integrations
        api_tools = [t for t in task_tools if t.api_endpoints]
        if len(api_tools) > 1:
            opportunities.append(
                f"API integration possible between: {', '.join([t.name for t in api_tools[:3]])}"
            )

        # Check for MCP integrations
        mcp_tools = [t for t in task_tools if "mcp" in t.integration_points]
        if mcp_tools:
            opportunities.append(
                f"MCP integration available via: {', '.join([t.name for t in mcp_tools])}"
            )

        # Check for orchestration opportunities
        if len(task_tools) > 3:
            orchestrators = [
                name
                for name, cap in all_capabilities.items()
                if "orchestrator" in cap.capabilities
            ]
            if orchestrators:
                opportunities.append(f"Orchestration available via: {orchestrators[0]}")

        return opportunities


class DynamicContextGenerator:
    """Generates dynamic context based on real-time analysis"""

    def __init__(self, discovery: EcosystemDiscovery, filter: ContextFilter):
        self.discovery = discovery
        self.filter = filter

    def generate_context(
        self,
        agent_type: str,
        task_description: str,
        additional_context: Dict[str, Any] = None,
    ) -> AgentContext:
        """Generate complete context package for an agent"""

        # Core identity context (same for all agents)
        core_identity = """Mission: Solo developer AI-agent ecosystem for technical excellence
Focus: Speed, performance, capability amplification
Environment: Single PC, agent-to-agent collaboration
Constraints: No enterprise concerns, no security theater
Goal: Maximum capability with minimal complexity"""

        # Discover ecosystem capabilities
        all_capabilities = self.discovery.scan_ecosystem()

        # Filter relevant tools
        relevant_tools = self.filter.filter_for_agent(
            agent_type, task_description, all_capabilities
        )

        # Identify integration opportunities
        integration_opps = self.filter.identify_integration_opportunities(
            relevant_tools, all_capabilities
        )

        # Extract performance targets
        performance_targets = self._extract_performance_targets(agent_type)

        # Find reusable components
        reusable = self._find_reusable_components(relevant_tools)

        # Generate best practices
        best_practices = self._generate_best_practices(agent_type, relevant_tools)

        # Define constraints
        constraints = self._define_constraints(agent_type)

        # Build task context
        task_context = {
            "agent_type": agent_type,
            "task_description": task_description,
            "ecosystem_size": len(all_capabilities),
            "relevant_tools_count": len(relevant_tools),
        }

        if additional_context:
            task_context.update(additional_context)

        return AgentContext(
            core_identity=core_identity,
            task_context=task_context,
            available_tools=relevant_tools,
            integration_opportunities=integration_opps,
            performance_targets=performance_targets,
            reusable_components=reusable,
            best_practices=best_practices,
            constraints=constraints,
        )

    def _extract_performance_targets(self, agent_type: str) -> Dict[str, Any]:
        """Define performance targets based on agent type"""

        base_targets = {
            "response_time": "< 5 seconds",
            "memory_usage": "< 500MB",
            "parallel_execution": True,
        }

        type_specific = {
            "documentation": {"file_processing": "10+ files/second"},
            "development": {"code_generation": "100+ lines/minute"},
            "integration": {"api_latency": "< 100ms"},
            "monitoring": {"metric_collection": "1000+ metrics/second"},
            "analysis": {"data_processing": "1GB+ per minute"},
        }

        base_targets.update(type_specific.get(agent_type.lower(), {}))
        return base_targets

    def _find_reusable_components(
        self, tools: List[ToolCapability]
    ) -> List[Dict[str, str]]:
        """Identify reusable components from tools"""

        components = []

        for tool in tools:
            if tool.type == "library":
                components.append(
                    {"name": tool.name, "path": tool.path, "type": "library"}
                )
            elif tool.api_endpoints:
                components.append(
                    {
                        "name": f"{tool.name}_api",
                        "endpoints": ", ".join(tool.api_endpoints[:3]),
                        "type": "api",
                    }
                )

        return components[:5]  # Limit to top 5

    def _generate_best_practices(
        self, agent_type: str, tools: List[ToolCapability]
    ) -> List[str]:
        """Generate best practices based on context"""

        practices = [
            "Focus on speed and performance over enterprise patterns",
            "Use async/parallel execution when possible",
            "Leverage existing ecosystem tools before building new ones",
        ]

        # Add type-specific practices
        type_practices = {
            "documentation": [
                "Generate markdown format for consistency",
                "Include code examples from actual codebase",
            ],
            "development": [
                "Follow existing code patterns in the ecosystem",
                "Prioritize working code over perfect abstractions",
            ],
            "integration": [
                "Use MCP for tool integration when available",
                "Prefer REST APIs for simple integrations",
            ],
        }

        practices.extend(type_practices.get(agent_type.lower(), []))

        # Add tool-specific practices
        if any(t.performance_metrics.get("async") for t in tools):
            practices.append("Use async patterns - ecosystem supports it")

        return practices[:5]  # Limit to top 5

    def _define_constraints(self, agent_type: str) -> List[str]:
        """Define constraints for the agent"""

        constraints = [
            "Single PC environment - no distributed systems",
            "Solo developer - no team coordination needed",
            "Performance over perfection",
        ]

        type_constraints = {
            "documentation": ["Keep docs concise and practical"],
            "development": ["Avoid over-engineering"],
            "integration": ["Minimize external dependencies"],
        }

        constraints.extend(type_constraints.get(agent_type.lower(), []))

        return constraints


class ContextInjectionSystem:
    """Main context injection system for orchestrator integration"""

    def __init__(self, master_root: str = "/home/opsvi/master_root"):
        self.discovery = EcosystemDiscovery(master_root)
        self.filter = ContextFilter()
        self.generator = DynamicContextGenerator(self.discovery, self.filter)
        self.context_cache: Dict[str, AgentContext] = {}

    def inject_context(
        self,
        agent_type: str,
        task_description: str,
        base_prompt: str,
        additional_context: Dict[str, Any] = None,
        use_cache: bool = True,
    ) -> str:
        """Inject context into agent prompt"""

        # Generate cache key
        cache_key = f"{agent_type}:{task_description[:50]}"

        # Use cached context if available
        if use_cache and cache_key in self.context_cache:
            context = self.context_cache[cache_key]
        else:
            # Generate fresh context
            context = self.generator.generate_context(
                agent_type, task_description, additional_context
            )
            self.context_cache[cache_key] = context

        # Enhance prompt with context
        context_enhancement = context.to_prompt_enhancement()

        # Inject context at appropriate position
        enhanced_prompt = f"""
{context_enhancement}

TASK INSTRUCTIONS:
{base_prompt}
"""

        return enhanced_prompt

    def get_context_file(
        self, agent_type: str, task_description: str, output_path: Optional[str] = None
    ) -> str:
        """Generate a context file for agent reference"""

        context = self.generator.generate_context(agent_type, task_description)

        # Convert to JSON format
        context_data = {
            "generated_at": datetime.now().isoformat(),
            "agent_type": agent_type,
            "task_description": task_description,
            "core_identity": context.core_identity,
            "task_context": context.task_context,
            "available_tools": [
                {
                    "name": t.name,
                    "type": t.type,
                    "description": t.description,
                    "capabilities": t.capabilities,
                    "path": t.path,
                }
                for t in context.available_tools
            ],
            "integration_opportunities": context.integration_opportunities,
            "performance_targets": context.performance_targets,
            "reusable_components": context.reusable_components,
            "best_practices": context.best_practices,
            "constraints": context.constraints,
        }

        # Write to file if path provided
        if output_path:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w") as f:
                json.dump(context_data, f, indent=2)
            return str(path)

        return json.dumps(context_data, indent=2)

    def refresh_ecosystem(self):
        """Force refresh of ecosystem capabilities"""
        self.discovery.scan_ecosystem(force_refresh=True)
        self.context_cache.clear()
        logger.info("Ecosystem capabilities refreshed")


# Singleton instance for easy import
_instance: Optional[ContextInjectionSystem] = None


def get_context_system(
    master_root: str = "/home/opsvi/master_root",
) -> ContextInjectionSystem:
    """Get or create the singleton context system instance"""
    global _instance
    if _instance is None:
        _instance = ContextInjectionSystem(master_root)
    return _instance
