"""
Clarification Interface Module

Handles user interaction and AI-powered response parsing for clarifications.
Extracted from request_validation.py for better modularity.
"""

import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.applications.oamat_sd.src.models.validation_models import (
    ClarificationQuestion,
    GapPriority,
    InformationGap,
    RequestType,
)


class ClarificationInterface:
    """Handles user interaction and clarification processing"""

    def __init__(self, model_config: dict[str, Any] | None = None):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # AI model for intelligent clarification generation
        if model_config and "model" in model_config:
            model_name = model_config["model"]
            model_kwargs = {"model": model_name}
            if not model_name.startswith("o3"):
                model_kwargs[
                    "temperature"
                ] = 0.3  # Slightly higher for more natural questions

            self.ai_model = ChatOpenAI(**model_kwargs)
            self.ai_enabled = True
            self.logger.info(
                f"✅ AI-powered clarification enabled with model: {model_name}"
            )
        else:
            self.ai_model = None
            self.ai_enabled = False
            self.logger.info("🔧 Standard clarification mode (no AI)")

    async def generate_clarification_questions(
        self,
        gaps: list[InformationGap],
        request_type: RequestType,
        original_request: str = "",
    ) -> list[ClarificationQuestion]:
        """Generate focused clarification questions for information gaps"""

        if self.ai_enabled:
            return await self._ai_generate_questions(
                gaps, request_type, original_request
            )
        else:
            return self._standard_generate_questions(gaps, request_type)

    async def _ai_generate_questions(
        self,
        gaps: list[InformationGap],
        request_type: RequestType,
        original_request: str,
    ) -> list[ClarificationQuestion]:
        """AI-powered clarification question generation"""

        if not gaps:
            return []

        # Prioritize critical gaps first
        critical_gaps = [g for g in gaps if g.priority == GapPriority.CRITICAL]
        important_gaps = [g for g in gaps if g.priority == GapPriority.IMPORTANT]
        prioritized_gaps = (critical_gaps + important_gaps)[:5]  # Limit to 5 questions

        questions = []

        for gap in prioritized_gaps:
            try:
                question = await self._ai_generate_single_question(
                    gap, request_type, original_request
                )
                if question:
                    questions.append(question)
            except Exception as e:
                self.logger.warning(
                    f"Failed to generate AI question for {gap.field_name}: {e}"
                )
                # Fallback to standard question
                fallback_question = self._standard_generate_single_question(
                    gap, request_type
                )
                if fallback_question:
                    questions.append(fallback_question)

        return questions

    async def _ai_generate_single_question(
        self, gap: InformationGap, request_type: RequestType, original_request: str
    ) -> ClarificationQuestion | None:
        """Generate a single clarification question using AI"""

        system_prompt = f"""You are a helpful project consultant. Generate a clear, specific question to clarify missing information for a {request_type.value} project.

Rules:
1. Ask ONE focused question about the missing field
2. Provide context about why this information is important
3. Suggest 2-4 realistic options if applicable
4. Keep questions conversational and non-technical for end users
5. Focus on business/user needs, not technical implementation details

Field to clarify: {gap.field_name}
Field description: {gap.description}
Priority: {gap.priority.value}

Format your response as JSON:
{{
    "question": "What would you like...",
    "importance": "This helps us...",
    "options": ["Option 1", "Option 2", "Option 3"],
    "default": "Option 1"
}}"""

        user_prompt = f"""Original request: "{original_request}"

Generate a clarification question for the missing field: {gap.field_name}"""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]

            response = await self.ai_model.ainvoke(messages)
            question_data = self._parse_question_response(response.content)

            if question_data:
                return ClarificationQuestion(
                    field_name=gap.field_name,
                    question=question_data.get(
                        "question", f"What would you like for {gap.field_name}?"
                    ),
                    importance_explanation=question_data.get(
                        "importance",
                        f"This helps determine the {gap.description.lower()}",
                    ),
                    options=(
                        question_data.get("options")
                        if "options" in question_data
                        else []
                    ),
                    default_option=question_data.get("default"),
                )
        except Exception as e:
            self.logger.error(
                f"AI question generation failed for {gap.field_name}: {e}"
            )

        return None

    def _standard_generate_questions(
        self, gaps: list[InformationGap], request_type: RequestType
    ) -> list[ClarificationQuestion]:
        """Standard template-based clarification question generation"""

        questions = []
        critical_gaps = [g for g in gaps if g.priority == GapPriority.CRITICAL]
        important_gaps = [g for g in gaps if g.priority == GapPriority.IMPORTANT]

        # Process critical gaps first, then important ones
        prioritized_gaps = (critical_gaps + important_gaps)[:5]

        for gap in prioritized_gaps:
            question = self._standard_generate_single_question(gap, request_type)
            if question:
                questions.append(question)

        return questions

    def _standard_generate_single_question(
        self, gap: InformationGap, request_type: RequestType
    ) -> ClarificationQuestion | None:
        """Generate a single clarification question using templates"""

        # Standard question templates by field
        question_templates = {
            "name": {
                "question": "What would you like to name your application/project?",
                "importance": "This helps us create properly named files and documentation",
                "options": [],
            },
            "description": {
                "question": "Can you provide a brief description of what this project should do?",
                "importance": "This helps us understand the core functionality and purpose",
                "options": [],
            },
            "framework": {
                "question": "Which web framework would you prefer?",
                "importance": "This determines the technology stack and development approach",
                "options": ["React", "Vue.js", "Angular", "Svelte", "Plain JavaScript"],
                "default": "React",
            },
            "database": {
                "question": "What type of database would you like to use?",
                "importance": "This affects data storage, performance, and deployment options",
                "options": [
                    "PostgreSQL",
                    "MySQL",
                    "SQLite",
                    "MongoDB",
                    "No database needed",
                ],
                "default": "PostgreSQL",
            },
            "authentication": {
                "question": "What type of user authentication do you need?",
                "importance": "This determines security setup and user management features",
                "options": [
                    "Basic login/password",
                    "OAuth (Google/GitHub)",
                    "JWT tokens",
                    "No authentication needed",
                ],
                "default": "Basic login/password",
            },
            "language": {
                "question": "Which programming language would you prefer?",
                "importance": "This determines the development environment and available libraries",
                "options": ["Python", "JavaScript", "TypeScript", "Java", "Go"],
                "default": "Python",
            },
            "styling": {
                "question": "How would you like to handle styling and UI?",
                "importance": "This affects the visual appearance and development workflow",
                "options": [
                    "Tailwind CSS",
                    "Bootstrap",
                    "Material-UI",
                    "Plain CSS",
                    "Styled Components",
                ],
                "default": "Tailwind CSS",
            },
        }

        template = question_templates.get(gap.field_name)
        if not template:
            # Generic template for unknown fields
            template = {
                "question": f"What would you like for {gap.field_name}?",
                "importance": f"This helps us configure the {gap.description.lower()}",
                "options": gap.suggested_defaults if gap.suggested_defaults else [],
            }

        return ClarificationQuestion(
            field_name=gap.field_name,
            question=template["question"],
            importance_explanation=template["importance"],
            options=template.get("options") if "options" in template else [],
            default_option=template.get("default") if "default" in template else None,
        )

    def format_questions_for_user(self, questions: list[ClarificationQuestion]) -> str:
        """Format clarification questions for user presentation"""

        if not questions:
            return "No clarification needed - all required information is available."

        formatted_lines = [
            "I need some additional information to proceed with your request:\n"
        ]

        for i, question in enumerate(questions, 1):
            formatted_lines.append(f"{i}. **{question.question}**")
            formatted_lines.append(f"   _{question.importance_explanation}_")

            if question.options:
                formatted_lines.append("   Options:")
                for option in question.options:
                    marker = (
                        " (recommended)" if option == question.default_option else ""
                    )
                    formatted_lines.append(f"   - {option}{marker}")

            formatted_lines.append("")  # Empty line between questions

        return "\n".join(formatted_lines)

    async def parse_user_responses(
        self, user_input: str, questions: list[ClarificationQuestion]
    ) -> dict[str, Any]:
        """Parse user responses to clarification questions"""

        if self.ai_enabled:
            return await self._ai_parse_responses(user_input, questions)
        else:
            return self._standard_parse_responses(user_input, questions)

    async def _ai_parse_responses(
        self, user_input: str, questions: list[ClarificationQuestion]
    ) -> dict[str, Any]:
        """AI-powered response parsing"""

        question_context = "\n".join(
            [f"- {q.field_name}: {q.question}" for q in questions]
        )

        system_prompt = f"""Parse user responses to clarification questions and extract field values.

Questions asked:
{question_context}

Extract the answer for each field. Return ONLY a JSON object with field names as keys and user's answers as values.
If a field is not answered, do not include it.
Example: {{"framework": "React", "database": "PostgreSQL", "authentication": "JWT"}}"""

        user_prompt = f"User responses: {user_input}"

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]

            response = await self.ai_model.ainvoke(messages)
            return self._parse_response_extraction(response.content)

        except Exception as e:
            self.logger.error(f"AI response parsing failed: {e}")
            # Fallback to standard parsing
            return self._standard_parse_responses(user_input, questions)

    def _standard_parse_responses(
        self, user_input: str, questions: list[ClarificationQuestion]
    ) -> dict[str, Any]:
        """Standard pattern-based response parsing"""

        responses = {}
        user_lower = user_input.lower()

        for question in questions:
            field_name = question.field_name

            # Check if any options are mentioned
            if question.options:
                for option in question.options:
                    if option.lower() in user_lower:
                        responses[field_name] = option
                        break

            # If no option matched, try to extract based on field patterns
            if field_name not in responses:
                if field_name == "name":
                    # Look for quoted names or "called" patterns
                    import re

                    name_match = re.search(
                        r'"([^"]+)"|called\s+(\w+)|name.*?(\w+)',
                        user_input,
                        re.IGNORECASE,
                    )
                    if name_match:
                        responses[field_name] = (
                            name_match.group(1)
                            or name_match.group(2)
                            or name_match.group(3)
                        )

                elif field_name in [
                    "framework",
                    "database",
                    "language",
                    "authentication",
                ]:
                    # Use default if available
                    if question.default_option:
                        responses[field_name] = question.default_option

        return responses

    def _parse_question_response(self, ai_response: str) -> dict[str, Any] | None:
        """Parse AI-generated question response"""
        try:
            import json

            response = ai_response.strip()
            if response.startswith("{") and response.endswith("}"):
                return json.loads(response)
        except:
            pass

        # Fallback parsing
        question_data = {}
        lines = ai_response.split("\n")

        for line in lines:
            if '"question"' in line:
                question_data["question"] = self._extract_quoted_value(line)
            elif '"importance"' in line:
                question_data["importance"] = self._extract_quoted_value(line)
            elif '"default"' in line:
                question_data["default"] = self._extract_quoted_value(line)

        return question_data if question_data else None

    def _parse_response_extraction(self, ai_response: str) -> dict[str, Any]:
        """Parse AI response extraction"""
        try:
            import json

            response = ai_response.strip()
            if response.startswith("{") and response.endswith("}"):
                return json.loads(response)
        except:
            pass

        # Fallback: simple pattern extraction
        extracted = {}
        lines = ai_response.split("\n")
        for line in lines:
            if ":" in line and not line.strip().startswith("#"):
                try:
                    key, value = line.split(":", 1)
                    key = key.strip().strip('"').strip("'")
                    value = value.strip().strip('"').strip("'").strip(",")
                    if key and value:
                        extracted[key] = value
                except:
                    continue

        return extracted

    def _extract_quoted_value(self, line: str) -> str:
        """Extract value from quoted string in a line"""
        import re

        match = re.search(r'"([^"]*)"', line)
        return match.group(1) if match else ""
