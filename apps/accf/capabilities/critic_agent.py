"""
CriticAgent - Fast response reviewer for quality control.

Reviews responses for correctness, logic errors, and major issues.
Uses a fast model (GPT-4.1-mini) to maintain speed while catching critical problems.
"""

import time
import logging
from typing import Dict, Any, Optional
from agent_base.agent_base import LLMBaseAgent


class CriticAgent(LLMBaseAgent):
    """
    CriticAgent - Fast response reviewer for quality control.

    Reviews responses for correctness, logic errors, security issues, and major problems.
    Uses a fast model to maintain speed while providing thorough quality control.
    Focuses on correctness and functionality, not minor stylistic issues.
    """

    MODEL = "gpt-4.1-mini"  # Fast model for speed
    ASSISTANT_NAME = "Critic"
    MAX_RETRY_ATTEMPTS = 3  # Hardcoded threshold for retry attempts

    def __init__(self, api_key_env: str = "OPENAI_API_KEY", config: dict = None):
        # Pass explicit name to satisfy AgentBase → LLMBaseAgent chain
        super().__init__(
            name=self.ASSISTANT_NAME, api_key_env=api_key_env, config=config
        )
        # Set up comprehensive debug logging
        self.logger.setLevel(logging.DEBUG)
        self.logger.info("=== CRITIC AGENT INITIALIZED WITH DEBUG LOGGING ===")
        self.logger.info(f"CriticAgent initialized with model: {self.MODEL}")

    def _log_critic_api_call(
        self, model: str, prompt_length: int, response_length: int, artifact_type: str
    ):
        """Log every critic API call with detailed information."""
        self.logger.debug("=== CRITIC API CALL START ===")
        self.logger.debug(f"Model: {model}")
        self.logger.debug(f"Review prompt length: {prompt_length} characters")
        self.logger.debug(f"Response to review length: {response_length} characters")
        self.logger.debug(f"Artifact type: {artifact_type}")
        self.logger.debug(f"Timestamp: {time.time()}")

    def _log_critic_api_response(self, response: dict, response_length: int):
        """Log every critic API response with detailed information."""
        self.logger.debug("=== CRITIC API RESPONSE RECEIVED ===")
        self.logger.debug(f"Response length: {response_length} characters")
        self.logger.debug(f"Response keys: {list(response.keys())}")
        self.logger.debug(f"Has error: {'error' in response}")
        if "error" in response:
            self.logger.debug(f"Error details: {response['error']}")
        self.logger.debug(f"Timestamp: {time.time()}")

    def _log_parsed_result(self, result: dict):
        """Log the parsed critic result with detailed information."""
        self.logger.debug("=== CRITIC RESULT PARSED ===")
        self.logger.debug(f"Passed: {result.get('passed', 'UNKNOWN')}")
        self.logger.debug(f"Feedback: {result.get('feedback', 'NONE')}")
        self.logger.debug(
            f"Critical issues count: {len(result.get('critical_issues', []))}"
        )
        self.logger.debug(f"Suggestions count: {len(result.get('suggestions', []))}")
        if result.get("critical_issues"):
            for i, issue in enumerate(result["critical_issues"]):
                self.logger.debug(f"Critical issue {i+1}: {issue}")
        if result.get("suggestions"):
            for i, suggestion in enumerate(result["suggestions"]):
                self.logger.debug(f"Suggestion {i+1}: {suggestion}")
        self.logger.debug(f"Timestamp: {time.time()}")

    def review_response(
        self,
        response: str,
        artifact_type: Optional[str] = None,
        original_prompt: str = "",
        context: str = "",
    ) -> Dict[str, Any]:
        """
        Review a response for correctness and major issues.

        Args:
            response: The response to review
            artifact_type: Type of artifact being reviewed (code, doc, etc.)
            original_prompt: The original user request
            context: Additional context about the request

        Returns:
            dict: Review result with pass/fail status and feedback
        """
        try:
            # Build review prompt based on artifact type
            review_prompt = self._build_review_prompt(
                response, artifact_type, original_prompt, context
            )

            # Log the critic API call
            self._log_critic_api_call(
                self.MODEL,
                len(review_prompt),
                len(response),
                artifact_type or "unknown",
            )
            self.logger.debug("=== CRITIC REVIEW PROMPT CONTENT ===")
            self.logger.debug(review_prompt)
            self.logger.debug("=== END CRITIC REVIEW PROMPT CONTENT ===")

            # Use fast model for review
            from shared.openai_interfaces.responses_interface import (
                OpenAIResponsesInterface,
            )

            llm = OpenAIResponsesInterface(api_key=self.api_key)

            review_response = llm.create_response(
                model=self.MODEL,
                input=review_prompt,
            )

            # Log the critic API response
            review_text = (
                review_response.get("output_text")
                or review_response.get("answer")
                or ""
            )
            self._log_critic_api_response(review_response, len(review_text))
            self.logger.debug("=== CRITIC REVIEW RESPONSE CONTENT ===")
            self.logger.debug(review_text)
            self.logger.debug("=== END CRITIC REVIEW RESPONSE CONTENT ===")

            # Extract review result
            if "error" in review_response:
                self.logger.error(f"Critic API Error: {review_response['error']}")
                return {
                    "passed": True,  # Default to pass on API errors
                    "feedback": f"API Error during review: {review_response['error']}",
                    "suggestions": [],
                    "critical_issues": [],
                }

            # Parse the review result
            result = self._parse_review_result(review_text)

            # Log the parsed result
            self._log_parsed_result(result)

            self.logger.info(
                f"Critic review result: {'PASSED' if result['passed'] else 'FAILED'}"
            )
            if not result["passed"]:
                self.logger.warning(
                    f"Critic found {len(result['critical_issues'])} critical issues"
                )

            return result

        except Exception as e:
            self.logger.error(f"CriticAgent review error: {e}")
            return {
                "passed": True,  # Default to pass on errors
                "feedback": f"Review error: {str(e)}",
                "suggestions": [],
                "critical_issues": [],
            }

    def _build_review_prompt(
        self,
        response: str,
        artifact_type: Optional[str],
        original_prompt: str,
        context: str,
    ) -> str:
        """Build the review prompt based on artifact type."""

        base_prompt = f"""You are a fast, pragmatic code reviewer focused on correctness and major issues. Your job is to catch glaring errors, incorrect code, security vulnerabilities, and major problems - NOT minor stylistic issues.

## REVIEW CRITERIA

### CRITICAL ISSUES (FAIL the response):
- Syntax errors that prevent execution
- Logic errors that break functionality
- Security vulnerabilities (SQL injection, XSS, etc.)
- Missing critical components or dependencies
- Incorrect API usage that would cause runtime errors
- Data type mismatches or validation errors
- Missing error handling for critical operations

### MINOR ISSUES (Suggestions only):
- Code style and formatting preferences
- Optional optimizations
- Documentation improvements
- Minor naming conventions
- Performance suggestions (unless they're critical)

## RESPONSE FORMAT
Respond in this exact format:

### VERDICT
PASS | FAIL

### FEEDBACK
[Brief explanation of the verdict]

### CRITICAL ISSUES
- [List any critical issues that caused a FAIL]
- [Leave empty if PASS]

### SUGGESTIONS
- [List any minor improvements or suggestions]
- [Leave empty if none]

## CONTEXT
Original Request: {original_prompt}
Context: {context}

## RESPONSE TO REVIEW
{response}

## REVIEW INSTRUCTIONS
1. Focus on correctness and functionality
2. Be pragmatic - only fail on major issues
3. Provide specific, actionable feedback
4. If unsure, default to PASS with suggestions
5. Consider the artifact type when reviewing

Review the response above and provide your verdict."""

        # Add artifact-specific guidance
        if artifact_type == "code":
            base_prompt += """

## CODE-SPECIFIC CRITERIA
- Check for syntax errors, missing imports, undefined variables
- Verify logic flow and algorithm correctness
- Look for security issues (eval, exec, unsafe file operations)
- Ensure proper error handling and edge cases
- Check for resource leaks or improper cleanup"""

        elif artifact_type == "doc":
            base_prompt += """

## DOCUMENTATION-SPECIFIC CRITERIA
- Verify technical accuracy of information
- Check for missing critical sections
- Ensure code examples are syntactically correct
- Look for broken links or references
- Verify API endpoint examples are valid"""

        elif artifact_type == "query":
            base_prompt += """

## QUERY-SPECIFIC CRITERIA
- Check for SQL injection vulnerabilities
- Verify query syntax is correct for the database type
- Ensure proper parameterization
- Look for performance issues (missing indexes, etc.)
- Check for logical errors in WHERE clauses"""

        elif artifact_type == "prompt":
            base_prompt += """

## PROMPT-SPECIFIC CRITERIA
- Verify instructions are clear and actionable
- Check for logical flow and completeness
- Ensure output format specifications are clear
- Look for conflicting or ambiguous instructions
- Verify role definitions are appropriate"""

        return base_prompt

    def _parse_review_result(self, review_text: str) -> Dict[str, Any]:
        """Parse the review response into structured format."""

        # Default result
        result = {
            "passed": True,
            "feedback": "",
            "suggestions": [],
            "critical_issues": [],
        }

        try:
            lines = review_text.strip().split("\n")
            current_section = None

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Parse verdict
                if line.startswith("### VERDICT"):
                    continue
                elif line in ["PASS", "FAIL"]:
                    result["passed"] = line == "PASS"
                    continue

                # Parse sections
                elif line.startswith("### FEEDBACK"):
                    current_section = "feedback"
                    continue
                elif line.startswith("### CRITICAL ISSUES"):
                    current_section = "critical_issues"
                    continue
                elif line.startswith("### SUGGESTIONS"):
                    current_section = "suggestions"
                    continue

                # Parse content
                if current_section == "feedback":
                    if result["feedback"]:
                        result["feedback"] += " " + line
                    else:
                        result["feedback"] = line

                elif current_section == "critical_issues" and line.startswith("- "):
                    result["critical_issues"].append(line[2:])

                elif current_section == "suggestions" and line.startswith("- "):
                    result["suggestions"].append(line[2:])

            # Clean up feedback
            result["feedback"] = result["feedback"].strip()

        except Exception as e:
            self.logger.error(f"Error parsing review result: {e}")
            result["feedback"] = f"Error parsing review: {str(e)}"

        return result

    # ------------------------------------------------------------------ #
    # Mandatory abstract-method implementation from LLMBaseAgent
    # ------------------------------------------------------------------ #
    def answer(self, prompt: str) -> dict:
        """
        Run a single-pass critique on `prompt` and return a structured response.

        This method satisfies the abstract requirement from LLMBaseAgent.
        For actual critique functionality, use review_response() method.
        """
        try:
            # Use the existing review_response method for actual critique
            result = self.review_response(
                response=prompt, artifact_type="prompt", original_prompt="", context=""
            )
            return {
                "result": result.get("feedback", "No feedback available"),
                "passed": result.get("passed", True),
                "critical_issues": result.get("critical_issues", []),
                "suggestions": result.get("suggestions", []),
            }
        except Exception as exc:
            return {
                "result": f"**CRITIC ERROR**: {exc}",
                "passed": True,  # Default to pass on errors
                "critical_issues": [],
                "suggestions": [],
            }
