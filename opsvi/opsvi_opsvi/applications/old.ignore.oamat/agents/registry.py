"""
OAMAT Agent Registry and Constants

Contains all agent definitions, tool registries, workflow patterns,
and operational guidelines for the OAMAT system.
"""

# Core System Understanding
SYSTEM_IDENTITY = """
You are a workflow orchestration specialist who transforms user requests into actionable, executable plans.

CORE APPROACH:
• Analyze requests thoroughly to understand true intent and requirements
• Ask strategic clarifying questions when genuinely needed to avoid wrong assumptions
• Break complex requests into logical, manageable steps
• Assign appropriate specialists to tasks based on their expertise
• Ensure practical, production-ready solutions with proper quality standards

COMMUNICATION STYLE:
• Professional and competent, with clear explanations
• Ask focused questions that distinguish between fundamentally different approaches
• Provide reasoning for recommendations and decisions
• Adapt technical depth to match user expertise level

QUALITY STANDARDS:
• Deliver complete, executable solutions that work as intended
• Include proper error handling, testing, and documentation
• Follow industry best practices and modern development standards
• Ensure security, performance, and maintainability considerations
"""

# Enhanced Agent Registry with Detailed Capabilities
AGENT_REGISTRY = {
    "researcher": {
        "primary_function": "Comprehensive research and knowledge gathering",
        "capabilities": [
            "Multi-source research and analysis",
            "Academic and technical literature review",
            "Market research and competitive analysis",
            "Technology trend analysis",
            "Best practice identification",
            "Knowledge base mining and synthesis",
            "Real-time information gathering",
            "Research report generation",
        ],
        "inputs": {
            "research_topic": "string - topic to research",
            "research_depth": "string - depth level (basic, comprehensive, expert)",
            "sources": "list - research sources to use",
            "constraints": "dict - research constraints and requirements",
        },
        "outputs": {
            "research_report": "comprehensive research findings",
            "source_analysis": "evaluation of sources and credibility",
            "recommendations": "actionable insights and recommendations",
            "knowledge_graph": "structured knowledge representation",
            "bibliography": "annotated source references",
        },
        "best_for": [
            "Technology landscape analysis",
            "Competitive intelligence",
            "Academic literature review",
            "Market research and trends",
            "Knowledge synthesis and insights",
        ],
        "execution_time": "3-15 minutes",
        "dependencies": [
            "knowledge_search",
            "web_search",
            "academic_search",
            "mcp_research_tools",
        ],
    },
    "requirements_analyst": {
        "primary_function": "Requirements gathering, analysis, and specification",
        "capabilities": [
            "Stakeholder requirement elicitation",
            "Functional and non-functional requirement analysis",
            "User story creation and prioritization",
            "Acceptance criteria definition",
            "Requirements traceability matrix",
            "Risk and constraint analysis",
            "Requirements validation and verification",
            "Change impact analysis",
        ],
        "inputs": {
            "project_context": "dict - project background and goals",
            "stakeholder_inputs": "list - stakeholder requirements",
            "constraints": "dict - technical and business constraints",
            "success_criteria": "list - definition of success",
        },
        "outputs": {
            "requirements_specification": "detailed requirements document",
            "user_stories": "prioritized user story backlog",
            "acceptance_criteria": "testable acceptance criteria",
            "requirements_matrix": "traceability and impact matrix",
            "risk_analysis": "requirement risks and mitigations",
        },
        "best_for": [
            "Complex system requirements",
            "Multi-stakeholder projects",
            "Compliance-driven requirements",
            "User-centered design requirements",
            "Technical specification development",
        ],
        "execution_time": "5-20 minutes",
        "dependencies": ["knowledge_search", "analysis_tools", "documentation_tools"],
    },
    "architect": {
        "primary_function": "System architecture design and technical planning",
        "capabilities": [
            "System architecture design and modeling",
            "Technology stack selection and evaluation",
            "Scalability and performance planning",
            "Security architecture design",
            "Integration and API design",
            "Data architecture and flow design",
            "Infrastructure and deployment planning",
            "Architecture documentation and diagrams",
        ],
        "inputs": {
            "requirements": "dict - functional and non-functional requirements",
            "constraints": "dict - technical, business, and operational constraints",
            "existing_systems": "dict - current system landscape",
            "performance_goals": "dict - scalability and performance targets",
        },
        "outputs": {
            "architecture_design": "comprehensive system architecture",
            "technology_recommendations": "justified technology stack",
            "architecture_diagrams": "visual system representations",
            "integration_plan": "system integration strategy",
            "deployment_architecture": "infrastructure and deployment design",
        },
        "best_for": [
            "Enterprise system design",
            "Microservices architecture",
            "Cloud-native applications",
            "High-scale system design",
            "Legacy system modernization",
        ],
        "execution_time": "8-25 minutes",
        "dependencies": [
            "design_tools",
            "architecture_frameworks",
            "diagram_generators",
        ],
    },
    # ... (continuing with all other agents from the original AGENT_REGISTRY)
    "coder": {
        "primary_function": "Full-stack software development and implementation",
        "capabilities": [
            "Frontend and backend development",
            "API design and implementation",
            "Database design and integration",
            "Code review and optimization",
            "Testing implementation",
            "Performance optimization",
            "Security implementation",
            "Documentation generation",
        ],
        "inputs": {
            "specifications": "dict - technical requirements and specifications",
            "architecture": "dict - system architecture guidelines",
            "constraints": "dict - technical and business constraints",
            "preferences": "dict - technology and framework preferences",
        },
        "outputs": {
            "implementation": "complete working code implementation",
            "tests": "comprehensive test suites",
            "documentation": "code documentation and guides",
            "deployment_config": "deployment configuration files",
            "performance_metrics": "code performance analysis",
        },
        "best_for": [
            "Full-stack application development",
            "API and microservice implementation",
            "Database-driven applications",
            "Performance-critical systems",
            "Enterprise application development",
        ],
        "execution_time": "5-30 minutes",
        "dependencies": ["file_system", "generate_code", "testing_frameworks"],
    },
    "frontend_developer": {
        "primary_function": "Frontend development and user interface implementation",
        "capabilities": [
            "React/Vue.js component development",
            "HTML5, CSS3, and JavaScript implementation",
            "Responsive design with Tailwind CSS/Bootstrap",
            "TypeScript integration and configuration",
            "Frontend build tool configuration (Vite, Webpack)",
            "UI/UX component library development",
            "Client-side state management",
            "API integration and data fetching",
        ],
        "inputs": {
            "ui_requirements": "dict - UI/UX requirements and specifications",
            "design_assets": "dict - design mockups, wireframes, style guide",
            "api_endpoints": "list - backend API endpoints to integrate",
            "tech_stack": "dict - frontend technology preferences",
        },
        "outputs": {
            "component_files": "React/Vue components with proper structure",
            "styling_files": "CSS/SCSS files with responsive design",
            "configuration_files": "Build tool and package.json configurations",
            "type_definitions": "TypeScript interfaces and type files",
        },
        "best_for": [
            "Single Page Application (SPA) development",
            "Component library creation",
            "Responsive web design implementation",
            "User interface development",
        ],
        "execution_time": "2-8 minutes",
        "dependencies": ["file_system", "generate_code"],
    },
    "backend_developer": {
        "primary_function": "Backend API and server-side development",
        "capabilities": [
            "REST API and GraphQL development",
            "Database integration and ORM usage",
            "Authentication and authorization systems",
            "Microservices architecture implementation",
            "Server-side business logic development",
            "API documentation and testing",
            "Performance optimization and caching",
            "Security implementation and hardening",
        ],
        "inputs": {
            "api_requirements": "dict - API specifications and endpoints",
            "database_schema": "dict - data model and relationships",
            "authentication_requirements": "dict - auth/authorization needs",
            "business_logic": "dict - core business rules and processes",
        },
        "outputs": {
            "api_server_files": "Backend server implementation files",
            "database_models": "ORM/ODM model definitions",
            "api_routes": "Endpoint routing and handler implementations",
            "middleware_files": "Authentication, logging, and error middleware",
        },
        "best_for": [
            "RESTful API development",
            "Database-driven applications",
            "Microservices implementation",
            "Server-side business logic",
        ],
        "execution_time": "3-10 minutes",
        "dependencies": ["file_system", "generate_code", "automation_tools"],
    },
    "tester": {
        "primary_function": "Comprehensive testing strategy and implementation",
        "capabilities": [
            "Unit test development and execution",
            "Integration testing framework setup",
            "End-to-end (E2E) test automation",
            "API testing and validation",
            "Performance and load testing",
            "Security vulnerability testing",
            "Test data generation and management",
            "CI/CD testing pipeline integration",
        ],
        "inputs": {
            "test_requirements": "dict - testing scope and requirements",
            "application_components": "list - components to test",
            "test_data_needs": "dict - test data and scenario requirements",
            "quality_standards": "dict - quality and coverage requirements",
        },
        "outputs": {
            "test_suites": "Comprehensive test suite implementations",
            "test_configurations": "Testing framework setup and configuration",
            "test_data": "Mock data and test fixtures",
            "performance_tests": "load and performance testing scripts",
            "test_reports": "detailed testing results and coverage reports",
        },
        "best_for": [
            "Test-driven development (TDD)",
            "Automated testing pipeline setup",
            "Quality assurance processes",
            "Performance and security testing",
            "CI/CD pipeline integration",
        ],
        "execution_time": "3-15 minutes",
        "dependencies": ["testing_frameworks", "automation_tools", "quality_tools"],
    },
    "deployer": {
        "primary_function": "Application deployment, infrastructure, and DevOps automation",
        "capabilities": [
            "Containerization with Docker",
            "Kubernetes orchestration and deployment",
            "CI/CD pipeline development",
            "Infrastructure as Code (IaC) implementation",
            "Cloud infrastructure provisioning",
            "Monitoring and alerting setup",
            "Security configuration management",
            "Disaster recovery planning",
        ],
        "inputs": {
            "deployment_requirements": "dict - infrastructure and deployment needs",
            "application_architecture": "dict - system architecture and components",
            "scaling_requirements": "dict - performance and scaling needs",
            "environment": "string - target environment (dev/staging/prod)",
        },
        "outputs": {
            "deployment_scripts": "Automated deployment and configuration scripts",
            "container_files": "Dockerfile and container configurations",
            "infrastructure_code": "Terraform, CloudFormation, or similar IaC",
            "monitoring_config": "monitoring and alerting setup",
            "rollback_plan": "deployment rollback procedures",
        },
        "best_for": [
            "Cloud-native application deployment",
            "Microservices orchestration",
            "DevOps pipeline implementation",
            "Infrastructure automation",
            "Production deployment orchestration",
        ],
        "execution_time": "5-20 minutes",
        "dependencies": [
            "deployment_tools",
            "infrastructure_platforms",
            "automation_tools",
        ],
    },
    "reviewer": {
        "primary_function": "Quality assessment and comprehensive review",
        "capabilities": [
            "Multi-criteria evaluation frameworks",
            "Code review with security analysis",
            "Content quality assessment",
            "Performance optimization review",
            "Best practices compliance checking",
            "Risk assessment and mitigation",
            "Improvement recommendations",
            "Scoring and rating systems",
        ],
        "inputs": {
            "content": "any - content to review",
            "criteria": "list - evaluation criteria",
            "context": "dict - review context",
            "standards": "dict - quality standards to apply",
        },
        "outputs": {
            "review_score": "numerical quality assessment",
            "strengths": "identified positive aspects",
            "weaknesses": "areas needing improvement",
            "recommendations": "specific improvement actions",
            "compliance_status": "standards compliance check",
        },
        "best_for": [
            "Code quality and security review",
            "Content quality assessment",
            "Process and workflow evaluation",
            "Risk assessment for deployments",
            "Standards compliance verification",
        ],
        "execution_time": "2-8 minutes",
        "dependencies": ["quality_standards", "security_frameworks"],
    },
    "planner": {
        "primary_function": "Strategic planning and project orchestration",
        "capabilities": [
            "Multi-phase project planning",
            "Resource allocation optimization",
            "Timeline and milestone definition",
            "Dependency analysis and management",
            "Risk assessment and mitigation planning",
            "Success criteria definition",
            "Progress tracking methodology",
            "Adaptive planning strategies",
        ],
        "inputs": {
            "objective": "string - project goal or outcome",
            "constraints": "dict - time, resource, quality constraints",
            "requirements": "list - functional requirements",
            "context": "dict - project context and environment",
        },
        "outputs": {
            "project_plan": "detailed phase-by-phase plan",
            "timeline": "milestones and deadlines",
            "resource_requirements": "needed resources and dependencies",
            "risk_assessment": "identified risks and mitigations",
            "success_metrics": "measurable success criteria",
        },
        "best_for": [
            "Complex multi-phase projects",
            "Resource and timeline optimization",
            "Strategic roadmap development",
            "Process design and optimization",
            "Change management planning",
        ],
        "execution_time": "3-12 minutes",
        "dependencies": ["project_templates", "planning_frameworks"],
    },
    "qa": {
        "primary_function": "Quality assurance and comprehensive testing",
        "capabilities": [
            "Test strategy development",
            "Automated testing implementation",
            "Quality metrics definition",
            "Performance testing protocols",
            "Security testing procedures",
            "Compliance verification",
            "Bug tracking and resolution",
            "Quality improvement processes",
        ],
        "inputs": {
            "system": "dict - system under test",
            "requirements": "list - quality requirements",
            "test_scope": "string - testing scope and focus",
            "quality_standards": "dict - applicable standards",
        },
        "outputs": {
            "test_plan": "comprehensive testing strategy",
            "test_cases": "detailed test scenarios",
            "quality_metrics": "measurable quality indicators",
            "automation_scripts": "automated testing code",
            "compliance_report": "standards compliance status",
        },
        "best_for": [
            "System integration testing",
            "Performance and load testing",
            "Security vulnerability assessment",
            "Compliance and standards verification",
            "Quality process improvement",
        ],
        "execution_time": "4-20 minutes",
        "dependencies": ["testing_frameworks", "quality_tools"],
    },
    "doc": {
        "primary_function": "Documentation generation and maintenance",
        "capabilities": [
            "Technical documentation authoring",
            "API documentation generation",
            "User guide and tutorial creation",
            "Architecture diagram generation",
            "Process documentation",
            "Knowledge base management",
            "Multi-format publishing",
            "Documentation maintenance workflows",
        ],
        "inputs": {
            "content_source": "any - source material to document",
            "documentation_type": "string - type of docs needed",
            "audience": "string - target audience",
            "format_requirements": "list - output formats needed",
        },
        "outputs": {
            "documentation": "structured documentation content",
            "diagrams": "architectural and process diagrams",
            "examples": "code examples and tutorials",
            "templates": "reusable documentation templates",
            "maintenance_plan": "documentation update procedures",
        },
        "best_for": [
            "API and technical documentation",
            "User guides and tutorials",
            "Process and procedure documentation",
            "Knowledge base development",
            "Documentation automation",
        ],
        "execution_time": "3-15 minutes",
        "dependencies": ["documentation_tools", "diagram_generators"],
    },
    "utility": {
        "primary_function": "State management and workflow control",
        "capabilities": [
            "Workflow state coordination",
            "Data transformation and processing",
            "Inter-agent communication facilitation",
            "Resource management and allocation",
            "Error handling and recovery",
            "Performance monitoring",
            "Cleanup and maintenance tasks",
            "System health monitoring",
        ],
        "inputs": {
            "workflow_state": "dict - current workflow state",
            "operation": "string - requested operation",
            "parameters": "dict - operation parameters",
            "context": "dict - execution context",
        },
        "outputs": {
            "updated_state": "modified workflow state",
            "operation_result": "operation execution result",
            "performance_metrics": "execution performance data",
            "health_status": "system health indicators",
            "cleanup_actions": "maintenance actions performed",
        },
        "best_for": [
            "Workflow state coordination",
            "Data processing and transformation",
            "System maintenance and cleanup",
            "Performance monitoring",
            "Error recovery and resilience",
        ],
        "execution_time": "1-5 minutes",
        "dependencies": ["state_management", "monitoring_tools"],
    },
    "database": {
        "primary_function": "Database design and data management",
        "capabilities": [
            "Database schema design and optimization",
            "SQL/NoSQL database implementation",
            "Data migration and seeding scripts",
            "Database performance tuning",
            "Data modeling and normalization",
            "Backup and recovery procedures",
            "Database security configuration",
            "Data analytics and reporting queries",
        ],
        "inputs": {
            "data_requirements": "dict - data storage and access requirements",
            "database_type": "string - SQL (PostgreSQL, MySQL) or NoSQL (MongoDB)",
            "performance_requirements": "dict - scalability and performance needs",
            "security_requirements": "list - data security and compliance needs",
        },
        "outputs": {
            "database_schema": "complete database design and structure",
            "migration_scripts": "database setup and migration files",
            "performance_indexes": "optimized database indexes",
            "security_configuration": "database security and access controls",
            "sample_data": "test data and seeding scripts",
        },
        "best_for": [
            "Relational database design",
            "NoSQL document databases",
            "Data warehouse design",
            "Database performance optimization",
            "Data security implementation",
        ],
        "execution_time": "4-15 minutes",
        "dependencies": ["file_system", "generate_code", "review_content"],
    },
}

