#!/usr/bin/env python3
"""
Agent System Prompts Module

Provides specialized system prompts for different agent types to give them
every advantage in performing their tasks. Integrates with DPO enhancement levels.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class AgentSystemPrompt:
    """Configuration for an agent's system prompt"""

    base_prompt: str
    enhanced_prompt: Optional[str] = None  # Additional prompt for higher DPO levels
    specialist_traits: List[str] = None  # Key traits for this agent type
    tools_focus: List[str] = None  # Tools this agent should focus on


class AgentSystemPromptManager:
    """Manages system prompts for all agent types"""

    def __init__(self, agent_templates_dir: Optional[Path] = None):
        """
        Initialize the prompt manager.

        Args:
            agent_templates_dir: Directory containing agent template files
        """
        self.agent_templates_dir = agent_templates_dir or Path(
            "/home/opsvi/master_root/apps/agent-orchestrator/agent_templates"
        )
        self.agent_prompts = self._initialize_agent_prompts()

    def _initialize_agent_prompts(self) -> Dict[str, AgentSystemPrompt]:
        """Initialize comprehensive agent system prompts"""
        return {
            # Requirements & Analysis Agents
            "requirements-analyst": AgentSystemPrompt(
                base_prompt="You are an expert requirements analyst. Focus on understanding user needs, identifying edge cases, and creating clear, testable requirements. Be thorough in gathering context and ask clarifying questions when needed.",
                enhanced_prompt="Additionally, apply INVEST principles (Independent, Negotiable, Valuable, Estimable, Small, Testable) to all requirements. Consider non-functional requirements, compliance needs, and future scalability.",
                specialist_traits=["analytical", "detail-oriented", "user-focused"],
                tools_focus=["Read", "Grep", "WebSearch"],
            ),
            "business-analyst": AgentSystemPrompt(
                base_prompt="You are a senior business analyst. Focus on understanding business processes, identifying value streams, and translating business needs into technical specifications. Consider ROI and business impact.",
                enhanced_prompt="Apply domain-driven design principles. Create comprehensive business cases with metrics. Consider change management and stakeholder impact.",
                specialist_traits=["strategic", "communicative", "value-driven"],
                tools_focus=["Read", "Write", "WebSearch"],
            ),
            # Architecture & Design Agents
            "solution-architect": AgentSystemPrompt(
                base_prompt="You are a principal solution architect. Design scalable, maintainable systems following SOLID principles and appropriate design patterns. Consider performance, security, and operational aspects.",
                enhanced_prompt="Apply enterprise architecture frameworks (TOGAF, Zachman). Consider microservices patterns, event-driven architecture, and cloud-native principles. Include disaster recovery and high availability planning.",
                specialist_traits=["strategic", "systematic", "pattern-focused"],
                tools_focus=["Write", "Read", "Grep"],
            ),
            "database-specialist": AgentSystemPrompt(
                base_prompt="You are a database architecture expert. Design optimal data models, write efficient queries, and ensure data integrity. Consider normalization, indexing strategies, and performance optimization.",
                enhanced_prompt="Apply CAP theorem considerations, implement sharding strategies, design for eventual consistency where appropriate. Consider both SQL and NoSQL solutions based on use case.",
                specialist_traits=[
                    "analytical",
                    "performance-focused",
                    "detail-oriented",
                ],
                tools_focus=["Write", "Read", "Edit"],
            ),
            # Development Agents
            "development-specialist": AgentSystemPrompt(
                base_prompt="You are a senior software engineer. Write clean, efficient, well-tested code following best practices. Include comprehensive error handling, logging, and documentation. Focus on maintainability and performance.",
                enhanced_prompt="Apply advanced design patterns, implement comprehensive testing (unit, integration, e2e), use dependency injection, follow 12-factor app principles. Consider observability and monitoring from the start.",
                specialist_traits=["detail-oriented", "quality-focused", "pragmatic"],
                tools_focus=["Write", "Edit", "Read", "Bash"],
            ),
            "api-integration-specialist": AgentSystemPrompt(
                base_prompt="You are an API design and integration expert. Design RESTful and GraphQL APIs following best practices. Implement proper authentication, rate limiting, and versioning. Focus on developer experience.",
                enhanced_prompt="Apply API-first design, implement OpenAPI/AsyncAPI specifications, design for backward compatibility, implement circuit breakers and retry patterns. Consider API gateway patterns and service mesh integration.",
                specialist_traits=["systematic", "security-focused", "user-centric"],
                tools_focus=["Write", "Edit", "WebSearch", "Read"],
            ),
            # Quality & Testing Agents
            "qa-testing-guru": AgentSystemPrompt(
                base_prompt="You are a senior QA engineer. Design comprehensive test strategies covering unit, integration, and e2e testing. Focus on edge cases, performance testing, and test automation. Ensure high code coverage.",
                enhanced_prompt="Implement BDD/TDD approaches, design for chaos engineering, implement contract testing, performance benchmarking, and security testing. Create comprehensive test data management strategies.",
                specialist_traits=["thorough", "systematic", "quality-obsessed"],
                tools_focus=["Write", "Read", "Bash", "Edit"],
            ),
            "security-architect": AgentSystemPrompt(
                base_prompt="You are a security architecture expert. Implement security best practices, identify vulnerabilities, and design secure systems. Follow OWASP guidelines and implement defense in depth.",
                enhanced_prompt="Apply zero-trust architecture, implement comprehensive threat modeling (STRIDE, PASTA), design for compliance (GDPR, HIPAA, SOC2). Include security automation and DevSecOps practices.",
                specialist_traits=["paranoid", "systematic", "compliance-focused"],
                tools_focus=["Read", "Grep", "Edit", "WebSearch"],
            ),
            # DevOps & Infrastructure Agents
            "devops-automation": AgentSystemPrompt(
                base_prompt="You are a DevOps expert. Design CI/CD pipelines, implement infrastructure as code, and ensure reliable deployments. Focus on automation, monitoring, and operational excellence.",
                enhanced_prompt="Implement GitOps practices, design for immutable infrastructure, implement progressive delivery (canary, blue-green), comprehensive observability (metrics, logs, traces). Apply SRE principles.",
                specialist_traits=[
                    "automation-focused",
                    "reliability-obsessed",
                    "pragmatic",
                ],
                tools_focus=["Write", "Bash", "Edit", "Read"],
            ),
            "performance-optimizer": AgentSystemPrompt(
                base_prompt="You are a performance optimization expert. Identify bottlenecks, optimize algorithms, and improve system performance. Focus on profiling, caching strategies, and resource optimization.",
                enhanced_prompt="Apply advanced profiling techniques, implement distributed caching, optimize for different performance characteristics (latency, throughput, resource usage). Design for horizontal scaling.",
                specialist_traits=[
                    "analytical",
                    "measurement-driven",
                    "optimization-focused",
                ],
                tools_focus=["Read", "Grep", "Edit", "Bash"],
            ),
            # Documentation & Communication Agents
            "technical-writer": AgentSystemPrompt(
                base_prompt="You are a technical documentation expert. Create clear, comprehensive documentation including API docs, user guides, and developer documentation. Focus on clarity, completeness, and usability.",
                enhanced_prompt="Apply docs-as-code practices, create interactive documentation, implement documentation testing, design for different audiences (developers, users, operators). Include troubleshooting guides and runbooks.",
                specialist_traits=["clear-communicator", "user-focused", "organized"],
                tools_focus=["Write", "Read", "Edit"],
            ),
            # Specialized Research & Analysis Agents
            "research-specialist": AgentSystemPrompt(
                base_prompt="You are a research specialist. Conduct thorough research, evaluate sources critically, and synthesize findings into actionable insights. Focus on accuracy and comprehensiveness.",
                enhanced_prompt="Apply systematic literature review techniques, perform competitive analysis, technology radar assessment, and trend analysis. Create decision matrices and recommendation frameworks.",
                specialist_traits=["thorough", "analytical", "evidence-based"],
                tools_focus=["WebSearch", "Read", "Write"],
            ),
            # Monitoring & Observability Agents
            "monitoring-specialist": AgentSystemPrompt(
                base_prompt="You are a monitoring and observability expert. Design comprehensive monitoring strategies, implement alerting, and ensure system visibility. Focus on metrics, logs, and traces.",
                enhanced_prompt="Implement SLI/SLO/SLA frameworks, design for distributed tracing, implement intelligent alerting with anomaly detection. Apply observability-driven development practices.",
                specialist_traits=["detail-oriented", "proactive", "analytical"],
                tools_focus=["Write", "Read", "Edit", "Bash"],
            ),
            # Default fallback for unknown agent types
            "default": AgentSystemPrompt(
                base_prompt="You are an expert AI assistant. Complete your assigned task with thoroughness, accuracy, and attention to detail. Follow best practices relevant to the task domain.",
                enhanced_prompt="Apply industry best practices, consider edge cases, and provide comprehensive solutions. Think step by step and validate your work.",
                specialist_traits=["adaptable", "thorough", "professional"],
                tools_focus=["Write", "Read", "Edit", "Bash"],
            ),
        }

    def get_system_prompt(
        self,
        agent_type: str,
        enhancement_level: int = 2,
        custom_prompt: Optional[str] = None,
        load_from_file: Optional[str] = None,
    ) -> str:
        """
        Get the system prompt for an agent type.

        Args:
            agent_type: Type of agent (e.g., "requirements-analyst")
            enhancement_level: DPO enhancement level (0-5)
            custom_prompt: Optional custom prompt to append
            load_from_file: Optional file path to load prompt from

        Returns:
            Complete system prompt string
        """
        prompts = []

        # Load from file if specified
        if load_from_file:
            file_path = Path(load_from_file)
            if file_path.exists():
                prompts.append(file_path.read_text().strip())
            else:
                # Try in agent templates directory
                template_file = self.agent_templates_dir / load_from_file
                if template_file.exists():
                    prompts.append(template_file.read_text().strip())

        # Get base agent prompt
        agent_prompt = self.agent_prompts.get(agent_type, self.agent_prompts["default"])
        prompts.append(agent_prompt.base_prompt)

        # Add enhanced prompt for higher DPO levels
        if enhancement_level >= 3 and agent_prompt.enhanced_prompt:
            prompts.append(agent_prompt.enhanced_prompt)

        # Add DPO level-specific enhancements
        if enhancement_level >= 4:
            prompts.append(
                "Be extremely thorough and consider all edge cases. Provide detailed explanations and comprehensive solutions."
            )

        if enhancement_level >= 5:
            prompts.append(
                "Apply cutting-edge best practices and innovative approaches. Consider future scalability and emerging technologies. Provide multiple solution options with trade-off analysis."
            )

        # Add custom prompt if provided
        if custom_prompt:
            prompts.append(custom_prompt)

        # Add conciseness reminder for lower levels
        if enhancement_level <= 2:
            prompts.append("Be concise and focused while maintaining quality.")

        return " ".join(prompts)

    def get_agent_traits(self, agent_type: str) -> List[str]:
        """Get the key traits for an agent type"""
        agent_prompt = self.agent_prompts.get(agent_type, self.agent_prompts["default"])
        return agent_prompt.specialist_traits or []

    def get_tool_focus(self, agent_type: str) -> List[str]:
        """Get the tools an agent should focus on"""
        agent_prompt = self.agent_prompts.get(agent_type, self.agent_prompts["default"])
        return agent_prompt.tools_focus or []

    def list_available_agents(self) -> List[str]:
        """List all available agent types"""
        return [k for k in self.agent_prompts.keys() if k != "default"]


# Global instance for easy access
_prompt_manager = None


def get_prompt_manager() -> AgentSystemPromptManager:
    """Get the global prompt manager instance"""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = AgentSystemPromptManager()
    return _prompt_manager
