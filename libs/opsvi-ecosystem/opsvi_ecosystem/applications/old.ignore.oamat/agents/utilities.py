"""
OAMAT Utilities Module

Contains utility functions for JSON processing, fallback creation, and serialization
that support the WorkflowManager's operations.
"""

import json
import logging
from typing import Any

from .models import (
    EnhancedRequestAnalysis,
    EnhancedWorkflowNode,
    EnhancedWorkflowPlan,
    TaskComplexity,
    WorkflowStrategy,
)

logger = logging.getLogger("OAMAT.Utilities")

# JSON Processing Utilities


def extract_structured_info(text_output: str, task_type: str = None) -> dict[str, Any]:
    """Extract structured information from unstructured text output"""
    try:
        # Basic structured extraction for common patterns
        structured_data = {
            "raw_text": text_output,
            "extracted_info": {},
            "task_type": task_type,
        }

        # Look for key-value patterns
        import re

        # Extract JSON-like structures
        json_pattern = r"\{[^{}]*\}"
        json_matches = re.findall(json_pattern, text_output)
        if json_matches:
            structured_data["potential_json"] = json_matches

        # Extract list patterns
        list_pattern = r"\[.*?\]"
        list_matches = re.findall(list_pattern, text_output)
        if list_matches:
            structured_data["potential_lists"] = list_matches

        # Extract quoted strings (potential values)
        quote_pattern = r'"([^"]*)"'
        quoted_values = re.findall(quote_pattern, text_output)
        if quoted_values:
            structured_data["quoted_values"] = quoted_values

        return structured_data

    except Exception as e:
        logger.error(f"Error extracting structured info: {e}")
        return {"error": str(e), "raw_text": text_output, "task_type": task_type}


def clean_json_response(response_text: str) -> str:
    """Clean up common JSON formatting issues from LLM responses"""
    try:
        import re

        # Remove markdown code fences
        cleaned = re.sub(r"```(?:json)?\s*\n?", "", response_text)
        cleaned = re.sub(r"\n?```\s*$", "", cleaned)

        # Remove common prefixes/suffixes and get just the JSON part
        cleaned = re.sub(r"^[^{]*({.*})[^}]*$", r"\1", cleaned, flags=re.DOTALL)

        # FIXED: Handle truncated JSON - find the longest valid JSON
        # Look for opening brace and try to find matching closing brace
        start_idx = cleaned.find("{")
        if start_idx != -1:
            brace_count = 0
            end_idx = start_idx

            for i, char in enumerate(cleaned[start_idx:], start_idx):
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break

            # If we found a complete JSON structure, use it
            if brace_count == 0:
                cleaned = cleaned[start_idx:end_idx]
            else:
                # Truncated JSON - try to close it properly
                cleaned = cleaned[start_idx:] + "}"

        # Fix common JSON issues
        cleaned = re.sub(r",\s*}", "}", cleaned)  # Remove trailing commas
        cleaned = re.sub(r",\s*]", "]", cleaned)  # Remove trailing commas in arrays

        # FIXED: Handle unterminated strings by closing them
        cleaned = re.sub(r'"([^"]*?)$', r'"\1"', cleaned)

        # FIXED: O3 specific issues - fix unquoted property names
        cleaned = re.sub(r"(\w+):\s*", r'"\1": ', cleaned)  # Fix unquoted keys
        cleaned = re.sub(
            r'""(\w+)"": ', r'"\1": ', cleaned
        )  # Fix double quotes on keys

        # FIXED: Handle line 4 column 36 error - often unquoted property names
        lines = cleaned.split("\n")
        for i, line in enumerate(lines):
            # Fix unquoted property names at start of lines
            if ":" in line and not line.strip().startswith('"'):
                # Find the property name and quote it
                match = re.match(r"(\s*)(\w+)(\s*:\s*)", line)
                if match:
                    indent, prop_name, colon_part = match.groups()
                    lines[i] = f'{indent}"{prop_name}"{colon_part}{line[match.end():]}'

        cleaned = "\n".join(lines)

        return cleaned.strip()

    except Exception as e:
        logger.warning(f"Error cleaning JSON response: {e}")
        return response_text


