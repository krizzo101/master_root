"""
OAMAT Workflow Manager: Intelligent Central Orchestration Engine

This agent serves as the primary intelligence coordinator for OAMAT LangGraph-based
agentic workflow system. It possesses comprehensive understanding of:
- System architecture and capabilities
- Agent specializations and optimal usage patterns
- Tool ecosystem and integration strategies
- Workflow design methodologies and best practices
- Error handling and escalation protocols

The WorkflowManager transforms natural language requests into sophisticated,
executable workflows with runtime adaptation capabilities.
"""

import json
import logging
import traceback
from datetime import datetime
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from src.applications.oamat.agents.llm_base_agent import (
    LLMBaseAgent,
)
from src.applications.oamat.agents.manager.request_analyzer import RequestAnalyzer
from src.applications.oamat.agents.manager.utilities import (
    extract_json_from_response,
    serialize_analysis,
)
from src.applications.oamat.agents.models import (
    ClarificationQuestion,
    DynamicQuestionUpdate,
    EnhancedRequestAnalysis,
    EnhancedWorkflowPlan,
    ExpandedPrompt,
    ProcessingRequest,
    ProcessingResponse,
    QuestionAnswer,
    QuestionCategory,
    RefinedSpecification,
    RefinedSpecUpdate,
    TaskComplexity,
    UserClarificationResponse,
    WorkflowStrategy,
)

# Import from modular components
from src.applications.oamat.agents.registry import (
    AGENT_REGISTRY,
    MCP_TOOL_REGISTRY,
    OPERATIONAL_GUIDELINES,
    SYSTEM_IDENTITY,
    WORKFLOW_PATTERNS,
)
from src.applications.oamat.oamat_logging import log_prompt_response
from src.applications.oamat.utils.rule_loader import get_rules_for_agent

logger = logging.getLogger("OAMAT.WorkflowManager")
manager_logger = logging.getLogger("oamat.manager")

# All constants and registries are now imported from registry.py module

# AGENT_REGISTRY is now imported from registry