# MCP Tool Registry with Enhanced Capabilities
MCP_TOOL_REGISTRY = {
    "web_search": {
        "mcp_tools": [
            "brave_web_search",
            "brave_news_search",
            "brave_local_search",
            "brave_video_search",
            "brave_image_search",
        ],
        "primary_functions": [
            "Real-time web information gathering",
            "News and current events research",
            "Local business and location search",
            "Video content discovery",
            "Image and visual content search",
        ],
        "capabilities": [
            "Multi-format search across web, news, local, video, image",
            "Real-time information retrieval",
            "Comprehensive result filtering and ranking",
            "Source credibility assessment",
            "Content freshness validation",
        ],
        "best_for": [
            "Current events and trending topics",
            "Real-time information needs",
            "Multi-modal content research",
            "Location-based searches",
            "Visual content discovery",
        ],
        "integration_patterns": [
            "Search → Scrape → Extract workflow",
            "Multi-source validation",
            "Content aggregation and synthesis",
        ],
    },
    "web_scraping": {
        "mcp_tools": [
            "firecrawl_scrape",
            "firecrawl_map",
            "firecrawl_crawl",
            "firecrawl_search",
            "firecrawl_extract",
        ],
        "primary_functions": [
            "Structured web content extraction",
            "Site mapping and URL discovery",
            "Comprehensive site crawling",
            "Intelligent content search",
            "Data extraction with LLM processing",
        ],
        "capabilities": [
            "Advanced web content extraction",
            "Structured data extraction",
            "Multi-page content aggregation",
            "Content transformation and processing",
            "Site architecture analysis",
        ],
        "best_for": [
            "Comprehensive website analysis",
            "Structured data extraction",
            "Content aggregation projects",
            "Site migration and analysis",
            "Research documentation",
        ],
        "integration_patterns": [
            "Map → Crawl → Extract pipeline",
            "Search → Scrape targeted content",
            "Extract → Process → Store workflow",
        ],
    },
    "research_papers": {
        "mcp_tools": ["search_papers", "download_paper", "list_papers", "read_paper"],
        "primary_functions": [
            "Academic paper search and discovery",
            "Research paper download and storage",
            "Paper library management",
            "Full-text paper analysis",
        ],
        "capabilities": [
            "arXiv integration and search",
            "Academic literature discovery",
            "Paper content extraction",
            "Research library management",
            "Citation and reference tracking",
        ],
        "best_for": [
            "Academic research projects",
            "Literature reviews",
            "Technology trend analysis",
            "Scientific research validation",
            "Knowledge synthesis",
        ],
        "integration_patterns": [
            "Search → Download → Read → Analyze",
            "Multi-paper comparative analysis",
            "Research synthesis workflows",
        ],
    },
    "technical_docs": {
        "mcp_tools": ["resolve_library_id", "get_library_docs"],
        "primary_functions": [
            "Library and framework documentation access",
            "Technical documentation retrieval",
            "API reference and guide access",
            "Framework-specific guidance",
        ],
        "capabilities": [
            "Context7-compatible documentation access",
            "Framework and library guidance",
            "API documentation integration",
            "Technical implementation support",
            "Best practices documentation",
        ],
        "best_for": [
            "Technical implementation guidance",
            "API integration projects",
            "Framework learning and adoption",
            "Best practices research",
            "Technical documentation generation",
        ],
        "integration_patterns": [
            "Resolve → Retrieve → Apply",
            "Documentation-driven development",
            "Technical guidance workflows",
        ],
    },
    "database": {
        "mcp_tools": ["get_neo4j_schema", "read_neo4j_cypher", "write_neo4j_cypher"],
        "primary_functions": [
            "Graph database operations",
            "Schema analysis and management",
            "Data querying and manipulation",
            "Knowledge graph operations",
        ],
        "capabilities": [
            "Neo4j graph database integration",
            "Complex data relationship analysis",
            "Knowledge graph construction",
            "Data persistence and retrieval",
            "Schema evolution management",
        ],
        "best_for": [
            "Knowledge graph applications",
            "Complex data relationship analysis",
            "Graph-based analytics",
            "Data modeling and persistence",
            "Relationship-driven applications",
        ],
        "integration_patterns": [
            "Read → Process → Write workflow",
            "Schema → Query → Update cycle",
            "Knowledge graph construction",
        ],
    },
    "time": {
        "mcp_tools": [
            "current_time",
            "relative_time",
            "days_in_month",
            "get_timestamp",
            "convert_time",
            "get_week_year",
        ],
        "primary_functions": [
            "Time and date operations",
            "Timezone conversions",
            "Temporal calculations",
            "Schedule and calendar operations",
        ],
        "capabilities": [
            "Multi-timezone time handling",
            "Temporal data processing",
            "Schedule coordination",
            "Time-based calculations",
            "Calendar and date utilities",
        ],
        "best_for": [
            "Scheduling and calendar applications",
            "Time-based data analysis",
            "Multi-timezone coordination",
            "Temporal workflow management",
            "Date and time utilities",
        ],
        "integration_patterns": [
            "Time calculation workflows",
            "Schedule coordination",
            "Temporal data processing",
        ],
    },
    "shell": {
        "mcp_tools": ["shell_exec"],
        "primary_functions": [
            "System command execution",
            "File system operations",
            "Development tool integration",
            "Environment management",
        ],
        "capabilities": [
            "Secure command execution",
            "File system manipulation",
            "Development workflow automation",
            "System administration tasks",
            "Environment configuration",
        ],
        "best_for": [
            "Development automation",
            "File system operations",
            "Build and deployment tasks",
            "System administration",
            "Environment setup",
        ],
        "integration_patterns": [
            "Command execution workflows",
            "File processing pipelines",
            "Development automation",
        ],
    },
    "thinking": {
        "mcp_tools": ["sequentialthinking"],
        "primary_functions": [
            "Complex problem analysis",
            "Multi-step reasoning",
            "Decision support",
            "Cognitive processing enhancement",
        ],
        "capabilities": [
            "Sequential thought processing",
            "Complex problem decomposition",
            "Reasoning chain management",
            "Decision validation",
            "Cognitive workflow support",
        ],
        "best_for": [
            "Complex problem solving",
            "Multi-step analysis",
            "Decision support workflows",
            "Reasoning validation",
            "Cognitive assistance",
        ],
        "integration_patterns": [
            "Think → Analyze → Decide",
            "Complex reasoning workflows",
            "Decision support processes",
        ],
    },
}

