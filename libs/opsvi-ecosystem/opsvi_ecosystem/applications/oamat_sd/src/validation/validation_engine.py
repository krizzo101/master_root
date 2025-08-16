"""
Validation Engine Module

AI-powered request validation and information extraction.
Extracted from request_validation.py for better modularity.
"""

import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.applications.oamat_sd.src.config.config_manager import ConfigManager
from src.applications.oamat_sd.src.models.validation_models import (
    RequestType,
    ValidationResult,
)
from src.applications.oamat_sd.src.validation.schema_registry import (
    RequestSchemaRegistry,
)


class ValidationEngine:
    """AI-powered request validation and information extraction"""

    def __init__(
        self,
        schema_registry: RequestSchemaRegistry,
        model_config: dict[str, Any] | None = None,
    ):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.schema_registry = schema_registry

        # NO FALLBACKS RULE: Model configuration strictly required for AI features
        if model_config and "model" in model_config:
            model_name = model_config["model"]
            model_kwargs = {"model": model_name}
            if not model_name.startswith("o3"):
                model_kwargs[
                    "temperature"
                ] = 0.1  # Low temperature for consistent analysis

            self.ai_model = ChatOpenAI(**model_kwargs)
            self.ai_enabled = True
            self.logger.info(
                f"✅ AI-powered validation enabled with model: {model_name}"
            )
        else:
            self.ai_model = None
            self.ai_enabled = False
            self.logger.info("🔧 Standard validation mode (no AI)")

    async def validate_request(self, request_content: str) -> ValidationResult:
        """
        Dynamically validate request using AI-driven analysis or standard patterns
        """
        self.logger.info("🎯 Starting request validation")

        if self.ai_enabled:
            return await self._ai_validate_request(request_content)
        else:
            return await self._standard_validate_request(request_content)

    async def _ai_validate_request(self, request_content: str) -> ValidationResult:
        """AI-powered request validation"""
        try:
            # Step 1: AI Request Type Detection
            request_type, type_confidence = await self._ai_detect_request_type(
                request_content
            )

            # Step 2: AI Information Extraction
            extracted_info = await self._ai_extract_information(
                request_content, request_type
            )

            # Step 3: AI Missing Fields Detection
            missing_fields = await self._ai_detect_missing_fields(
                request_content, request_type, extracted_info
            )

            # Step 4: Validation Assessment
            is_valid = request_type != RequestType.UNKNOWN and len(missing_fields) == 0

            # Calculate overall confidence
            confidence = (type_confidence + len(extracted_info) * 0.1) / 2.0
            confidence = min(confidence, 1.0)

            result = ValidationResult(
                request_type=request_type,
                is_valid=is_valid,
                missing_fields=missing_fields,
                extracted_info=extracted_info,
                confidence=confidence,
            )

            self.logger.info(
                f"✅ AI validation complete: {request_type}, valid: {is_valid}, confidence: {confidence:.2f}"
            )
            return result

        except Exception as e:
            self.logger.error(f"❌ AI validation failed: {e}")
            # NO FALLBACKS RULE: Must fail completely if AI analysis fails
            raise RuntimeError(
                f"AI validation failed: {e}. Cannot proceed without AI analysis."
            )

    async def _standard_validate_request(
        self, request_content: str
    ) -> ValidationResult:
        """Standard pattern-based validation"""
        # Detect request type using keywords
        request_type = self._pattern_detect_request_type(request_content)

        # Extract basic information using patterns
        extracted_info = self._pattern_extract_information(request_content)

        # Check missing fields
        missing_fields = self._pattern_detect_missing_fields(
            request_type, extracted_info
        )

        # Simple validation - NO HARDCODED VALUES
        is_valid = (
            request_type != RequestType.UNKNOWN
            and len(missing_fields)
            <= ConfigManager().validation.missing_fields_threshold
        )
        confidence = (
            ConfigManager().validation.confidence_scores["valid_request"]
            if is_valid
            else ConfigManager().validation.confidence_scores["invalid_request"]
        )

        result = ValidationResult(
            request_type=request_type,
            is_valid=is_valid,
            missing_fields=missing_fields,
            extracted_info=extracted_info,
            confidence=confidence,
        )

        self.logger.info(
            f"✅ Standard validation complete: {request_type}, valid: {is_valid}"
        )
        return result

    async def _ai_detect_request_type(
        self, request_content: str
    ) -> tuple[RequestType, float]:
        """Use AI to detect request type"""
        system_prompt = """You are an expert software project analyzer. Analyze the request and determine the type of project being described.

Request types:
- web_application: Full-stack web applications, websites, web services
- microservices: Microservices architecture, distributed systems, service mesh
- simple_script: Scripts, utilities, automation tools, command-line tools
- data_analysis: Data processing, analytics, visualization, ML/AI projects
- automation: Process automation, workflows, CI/CD, infrastructure automation

Respond with ONLY the request type and confidence (0.0-1.0), format: "TYPE:CONFIDENCE"
Example: "web_application:0.9" """

        user_prompt = f"Analyze this request:\n\n{request_content}"

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        response = await self.ai_model.ainvoke(messages)
        return self._parse_type_response(response.content)

    async def _ai_extract_information(
        self, request_content: str, request_type: RequestType
    ) -> dict[str, Any]:
        """Use AI to extract information from request"""
        schema = self.schema_registry.get_schema(request_type)
        if not schema:
            return {}

        field_descriptions = "\n".join(
            [f"- {field.name}: {field.description}" for field in schema.fields]
        )

        system_prompt = f"""Extract information for a {request_type.value} project. Look for these fields:

{field_descriptions}

Extract any values mentioned in the request. Return ONLY a JSON object with field names as keys and extracted values as values.
If a field is not mentioned, do not include it in the response.
Example: {{"name": "My App", "framework": "React", "database": "PostgreSQL"}}"""

        user_prompt = f"Extract information from this request:\n\n{request_content}"

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        response = await self.ai_model.ainvoke(messages)
        return self._parse_extraction_response(response.content)

    async def _ai_detect_missing_fields(
        self,
        request_content: str,
        request_type: RequestType,
        extracted_info: dict[str, Any],
    ) -> list[str]:
        """Use AI to detect missing critical fields"""
        schema = self.schema_registry.get_schema(request_type)
        if not schema:
            return []

        required_fields = [field.name for field in schema.get_required_fields()]
        missing_required = [
            field for field in required_fields if field not in extracted_info
        ]

        # For non-required fields, use AI to determine what's missing
        all_fields = [field.name for field in schema.fields]
        missing_all = [field for field in all_fields if field not in extracted_info]

        if len(missing_all) <= 2:  # Small number of missing fields
            return missing_required

        # Use AI to prioritize missing fields
        system_prompt = f"""Given a {request_type.value} project request, identify which missing fields are most important to clarify.

Available fields: {', '.join(all_fields)}
Already extracted: {', '.join(extracted_info.keys()) if extracted_info else 'none'}
Missing fields: {', '.join(missing_all)}

Return ONLY a JSON list of the 3-5 most important missing fields that should be clarified.
Example: ["database", "authentication", "deployment"]"""

        user_prompt = (
            f"Prioritize missing fields for this request:\n\n{request_content}"
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        response = await self.ai_model.ainvoke(messages)
        ai_missing = self._parse_missing_fields_response(response.content)

        # Ensure required fields are included
        final_missing = list(set(missing_required + ai_missing))
        return final_missing

    def _pattern_detect_request_type(self, request_content: str) -> RequestType:
        """Pattern-based request type detection"""
        content_lower = request_content.lower()

        # Web application indicators
        web_indicators = [
            "web app",
            "website",
            "web application",
            "frontend",
            "backend",
            "full stack",
            "react",
            "vue",
            "angular",
        ]
        if any(indicator in content_lower for indicator in web_indicators):
            return RequestType.WEB_APPLICATION

        # Microservices indicators
        micro_indicators = [
            "microservice",
            "microservices",
            "distributed",
            "service mesh",
            "api gateway",
            "docker",
            "kubernetes",
        ]
        if any(indicator in content_lower for indicator in micro_indicators):
            return RequestType.MICROSERVICES

        # Data analysis indicators
        data_indicators = [
            "data analysis",
            "analytics",
            "visualization",
            "machine learning",
            "ml",
            "ai",
            "pandas",
            "jupyter",
        ]
        if any(indicator in content_lower for indicator in data_indicators):
            return RequestType.DATA_ANALYSIS

        # Automation indicators
        auto_indicators = [
            "automate",
            "automation",
            "workflow",
            "ci/cd",
            "pipeline",
            "deploy",
            "infrastructure",
        ]
        if any(indicator in content_lower for indicator in auto_indicators):
            return RequestType.AUTOMATION

        # Script indicators
        script_indicators = [
            "script",
            "utility",
            "tool",
            "command line",
            "cli",
            "batch",
            "bash",
            "python script",
        ]
        if any(indicator in content_lower for indicator in script_indicators):
            return RequestType.SIMPLE_SCRIPT

        return RequestType.UNKNOWN

    def _pattern_extract_information(self, request_content: str) -> dict[str, Any]:
        """Pattern-based information extraction"""
        content_lower = request_content.lower()
        extracted = {}

        # Extract technology mentions
        if "react" in content_lower:
            extracted["framework"] = "React"
        elif "vue" in content_lower:
            extracted["framework"] = "Vue"
        elif "angular" in content_lower:
            extracted["framework"] = "Angular"

        if "postgresql" in content_lower or "postgres" in content_lower:
            extracted["database"] = "PostgreSQL"
        elif "mysql" in content_lower:
            extracted["database"] = "MySQL"
        elif "sqlite" in content_lower:
            extracted["database"] = "SQLite"

        # Extract programming language
        if "python" in content_lower:
            extracted["language"] = "Python"
        elif "javascript" in content_lower or "js" in content_lower:
            extracted["language"] = "JavaScript"
        elif "java" in content_lower:
            extracted["language"] = "Java"

        return extracted

    def _pattern_detect_missing_fields(
        self, request_type: RequestType, extracted_info: dict[str, Any]
    ) -> list[str]:
        """Pattern-based missing field detection"""
        schema = self.schema_registry.get_schema(request_type)
        if not schema:
            return []

        required_fields = [field.name for field in schema.get_required_fields()]
        missing_required = [
            field for field in required_fields if field not in extracted_info
        ]

        # Add important optional fields if not present
        important_optional = ["framework", "database", "authentication"]
        missing_important = [
            field for field in important_optional if field not in extracted_info
        ]

        return missing_required + missing_important[:2]  # Limit to avoid overwhelming

    def _parse_type_response(self, ai_response: str) -> tuple[RequestType, float]:
        """Parse AI request type response"""
        try:
            if ":" in ai_response:
                type_str, confidence_str = ai_response.strip().split(":", 1)
                confidence = float(confidence_str)

                type_map = {
                    "technical": RequestType.TECHNICAL,
                    "creative": RequestType.CREATIVE,
                    "data_analysis": RequestType.DATA_ANALYSIS,
                    "automation": RequestType.AUTOMATION,
                }

                type_key = type_str.strip()
                if type_key not in type_map:
                    self.logger.warning(f"Unknown request type: {type_key}")
                    detected_type = RequestType.UNKNOWN
                else:
                    detected_type = type_map[type_key]

                return detected_type, confidence
        except Exception as e:
            self.logger.error(f"Failed to parse AI response for request type: {e}")
            raise RuntimeError(
                f"Request type parsing failed - no fallbacks allowed: {e}"
            )

    def _parse_extraction_response(self, ai_response: str) -> dict[str, Any]:
        """Parse AI information extraction response"""
        try:
            import json

            # Try to parse as JSON
            response = ai_response.strip()
            if response.startswith("{") and response.endswith("}"):
                return json.loads(response)
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.error(f"Failed to parse AI response as JSON: {e}")
            raise RuntimeError(f"JSON parsing failed - no fallbacks allowed: {e}")

    def _parse_missing_fields_response(self, ai_response: str) -> list[str]:
        """Parse AI missing fields response"""
        try:
            import json

            # Try to parse as JSON list
            response = ai_response.strip()
            if response.startswith("[") and response.endswith("]"):
                return json.loads(response)
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.error(f"Failed to parse AI response as JSON list: {e}")
            raise RuntimeError(f"JSON list parsing failed - no fallbacks allowed: {e}")
