import time
import logging
import os
import sys

from agent_base.agent_base import LLMBaseAgent


class ConsultAgent(LLMBaseAgent):
    """
    ConsultAgent (Architect) using OpenAI Responses API (o3) with session management.
    Specialized in generating detailed, actionable prompts for GPT-4.1 development agents in Cursor IDE.
    Leverages o3's advanced reasoning capabilities to create comprehensive prompts that guide GPT-4.1 agents through complex development tasks.
    Maintains conversation state per session_id, supports file attachments, and provides expert prompt engineering.
    """

    # In-memory session store: session_id -> {last_active, conversation_history}
    session_store = {}
    SESSION_TIMEOUT = 60 * 60  # 1 hour inactivity timeout
    MODEL = "o3"
    ASSISTANT_NAME = "Architect_o3"

    def __init__(self, api_key_env: str = "OPENAI_API_KEY", config: dict = None):
        super().__init__(name="ConsultAgent", api_key_env=api_key_env, config=config)
        # Set up comprehensive debug logging
        self.logger.setLevel(logging.DEBUG)
        self.logger.info("=== CONSULT AGENT INITIALIZED WITH DEBUG LOGGING ===")

    def _log_api_call(self, model: str, prompt_length: int, context: str = ""):
        """Log every API call with detailed information."""
        self.logger.debug("=== API CALL START ===")
        self.logger.debug(f"Model: {model}")
        self.logger.debug(f"Prompt length: {prompt_length} characters")
        self.logger.debug(f"Context: {context}")
        self.logger.debug(f"Timestamp: {time.time()}")

    def _log_api_response(self, response: dict, response_length: int):
        """Log every API response with detailed information."""
        self.logger.debug("=== API RESPONSE RECEIVED ===")
        self.logger.debug(f"Response length: {response_length} characters")
        self.logger.debug(f"Response keys: {list(response.keys())}")
        self.logger.debug(f"Has error: {'error' in response}")
        if "error" in response:
            self.logger.debug(f"Error details: {response['error']}")
        self.logger.debug(f"Timestamp: {time.time()}")

    def _log_critic_call(
        self, response_length: int, artifact_type: str, original_prompt: str
    ):
        """Log every critic API call with detailed information."""
        self.logger.debug("=== CRITIC API CALL START ===")
        self.logger.debug(f"Response to review length: {response_length} characters")
        self.logger.debug(f"Artifact type: {artifact_type}")
        self.logger.debug(f"Original prompt provided: {bool(original_prompt)}")
        self.logger.debug(f"Original prompt length: {len(original_prompt)} characters")
        self.logger.debug(f"Timestamp: {time.time()}")

    def _log_critic_response(self, critic_result: dict):
        """Log every critic response with detailed information."""
        self.logger.debug("=== CRITIC RESPONSE RECEIVED ===")
        self.logger.debug(f"Passed: {critic_result.get('passed', 'UNKNOWN')}")
        self.logger.debug(f"Feedback: {critic_result.get('feedback', 'NONE')}")
        self.logger.debug(
            f"Critical issues count: {len(critic_result.get('critical_issues', []))}"
        )
        self.logger.debug(
            f"Suggestions count: {len(critic_result.get('suggestions', []))}"
        )
        if critic_result.get("critical_issues"):
            for i, issue in enumerate(critic_result["critical_issues"]):
                self.logger.debug(f"Critical issue {i+1}: {issue}")
        if critic_result.get("suggestions"):
            for i, suggestion in enumerate(critic_result["suggestions"]):
                self.logger.debug(f"Suggestion {i+1}: {suggestion}")
        self.logger.debug(f"Timestamp: {time.time()}")

    def _session_expired(self, session):
        import time

        return time.time() - session["last_active"] > self.SESSION_TIMEOUT

    def _get_or_create_session(self, session_id):
        import time

        session = self.session_store.get(session_id)
        if not session or self._session_expired(session):
            # Use simple session tracking for Responses API
            session = {
                "session_id": session_id,
                "last_active": time.time(),
                "conversation_history": [],
            }
            self.session_store[session_id] = session
            self.logger.info(f"Started new session: {session_id}")
        else:
            session["last_active"] = time.time()
        return session

    def reset_session(self, session_id):
        import time

        # Use simple session tracking for Responses API
        session = {
            "session_id": session_id,
            "last_active": time.time(),
            "conversation_history": [],
        }
        self.session_store[session_id] = session
        self.logger.info(f"Session reset: {session_id}")
        return session

    def _get_artifact_guidance(self, artifact_type: str) -> str:
        """
        Get artifact-specific guidance for prompt generation.

        Args:
            artifact_type: The type of artifact being generated

        Returns:
            str: Artifact-specific guidance text
        """
        guidance_map = {
            "answer": """
## ARTIFACT TYPE: GENERAL ANSWER
**Purpose**: General responses and analysis without specific output format requirements

## ROLE PROFILE: STRATEGIC ANALYST
**Skills**: Systems thinking, pattern recognition, strategic planning, risk assessment
**Experience**: 10+ years in software architecture, system design, and technical strategy
**Focus**: Holistic analysis, cross-cutting concerns, long-term implications, strategic recommendations
**Behavioral Characteristics**:
- Thinks in systems and patterns rather than isolated components
- Considers multiple perspectives and trade-offs
- Focuses on actionable insights and strategic implications
- Balances technical depth with business impact
- Identifies root causes and systemic issues

**Requirements**:
- Provide comprehensive analysis and recommendations
- Include relevant context and background information
- Structure response logically with clear sections
- Include actionable insights and next steps
- Consider multiple perspectives and edge cases
**Output Format**: Well-structured markdown response with clear organization""",
            "plan": """
## ARTIFACT TYPE: PROJECT PLAN (.md)
**Purpose**: Comprehensive project planning and execution roadmaps

## ROLE PROFILE: PROJECT MANAGER & TECHNICAL ARCHITECT
**Skills**: Project planning, technical architecture, risk management, resource allocation, timeline management
**Experience**: 10+ years in project management, technical leadership, and software delivery
**Focus**: Strategic planning, execution feasibility, risk mitigation, stakeholder alignment, delivery excellence
**Behavioral Characteristics**:
- Thinks in terms of project phases, dependencies, and critical paths
- Prioritizes realistic timelines, resource constraints, and risk management
- Considers stakeholder needs, technical constraints, and business objectives
- Focuses on measurable outcomes, milestones, and success criteria
- Anticipates potential blockers, dependencies, and mitigation strategies
- Balances scope, timeline, and quality requirements
- Considers team dynamics, skill gaps, and capacity planning
- Plans for contingencies, rollback strategies, and change management

**Requirements**:
- Include project overview, objectives, and success criteria
- Define phases, milestones, and deliverables with timelines
- Identify risks, dependencies, and mitigation strategies
- Specify resource requirements, roles, and responsibilities
- Include technical architecture, design decisions, and constraints
- Provide stakeholder communication and governance structure
- Include quality gates, testing strategy, and deployment approach
- Specify monitoring, metrics, and success measurement criteria
**Output Format**: Comprehensive project plan in markdown with clear structure, timelines, and actionable items""",
            "code": """
## ARTIFACT TYPE: CODE (.py)
**Purpose**: Python scripts for specific functionality

## ROLE PROFILE: SENIOR PYTHON DEVELOPER
**Skills**: Python mastery, software engineering, debugging, performance optimization, testing
**Experience**: 8+ years in Python development, production systems, and software architecture
**Focus**: Code quality, maintainability, performance, security, production readiness
**Behavioral Characteristics**:
- Writes defensive, production-ready code with comprehensive error handling
- Prioritizes code clarity and maintainability over cleverness
- Thinks about edge cases, failure modes, and debugging scenarios
- Considers performance implications and resource usage
- Follows established patterns and best practices religiously
- Documents code for future maintainers

## DIRECT ARTIFACT GENERATION
You are a Senior Python Developer. Generate the actual Python code that the user has requested.

**Your Task**: Create production-quality Python code that:
- Includes proper imports and dependencies
- Has comprehensive error handling and logging
- Follows PEP 8 standards and type hints
- Includes docstrings and comments
- Is ready to run with minimal setup

**Output**: Return the complete Python code in a code block, ready to use.""",
            "prompt": """
## ARTIFACT TYPE: PROMPT (markdown)
**Purpose**: LLM prompts for specific tasks

## ROLE PROFILE: PROMPT ENGINEER
**Skills**: LLM optimization, prompt design, model behavior, human-AI interaction
**Experience**: 5+ years in prompt engineering, LLM optimization, and AI interaction design
**Focus**: Clarity, effectiveness, model alignment, user experience, prompt optimization
**Behavioral Characteristics**:
- Thinks in terms of model behavior, capabilities, and limitations
- Prioritizes clarity, specificity, and effective communication with AI
- Considers model context windows, token limits, and optimization strategies
- Focuses on prompt structure, examples, and verification mechanisms
- Anticipates model confusion, hallucination, and edge cases
- Balances detail with token efficiency
- Considers the target model's strengths and weaknesses
- Plans for prompt evolution and model updates

**Requirements**:
- Specify target model and expected output format
- Include clear constraints and examples
- Define role, objective, and audience
- Use structured formatting with clear sections
- Include verification steps and quality criteria
**Output Format**: Markdown-formatted prompt with examples""",
            "test": """
## ARTIFACT TYPE: TEST (.py)
**Purpose**: Test files for functionality validation

## ROLE PROFILE: TEST ENGINEER
**Skills**: Test automation, quality assurance, debugging, test design, coverage analysis
**Experience**: 6+ years in test engineering, quality assurance, and test automation
**Focus**: Quality, reliability, maintainability, comprehensive coverage, automation
**Behavioral Characteristics**:
- Thinks in terms of test scenarios, edge cases, and failure modes
- Prioritizes test reliability, maintainability, and comprehensive coverage
- Considers both positive and negative test cases
- Thinks about test data, fixtures, and test environment setup
- Anticipates potential failures and debugging scenarios
- Focuses on test automation and repeatability
- Considers test performance and execution time
- Plans for test maintenance and evolution

**Requirements**:
- Include unit tests, integration tests, and edge cases
- Use pytest framework and best practices
- Mock external dependencies appropriately
- Include test data and fixtures
- Specify test coverage requirements
**Output Format**: Python test file with comprehensive test cases""",
            "doc": """
## ARTIFACT TYPE: DOCUMENTATION (.md)
**Purpose**: Documentation with markdown formatting

## ROLE PROFILE: TECHNICAL WRITER
**Skills**: Technical communication, information architecture, user experience, visual design
**Experience**: 5+ years in technical writing, developer documentation, and user experience
**Focus**: Clarity, accessibility, user journey, information hierarchy, visual communication
**Behavioral Characteristics**:
- Thinks from the user's perspective and experience level
- Structures information for easy scanning and comprehension
- Uses visual elements (diagrams, tables, code blocks) to enhance understanding
- Anticipates user questions and provides answers proactively
- Balances completeness with conciseness
- Considers multiple learning styles and accessibility needs
- Creates documentation that ages well and stays relevant

**Requirements**:
- Use markdown formatting with clear structure
- Include mermaid diagrams where appropriate for visual clarity
- Provide usage examples and code snippets
- Include installation and setup instructions
- Specify target audience and technical depth
**Output Format**: Markdown documentation with diagrams and examples""",
            "diagram": """
## ARTIFACT TYPE: DIAGRAM (.mdd)
**Purpose**: Mermaid diagrams for visual representation

## ROLE PROFILE: SOLUTION ARCHITECT
**Skills**: System design, visual communication, information architecture, technical visualization
**Experience**: 8+ years in solution architecture, system design, and technical communication
**Focus**: Clarity, accuracy, visual hierarchy, accessibility, effective communication
**Behavioral Characteristics**:
- Thinks in terms of systems, components, and their interactions
- Prioritizes visual clarity and information hierarchy
- Considers the audience's technical background and needs
- Uses appropriate diagram types for different purposes (flow, sequence, architecture)
- Ensures diagrams are self-contained and understandable
- Balances detail with readability
- Considers accessibility and different viewing contexts
- Creates diagrams that serve multiple purposes (documentation, planning, communication)

**Requirements**:
- Use Mermaid syntax exclusively
- High contrast: Light text/lines on dark background OR dark text/lines on light background
- Ensure accessibility and readability
- Include proper labels and relationships
- Use appropriate diagram types (flowchart, sequence, class, etc.)
**Output Format**: Mermaid diagram with high contrast styling""",
            "query": """
## ARTIFACT TYPE: DATABASE QUERY (SQL/Cypher)
**Purpose**: Database queries for data operations

## ROLE PROFILE: DATABASE ADMINISTRATOR
**Skills**: Database optimization, query performance, data modeling, indexing strategies
**Experience**: 10+ years in database administration, query optimization, and data architecture
**Focus**: Performance, scalability, data integrity, security, optimization
**Behavioral Characteristics**:
- Thinks in terms of data relationships, indexes, and query execution plans
- Prioritizes query performance and resource efficiency
- Considers data volume, growth patterns, and scalability implications
- Thinks about data integrity, constraints, and validation
- Anticipates edge cases in data and query patterns
- Considers security implications and access patterns
- Plans for maintenance, monitoring, and troubleshooting

**Requirements**:
- ALWAYS include database schema in the request
- Provide table structures, relationships, and sample data
- Include proper error handling and optimization
- Specify query performance requirements
- Include expected output format and data types
**Output Format**: SQL or Cypher query with schema context""",
            "rule": """
## ARTIFACT TYPE: CURSOR RULE (.mdc)
**Purpose**: Cursor rules for development standards

## ROLE PROFILE: DEVELOPMENT STANDARDS ENGINEER
**Skills**: Process design, quality standards, automation, tooling, best practices
**Experience**: 7+ years in development standards, tooling, and process improvement
**Focus**: Consistency, automation, quality, maintainability, developer experience
**Behavioral Characteristics**:
- Thinks in terms of processes, standards, and consistency
- Prioritizes developer experience and productivity
- Considers automation, tooling, and integration points
- Focuses on maintainability and long-term sustainability
- Anticipates edge cases and exceptions in processes
- Balances flexibility with consistency
- Considers the impact on team productivity and quality
- Plans for evolution and improvement of standards

**Requirements**:
- MANDATORY: Reference @101-cursor-rules-generation-protocol.mdc
- MANDATORY: Place results in .cursor/rules/ directory
- Follow Cursor rules generation protocol exactly
- Include proper frontmatter and description
- Specify triggers, principles, and validation
**Output Format**: Cursor rule following the generation protocol""",
            "config": """
## ARTIFACT TYPE: CONFIGURATION (yaml/JSON/ini)
**Purpose**: Configuration files for applications/services

## ROLE PROFILE: DEVOPS ENGINEER
**Skills**: Infrastructure automation, configuration management, deployment, monitoring
**Experience**: 8+ years in DevOps, infrastructure, and configuration management
**Focus**: Automation, reliability, security, scalability, operational excellence
**Behavioral Characteristics**:
- Thinks in terms of infrastructure, deployment, and operational concerns
- Prioritizes automation, reliability, and security
- Considers environment-specific configurations and deployment strategies
- Focuses on monitoring, logging, and operational visibility
- Anticipates failure modes and recovery scenarios
- Balances flexibility with security and compliance
- Considers the impact on operations and maintenance
- Plans for scaling and evolution of infrastructure

**Requirements**:
- Include all required settings and environment variables
- Specify configuration format and structure
- Include validation and error handling
- Provide default values and examples
- Specify deployment and environment requirements
**Output Format**: Configuration file in specified format""",
            "schema": """
## ARTIFACT TYPE: DATABASE SCHEMA (.sql/.cypher)
**Purpose**: Database schema definitions

## ROLE PROFILE: DATA ARCHITECT
**Skills**: Data modeling, database design, performance optimization, data governance
**Experience**: 12+ years in data architecture, database design, and data modeling
**Focus**: Data integrity, performance, scalability, maintainability, governance
**Behavioral Characteristics**:
- Thinks in terms of data relationships, constraints, and business rules
- Prioritizes data integrity, performance, and scalability
- Considers data growth patterns, access patterns, and optimization strategies
- Focuses on data governance, security, and compliance
- Anticipates data quality issues and validation requirements
- Balances normalization with performance requirements
- Considers the impact on applications and reporting
- Plans for data evolution and migration strategies

**Requirements**:
- Include tables, relationships, indexes, and constraints
- Specify data types and validation rules
- Include foreign key relationships and constraints
- Provide migration scripts if needed
- Include performance optimization considerations
**Output Format**: Database schema with relationships and constraints""",
            "workflow": """
## ARTIFACT TYPE: CI/CD WORKFLOW (.yml)
**Purpose**: CI/CD workflow configurations

## ROLE PROFILE: CI/CD ENGINEER
**Skills**: Build automation, deployment pipelines, testing automation, infrastructure as code
**Experience**: 8+ years in CI/CD, build automation, and deployment engineering
**Focus**: Automation, reliability, speed, quality gates, deployment safety
**Behavioral Characteristics**:
- Thinks in terms of build pipelines, deployment stages, and automation
- Prioritizes reliability, speed, and quality in the delivery process
- Considers testing, security, and quality gates at each stage
- Focuses on deployment safety, rollback strategies, and monitoring
- Anticipates failure points and recovery mechanisms
- Balances automation with human oversight and approval
- Considers the impact on development velocity and quality
- Plans for pipeline evolution and optimization

**Requirements**:
- Include testing, security scanning, and deployment steps
- Specify build requirements and dependencies
- Include proper error handling and notifications
- Provide environment-specific configurations
- Include performance and resource optimization
**Output Format**: YAML workflow configuration""",
            "docker": """
## ARTIFACT TYPE: DOCKER CONFIGURATION (Dockerfile)
**Purpose**: Container configurations

## ROLE PROFILE: CONTAINER ENGINEER
**Skills**: Containerization, security, performance optimization, infrastructure automation
**Experience**: 6+ years in containerization, Docker, and container orchestration
**Focus**: Security, performance, reliability, maintainability, operational excellence
**Behavioral Characteristics**:
- Thinks in terms of containers, images, and container orchestration
- Prioritizes security, performance, and resource efficiency
- Considers multi-stage builds, layer optimization, and image size
- Focuses on security best practices and vulnerability management
- Anticipates runtime issues, resource constraints, and failure modes
- Balances optimization with maintainability and debugging capabilities
- Considers the impact on deployment, scaling, and operations
- Plans for container evolution and platform compatibility

**Requirements**:
- Include multi-stage builds for optimization
- Follow security best practices (non-root user, minimal base images)
- Include health checks and resource limits
- Specify environment variables and dependencies
- Include proper logging and monitoring setup
**Output Format**: Dockerfile with security and optimization""",
            "env": """
## ARTIFACT TYPE: ENVIRONMENT TEMPLATE (.env)
**Purpose**: Environment variable templates

## ROLE PROFILE: SECURITY ENGINEER
**Skills**: Security configuration, secrets management, compliance, risk assessment
**Experience**: 7+ years in security engineering, secrets management, and compliance
**Focus**: Security, compliance, risk management, operational security
**Behavioral Characteristics**:
- Thinks in terms of security, compliance, and risk management
- Prioritizes security best practices and secrets management
- Considers compliance requirements and audit trails
- Focuses on operational security and access control
- Anticipates security vulnerabilities and attack vectors
- Balances usability with security requirements
- Considers the impact on operations and compliance
- Plans for security evolution and threat landscape changes

**Requirements**:
- Include all required variables with descriptions
- Provide default values and examples
- Specify variable types and validation rules
- Include security considerations for sensitive data
- Provide deployment and environment guidance
**Output Format**: Environment file template with documentation""",
        }

        return guidance_map.get(artifact_type, "")

    def answer(
        self,
        prompt: str,
        session_id: str = "default",
        file_paths: list = None,
        artifact_type: str = None,
        iterate: int = None,
        critic_enabled: bool = False,
        model: str = None,
    ) -> dict:
        response_dict = {
            "result": "",
            "details": [],
            "session_id": session_id if "session_id" in locals() else "unknown",
            "analysis_type": "gpt4_prompt_generation",
            "file_analysis": bool(file_paths) if file_paths is not None else False,
            "iterations": 0,
        }
        try:
            session = self._get_or_create_session(session_id)

            # Validate model parameter against @953-openai-api-standards.mdc
            APPROVED_MODELS = {
                "o4-mini",
                "o3",
                "gpt-4.1-mini",
                "gpt-4.1",
                "gpt-4.1-nano",
            }
            if model is not None and model not in APPROVED_MODELS:
                raise ValueError(
                    f"UNAUTHORIZED MODEL: {model}. Only approved models are allowed: {', '.join(APPROVED_MODELS)}"
                )

            # Use provided model or default to o3
            selected_model = model if model is not None else self.MODEL

            # Initialize critic agent if enabled
            critic_agent = None
            if critic_enabled:
                self.logger.info("=== CRITIC INITIALIZATION START ===")
                # Debug: Show current working directory and Python path
                self.logger.debug(f"Current working directory: {os.getcwd()}")
                self.logger.debug(f"Python path: {sys.path}")
                self.logger.debug(f"Current file location: {__file__}")

                try:
                    from .critic_agent import CriticAgent

                    critic_agent = CriticAgent(api_key_env="OPENAI_API_KEY")
                    self.logger.info(
                        "Critic agent enabled for quality control (relative import)"
                    )
                except Exception as e:
                    self.logger.error(
                        f"Failed to initialize critic agent with relative import: {e}"
                    )
                    self.logger.error(f"Exception type: {type(e).__name__}")
                    self.logger.error(f"Exception details: {str(e)}")
                    try:
                        from capabilities.critic_agent import CriticAgent

                        critic_agent = CriticAgent(api_key_env="OPENAI_API_KEY")
                        self.logger.info(
                            "Critic agent enabled for quality control (absolute import)"
                        )
                    except Exception as e2:
                        self.logger.error(
                            f"Failed to initialize critic agent with absolute import: {e2}"
                        )
                        self.logger.error(f"Exception type: {type(e2).__name__}")
                        self.logger.error(f"Exception details: {str(e2)}")
                        critic_agent = None
                self.logger.info(
                    f"=== CRITIC INITIALIZATION END - Agent exists: {critic_agent is not None} ==="
                )

            # Use Responses interface for OpenAI API access
            from shared.openai_interfaces.responses_interface import (
                OpenAIResponsesInterface,
            )

            llm = OpenAIResponsesInterface(api_key=self.api_key)

            # Build context from conversation history and file analysis
            context_parts = []

            # Add conversation history for context
            if session["conversation_history"]:
                context_parts.append("Previous conversation context:")
                for entry in session["conversation_history"][-3:]:  # Last 3 exchanges
                    context_parts.append(f"Q: {entry.get('question', '')}")
                    context_parts.append(f"A: {entry.get('answer', '')}")
                context_parts.append("")

            # Add file analysis if files are provided
            file_analysis = ""
            if file_paths:
                self.logger.info(
                    f"Processing {len(file_paths)} files for architectural analysis"
                )
                file_analysis = "File Analysis:\n"
                for file_path in file_paths:
                    try:
                        # Validate file exists and is readable
                        if not os.path.exists(file_path):
                            self.logger.warning(f"File not found: {file_path}")
                            continue

                        # Read file content for analysis
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            file_analysis += (
                                f"\n--- {file_path} ---\n{content[:2000]}...\n"
                            )
                    except Exception as e:
                        self.logger.error(f"Error reading file {file_path}: {e}")
                        file_analysis += (
                            f"\n--- {file_path} ---\n[Error reading file: {e}]\n"
                        )

            # Build artifact-specific guidance
            artifact_guidance = ""
            if artifact_type:
                artifact_guidance = self._get_artifact_guidance(artifact_type)

            # Build the full prompt optimized for o3 reasoning capabilities
            if artifact_type:
                # Generate actual artifact content
                architectural_prompt = f"""You are a specialized professional with the role profile and expertise described below. Your mission is to generate the actual {artifact_type} artifact requested by the user.

{artifact_guidance}

## CORE MISSION
You are an expert in your field with the skills, experience, and behavioral characteristics outlined above. Generate the actual {artifact_type} content that the user has requested, following the requirements and output format specified in your role profile.

## TASK INSTRUCTIONS
1. **Analyze the user request**: Understand what specific {artifact_type} content is needed
2. **Apply your expertise**: Use your skills, experience, and behavioral characteristics to create high-quality content
3. **Follow requirements**: Adhere to the specific requirements and output format for {artifact_type}
4. **Ensure quality**: Meet the quality standards and best practices for your field
5. **Provide context**: Include necessary context, explanations, or metadata as appropriate

## KNOWLEDGE CONTEXT
{file_analysis}

## CONVERSATION HISTORY
{context_parts}

## USER REQUEST
{prompt}

## TASK
Generate the actual {artifact_type} content requested by the user. Follow your role profile, requirements, and output format specifications."""
            else:
                # Original prompt generation behavior
                architectural_prompt = f"""You are 'Architect', an expert prompt engineer and software architect specialized in generating detailed, actionable prompts for GPT-4.1 development agents in Cursor IDE environments.

## CORE MISSION
Your primary role is to analyze user requests and generate comprehensive, GPT-4.1-optimized prompts that enable development agents to execute tasks effectively. You leverage o3's advanced reasoning capabilities to create step-by-step, detailed prompts that guide GPT-4.1 agents through complex development tasks.

## GPT-4.1 PROMPT-WRITING RULES (MANDATORY)
- **Be super literal**: GPT-4.1 obeys instructions very exactly; don't rely on implications—explicitly state every requirement.
- **Define Role, Objective, and Audience**: Start by declaring who the assistant is, what its goal is, and who it's writing for. Clarity improves relevance.
- **Use structured formatting**: Leverage Markdown headers, XML, or clear delimiting to organize sections—role, task, planning, output.
- **Include step-by-step planning**: Prompt GPT-4.1 to first produce a reasoning plan (chain-of-thought), then execute it.
- **Bookend instructions in long-context prompts**: Repeat key instructions at both the start and the end of the context for best performance. If only once, put them before the context.
- **Spell out "do-not" behavior**: Add lines like "Do not guess," "If unsure, say 'I don't know'," "Only use the given context unless asked otherwise."
- **Specify output format clearly**: State desired format (Markdown, JSON, bullet list, table, code block), tone, word limit, structure.
- **Use few-shot examples when useful**: Provide one or more exemplar inputs/outputs to model expected style.
- **Account for token limits**: GPT-4.1 handles up to 1M tokens—avoid overloading; keep prompts compact when possible.
- **Structure tool definitions explicitly**: When using tools, name tools clearly, include detailed `description`, parameter definitions, and usage examples in a dedicated section—not buried in prose.
- **Avoid conflicting instructions**: Keep instructions consistent; if conflict, the last one usually wins—don't rely on implicit overrides.
- **Use minimal control tokens or macro keywords**: One-word prompts like "Clarify," "Stack," "Pulsecheck" can produce strong, repeatable patterns.
- **Iterate and refine prompts empirically**: Test prompts, observe behavior, tweak wording, ordering, specificity to improve performance.
- **Encourage verification mindset**: Add instructions like "Identify relevant sources", "Verify factual claims where possible", "Pause to review each step." Limits hallucination.
- **Prefer structure over natural conversation when precision matters**: Use clearly marked sections rather than free-floating instructions.
- **Avoid emotional tone or all-caps drama**: GPT-4.1 treats such phrasing literally; keep prompts professional and logical.

## REASONING PROCESS (o3 OPTIMIZED)
1. **Analyze the user request**: Break down the request into its core components and objectives
2. **Identify the target agent's role**: Determine what type of GPT-4.1 agent will execute this task
3. **Structure the prompt**: Create a comprehensive prompt that follows GPT-4.1 best practices
4. **Include context and constraints**: Provide necessary background information and limitations
5. **Define success criteria**: Specify what constitutes successful completion of the task
6. **Add verification steps**: Include instructions for the agent to verify its work

## OUTPUT FORMAT
Generate a complete, ready-to-use prompt that includes:
- **Role Definition**: Clear statement of who the GPT-4.1 agent is and its purpose
- **Task Description**: Detailed explanation of what needs to be accomplished
- **Step-by-Step Instructions**: Structured guidance for execution
- **Context and Constraints**: Relevant background information and limitations
- **Expected Output Format**: Specific format requirements for the response
- **Quality Criteria**: Standards for successful completion
- **Verification Instructions**: Steps to ensure accuracy and completeness

## KNOWLEDGE CONTEXT
{file_analysis}

{artifact_guidance}

## CONVERSATION HISTORY
{context_parts}

## USER REQUEST
{prompt}

## TASK
Generate a detailed, actionable prompt for a GPT-4.1 development agent to execute this request in the local project. The prompt should be comprehensive, well-structured, and optimized for GPT-4.1's capabilities and limitations."""

            # Initialize iteration variables
            current_response = ""
            iteration_count = 0
            max_iterations = iterate if iterate else 1

            # Store original context for iterations
            original_context = {
                "prompt": prompt,
                "file_analysis": file_analysis,
                "artifact_guidance": artifact_guidance,
                "context_parts": context_parts,
                "artifact_type": artifact_type,
            }

            # Iteration loop
            while iteration_count < max_iterations:
                iteration_count += 1
                self.logger.info(
                    f"Starting iteration {iteration_count}/{max_iterations}"
                )

                # Build the prompt for this iteration
                if iteration_count == 1:
                    # First iteration - use original prompt
                    current_prompt = architectural_prompt
                else:
                    # Subsequent iterations - add iteration guidance
                    iteration_guidance = """
## ITERATION REVIEW INSTRUCTIONS
Review the previous response for errors, omissions, unclear points, inefficiency, or any area that could be clarified, optimized, or enhanced. Improve the response for accuracy, completeness, clarity, and practical value.

After revising, evaluate whether another review would likely add significant value.
If not, append [STOP] to your output; otherwise, do not include [STOP].

Output only the improved response, appending [STOP] if you determine further iteration is unnecessary.

## PREVIOUS RESPONSE TO IMPROVE
"""

                    # Rebuild the prompt for iteration
                    if artifact_type:
                        current_prompt = f"""You are a specialized professional with the role profile and expertise described below. Your mission is to generate the actual {artifact_type} artifact requested by the user.

{artifact_guidance}

## CORE MISSION
You are an expert in your field with the skills, experience, and behavioral characteristics outlined above. Generate the actual {artifact_type} content that the user has requested, following the requirements and output format specified in your role profile.

## TASK INSTRUCTIONS
1. **Analyze the user request**: Understand what specific {artifact_type} content is needed
2. **Apply your expertise**: Use your skills, experience, and behavioral characteristics to create high-quality content
3. **Follow requirements**: Adhere to the specific requirements and output format for {artifact_type}
4. **Ensure quality**: Meet the quality standards and best practices for your field
5. **Provide context**: Include necessary context, explanations, or metadata as appropriate

{iteration_guidance}

{current_response}

## KNOWLEDGE CONTEXT
{file_analysis}

## CONVERSATION HISTORY
{context_parts}

## USER REQUEST
{prompt}

## TASK
Generate the actual {artifact_type} content requested by the user. Follow your role profile, requirements, and output format specifications."""
                    else:
                        current_prompt = f"""You are Architect, an expert prompt engineer specializing in creating detailed, actionable prompts for GPT-4.1 development agents. You leverage o3's advanced reasoning capabilities to generate comprehensive prompts that guide GPT-4.1 agents through complex development tasks.

{iteration_guidance}

{current_response}

## GPT-4.1 PROMPT-WRITING RULES (MANDATORY)
- **Be super literal**: GPT-4.1 obeys instructions very exactly; don't rely on implications—explicitly state every requirement.
- **Define Role, Objective, and Audience**: Start by declaring who the assistant is, what its goal is, and who it's writing for. Clarity improves relevance.
- **Use structured formatting**: Leverage Markdown headers, XML, or clear delimiting to organize sections—role, task, planning, output.
- **Include step-by-step planning**: Prompt GPT-4.1 to first produce a reasoning plan (chain-of-thought), then execute it.
- **Bookend instructions in long-context prompts**: Repeat key instructions at both the start and the end of the context for best performance. If only once, put them before the context.
- **Spell out "do-not" behavior**: Add lines like "Do not guess," "If unsure, say 'I don't know'," "Only use the given context unless asked otherwise."
- **Specify output format clearly**: State desired format (Markdown, JSON, bullet list, table, code block), tone, word limit, structure.
- **Use few-shot examples when useful**: Provide one or more exemplar inputs/outputs to model expected style.
- **Account for token limits**: GPT-4.1 handles up to 1M tokens—avoid overloading; keep prompts compact when possible.
- **Structure tool definitions explicitly**: When using tools, name tools clearly, include detailed `description`, parameter definitions, and usage examples in a dedicated section—not buried in prose.
- **Avoid conflicting instructions**: Keep instructions consistent; if conflict, the last one usually wins—don't rely on implicit overrides.
- **Use minimal control tokens or macro keywords**: One-word prompts like "Clarify," "Stack," "Pulsecheck" can produce strong, repeatable patterns.
- **Iterate and refine prompts empirically**: Test prompts, observe behavior, tweak wording, ordering, specificity to improve performance.
- **Encourage verification mindset**: Add instructions like "Identify relevant sources", "Verify factual claims where possible", "Pause to review each step." Limits hallucination.
- **Prefer structure over natural conversation when precision matters**: Use clearly marked sections rather than free-floating instructions.
- **Avoid emotional tone or all-caps drama**: GPT-4.1 treats such phrasing literally; keep prompts professional and logical.

## REASONING PROCESS (o3 OPTIMIZED)
1. **Analyze the user request**: Break down the request into its core components and objectives
2. **Identify the target agent's role**: Determine what type of GPT-4.1 agent will execute this task
3. **Structure the prompt**: Create a comprehensive prompt that follows GPT-4.1 best practices
4. **Include context and constraints**: Provide necessary background information and limitations
5. **Define success criteria**: Specify what constitutes successful completion of the task
6. **Add verification steps**: Include instructions for the agent to verify its work

## OUTPUT FORMAT
Generate a complete, ready-to-use prompt that includes:
- **Role Definition**: Clear statement of who the GPT-4.1 agent is and its purpose
- **Task Description**: Detailed explanation of what needs to be accomplished
- **Step-by-Step Instructions**: Structured guidance for execution
- **Context and Constraints**: Relevant background information and limitations
- **Expected Output Format**: Specific format requirements for the response
- **Quality Criteria**: Standards for successful completion
- **Verification Instructions**: Steps to ensure accuracy and completeness

## KNOWLEDGE CONTEXT
{file_analysis}

## CONVERSATION HISTORY
{context_parts}

## USER REQUEST
{prompt}

## TASK
Generate a detailed, actionable prompt for a GPT-4.1 development agent to execute this request in the local project. The prompt should be comprehensive, well-structured, and optimized for GPT-4.1's capabilities and limitations."""

                # Use selected model for complex reasoning/architecture
                self._log_api_call(selected_model, len(current_prompt))
                response = llm.create_response(
                    model=selected_model,
                    input=current_prompt,
                )

                # Extract response from shared interface
                if "error" in response:
                    self.logger.error(f"API Error: {response['error']}")
                    current_response = f"API Error: {response['error']}"
                    break
                else:
                    current_response = (
                        response.get("output_text") or response.get("answer") or ""
                    )

                self._log_api_response(response, len(current_response))

                self.logger.debug(
                    f"ConsultAgent iteration {iteration_count} output length: {len(current_response)} characters"
                )
                self.logger.debug("=== CONSULT AGENT RESPONSE CONTENT ===")
                self.logger.debug(current_response)
                self.logger.debug("=== END CONSULT AGENT RESPONSE CONTENT ===")

                # Critic review if enabled
                self.logger.info("=== CRITIC STATUS CHECK ===")
                self.logger.info(f"Critic agent exists: {critic_agent is not None}")
                self.logger.info(f"Critic enabled: {critic_enabled}")

                if critic_agent and critic_enabled:
                    self.logger.info(
                        f"Running critic review for iteration {iteration_count}"
                    )
                    # Build context for critic
                    context_info = f"Artifact type: {artifact_type or 'prompt'}"
                    if file_paths:
                        context_info += f", Files analyzed: {len(file_paths)}"

                    # Run critic review - don't pass original prompt for first few iterations
                    # to make critic more likely to catch actual errors
                    critic_prompt = "" if iteration_count <= 2 else prompt
                    critic_result = critic_agent.review_response(
                        response=current_response,
                        artifact_type=artifact_type,
                        original_prompt=critic_prompt,
                        context=context_info,
                    )
                    self._log_critic_response(critic_result)

                    # Log critic results
                    self.logger.info(
                        f"Critic review: {'PASSED' if critic_result['passed'] else 'FAILED'}"
                    )
                    if not critic_result["passed"]:
                        self.logger.warning(
                            f"Critic feedback: {critic_result['feedback']}"
                        )
                        for issue in critic_result["critical_issues"]:
                            self.logger.warning(f"Critical issue: {issue}")

                    # If critic failed and we haven't hit max retries, force another iteration
                    if not critic_result["passed"]:
                        max_critic_retries = 3  # Hardcoded threshold
                        if iteration_count < max_critic_retries:
                            self.logger.warning(
                                f"Critic failed - forcing retry {iteration_count + 1}/{max_critic_retries}"
                            )
                            # Don't break - continue to next iteration
                            continue
                        else:
                            self.logger.error(
                                f"Critic failed after {max_critic_retries} attempts - logging for human review"
                            )
                            # Add critic feedback to response details
                            current_response += f"\n\n## CRITIC REVIEW (FAILED AFTER {max_critic_retries} ATTEMPTS)\n"
                            current_response += (
                                f"**Feedback**: {critic_result['feedback']}\n"
                            )
                            if critic_result["critical_issues"]:
                                current_response += "**Critical Issues**:\n"
                                for issue in critic_result["critical_issues"]:
                                    current_response += f"- {issue}\n"
                            if critic_result["suggestions"]:
                                current_response += "**Suggestions**:\n"
                                for suggestion in critic_result["suggestions"]:
                                    current_response += f"- {suggestion}\n"
                            current_response += "\n**NOTE**: This response failed critic review and requires human review."
                            break
                    else:
                        # Critic passed - add suggestions if any
                        if critic_result["suggestions"]:
                            self.logger.info(
                                f"Critic passed with {len(critic_result['suggestions'])} suggestions"
                            )
                            # Add suggestions as comments/notes in the response
                            if artifact_type == "code":
                                current_response += "\n\n# Critic Suggestions:\n"
                                for suggestion in critic_result["suggestions"]:
                                    current_response += f"# {suggestion}\n"
                            else:
                                current_response += "\n\n## Critic Suggestions:\n"
                                for suggestion in critic_result["suggestions"]:
                                    current_response += f"- {suggestion}\n"
                else:
                    self.logger.warning(
                        "Critic review skipped - agent not available or not enabled"
                    )
                    # Add debug message to response details
                    if "details" in response_dict:
                        response_dict["details"].append(
                            "Critic review skipped: critic agent not initialized or not enabled."
                        )

                # Check for STOP signal
                if "[STOP]" in current_response:
                    current_response = current_response.replace("[STOP]", "").strip()
                    self.logger.info(
                        f"STOP signal detected at iteration {iteration_count}"
                    )
                    break

            # Update conversation history with final response
            session["conversation_history"].append(
                {
                    "question": prompt,
                    "answer": current_response,
                    "timestamp": time.time(),
                }
            )

            # Enhanced response with prompt generation context
            response_dict["result"] = current_response
            response_dict["iterations"] = iteration_count

            # Add debug info directly to the result text
            debug_info = []
            if critic_enabled:
                debug_info.append(f"Critic enabled: {critic_enabled}")
                debug_info.append(f"Critic agent exists: {critic_agent is not None}")
                if critic_agent:
                    debug_info.append("Critic agent initialized successfully")
                else:
                    debug_info.append("ERROR: Critic agent failed to initialize")

                debug_info.append(f"Session ID: {session_id}")
                debug_info.append(f"Artifact type: {artifact_type}")
                debug_info.append(f"Iterations: {iteration_count}")

            if debug_info:
                response_dict["result"] += "\n\n=== DEBUG INFO ===\n"
                for info in debug_info:
                    response_dict["result"] += f"- {info}\n"
                response_dict["result"] += "=== END DEBUG INFO ===\n"

            # Add critic status to response details for debugging
            if critic_enabled:
                response_dict["details"].append(f"Critic enabled: {critic_enabled}")
                response_dict["details"].append(
                    f"Critic agent exists: {critic_agent is not None}"
                )
                if critic_agent:
                    response_dict["details"].append(
                        "Critic agent initialized successfully"
                    )
                else:
                    response_dict["details"].append(
                        "ERROR: Critic agent failed to initialize"
                    )

                # Force debug info into response
                response_dict["details"].append("=== DEBUG INFO ===")
                response_dict["details"].append(f"Session ID: {session_id}")
                response_dict["details"].append(f"Artifact type: {artifact_type}")
                response_dict["details"].append(f"Iterations: {iteration_count}")
                response_dict["details"].append("=== END DEBUG INFO ===")

            # Add file analysis summary if files were processed
            if file_paths:
                response_dict["details"].append(
                    f"Analyzed {len(file_paths)} files for prompt context"
                )

            # Add iteration summary
            if iterate and iterate > 1:
                response_dict["details"].append(
                    f"Completed {iteration_count} iterations to improve response quality"
                )

            # Add critic summary if enabled
            if critic_enabled:
                response_dict["details"].append(
                    "Critic review enabled - quality control applied"
                )

            return response_dict

        except Exception as e:
            self.logger.error(f"ConsultAgent error: {e}")
            import traceback

            self.logger.error(f"Traceback: {traceback.format_exc()}")
            response_dict["result"] = f"Error generating GPT-4.1 prompt: {str(e)}"
            response_dict["details"] = [
                f"Error: {str(e)}",
                f"Traceback: {traceback.format_exc()}",
            ]
            return response_dict