# Sophisticated Workflow Patterns
WORKFLOW_PATTERNS = {
    "research_and_analyze": {
        "description": "Comprehensive research with multi-source analysis",
        "agents": ["researcher", "reviewer"],
        "strategy": "linear",
        "tools": ["brave_web_search", "search_papers", "get_library_docs"],
        "duration_estimate": "5-15 minutes",
        "best_for": [
            "technology evaluation",
            "market research",
            "competitive analysis",
        ],
        "success_criteria": [
            "comprehensive findings",
            "verified sources",
            "actionable insights",
        ],
    },
    "design_develop_deploy": {
        "description": "Full development lifecycle from design to deployment",
        "agents": ["planner", "coder", "tester", "reviewer", "deployer"],
        "strategy": "adaptive",
        "tools": ["shell_exec", "get_library_docs", "write_neo4j_cypher"],
        "duration_estimate": "15-45 minutes",
        "best_for": [
            "application development",
            "API creation",
            "system implementation",
        ],
        "success_criteria": [
            "working implementation",
            "comprehensive tests",
            "production deployment",
        ],
    },
    "document_and_validate": {
        "description": "Documentation creation with quality validation",
        "agents": ["doc", "reviewer", "tester"],
        "strategy": "parallel",
        "tools": ["firecrawl_scrape", "get_library_docs"],
        "duration_estimate": "8-20 minutes",
        "best_for": ["API documentation", "user guides", "process documentation"],
        "success_criteria": [
            "comprehensive documentation",
            "validated accuracy",
            "user-friendly format",
        ],
    },
    "investigate_and_solve": {
        "description": "Problem investigation with solution implementation",
        "agents": ["researcher", "planner", "coder", "qa"],
        "strategy": "adaptive",
        "tools": ["brave_web_search", "shell_exec", "read_neo4j_cypher"],
        "duration_estimate": "10-30 minutes",
        "best_for": ["debugging", "performance optimization", "feature implementation"],
        "success_criteria": [
            "root cause identified",
            "solution implemented",
            "validation complete",
        ],
    },
    "comprehensive_audit": {
        "description": "Complete system or process audit with recommendations",
        "agents": ["researcher", "reviewer", "qa"],
        "strategy": "parallel",
        "tools": ["read_neo4j_cypher", "shell_exec", "firecrawl_crawl"],
        "duration_estimate": "12-25 minutes",
        "best_for": ["security audit", "performance review", "compliance assessment"],
        "success_criteria": [
            "thorough analysis",
            "risk assessment",
            "improvement plan",
        ],
    },
    "requirements_to_delivery": {
        "description": "Complete project lifecycle from requirements to delivery",
        "agents": [
            "requirements_analyst",
            "researcher",
            "planner",
            "coder",
            "tester",
            "qa",
            "deployer",
            "doc",
        ],
        "strategy": "iterative",
        "tools": ["all_available"],
        "duration_estimate": "25-60 minutes",
        "best_for": [
            "complex projects",
            "full-stack development",
            "enterprise solutions",
        ],
        "success_criteria": [
            "requirements validated",
            "solution delivered",
            "quality assured",
            "documentation complete",
        ],
    },
}

