"""Specifier agent for the autonomous software factory."""

import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from opsvi_auto_forge.agents.base_agent import AgentResponse, BaseAgent
from opsvi_auto_forge.config.models import AgentRole
from opsvi_auto_forge.application.orchestrator.task_models import TaskExecution


class RequirementsOutput(BaseModel):
    """Structured output for requirements extraction."""

    functional_requirements: List[Dict[str, Any]] = Field(
        ..., description="Functional requirements with details"
    )
    non_functional_requirements: List[Dict[str, Any]] = Field(
        ..., description="Non-functional requirements"
    )
    user_stories: List[Dict[str, Any]] = Field(
        ..., description="User stories with acceptance criteria"
    )
    constraints: List[str] = Field(
        default_factory=list, description="Technical and business constraints"
    )
    assumptions: List[str] = Field(default_factory=list, description="Key assumptions")
    dependencies: List[str] = Field(
        default_factory=list, description="External dependencies"
    )
    success_metrics: List[str] = Field(..., description="Success metrics and KPIs")


class SpecificationOutput(BaseModel):
    """Structured output for technical specifications."""

    api_specifications: List[Dict[str, Any]] = Field(
        ..., description="API endpoint specifications"
    )
    data_models: List[Dict[str, Any]] = Field(
        ..., description="Data models and schemas"
    )
    business_logic: List[Dict[str, Any]] = Field(
        ..., description="Business logic specifications"
    )
    error_handling: List[Dict[str, Any]] = Field(
        ..., description="Error handling specifications"
    )
    security_requirements: List[str] = Field(
        ..., description="Security requirements and measures"
    )
    performance_requirements: List[str] = Field(
        ..., description="Performance requirements"
    )
    integration_points: List[Dict[str, Any]] = Field(
        default_factory=list, description="Integration specifications"
    )


class TechSpecOutput(BaseModel):
    """Structured output for technology-specific specifications."""

    technology_stack: Dict[str, Any] = Field(
        ..., description="Recommended technology stack"
    )
    architecture_patterns: List[str] = Field(
        ..., description="Architecture patterns to use"
    )
    design_patterns: List[str] = Field(
        ..., description="Design patterns for implementation"
    )
    database_schema: Dict[str, Any] = Field(..., description="Database schema design")
    api_design: Dict[str, Any] = Field(..., description="API design and structure")
    deployment_config: Dict[str, Any] = Field(
        ..., description="Deployment configuration"
    )
    development_guidelines: List[str] = Field(
        ..., description="Development guidelines and standards"
    )


