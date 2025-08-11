# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Practical Effectiveness Validator","description":"This module provides practical effectiveness testing for rules by generating test scenarios and evaluating rule performance when applied to real-world situations.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Module Documentation","description":"Overview of the module's purpose and functionality.","line_start":2,"line_end":6},{"name":"Imports","description":"Import statements for required libraries and modules.","line_start":8,"line_end":14},{"name":"Logging Configuration","description":"Configuration of logging for the module.","line_start":16,"line_end":20},{"name":"Constants","description":"Definition of constants used in the module.","line_start":22,"line_end":23},{"name":"PracticalValidator Class","description":"Class that provides methods for validating rules against scenarios.","line_start":25,"line_end":122},{"name":"Function Definitions","description":"Various functions for rule analysis, scenario generation, and evaluation.","line_start":124,"line_end":1096}],"key_elements":[{"name":"PracticalValidator","description":"Class for validating rules against real-world scenarios.","line":26},{"name":"validate","description":"Validates a rule by performing practical validation.","line":35},{"name":"analyze_rule","description":"Analyzes rule content for testing-relevant metadata.","line":50},{"name":"generate_scenarios","description":"Generates test scenarios based on rule analysis.","line":63},{"name":"apply_to_scenario","description":"Applies a rule to a test scenario.","line":77},{"name":"generate_report","description":"Generates a report based on validation results.","line":91},{"name":"analyze_rule_for_testing","description":"Extracts metadata from rule content for testing.","line":106},{"name":"generate_test_scenarios","description":"Generates test scenarios based on rule analysis.","line":223},{"name":"apply_rule_to_scenario","description":"Applies a rule to a specific test scenario.","line":404},{"name":"evaluate_content_against_criteria","description":"Evaluates generated content against scenario criteria.","line":525},{"name":"perform_practical_validation","description":"Performs practical validation of a rule.","line":688},{"name":"_generate_effectiveness_assessment","description":"Generates an assessment of rule effectiveness.","line":807},{"name":"_identify_practical_improvements","description":"Identifies potential improvements based on testing results.","line":829},{"name":"generate_practical_test_report","description":"Generates a detailed report of practical testing results.","line":982},{"name":"format_list","description":"Formats a list as markdown bullet points.","line":1092}]}
"""
# FILE_MAP_END

"""
Practical Effectiveness Validator

