#!/usr/bin/env python3
"""
Sample Data Generator for DPO Testing

Provides comprehensive sample data for testing various DPO scenarios
including different project types, complexity levels, and contexts.
"""

import json
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class ProjectType(Enum):
    """Project types for testing"""

    API = "api"
    WEBAPP = "webapp"
    CLI = "cli"
    LIBRARY = "library"
    INTEGRATION = "integration"
    MICROSERVICE = "microservice"
    MOBILE = "mobile"
    DESKTOP = "desktop"


class ComplexityLevel(Enum):
    """Complexity levels for testing"""

    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    ENTERPRISE = "enterprise"


@dataclass
class SampleRequest:
    """Sample development request"""

    request: str
    context: Dict[str, Any]
    expected_type: ProjectType
    expected_complexity: ComplexityLevel
    expected_agents: range
    expected_phases: List[str]
    description: str


class SampleRequestGenerator:
    """Generator for sample development requests"""

    def __init__(self):
        self.api_frameworks = [
            "FastAPI",
            "Django",
            "Flask",
            "Express",
            "Spring Boot",
            "ASP.NET Core",
        ]
        self.frontend_frameworks = ["React", "Vue", "Angular", "Svelte", "Next.js"]
        self.databases = ["PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite"]
        self.languages = [
            "Python",
            "JavaScript",
            "TypeScript",
            "Java",
            "C#",
            "Go",
            "Rust",
        ]
        self.cloud_platforms = ["AWS", "Azure", "GCP", "Heroku", "Vercel"]

    def get_api_request(self, complexity: str = "medium") -> SampleRequest:
        """Generate API development request"""

        if complexity == "simple":
            return SampleRequest(
                request="Build a simple REST API for user authentication with basic CRUD operations",
                context={
                    "framework": random.choice(["FastAPI", "Flask", "Express"]),
                    "database": random.choice(["SQLite", "PostgreSQL"]),
                    "authentication": "JWT",
                    "features": ["user_registration", "login", "profile_management"],
                },
                expected_type=ProjectType.API,
                expected_complexity=ComplexityLevel.SIMPLE,
                expected_agents=range(3, 6),
                expected_phases=[
                    "discovery",
                    "implementation",
                    "testing",
                    "documentation",
                ],
                description="Simple authentication API with basic features",
            )

        elif complexity == "medium":
            return SampleRequest(
                request="Create a RESTful API for a task management system with user roles, notifications, and file attachments",
                context={
                    "framework": random.choice(self.api_frameworks[:3]),
                    "database": random.choice(["PostgreSQL", "MySQL"]),
                    "authentication": "OAuth2",
                    "features": [
                        "task_management",
                        "user_roles",
                        "notifications",
                        "file_upload",
                        "search",
                    ],
                    "integrations": ["email_service", "cloud_storage"],
                },
                expected_type=ProjectType.API,
                expected_complexity=ComplexityLevel.MEDIUM,
                expected_agents=range(5, 8),
                expected_phases=[
                    "discovery",
                    "architecture",
                    "implementation",
                    "testing",
                    "documentation",
                ],
                description="Task management API with advanced features",
            )

        elif complexity == "complex":
            return SampleRequest(
                request="Build a comprehensive e-commerce API with inventory management, payment processing, recommendation engine, and analytics",
                context={
                    "framework": random.choice(self.api_frameworks),
                    "database": ["PostgreSQL", "Redis"],
                    "authentication": "OAuth2 + 2FA",
                    "features": [
                        "product_catalog",
                        "inventory_management",
                        "order_processing",
                        "payment_integration",
                        "recommendation_engine",
                        "analytics_dashboard",
                        "admin_panel",
                        "customer_support",
                        "multi_tenant",
                    ],
                    "integrations": [
                        "payment_gateway",
                        "shipping_service",
                        "email_marketing",
                    ],
                    "scale": "high_availability",
                    "security": "PCI_compliance",
                },
                expected_type=ProjectType.API,
                expected_complexity=ComplexityLevel.COMPLEX,
                expected_agents=range(10, 15),
                expected_phases=[
                    "discovery",
                    "architecture",
                    "implementation",
                    "testing",
                    "security",
                    "deployment",
                    "documentation",
                ],
                description="Enterprise-grade e-commerce API with advanced features",
            )

        return self.get_api_request("medium")  # Default fallback

    def get_webapp_request(self, complexity: str = "medium") -> SampleRequest:
        """Generate web application request"""

        if complexity == "simple":
            return SampleRequest(
                request="Create a simple blog website with post creation, editing, and commenting features",
                context={
                    "frontend": random.choice(["React", "Vue", "HTML/CSS/JS"]),
                    "backend": random.choice(["Node.js", "Python"]),
                    "database": "SQLite",
                    "features": [
                        "blog_posts",
                        "comments",
                        "user_profiles",
                        "admin_panel",
                    ],
                },
                expected_type=ProjectType.WEBAPP,
                expected_complexity=ComplexityLevel.SIMPLE,
                expected_agents=range(4, 7),
                expected_phases=[
                    "discovery",
                    "design",
                    "frontend",
                    "backend",
                    "testing",
                    "deployment",
                ],
                description="Simple blog application",
            )

        elif complexity == "complex":
            return SampleRequest(
                request="Build a comprehensive project management web application with real-time collaboration, advanced analytics, and mobile responsiveness",
                context={
                    "frontend": random.choice(["React", "Vue", "Angular"]),
                    "backend": random.choice(["Node.js", "Python", "Java"]),
                    "database": ["PostgreSQL", "Redis"],
                    "realtime": "WebSocket",
                    "features": [
                        "project_management",
                        "team_collaboration",
                        "real_time_chat",
                        "file_sharing",
                        "time_tracking",
                        "reporting_analytics",
                        "mobile_responsive",
                        "offline_support",
                        "integrations",
                    ],
                    "integrations": ["slack", "github", "google_workspace"],
                    "scale": "enterprise",
                },
                expected_type=ProjectType.WEBAPP,
                expected_complexity=ComplexityLevel.COMPLEX,
                expected_agents=range(12, 18),
                expected_phases=[
                    "discovery",
                    "architecture",
                    "design",
                    "frontend",
                    "backend",
                    "testing",
                    "deployment",
                    "documentation",
                ],
                description="Enterprise project management application",
            )

        # Default medium complexity
        return SampleRequest(
            request="Develop a social media dashboard for managing multiple social accounts with analytics",
            context={
                "frontend": random.choice(self.frontend_frameworks[:3]),
                "backend": random.choice(["Node.js", "Python"]),
                "database": "PostgreSQL",
                "features": [
                    "social_media_integration",
                    "post_scheduling",
                    "analytics",
                    "user_management",
                ],
                "integrations": ["twitter_api", "facebook_api", "instagram_api"],
            },
            expected_type=ProjectType.WEBAPP,
            expected_complexity=ComplexityLevel.MEDIUM,
            expected_agents=range(6, 10),
            expected_phases=[
                "discovery",
                "design",
                "frontend",
                "backend",
                "testing",
                "deployment",
            ],
            description="Social media management dashboard",
        )

    def get_cli_request(self, complexity: str = "medium") -> SampleRequest:
        """Generate CLI tool request"""

        if complexity == "simple":
            return SampleRequest(
                request="Create a command-line tool for file compression and decompression with basic options",
                context={
                    "language": random.choice(["Python", "Go", "Rust"]),
                    "features": [
                        "file_compression",
                        "directory_compression",
                        "progress_bar",
                    ],
                    "output_format": ["zip", "tar.gz"],
                },
                expected_type=ProjectType.CLI,
                expected_complexity=ComplexityLevel.SIMPLE,
                expected_agents=range(3, 5),
                expected_phases=[
                    "discovery",
                    "implementation",
                    "testing",
                    "documentation",
                ],
                description="Simple file compression tool",
            )

        elif complexity == "medium":
            return SampleRequest(
                request="Build a CLI tool for log analysis with pattern matching, filtering, and report generation",
                context={
                    "language": random.choice(["Python", "Go", "Rust"]),
                    "features": [
                        "log_parsing",
                        "pattern_matching",
                        "filtering",
                        "statistics",
                        "report_generation",
                        "multiple_formats",
                        "real_time_monitoring",
                    ],
                    "input_formats": ["json", "text", "csv"],
                    "output_formats": ["html", "pdf", "json"],
                },
                expected_type=ProjectType.CLI,
                expected_complexity=ComplexityLevel.MEDIUM,
                expected_agents=range(4, 7),
                expected_phases=[
                    "discovery",
                    "implementation",
                    "testing",
                    "documentation",
                ],
                description="Log analysis and reporting tool",
            )

        return self.get_cli_request("medium")  # Default fallback

    def get_integration_request(self, complexity: str = "medium") -> SampleRequest:
        """Generate integration service request"""

        if complexity == "enterprise":
            return SampleRequest(
                request="Build a comprehensive data integration platform connecting multiple enterprise systems with real-time sync and monitoring",
                context={
                    "language": random.choice(["Python", "Java", "Go"]),
                    "integrations": [
                        "salesforce_api",
                        "hubspot_api",
                        "slack_api",
                        "jira_api",
                        "database_connectors",
                        "file_systems",
                        "message_queues",
                    ],
                    "features": [
                        "real_time_sync",
                        "data_transformation",
                        "error_handling",
                        "monitoring_dashboard",
                        "alerting",
                        "retry_logic",
                        "data_validation",
                        "audit_logging",
                    ],
                    "architecture": "microservices",
                    "scale": "enterprise",
                    "reliability": "99.9%_uptime",
                },
                expected_type=ProjectType.INTEGRATION,
                expected_complexity=ComplexityLevel.ENTERPRISE,
                expected_agents=range(10, 15),
                expected_phases=[
                    "discovery",
                    "architecture",
                    "implementation",
                    "testing",
                    "monitoring",
                    "deployment",
                    "documentation",
                ],
                description="Enterprise data integration platform",
            )

        # Default medium complexity
        return SampleRequest(
            request="Create a service to integrate CRM data with email marketing platform",
            context={
                "language": random.choice(["Python", "Node.js"]),
                "integrations": ["crm_api", "email_platform_api"],
                "features": ["data_sync", "automated_campaigns", "reporting"],
                "schedule": "real_time",
            },
            expected_type=ProjectType.INTEGRATION,
            expected_complexity=ComplexityLevel.MEDIUM,
            expected_agents=range(5, 8),
            expected_phases=["discovery", "implementation", "testing", "deployment"],
            description="CRM to email marketing integration",
        )

    def get_library_request(self, complexity: str = "medium") -> SampleRequest:
        """Generate library development request"""

        return SampleRequest(
            request="Develop a Python library for advanced data validation with custom rules and extensible architecture",
            context={
                "language": "Python",
                "features": [
                    "schema_validation",
                    "custom_validators",
                    "error_reporting",
                    "performance_optimization",
                    "plugin_system",
                ],
                "target_audience": "developers",
                "distribution": "pypi",
                "documentation": "comprehensive",
            },
            expected_type=ProjectType.LIBRARY,
            expected_complexity=ComplexityLevel.MEDIUM,
            expected_agents=range(4, 7),
            expected_phases=[
                "discovery",
                "design",
                "implementation",
                "testing",
                "documentation",
            ],
            description="Advanced data validation library",
        )

    def get_microservice_request(self, complexity: str = "medium") -> SampleRequest:
        """Generate microservice request"""

        return SampleRequest(
            request="Build a notification microservice with multiple delivery channels and retry logic",
            context={
                "language": random.choice(["Python", "Go", "Java"]),
                "architecture": "microservice",
                "features": [
                    "multi_channel_delivery",
                    "retry_logic",
                    "rate_limiting",
                    "template_engine",
                    "analytics",
                    "health_monitoring",
                ],
                "channels": ["email", "sms", "push_notifications", "webhooks"],
                "infrastructure": ["docker", "kubernetes"],
            },
            expected_type=ProjectType.MICROSERVICE,
            expected_complexity=ComplexityLevel.MEDIUM,
            expected_agents=range(6, 9),
            expected_phases=[
                "discovery",
                "architecture",
                "implementation",
                "testing",
                "deployment",
            ],
            description="Multi-channel notification microservice",
        )

    def get_random_request(self) -> SampleRequest:
        """Get a random request for testing"""
        project_types = [
            (self.get_api_request, ["simple", "medium", "complex"]),
            (self.get_webapp_request, ["simple", "complex"]),
            (self.get_cli_request, ["simple", "medium"]),
            (self.get_integration_request, ["medium", "enterprise"]),
            (self.get_library_request, ["medium"]),
            (self.get_microservice_request, ["medium"]),
        ]

        generator, complexities = random.choice(project_types)
        complexity = random.choice(complexities)

        return generator(complexity)

    def get_malformed_requests(self) -> List[Dict[str, Any]]:
        """Get malformed requests for error testing"""
        return [
            {
                "request": "",  # Empty request
                "context": {},
                "expected_error": "empty_request",
            },
            {
                "request": "Build something",  # Vague request
                "context": {},
                "expected_error": "vague_request",
            },
            {
                "request": "Create a web application for managing users",
                "context": {
                    "framework": "NonexistentFramework",  # Invalid framework
                    "database": "InvalidDB",
                },
                "expected_error": "invalid_context",
            },
            {
                "request": None,  # None request
                "context": {},
                "expected_error": "null_request",
            },
            {
                "request": "Build an API" * 1000,  # Extremely long request
                "context": {},
                "expected_error": "request_too_long",
            },
        ]

    def get_edge_case_requests(self) -> List[SampleRequest]:
        """Get edge case requests for boundary testing"""
        return [
            SampleRequest(
                request="Build a minimal 'Hello World' API with just one endpoint",
                context={"framework": "FastAPI", "minimal": True},
                expected_type=ProjectType.API,
                expected_complexity=ComplexityLevel.SIMPLE,
                expected_agents=range(2, 4),
                expected_phases=["implementation", "testing"],
                description="Minimal API edge case",
            ),
            SampleRequest(
                request="Create a massive enterprise system with 50+ microservices, multiple databases, AI/ML components, and global distribution",
                context={
                    "architecture": "distributed_microservices",
                    "scale": "global",
                    "components": ["ai_ml", "blockchain", "iot", "realtime_analytics"],
                    "databases": ["postgresql", "mongodb", "redis", "elasticsearch"],
                    "cloud": "multi_cloud",
                },
                expected_type=ProjectType.MICROSERVICE,
                expected_complexity=ComplexityLevel.ENTERPRISE,
                expected_agents=range(20, 25),
                expected_phases=[
                    "discovery",
                    "architecture",
                    "planning",
                    "implementation",
                    "integration",
                    "testing",
                    "deployment",
                    "monitoring",
                ],
                description="Maximum complexity enterprise system",
            ),
        ]

    def get_performance_test_requests(self) -> List[SampleRequest]:
        """Get requests specifically for performance testing"""
        return [
            self.get_api_request("simple"),
            self.get_api_request("medium"),
            self.get_api_request("complex"),
            self.get_webapp_request("simple"),
            self.get_webapp_request("complex"),
            self.get_cli_request("medium"),
            self.get_integration_request("enterprise"),
        ]