def extract_json_from_response(response_text: str) -> dict[str, Any]:
    """Extract JSON from response text with multiple fallback strategies"""
    try:
        import re

        # Strategy 1: Look for JSON in code blocks
        code_block_pattern = r"```(?:json)?\s*\n?({.*?})\s*\n?```"
        match = re.search(code_block_pattern, response_text, re.DOTALL)
        if match:
            try:
                cleaned = clean_json_response(match.group(1))
                return json.loads(cleaned)
            except json.JSONDecodeError:
                pass

        # Strategy 2: Look for largest JSON object and try to repair it
        json_pattern = r"{[^{}]*(?:{[^{}]*}[^{}]*)*}"
        matches = re.findall(json_pattern, response_text, re.DOTALL)
        for match in sorted(matches, key=len, reverse=True):
            try:
                cleaned = clean_json_response(match)
                return json.loads(cleaned)
            except json.JSONDecodeError:
                continue

        # Strategy 3: Try to extract and repair truncated JSON
        start_idx = response_text.find("{")
        if start_idx != -1:
            # Get everything from first { to end, then try to repair
            partial_json = response_text[start_idx:]

            # Simple repair attempts
            repair_attempts = [
                partial_json + "}",  # Add closing brace
                partial_json + '"}',  # Close string and object
                partial_json + '"}}',  # Close nested structures
                partial_json.rsplit(",", 1)[0] + "}",  # Remove last incomplete field
            ]

            for attempt in repair_attempts:
                try:
                    cleaned = clean_json_response(attempt)
                    parsed = json.loads(cleaned)
                    logger.info("Successfully repaired truncated JSON")
                    return parsed
                except json.JSONDecodeError:
                    continue

        # Strategy 4: Create fallback JSON structure if we can extract key info
        fallback_data = create_fallback_json_from_text(response_text)
        if fallback_data:
            logger.info("Created fallback JSON structure from text analysis")
            return fallback_data

        # Strategy 5: Return None to trigger fallback workflow
        logger.warning("Could not extract or repair JSON from O3 response")
        return None

    except Exception as e:
        logger.error(f"Error extracting JSON from response: {e}")
        return None


def create_fallback_json_from_text(response_text: str) -> dict[str, Any] | None:
    """Create a fallback JSON structure by extracting key information from text"""
    try:
        import re

        # Extract title if present
        title_match = re.search(
            r'title["\s]*:[\s"]*([^"\n,}]+)', response_text, re.IGNORECASE
        )
        title = title_match.group(1).strip('"') if title_match else "Dynamic Workflow"

        # Extract description if present
        desc_match = re.search(
            r'description["\s]*:[\s"]*([^"\n,}]+)', response_text, re.IGNORECASE
        )
        description = (
            desc_match.group(1).strip('"') if desc_match else "Generated workflow"
        )

        # Extract strategy if present
        strategy_match = re.search(
            r'strategy["\s]*:[\s"]*([^"\n,}]+)', response_text, re.IGNORECASE
        )
        strategy = strategy_match.group(1).strip('"') if strategy_match else "adaptive"

        # Create minimal valid workflow structure
        fallback_structure = {
            "title": title,
            "description": description,
            "strategy": strategy,
            "nodes": [
                {
                    "id": "fallback_node",
                    "agent_role": "researcher",
                    "task_type": "research",
                    "parameters": {"research_topic": "user request"},
                    "tools_required": ["brave_web_search"],
                    "next_nodes": [],
                    "parallel_execution": False,
                    "quality_gates": ["source_verification"],
                    "success_criteria": ["relevant_findings"],
                }
            ],
            "expected_outputs": ["research_findings"],
            "success_criteria": ["basic_information_gathered"],
        }

        return fallback_structure

    except Exception as e:
        logger.error(f"Error creating fallback JSON from text: {e}")
        return None


# Fallback Creation Utilities