This module provides practical effectiveness testing for rules by generating test scenarios
and evaluating rule performance when applied to real-world situations.
"""

import os
import json
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import openai

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Base path for rule guidance files - adjust this to the parent directory for proper file access
RULE_GUIDANCE_DIR = "../.cursor/rules/"


class PracticalValidator:
    """
    Validator for practical effectiveness of rules.

    This class provides methods for testing rules against real-world scenarios
    and evaluating their effectiveness.
    """

    @staticmethod
    def validate(
        rule_file_path: str, rule_content: str, num_scenarios: int = 3
    ) -> Dict[str, Any]:
        """
        Perform practical validation of a rule.

        Args:
            rule_file_path: Path to the rule file
            rule_content: Content of the rule
            num_scenarios: Number of test scenarios to generate

        Returns:
            Validation results
        """
        return perform_practical_validation(rule_file_path, rule_content, num_scenarios)

    @staticmethod
    def analyze_rule(rule_content: str) -> Dict[str, Any]:
        """
        Extract testing-relevant metadata from rule content.

        Args:
            rule_content: The content of the rule to analyze

        Returns:
            Dictionary with rule analysis data for test scenario generation
        """
        return analyze_rule_for_testing(rule_content)

    @staticmethod
    def generate_scenarios(
        rule_analysis: Dict[str, Any], num_scenarios: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Generate test scenarios for a rule.

        Args:
            rule_analysis: Analysis data for the rule
            num_scenarios: Number of scenarios to generate

        Returns:
            List of test scenarios
        """
        return generate_test_scenarios(rule_analysis, num_scenarios)

    @staticmethod
    def apply_to_scenario(
        rule_content: str, scenario: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply a rule to a test scenario.

        Args:
            rule_content: Content of the rule
            scenario: Test scenario

        Returns:
            Results of applying the rule
        """
        return apply_rule_to_scenario(rule_content, scenario)

    @staticmethod
    def generate_report(
        rule_id: str, rule_name: str, validation_results: Dict[str, Any]
    ) -> str:
        """
        Generate a practical test report.

        Args:
            rule_id: ID of the rule
            rule_name: Name of the rule
            validation_results: Validation results

        Returns:
            Formatted test report
        """
        return generate_practical_test_report(rule_id, rule_name, validation_results)


def analyze_rule_for_testing(rule_content: str) -> Dict[str, Any]:
    """
    Extract testing-relevant metadata from rule content.

    Args:
        rule_content: The content of the rule to analyze

    Returns:
        Dictionary with rule analysis data for test scenario generation
    """
    logger.info("Analyzing rule content for test scenario generation")

    # Parse basic rule information
    rule_id = ""
    rule_name = ""

    # Extract rule ID and name from frontmatter or title
    id_match = re.search(r'id:\s*(\d+)[^"\n]*', rule_content)
    if id_match:
        rule_id = id_match.group(1)

    name_match = re.search(r'name:\s*"?([^"\n]+)"?', rule_content) or re.search(
        r"# (.+)", rule_content
    )
    if name_match:
        rule_name = name_match.group(1)

    # Extract applicable file types from globs
    globs = []
    globs_match = re.search(r"globs:\s*\[(.*?)\]", rule_content, re.DOTALL)
    if globs_match:
        globs_raw = globs_match.group(1)
        # Extract individual glob patterns
        for glob in re.finditer(r'"([^"]+)"', globs_raw):
            globs.append(glob.group(1))
        if not globs and "*" in globs_raw:
            globs = ["**/*"]

    # Get API key from environment
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("OpenAI API key not found in environment variables")
        return {
            "rule_id": rule_id,
            "rule_name": rule_name,
            "error": "OpenAI API key not found",
        }

    client = openai.OpenAI(api_key=api_key)

    # Create prompt for rule analysis
    prompt = f"""
    # Rule Analysis Task
    
    ## Rule Content
    ```
    {rule_content}
    ```
    
    ## Analysis Instructions
    Analyze this rule and extract the following information needed for test scenario generation:
    
    1. Primary purpose of the rule
    2. Applicable domains (e.g., web development, system programming, data science)
    3. File types and technologies this rule applies to
    4. Key requirements the rule enforces
    5. Potential user requests that would trigger this rule
    6. Edge cases and boundary conditions this rule should address
    
    Provide your analysis in the following JSON format:
    ```json
    {{
        "primary_purpose": "Brief description of the rule's main purpose",
        "applicable_domains": ["domain1", "domain2", ...],
        "applicable_technologies": ["tech1", "tech2", ...],
        "key_requirements": ["requirement1", "requirement2", ...],
        "potential_user_requests": ["request1", "request2", ...],
        "edge_cases": ["edge case1", "edge case2", ...]
    }}
    ```
    """

    try:
        # Call the OpenAI API for analysis
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert rule analyzer that extracts structured metadata from rule definitions.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        # Extract and parse the response
        analysis_text = response.choices[0].message.content
        analysis = json.loads(analysis_text)

        # Combine extracted data with parsed analysis
        analysis.update({"rule_id": rule_id, "rule_name": rule_name, "globs": globs})

        logger.info(f"Successfully analyzed rule: {rule_name}")
        return analysis

    except Exception as e:
        logger.error(f"Error analyzing rule: {str(e)}")
        return {
            "rule_id": rule_id,
            "rule_name": rule_name,
            "globs": globs,
            "error": f"Analysis error: {str(e)}",
        }


def generate_test_scenarios(
    rule_analysis: Dict[str, Any], num_scenarios: int = 3
) -> List[Dict[str, Any]]:
    """
    Generate domain-specific test scenarios based on rule analysis.

    Args:
        rule_analysis: Dictionary with rule analysis data
        num_scenarios: Number of scenarios to generate

    Returns:
        List of test scenario dictionaries
    """
    logger.info(
        f"Generating {num_scenarios} test scenarios for rule {rule_analysis.get('rule_name', 'Unknown')}"
    )

    # Get API key from environment
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("OpenAI API key not found in environment variables")
        return [{"error": "OpenAI API key not found"}]

    client = openai.OpenAI(api_key=api_key)

    # Load rule 010 for cursor rules generation standards
    cursor_rules_generation_path = Path(
        RULE_GUIDANCE_DIR + "012-standalone-rules-generation.mdc"
    )
    cursor_rules_generation_content = None
    if cursor_rules_generation_path.exists():
        try:
            with open(cursor_rules_generation_path, "r", encoding="utf-8") as f:
                cursor_rules_generation_content = f.read()
            logger.info(
                f"Successfully loaded rule 012 for standalone rules generation standards"
            )
        except Exception as e:
            logger.warning(f"Could not load rule 012: {str(e)}")

    # Load rule 015 for AI interpretability standards
    ai_interpretability_path = Path(
        RULE_GUIDANCE_DIR + "015-rule-ai-interpretability.mdc"
    )
    ai_interpretability_content = None
    if ai_interpretability_path.exists():
        try:
            with open(ai_interpretability_path, "r", encoding="utf-8") as f:
                ai_interpretability_content = f.read()
            logger.info(
                f"Successfully loaded rule 015 for AI interpretability standards"
            )
        except Exception as e:
            logger.warning(f"Could not load rule 015: {str(e)}")

    # Create scenario generation prompt
    prompt = f"""
    # Test Scenario Generation Task
    
    ## Context
    You are designing test scenarios to evaluate how effectively an AI assistant can interpret and apply a rule. 
    The rule will be used by an AI integrated in an IDE to guide its behavior when assisting developers.
    
    When designing test scenarios, specifically evaluate how well the rule can be algorithmically interpreted by the AI.
    Test whether the rule provides clear decision criteria that an AI can follow consistently across different situations.
    Consider whether the rule enables the AI to explain its decisions clearly to developers.
    
    ## Rule Analysis
    {json.dumps(rule_analysis, indent=2)}
    """

    # Add rule structure standards if available
    if cursor_rules_generation_content:
        prompt += f"""
    ## Rule Structure Standards
    The following rule defines the required structure and format for Cursor rules:
    ```
    {cursor_rules_generation_content}
    ```
    
    Consider these structural standards when designing scenarios to test rule effectiveness.
    """

    # Add AI interpretability standards if available
    if ai_interpretability_content:
        prompt += f"""
    ## AI Interpretability Standards
    The following rule defines standards for making rules interpretable by AI systems:
    ```
    {ai_interpretability_content}
    ```
    
    Include scenarios that specifically test how well the rule follows these AI interpretability standards.
    """

    # Continue with the rest of the prompt
    prompt += f"""
    ## Generation Instructions
    Create {num_scenarios} diverse test scenarios to evaluate the effectiveness of this rule when applied by an AI assistant.
    
    For each scenario, provide:
    
    1. A realistic context where this rule would apply
    2. A specific user request that would trigger the AI to apply this rule
    3. Expected behaviors or content that should appear in the AI's response
    4. Clear, measurable success criteria for evaluating if the AI correctly applied the rule
    
    Include normal cases, edge cases, and scenarios testing different aspects of the rule.
    Your scenarios must be specific to the domains: {", ".join(rule_analysis.get("applicable_domains", ["software development"]))}
    
    ## Advanced Requirements
    - Each scenario should focus on testing a different aspect of the rule
    - Include at least one scenario that tests how the AI interprets edge cases or ambiguities in the rule
    - Success criteria must be objectively measurable and focused on the AI's ability to follow the rule
    - Make scenarios as realistic as possible with domain-specific details
    - Test whether the AI can determine what is required versus suggested by the rule
    
    Provide scenarios in the following JSON format:
    ```json
    [
        {{
            "name": "Descriptive name of scenario",
            "context": {{
                "domain": "Specific domain",
                "file_type": "Specific file type",
                "additional_context_field1": "value1",
                "additional_context_field2": "value2"
            }},
            "user_request": "Detailed description of what the user is asking for",
            "expected_behaviors": [
                "Specific behavior 1 expected in the AI's output",
                "Specific behavior 2 expected in the AI's output"
            ],
            "success_criteria": [
                "Measurable criterion 1 to evaluate AI rule application",
                "Measurable criterion 2 to evaluate AI rule application"
            ]
        }},
        // Additional scenarios...
    ]
    ```
    """

    try:
        # Call the OpenAI API for scenario generation
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert test scenario designer specialized in creating realistic, domain-specific test cases for evaluating AI systems. You have expertise across all software development domains and can create scenarios that effectively test how well an AI can interpret and apply rules.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            response_format={"type": "json_object"},
        )

        # Extract and parse the response
        scenarios_text = response.choices[0].message.content
        scenarios = json.loads(scenarios_text)

        if not isinstance(scenarios, list):
            # Handle case where response isn't a list
            logger.warning(
                "Received non-list response for scenarios, attempting to extract"
            )
            if isinstance(scenarios, dict) and "scenarios" in scenarios:
                scenarios = scenarios["scenarios"]
            else:
                logger.error("Could not extract scenarios from response")
                return [{"error": "Invalid scenario format received"}]

        logger.info(f"Successfully generated {len(scenarios)} test scenarios")
        return scenarios

    except Exception as e:
        logger.error(f"Error generating test scenarios: {str(e)}")
        return [{"error": f"Scenario generation error: {str(e)}"}]


def apply_rule_to_scenario(
    rule_content: str, scenario: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Apply a rule to a specific test scenario and generate content.

    Args:
        rule_content: Content of the rule
        scenario: Test scenario dictionary

    Returns:
        Dictionary with generated content and metadata
    """
    scenario_name = scenario.get("name", "Unknown scenario")
    logger.info(f"Applying rule to scenario: {scenario_name}")

    # Get API key from environment
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("OpenAI API key not found in environment variables")
        return {"error": "OpenAI API key not found"}

    client = openai.OpenAI(api_key=api_key)

    # Load rule 015 for AI interpretability standards
    ai_interpretability_path = Path(
        RULE_GUIDANCE_DIR + "015-rule-ai-interpretability.mdc"
    )
    ai_interpretability_content = None
    if ai_interpretability_path.exists():
        try:
            with open(ai_interpretability_path, "r", encoding="utf-8") as f:
                ai_interpretability_content = f.read()
            logger.info(
                f"Successfully loaded rule 015 for AI interpretability standards"
            )
        except Exception as e:
            logger.warning(f"Could not load rule 015: {str(e)}")

    # Create application prompt
    prompt = f"""
    # Rule Application Task
    
    ## Context
    You are an AI assistant integrated into an IDE. You follow rules precisely when generating 
    content for developers. The following rule guides your behavior when responding to user requests.
    Your task is to simulate how an AI would apply this rule to the specific user request.
    
    ## Rule
    ```
    {rule_content}
    ```
    
    ## User Request
    {scenario.get('user_request', 'Generate content according to the rule')}
    
    ## Scenario Context
    {json.dumps(scenario.get('context', {}), indent=2)}
    """

    # Add AI interpretability standards if available
    if ai_interpretability_content:
        prompt += f"""
    ## AI Interpretability Standards
    When applying the rule, follow these AI interpretability guidelines to ensure clear rule interpretation:
    ```
    {ai_interpretability_content}
    ```
    
    Apply these standards to demonstrate how an AI would interpret and implement the rule.
    """

    prompt += f"""
    ## Task
    Apply this rule precisely when responding to the user request as if you were the AI assistant. 
    Generate appropriate content that follows the rule's requirements, especially focusing on any 
    explicit MUST/SHOULD/NEVER directives in the rule.
    
    ## Expected Behaviors
    As an AI assistant, your response should demonstrate these behaviors:
    {json.dumps(scenario.get('expected_behaviors', []), indent=2)}
    
    ## Response Format
    Provide your response exactly as an AI assistant would respond to this request,
    creating code or content that precisely follows the rule's requirements.
    Your response should demonstrate how well the AI can interpret and apply this rule.
    """

    try:
        # Call the OpenAI API to apply the rule
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are simulating how an AI assistant integrated into an IDE would follow a specific rule when responding to a user request. Your goal is to demonstrate how the AI would interpret and apply the rule to generate a response.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
            max_tokens=2000,
        )

        # Extract the generated content
        generated_content = response.choices[0].message.content

        logger.info(f"Successfully generated content for scenario: {scenario_name}")
        return {
            "scenario_name": scenario_name,
            "generated_content": generated_content,
            "timestamp": None,  # Will be filled in by calling function
        }

    except Exception as e:
        logger.error(f"Error generating content for scenario: {str(e)}")
        return {
            "scenario_name": scenario_name,
            "error": f"Content generation error: {str(e)}",
        }


