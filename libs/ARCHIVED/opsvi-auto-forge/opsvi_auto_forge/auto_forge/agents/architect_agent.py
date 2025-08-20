"""Architect agent for the autonomous software factory."""

import logging
from typing import Any, Dict, List, Optional

from opsvi_auto_forge.agents.base_agent import AgentResponse, BaseAgent
from opsvi_auto_forge.application.orchestrator.task_models import TaskExecution
from opsvi_auto_forge.config.models import AgentRole
from pydantic import BaseModel, Field


class ArchitectureOutput(BaseModel):
    """Structured output for architecture design."""

    system_overview: str = Field(
        ..., description="High-level system architecture overview"
    )
    components: List[Dict[str, Any]] = Field(
        ..., description="System components and their responsibilities"
    )
    layers: List[Dict[str, Any]] = Field(
        ..., description="Architecture layers and their purposes"
    )
    patterns: List[str] = Field(..., description="Architecture patterns used")
    interfaces: List[Dict[str, Any]] = Field(
        ..., description="Component interfaces and contracts"
    )
    deployment_model: Dict[str, Any] = Field(..., description="Deployment architecture")
    scalability_approach: str = Field(..., description="Scalability strategy")
    security_architecture: List[str] = Field(
        ..., description="Security measures and patterns"
    )


class DataFlowOutput(BaseModel):
    """Structured output for data flow design."""

    data_flows: List[Dict[str, Any]] = Field(
        ..., description="Data flow diagrams and descriptions"
    )
    data_stores: List[Dict[str, Any]] = Field(
        ..., description="Data storage components"
    )
    data_transformations: List[Dict[str, Any]] = Field(
        ..., description="Data transformation processes"
    )
    integration_points: List[Dict[str, Any]] = Field(
        ..., description="External integration points"
    )
    data_security: List[str] = Field(..., description="Data security measures")
    data_validation: List[Dict[str, Any]] = Field(
        ..., description="Data validation rules"
    )


class DatabaseSchemaOutput(BaseModel):
    """Structured output for database schema design."""

    tables: List[Dict[str, Any]] = Field(
        ..., description="Database tables with columns and constraints"
    )
    relationships: List[Dict[str, Any]] = Field(
        ..., description="Table relationships and foreign keys"
    )
    indexes: List[Dict[str, Any]] = Field(
        ..., description="Database indexes for performance"
    )
    constraints: List[Dict[str, Any]] = Field(..., description="Database constraints")
    migrations: List[Dict[str, Any]] = Field(
        ..., description="Database migration scripts"
    )
    data_seeding: List[Dict[str, Any]] = Field(
        default_factory=list, description="Initial data seeding"
    )


class CICDOutput(BaseModel):
    """Structured output for CI/CD pipeline design."""

    pipeline_stages: List[Dict[str, Any]] = Field(
        ..., description="CI/CD pipeline stages"
    )
    build_configuration: Dict[str, Any] = Field(..., description="Build configuration")
    test_strategy: Dict[str, Any] = Field(
        ..., description="Testing strategy and configuration"
    )
    deployment_strategy: Dict[str, Any] = Field(..., description="Deployment strategy")
    quality_gates: List[Dict[str, Any]] = Field(
        ..., description="Quality gates and checks"
    )
    monitoring: List[Dict[str, Any]] = Field(
        ..., description="Monitoring and alerting configuration"
    )