class SampleWorkflowData:
    """Sample workflow data for testing"""

    @staticmethod
    def get_sample_workflow() -> Dict[str, Any]:
        """Get a sample workflow structure"""
        return {
            "workflow_id": "sample_workflow_123",
            "phases": [
                {
                    "phase_id": "discovery",
                    "phase_name": "Requirements Discovery",
                    "phase_type": "discovery",
                    "agents": [
                        {
                            "role": "business_analyst",
                            "task": "Gather and document requirements",
                            "context": {
                                "domain_knowledge": ["API design", "user requirements"],
                                "tools": ["interview_template", "requirements_doc"],
                            },
                        },
                        {
                            "role": "technical_architect",
                            "task": "Define technical requirements and constraints",
                            "context": {
                                "domain_knowledge": [
                                    "system_architecture",
                                    "scalability",
                                ],
                                "tools": [
                                    "architecture_template",
                                    "constraint_analysis",
                                ],
                            },
                        },
                    ],
                    "dependencies": [],
                    "parallel_execution": True,
                    "quality_gates": ["requirements_review", "technical_feasibility"],
                    "expected_outputs": [
                        "requirements_document",
                        "technical_constraints",
                    ],
                },
                {
                    "phase_id": "architecture",
                    "phase_name": "System Architecture",
                    "phase_type": "design",
                    "agents": [
                        {
                            "role": "solution_architect",
                            "task": "Design system architecture",
                            "context": {
                                "domain_knowledge": ["microservices", "api_patterns"],
                                "tools": ["architecture_tools", "design_patterns"],
                            },
                        }
                    ],
                    "dependencies": ["discovery"],
                    "parallel_execution": False,
                    "quality_gates": ["architecture_review"],
                    "expected_outputs": ["architecture_diagram", "design_document"],
                },
                {
                    "phase_id": "implementation",
                    "phase_name": "Development Implementation",
                    "phase_type": "implementation",
                    "agents": [
                        {
                            "role": "backend_developer",
                            "task": "Implement API endpoints",
                            "context": {
                                "domain_knowledge": ["fastapi", "postgresql"],
                                "tools": ["ide", "testing_framework"],
                                "code_examples": [
                                    "api_patterns",
                                    "database_operations",
                                ],
                            },
                        },
                        {
                            "role": "database_developer",
                            "task": "Design and implement database schema",
                            "context": {
                                "domain_knowledge": ["postgresql", "database_design"],
                                "tools": ["database_tools", "migration_scripts"],
                            },
                        },
                    ],
                    "dependencies": ["architecture"],
                    "parallel_execution": True,
                    "quality_gates": ["code_review", "unit_tests"],
                    "expected_outputs": ["api_implementation", "database_schema"],
                },
            ],
            "metadata": {
                "total_agents": 5,
                "estimated_duration": "1 week",
                "complexity": "medium",
                "project_type": "api",
            },
        }

    @staticmethod
    def get_sample_enhanced_request() -> Dict[str, Any]:
        """Get a sample enhanced request with intelligence"""
        return {
            "original_request": "Build a REST API for user management",
            "analysis": {
                "request_type": "BUILD",
                "project_type": "api",
                "complexity": "medium",
                "key_requirements": ["user_management", "REST_API", "authentication"],
                "suggested_technologies": ["FastAPI", "PostgreSQL"],
                "risk_factors": ["security", "scalability"],
                "estimated_effort": "1-2 weeks",
                "confidence_score": 0.85,
            },
            "enhancements": [
                {
                    "id": "security_001",
                    "category": "SECURITY",
                    "title": "Implement OAuth2 authentication",
                    "description": "Add OAuth2 with JWT tokens for secure authentication",
                    "impact": "high",
                    "effort": "medium",
                    "priority": "high",
                    "phase": "foundation",
                },
                {
                    "id": "perf_001",
                    "category": "PERFORMANCE",
                    "title": "Add database indexing",
                    "description": "Optimize database queries with proper indexing",
                    "impact": "medium",
                    "effort": "low",
                    "priority": "medium",
                    "phase": "core",
                },
            ],
            "synthesis": {
                "priority_order": ["security_001", "perf_001"],
                "phase_roadmap": {"foundation": ["security_001"], "core": ["perf_001"]},
                "implementation_strategy": "security_first",
            },
        }