class SpecifierAgent(BaseAgent):
    """Agent responsible for requirements and specifications tasks."""

    def __init__(
        self,
        neo4j_client=None,
        logger: Optional[logging.Logger] = None,
        prompt_gateway=None,
        context_store=None,
    ):
        """Initialize the specifier agent."""
        super().__init__(
            AgentRole.SPECIFIER, neo4j_client, logger, prompt_gateway, context_store
        )

    async def execute(
        self,
        task_execution: TaskExecution,
        inputs: Dict[str, Any],
    ) -> AgentResponse:
        """Execute specification task.

        Args:
            task_execution: The task execution instance
            inputs: Input data containing requirements and context

        Returns:
            AgentResponse with specification results
        """
        task_name = task_execution.definition.name

        if task_name == "requirements":
            return await self._extract_requirements(task_execution, inputs)
        elif task_name == "spec":
            return await self._create_specifications(task_execution, inputs)
        elif task_name == "techspec":
            return await self._create_tech_specifications(task_execution, inputs)
        else:
            return AgentResponse(
                success=False,
                content=f"Unknown specification task: {task_name}",
                errors=[f"Unsupported task type: {task_name}"],
            )

    async def _extract_requirements(
        self,
        task_execution: TaskExecution,
        inputs: Dict[str, Any],
    ) -> AgentResponse:
        """Extract and formalize requirements.

        Args:
            task_execution: The task execution instance
            inputs: Input data containing project description

        Returns:
            AgentResponse with requirements extraction results
        """
        project_description = inputs.get("description", "")
        context = inputs.get("context", {})

        try:
            # For now, create structured requirements without AI model call
            # In production, this would use the gpt-4.1-mini model for execution
            requirements_output = RequirementsOutput(
                functional_requirements=[
                    {
                        "id": "FR-001",
                        "title": "User Authentication",
                        "description": "Users must be able to authenticate using JWT tokens",
                        "priority": "high",
                        "acceptance_criteria": [
                            "Users can register with email and password",
                            "Users can login and receive JWT token",
                            "Protected endpoints require valid JWT token",
                            "Token expiration is handled gracefully",
                        ],
                    },
                    {
                        "id": "FR-002",
                        "title": "Item Management",
                        "description": "Users can perform CRUD operations on items",
                        "priority": "high",
                        "acceptance_criteria": [
                            "Users can create new items",
                            "Users can read item details",
                            "Users can update existing items",
                            "Users can delete items",
                            "Items are associated with authenticated users",
                        ],
                    },
                    {
                        "id": "FR-003",
                        "title": "Health Check",
                        "description": "System provides health check endpoint",
                        "priority": "medium",
                        "acceptance_criteria": [
                            "Health endpoint returns system status",
                            "Health check includes database connectivity",
                            "Health check includes service dependencies",
                        ],
                    },
                ],
                non_functional_requirements=[
                    {
                        "category": "Performance",
                        "requirements": [
                            "API response time < 200ms for 95% of requests",
                            "Support for 1000+ concurrent users",
                            "Database queries optimized for performance",
                        ],
                    },
                    {
                        "category": "Security",
                        "requirements": [
                            "All endpoints use HTTPS",
                            "JWT tokens are securely generated and validated",
                            "Input validation prevents injection attacks",
                            "Sensitive data is encrypted at rest",
                        ],
                    },
                    {
                        "category": "Reliability",
                        "requirements": [
                            "99.9% uptime target",
                            "Graceful error handling",
                            "Comprehensive logging and monitoring",
                        ],
                    },
                ],
                user_stories=[
                    {
                        "id": "US-001",
                        "title": "As a user, I want to register an account",
                        "description": "I want to create a new account with email and password",
                        "acceptance_criteria": [
                            "Registration form validates email format",
                            "Password meets security requirements",
                            "Account is created successfully",
                            "User receives confirmation",
                        ],
                        "story_points": 3,
                    },
                    {
                        "id": "US-002",
                        "title": "As a user, I want to login to my account",
                        "description": "I want to authenticate and access my data",
                        "acceptance_criteria": [
                            "Login validates credentials",
                            "JWT token is issued upon successful login",
                            "Failed login attempts are handled gracefully",
                            "User is redirected to appropriate page",
                        ],
                        "story_points": 2,
                    },
                    {
                        "id": "US-003",
                        "title": "As a user, I want to manage my items",
                        "description": "I want to create, read, update, and delete items",
                        "acceptance_criteria": [
                            "I can create new items with required fields",
                            "I can view a list of my items",
                            "I can edit existing items",
                            "I can delete items with confirmation",
                            "Only my own items are visible to me",
                        ],
                        "story_points": 5,
                    },
                ],
                constraints=[
                    "Must use FastAPI framework",
                    "Must use SQLite database",
                    "Must implement JWT authentication",
                    "Must achieve 85%+ test coverage",
                    "Must follow PEP 8 coding standards",
                ],
                assumptions=[
                    "Users have modern web browsers",
                    "Database will be local SQLite instance",
                    "No external authentication providers required",
                    "Single-user deployment model",
                ],
                dependencies=[
                    "FastAPI framework",
                    "SQLite database",
                    "JWT library for authentication",
                    "Pytest for testing",
                    "Alembic for migrations",
                ],
                success_metrics=[
                    "All functional requirements implemented and tested",
                    "85%+ test coverage achieved",
                    "All security requirements satisfied",
                    "Performance benchmarks met",
                    "Code quality standards maintained",
                ],
            )

            # Log decision
            self._log_decision(
                task_execution,
                f"Extracted {len(requirements_output.functional_requirements)} functional requirements",
                confidence=0.9,
                params={"user_stories_count": len(requirements_output.user_stories)},
            )

            return AgentResponse(
                success=True,
                content=requirements_output.model_dump_json(indent=2),
                artifacts=[
                    {
                        "type": "documentation",
                        "content": requirements_output.model_dump_json(indent=2),
                        "metadata": {
                            "functional_requirements_count": len(
                                requirements_output.functional_requirements
                            ),
                            "user_stories_count": len(requirements_output.user_stories),
                            "constraints_count": len(requirements_output.constraints),
                        },
                    }
                ],
                metadata={
                    "functional_requirements_count": len(
                        requirements_output.functional_requirements
                    ),
                    "user_stories_count": len(requirements_output.user_stories),
                    "constraints_count": len(requirements_output.constraints),
                },
            )

        except Exception as e:
            self.logger.error(
                f"Failed to extract requirements: {str(e)}", exc_info=True
            )
            return AgentResponse(
                success=False,
                content=f"Failed to extract requirements: {str(e)}",
                errors=[str(e)],
            )

    async def _create_specifications(
        self,
        task_execution: TaskExecution,
        inputs: Dict[str, Any],
    ) -> AgentResponse:
        """Create detailed technical specifications.

        Args:
            task_execution: The task execution instance
            inputs: Input data containing requirements

        Returns:
            AgentResponse with specification results
        """
        requirements = inputs.get("requirements", {})

        try:
            # Create detailed specifications
            spec_output = SpecificationOutput(
                api_specifications=[
                    {
                        "endpoint": "/auth/register",
                        "method": "POST",
                        "description": "Register a new user account",
                        "request_body": {
                            "email": "string (required)",
                            "password": "string (required, min 8 chars)",
                            "full_name": "string (optional)",
                        },
                        "response": {
                            "201": {"message": "User created successfully"},
                            "400": {"error": "Validation error"},
                            "409": {"error": "User already exists"},
                        },
                    },
                    {
                        "endpoint": "/auth/login",
                        "method": "POST",
                        "description": "Authenticate user and get JWT token",
                        "request_body": {
                            "username": "string (required)",
                            "password": "string (required)",
                        },
                        "response": {
                            "200": {"access_token": "string", "token_type": "bearer"},
                            "401": {"error": "Invalid credentials"},
                        },
                    },
                    {
                        "endpoint": "/items",
                        "method": "GET",
                        "description": "Get list of user's items",
                        "headers": {"Authorization": "Bearer <token>"},
                        "response": {
                            "200": {"items": "array of Item objects"},
                            "401": {"error": "Unauthorized"},
                        },
                    },
                    {
                        "endpoint": "/items",
                        "method": "POST",
                        "description": "Create a new item",
                        "headers": {"Authorization": "Bearer <token>"},
                        "request_body": {
                            "title": "string (required)",
                            "description": "string (optional)",
                            "price": "number (optional)",
                        },
                        "response": {
                            "201": {"item": "Item object"},
                            "400": {"error": "Validation error"},
                            "401": {"error": "Unauthorized"},
                        },
                    },
                    {
                        "endpoint": "/health",
                        "method": "GET",
                        "description": "Health check endpoint",
                        "response": {
                            "200": {
                                "status": "healthy",
                                "timestamp": "ISO datetime",
                                "version": "string",
                            }
                        },
                    },
                ],
                data_models=[
                    {
                        "name": "User",
                        "fields": [
                            {
                                "name": "id",
                                "type": "UUID",
                                "description": "Primary key",
                            },
                            {
                                "name": "email",
                                "type": "string",
                                "description": "User email (unique)",
                            },
                            {
                                "name": "hashed_password",
                                "type": "string",
                                "description": "Hashed password",
                            },
                            {
                                "name": "full_name",
                                "type": "string",
                                "description": "User's full name",
                            },
                            {
                                "name": "is_active",
                                "type": "boolean",
                                "description": "Account status",
                            },
                            {
                                "name": "created_at",
                                "type": "datetime",
                                "description": "Account creation time",
                            },
                        ],
                    },
                    {
                        "name": "Item",
                        "fields": [
                            {
                                "name": "id",
                                "type": "UUID",
                                "description": "Primary key",
                            },
                            {
                                "name": "title",
                                "type": "string",
                                "description": "Item title",
                            },
                            {
                                "name": "description",
                                "type": "string",
                                "description": "Item description",
                            },
                            {
                                "name": "price",
                                "type": "decimal",
                                "description": "Item price",
                            },
                            {
                                "name": "owner_id",
                                "type": "UUID",
                                "description": "Foreign key to User",
                            },
                            {
                                "name": "created_at",
                                "type": "datetime",
                                "description": "Item creation time",
                            },
                            {
                                "name": "updated_at",
                                "type": "datetime",
                                "description": "Last update time",
                            },
                        ],
                    },
                ],
                business_logic=[
                    {
                        "name": "User Authentication",
                        "description": "Handle user registration and login",
                        "rules": [
                            "Email must be unique across all users",
                            "Password must be hashed using bcrypt",
                            "JWT tokens expire after 30 minutes",
                            "Failed login attempts are logged",
                        ],
                    },
                    {
                        "name": "Item Management",
                        "description": "Handle CRUD operations for items",
                        "rules": [
                            "Users can only access their own items",
                            "Item titles are required and must be non-empty",
                            "Prices must be positive numbers",
                            "Soft delete for items (mark as deleted, don't remove)",
                        ],
                    },
                    {
                        "name": "Data Validation",
                        "description": "Input validation and sanitization",
                        "rules": [
                            "All inputs are validated using Pydantic models",
                            "SQL injection prevention through parameterized queries",
                            "XSS prevention through input sanitization",
                            "Rate limiting on authentication endpoints",
                        ],
                    },
                ],
                error_handling=[
                    {
                        "error_type": "ValidationError",
                        "description": "Input validation failures",
                        "http_status": 400,
                        "response_format": {
                            "error": "Validation error",
                            "details": "array of errors",
                        },
                    },
                    {
                        "error_type": "AuthenticationError",
                        "description": "Authentication failures",
                        "http_status": 401,
                        "response_format": {"error": "Unauthorized"},
                    },
                    {
                        "error_type": "NotFoundError",
                        "description": "Resource not found",
                        "http_status": 404,
                        "response_format": {"error": "Resource not found"},
                    },
                    {
                        "error_type": "InternalServerError",
                        "description": "Unexpected server errors",
                        "http_status": 500,
                        "response_format": {"error": "Internal server error"},
                    },
                ],
                security_requirements=[
                    "JWT tokens must be signed with secure secret key",
                    "Passwords must be hashed using bcrypt with salt",
                    "All endpoints must validate JWT tokens",
                    "CORS must be properly configured",
                    "Rate limiting must be implemented",
                    "Input validation must prevent injection attacks",
                ],
                performance_requirements=[
                    "API response time < 200ms for 95% of requests",
                    "Database queries must use indexes",
                    "Connection pooling for database connections",
                    "Caching for frequently accessed data",
                    "Async/await for I/O operations",
                ],
                integration_points=[
                    {
                        "name": "Database",
                        "type": "SQLite",
                        "description": "Primary data storage",
                        "requirements": [
                            "Connection pooling",
                            "Migration support via Alembic",
                            "Backup and recovery procedures",
                        ],
                    }
                ],
            )

            # Log decision
            self._log_decision(
                task_execution,
                f"Created specifications with {len(spec_output.api_specifications)} API endpoints",
                confidence=0.9,
                params={"endpoints_count": len(spec_output.api_specifications)},
            )

            return AgentResponse(
                success=True,
                content=spec_output.model_dump_json(indent=2),
                artifacts=[
                    {
                        "type": "documentation",
                        "content": spec_output.model_dump_json(indent=2),
                        "metadata": {
                            "api_endpoints_count": len(spec_output.api_specifications),
                            "data_models_count": len(spec_output.data_models),
                            "security_requirements_count": len(
                                spec_output.security_requirements
                            ),
                        },
                    }
                ],
                metadata={
                    "api_endpoints_count": len(spec_output.api_specifications),
                    "data_models_count": len(spec_output.data_models),
                    "security_requirements_count": len(
                        spec_output.security_requirements
                    ),
                },
            )

        except Exception as e:
            self.logger.error(
                f"Failed to create specifications: {str(e)}", exc_info=True
            )
            return AgentResponse(
                success=False,
                content=f"Failed to create specifications: {str(e)}",
                errors=[str(e)],
            )

    async def _create_tech_specifications(
        self,
        task_execution: TaskExecution,
        inputs: Dict[str, Any],
    ) -> AgentResponse:
        """Create technology-specific specifications.

        Args:
            task_execution: The task execution instance
            inputs: Input data containing requirements and specifications

        Returns:
            AgentResponse with tech specification results
        """
        requirements = inputs.get("requirements", {})
        specifications = inputs.get("specifications", {})

        try:
            # Create technology-specific specifications
            tech_spec_output = TechSpecOutput(
                technology_stack={
                    "framework": "FastAPI",
                    "database": "SQLite",
                    "authentication": "JWT",
                    "testing": "Pytest",
                    "migrations": "Alembic",
                    "validation": "Pydantic",
                    "documentation": "OpenAPI/Swagger",
                    "containerization": "Docker",
                },
                architecture_patterns=[
                    "Layered Architecture (Controller-Service-Repository)",
                    "Dependency Injection",
                    "Repository Pattern",
                    "Factory Pattern",
                    "Observer Pattern for events",
                ],
                design_patterns=[
                    "Model-View-Controller (MVC)",
                    "Data Transfer Object (DTO)",
                    "Singleton for configuration",
                    "Strategy for different authentication methods",
                    "Template Method for common operations",
                ],
                database_schema={
                    "tables": [
                        {
                            "name": "users",
                            "columns": [
                                {"name": "id", "type": "UUID", "primary_key": True},
                                {
                                    "name": "email",
                                    "type": "VARCHAR(255)",
                                    "unique": True,
                                    "not_null": True,
                                },
                                {
                                    "name": "hashed_password",
                                    "type": "VARCHAR(255)",
                                    "not_null": True,
                                },
                                {"name": "full_name", "type": "VARCHAR(255)"},
                                {
                                    "name": "is_active",
                                    "type": "BOOLEAN",
                                    "default": True,
                                },
                                {
                                    "name": "created_at",
                                    "type": "TIMESTAMP",
                                    "default": "CURRENT_TIMESTAMP",
                                },
                                {
                                    "name": "updated_at",
                                    "type": "TIMESTAMP",
                                    "default": "CURRENT_TIMESTAMP",
                                },
                            ],
                            "indexes": [
                                {"name": "idx_users_email", "columns": ["email"]},
                                {
                                    "name": "idx_users_created_at",
                                    "columns": ["created_at"],
                                },
                            ],
                        },
                        {
                            "name": "items",
                            "columns": [
                                {"name": "id", "type": "UUID", "primary_key": True},
                                {
                                    "name": "title",
                                    "type": "VARCHAR(255)",
                                    "not_null": True,
                                },
                                {"name": "description", "type": "TEXT"},
                                {"name": "price", "type": "DECIMAL(10,2)"},
                                {"name": "owner_id", "type": "UUID", "not_null": True},
                                {
                                    "name": "created_at",
                                    "type": "TIMESTAMP",
                                    "default": "CURRENT_TIMESTAMP",
                                },
                                {
                                    "name": "updated_at",
                                    "type": "TIMESTAMP",
                                    "default": "CURRENT_TIMESTAMP",
                                },
                            ],
                            "foreign_keys": [
                                {
                                    "column": "owner_id",
                                    "references": "users(id)",
                                    "on_delete": "CASCADE",
                                }
                            ],
                            "indexes": [
                                {"name": "idx_items_owner_id", "columns": ["owner_id"]},
                                {
                                    "name": "idx_items_created_at",
                                    "columns": ["created_at"],
                                },
                            ],
                        },
                    ],
                    "migrations": [
                        {
                            "version": "001_initial",
                            "description": "Create users and items tables",
                            "upgrade": [
                                "CREATE TABLE users (...)",
                                "CREATE TABLE items (...)",
                            ],
                            "downgrade": ["DROP TABLE items", "DROP TABLE users"],
                        }
                    ],
                },
                api_design={
                    "version": "v1",
                    "base_path": "/api/v1",
                    "authentication": "Bearer token in Authorization header",
                    "content_type": "application/json",
                    "response_format": {
                        "success": {
                            "data": "response_data",
                            "message": "optional_message",
                        },
                        "error": {
                            "error": "error_message",
                            "details": "optional_details",
                        },
                    },
                    "pagination": {
                        "page": "integer (default: 1)",
                        "size": "integer (default: 20, max: 100)",
                        "response": {
                            "items": "array",
                            "total": "integer",
                            "page": "integer",
                            "pages": "integer",
                        },
                    },
                },
                deployment_config={
                    "environment": "production",
                    "server": "uvicorn",
                    "workers": 4,
                    "host": "0.0.0.0",
                    "port": 8000,
                    "reload": False,
                    "log_level": "info",
                    "database_url": "sqlite:///./app.db",
                    "secret_key": "environment_variable",
                    "cors_origins": ["http://localhost:3000"],
                    "rate_limit": {"requests_per_minute": 60, "burst_size": 10},
                },
                development_guidelines=[
                    "Follow PEP 8 coding standards",
                    "Use type hints for all functions",
                    "Write comprehensive docstrings",
                    "Implement comprehensive error handling",
                    "Use async/await for I/O operations",
                    "Write unit tests for all functions",
                    "Achieve 85%+ test coverage",
                    "Use dependency injection for services",
                    "Implement proper logging",
                    "Use environment variables for configuration",
                ],
            )

            # Log decision
            self._log_decision(
                task_execution,
                f"Created tech specifications with {len(tech_spec_output.architecture_patterns)} architecture patterns",
                confidence=0.9,
                params={"patterns_count": len(tech_spec_output.architecture_patterns)},
            )

            return AgentResponse(
                success=True,
                content=tech_spec_output.model_dump_json(indent=2),
                artifacts=[
                    {
                        "type": "documentation",
                        "content": tech_spec_output.model_dump_json(indent=2),
                        "metadata": {
                            "architecture_patterns_count": len(
                                tech_spec_output.architecture_patterns
                            ),
                            "design_patterns_count": len(
                                tech_spec_output.design_patterns
                            ),
                            "database_tables_count": len(
                                tech_spec_output.database_schema["tables"]
                            ),
                        },
                    }
                ],
                metadata={
                    "architecture_patterns_count": len(
                        tech_spec_output.architecture_patterns
                    ),
                    "design_patterns_count": len(tech_spec_output.design_patterns),
                    "database_tables_count": len(
                        tech_spec_output.database_schema["tables"]
                    ),
                },
            )

        except Exception as e:
            self.logger.error(
                f"Failed to create tech specifications: {str(e)}", exc_info=True
            )
            return AgentResponse(
                success=False,
                content=f"Failed to create tech specifications: {str(e)}",
                errors=[str(e)],
            )