class ArchitectAgent(BaseAgent):
    """Agent responsible for architecture design tasks."""

    def __init__(
        self,
        neo4j_client=None,
        logger: Optional[logging.Logger] = None,
        prompt_gateway=None,
        context_store=None,
    ):
        """Initialize the architect agent."""
        super().__init__(
            AgentRole.ARCHITECT, neo4j_client, logger, prompt_gateway, context_store
        )

    async def execute(
        self,
        task_execution: TaskExecution,
        inputs: Dict[str, Any],
    ) -> AgentResponse:
        """Execute architecture design task.

        Args:
            task_execution: The task execution instance
            inputs: Input data containing requirements and specifications

        Returns:
            AgentResponse with architecture design results
        """
        task_name = task_execution.definition.name

        if task_name == "arch":
            return await self._design_architecture(task_execution, inputs)
        elif task_name == "dataflow":
            return await self._design_data_flow(task_execution, inputs)
        elif task_name == "dbschema":
            return await self._design_database_schema(task_execution, inputs)
        elif task_name == "cicd":
            return await self._design_cicd_pipeline(task_execution, inputs)
        else:
            return AgentResponse(
                success=False,
                content=f"Unknown architecture task: {task_name}",
                errors=[f"Unsupported task type: {task_name}"],
            )

    async def _design_architecture(
        self,
        task_execution: TaskExecution,
        inputs: Dict[str, Any],
    ) -> AgentResponse:
        """Design system architecture.

        Args:
            task_execution: The task execution instance
            inputs: Input data containing requirements and specifications

        Returns:
            AgentResponse with architecture design results
        """
        requirements = inputs.get("requirements", {})
        specifications = inputs.get("specifications", {})

        try:
            # For now, create structured architecture without AI model call
            # In production, this would use the o4-mini model for reasoning
            architecture_output = ArchitectureOutput(
                system_overview="""
                The system follows a layered architecture pattern with clear separation of concerns:
                - Presentation Layer: FastAPI application with REST API endpoints
                - Business Logic Layer: Service classes handling business rules
                - Data Access Layer: Repository pattern for database operations
                - Infrastructure Layer: Database, authentication, and external services

                The architecture emphasizes modularity, testability, and maintainability.
                """,
                components=[
                    {
                        "name": "FastAPI Application",
                        "type": "Web Framework",
                        "responsibilities": [
                            "Handle HTTP requests and responses",
                            "Route requests to appropriate handlers",
                            "Validate input data using Pydantic models",
                            "Generate OpenAPI documentation",
                        ],
                        "dependencies": ["Business Services", "Authentication Service"],
                    },
                    {
                        "name": "Authentication Service",
                        "type": "Security Component",
                        "responsibilities": [
                            "User registration and login",
                            "JWT token generation and validation",
                            "Password hashing and verification",
                            "User session management",
                        ],
                        "dependencies": ["User Repository"],
                    },
                    {
                        "name": "Item Service",
                        "type": "Business Logic",
                        "responsibilities": [
                            "Item CRUD operations",
                            "Business rule validation",
                            "Data transformation",
                            "Error handling",
                        ],
                        "dependencies": ["Item Repository", "User Service"],
                    },
                    {
                        "name": "User Repository",
                        "type": "Data Access",
                        "responsibilities": [
                            "User data persistence",
                            "Database queries for users",
                            "User data validation",
                            "Connection management",
                        ],
                        "dependencies": ["SQLite Database"],
                    },
                    {
                        "name": "Item Repository",
                        "type": "Data Access",
                        "responsibilities": [
                            "Item data persistence",
                            "Database queries for items",
                            "Item data validation",
                            "Connection management",
                        ],
                        "dependencies": ["SQLite Database"],
                    },
                    {
                        "name": "SQLite Database",
                        "type": "Data Storage",
                        "responsibilities": [
                            "Data persistence",
                            "ACID transactions",
                            "Data integrity",
                            "Query optimization",
                        ],
                        "dependencies": [],
                    },
                ],
                layers=[
                    {
                        "name": "Presentation Layer",
                        "components": ["FastAPI Application"],
                        "purpose": "Handle HTTP requests and provide API interface",
                    },
                    {
                        "name": "Business Logic Layer",
                        "components": ["Authentication Service", "Item Service"],
                        "purpose": "Implement business rules and orchestrate operations",
                    },
                    {
                        "name": "Data Access Layer",
                        "components": ["User Repository", "Item Repository"],
                        "purpose": "Abstract database operations and data persistence",
                    },
                    {
                        "name": "Infrastructure Layer",
                        "components": ["SQLite Database"],
                        "purpose": "Provide foundational services and data storage",
                    },
                ],
                patterns=[
                    "Layered Architecture",
                    "Repository Pattern",
                    "Dependency Injection",
                    "Service Layer Pattern",
                    "Factory Pattern",
                    "Observer Pattern",
                ],
                interfaces=[
                    {
                        "name": "UserService",
                        "methods": [
                            "create_user(email: str, password: str) -> User",
                            "authenticate_user(email: str, password: str) -> Optional[User]",
                            "get_user_by_id(user_id: UUID) -> Optional[User]",
                        ],
                    },
                    {
                        "name": "ItemService",
                        "methods": [
                            "create_item(item_data: ItemCreate, user_id: UUID) -> Item",
                            "get_items_by_user(user_id: UUID) -> List[Item]",
                            "update_item(item_id: UUID, item_data: ItemUpdate, user_id: UUID) -> Optional[Item]",
                            "delete_item(item_id: UUID, user_id: UUID) -> bool",
                        ],
                    },
                    {
                        "name": "UserRepository",
                        "methods": [
                            "create(user: User) -> User",
                            "get_by_id(user_id: UUID) -> Optional[User]",
                            "get_by_email(email: str) -> Optional[User]",
                            "update(user: User) -> User",
                        ],
                    },
                ],
                deployment_model={
                    "type": "Single Server",
                    "components": [
                        "FastAPI application running on uvicorn",
                        "SQLite database file",
                        "Static files and assets",
                    ],
                    "scaling": "Vertical scaling (more CPU/memory)",
                    "load_balancing": "Not required for single server",
                    "monitoring": "Application logs and health checks",
                },
                scalability_approach="""
                The system is designed for vertical scaling initially:
                - Single server deployment with resource scaling
                - Database connection pooling for better performance
                - Caching strategies for frequently accessed data
                - Async/await patterns for better concurrency

                Future horizontal scaling considerations:
                - Separate database server
                - Load balancer for multiple application instances
                - Microservices decomposition if needed
                """,
                security_architecture=[
                    "JWT-based authentication with secure token handling",
                    "Password hashing using bcrypt with salt",
                    "Input validation and sanitization",
                    "SQL injection prevention through parameterized queries",
                    "CORS configuration for cross-origin requests",
                    "Rate limiting on authentication endpoints",
                    "Secure headers and HTTPS enforcement",
                    "Audit logging for security events",
                ],
            )

            # Log decision
            self._log_decision(
                task_execution,
                f"Designed architecture with {len(architecture_output.components)} components",
                confidence=0.9,
                params={"patterns_count": len(architecture_output.patterns)},
            )

            return AgentResponse(
                success=True,
                content=architecture_output.model_dump_json(indent=2),
                artifacts=[
                    {
                        "type": "architecture",
                        "content": architecture_output.model_dump_json(indent=2),
                        "metadata": {
                            "components_count": len(architecture_output.components),
                            "layers_count": len(architecture_output.layers),
                            "patterns_count": len(architecture_output.patterns),
                        },
                    }
                ],
                metadata={
                    "components_count": len(architecture_output.components),
                    "layers_count": len(architecture_output.layers),
                    "patterns_count": len(architecture_output.patterns),
                },
            )

        except Exception as e:
            self.logger.error(f"Failed to design architecture: {str(e)}", exc_info=True)
            return AgentResponse(
                success=False,
                content=f"Failed to design architecture: {str(e)}",
                errors=[str(e)],
            )

    async def _design_data_flow(
        self,
        task_execution: TaskExecution,
        inputs: Dict[str, Any],
    ) -> AgentResponse:
        """Design data flow and integration patterns.

        Args:
            task_execution: The task execution instance
            inputs: Input data containing architecture and specifications

        Returns:
            AgentResponse with data flow design results
        """
        architecture = inputs.get("architecture", {})
        specifications = inputs.get("specifications", {})

        try:
            # Create data flow design
            data_flow_output = DataFlowOutput(
                data_flows=[
                    {
                        "name": "User Registration Flow",
                        "description": "Flow for new user registration",
                        "steps": [
                            "Client sends registration request with email/password",
                            "API validates input data",
                            "Password is hashed using bcrypt",
                            "User record is created in database",
                            "Success response is returned to client",
                        ],
                        "data_entities": ["User", "Password Hash"],
                        "error_handling": [
                            "Email validation errors",
                            "Password strength errors",
                            "Duplicate email errors",
                        ],
                    },
                    {
                        "name": "User Authentication Flow",
                        "description": "Flow for user login and authentication",
                        "steps": [
                            "Client sends login request with credentials",
                            "API validates input data",
                            "User is retrieved from database by email",
                            "Password is verified against hash",
                            "JWT token is generated and returned",
                            "Token is stored by client for subsequent requests",
                        ],
                        "data_entities": ["User", "JWT Token"],
                        "error_handling": [
                            "Invalid credentials",
                            "User not found",
                            "Account disabled",
                        ],
                    },
                    {
                        "name": "Item Management Flow",
                        "description": "Flow for item CRUD operations",
                        "steps": [
                            "Client sends authenticated request with JWT token",
                            "API validates JWT token and extracts user ID",
                            "Business logic processes the request",
                            "Database operations are performed",
                            "Response is returned to client",
                        ],
                        "data_entities": ["Item", "User", "JWT Token"],
                        "error_handling": [
                            "Authentication errors",
                            "Authorization errors",
                            "Validation errors",
                        ],
                    },
                ],
                data_stores=[
                    {
                        "name": "SQLite Database",
                        "type": "Relational Database",
                        "tables": ["users", "items"],
                        "purpose": "Primary data persistence",
                        "access_patterns": [
                            "CRUD operations",
                            "Query by user",
                            "Query by item",
                        ],
                    },
                    {
                        "name": "JWT Token Store",
                        "type": "Client-side Storage",
                        "purpose": "Temporary authentication state",
                        "lifetime": "30 minutes",
                        "security": "Signed and encrypted tokens",
                    },
                ],
                data_transformations=[
                    {
                        "name": "Password Hashing",
                        "input": "Plain text password",
                        "output": "Bcrypt hash with salt",
                        "algorithm": "bcrypt",
                        "security": "One-way hashing with salt",
                    },
                    {
                        "name": "JWT Token Generation",
                        "input": "User ID and metadata",
                        "output": "Signed JWT token",
                        "algorithm": "HS256",
                        "security": "HMAC with secret key",
                    },
                    {
                        "name": "Input Validation",
                        "input": "Raw user input",
                        "output": "Validated and sanitized data",
                        "validation": "Pydantic models",
                        "security": "Type checking and sanitization",
                    },
                ],
                integration_points=[
                    {
                        "name": "Database Integration",
                        "type": "Internal",
                        "protocol": "SQL",
                        "purpose": "Data persistence",
                        "security": "Connection pooling, parameterized queries",
                    },
                    {
                        "name": "Client Integration",
                        "type": "External",
                        "protocol": "HTTP/REST",
                        "purpose": "API communication",
                        "security": "HTTPS, JWT authentication, CORS",
                    },
                ],
                data_security=[
                    "All passwords are hashed using bcrypt with salt",
                    "JWT tokens are signed with secure secret key",
                    "Database connections use parameterized queries",
                    "Input data is validated and sanitized",
                    "Sensitive data is not logged",
                    "HTTPS is enforced for all communications",
                ],
                data_validation=[
                    {
                        "entity": "User",
                        "rules": [
                            "Email must be valid format and unique",
                            "Password must be at least 8 characters",
                            "Full name is optional but must be string if provided",
                        ],
                    },
                    {
                        "entity": "Item",
                        "rules": [
                            "Title is required and must be non-empty string",
                            "Description is optional",
                            "Price must be positive number if provided",
                            "Owner ID must be valid UUID",
                        ],
                    },
                    {
                        "entity": "JWT Token",
                        "rules": [
                            "Token must be valid format",
                            "Token must not be expired",
                            "Token must be signed with correct secret",
                        ],
                    },
                ],
            )

            # Log decision
            self._log_decision(
                task_execution,
                f"Designed data flow with {len(data_flow_output.data_flows)} flows",
                confidence=0.9,
                params={"flows_count": len(data_flow_output.data_flows)},
            )

            return AgentResponse(
                success=True,
                content=data_flow_output.model_dump_json(indent=2),
                artifacts=[
                    {
                        "type": "analysis",
                        "content": data_flow_output.model_dump_json(indent=2),
                        "metadata": {
                            "flows_count": len(data_flow_output.data_flows),
                            "stores_count": len(data_flow_output.data_stores),
                            "transformations_count": len(
                                data_flow_output.data_transformations
                            ),
                        },
                    }
                ],
                metadata={
                    "flows_count": len(data_flow_output.data_flows),
                    "stores_count": len(data_flow_output.data_stores),
                    "transformations_count": len(data_flow_output.data_transformations),
                },
            )

        except Exception as e:
            self.logger.error(f"Failed to design data flow: {str(e)}", exc_info=True)
            return AgentResponse(
                success=False,
                content=f"Failed to design data flow: {str(e)}",
                errors=[str(e)],
            )

    async def _design_database_schema(
        self,
        task_execution: TaskExecution,
        inputs: Dict[str, Any],
    ) -> AgentResponse:
        """Design database schema.

        Args:
            task_execution: The task execution instance
            inputs: Input data containing specifications and requirements

        Returns:
            AgentResponse with database schema design results
        """
        specifications = inputs.get("specifications", {})
        requirements = inputs.get("requirements", {})

        try:
            # Create database schema design
            db_schema_output = DatabaseSchemaOutput(
                tables=[
                    {
                        "name": "users",
                        "description": "User accounts and authentication data",
                        "columns": [
                            {
                                "name": "id",
                                "type": "UUID",
                                "constraints": ["PRIMARY KEY", "NOT NULL"],
                                "default": "gen_random_uuid()",
                                "description": "Unique user identifier",
                            },
                            {
                                "name": "email",
                                "type": "VARCHAR(255)",
                                "constraints": ["UNIQUE", "NOT NULL"],
                                "description": "User email address (unique)",
                            },
                            {
                                "name": "hashed_password",
                                "type": "VARCHAR(255)",
                                "constraints": ["NOT NULL"],
                                "description": "Bcrypt hashed password",
                            },
                            {
                                "name": "full_name",
                                "type": "VARCHAR(255)",
                                "constraints": [],
                                "description": "User's full name",
                            },
                            {
                                "name": "is_active",
                                "type": "BOOLEAN",
                                "constraints": ["NOT NULL"],
                                "default": "TRUE",
                                "description": "Account active status",
                            },
                            {
                                "name": "created_at",
                                "type": "TIMESTAMP",
                                "constraints": ["NOT NULL"],
                                "default": "CURRENT_TIMESTAMP",
                                "description": "Account creation timestamp",
                            },
                            {
                                "name": "updated_at",
                                "type": "TIMESTAMP",
                                "constraints": ["NOT NULL"],
                                "default": "CURRENT_TIMESTAMP",
                                "description": "Last update timestamp",
                            },
                        ],
                    },
                    {
                        "name": "items",
                        "description": "User items and data",
                        "columns": [
                            {
                                "name": "id",
                                "type": "UUID",
                                "constraints": ["PRIMARY KEY", "NOT NULL"],
                                "default": "gen_random_uuid()",
                                "description": "Unique item identifier",
                            },
                            {
                                "name": "title",
                                "type": "VARCHAR(255)",
                                "constraints": ["NOT NULL"],
                                "description": "Item title",
                            },
                            {
                                "name": "description",
                                "type": "TEXT",
                                "constraints": [],
                                "description": "Item description",
                            },
                            {
                                "name": "price",
                                "type": "DECIMAL(10,2)",
                                "constraints": ["CHECK (price >= 0)"],
                                "description": "Item price (positive number)",
                            },
                            {
                                "name": "owner_id",
                                "type": "UUID",
                                "constraints": ["NOT NULL", "FOREIGN KEY"],
                                "description": "Reference to user who owns this item",
                            },
                            {
                                "name": "created_at",
                                "type": "TIMESTAMP",
                                "constraints": ["NOT NULL"],
                                "default": "CURRENT_TIMESTAMP",
                                "description": "Item creation timestamp",
                            },
                            {
                                "name": "updated_at",
                                "type": "TIMESTAMP",
                                "constraints": ["NOT NULL"],
                                "default": "CURRENT_TIMESTAMP",
                                "description": "Last update timestamp",
                            },
                        ],
                    },
                ],
                relationships=[
                    {
                        "name": "user_items",
                        "type": "One-to-Many",
                        "parent_table": "users",
                        "child_table": "items",
                        "parent_column": "id",
                        "child_column": "owner_id",
                        "on_delete": "CASCADE",
                        "on_update": "CASCADE",
                    }
                ],
                indexes=[
                    {
                        "name": "idx_users_email",
                        "table": "users",
                        "columns": ["email"],
                        "type": "UNIQUE",
                        "purpose": "Fast email lookups for authentication",
                    },
                    {
                        "name": "idx_users_created_at",
                        "table": "users",
                        "columns": ["created_at"],
                        "type": "BTREE",
                        "purpose": "Fast user creation date queries",
                    },
                    {
                        "name": "idx_items_owner_id",
                        "table": "items",
                        "columns": ["owner_id"],
                        "type": "BTREE",
                        "purpose": "Fast item queries by owner",
                    },
                    {
                        "name": "idx_items_created_at",
                        "table": "items",
                        "columns": ["created_at"],
                        "type": "BTREE",
                        "purpose": "Fast item creation date queries",
                    },
                ],
                constraints=[
                    {
                        "name": "chk_items_price_positive",
                        "table": "items",
                        "type": "CHECK",
                        "definition": "price >= 0",
                        "purpose": "Ensure item prices are non-negative",
                    },
                    {
                        "name": "fk_items_owner",
                        "table": "items",
                        "type": "FOREIGN KEY",
                        "definition": "owner_id REFERENCES users(id) ON DELETE CASCADE",
                        "purpose": "Ensure referential integrity between items and users",
                    },
                ],
                migrations=[
                    {
                        "version": "001_initial_schema",
                        "description": "Create initial database schema",
                        "upgrade": [
                            """
                            CREATE TABLE users (
                                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                                email VARCHAR(255) UNIQUE NOT NULL,
                                hashed_password VARCHAR(255) NOT NULL,
                                full_name VARCHAR(255),
                                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                            );
                            """,
                            """
                            CREATE TABLE items (
                                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                                title VARCHAR(255) NOT NULL,
                                description TEXT,
                                price DECIMAL(10,2) CHECK (price >= 0),
                                owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                            );
                            """,
                            "CREATE UNIQUE INDEX idx_users_email ON users(email);",
                            "CREATE INDEX idx_users_created_at ON users(created_at);",
                            "CREATE INDEX idx_items_owner_id ON items(owner_id);",
                            "CREATE INDEX idx_items_created_at ON items(created_at);",
                        ],
                        "downgrade": ["DROP TABLE items;", "DROP TABLE users;"],
                    }
                ],
                data_seeding=[
                    {
                        "table": "users",
                        "description": "Create test user for development",
                        "data": [
                            {
                                "email": "test@example.com",
                                "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
                                "full_name": "Test User",
                                "is_active": True,
                            }
                        ],
                    }
                ],
            )

            # Log decision
            self._log_decision(
                task_execution,
                f"Designed database schema with {len(db_schema_output.tables)} tables",
                confidence=0.9,
                params={"tables_count": len(db_schema_output.tables)},
            )

            return AgentResponse(
                success=True,
                content=db_schema_output.model_dump_json(indent=2),
                artifacts=[
                    {
                        "type": "config",
                        "content": db_schema_output.model_dump_json(indent=2),
                        "metadata": {
                            "tables_count": len(db_schema_output.tables),
                            "relationships_count": len(db_schema_output.relationships),
                            "indexes_count": len(db_schema_output.indexes),
                        },
                    }
                ],
                metadata={
                    "tables_count": len(db_schema_output.tables),
                    "relationships_count": len(db_schema_output.relationships),
                    "indexes_count": len(db_schema_output.indexes),
                },
            )

        except Exception as e:
            self.logger.error(
                f"Failed to design database schema: {str(e)}", exc_info=True
            )
            return AgentResponse(
                success=False,
                content=f"Failed to design database schema: {str(e)}",
                errors=[str(e)],
            )

    async def _design_cicd_pipeline(
        self,
        task_execution: TaskExecution,
        inputs: Dict[str, Any],
    ) -> AgentResponse:
        """Design CI/CD pipeline.

        Args:
            task_execution: The task execution instance
            inputs: Input data containing architecture and requirements

        Returns:
            AgentResponse with CI/CD pipeline design results
        """
        architecture = inputs.get("architecture", {})
        requirements = inputs.get("requirements", {})

        try:
            # Create CI/CD pipeline design
            cicd_output = CICDOutput(
                pipeline_stages=[
                    {
                        "name": "Code Quality",
                        "description": "Static analysis and code quality checks",
                        "tools": ["ruff", "mypy", "bandit"],
                        "exit_criteria": [
                            "No linting errors",
                            "Type checking passes",
                            "No security issues",
                        ],
                        "parallel": True,
                    },
                    {
                        "name": "Unit Tests",
                        "description": "Run unit tests and measure coverage",
                        "tools": ["pytest", "coverage"],
                        "exit_criteria": ["All tests pass", "Coverage >= 85%"],
                        "parallel": True,
                    },
                    {
                        "name": "Integration Tests",
                        "description": "Run integration tests",
                        "tools": ["pytest", "testcontainers"],
                        "exit_criteria": ["All integration tests pass"],
                        "parallel": False,
                    },
                    {
                        "name": "Security Scan",
                        "description": "Security vulnerability scanning",
                        "tools": ["trivy", "bandit"],
                        "exit_criteria": ["No HIGH/CRITICAL vulnerabilities"],
                        "parallel": True,
                    },
                    {
                        "name": "Build",
                        "description": "Build application and Docker image",
                        "tools": ["docker", "docker-compose"],
                        "exit_criteria": ["Docker image builds successfully"],
                        "parallel": False,
                    },
                    {
                        "name": "Deploy",
                        "description": "Deploy to staging environment",
                        "tools": ["docker-compose", "docker"],
                        "exit_criteria": [
                            "Application starts successfully",
                            "Health checks pass",
                        ],
                        "parallel": False,
                    },
                ],
                build_configuration={
                    "dockerfile": "Dockerfile",
                    "context": ".",
                    "image_name": "fastapi-app",
                    "image_tag": "latest",
                    "build_args": {"PYTHON_VERSION": "3.12", "APP_ENV": "production"},
                    "multi_stage": True,
                    "optimization": {
                        "cache_layers": True,
                        "parallel_builds": True,
                        "security_scan": True,
                    },
                },
                test_strategy={
                    "unit_tests": {
                        "framework": "pytest",
                        "coverage_target": 85,
                        "parallel_execution": True,
                        "test_discovery": "tests/",
                        "reports": ["coverage.xml", "coverage.html"],
                    },
                    "integration_tests": {
                        "framework": "pytest",
                        "database": "testcontainers",
                        "parallel_execution": False,
                        "test_discovery": "tests/integration/",
                    },
                    "e2e_tests": {
                        "framework": "pytest",
                        "browser": "playwright",
                        "parallel_execution": True,
                        "test_discovery": "tests/e2e/",
                    },
                },
                deployment_strategy={
                    "environments": ["staging", "production"],
                    "strategy": "Blue-Green Deployment",
                    "rollback": "Automatic on failure",
                    "health_checks": [
                        "HTTP GET /health",
                        "Database connectivity",
                        "Service dependencies",
                    ],
                    "monitoring": [
                        "Application metrics",
                        "Error tracking",
                        "Performance monitoring",
                    ],
                },
                quality_gates=[
                    {
                        "name": "Code Quality",
                        "checks": [
                            "ruff linting passes",
                            "mypy type checking passes",
                            "bandit security scan passes",
                        ],
                        "threshold": "All checks must pass",
                    },
                    {
                        "name": "Test Coverage",
                        "checks": [
                            "Unit test coverage >= 85%",
                            "All unit tests pass",
                            "All integration tests pass",
                        ],
                        "threshold": "All checks must pass",
                    },
                    {
                        "name": "Security",
                        "checks": [
                            "No HIGH/CRITICAL vulnerabilities",
                            "No secrets in code",
                            "Dependency security scan passes",
                        ],
                        "threshold": "All checks must pass",
                    },
                    {
                        "name": "Performance",
                        "checks": [
                            "Build time < 5 minutes",
                            "Test execution time < 10 minutes",
                            "Application startup time < 30 seconds",
                        ],
                        "threshold": "All checks must pass",
                    },
                ],
                monitoring=[
                    {
                        "name": "Application Metrics",
                        "tools": ["prometheus", "grafana"],
                        "metrics": [
                            "Request rate and latency",
                            "Error rates",
                            "Database connection pool",
                            "Memory and CPU usage",
                        ],
                    },
                    {
                        "name": "Logging",
                        "tools": ["structured logging", "log aggregation"],
                        "levels": ["INFO", "WARNING", "ERROR"],
                        "format": "JSON with correlation IDs",
                    },
                    {
                        "name": "Alerting",
                        "tools": ["prometheus alertmanager"],
                        "alerts": [
                            "High error rate",
                            "High latency",
                            "Service down",
                            "Database connectivity issues",
                        ],
                    },
                ],
            )

            # Log decision
            self._log_decision(
                task_execution,
                f"Designed CI/CD pipeline with {len(cicd_output.pipeline_stages)} stages",
                confidence=0.9,
                params={"stages_count": len(cicd_output.pipeline_stages)},
            )

            return AgentResponse(
                success=True,
                content=cicd_output.model_dump_json(indent=2),
                artifacts=[
                    {
                        "type": "config",
                        "content": cicd_output.model_dump_json(indent=2),
                        "metadata": {
                            "stages_count": len(cicd_output.pipeline_stages),
                            "quality_gates_count": len(cicd_output.quality_gates),
                            "monitoring_count": len(cicd_output.monitoring),
                        },
                    }
                ],
                metadata={
                    "stages_count": len(cicd_output.pipeline_stages),
                    "quality_gates_count": len(cicd_output.quality_gates),
                    "monitoring_count": len(cicd_output.monitoring),
                },
            )

        except Exception as e:
            self.logger.error(
                f"Failed to design CI/CD pipeline: {str(e)}", exc_info=True
            )
            return AgentResponse(
                success=False,
                content=f"Failed to design CI/CD pipeline: {str(e)}",
                errors=[str(e)],
            )