def create_fallback_analysis(
    user_request: str, context: dict[str, Any] = None
) -> EnhancedRequestAnalysis:
    """Create sophisticated fallback analysis when primary analysis fails."""
    return EnhancedRequestAnalysis(
        primary_intent=user_request[:200],
        secondary_intents=["error recovery", "basic assistance"],
        complexity=TaskComplexity.MODERATE,
        estimated_effort_hours=1.0,
        required_expertise=["research", "planning", "assistance"],
        recommended_agents=["researcher", "reviewer"],
        recommended_tools=["brave_web_search"],
        alternative_approaches=["manual research", "simple analysis"],
        success_criteria=["basic information gathered", "response provided"],
        quality_requirements=["accurate information", "clear communication"],
        deliverable_expectations=["research findings", "structured response"],
        identified_risks=["analysis failure", "unclear requirements"],
        constraints=["technical limitations", "incomplete understanding"],
        dependencies=["web access", "search capabilities"],
        workflow_strategy=WorkflowStrategy.LINEAR,
        optimization_opportunities=["improve clarity", "add context"],
        escalation_conditions=["repeated failures", "complex requirements"],
        confidence_score=0.4,
    )


def create_fallback_workflow(
    workflow_id: str, analysis: EnhancedRequestAnalysis, user_request: str
) -> EnhancedWorkflowPlan:
    """Create sophisticated fallback workflow when primary generation fails."""
    import json

    fallback_node = EnhancedWorkflowNode(
        id="fallback_research",
        agent_role="researcher",
        task_type="comprehensive_research",
        description=f"Research and analyze the user request: {user_request}",
        parameters=json.dumps(
            {"research_topic": user_request, "depth": "comprehensive"}
        ),
        tools_required=["brave_web_search"],
        next_nodes=[],
        quality_gates=["source_verification"],
        success_criteria=["relevant_findings"],
        expected_outputs=["research_findings", "analysis_summary"],
    )

    return EnhancedWorkflowPlan(
        id=workflow_id,
        title="Fallback Research Workflow",
        description="Basic research and analysis workflow for error recovery",
        strategy=WorkflowStrategy.LINEAR,
        complexity=analysis.complexity,
        nodes=[fallback_node],
        expected_outputs=["research_findings"],
        success_criteria=["basic_information_gathered"],
    )


def create_fallback_decision(
    available_options: list[str], error_reason: str
) -> dict[str, Any]:
    """Create intelligent fallback decision when primary decision-making fails."""
    return {
        "selected_next_nodes": available_options[:1] if available_options else [],
        "decision_reasoning": f"Fallback decision due to analysis failure: {error_reason}",
        "confidence_level": 0.3,
        "continue_workflow": bool(available_options),
        "quality_assessment": {
            "current_quality_score": 0.5,
            "expected_outcome_quality": 0.6,
            "quality_concerns": ["decision_making_failure"],
        },
        "required_mutations": [],
        "escalation_needed": True,
        "user_interaction_required": True,
        "risk_factors": ["automated_decision_failure", "potential_suboptimal_path"],
        "optimization_opportunities": ["manual_review", "decision_refinement"],
    }


def create_fallback_workflow_data(
    user_request: str, analysis: EnhancedRequestAnalysis
) -> dict:
    """Create fallback workflow data when structured generation fails."""
    return {
        "title": f"Fallback Workflow for: {user_request[:50]}...",
        "description": "Emergency fallback workflow created due to planning failure",
        "strategy": "linear",
        "complexity": analysis.complexity.value
        if hasattr(analysis.complexity, "value")
        else "moderate",
        "nodes": [
            {
                "id": "emergency_research",
                "agent_role": "researcher",
                "task_type": "basic_research",
                "parameters": {"topic": user_request},
                "tools_required": ["brave_web_search"],
                "next_nodes": [],
            }
        ],
        "expected_outputs": ["basic_research_results"],
        "success_criteria": ["minimal_information_gathered"],
    }


# Serialization Utilities


def serialize_analysis(analysis: EnhancedRequestAnalysis) -> dict[str, Any]:
    """Serialize analysis object for JSON inclusion in prompts"""
    try:
        # Convert Pydantic model to dict
        analysis_dict = analysis.model_dump()

        # Ensure enum values are serialized as strings
        if "complexity" in analysis_dict:
            if hasattr(analysis_dict["complexity"], "value"):
                analysis_dict["complexity"] = analysis_dict["complexity"].value

        return analysis_dict

    except Exception as e:
        logger.error(f"Error serializing analysis: {e}")
        # Return basic dict representation
        return {
            "primary_intent": getattr(analysis, "primary_intent", "unknown"),
            "complexity": str(getattr(analysis, "complexity", "moderate")),
            "recommended_agents": getattr(
                analysis, "recommended_agents", ["researcher"]
            ),
            "serialization_error": str(e),
        }
