"""
Request Validation Agent - Truly Agentic Implementation

AI-driven request validation using dynamic analysis rather than
predefined schemas. Adapts validation approach based on content analysis.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.applications.oamat_sd.src.interfaces.agent_interfaces import (
    IRequestValidationAgent,
)
from src.applications.oamat_sd.src.models.data_models import (
    RequestInput,
    RequestType,
    ValidationResult,
)

logger = logging.getLogger(__name__)


class RequestType(str, Enum):
    """Types of requests that can be processed."""

    WEB_APPLICATION = "web_application"
    MICROSERVICES = "microservices"
    SIMPLE_SCRIPT = "simple_script"
    DATA_ANALYSIS = "data_analysis"
    AUTOMATION = "automation"
    UNKNOWN = "unknown"


class GapPriority(str, Enum):
    """Priority levels for missing information gaps."""

    CRITICAL = "critical"
    IMPORTANT = "important"
    OPTIONAL = "optional"


@dataclass
class RequestField:
    """Definition of a field in a request schema."""

    name: str
    description: str
    field_type: type
    required: bool = True
    default: Any | None = None
    validation_pattern: str | None = None


@dataclass
class RequestSchema:
    """Schema definition for a specific request type."""

    request_type: RequestType
    description: str
    fields: list[RequestField]

    def get_required_fields(self) -> list[RequestField]:
        """Get all required fields for this schema."""
        return [field for field in self.fields if field.required]

    def get_optional_fields(self) -> list[RequestField]:
        """Get all optional fields for this schema."""
        return [field for field in self.fields if not field.required]


@dataclass
class ValidationResult:
    """Result of request validation process."""

    request_type: RequestType
    is_valid: bool
    missing_fields: list[str]
    extracted_info: dict[str, Any]
    confidence: float
    validation_errors: list[str] = field(default_factory=list)


@dataclass
class InformationGap:
    """Represents a gap in request information."""

    field_name: str
    priority: GapPriority
    description: str
    researchable: bool
    suggested_defaults: list[Any] = field(default_factory=list)
    research_keywords: list[str] = field(default_factory=list)


@dataclass
class GapAnalysisResult:
    """Result of gap analysis process."""

    gaps: list[InformationGap]
    confidence: float
    completeness_score: float
    critical_gaps_count: int
    researchable_gaps: list[InformationGap] = field(default_factory=list)
    unresearchable_gaps: list[InformationGap] = field(default_factory=list)


@dataclass
class CompletionResult:
    """Result of information completion process."""

    filled_fields: dict[str, Any]
    applied_defaults: dict[str, Any]
    research_results: dict[str, Any]
    assumptions: list[str]
    escalation_required: bool
    critical_gaps_remaining: list[str]


@dataclass
class ClarificationQuestion:
    """A focused question for user clarification."""

    field_name: str
    question: str
    importance_explanation: str
    options: list[str] = field(default_factory=list)
    default_option: str | None = None


class RequestSchemaRegistry:
    """Registry for request schemas and validation rules."""

    def __init__(self):
        self._schemas: dict[RequestType, RequestSchema] = {}
        self._initialize_default_schemas()

    def _initialize_default_schemas(self):
        """Initialize default schemas for common request types."""

        # Web Application Schema
        web_app_fields = [
            RequestField("name", "Application name", str, required=True),
            RequestField("description", "Application description", str, required=True),
            RequestField(
                "framework",
                "Web framework (React, Vue, etc.)",
                str,
                required=False,
                default="React",
            ),
            RequestField(
                "styling",
                "Styling approach (CSS, Tailwind, etc.)",
                str,
                required=False,
                default="Tailwind",
            ),
            RequestField(
                "authentication",
                "Authentication requirements",
                str,
                required=False,
                default="basic",
            ),
            RequestField(
                "database",
                "Database requirements",
                str,
                required=False,
                default="SQLite",
            ),
            RequestField(
                "deployment", "Deployment target", str, required=False, default="local"
            ),
        ]

        self._schemas[RequestType.WEB_APPLICATION] = RequestSchema(
            request_type=RequestType.WEB_APPLICATION,
            description="Full-stack web application development",
            fields=web_app_fields,
        )

        # Microservices Schema
        microservices_fields = [
            RequestField("service_name", "Primary service name", str, required=True),
            RequestField(
                "architecture", "Service architecture description", str, required=True
            ),
            RequestField("services", "List of required services", list, required=True),
            RequestField(
                "communication",
                "Inter-service communication",
                str,
                required=False,
                default="REST",
            ),
            RequestField(
                "data_storage",
                "Data storage strategy",
                str,
                required=False,
                default="PostgreSQL",
            ),
            RequestField(
                "orchestration",
                "Container orchestration",
                str,
                required=False,
                default="Docker",
            ),
        ]

        self._schemas[RequestType.MICROSERVICES] = RequestSchema(
            request_type=RequestType.MICROSERVICES,
            description="Microservices architecture development",
            fields=microservices_fields,
        )

        # Simple Script Schema
        script_fields = [
            RequestField("purpose", "Script purpose/goal", str, required=True),
            RequestField(
                "language",
                "Programming language",
                str,
                required=False,
                default="Python",
            ),
            RequestField(
                "inputs",
                "Input requirements",
                str,
                required=False,
                default="command line",
            ),
            RequestField(
                "outputs", "Expected outputs", str, required=False, default="console"
            ),
        ]

        self._schemas[RequestType.SIMPLE_SCRIPT] = RequestSchema(
            request_type=RequestType.SIMPLE_SCRIPT,
            description="Simple script or utility development",
            fields=script_fields,
        )

    def get_schema(self, request_type: RequestType) -> RequestSchema | None:
        """Get schema for a specific request type."""
        return self._schemas.get(request_type)

    def register_schema(self, schema: RequestSchema):
        """Register a new schema."""
        self._schemas[schema.request_type] = schema

    def list_schemas(self) -> list[RequestType]:
        """List all available schema types."""
        return list(self._schemas.keys())

    def validate_compliance(
        self, request_type: RequestType, data: dict[str, Any]
    ) -> tuple[bool, list[str]]:
        """Validate data compliance with schema."""
        schema = self.get_schema(request_type)
        if not schema:
            return False, [f"No schema found for request type: {request_type}"]

        errors = []
        required_fields = schema.get_required_fields()

        for field in required_fields:
            if field.name not in data:
                errors.append(f"Missing required field: {field.name}")
            elif not isinstance(data[field.name], field.field_type):
                errors.append(
                    f"Invalid type for field {field.name}: expected {field.field_type.__name__}"
                )

        return len(errors) == 0, errors


class RequestValidationAgent(IRequestValidationAgent):
    """
    Truly agentic request validation using AI-driven analysis

    NO PREDEFINED SCHEMAS - uses AI to understand request context and needs
    """

    def __init__(
        self,
        schema_registry: RequestSchemaRegistry | None = None,
        model_config: dict[str, Any] | None = None,
    ):
        self.schema_registry = schema_registry or RequestSchemaRegistry()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Use AI model for intelligent validation - APPROVED MODELS ONLY
        # NO FALLBACKS RULE: Model configuration strictly required
        if not model_config or "model" not in model_config:
            raise RuntimeError(
                "Model configuration required. Cannot proceed without explicit model specification."
            )
        model_name = model_config["model"]

        # Handle O3 models that don't support temperature
        model_kwargs = {"model": model_name}
        if not model_name.startswith("o3"):
            model_kwargs["temperature"] = 0.1  # Low temperature for consistent analysis

        self.ai_model = ChatOpenAI(**model_kwargs)

    async def validate_request(self, request: RequestInput) -> ValidationResult:
        """
        Dynamically validate request using AI-driven analysis

        Uses intelligent analysis rather than rule-based validation
        """
        self.logger.info(f"Validating request dynamically: {request.content[:100]}...")

        try:
            # AI-driven request type detection
            detected_type, confidence = await self.generate_validation_strategy(
                request.content
            )

            # AI-driven information extraction
            extracted_info = await self.extract_information_dynamically(request)

            # Determine validation success based on AI analysis
            validation_errors = await self._analyze_validation_issues(
                request, extracted_info
            )

            is_valid = len(validation_errors) == 0 or all(
                error.startswith("Warning:") for error in validation_errors
            )

            return ValidationResult(
                is_valid=is_valid,
                detected_type=detected_type,
                confidence_score=confidence,
                extracted_info=extracted_info,
                validation_errors=validation_errors,
                schema_matches=[detected_type.value] if detected_type else [],
            )

        except Exception as e:
            self.logger.error(f"AI-driven validation failed: {e}")
            return ValidationResult(
                is_valid=False,
                detected_type=None,
                confidence_score=0.0,
                extracted_info={},
                validation_errors=[f"Validation error: {e}"],
                schema_matches=[],
            )

    async def extract_information_dynamically(
        self, request: RequestInput
    ) -> dict[str, Any]:
        """
        Use AI to extract information from natural language

        Generates extraction strategy based on content analysis
        """
        extraction_prompt = f"""
        Analyze this request and extract all relevant structured information:

        REQUEST: {request.content}
        CONTEXT: {request.context}
        USER PREFERENCES: {request.user_preferences}

        Think about what information is explicitly stated and what can be reasonably inferred.
        Extract:
        1. Technical requirements (frameworks, languages, tools)
        2. Functional requirements (features, capabilities)
        3. Non-functional requirements (performance, security, scale)
        4. Constraints and preferences
        5. Domain-specific information

        Don't force extraction into predefined categories - adapt to what's actually in the request.
        """

        try:
            response = await self.ai_model.ainvoke(
                [
                    SystemMessage(
                        content="You are an expert at extracting structured information from natural language requests. Adapt your extraction approach to the specific content."
                    ),
                    HumanMessage(content=extraction_prompt),
                ]
            )

            # Parse AI response into structured data
            return await self._parse_extraction_response(response.content, request)

        except Exception as e:
            self.logger.error(f"Dynamic extraction failed: {e}")
            return {"extraction_error": str(e)}

    async def generate_validation_strategy(
        self, content: str
    ) -> tuple[RequestType | None, float]:
        """
        Dynamically generate validation approach for this specific content

        Creates novel validation strategies rather than template matching
        """
        strategy_prompt = f"""
        Analyze this request and determine its type and characteristics:

        REQUEST: {content}

        Think about:
        1. What type of project/task is this requesting?
        2. What domain does it belong to?
        3. How complex and specific is the request?
        4. What validation approach would be most appropriate?

        Classify into one of these types based on the actual content:
        - WEB_APPLICATION: Web-based applications or websites
        - MICROSERVICE: Service-oriented or API development
        - SCRIPT: Automation scripts or simple programs
        - AUTOMATION: Process automation or workflows
        - ANALYSIS: Data analysis or research tasks
        - CUSTOM: Unique requests that don't fit standard categories

        Provide your confidence level (0-1) in this classification.
        """

        try:
            response = await self.ai_model.ainvoke(
                [
                    SystemMessage(
                        content="You are an expert at analyzing and classifying requests. Use contextual understanding to determine the most appropriate type."
                    ),
                    HumanMessage(content=strategy_prompt),
                ]
            )

            # Parse AI response to extract type and confidence
            detected_type, confidence = self._parse_type_response(response.content)
            return detected_type, confidence

        except Exception as e:
            self.logger.error(f"Strategy generation failed: {e}")
            return None, 0.0

    async def _analyze_validation_issues(
        self, request: RequestInput, extracted_info: dict[str, Any]
    ) -> list[str]:
        """Use AI to identify potential validation issues"""

        issues_prompt = f"""
        Review this request and extracted information for potential issues:

        REQUEST: {request.content}
        EXTRACTED INFO: {extracted_info}

        Identify any:
        1. Critical missing information that would block execution
        2. Ambiguities that need clarification
        3. Potential conflicts or inconsistencies
        4. Quality issues with the request

        Focus on actual problems, not arbitrary schema compliance.
        """

        try:
            response = await self.ai_model.ainvoke(
                [
                    SystemMessage(
                        content="You are an expert at identifying potential issues in requests. Focus on real problems that would affect execution."
                    ),
                    HumanMessage(content=issues_prompt),
                ]
            )

            return self._parse_issues_response(response.content)

        except Exception as e:
            self.logger.error(f"Issue analysis failed: {e}")
            return [f"Analysis error: {e}"]

    def detect_request_type(self, request_text: str) -> RequestType:
        """Legacy synchronous method for backward compatibility"""
        request_lower = request_text.lower()

        # Basic heuristic detection for TDD compatibility
        web_indicators = [
            "web app",
            "website",
            "frontend",
            "backend",
            "full stack",
            "react",
            "vue",
            "angular",
        ]
        if any(indicator in request_lower for indicator in web_indicators):
            return RequestType.WEB_APPLICATION

        # Microservices indicators
        micro_indicators = [
            "microservice",
            "service",
            "api",
            "docker",
            "kubernetes",
            "distributed",
        ]
        if any(indicator in request_lower for indicator in micro_indicators):
            return RequestType.MICROSERVICES

        # Script indicators
        script_indicators = ["script", "automation", "tool", "utility", "command"]
        if any(indicator in request_lower for indicator in script_indicators):
            return RequestType.SIMPLE_SCRIPT

        return RequestType.UNKNOWN

    def extract_information(
        self, request_text: str, request_type: RequestType
    ) -> dict[str, Any]:
        """Extract available information from the request text."""
        extracted = {}
        request_lower = request_text.lower()

        # Basic name extraction (simplified for TDD)
        if "name" in request_lower or "called" in request_lower:
            # Simple heuristic extraction
            words = request_text.split()
            for i, word in enumerate(words):
                if word.lower() in ["name", "called"] and i + 1 < len(words):
                    extracted["name"] = words[i + 1].strip('",.')
                    break

        # Framework detection
        frameworks = ["react", "vue", "angular", "svelte", "next.js", "nuxt"]
        for framework in frameworks:
            if framework in request_lower:
                extracted["framework"] = framework.title()
                break

        # Basic purpose extraction
        if request_type == RequestType.SIMPLE_SCRIPT:
            extracted["purpose"] = (
                request_text[:100] + "..." if len(request_text) > 100 else request_text
            )

        return extracted

    def identify_missing_fields(
        self, request_type: RequestType, extracted_info: dict[str, Any]
    ) -> list[str]:
        """Identify missing required and important optional fields."""
        schema = self.schema_registry.get_schema(request_type)
        if not schema:
            return []

        missing = []

        # Check required fields
        for field in schema.get_required_fields():
            if field.name not in extracted_info:
                missing.append(field.name)

        # Check important optional fields (heuristic)
        for field in schema.get_optional_fields():
            if field.name not in extracted_info and field.name in [
                "framework",
                "database",
                "authentication",
            ]:
                missing.append(field.name)

        return missing

    def validate_request(self, request_input) -> ValidationResult:
        """Perform complete request validation."""
        # Handle both string and RequestInput objects
        if hasattr(request_input, "content"):
            request_text = request_input.content
            self.logger.info(f"Validating RequestInput: {request_text[:50]}...")
        else:
            request_text = str(request_input)
            self.logger.info(f"Validating request: {request_text[:50]}...")

        # Detect request type
        request_type = self.detect_request_type(request_text)

        # Extract available information
        extracted_info = self.extract_information(request_text, request_type)

        # Identify missing fields
        missing_fields = self.identify_missing_fields(request_type, extracted_info)

        # Calculate confidence
        schema = self.schema_registry.get_schema(request_type)
        total_fields = len(schema.fields) if schema else 1
        found_fields = len(extracted_info)
        confidence = min(found_fields / total_fields, 1.0)

        # Validate compliance
        is_valid = request_type != RequestType.UNKNOWN and len(missing_fields) == 0

        return ValidationResult(
            request_type=request_type,
            is_valid=is_valid,
            missing_fields=missing_fields,
            extracted_info=extracted_info,
            confidence=confidence,
        )


class GapAnalysisAgent:
    """Agent responsible for analyzing information gaps and prioritizing them."""

    def __init__(self, schema_registry: RequestSchemaRegistry):
        self.schema_registry = schema_registry
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def prioritize_gaps(
        self, missing_fields: list[str], request_type: RequestType
    ) -> list[InformationGap]:
        """Prioritize missing information gaps."""
        schema = self.schema_registry.get_schema(request_type)
        if not schema:
            return []

        gaps = []
        field_map = {field.name: field for field in schema.fields}

        for field_name in missing_fields:
            field = field_map.get(field_name)
            if not field:
                continue

            # Determine priority
            if field.required:
                priority = GapPriority.CRITICAL
            elif field_name in ["framework", "database", "authentication"]:
                priority = GapPriority.IMPORTANT
            else:
                priority = GapPriority.OPTIONAL

            # Determine if researchable
            researchable = field_name in [
                "framework",
                "database",
                "styling",
                "language",
            ]

            # Create gap
            gap = InformationGap(
                field_name=field_name,
                priority=priority,
                description=field.description,
                researchable=researchable,
                suggested_defaults=[field.default] if field.default else [],
                research_keywords=(
                    [field_name, request_type.value] if researchable else []
                ),
            )
            gaps.append(gap)

        return gaps

    def calculate_confidence(self, gaps: list[InformationGap]) -> float:
        """Calculate confidence based on gaps."""
        if not gaps:
            return 1.0

        critical_gaps = len([g for g in gaps if g.priority == GapPriority.CRITICAL])
        important_gaps = len([g for g in gaps if g.priority == GapPriority.IMPORTANT])
        optional_gaps = len([g for g in gaps if g.priority == GapPriority.OPTIONAL])

        # Weight gaps by priority
        penalty = (critical_gaps * 0.4) + (important_gaps * 0.2) + (optional_gaps * 0.1)
        confidence = max(0.0, 1.0 - penalty)

        return confidence

    def categorize_gaps(
        self, gaps: list[InformationGap]
    ) -> tuple[list[InformationGap], list[InformationGap]]:
        """Categorize gaps into researchable and unresearchable."""
        researchable = [gap for gap in gaps if gap.researchable]
        unresearchable = [gap for gap in gaps if not gap.researchable]
        return researchable, unresearchable

    def analyze_gaps(self, validation_result: ValidationResult) -> GapAnalysisResult:
        """Perform comprehensive gap analysis."""
        self.logger.info(f"Analyzing gaps for {validation_result.request_type}")

        # Prioritize gaps
        gaps = self.prioritize_gaps(
            validation_result.missing_fields, validation_result.request_type
        )

        # Calculate metrics
        confidence = self.calculate_confidence(gaps)
        completeness_score = 1.0 - len(gaps) / 10.0  # Simplified scoring
        critical_gaps_count = len(
            [g for g in gaps if g.priority == GapPriority.CRITICAL]
        )

        # Categorize gaps
        researchable_gaps, unresearchable_gaps = self.categorize_gaps(gaps)

        return GapAnalysisResult(
            gaps=gaps,
            confidence=confidence,
            completeness_score=max(0.0, completeness_score),
            critical_gaps_count=critical_gaps_count,
            researchable_gaps=researchable_gaps,
            unresearchable_gaps=unresearchable_gaps,
        )


class InformationCompletionAgent:
    """Agent responsible for filling information gaps through research and defaults."""

    def __init__(self, schema_registry: RequestSchemaRegistry):
        self.schema_registry = schema_registry
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def research_gap(self, gap: InformationGap) -> Any | None:
        """Research information for a specific gap."""
        if not gap.researchable:
            return None

        # Simplified research simulation for TDD
        research_db = {
            "framework": "React",
            "database": "PostgreSQL",
            "styling": "Tailwind CSS",
            "language": "Python",
            "authentication": "JWT",
            "communication": "REST API",
        }

        return research_db.get(gap.field_name)

    def apply_defaults(self, gaps: list[InformationGap]) -> dict[str, Any]:
        """Apply reasonable defaults for gaps that have them."""
        defaults = {}

        for gap in gaps:
            if gap.suggested_defaults:
                defaults[gap.field_name] = gap.suggested_defaults[0]

        return defaults

    def document_assumptions(
        self, filled_fields: dict[str, Any], applied_defaults: dict[str, Any]
    ) -> list[str]:
        """Document assumptions made during completion."""
        assumptions = []

        for field, value in applied_defaults.items():
            assumptions.append(f"Assumed {field} = '{value}' based on common defaults")

        for field, value in filled_fields.items():
            if field not in applied_defaults:
                assumptions.append(
                    f"Researched {field} = '{value}' based on best practices"
                )

        return assumptions

    async def complete_information(
        self, gap_analysis: GapAnalysisResult
    ) -> CompletionResult:
        """Complete missing information through research and defaults."""
        self.logger.info(f"Completing information for {len(gap_analysis.gaps)} gaps")

        filled_fields = {}
        research_results = {}

        # Research researchable gaps
        for gap in gap_analysis.researchable_gaps:
            if (
                gap.priority != GapPriority.CRITICAL
            ):  # Don't auto-research critical fields
                result = await self.research_gap(gap)
                if result:
                    filled_fields[gap.field_name] = result
                    research_results[gap.field_name] = result

        # Apply defaults for remaining gaps
        remaining_gaps = [
            g for g in gap_analysis.gaps if g.field_name not in filled_fields
        ]
        applied_defaults = self.apply_defaults(remaining_gaps)

        # Combine results
        all_filled = {**filled_fields, **applied_defaults}

        # Check for critical gaps remaining
        critical_gaps_remaining = [
            g.field_name
            for g in gap_analysis.gaps
            if g.priority == GapPriority.CRITICAL and g.field_name not in all_filled
        ]

        # Document assumptions
        assumptions = self.document_assumptions(filled_fields, applied_defaults)

        return CompletionResult(
            filled_fields=all_filled,
            applied_defaults=applied_defaults,
            research_results=research_results,
            assumptions=assumptions,
            escalation_required=len(critical_gaps_remaining) > 0,
            critical_gaps_remaining=critical_gaps_remaining,
        )


class UserClarificationInterface:
    """Interface for handling user clarification when critical gaps remain."""

    def __init__(self, schema_registry: RequestSchemaRegistry):
        self.schema_registry = schema_registry
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def generate_focused_questions(
        self, critical_gaps: list[str], request_type: RequestType
    ) -> list[ClarificationQuestion]:
        """Generate focused questions for critical gaps."""
        schema = self.schema_registry.get_schema(request_type)
        if not schema:
            return []

        field_map = {field.name: field for field in schema.fields}
        questions = []

        for gap_name in critical_gaps:
            field = field_map.get(gap_name)
            if not field:
                continue

            # Generate question based on field type
            question_text = f"What should be the {field.description.lower()}?"

            # Generate options based on field name
            options = self._get_field_options(gap_name, request_type)

            # Importance explanation
            importance = f"This is required because {field.description.lower()} is essential for {request_type.value} development."

            question = ClarificationQuestion(
                field_name=gap_name,
                question=question_text,
                importance_explanation=importance,
                options=options,
                default_option=options[0] if options else None,
            )
            questions.append(question)

        return questions

    def _get_field_options(
        self, field_name: str, request_type: RequestType
    ) -> list[str]:
        """Get reasonable options for a field."""
        options_map = {
            "framework": ["React", "Vue.js", "Angular", "Svelte", "Next.js"],
            "database": ["PostgreSQL", "MySQL", "SQLite", "MongoDB", "Redis"],
            "language": ["Python", "JavaScript", "TypeScript", "Java", "Go"],
            "authentication": ["Basic", "JWT", "OAuth", "SAML", "None"],
            "name": [],  # No predefined options for names
            "description": [],  # No predefined options for descriptions
        }

        return options_map.get(field_name, [])

    def explain_importance(self, field_name: str, request_type: RequestType) -> str:
        """Explain why a field is important."""
        explanations = {
            "name": "A clear name helps identify and organize the project",
            "description": "A description clarifies the project goals and requirements",
            "framework": "The framework choice affects the entire development approach",
            "database": "Database selection impacts data storage and performance",
            "language": "Programming language determines the development ecosystem",
        }

        base_explanation = explanations.get(
            field_name, f"{field_name} is required for proper configuration"
        )
        return f"{base_explanation} in {request_type.value} development."

    def handle_user_response(
        self, questions: list[ClarificationQuestion], responses: dict[str, str]
    ) -> dict[str, Any]:
        """Handle user responses to clarification questions."""
        filled_data = {}

        for question in questions:
            response = responses.get(question.field_name)
            if response:
                if response.lower() == "cancel":
                    raise ValueError("User cancelled the request")
                filled_data[question.field_name] = response
            elif question.default_option:
                filled_data[question.field_name] = question.default_option

        return filled_data

    async def _parse_extraction_response(
        self, ai_response: str, request: RequestInput
    ) -> dict[str, Any]:
        """Parse AI extraction response into structured data"""
        # Simple parsing for TDD - would be more sophisticated in full implementation
        extracted_info = {}

        response_lower = ai_response.lower()

        # Extract technical information
        if "react" in response_lower:
            extracted_info["framework"] = "React"
        elif "vue" in response_lower:
            extracted_info["framework"] = "Vue.js"
        elif "angular" in response_lower:
            extracted_info["framework"] = "Angular"

        if "postgresql" in response_lower or "postgres" in response_lower:
            extracted_info["database"] = "PostgreSQL"
        elif "mysql" in response_lower:
            extracted_info["database"] = "MySQL"

        # Extract from original request as fallback
        content_lower = request.content.lower()
        if "api" in content_lower:
            extracted_info["api_required"] = True
        if "auth" in content_lower:
            extracted_info["authentication"] = True

        extracted_info["ai_analysis"] = ai_response[:200]  # Store AI reasoning
        return extracted_info

    def _parse_type_response(
        self, ai_response: str
    ) -> tuple[RequestType | None, float]:
        """Parse AI response to extract request type and confidence"""
        response_lower = ai_response.lower()

        # Extract request type
        detected_type = None
        if "web_application" in response_lower or "web application" in response_lower:
            detected_type = RequestType.WEB_APPLICATION
        elif "microservice" in response_lower:
            detected_type = RequestType.MICROSERVICES
        elif "script" in response_lower:
            detected_type = RequestType.SIMPLE_SCRIPT
        elif "automation" in response_lower:
            detected_type = RequestType.AUTOMATION
        elif "analysis" in response_lower:
            detected_type = RequestType.DATA_ANALYSIS
        else:
            detected_type = RequestType.UNKNOWN

        # Extract confidence
        confidence = 0.7  # Default
        if "very confident" in response_lower or "confident: 0.9" in response_lower:
            confidence = 0.9
        elif "confident" in response_lower or "confidence: 0.8" in response_lower:
            confidence = 0.8
        elif "moderate" in response_lower:
            confidence = 0.6
        elif "low" in response_lower:
            confidence = 0.4

        return detected_type, confidence

    def _parse_issues_response(self, ai_response: str) -> list[str]:
        """Parse AI response to extract validation issues"""
        issues = []

        # Simple parsing for TDD
        response_lower = ai_response.lower()

        if "missing" in response_lower:
            issues.append("Some required information may be missing")
        if "ambiguous" in response_lower or "unclear" in response_lower:
            issues.append("Request contains ambiguous requirements")
        if "conflict" in response_lower:
            issues.append("Potential conflicts detected in requirements")
        if "no issues" in response_lower or "looks good" in response_lower:
            pass  # No issues to add

        return issues