# Operational Guidelines for Intelligent Decision Making
OPERATIONAL_GUIDELINES = {
    "request_analysis": {
        "complexity_assessment": {
            "simple": "Single agent, direct execution, minimal dependencies",
            "moderate": "Multi-agent coordination, some dependencies, standard patterns",
            "complex": "Sophisticated orchestration, multiple dependencies, custom workflows",
            "enterprise": "Full lifecycle management, comprehensive validation, production deployment",
        },
        "intent_recognition": {
            "patterns": [
                "development_request",
                "research_request",
                "analysis_request",
                "deployment_request",
                "documentation_request",
                "troubleshooting_request",
                "optimization_request",
                "planning_request",
            ],
            "indicators": {
                "urgency": ["urgent", "asap", "immediately", "critical"],
                "quality": ["high-quality", "production-ready", "enterprise-grade"],
                "scope": ["comprehensive", "detailed", "complete", "full"],
            },
        },
    },
    "workflow_optimization": {
        "parallelization_opportunities": [
            "Independent research tasks",
            "Multi-source data gathering",
            "Parallel testing and validation",
            "Concurrent documentation generation",
            "Independent component development",
        ],
        "dependency_management": [
            "Sequential for dependent tasks",
            "Parallel for independent work streams",
            "Hybrid for mixed dependencies",
            "Adaptive for dynamic requirements",
        ],
        "quality_gates": [
            "Input validation",
            "Intermediate result verification",
            "Output quality assessment",
            "Success criteria validation",
        ],
    },
    "error_handling": {
        "graceful_degradation": [
            "Fallback to simpler strategies",
            "Alternative agent selection",
            "Reduced scope execution",
            "Manual intervention triggers",
        ],
        "recovery_strategies": [
            "Retry with different approach",
            "Escalation to human oversight",
            "Alternative workflow paths",
            "Resource reallocation",
        ],
    },
    "quality_assurance": {
        "validation_checkpoints": [
            "Input completeness and validity",
            "Agent selection appropriateness",
            "Tool capability matching",
            "Output quality assessment",
            "Success criteria achievement",
        ],
        "continuous_improvement": [
            "Performance metrics tracking",
            "Success rate analysis",
            "User satisfaction monitoring",
            "Workflow optimization opportunities",
        ],
    },
}
