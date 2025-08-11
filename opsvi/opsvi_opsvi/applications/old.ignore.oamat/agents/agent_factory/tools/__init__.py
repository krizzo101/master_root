"""
OAMAT Agent Factory Tools Package

Modularized tool creation functions for LangGraph agents.
Extracted from agent_factory.py for better organization and maintainability.
"""

from src.applications.oamat.agents.agent_factory.tools.analysis import (
    create_analysis_tools,
)
from src.applications.oamat.agents.agent_factory.tools.automation import (
    create_automation_tools,
)
from src.applications.oamat.agents.agent_factory.tools.code_generation import (
    CodeRequest,
    DocumentationRequest,
    ReviewRequest,
    create_code_generation_tool,
    create_code_review_tool,
    create_completion_tool,
    create_documentation_tool,
)
from src.applications.oamat.agents.agent_factory.tools.database import (
    create_database_operations_tools,
)
from src.applications.oamat.agents.agent_factory.tools.deployment import (
    create_deployment_tools,
)
from src.applications.oamat.agents.agent_factory.tools.design import (
    create_architecture_tools,
    create_design_tools,
)
from src.applications.oamat.agents.agent_factory.tools.diagramming import (
    create_diagram_generation_tools,
)
from src.applications.oamat.agents.agent_factory.tools.file_system import (
    create_file_system_tools,
)
from src.applications.oamat.agents.agent_factory.tools.monitoring import (
    create_monitoring_tools,
)
from src.applications.oamat.agents.agent_factory.tools.planning import (
    create_planning_frameworks_tools,
)
from src.applications.oamat.agents.agent_factory.tools.quality import (
    create_quality_assurance_tools,
    create_quality_standards_tools,
)
from src.applications.oamat.agents.agent_factory.tools.research import (
    ResearchRequest,
    create_academic_search_tool,
    create_knowledge_search_tool,
    create_mcp_research_tools,
    create_web_search_tool,
)
from src.applications.oamat.agents.agent_factory.tools.rules import (
    create_rule_access_tools,
)
from src.applications.oamat.agents.agent_factory.tools.security import (
    create_security_framework_tools,
)
from src.applications.oamat.agents.agent_factory.tools.state_management import (
    create_state_management_tools,
)
from src.applications.oamat.agents.agent_factory.tools.testing import (
    create_testing_framework_tools,
)
from src.applications.oamat.agents.agent_factory.tools.web_scraping import (
    create_web_scraping_tools,
)

__all__ = [
    # File system tools
    "create_file_system_tools",
    # Research tools
    "create_knowledge_search_tool",
    "create_web_search_tool",
    "create_academic_search_tool",
    "create_mcp_research_tools",
    # Code generation tools
    "create_code_generation_tool",
    "create_code_review_tool",
    "create_documentation_tool",
    "create_completion_tool",
    # Testing tools
    "create_testing_framework_tools",
    # Deployment tools
    "create_deployment_tools",
    # Automation tools
    "create_automation_tools",
    # Quality tools
    "create_quality_assurance_tools",
    "create_quality_standards_tools",
    # Security tools
    "create_security_framework_tools",
    # State management tools
    "create_state_management_tools",
    # Monitoring tools
    "create_monitoring_tools",
    # Diagramming tools
    "create_diagram_generation_tools",
    # Rules tools
    "create_rule_access_tools",
    # Analysis tools
    "create_analysis_tools",
    # Design tools
    "create_design_tools",
    "create_architecture_tools",
    # Planning tools
    "create_planning_frameworks_tools",
    # Database tools
    "create_database_operations_tools",
    # Web scraping tools
    "create_web_scraping_tools",
    # Request models
    "ResearchRequest",
    "CodeRequest",
    "ReviewRequest",
    "DocumentationRequest",
]