def evaluate_content_against_criteria(
    generated_content: str, scenario: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evaluate generated content against scenario success criteria.

    Args:
        generated_content: Content generated by applying the rule
        scenario: Test scenario dictionary with success criteria

    Returns:
        Dictionary with evaluation results
    """
    scenario_name = scenario.get("name", "Unknown scenario")
    logger.info(f"Evaluating content for scenario: {scenario_name}")

    # Get API key from environment
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("OpenAI API key not found in environment variables")
        return {"error": "OpenAI API key not found"}

    client = openai.OpenAI(api_key=api_key)

    # Load rule 015 for AI interpretability standards
    ai_interpretability_path = Path(
        RULE_GUIDANCE_DIR + "015-rule-ai-interpretability.mdc"
    )
    ai_interpretability_content = None
    if ai_interpretability_path.exists():
        try:
            with open(ai_interpretability_path, "r", encoding="utf-8") as f:
                ai_interpretability_content = f.read()
            logger.info(
                f"Successfully loaded rule 015 for AI interpretability standards"
            )
        except Exception as e:
            logger.warning(f"Could not load rule 015: {str(e)}")

    # Get success criteria and expected behaviors
    success_criteria = scenario.get("success_criteria", [])
    expected_behaviors = scenario.get("expected_behaviors", [])

    if not success_criteria:
        logger.warning(f"No success criteria provided for scenario: {scenario_name}")
        success_criteria = ["Content demonstrates expected behaviors"]

    # Create evaluation prompt
    prompt = f"""
    # Content Evaluation Task
    
    ## Context
    You are evaluating how effectively an AI assistant has applied a rule to generate content.
    Your goal is to determine whether the AI correctly interpreted the rule and followed its requirements,
    especially any explicit MUST/SHOULD/NEVER directives.
    
    ## Content to Evaluate
    ```
    {generated_content}
    ```
    
    ## Expected Behaviors
    {json.dumps(expected_behaviors, indent=2)}
    
    ## Success Criteria
    {json.dumps(success_criteria, indent=2)}
    """

    # Add AI interpretability standards if available
    if ai_interpretability_content:
        prompt += f"""
    ## AI Interpretability Standards
    When evaluating how well the AI applied the rule, use these AI interpretability standards:
    ```
    {ai_interpretability_content}
    ```
    
    Consider whether the AI correctly followed explicit directives and properly interpreted the rule according to these standards.
    """

    prompt += f"""
    ## Evaluation Instructions
    Evaluate the content against each success criterion and expected behavior.
    For each criterion/behavior, determine if it's fully met, partially met, or not met.
    
    Focus specifically on evaluating:
    1. Whether the AI correctly identified and followed explicit requirements in the rule
    2. How consistently the AI applied the rule's guidance
    3. Whether the AI's response would be helpful to a developer
    4. How well the AI was able to interpret and apply the rule
    
    Provide specific evidence from the content to support your evaluation.
    Be objective and thorough in your assessment.
    
    ## Response Format
    Respond with a JSON object in the following format:
    ```json
    {{
        "overall_score": 0-10 score representing how effectively the AI interpreted and applied the rule,
        "criteria_evaluations": [
            {{
                "criterion": "Success criterion text",
                "status": "fully_met|partially_met|not_met",
                "evidence": "Evidence from content supporting this evaluation",
                "score": 0-10 score for this specific criterion
            }},
            // Additional criteria evaluations...
        ],
        "behavior_evaluations": [
            {{
                "behavior": "Expected behavior text",
                "status": "fully_met|partially_met|not_met",
                "evidence": "Evidence from content supporting this evaluation"
            }},
            // Additional behavior evaluations...
        ],
        "strengths": [
            "Specific strength in how the AI applied the rule",
            "Another specific strength"
        ],
        "weaknesses": [
            "Specific weakness in how the AI interpreted or applied the rule",
            "Another specific weakness"
        ],
        "rule_effectiveness_assessment": "Overall assessment of how effectively the rule guided the AI's response in this scenario",
        "rule_improvement_suggestions": [
            "Specific suggestion for improving the rule to make it more effective for AI interpretation",
            "Another specific rule improvement suggestion"
        ]
    }}
    ```
    """

    try:
        # Call the OpenAI API for evaluation
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert evaluator specialized in assessing how effectively AI systems interpret and apply rules. You provide objective, evidence-based assessments of both the AI's performance and the quality of the rules themselves.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        # Extract and parse the evaluation
        evaluation_text = response.choices[0].message.content
        evaluation = json.loads(evaluation_text)

        # Add scenario name for reference
        evaluation["scenario_name"] = scenario_name

        logger.info(f"Successfully evaluated content for scenario: {scenario_name}")
        return evaluation

    except Exception as e:
        logger.error(f"Error evaluating content: {str(e)}")
        return {"scenario_name": scenario_name, "error": f"Evaluation error: {str(e)}"}


def perform_practical_validation(
    rule_file_path: str, rule_content: str, num_scenarios: int = 3
) -> Dict[str, Any]:
    """
    Perform practical validation of a rule by generating test scenarios, applying the rule,
    and evaluating the results.

    Args:
        rule_file_path: Path to the rule file
        rule_content: Content of the rule
        num_scenarios: Number of test scenarios to generate

    Returns:
        Dictionary with validation results
    """
    logger.info(f"Starting practical validation for rule: {rule_file_path}")

    # Prepare results structure
    validation_results = {
        "rule_file_path": rule_file_path,
        "status": "in_progress",
        "practical_score": 0.0,
        "rule_analysis": None,
        "test_scenarios": [],
        "scenario_results": [],
        "effectiveness_assessment": "",
        "identified_improvements": [],
    }

    try:
        # Step 1: Analyze the rule for testing
        rule_analysis = analyze_rule_for_testing(rule_content)
        validation_results["rule_analysis"] = rule_analysis

        if "error" in rule_analysis:
            validation_results["status"] = "error"
            validation_results["error"] = rule_analysis["error"]
            return validation_results

        # Step 2: Generate test scenarios
        test_scenarios = generate_test_scenarios(rule_analysis, num_scenarios)
        validation_results["test_scenarios"] = test_scenarios

        if test_scenarios and "error" in test_scenarios[0]:
            validation_results["status"] = "error"
            validation_results["error"] = test_scenarios[0]["error"]
            return validation_results

        # Step 3: Apply rule to each scenario and evaluate
        scenario_results = []
        total_score = 0.0

        for scenario in test_scenarios:
            # Apply rule to scenario
            generated_content = apply_rule_to_scenario(rule_content, scenario)

            if "error" in generated_content:
                scenario_results.append(
                    {"scenario": scenario, "error": generated_content["error"]}
                )
                continue

            # Evaluate content against criteria
            evaluation = evaluate_content_against_criteria(
                generated_content["generated_content"], scenario
            )

            if "error" in evaluation:
                scenario_results.append(
                    {
                        "scenario": scenario,
                        "generated_content": generated_content["generated_content"],
                        "error": evaluation["error"],
                    }
                )
                continue

            # Store results
            scenario_results.append(
                {
                    "scenario": scenario,
                    "generated_content": generated_content["generated_content"],
                    "evaluation": evaluation,
                }
            )

            # Add to total score
            if "overall_score" in evaluation:
                total_score += float(evaluation["overall_score"])

        validation_results["scenario_results"] = scenario_results

        # Calculate average practical score
        if scenario_results:
            validation_results["practical_score"] = total_score / len(scenario_results)

        # Step 4: Generate overall effectiveness assessment
        validation_results[
            "effectiveness_assessment"
        ] = _generate_effectiveness_assessment(validation_results)

        # Step 5: Identify potential improvements based on practical testing
        validation_results[
            "identified_improvements"
        ] = _identify_practical_improvements(validation_results)

        validation_results["status"] = "completed"
        logger.info(
            f"Practical validation completed with score: {validation_results.get('practical_score', 0.0)}"
        )

    except Exception as e:
        logger.error(f"Error during practical validation: {str(e)}")
        validation_results["status"] = "error"
        validation_results["error"] = f"Exception during validation: {str(e)}"

    return validation_results


def _generate_effectiveness_assessment(validation_results: Dict[str, Any]) -> str:
    """
    Generate an overall assessment of rule effectiveness based on practical testing.

    Args:
        validation_results: Dictionary with validation results

    Returns:
        String with effectiveness assessment
    """
    practical_score = validation_results.get("practical_score", 0.0)

    if practical_score >= 9.0:
        return "The rule demonstrates excellent effectiveness in practical application across all tested scenarios."
    elif practical_score >= 8.0:
        return "The rule demonstrates good effectiveness in practical application but has minor improvement opportunities."
    elif practical_score >= 6.0:
        return "The rule shows moderate effectiveness in practical application with several areas for improvement."
    else:
        return "The rule has limited effectiveness in practical application and needs significant improvement."


def _identify_practical_improvements(validation_results: Dict[str, Any]) -> List[str]:
    """
    Identify potential improvements based on practical testing results.

    Args:
        validation_results: Dictionary with validation results

    Returns:
        List of improvement suggestions
    """
    improvements = []
    scenario_results = validation_results.get("scenario_results", [])

    # Collect weaknesses from all scenario evaluations
    all_weaknesses = []
    improvement_suggestions = []

    for result in scenario_results:
        if "evaluation" in result and "weaknesses" in result["evaluation"]:
            all_weaknesses.extend(result["evaluation"]["weaknesses"])

        # Also collect direct rule improvement suggestions if available
        if (
            "evaluation" in result
            and "rule_improvement_suggestions" in result["evaluation"]
        ):
            improvement_suggestions.extend(
                result["evaluation"]["rule_improvement_suggestions"]
            )

    # If we already have specific improvement suggestions from evaluations, prioritize those
    if improvement_suggestions:
        return improvement_suggestions

    # Load rule 015 for AI interpretability standards
    ai_interpretability_path = Path(
        RULE_GUIDANCE_DIR + "015-rule-ai-interpretability.mdc"
    )
    ai_interpretability_content = None
    if ai_interpretability_path.exists():
        try:
            with open(ai_interpretability_path, "r", encoding="utf-8") as f:
                ai_interpretability_content = f.read()
            logger.info(
                f"Successfully loaded rule 015 for AI interpretability standards"
            )
        except Exception as e:
            logger.warning(f"Could not load rule 015: {str(e)}")

    # If no specific weaknesses found, return generic improvements
    if not all_weaknesses:
        return [
            "Add explicit MUST/SHOULD/NEVER directives to all requirements for clearer AI interpretation",
            "Include specific decision criteria that an AI can follow algorithmically",
            "Enhance examples to demonstrate how an AI should apply the rule in different contexts",
            "Add explicit guidance on how the AI should explain its application of the rule to users",
        ]

    # Get API key from environment
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("OpenAI API key not found in environment variables")
        return ["Could not generate improvements due to missing API key"]

    client = openai.OpenAI(api_key=api_key)

    # Create improvement suggestions prompt
    prompt = f"""
    # Rule Improvement Suggestions Task
    
    ## Context
    You are analyzing weaknesses identified during practical testing of a rule for an AI assistant.
    This rule guides the AI's behavior when assisting developers in an IDE.
    
    A high-quality rule for AI consumption should:
    1. Use explicit directive markers (MUST, SHOULD, NEVER) for easy identification of requirements
    2. Provide algorithmic clarity so an AI can follow it precisely
    3. Enable the AI to explain its decisions to developers
    4. Apply consistently across different situations
    
    ## Practical Testing Weaknesses
    The following weaknesses were observed when the rule was applied by an AI in realistic scenarios:
    {json.dumps(all_weaknesses, indent=2)}
    """

    # Add AI interpretability standards if available
    if ai_interpretability_content:
        prompt += f"""
    ## AI Interpretability Standards
    Apply these AI interpretability standards when generating improvement suggestions:
    ```
    {ai_interpretability_content}
    ```
    
    Your suggestions should align with these standards for optimal AI interpretability.
    """

    prompt += f"""
    ## Task
    Based on these weaknesses, suggest specific improvements that would make the rule more effective 
    for AI interpretation and application in real-world development scenarios.
    
    Generate 3-7 concrete, actionable improvement suggestions that address the identified weaknesses.
    Each suggestion should:
    1. Focus on making the rule more algorithmically processable by the AI
    2. Be specific about what should be added, modified, or clarified
    3. Explain how it would improve the AI's ability to interpret and apply the rule
    
    Provide your suggestions as a JSON array of strings, with each string representing a specific improvement.
    """

    try:
        # Call the OpenAI API for improvement suggestions
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert rule designer specialized in creating rules that AI systems can effectively interpret and apply. You focus on making rules algorithmic, explicit, and consistent for AI consumption.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
            response_format={"type": "json_object"},
        )

        # Extract and parse the suggestions
        suggestions_text = response.choices[0].message.content
        suggestions = json.loads(suggestions_text)

        if isinstance(suggestions, list):
            improvements = suggestions
        elif isinstance(suggestions, dict) and "suggestions" in suggestions:
            improvements = suggestions["suggestions"]
        else:
            logger.warning("Received unexpected format for improvement suggestions")
            improvements = [
                f"Improve AI interpretability for issue: {weakness}"
                for weakness in all_weaknesses[:5]
            ]

        logger.info(f"Generated {len(improvements)} practical improvement suggestions")

    except Exception as e:
        logger.error(f"Error generating improvement suggestions: {str(e)}")
        improvements = [
            f"Enhance AI interpretability for: {weakness}"
            for weakness in all_weaknesses[:5]
        ]

    return improvements


def generate_practical_test_report(
    rule_id: str, rule_name: str, validation_results: Dict[str, Any]
) -> str:
    """
    Generate a detailed report of practical testing results.

    Args:
        rule_id: ID of the rule
        rule_name: Name of the rule
        validation_results: Dictionary with validation results

    Returns:
        Markdown formatted report content
    """
    practical_score = validation_results.get("practical_score", 0.0)
    scenario_results = validation_results.get("scenario_results", [])
    improvements = validation_results.get("identified_improvements", [])

    # Format the report
    report = f"""# Rule {rule_id}: {rule_name} - Practical Testing Report

## Overview

This report details the practical effectiveness testing for Rule {rule_id}: {rule_name}. The testing evaluates how effectively an AI assistant can interpret and apply this rule when generating content for developers in an IDE.

## AI Interpretability Score

**Overall Score**: {practical_score:.1f}/10

This score represents how effectively an AI can interpret and apply this rule across different scenarios. A higher score indicates the rule provides clear, algorithmic guidance that an AI can consistently follow.

## Test Scenarios

The rule was tested in {len(scenario_results)} practical scenarios that simulate real-world situations where an AI would need to apply this rule:

"""

    # Add scenario details
    for i, result in enumerate(scenario_results, 1):
        scenario = result.get("scenario", {})
        evaluation = result.get("evaluation", {})

        report += f"""### Scenario {i}: {scenario.get('name', 'Unnamed Scenario')}

**Domain**: {scenario.get('context', {}).get('domain', 'Unknown')}
**User Request**: {scenario.get('user_request', 'No request specified')}

#### Evaluation Results

**Score**: {evaluation.get('overall_score', 'N/A')}/10
**Assessment**: {evaluation.get('rule_effectiveness_assessment', 'No assessment available')}

##### Strengths in AI Rule Application
{format_list(evaluation.get('strengths', []))}

##### Weaknesses in AI Rule Application
{format_list(evaluation.get('weaknesses', []))}

##### Criteria Evaluation
| Success Criterion | Status | Evidence |
|-------------------|--------|----------|
"""

        # Add criteria evaluations
        for criterion_eval in evaluation.get("criteria_evaluations", []):
            criterion = criterion_eval.get("criterion", "Unknown")
            status = criterion_eval.get("status", "not_evaluated")
            evidence = criterion_eval.get("evidence", "No evidence provided")

            report += f"| {criterion} | {status} | {evidence} |\n"

        # Add rule improvement suggestions if available
        if (
            "rule_improvement_suggestions" in evaluation
            and evaluation["rule_improvement_suggestions"]
        ):
            report += f"""
##### Rule Improvement Suggestions from This Scenario
{format_list(evaluation.get('rule_improvement_suggestions', []))}
"""

        report += "\n\n"

    # Add improvement suggestions
    report += f"""## AI Interpretability Improvement Recommendations

Based on practical testing results, the following improvements would enhance the rule's effectiveness for AI interpretation and application:

{format_list(improvements)}

## Key Findings

### AI Interpretation Challenges
The practical testing revealed specific areas where the AI had difficulty interpreting or applying the rule:

- {'No significant interpretation challenges identified.' if practical_score >= 9.0 else 'The rule contains ambiguities or lacks explicit directives that made consistent AI interpretation difficult.'}
- {'The rule provides clear algorithmic guidance that an AI can follow.' if practical_score >= 8.5 else 'The rule could benefit from more explicit MUST/SHOULD/NEVER statements to help the AI identify requirements.'}
- {'Examples effectively demonstrate how to apply the rule.' if practical_score >= 8.0 else 'Examples could be improved to better demonstrate rule application.'}

### Rule Effectiveness for AI Consumption
{validation_results.get('effectiveness_assessment', 'No assessment available')}

## Conclusion

This practical effectiveness testing demonstrates how an AI actually applies this rule in realistic scenarios, providing empirical evidence of the rule's quality beyond theoretical evaluation. The improvements recommended in this report would enhance the rule's algorithmic clarity and consistency, making it more effective for AI consumption.
"""

    return report


def format_list(items: List[str]) -> str:
    """Format a list as markdown bullet points."""
    if not items:
        return "- No items identified"
    return "\n".join(f"- {item}" for item in items)
