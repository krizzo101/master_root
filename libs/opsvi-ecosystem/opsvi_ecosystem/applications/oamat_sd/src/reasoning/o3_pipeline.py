"""
O3 Reasoning Pipeline Module

Handles O3 meta-intelligence and dynamic workflow generation.
Extracted from smart_decomposition_agent.py for better modularity.
"""

from datetime import datetime
import json
from typing import Any

from src.applications.oamat_sd.src.models.workflow_models import (
    AVAILABLE_MCP_TOOLS,
    SmartDecompositionState,
)
from src.applications.oamat_sd.src.reasoning.structured_output_enforcer import (
    StructuredOutputEnforcer,
)
from src.applications.oamat_sd.src.sd_logging import LoggerFactory


class O3PipelineEngine:
    """Handles O3 reasoning and dynamic workflow generation"""

    def __init__(self, logger_factory: LoggerFactory, openai_client):
        self.logger_factory = logger_factory
        self.logger = logger_factory.get_debug_logger()
        self.openai_client = openai_client

        # Initialize structured output enforcer for O3 reasoning
        self.structured_enforcer = StructuredOutputEnforcer()

        # Initialize O3 reasoning model configuration - NO HARDCODED VALUES
        from src.applications.oamat_sd.src.config.config_manager import ConfigManager

        reasoning_config = ConfigManager().get_model_config("reasoning")

        self.model_config = {
            "model_name": reasoning_config.model_name,
            "max_tokens": reasoning_config.max_tokens,
            "reasoning_effort": getattr(reasoning_config, "reasoning_effort", "medium"),
            # Note: temperature not supported by O3 models
        }

    async def generate_workflow_specification(
        self, state: SmartDecompositionState
    ) -> SmartDecompositionState:
        """Generate comprehensive WorkflowSpecification using O3 meta-intelligence"""
        self.logger.info(
            "Generating WorkflowSpecification using O3 meta-intelligence..."
        )

        specification_start_time = datetime.now()

        try:
            # Enhanced logging: Log O3 specification generation start
            user_request = (
                state.get("user_request", "")
                if isinstance(state, dict)
                else state.user_request
            )
            self.logger_factory.log_component_operation(
                component="o3_pipeline",
                operation="specification_generation_start",
                data={
                    "user_request_length": len(user_request),
                    "o3_model": "o3-mini",
                    "generation_mode": "dynamic",
                    "available_tools_count": len(AVAILABLE_MCP_TOOLS),
                },
            )

            # Create comprehensive O3 meta-intelligence prompt with standardized context
            standardized_context = (
                state.get("context", {}).get("standardized_request")
                if isinstance(state, dict)
                else getattr(state, "context", {}).get("standardized_request")
            )
            o3_prompt = self._create_o3_meta_intelligence_prompt(
                user_request, standardized_context
            )

            # Execute O3 reasoning with structured output enforcement
            workflow_specification = (
                await self.structured_enforcer.enforce_workflow_specification(
                    prompt=o3_prompt,
                    model_config=self.model_config,
                    context={
                        "user_request": user_request,
                        "available_tools": list(AVAILABLE_MCP_TOOLS.keys()),
                    },
                )
            )

            # Calculate specification generation time
            specification_time = (
                datetime.now() - specification_start_time
            ).total_seconds() * 1000

            # Enhanced logging: Log successful O3 specification generation
            self.logger_factory.log_component_operation(
                component="o3_pipeline",
                operation="specification_generation_complete",
                data={
                    "specification_successful": True,
                    "generation_time_ms": specification_time,
                    "agents_specified": len(
                        workflow_specification.get("agent_specifications")
                        if "agent_specifications" in workflow_specification
                        else []
                    ),
                    "workflow_complexity": self._calculate_workflow_complexity(
                        workflow_specification
                    ),
                    "structured_output_enforcement": True,
                    "dynamic_generation": True,
                },
                execution_time_ms=specification_time,
                success=True,
            )

            # Update state with workflow specification
            state["workflow_specification"] = workflow_specification
            self.logger.info("O3 WorkflowSpecification generation complete")

        except Exception as e:
            # Calculate generation time for failed specification
            specification_time = (
                datetime.now() - specification_start_time
            ).total_seconds() * 1000

            # Enhanced logging: Log failed O3 specification generation
            self.logger_factory.log_component_operation(
                component="o3_pipeline",
                operation="specification_generation_failed",
                data={
                    "failure_reason": "o3_generation_error",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "generation_time_ms": specification_time,
                },
                execution_time_ms=specification_time,
                success=False,
            )

            self.logger.error(f"O3 WorkflowSpecification generation failed: {e}")
            raise RuntimeError(
                f"O3 specification generation failed: {e}. Cannot proceed without workflow specification."
            )

        return state

    def _create_o3_meta_intelligence_prompt(
        self, user_request: str, standardized_context: dict = None
    ) -> str:
        """Create comprehensive O3 master prompt for complete workflow architecture generation"""

        # Detailed MCP tool documentation for O3 education
        mcp_tool_details = {
            "codebase_search": {
                "description": "Semantic search for understanding code by meaning",
                "parameters": {
                    "query": "search question",
                    "target_directories": "optional scope",
                },
                "use_cases": [
                    "Understanding existing codebases",
                    "Finding implementation patterns",
                    "Code analysis",
                ],
                "outputs": ["Code snippets", "Function definitions", "Usage examples"],
            },
            "read_file": {
                "description": "Read file contents with line range support",
                "parameters": {
                    "target_file": "file path",
                    "start_line": "optional",
                    "end_line": "optional",
                },
                "use_cases": [
                    "Reading configuration files",
                    "Analyzing source code",
                    "Template inspection",
                ],
                "outputs": ["File contents", "Code sections", "Configuration data"],
            },
            "edit_file": {
                "description": "Create or modify files with precise edits",
                "parameters": {"target_file": "file path", "code_edit": "new content"},
                "use_cases": [
                    "Creating new files",
                    "Modifying existing code",
                    "Configuration updates",
                ],
                "outputs": [
                    "File creation",
                    "Code modifications",
                    "Configuration changes",
                ],
            },
            "run_terminal_cmd": {
                "description": "Execute terminal commands for project operations",
                "parameters": {"command": "terminal command"},
                "use_cases": [
                    "Installing dependencies",
                    "Running tests",
                    "Build operations",
                ],
                "outputs": ["Command output", "Installation results", "Test results"],
            },
            "grep_search": {
                "description": "Fast regex search across files",
                "parameters": {
                    "query": "regex pattern",
                    "include_pattern": "file filter",
                },
                "use_cases": [
                    "Finding specific code patterns",
                    "Text search",
                    "Symbol lookup",
                ],
                "outputs": ["Search results", "Pattern matches", "File locations"],
            },
            "list_dir": {
                "description": "List directory contents for structure analysis",
                "parameters": {"relative_workspace_path": "directory path"},
                "use_cases": [
                    "Understanding project structure",
                    "File discovery",
                    "Directory analysis",
                ],
                "outputs": [
                    "File listings",
                    "Directory structure",
                    "Project organization",
                ],
            },
            "web_search": {
                "description": "Search web for current information and documentation",
                "parameters": {"search_term": "search query"},
                "use_cases": [
                    "Finding documentation",
                    "Research",
                    "Current information",
                ],
                "outputs": [
                    "Web results",
                    "Documentation links",
                    "Reference materials",
                ],
            },
        }

        # Enhanced O3 Framework Education prompt
        framework_education = """
## OAMAT_SD FRAMEWORK TECHNICAL ARCHITECTURE EDUCATION

### EXECUTION PIPELINE TECHNICAL DETAILS
You are generating specifications for a sophisticated 5-stage execution framework. Understanding this pipeline is CRITICAL for generating proper agent specifications:

#### Stage 1: O3 Reasoning (Current Stage)
```python
# Your WorkflowSpecification output becomes:
workflow_spec = {
    "agents": [{
        "agent_id": "unique_identifier",  # REQUIRED - used by ExecutionEngine
        "role": "dynamic_role_name",
        "complete_prompt": "full_agent_instructions",  # CRITICAL - this prompt determines everything
        "required_tools": ["tool1", "tool2"],
        "required_deliverables": [{
            "name": "deliverable_name",
            "file_pattern": "filename_pattern"  # Used for file extraction
        }]
    }]
}
```

#### Stage 2: Agent Creation → LangGraph Agents
```python
# Your specifications become:
for agent_spec in workflow_specification.agents:
    agent = create_react_agent(
        model=gpt_4_1_mini,
        tools=mcp_tools_from_spec,
        prompt=agent_spec.complete_prompt  # YOUR GENERATED PROMPT
    )
```

#### Stage 3: Parallel Execution → ReAct Loops
```python
# Each agent executes YOUR complete_prompt via:
result = await agent.ainvoke({"messages": [HumanMessage(content=user_request)]})

# Agent follows ReAct pattern:
# Thought: "I need to create X files for this request"
# Action: edit_file(target_file="src/main.py", code_edit="clean_executable_code")
# Observation: "File created successfully"
# Thought: "Now I need to create Y file"
# Action: edit_file(target_file="docs/README.md", code_edit="clean_executable_code")
```

#### Stage 4: File Extraction Engine
```python
# Extracts files from agent outputs using these EXACT patterns:
FILE_PATTERNS = [
    # Pattern 1: Direct file declarations
    r"File:\\s*([^\\n]+)\\s*\\n(.*?)(?=File:|$)",

    # Pattern 2: Code blocks with filenames
    r"```(?:python|js|ts|yaml|json|dockerfile)?\\s*#?\\s*([^\\n]*\\.(py|js|ts|yml|yaml|json|dockerfile|md|txt))\\s*\\n(.*?)\\n```",

    # Pattern 3: Tool calls (edit_file)
    r'edit_file\\(target_file="([^"]+)".*?code_edit="(.*?)"',
]
```

### PROJECT STRUCTURE ORGANIZATION (CRITICAL)

**MANDATORY FILE ORGANIZATION**: The system creates `src/` and `docs/` directories automatically.
Agents MUST organize files into the proper directory structure:

#### Required Directory Organization:
```
project_root/
├── src/           # SOURCE CODE FILES (Python, JavaScript, etc.)
│   ├── main.py
│   ├── models.py
│   ├── config.py
│   └── utils.py
├── docs/          # DOCUMENTATION FILES (Markdown, text)
│   ├── README.md
│   ├── API.md
│   └── SETUP.md
├── tests/         # TEST FILES (created as needed)
│   └── test_main.py
└── (root level)   # PROJECT CONFIG FILES
    ├── requirements.txt
    ├── docker-compose.yml
    └── .env
```

**CRITICAL RULE**: Agents must specify full directory paths in filenames:
- ✅ CORRECT: "src/main.py", "docs/README.md", "requirements.txt"
- ❌ WRONG: "main.py", "README.md" (these go to root and leave src/docs empty)

### MCP TOOL SYSTEM TECHNICAL SPECIFICATIONS

#### Available Tools and Exact Signatures:
```python
# File Operations
edit_file(target_file: str, instructions: str, code_edit: str) → None
read_file(target_file: str, start_line: int, end_line: int) → str

# Web Operations
web_search(search_term: str) → List[SearchResult]
mcp_web_scraping_firecrawl_scrape(url: str, formats: List[str]) → str

# Research Operations
mcp_research_papers_search_papers(query: str, max_results: int) → List[Paper]

# Shell Operations (MANDATORY)
mcp_shell_shell_exec(command: str) → ExecutionResult
```

#### Tool Execution Environment:
```python
# Agents can make multiple tool calls per session
# Maximum ~20-50 tool calls before efficiency drops
# Each tool call has specific input/output format
# Error handling returns structured error messages
```

### FILE EXTRACTION SUCCESS PATTERNS

#### Agent Output Format for Successful File Generation:
```python
# FORMAT 1: Direct file specification with proper directory organization (PREFERRED)
"File: src/main.py
from fastapi import FastAPI
app = FastAPI()

File: src/models.py
from sqlalchemy import Column, Integer, String

File: docs/README.md
# Project Documentation
This project provides...

File: requirements.txt
fastapi==0.104.1
sqlalchemy==2.0.23
"

# FORMAT 2: Code blocks with directory-organized filenames (ACCEPTABLE)
"```python src/main.py
from fastapi import FastAPI
app = FastAPI()
```

```python src/models.py
from sqlalchemy import Column, Integer, String
```

```markdown docs/README.md
# Project Documentation
This project provides...
```

```text requirements.txt
fastapi==0.104.1
sqlalchemy==2.0.23
```"

# FORMAT 3: Tool calls with proper directory paths (ALSO ACCEPTABLE)
"I'll create the main application file:
edit_file(target_file='src/main.py', code_edit='from fastapi import FastAPI\\napp = FastAPI()')

Now I'll create the documentation:
edit_file(target_file='docs/README.md', code_edit='# Project Documentation\\nThis project provides...')"
```

### CRITICAL SUCCESS FACTORS

#### For Agent Prompt Generation:
1. **File-Focused Instructions**: Agent prompts MUST emphasize creating discrete, named files
2. **Directory Organization**: Agents MUST use proper directory paths (src/, docs/, tests/)
3. **Clean Code Requirements**: Agents must generate executable code without tutorial text
4. **Specific Deliverables**: Each agent MUST know exactly what files to create and where
5. **Format Adherence**: Agent output must match file extraction patterns

#### Example of GOOD Agent Prompt:
```
You are an Implementation Agent. Create the following files for a FastAPI application:

REQUIRED DELIVERABLES:
- src/main.py: FastAPI application entry point
- src/models.py: SQLAlchemy database models
- src/config.py: Application configuration
- docs/README.md: Project documentation
- requirements.txt: Python dependencies

DIRECTORY ORGANIZATION RULES:
- Python source code files → src/ directory
- Documentation files → docs/ directory
- Configuration files → project root

FORMAT: Use 'File: full/path/filename' followed by clean, executable code.
NO tutorials, explanations, or mixed content.
```

#### Example of BAD Agent Prompt:
```
Create a FastAPI application with good practices and documentation.
```

### AGENT COORDINATION PATTERNS

#### Parallel Execution via Send API:
```python
# Multiple agents can work simultaneously on different aspects
# Use Send API for parallel coordination
# Agents communicate via shared state object
```

#### Tool Usage Guidelines:
```python
# Agents should use tools for ALL file operations
# Never generate file content in text without tool calls
# Each file creation should be explicit and separate
# Always specify full directory paths in target_file parameter
```

### QUALITY VALIDATION CRITERIA

Your generated agent specifications will be considered successful if:
1. **File Generation**: Agents create exactly the specified deliverables in correct directories
2. **Directory Organization**: Files are properly organized into src/, docs/, and root levels
3. **Clean Code**: Generated files contain executable code without documentation
4. **Pattern Compliance**: Agent outputs match file extraction patterns
5. **Role Clarity**: Each agent has a clear, specific function

### REQUEST TYPE ADAPTABILITY

#### For Code Projects:
- Source files MUST go in src/ directory (src/main.py, src/models.py)
- Documentation MUST go in docs/ directory (docs/README.md, docs/API.md)
- Config files go at root level (requirements.txt, docker-compose.yml)
- Use proper file extensions and structure
- Include necessary dependencies and imports

#### For Research Projects:
- Research documents → docs/ directory
- Data analysis scripts → src/ directory
- Use clear file naming conventions
- Include proper citations and references

#### For Creative Projects:
- Content files → appropriate directories based on type
- Source code (if any) → src/ directory
- Documentation → docs/ directory
- Use appropriate file formats
- Structure content logically

## FRAMEWORK EXECUTION VALIDATION

The success of your WorkflowSpecification depends on:
1. Agent prompts that generate file-extractable content WITH PROPER DIRECTORY PATHS
2. Clear deliverable specifications with file patterns including directory organization
3. Tool assignments that match agent capabilities
4. Role definitions that prevent overlap and ensure coverage
5. CRITICAL: All agents understand and follow directory organization rules
"""

        # Enhanced prompt with preprocessed context
        standardized_context_section = ""
        if standardized_context:
            standardized_context_section = f"""
## PREPROCESSED REQUEST ANALYSIS (HIGH CONFIDENCE CONTEXT)

**IMPORTANT**: The user request has been intelligently preprocessed. Use this structured analysis for optimal workflow generation:

### CLASSIFICATION ANALYSIS:
- **Request Type**: {standardized_context.get('classification', {}).get('request_type', 'unspecified')}
- **Complexity Level**: {standardized_context.get('classification', {}).get('complexity_level', 'unspecified')}
- **Domain Category**: {standardized_context.get('classification', {}).get('domain_category', 'unspecified')}
- **Platform Target**: {standardized_context.get('classification', {}).get('platform_target', 'unspecified')}
- **Quality Level**: {standardized_context.get('classification', {}).get('quality_level', 'development')}
- **Estimated Effort**: {standardized_context.get('classification', {}).get('estimated_effort', 'unknown')}

### TECHNICAL SPECIFICATIONS:
- **Programming Languages**: {standardized_context.get('technical_specification', {}).get('programming_languages', [])}
- **Frameworks**: {standardized_context.get('technical_specification', {}).get('frameworks', [])}
- **Platforms**: {standardized_context.get('technical_specification', {}).get('platforms', [])}
- **Databases**: {standardized_context.get('technical_specification', {}).get('databases', [])}
- **External Services**: {standardized_context.get('technical_specification', {}).get('external_services', [])}
- **Performance Requirements**: {standardized_context.get('technical_specification', {}).get('performance_requirements', [])}
- **Security Requirements**: {standardized_context.get('technical_specification', {}).get('security_requirements', [])}

### FUNCTIONAL REQUIREMENTS:
{json.dumps(standardized_context.get('functional_requirements', []), indent=2)}

### DELIVERABLES SPECIFICATION:
- **File Types**: {standardized_context.get('deliverables', {}).get('file_types', [])}
- **Directory Structure**: {standardized_context.get('deliverables', {}).get('directory_structure', [])}
- **Documentation Requirements**: {standardized_context.get('deliverables', {}).get('documentation_requirements', [])}
- **Configuration Files**: {standardized_context.get('deliverables', {}).get('configuration_files', [])}
- **Test Requirements**: {standardized_context.get('deliverables', {}).get('test_requirements', [])}

### SUCCESS CRITERIA:
- **Primary Objectives**: {standardized_context.get('success_criteria', {}).get('primary_objectives', [])}
- **Success Metrics**: {standardized_context.get('success_criteria', {}).get('success_metrics', [])}
- **Validation Steps**: {standardized_context.get('success_criteria', {}).get('validation_steps', [])}

### CONTEXT INFORMATION:
- **User Environment**: {standardized_context.get('context', {}).get('user_environment', {})}
- **Existing Systems**: {standardized_context.get('context', {}).get('existing_systems', [])}
- **Constraints**: {standardized_context.get('context', {}).get('constraints', [])}
- **Assumptions**: {standardized_context.get('context', {}).get('assumptions', [])}

**CONFIDENCE SCORES**:
- Overall: {standardized_context.get('confidence_scores', {}).get('overall_confidence', 'unknown')}
- Classification: {standardized_context.get('confidence_scores', {}).get('classification_confidence', 'unknown')}
- Technical: {standardized_context.get('confidence_scores', {}).get('technical_confidence', 'unknown')}
- Requirements: {standardized_context.get('confidence_scores', {}).get('requirements_confidence', 'unknown')}

**LEVERAGE THIS CONTEXT**: Use this comprehensive analysis to generate highly targeted agent specifications that precisely address the identified requirements, technical constraints, and success criteria.
"""

        prompt = f"""
{framework_education}

You are an advanced O3 reasoning model responsible for intelligent request decomposition and multi-agent workflow orchestration. Your task is to analyze user requests and create comprehensive, executable specifications.

## CORE MISSION
Transform ANY user request into a structured WorkflowSpecification that coordinates specialized agents to deliver complete, functional results.

{standardized_context_section}

## CRITICAL REQUIREMENTS

        Available MCP Tools for Agent Assignment:
        {json.dumps(mcp_tool_details, indent=2)}

        ### 1. REQUEST ANALYSIS
        - Analyze request type, complexity, and deliverable requirements
        - Identify all necessary components and dependencies
        - Determine optimal agent specialization and coordination
        - **USE PREPROCESSED ANALYSIS** above for enhanced understanding

        ### 2. WORKFLOW ARCHITECTURE
        - Design agent roles with clear, non-overlapping responsibilities
        - Plan execution dependencies and coordination points
        - Ensure complete coverage of all request requirements
        - **ALIGN WITH IDENTIFIED TECHNICAL SPECIFICATIONS** above

        ### 3. AGENT SPECIFICATION
        - Create detailed, role-specific complete_prompt for each agent
        - Assign appropriate tools based on agent function and requirements
        - Define specific deliverables with clear file patterns for extraction
        - **ENSURE DELIVERABLES MATCH PREPROCESSED REQUIREMENTS** above
        - CRITICAL: Ensure all agent prompts specify proper directory organization (src/, docs/, root)

        ### 4. EXECUTION OPTIMIZATION
        - Design for parallel execution where possible
        - Minimize agent interdependencies
        - Ensure scalable and efficient workflow execution
        - **CONSIDER COMPLEXITY LEVEL** for optimal agent allocation

        ### 5. OUTPUT VALIDATION
        - Verify all components address the original request
        - Ensure agent prompts will generate extractable files
        - Validate tool assignments match agent capabilities
        - **VALIDATE AGAINST SUCCESS CRITERIA** identified above

        GENERATE COMPLETE WORKFLOWSPECIFICATION FOR: {user_request}

        Focus on creating agent specifications that will result in successful file extraction and complete request fulfillment.

        CRITICAL: Ensure ALL agent prompts instruct agents to use proper directory organization:
        - Source code files → src/ directory (src/main.py, src/models.py)
        - Documentation → docs/ directory (docs/README.md, docs/API.md)
        - Configuration → root level (requirements.txt, .env)"""

        return prompt

    def _parse_o3_response_to_specification(
        self, o3_response: str, user_request: str
    ) -> dict[str, Any]:
        """Parse O3 response to extract WorkflowSpecification with robust JSON parsing"""
        try:
            import re

            self.logger.info("🔍 Parsing O3 response for workflow specification...")

            # Debug: Log the response for analysis
            self.logger.debug(f"O3 Response (first 500 chars): {o3_response[:500]}...")

            json_match = None
            parsing_attempts = []

            # Strategy 1: Look for JSON code blocks with various markdown formats
            json_patterns = [
                r"```json\s*(.*?)\s*```",  # Standard JSON code blocks
                r"```\s*json\s*(.*?)\s*```",  # JSON with extra spacing
                r"```\s*(.*?)\s*```",  # Any code block
                r"```[\w]*\s*(.*?)\s*```",  # Code blocks with language
            ]

            for pattern in json_patterns:
                matches = re.findall(pattern, o3_response, re.DOTALL | re.IGNORECASE)
                if matches:
                    for match in matches:
                        # Try to parse each match
                        try:
                            candidate = json.loads(match.strip())
                            if isinstance(candidate, dict) and len(candidate) > 3:
                                json_match = match.strip()
                                parsing_attempts.append(
                                    f"✅ JSON code block pattern: {pattern[:20]}..."
                                )
                                break
                        except json.JSONDecodeError:
                            parsing_attempts.append(
                                f"❌ JSON code block pattern: {pattern[:20]}... - invalid JSON"
                            )
                if json_match:
                    break

            # Strategy 2: Look for standalone JSON objects
            if not json_match:
                json_patterns = [
                    r"\{(?:[^{}]|{[^{}]*})*\}",  # Basic nested JSON matching
                    r'\{.*?"workflow_id".*?\}',  # JSON containing workflow_id
                    r'\{.*?"agents".*?\}',  # JSON containing agents
                    r'\{.*?"complexity".*?\}',  # JSON containing complexity
                ]

                for pattern in json_patterns:
                    matches = re.findall(pattern, o3_response, re.DOTALL)
                    for match in matches:
                        try:
                            candidate = json.loads(match)
                            if isinstance(candidate, dict) and len(candidate) > 3:
                                json_match = match
                                parsing_attempts.append(
                                    f"✅ Standalone JSON pattern: {pattern[:20]}..."
                                )
                                break
                        except json.JSONDecodeError:
                            parsing_attempts.append(
                                f"❌ Standalone JSON pattern: {pattern[:20]}... - invalid JSON"
                            )
                    if json_match:
                        break

            # Strategy 3: Try to find the largest valid JSON object in the response
            if not json_match:
                # Look for opening { and try to find matching closing }
                start_positions = [i for i, c in enumerate(o3_response) if c == "{"]

                for start_pos in start_positions:
                    brace_count = 0
                    for i in range(start_pos, len(o3_response)):
                        if o3_response[i] == "{":
                            brace_count += 1
                        elif o3_response[i] == "}":
                            brace_count -= 1
                            if brace_count == 0:
                                # Found complete JSON object
                                candidate_json = o3_response[start_pos : i + 1]
                                try:
                                    candidate = json.loads(candidate_json)
                                    if (
                                        isinstance(candidate, dict)
                                        and len(candidate) > 3
                                    ):
                                        json_match = candidate_json
                                        parsing_attempts.append(
                                            "✅ Brace matching strategy"
                                        )
                                        break
                                except json.JSONDecodeError:
                                    parsing_attempts.append(
                                        "❌ Brace matching - invalid JSON"
                                    )
                    if json_match:
                        break

            # Log parsing attempts for debugging
            self.logger.debug(f"JSON parsing attempts: {parsing_attempts}")

            if json_match:
                try:
                    workflow_spec = json.loads(json_match)
                    self.logger.info("✅ Successfully parsed JSON from O3 response")

                    # Validate the specification structure
                    if self._validate_workflow_specification(workflow_spec):
                        self.logger.info("✅ Workflow specification validation passed")
                        return workflow_spec
                    else:
                        self.logger.warning(
                            "❌ Workflow specification validation failed - using fallback"
                        )

                except json.JSONDecodeError as e:
                    self.logger.warning(f"❌ Failed to parse matched JSON: {e}")

            # NO FALLBACKS RULE: System must fail completely if O3 generation fails
            self.logger.error(
                "❌ CRITICAL FAILURE: All O3 JSON parsing strategies failed. No fallbacks permitted per contract."
            )
            raise SystemError(
                "O3 WorkflowSpecification generation failed completely. "
                "System cannot proceed without valid O3-generated specifications. "
                "NO FALLBACKS PERMITTED per architectural contract."
            )

        except Exception as e:
            self.logger.error(
                f"❌ CRITICAL SYSTEM FAILURE: O3 response parsing failed: {e}"
            )
            raise SystemError(
                f"O3 WorkflowSpecification generation failed: {e}. "
                "System cannot proceed without valid O3-generated specifications. "
                "NO FALLBACKS PERMITTED per architectural contract."
            ) from e

    def _validate_workflow_specification(self, spec: dict[str, Any]) -> bool:
        """Validate the structure of a WorkflowSpecification"""
        required_fields = ["workflow_id", "agent_specifications"]

        for field in required_fields:
            if field not in spec:
                self.logger.warning(f"Missing required field: {field}")
                return False

        # Validate agent specifications - NO FALLBACKS
        if "agent_specifications" not in spec:
            self.logger.warning("Agent specifications missing from workflow spec")
            return False

        agents = spec["agent_specifications"]
        if not agents:
            self.logger.warning("No agent specifications found")
            return False

        for agent in agents:
            if not isinstance(agent, dict):
                continue

            required_agent_fields = ["agent_id", "role", "tools", "complete_prompt"]
            for field in required_agent_fields:
                if field not in agent:
                    self.logger.warning(f"Agent missing required field: {field}")
                    return False

        return True

    def _calculate_workflow_complexity(self, workflow_spec: dict[str, Any]) -> str:
        """Calculate the complexity of a workflow specification - NO FALLBACKS"""
        if "agent_specifications" not in workflow_spec:
            return "unknown"

        agents = workflow_spec["agent_specifications"]
        total_tools = sum(
            len(agent.get("tools") if "tools" in agent else []) for agent in agents
        )
        total_deliverables = sum(
            len(
                agent.get("required_deliverables")
                if "required_deliverables" in agent
                else []
            )
            for agent in agents
        )

        complexity_score = len(agents) * 2 + total_tools + total_deliverables

        if complexity_score <= 10:
            return "low"
        elif complexity_score <= 20:
            return "medium"
        else:
            return "high"