class WorkflowManager(LLMBaseAgent):
    """
    Enhanced WorkflowManager with sophisticated orchestration capabilities
    """

    def __init__(self, neo4j_client=None, model: str = "o3-mini"):
        super().__init__(
            agent_name="workflow_manager",
            role="workflow_orchestration",
            expertise=["workflow_design", "agent_coordination", "task_analysis"],
            model=model,
        )
        self.system_identity = SYSTEM_IDENTITY
        self.agent_registry = AGENT_REGISTRY
        self.tool_registry = MCP_TOOL_REGISTRY
        self.workflow_patterns = WORKFLOW_PATTERNS
        self.operational_guidelines = OPERATIONAL_GUIDELINES

        self.request_analyzer = RequestAnalyzer(self)

        # Dynamic persona that evolves with understanding
        self.current_persona = None
        self.understanding_evolution = {}

        # Enhanced analysis capabilities
        self.analysis_history = []
        self.workflow_performance_metrics = {}

        # Load rules for this agent
        self.rules = get_rules_for_agent("workflow_manager")

    def _generate_dynamic_persona(
        self,
        user_request: str,
        task_context: dict[str, Any],
        understanding_level: str = "initial",
    ) -> str:
        """
        Generate a dynamic persona based on the user request and current understanding.
        This persona evolves as the agent gains deeper understanding of the task.
        """
        base_persona = f"""You are the OAMAT Workflow Manager, a sophisticated AI orchestration engine with deep expertise in:

**CORE COMPETENCIES:**
- Intelligent workflow design and optimization
- Multi-agent coordination and task delegation
- Tool ecosystem mastery and integration strategies
- Risk assessment and mitigation planning
- Quality assurance and success criteria definition

**CURRENT CONTEXT UNDERSTANDING:**
Request Domain: {task_context.get('domain_category', 'general')}
Complexity Level: {task_context.get('complexity', 'moderate')}
Understanding Phase: {understanding_level}

**OPERATIONAL EXCELLENCE:**
- Transform ambiguous requests into executable workflows
- Optimize for efficiency, quality, and reliability
- Anticipate edge cases and failure scenarios
- Provide clear reasoning for all decisions
- Maintain awareness of resource constraints and dependencies

**RESPONSE STYLE:**
- Be thorough yet concise in analysis
- Provide structured, actionable recommendations
- Explain complex technical concepts clearly
- Maintain professional confidence while acknowledging uncertainties
- Focus on practical, implementable solutions

**CURRENT TASK FOCUS:**
{user_request[:200]}{'...' if len(user_request) > 200 else ''}

**ADAPTIVE INTELLIGENCE:**
Your persona and approach should evolve as you gain deeper understanding of the user's needs, technical constraints, and success criteria. Always strive for the optimal balance between comprehensive planning and practical execution."""

        # Enhance persona based on understanding evolution
        if self.understanding_evolution:
            evolution_context = self._format_understanding_evolution()
            base_persona += f"\n\n**EVOLVED UNDERSTANDING:**\n{evolution_context}"

        return base_persona

    def _format_understanding_evolution(self) -> str:
        """Format the understanding evolution for persona enhancement"""
        if not self.understanding_evolution:
            return "No evolution data available."

        evolution_summary = []
        for phase, insights in self.understanding_evolution.items():
            if insights:
                evolution_summary.append(
                    f"- {phase.title()}: {insights.get('key_insight', 'Processing...')}"
                )

        return (
            "\n".join(evolution_summary)
            if evolution_summary
            else "Understanding is developing..."
        )

    def _update_persona_for_understanding_evolution(
        self, new_understanding: dict[str, Any]
    ) -> None:
        """Update the current understanding and regenerate persona if needed"""
        phase = new_understanding.get("phase", "analysis")
        insights = new_understanding.get("insights", {})

        if phase not in self.understanding_evolution:
            self.understanding_evolution[phase] = {}

        self.understanding_evolution[phase].update(insights)

        # Regenerate persona with new understanding
        if hasattr(self, "_last_request_context"):
            self.current_persona = self._generate_dynamic_persona(
                self._last_request_context.get("user_request", ""),
                self._last_request_context.get("task_context", {}),
                understanding_level="evolved",
            )

    def _analyze_task_context(
        self, user_request: str, context: dict[str, Any] = None
    ) -> dict[str, Any]:
        """Analyze the task context for persona generation"""
        # This would typically involve more sophisticated analysis
        # For now, provide basic context analysis
        return {
            "domain_category": (
                context.get("domain", "general") if context else "general"
            ),
            "complexity": "moderate",  # Would be determined by actual analysis
            "user_preferences": context.get("preferences", {}) if context else {},
        }

    def _get_contextual_system_identity(
        self, task_context: dict[str, Any] = None, understanding_level: str = "initial"
    ) -> str:
        """Get system identity with contextual enhancements"""
        base_identity = self.system_identity

        # Initialize contextual_enhancement with a default value
        contextual_enhancement = ""

        if task_context:
            domain = task_context.get("domain_category", "general")
            complexity = task_context.get("complexity", "moderate")

            contextual_enhancement = f"""

**CONTEXTUAL SPECIALIZATION:**
- Domain Focus: {domain.title()}
- Complexity Level: {complexity.title()}
- Understanding Phase: {understanding_level.title()}

**ADAPTIVE CAPABILITIES:**
Your responses should be tailored to the specific domain and complexity level while maintaining your core competencies in workflow orchestration and multi-agent coordination."""

        return base_identity + contextual_enhancement

    def process_request(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Process a request and return structured response"""
        request = ProcessingRequest(**input_data)

        # Analyze the request using the dedicated analyzer
        analysis = self.request_analyzer.analyze_request(
            request.user_request, request.context
        )

        # Generate workflow
        workflow = self.generate_sophisticated_workflow(
            analysis, request.user_request, request.context
        )

        return ProcessingResponse(
            success=True,
            analysis=analysis,
            workflow=workflow,
            agent="workflow_manager",
        ).model_dump()

    def modify_workflow_plan(
        self,
        original_plan: EnhancedWorkflowPlan,
        modification_request: str,
        context: dict | None = None,
    ) -> EnhancedWorkflowPlan:
        """Modifies an existing workflow plan based on user feedback."""
        modification_prompt = f"""
Modify the following workflow plan based on the user's request.

ORIGINAL PLAN:
{original_plan.model_dump_json(indent=2)}

MODIFICATION REQUEST:
"{modification_request}"

Return only the new, modified EnhancedWorkflowPlan JSON object.
"""
        messages = [
            SystemMessage(content=self.system_identity),
            HumanMessage(content=modification_prompt),
        ]
        modified_plan = self.llm_call(messages, response_format=EnhancedWorkflowPlan)
        return modified_plan

    def create_enhanced_workflow_plan(
        self,
        user_request: str,
        context: dict | None = None,
        interactive: bool = False,
    ) -> EnhancedWorkflowPlan:
        """Creates a new workflow plan, typically for regeneration."""

        # Enhanced logging for manager agent activity
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        # Log the manager agent invocation with full details
        manager_log = f"""
========================================
🧠 MANAGER AGENT INVOCATION
========================================
TIMESTAMP: {timestamp}
METHOD: create_enhanced_workflow_plan
USER REQUEST: {user_request}
CONTEXT: {json.dumps(context, indent=2) if context else "None"}
INTERACTIVE: {interactive}
========================================
"""
        print(manager_log)
        manager_logger.info(manager_log)
        logger.info(
            f"Manager Agent: create_enhanced_workflow_plan called for request: {user_request[:100]}..."
        )

        # Generate the workflow and capture the result
        result = self.generate_enhanced_workflow_with_clarification(
            user_request, context, interactive
        )

        # Log the manager agent response
        result_log = f"""
========================================
🧠 MANAGER AGENT RESPONSE
========================================
TIMESTAMP: {datetime.now().strftime("%H:%M:%S.%f")[:-3]}
WORKFLOW CREATED: {result.title if result else "FAILED"}
NODES COUNT: {len(result.nodes) if result and result.nodes else 0}
ESTIMATED DURATION: {result.estimated_duration_minutes if result else "N/A"} minutes
SUCCESS CRITERIA: {len(result.success_criteria) if result and result.success_criteria else 0} items
WORKFLOW STRATEGY: {getattr(result, 'strategy', 'N/A') if result else "N/A"}
NODE DETAILS:
"""

        if result and result.nodes:
            for i, node in enumerate(result.nodes):
                result_log += (
                    f"  Node {i+1}: {node.agent_role} - {node.description[:80]}...\n"
                )
        else:
            result_log += "  NO NODES CREATED\n"

        result_log += "========================================"
        print(result_log)
        manager_logger.info(result_log)
        logger.info(
            f"Manager Agent: Workflow plan created with {len(result.nodes) if result and result.nodes else 0} nodes"
        )

        return result

    def generate_sophisticated_workflow(
        self,
        analysis: EnhancedRequestAnalysis,
        user_request: str,
        context: dict[str, Any] = None,
    ) -> EnhancedWorkflowPlan:
        """
        Generate sophisticated workflow based on comprehensive analysis
        """
        try:
            # Update persona for workflow generation
            self.current_persona = self._generate_dynamic_persona(
                user_request, analysis.context_understanding, "workflow_generation"
            )

            # Build sophisticated workflow prompt
            workflow_prompt = f"""As the OAMAT Workflow Manager, design a sophisticated workflow based on this analysis:

**ANALYSIS SUMMARY:**
{serialize_analysis(analysis)}

**ORIGINAL REQUEST:**
{user_request}

**CONTEXT:**
{json.dumps(context, indent=2) if context else "No additional context"}

**YOUR ENHANCED PERSONA:**
{self.current_persona}

**WORKFLOW DESIGN REQUIREMENTS:**

1. **Strategic Orchestration**: Design based on {analysis.workflow_strategy.value} strategy
2. **Agent Utilization**: Optimize use of recommended agents: {', '.join(analysis.recommended_agents)}
3. **Tool Integration**: Incorporate required tools: {', '.join(analysis.required_tools)}
4. **Quality Assurance**: Implement success criteria and quality gates
5. **Risk Mitigation**: Address identified risks and uncertainty factors
6. **Efficiency Optimization**: Maximize parallel execution where appropriate

**AVAILABLE RESOURCES:**

**Agent Registry:**
{json.dumps(AGENT_REGISTRY, indent=2)}

**Tool Registry:**
{json.dumps(MCP_TOOL_REGISTRY, indent=2)}

**Workflow Patterns:**
{json.dumps(WORKFLOW_PATTERNS, indent=2)}

**DESIGN PRINCIPLES:**
- Create clear, actionable nodes with specific parameters
- Ensure proper dependency management and flow control
- Include comprehensive error handling and risk mitigation
- Optimize for both efficiency and reliability
- Provide detailed success criteria and quality gates

**INTELLIGENT SUBDIVISION MARKING (CRITICAL):**
For each node you create, intelligently analyze if it should be subdivided:

**Mark `requires_subdivision: true` if the node:**
- Involves multiple technical domains (e.g., frontend + backend + database)
- Will generate many files OR substantial/complex individual files
- Requires complex directory structures with multiple subdirectories
- Can be parallelized into distinct, independent components
- Involves multi-step implementation across different technology stacks
- Represents a large scope that would benefit from focused, specialized attention

**Set subdivision metadata:**
- `subdivision_reasoning`: Why this node needs subdivision (focus on scope, structure, domain complexity)
- `estimated_sub_nodes`: How many sub-nodes (based on natural decomposition of deliverables)
- `suggested_sub_roles`: Specific agent roles for subdivision (aligned with major components/domains)
- `complexity_score`: 0.0 (simple) to 1.0 (very complex)
- `parallelization_potential`: 0.0 (sequential) to 1.0 (highly parallel)

**Examples:**
- "coder" building full e-commerce platform (many files, multiple domains) → `requires_subdivision: true`, `suggested_sub_roles: ["frontend_developer", "backend_developer", "database_specialist"]`
- "frontend_developer" creating complex UI with many subdirectories → `requires_subdivision: true`, `suggested_sub_roles: ["component_developer", "page_developer", "styling_specialist"]`
- "coder" generating multiple substantial files → `requires_subdivision: true`, with each major file/module getting its own focused developer
- "coder" generating few simple, small files → `requires_subdivision: false` (manageable scope for single agent)
- "doc" writing single API reference → `requires_subdivision: false` (atomic task)

**OUTPUT REQUIREMENTS:**
Return a structured workflow plan that matches the EnhancedWorkflowPlan schema exactly.
Ensure all nodes have proper agent_role assignments from the available registry.
Include estimated durations and resource requirements.
Design for maximum automation while maintaining quality standards.
**CRITICAL**: Mark subdivision candidates intelligently during generation to eliminate later evaluation overhead.

**CRITICAL FORMATTING REQUIREMENTS:**
- All list fields (success_criteria, quality_requirements, etc.) must be arrays of strings
- Never return objects or dictionaries for list fields
- All node.parameters must be valid JSON strings
- All duration fields must be integers (minutes)
- IMPORTANT: next_nodes field must contain agent_role names (e.g., "frontend_developer", "tester"), NOT node IDs like "node2", "node3"
- For workflow flow: Use actual agent role names in next_nodes to specify which agent(s) execute next

**WORKFLOW NODE EXAMPLE:**
{{
  "agent_role": "planner",
  "description": "Plan the project structure and requirements",
  "next_nodes": ["frontend_developer", "backend_developer"]  // ✅ CORRECT: agent role names
}}

NOT:
{{
  "agent_role": "planner",
  "next_nodes": ["node2", "node3"]  // ❌ WRONG: generic node IDs
}}"""

            # Enhanced logging for LLM interaction
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

            # Log prompt with truncation for debug/console and full content for API
            log_prompt_response(
                content=workflow_prompt,
                content_type="prompt",
                context="Manager Agent - Workflow Generation",
                timestamp=timestamp,
                debug_mode=True,
            )

            prompt_log = f"""
========================================
🧠 MANAGER AGENT LLM CALL - WORKFLOW GENERATION
========================================
TIMESTAMP: {timestamp}
SYSTEM IDENTITY: {self._get_contextual_system_identity()[:200]}...
PROMPT LENGTH: {len(workflow_prompt)} characters
========================================
"""
            # Log verbose details to debug/manager files only, not console
            manager_logger.info(prompt_log)

            # Generate workflow with enhanced context using structured output
            messages = [
                SystemMessage(content=self._get_contextual_system_identity()),
                HumanMessage(content=workflow_prompt),
            ]

            logger.info("🔄 Processing workflow generation response...")

            # Use structured output to directly get EnhancedWorkflowPlan
            workflow_plan = self.llm_call(
                messages, response_format=EnhancedWorkflowPlan
            )

            # Enhanced logging for LLM response
            response_log = f"""
========================================
🧠 MANAGER AGENT LLM RESPONSE - WORKFLOW GENERATION
========================================
TIMESTAMP: {datetime.now().strftime("%H:%M:%S.%f")[:-3]}
RESPONSE TYPE: {type(workflow_plan).__name__}
SUCCESS: {workflow_plan is not None}
WORKFLOW TITLE: {workflow_plan.title if workflow_plan else "NONE"}
NODES GENERATED: {len(workflow_plan.nodes) if workflow_plan and workflow_plan.nodes else 0}
STRATEGY: {getattr(workflow_plan, 'strategy', 'N/A') if workflow_plan else "N/A"}
========================================
"""
            # Log verbose details to debug/manager files only, not console
            manager_logger.info(response_log)

            full_response = f"🧠 FULL MANAGER AGENT WORKFLOW RESPONSE:\n{workflow_plan.model_dump_json(indent=2) if workflow_plan else 'None'}"
            # Log full response to debug/manager files only, not console
            manager_logger.info(full_response)

            # Clean user-friendly console message instead of verbose output
            if workflow_plan and workflow_plan.nodes:
                logger.info(
                    f"🎯 Created workflow: '{workflow_plan.title}' with {len(workflow_plan.nodes)} steps"
                )
            else:
                logger.warning("⚠️ Workflow generation failed - no nodes created")
            logger.info(
                f"Manager Agent LLM call completed successfully: {len(workflow_plan.nodes) if workflow_plan and workflow_plan.nodes else 0} nodes generated"
            )

            return workflow_plan

        except Exception as e:
            logger.error(f"Error in workflow generation: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # No fallbacks - let the failure propagate
            raise RuntimeError(f"Workflow generation failed: {str(e)}")

    def generate_enhanced_workflow_with_clarification(
        self,
        user_request: str,
        context: dict[str, Any] = None,
        interactive: bool = True,
    ) -> EnhancedWorkflowPlan | None:
        """
        Generate workflow with optional user clarification for complex requests
        """
        try:
            # First, expand the user request to understand it better
            if interactive:
                print("\n🤖 Using o3-mini to expand and understand your request...")
            expanded_prompt = self.analyze_user_request(user_request, context)

            # Present the expanded understanding for approval
            if interactive:
                # Show the o3-mini expansion for approval
                approved, feedback = self._present_expanded_understanding_for_approval(
                    expanded_prompt, user_request, interactive
                )
                if not approved:
                    if feedback:
                        # Incorporate feedback and try again
                        context = context or {}
                        context["user_feedback"] = feedback
                        return self.generate_enhanced_workflow_with_clarification(
                            user_request, context, interactive
                        )
                    else:
                        return None

            # If we have clarification questions, gather responses
            if expanded_prompt.clarification_questions:
                if interactive:
                    print(
                        "\n🔄 Moving to clarification questions to refine understanding..."
                    )
                (
                    clarification_response,
                    refined_spec,
                ) = self._gather_dynamic_clarifications(expanded_prompt, interactive)

                # Generate workflow from refined specification
                return self.generate_workflow_from_refined_spec(
                    refined_spec, user_request, context
                )
            else:
                # No clarification needed, generate workflow directly
                if interactive:
                    print(
                        "\n✅ No clarification questions needed. Generating workflow..."
                    )
                initial_spec = self._create_initial_spec_from_expansion(expanded_prompt)
                return self.generate_workflow_from_refined_spec(
                    initial_spec, user_request, context
                )

        except Exception as e:
            logger.error(f"Error in enhanced workflow generation: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # No fallbacks - let the failure propagate
            raise RuntimeError(f"Enhanced workflow generation failed: {str(e)}")

    def generate_workflow_from_refined_spec(
        self,
        refined_spec: RefinedSpecification,
        original_request: str,
        context: dict[str, Any] = None,
    ) -> EnhancedWorkflowPlan:
        """
        Generate a workflow from a refined specification
        """
        try:
            # Create an enhanced analysis based on the refined spec
            analysis = EnhancedRequestAnalysis(
                primary_intent=refined_spec.refined_objective or original_request,
                complexity=refined_spec.estimated_complexity or TaskComplexity.MODERATE,
                required_capabilities=refined_spec.detailed_requirements or [],
                success_criteria=refined_spec.acceptance_criteria or [],
                constraints=refined_spec.constraints or [],
                confidence_score=refined_spec.confidence_score,
                recommended_agents=self._extract_agents_from_spec(refined_spec),
                required_tools=self._extract_tools_from_spec(refined_spec),
                workflow_strategy=self._determine_strategy_from_spec(refined_spec),
            )

            # Generate workflow using the enhanced analysis
            workflow = self.generate_sophisticated_workflow(
                analysis, original_request, context
            )

            # Enhance workflow with spec-specific details
            workflow.title = f"Refined Workflow: {refined_spec.refined_objective or original_request[:50]}"
            workflow.description = f"Workflow generated from refined specification with {refined_spec.confidence_score:.1%} confidence"
            workflow.success_criteria = (
                refined_spec.acceptance_criteria or workflow.success_criteria
            )
            workflow.estimated_duration_minutes = self._estimate_duration_from_spec(
                refined_spec
            )

            # Add critical path items as critical nodes
            if refined_spec.critical_path_items:
                for node in workflow.nodes:
                    if any(
                        critical_item.lower() in node.description.lower()
                        for critical_item in refined_spec.critical_path_items
                    ):
                        node.critical = True
                        node.critical_reason = "Identified as critical path item"

            return workflow

        except Exception as e:
            logger.error(f"Error generating workflow from refined spec: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # No fallbacks - let the failure propagate
            raise RuntimeError(
                f"Workflow generation from refined spec failed: {str(e)}"
            )

    def _extract_agents_from_spec(self, spec: RefinedSpecification) -> list[str]:
        """Extract recommended agents from refined specification"""
        agents = []

        # Analyze technical specifications for agent hints
        if spec.technical_specifications:
            tech_specs = spec.technical_specifications
            if any(
                key in tech_specs for key in ["frontend", "ui", "web", "react", "vue"]
            ):
                agents.append("frontend_developer")
            if any(
                key in tech_specs for key in ["backend", "api", "server", "database"]
            ):
                agents.append("backend_developer")
            if any(
                key in tech_specs
                for key in ["deploy", "docker", "k8s", "infrastructure"]
            ):
                agents.append("devops_engineer")
            if any(key in tech_specs for key in ["test", "qa", "quality"]):
                agents.append("qa_engineer")

        # Analyze requirements for agent hints
        if spec.detailed_requirements:
            requirements_text = " ".join(spec.detailed_requirements).lower()
            if "research" in requirements_text or "analyze" in requirements_text:
                agents.append("research_agent")
            if "document" in requirements_text or "write" in requirements_text:
                agents.append("documentation_agent")

        # Default to research agent if no specific agents identified
        if not agents:
            agents.append("research_agent")

        return agents

    def _extract_tools_from_spec(self, spec: RefinedSpecification) -> list[str]:
        """Extract required tools from refined specification"""
        tools = []

        if spec.technical_specifications:
            tech_specs = " ".join(spec.technical_specifications.values()).lower()
            if "web" in tech_specs or "http" in tech_specs:
                tools.extend(["web_search", "web_scraping"])
            if "file" in tech_specs or "code" in tech_specs:
                tools.extend(["file_operations", "code_analysis"])
            if "database" in tech_specs:
                tools.append("database_operations")

        return tools

    def _determine_strategy_from_spec(
        self, spec: RefinedSpecification
    ) -> WorkflowStrategy:
        """Determine workflow strategy from refined specification"""
        if spec.implementation_phases and len(spec.implementation_phases) > 3:
            return WorkflowStrategy.SDLC
        elif spec.estimated_complexity == TaskComplexity.COMPLEX:
            return WorkflowStrategy.ADAPTIVE
        else:
            return WorkflowStrategy.LINEAR

    def _estimate_duration_from_spec(self, refined_spec: RefinedSpecification) -> int:
        """Estimate duration from refined specification"""
        base_duration = 60  # 1 hour base

        # Adjust based on complexity
        if refined_spec.estimated_complexity == TaskComplexity.SIMPLE:
            base_duration = 30
        elif refined_spec.estimated_complexity == TaskComplexity.COMPLEX:
            base_duration = 180
        elif refined_spec.estimated_complexity == TaskComplexity.ENTERPRISE:
            base_duration = 480

        # Adjust based on number of requirements
        if refined_spec.detailed_requirements:
            base_duration += len(refined_spec.detailed_requirements) * 15

        # Adjust based on implementation phases
        if refined_spec.implementation_phases:
            base_duration += len(refined_spec.implementation_phases) * 30

        return base_duration

    def make_intelligent_routing_decision(
        self,
        node_id: str,
        workflow_state: dict[str, Any],
        available_options: list[str],
        context: dict[str, Any] = None,
    ) -> dict[str, Any]:
        """
        Make intelligent routing decisions during workflow execution
        """
        try:
            # Build routing decision prompt
            routing_prompt = f"""As the OAMAT Workflow Manager, make an intelligent routing decision:

**CURRENT CONTEXT:**
- Node ID: {node_id}
- Available Options: {available_options}
- Workflow State: {json.dumps(workflow_state, indent=2)}
- Additional Context: {json.dumps(context or {}, indent=2)}

**DECISION REQUIREMENTS:**
Analyze the current state and choose the optimal next path considering:
1. Progress toward workflow objectives
2. Risk assessment of each option
3. Resource optimization opportunities
4. Quality and success probability

**RESPONSE FORMAT:**
Provide a JSON response with:
- "decision": chosen option from available_options
- "reasoning": detailed explanation of the choice
- "confidence": confidence score (0.0-1.0)
- "risk_assessment": risk level (low, medium, high)
"""

            # Enhanced logging for routing decision LLM call
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

            # Log routing prompt with truncation for debug/console and full content for API
            log_prompt_response(
                content=routing_prompt,
                content_type="prompt",
                context="Manager Agent - Routing Decision",
                timestamp=timestamp,
                debug_mode=True,
            )

            routing_prompt_log = f"""
========================================
🧠 MANAGER AGENT LLM CALL - ROUTING DECISION
========================================
TIMESTAMP: {timestamp}
NODE_ID: {node_id}
AVAILABLE_OPTIONS: {available_options}
CONTEXT_KEYS: {list(context.keys()) if context else "None"}
PROMPT LENGTH: {len(routing_prompt)} characters
========================================
"""
            print(routing_prompt_log)
            manager_logger.info(routing_prompt_log)

            messages = [
                SystemMessage(content=self._get_contextual_system_identity()),
                HumanMessage(content=routing_prompt),
            ]

            response = self.llm.invoke(messages)
            decision = extract_json_from_response(response.content)

            # Log response with truncation for debug/console and full content for API
            current_timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            log_prompt_response(
                content=response.content,
                content_type="response",
                context="Manager Agent - Routing Decision",
                timestamp=current_timestamp,
                debug_mode=True,
            )

            # Enhanced logging for routing decision response
            routing_response_log = f"""
========================================
🧠 MANAGER AGENT LLM RESPONSE - ROUTING DECISION
========================================
TIMESTAMP: {current_timestamp}
RAW_RESPONSE_LENGTH: {len(response.content) if response.content else 0} characters
PARSED_DECISION: {decision.get('decision', 'N/A') if isinstance(decision, dict) else 'PARSE_FAILED'}
REASONING_PREVIEW: {decision.get('reasoning', 'N/A')[:100] if isinstance(decision, dict) else 'N/A'}...
CONFIDENCE: {decision.get('confidence', 'N/A') if isinstance(decision, dict) else 'N/A'}
RISK_ASSESSMENT: {decision.get('risk_assessment', 'N/A') if isinstance(decision, dict) else 'N/A'}
DECISION_VALID: {isinstance(decision, dict) and 'decision' in decision}
========================================
"""
            print(routing_response_log)
            manager_logger.info(routing_response_log)

            if isinstance(decision, dict):
                logger.info(
                    f"Manager Agent routing decision: {decision.get('decision')} (confidence: {decision.get('confidence', 'N/A')})"
                )
                return decision
            else:
                raise ValueError("Invalid decision format received")

        except Exception as e:
            logger.error(f"Error in routing decision: {str(e)}")
            # No fallbacks - let the failure propagate
            raise RuntimeError(f"Routing decision failed: {str(e)}")

    def build_prompt(self, task_type: str, **kwargs) -> str:
        """Build prompts for different task types"""
        base_prompt = f"""You are the OAMAT Workflow Manager, an advanced AI orchestration system.

{self.system_identity}

**Current Task**: {task_type}
**Context**: {json.dumps(kwargs, indent=2)}

"""

        if task_type == "analysis":
            return (
                base_prompt
                + """
**ANALYSIS REQUIREMENTS:**
Perform comprehensive request analysis including:
- Intent analysis and domain categorization
- Complexity assessment and effort estimation
- Capability and tool requirements
- Strategic recommendations and risk assessment
- Success criteria and quality requirements

Return analysis in EnhancedRequestAnalysis JSON format.
"""
            )

        elif task_type == "workflow":
            return (
                base_prompt
                + """
**WORKFLOW GENERATION REQUIREMENTS:**
Design sophisticated workflow including:
- Strategic node orchestration with proper agent assignments
- Comprehensive parameter specification and dependency management
- Quality gates and success criteria definition
- Risk mitigation strategies
- Resource optimization and parallel execution planning

Return workflow in EnhancedWorkflowPlan JSON format.
"""
            )

        elif task_type == "routing_decision":
            return (
                base_prompt
                + """
**ROUTING DECISION REQUIREMENTS:**
Make intelligent routing decision including:
- Current state analysis and progress evaluation
- Option assessment and risk consideration
- Optimal path selection with clear reasoning
- Confidence scoring and alternative evaluation

Return decision in structured JSON format.
"""
            )

        else:
            return base_prompt + f"Handle {task_type} task with professional expertise."

    def parse_output(self, output: Any, task_type: str = None) -> Any:
        """Parse LLM output based on task type"""
        if isinstance(output, str):
            try:
                return extract_json_from_response(output)
            except Exception as e:
                logger.error(f"Error parsing output: {e}")
                # No fallbacks - let the failure propagate
                raise RuntimeError(f"Output parsing failed: {str(e)}")
        return output

    # Enhanced clarification and specification methods
    def analyze_user_request(
        self, user_request: str, context: dict[str, Any] = None
    ) -> ExpandedPrompt:
        """Analyze and expand user request to better understand requirements"""
        # Use the real RequestAnalyzer implementation
        return self.request_analyzer.analyze_user_request(user_request, context)

    def gather_user_clarifications(
        self, expanded_prompt: ExpandedPrompt, interactive: bool = True
    ) -> tuple[UserClarificationResponse, RefinedSpecification]:
        """Gather user clarifications for complex requests"""
        if not expanded_prompt.clarification_questions or not interactive:
            # No clarification needed or non-interactive mode
            responses = UserClarificationResponse(responses=[], skip_remaining=True)
            spec = self._create_initial_spec_from_expansion(expanded_prompt)
            return responses, spec

        responses = []
        current_spec = self._create_initial_spec_from_expansion(expanded_prompt)
        remaining_questions = list(expanded_prompt.clarification_questions)

        for i, question in enumerate(expanded_prompt.clarification_questions):
            if not remaining_questions:
                break

            self._present_current_topic(
                question, i + 1, len(expanded_prompt.clarification_questions)
            )

            while True:
                try:
                    answer = input(f"\n{question.question}\n> ").strip()

                    if answer.lower() in ["skip", "s"]:
                        break
                    elif answer.lower() in ["help", "h", "?"]:
                        self._handle_help_request(answer, question, current_spec)
                        continue
                    elif answer.lower() in ["status", "current"]:
                        self._show_current_understanding(current_spec)
                        continue
                    elif answer.lower() in ["quit", "q", "exit"]:
                        responses.append(
                            QuestionAnswer(
                                question_id=question.id,
                                answer=answer,
                                skipped=False,
                                additional_context="",
                            )
                        )
                        return (
                            UserClarificationResponse(
                                responses=responses, skip_remaining=True
                            ),
                            current_spec,
                        )
                    elif answer:
                        # Process the answer
                        processed_answer = self._process_conversational_answer(
                            answer, question, current_spec, responses
                        )
                        responses.append(
                            QuestionAnswer(
                                question_id=question.id,
                                answer=processed_answer.get("answer", answer),
                                confidence=processed_answer.get("confidence", 0.8),
                                additional_context=processed_answer.get("context", ""),
                                skipped=False,
                            )
                        )

                        # Update spec and regenerate questions if needed
                        (
                            current_spec,
                            remaining_questions,
                        ) = self._update_spec_and_regenerate_questions(
                            current_spec,
                            responses[-1],
                            remaining_questions,
                            question,
                        )
                        break
                    else:
                        print(
                            "Please provide an answer, or type 'skip', 'help', or 'quit'"
                        )

                except KeyboardInterrupt:
                    print("\n\nProcess interrupted by user.")
                    return (
                        UserClarificationResponse(
                            responses=responses, skip_remaining=True
                        ),
                        current_spec,
                    )
                except Exception as e:
                    print(f"Error processing answer: {e}")
                    continue

        # Perform final review and refinement
        final_spec = self._perform_final_review(
            current_spec, f"Based on {len(responses)} clarifications"
        )

        return (
            UserClarificationResponse(responses=responses, skip_remaining=False),
            final_spec,
        )

    def _gather_dynamic_clarifications(
        self, expanded_prompt: ExpandedPrompt, interactive: bool = True
    ) -> tuple[UserClarificationResponse, RefinedSpecification]:
        """
        Gathers user clarifications with dynamic question generation and understanding updates.
        Adapted from working commits b966b80 and 255b9b5.
        """
        if not interactive:
            # Non-interactive mode: use defaults
            responses = UserClarificationResponse(responses=[], skip_remaining=True)
            spec = self._create_initial_spec_from_expansion(expanded_prompt)
            return responses, spec

        # Start with the initial refined spec from the expansion phase
        current_spec = self._create_initial_spec_from_expansion(expanded_prompt)
        questions_to_ask = list(expanded_prompt.clarification_questions or [])

        # Prioritize questions: high -> medium -> low
        priority_map = {"high": 0, "medium": 1, "low": 2}
        questions_to_ask.sort(key=lambda q: priority_map.get(q.priority, 99))

        answered_questions: list[QuestionAnswer] = []
        max_questions = 10  # Safety limit
        questions_asked = 0

        if questions_to_ask:
            print("\n" + "=" * 80)
            print("🤖 DYNAMIC CLARIFICATION QUESTIONS")
            print("=" * 80)
            print(
                "I'll ask the most impactful questions first to understand your needs."
            )
            print("Questions will be updated based on your answers.")
            print(
                "Type 'skip' to use defaults, 'status' to see current understanding, or 'quit' to stop."
            )
            print("-" * 80)

        while questions_to_ask and questions_asked < max_questions:
            current_question = questions_to_ask[
                0
            ]  # Get highest priority question, DO NOT POP
            questions_asked += 1

            if interactive:
                priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                    current_question.priority, "⚪"
                )
                print(
                    f"\n{priority_emoji} Question {questions_asked} (Priority: {current_question.priority})"
                )
                print(
                    f"📂 Category: {current_question.category.replace('_', ' ').title()}"
                )
                print(f"❓ {current_question.question}")

                if (
                    current_question.default_value
                    and current_question.default_value != "None"
                ):
                    print(f"💡 Default: {current_question.default_value}")

                print("-" * 60)
                answer_text = input("Your answer: ").strip()

                if answer_text.lower() in ["skip", "s"]:
                    answer_text = current_question.default_value or "skipped"
                elif answer_text.lower() in ["quit", "q", "exit"]:
                    print("\n🛑 Clarification process stopped by user.")
                    break
                elif answer_text.lower() in ["status", "current"]:
                    self._show_current_understanding(current_spec)
                    # No need to re-add the question as it wasn't removed
                    questions_asked -= 1
                    continue
                elif not answer_text and current_question.default_value:
                    answer_text = current_question.default_value
                elif not answer_text:
                    print("Please provide an answer or type 'skip'")
                    # No need to re-add the question as it wasn't removed
                    questions_asked -= 1
                    continue
            else:
                # Non-interactive mode: use default or skip
                answer_text = current_question.default_value or "N/A"

            # Record the answer
            answer = QuestionAnswer(question_id=current_question.id, answer=answer_text)
            answered_questions.append(answer)

            # Show processing message
            if interactive:
                print("🔄 Processing your answer and updating understanding...")

            # Dynamically update the spec and remaining questions based on the new answer
            current_spec, questions_to_ask = self._update_spec_and_regenerate_questions(
                current_spec, answer, questions_to_ask, current_question
            )

            # Check for confidence exit condition
            if current_spec.confidence_score and current_spec.confidence_score > 0.90:
                print(
                    f"\n🎯 Confidence threshold reached ({current_spec.confidence_score:.0%}). I have enough information to proceed!"
                )
                break

        # Final input opportunity
        additional_input = ""
        if interactive:
            print("\n" + "=" * 80)
            print("🎯 FINAL INPUT OPPORTUNITY")
            print("=" * 80)
            additional_input = input(
                "Any other guidance, constraints, or details to add? (Press Enter to continue): "
            ).strip()

        # Final specification with additional context
        if additional_input:
            current_spec.detailed_requirements = (
                current_spec.detailed_requirements or []
            )
            current_spec.detailed_requirements.append(
                f"Final User Guidance: {additional_input}"
            )

        user_response_model = UserClarificationResponse(
            responses=answered_questions,
            additional_context=additional_input,
            skip_remaining=False,
        )

        return user_response_model, current_spec

    def _update_spec_and_regenerate_questions(
        self,
        current_spec: RefinedSpecification,
        latest_answer: QuestionAnswer,
        remaining_questions: list[ClarificationQuestion],
        answered_question: ClarificationQuestion,
    ) -> tuple[RefinedSpecification, list[ClarificationQuestion]]:
        """
        Dynamically update specification based on latest answer and regenerate questions.
        Adapted from working commits b966b80 and 255b9b5.
        """
        # FAIL-FAST: No try/except block. If any step fails, the exception will propagate.

        # Step 1: Update the specification intelligently using LLM
        updated_spec = self._update_specification_with_llm(
            current_spec, latest_answer, answered_question
        )

        # Step 2: Regenerate questions based on the updated understanding
        updated_questions = self._regenerate_questions_with_inference(
            updated_spec, latest_answer, remaining_questions, answered_question
        )

        # Step 3: Update confidence score based on how much understanding improved
        if updated_spec.confidence_score is None:
            updated_spec.confidence_score = 0.5

        # Increase confidence if answer was substantive
        if latest_answer.answer and latest_answer.answer.lower() not in [
            "skip",
            "skipped",
            "n/a",
        ]:
            confidence_boost = 0.15 if len(latest_answer.answer) > 20 else 0.10
            updated_spec.confidence_score = min(
                updated_spec.confidence_score + confidence_boost, 1.0
            )

        return updated_spec, updated_questions

    def _update_specification_with_llm(
        self,
        current_spec: RefinedSpecification,
        latest_answer: QuestionAnswer,
        answered_question: ClarificationQuestion,
    ) -> RefinedSpecification:
        """Use LLM to intelligently update the specification based on the latest answer"""
        try:
            if not answered_question:
                # This should ideally not happen with the new logic
                logger.warning("Could not find the answered question to update spec.")
                return current_spec

            # Create prompt for LLM to update specification
            update_prompt = f"""
You are updating a project specification based on a user's answer to a clarification question.

CURRENT SPECIFICATION:
- Objective: {current_spec.refined_objective}
- Requirements: {current_spec.detailed_requirements}
- Technical Specs: {current_spec.technical_specifications}
- Constraints: {current_spec.constraints}
- Assumptions: {current_spec.assumptions}

QUESTION ANSWERED:
Category: {answered_question.category}
Question: {answered_question.question}
User's Answer: {latest_answer.answer}

TASK: Update the specification to incorporate this new information. Be intelligent about:
1. What this answer tells us about the user's needs
2. How it affects existing requirements and assumptions
3. What new technical specifications or constraints it introduces
4. Any assumptions that are now confirmed or can be removed

Return the updated specification as JSON following the RefinedSpecification schema.
"""

            messages = [HumanMessage(content=update_prompt)]
            response = self.llm_call(messages, response_format=RefinedSpecUpdate)

            if response and isinstance(response, RefinedSpecUpdate):
                print(f"   ✅ Specification updated: {response.reasoning}")
                return response.updated_spec
            else:
                print("   ⚠️  Specification update failed, using basic update")
                return self._basic_spec_update(
                    current_spec, latest_answer, answered_question
                )

        except Exception as e:
            logger.error(f"Error in LLM spec update: {e}")
            # FAIL-FAST: Re-raise the exception instead of falling back.
            raise e

    def _regenerate_questions_with_inference(
        self,
        updated_spec: RefinedSpecification,
        latest_answer: QuestionAnswer,
        remaining_questions: list[ClarificationQuestion],
        answered_question: ClarificationQuestion,
    ) -> list[ClarificationQuestion]:
        """Regenerate questions based on updated understanding with inference analysis"""
        try:
            # Create list of all answered questions for context
            answered_questions_context = [
                latest_answer
            ]  # This could be expanded in the future

            # Build prompt for dynamic question regeneration
            regenerate_prompt = f"""
You are dynamically updating clarification questions based on a user's latest answer.

CURRENT UNDERSTANDING:
- Objective: {updated_spec.refined_objective}
- Requirements: {updated_spec.detailed_requirements}
- Technical Specs: {updated_spec.technical_specifications}
- Constraints: {updated_spec.constraints}
- Assumptions: {updated_spec.assumptions}
- Confidence: {updated_spec.confidence_score:.0%}

LATEST ANSWER:
Question: {answered_question.question}
Answer: {latest_answer.answer}

REMAINING QUESTIONS:
{json.dumps([q.model_dump() for q in remaining_questions], indent=2)}

INSTRUCTIONS:
1. **INFERENCE ANALYSIS FIRST**: What can now be inferred from the current understanding?
2. **REMOVE REDUNDANT QUESTIONS**: Remove questions whose answers can now be inferred
3. **ADD NEW STRATEGIC QUESTIONS**: Only add questions that address genuine gaps in understanding
4. **PRIORITIZE BY IMPACT**: Focus on questions that would significantly change the solution

INFERENCE CHECKLIST:
- Can WHO be determined from the current understanding?
- Can WHY be determined from the stated requirements?
- Can HOW be determined from the technical specifications?
- Can WHAT be determined from the scope and deliverables?
- Can WHERE be determined from the constraints?

ONLY ask questions when:
- The answer cannot be reasonably inferred
- Multiple reasonable interpretations exist that would change the solution
- The question addresses a genuine strategic gap

Return the updated questions as JSON following the DynamicQuestionUpdate schema.
"""

            messages = [HumanMessage(content=regenerate_prompt)]
            response = self.llm_call(messages, response_format=DynamicQuestionUpdate)

            if response and isinstance(response, DynamicQuestionUpdate):
                print(f"   ✅ Questions updated: {response.reasoning}")
                return response.updated_questions
            else:
                print("   ⚠️  Question regeneration failed, using basic removal")
                # Now safe to remove the question that was just processed
                return [q for q in remaining_questions if q.id != answered_question.id]

        except Exception as e:
            logger.error(f"Error in question regeneration: {e}")
            # FAIL-FAST: Re-raise the exception instead of falling back.
            raise e

    def _basic_spec_update(
        self,
        current_spec: RefinedSpecification,
        latest_answer: QuestionAnswer,
        answered_question: ClarificationQuestion,
    ) -> RefinedSpecification:
        """Basic fallback specification update"""
        if answered_question.category == QuestionCategory.SCOPE:
            if not current_spec.detailed_requirements:
                current_spec.detailed_requirements = []
            current_spec.detailed_requirements.append(latest_answer.answer)
        elif answered_question.category == QuestionCategory.TECHNICAL:
            if not current_spec.technical_specifications:
                current_spec.technical_specifications = {}
            current_spec.technical_specifications[
                answered_question.question
            ] = latest_answer.answer
        elif answered_question.category == QuestionCategory.CONSTRAINTS:
            if not current_spec.constraints:
                current_spec.constraints = []
            current_spec.constraints.append(latest_answer.answer)
        elif answered_question.category == QuestionCategory.FUNCTIONAL:
            if not current_spec.detailed_requirements:
                current_spec.detailed_requirements = []
            current_spec.detailed_requirements.append(
                f"Functional requirement: {latest_answer.answer}"
            )
        elif answered_question.category == QuestionCategory.INFRASTRUCTURE:
            if not current_spec.technical_specifications:
                current_spec.technical_specifications = {}
            current_spec.technical_specifications[
                f"Infrastructure: {answered_question.question}"
            ] = latest_answer.answer

        return current_spec

    def _perform_final_review(
        self, final_spec: RefinedSpecification, additional_context: str
    ) -> RefinedSpecification:
        """Perform final review and refinement of the specification"""
        try:
            # Ensure all required fields are populated
            if not final_spec.refined_objective:
                final_spec.refined_objective = (
                    final_spec.original_request or "Refined objective"
                )

            if not final_spec.detailed_requirements:
                final_spec.detailed_requirements = ["Complete the requested task"]

            if not final_spec.acceptance_criteria:
                final_spec.acceptance_criteria = ["Task completed successfully"]

            # Set final confidence score
            if final_spec.confidence_score < 0.5:
                final_spec.confidence_score = (
                    0.7  # Reasonable default after clarification
                )

            return final_spec

        except Exception as e:
            logger.error(f"Error in final review: {e}")
            return final_spec

    def _create_initial_spec_from_expansion(
        self, expanded_prompt: ExpandedPrompt
    ) -> RefinedSpecification:
        """Create initial specification from expanded prompt"""
        return RefinedSpecification(
            refined_objective=expanded_prompt.objective or "",
            detailed_requirements=expanded_prompt.scope_and_deliverables or [],
            technical_specifications=expanded_prompt.technical_architecture or {},
            acceptance_criteria=expanded_prompt.success_criteria or [],
            constraints=[],
            implementation_phases=expanded_prompt.execution_approach or [],
            critical_path_items=[],
            estimated_complexity=TaskComplexity.MODERATE,
            confidence_score=getattr(expanded_prompt, "confidence_score", 0.6),
        )

    def _present_expanded_understanding_for_approval(
        self, expanded_prompt: ExpandedPrompt, user_request: str, interactive: bool
    ) -> tuple[bool, str | None]:
        """
        Present the agent's expanded understanding to the user for approval before asking clarifying questions.
        Adapted from working commit a1bba2d.
        """
        if not interactive:
            return True, None

        print("\n" + "=" * 80)
        print("📋 AGENT'S UNDERSTANDING OF YOUR REQUEST")
        print("=" * 80)

        print("\n🎯 **OBJECTIVE:**")
        print(f"   {expanded_prompt.objective}")

        print("\n📝 **WHAT I THINK YOU'RE ASKING FOR:**")
        for i, req in enumerate(expanded_prompt.scope_and_deliverables or [], 1):
            print(f"   {i}. {req}")

        print("\n🔧 **TECHNICAL APPROACH:**")
        for key, value in (expanded_prompt.technical_architecture or {}).items():
            print(f"   • {key}: {value}")

        print("\n⚠️  **ASSUMPTIONS I'M MAKING:**")
        for assumption in expanded_prompt.inferred_assumptions or []:
            print(f"   • {assumption}")

        if expanded_prompt.success_criteria:
            print("\n✅ **SUCCESS CRITERIA:**")
            for criteria in expanded_prompt.success_criteria:
                print(f"   • {criteria}")

        if expanded_prompt.potential_risks:
            print("\n🚨 **POTENTIAL CHALLENGES:**")
            for risk in expanded_prompt.potential_risks:
                print(f"   • {risk}")

        print("\n" + "=" * 80)
        print("❓ Is this understanding correct? Should I proceed with this approach?")
        print("   • Type 'yes' or 'y' to proceed with clarifying questions")
        print("   • Type 'no' or 'n' to reject and provide feedback")
        print("   • Provide specific feedback to guide me in the right direction")
        print("=" * 80)

        while True:
            try:
                user_input = input("\n👤 Your response: ").strip().lower()

                if user_input in ["yes", "y", "approve", "correct", "good"]:
                    print(
                        "\n✅ Understanding approved! Proceeding with clarifying questions..."
                    )
                    return True, None

                elif user_input in ["no", "n", "reject", "wrong", "incorrect"]:
                    feedback = input(
                        "\n💬 Please explain what's wrong or what I missed: "
                    ).strip()
                    if feedback:
                        print(
                            "\n📝 Got it! I'll revise my understanding based on your feedback."
                        )
                        return False, feedback
                    else:
                        print(
                            "\n❌ No feedback provided. I'll try a different approach."
                        )
                        return (
                            False,
                            "The understanding was incorrect. Please try a different approach.",
                        )

                elif len(user_input) > 10:  # Assume it's detailed feedback
                    print(
                        "\n📝 Thank you for the detailed feedback! I'll revise my understanding."
                    )
                    return False, user_input

                else:
                    print(
                        "\n❓ Please respond with 'yes'/'no' or provide specific feedback about what's wrong."
                    )

            except KeyboardInterrupt:
                print("\n\n❌ Process interrupted by user.")
                return False, "Process was interrupted by user."

    def _present_for_approval(
        self, spec: RefinedSpecification, interactive: bool
    ) -> tuple[bool, str | None]:
        """Present specification for user approval"""
        if not interactive:
            return True, None

        print("\n" + "=" * 80)
        print("📋 REFINED SPECIFICATION REVIEW")
        print("=" * 80)
        print(f"\n🎯 Objective: {spec.refined_objective}")
        print(f"\n📊 Confidence: {spec.confidence_score:.1%}")

        if spec.detailed_requirements:
            print(f"\n📝 Requirements ({len(spec.detailed_requirements)}):")
            for i, req in enumerate(spec.detailed_requirements[:5], 1):
                print(f"  {i}. {req}")
            if len(spec.detailed_requirements) > 5:
                print(f"  ... and {len(spec.detailed_requirements) - 5} more")

        if spec.technical_specifications:
            print("\n⚙️ Technical Specifications:")
            for key, value in list(spec.technical_specifications.items())[:3]:
                print(f"  • {key}: {value}")
            if len(spec.technical_specifications) > 3:
                print(f"  ... and {len(spec.technical_specifications) - 3} more")

        print("\n" + "=" * 80)

        while True:
            try:
                response = (
                    input("\nApprove this specification? (y/n/details): ")
                    .strip()
                    .lower()
                )
                if response in ["y", "yes", "approve"]:
                    return True, None
                elif response in ["n", "no", "reject"]:
                    feedback = input("What needs to be changed? ").strip()
                    return False, (
                        feedback if feedback else "User rejected specification"
                    )
                elif response in ["d", "details", "show"]:
                    self._show_current_understanding(spec)
                else:
                    print("Please enter 'y' (yes), 'n' (no), or 'details'")
            except KeyboardInterrupt:
                print("\n\nProcess interrupted by user.")
                return False, "Process interrupted"

    def _present_current_topic(
        self, question: ClarificationQuestion, current: int, total: int
    ):
        """Present current clarification topic"""
        print(f"\n--- Question {current}/{total}: {question.category.title()} ---")
        print(f"Priority: {question.priority}")
        if question.explanation:
            print(f"Why this matters: {question.explanation}")

    def _handle_help_request(
        self, command: str, question: ClarificationQuestion, spec: RefinedSpecification
    ):
        """Handle user help requests during clarification"""
        if command == "help":
            help_text = self._generate_contextual_help(question, spec)
            print(f"\n{help_text}")
        elif command == "examples":
            examples = self._generate_examples_for_question(question, spec)
            print("\nExamples:")
            for i, example in enumerate(examples, 1):
                print(f"{i}. {example}")
        elif command == "options":
            options = self._generate_options_for_question(question, spec)
            print("\nSuggested options:")
            for i, option in enumerate(options, 1):
                print(f"{i}. {option['value']}: {option['description']}")

    def _generate_contextual_help(
        self, question: ClarificationQuestion, spec: RefinedSpecification
    ) -> str:
        """Generate contextual help for a question"""
        return f"""
Help for: {question.question}

This question helps us understand {question.category} aspects of your project.
{question.explanation or 'This information will help us create a better workflow.'}

You can:
- Answer directly
- Type 'examples' to see examples
- Type 'options' to see suggested options
- Type 'skip' to skip this question
- Type 'status' to see current understanding
"""

    def _generate_examples_for_question(
        self, question: ClarificationQuestion, spec: RefinedSpecification
    ) -> list[str]:
        """Generate examples for a clarification question"""
        # Simplified implementation
        return ["Example answer 1", "Example answer 2", "Example answer 3"]

    def _generate_options_for_question(
        self, question: ClarificationQuestion, spec: RefinedSpecification
    ) -> list[dict[str, str]]:
        """Generate options for a clarification question"""
        # Use predefined options if available
        if question.options:
            return [
                {"value": opt, "description": f"Choose {opt}"}
                for opt in question.options
            ]

        # Generate contextual options
        return [
            {"value": "standard", "description": "Use standard approach"},
            {"value": "custom", "description": "Use custom approach"},
            {"value": "minimal", "description": "Use minimal approach"},
        ]

    def _process_conversational_answer(
        self,
        answer: str,
        question: ClarificationQuestion,
        spec: RefinedSpecification,
        history: list[dict],
    ) -> dict:
        """Process conversational answer and extract structured information"""
        # Simplified implementation
        return {
            "question_id": question.id,
            "answer": answer,
            "processed": True,
            "confidence": 0.8,
        }

    def _show_current_understanding(self, spec: RefinedSpecification):
        """Show current understanding of the specification"""
        # Log verbose details to debug/manager files only, not console
        understanding_log = f"""
=== Current Understanding ===
Objective: {spec.refined_objective}
Requirements: {len(spec.detailed_requirements or [])} items
Confidence: {spec.confidence_score:.1%}
{f"Constraints: {len(spec.constraints)} identified" if spec.constraints else ""}
========================
"""
        manager_logger.info(understanding_log)

        # Clean user-friendly console message instead
        logger.info(
            f"📋 Refined specification: {spec.confidence_score:.0%} confidence, {len(spec.detailed_requirements or [])} requirements"
        )
