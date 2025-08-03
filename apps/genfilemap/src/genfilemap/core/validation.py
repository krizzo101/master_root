"""
Validation module for file map generation.

This module provides functionality for validating generated file maps
using AI assistance to ensure map accuracy and consistency.
"""

import json
import os
from typing import Dict, Any, List, Optional

from genfilemap.logging_utils import debug, info, warning, error
from genfilemap.config import get_config_value


def create_validation_prompt(file_path: str, content: str, file_map_json: str) -> str:
    """
    Creates a relaxed prompt for AI validation of file maps.
    This version focuses on major structural issues rather than minor details.

    Args:
        file_path: Path to the file
        content: Content of the file
        file_map_json: Generated file map JSON

    Returns:
        str: Formatted prompt for relaxed validation
    """
    file_ext = os.path.splitext(file_path)[1]
    file_name = os.path.basename(file_path)

    prompt = f"""# Role and Objective
You are a file map validation expert with a focus on practical usability. Your mission is to validate file maps for major structural accuracy while being lenient on minor details.

# Validation Task
Validate the provided file map against the source file content with a focus on major issues only.

## File Information
- **File**: {file_path}
- **Name**: {file_name}
- **Extension**: {file_ext}

# Relaxed Validation Approach
Focus ONLY on major issues that would significantly impact navigation or understanding:

## Critical Issues Only (Mark as Invalid)
- **Major Missing Elements**: Missing primary classes, main functions, or core imports
- **Severe Line Number Errors**: Line numbers that are completely wrong (off by more than 10 lines)
- **JSON Structure Problems**: Invalid JSON syntax or completely missing required fields
- **Major Misrepresentation**: Completely incorrect function signatures or class hierarchies

## Acceptable Minor Issues (Still Mark as Valid)
- Missing minor helper functions or utility methods
- Line numbers that are slightly off (within 5-10 lines)
- Minor import omissions (especially internal/relative imports)
- Small constants or variables not captured
- Minor description inaccuracies
- Slightly imprecise section boundaries
- Missing some method parameters or return types

# Lenient Standards
- **Missing some imports**: ACCEPTABLE - Focus on major external dependencies only
- **Minor constant omissions**: ACCEPTABLE - Only major configuration constants matter
- **Approximate line numbers**: ACCEPTABLE - Within reasonable range is fine
- **Missing minor functions**: ACCEPTABLE - Focus on main functionality
- **Imprecise signatures**: ACCEPTABLE - As long as function name and purpose are clear

# Source File Content
```
{content}
```

# File Map to Validate
```json
{file_map_json}
```

# Output Requirements

Provide your validation results in this EXACT JSON format:

```json
{{
  "is_valid": true/false,
  "summary": "Brief summary focusing on major issues only",
  "confidence_score": 85,
  "issues": [
    {{
      "type": "major_missing|critical_error|severe_inaccuracy",
      "description": "Description of major issue only",
      "location": "Location of issue",
      "severity": "high|critical",
      "line_reference": 42,
      "suggested_fix": "Fix for major issue"
    }}
  ],
  "validation_details": {{
    "major_elements_checked": 10,
    "critical_issues_found": 0
  }},
  "recommendations": [
    "Only major recommendations for significant improvements"
  ]
}}
```

# Relaxed Validation Instructions
- Be lenient and focus on major structural accuracy only
- Mark as valid (true) if the file map captures the main structure and major elements
- Mark as invalid (false) ONLY for major structural problems or completely missing core elements
- Ignore minor omissions, slight line number discrepancies, and small details
- A file map is valid if it provides reasonable navigation and understanding of the main file structure

The goal is practical usability, not perfect precision. Minor issues are acceptable as long as the overall structure is captured.

Think through the validation focusing on major elements only, then provide ONLY the JSON validation result."""

    return prompt


async def validate_file_map(
    file_path: str,
    content: str,
    file_map_json: str,
    api_client,
    model: str,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Validates a file map against the file content using AI.

    Args:
        file_path: Path to the file
        content: Content of the file
        file_map_json: Generated file map JSON
        api_client: API client for making requests
        model: Model to use for validation
        config: Configuration dictionary

    Returns:
        Dict[str, Any]: Validation results
    """
    debug(f"Validating file map for {file_path}")

    # Use validation model from config if specified, otherwise fall back to the provided model
    validation_model = model
    if config and get_config_value(config, "validation.model"):
        validation_model = get_config_value(config, "validation.model")

    # Determine if strict validation should be used
    strict_validation = False
    if config:
        strict_validation = get_config_value(config, "validation.strict", False)

    # Create the validation prompt
    prompt = create_validation_prompt(file_path, content, file_map_json)

    try:
        # Call the AI validator
        debug(f"Calling validation model: {validation_model}")

        # Split the prompt into system and user messages
        system_message = "You are an expert code analyzer tasked with validating file maps for accuracy."
        user_message = prompt

        validation_response = await api_client.generate_completion(
            system_message=system_message,
            user_message=user_message,
            model=validation_model,
            max_tokens=2000,
        )

        # Parse the validation results
        try:
            # Look for JSON in the response
            json_start = validation_response.find("{")
            json_end = validation_response.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_content = validation_response[json_start:json_end]
                validation_results = json.loads(json_content)

                # Add additional validation metadata
                validation_results["file"] = file_path
                validation_results["model_used"] = validation_model
                validation_results["strict_mode"] = strict_validation

                if not validation_results.get("issues"):
                    validation_results["issues"] = []

                # Mark as valid if there are no issues
                if not validation_results.get(
                    "is_valid"
                ) and not validation_results.get("issues"):
                    validation_results["is_valid"] = True

                if not validation_results.get("summary"):
                    if validation_results.get("is_valid", False):
                        validation_results["summary"] = (
                            "File map validated successfully with no issues found."
                        )
                    else:
                        validation_results["summary"] = (
                            f"File map validation found {len(validation_results.get('issues', []))} issues."
                        )

                debug(f"Validation results: {validation_results['summary']}")
                return validation_results
            else:
                error(f"Failed to parse validation response: {validation_response}")
                return {
                    "is_valid": False,
                    "file": file_path,
                    "summary": "Failed to parse validation response",
                    "issues": [
                        {
                            "type": "validation_error",
                            "description": "Could not parse validation response",
                            "severity": "high",
                        }
                    ],
                }
        except json.JSONDecodeError as e:
            error(f"JSON parse error in validation response: {str(e)}")
            return {
                "is_valid": False,
                "file": file_path,
                "summary": "JSON parse error in validation response",
                "issues": [
                    {
                        "type": "validation_error",
                        "description": f"JSON parse error: {str(e)}",
                        "severity": "high",
                    }
                ],
            }
    except Exception as e:
        error(f"Error during file map validation for {file_path}: {str(e)}")
        return {
            "is_valid": False,
            "file": file_path,
            "summary": f"Error during validation: {str(e)}",
            "issues": [
                {
                    "type": "validation_error",
                    "description": f"Validation API error: {str(e)}",
                    "severity": "high",
                }
            ],
        }


def should_abort_on_validation_failure(
    validation_result: Dict[str, Any], config: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Determines if processing should be aborted based on validation results.
    This relaxed version only aborts on truly critical structural issues.

    Args:
        validation_result: Validation results dictionary
        config: Configuration dictionary

    Returns:
        bool: True if processing should be aborted, False otherwise
    """
    # If validation was successful, don't abort
    if validation_result.get("is_valid", False):
        return False

    # Check if we should abort on validation failure
    abort_on_failure = False
    if config:
        abort_on_failure = get_config_value(
            config, "validation.abort_on_failure", False
        )

    # If not configured to abort on failure, don't abort
    if not abort_on_failure:
        return False

    # In relaxed mode, only abort on truly critical issues
    # Check for critical issues that would make the file map completely unusable
    has_critical_structural_issues = any(
        issue.get("severity") == "critical"
        and issue.get("type")
        in ["major_missing", "critical_error", "severe_inaccuracy"]
        for issue in validation_result.get("issues", [])
    )

    # Even in strict mode, be more lenient - only abort on critical structural issues
    strict_mode = config and get_config_value(config, "validation.strict", False)

    # Only abort if there are truly critical structural issues
    # Don't abort on minor issues even in strict mode
    return has_critical_structural_issues


def log_validation_issues(validation_result: Dict[str, Any], file_path: str) -> None:
    """
    Logs validation issues with appropriate severity levels.
    This relaxed version treats most issues as informational.

    Args:
        validation_result: Validation results dictionary
        file_path: Path to the file being validated
    """
    if validation_result.get("is_valid", False):
        info(f"File map validation successful for {file_path}")
        return

    # In relaxed mode, treat validation issues as informational unless critical
    has_critical_issues = any(
        issue.get("severity") == "critical"
        for issue in validation_result.get("issues", [])
    )

    if has_critical_issues:
        warning(
            f"File map validation found critical issues for {file_path}: {validation_result.get('summary', 'Unknown issues')}"
        )
    else:
        info(
            f"File map validation completed for {file_path} with minor issues: {validation_result.get('summary', 'Minor issues found')}"
        )

    for i, issue in enumerate(validation_result.get("issues", [])):
        severity = issue.get("severity", "medium")
        issue_desc = f"Issue {i+1}: {issue.get('type')} - {issue.get('description')}"

        if severity == "critical":
            error(f"CRITICAL: {issue_desc}")
        elif severity == "high":
            info(f"HIGH: {issue_desc}")  # Downgrade from error to info
        elif severity == "medium":
            info(f"MEDIUM: {issue_desc}")  # Downgrade from warning to info
        else:
            info(issue_desc)


def create_comprehensive_validation_prompt(
    file_path: str, content: str, file_map_json: str
) -> str:
    """
    Creates a comprehensive validation prompt that provides detailed, actionable feedback.
    This version focuses on identifying specific issues that can be corrected.

    Args:
        file_path: Path to the file
        content: Content of the file
        file_map_json: Generated file map JSON

    Returns:
        str: Formatted prompt for comprehensive validation with correction guidance
    """
    file_ext = os.path.splitext(file_path)[1]
    file_name = os.path.basename(file_path)

    prompt = f"""# Role and Objective
You are a file map validation expert. Your mission is to thoroughly validate file maps and provide specific, actionable feedback for corrections.

# Validation Task
Perform a comprehensive validation of the provided file map against the source file content.

## File Information
- **File**: {file_path}
- **Name**: {file_name}
- **Extension**: {file_ext}

# Comprehensive Validation Criteria

## Structural Accuracy (Critical)
- **Function Count**: Verify all functions are captured (including async functions)
- **Class Count**: Verify all classes are captured
- **Method Count**: Verify all methods within classes (including async methods)
- **Import Accuracy**: Verify only top-level imports are included
- **Line Numbers**: Verify line numbers are accurate (accounting for FILE_MAP header)

## Content Accuracy (Important)
- **Function Signatures**: Check parameter lists, return types, async keywords
- **Class Inheritance**: Verify base classes are correctly identified
- **Constants**: Check that major constants are captured
- **Descriptions**: Verify descriptions are meaningful and accurate

## Specific Checks to Perform
1. **Count all functions in source** (including async def)
2. **Count all classes in source**
3. **For each class, count all methods** (including async def)
4. **Verify import statements** (only top-level, not nested)
5. **Check line number accuracy** (remember FILE_MAP adds 2 lines offset)
6. **Verify function signatures** include async keyword where appropriate

# Source File Content
```
{content}
```

# File Map to Validate
```json
{file_map_json}
```

# Output Requirements

Provide your validation results in this EXACT JSON format:

```json
{{
  "is_valid": true/false,
  "summary": "Detailed summary of validation results",
  "confidence_score": 85,
  "issues": [
    {{
      "type": "missing_function|incorrect_count|wrong_line_number|missing_async|incorrect_signature",
      "description": "Specific description of the issue",
      "location": "Location in file map or source",
      "severity": "critical|high|medium|low",
      "line_reference": 42,
      "expected_value": "What the correct value should be",
      "actual_value": "What was found in the file map",
      "suggested_fix": "Specific correction to make"
    }}
  ],
  "corrections": {{
    "functions_to_add": [
      {{
        "name": "missing_function_name",
        "line": 123,
        "signature": "async def missing_function(param1: str) -> bool",
        "is_async": true
      }}
    ],
    "functions_to_update": [
      {{
        "name": "existing_function",
        "current_line": 100,
        "correct_line": 102,
        "current_signature": "def func()",
        "correct_signature": "async def func(param: str)"
      }}
    ],
    "classes_to_add": [],
    "classes_to_update": [
      {{
        "name": "ExistingClass",
        "missing_methods": [
          {{
            "name": "missing_method",
            "line": 150,
            "signature": "async def missing_method(self) -> None"
          }}
        ]
      }}
    ],
    "line_number_corrections": [
      {{
        "element_type": "function",
        "element_name": "function_name",
        "current_line": 100,
        "correct_line": 102
      }}
    ]
  }},
  "validation_details": {{
    "total_functions_in_source": 10,
    "total_functions_in_map": 8,
    "total_classes_in_source": 3,
    "total_classes_in_map": 3,
    "total_methods_in_source": 25,
    "total_methods_in_map": 20,
    "import_statements_correct": true,
    "line_numbers_accurate": false
  }},
  "recommendations": [
    "Specific recommendations for improving the file map"
  ]
}}
```

# Validation Instructions
- Be thorough and precise in identifying discrepancies
- Count every function, class, and method in the source
- Check that async functions are properly marked
- Verify line numbers account for FILE_MAP header offset (+2 lines)
- Provide specific corrections in the "corrections" section
- Mark as invalid if there are significant structural discrepancies
- Focus on actionable feedback that can be used for automatic correction

Perform the validation systematically and provide ONLY the JSON validation result with detailed corrections."""

    return prompt


async def correct_file_map(
    file_path: str,
    content: str,
    file_map_json: str,
    validation_result: Dict[str, Any],
    api_client,
    model: str,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Corrects a file map based on validation results using AI assistance.

    Args:
        file_path: Path to the file
        content: Content of the file
        file_map_json: Original file map JSON
        validation_result: Results from comprehensive validation
        api_client: API client for making requests
        model: Model to use for correction
        config: Configuration dictionary

    Returns:
        Dict[str, Any]: Correction results with updated file map
    """
    debug(f"Correcting file map for {file_path}")

    # If the file map is already valid, no correction needed
    if validation_result.get("is_valid", False):
        return {
            "corrected": False,
            "reason": "File map is already valid",
            "file_map_json": file_map_json,
        }

    # Extract corrections from validation result
    corrections = validation_result.get("corrections", {})
    issues = validation_result.get("issues", [])

    if not corrections and not issues:
        return {
            "corrected": False,
            "reason": "No specific corrections provided by validation",
            "file_map_json": file_map_json,
        }

    # Create correction prompt
    correction_prompt = create_correction_prompt(
        file_path, content, file_map_json, validation_result
    )

    try:
        debug(f"Calling correction model: {model}")

        # Call the AI corrector
        system_message = "You are an expert code analyzer tasked with correcting file maps based on validation feedback."

        correction_response = await api_client.generate_completion(
            system_message=system_message,
            user_message=correction_prompt,
            model=model,
            max_tokens=4000,  # More tokens for correction
        )

        # Parse the correction results
        try:
            # Look for JSON in the response
            json_start = correction_response.find("{")
            json_end = correction_response.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_content = correction_response[json_start:json_end]
                correction_results = json.loads(json_content)

                # Validate that we got a corrected file map
                if "corrected_file_map" in correction_results:
                    debug(f"File map correction successful")
                    return {
                        "corrected": True,
                        "file_map_json": json.dumps(
                            correction_results["corrected_file_map"]
                        ),
                        "corrections_applied": correction_results.get(
                            "corrections_applied", []
                        ),
                        "summary": correction_results.get(
                            "summary", "File map corrected successfully"
                        ),
                    }
                else:
                    error(f"Correction response missing corrected_file_map")
                    return {
                        "corrected": False,
                        "reason": "Correction response missing corrected file map",
                        "file_map_json": file_map_json,
                    }
            else:
                error(f"Failed to parse correction response: {correction_response}")
                return {
                    "corrected": False,
                    "reason": "Failed to parse correction response",
                    "file_map_json": file_map_json,
                }
        except json.JSONDecodeError as e:
            error(f"JSON parse error in correction response: {str(e)}")
            return {
                "corrected": False,
                "reason": f"JSON parse error: {str(e)}",
                "file_map_json": file_map_json,
            }
    except Exception as e:
        error(f"Error during file map correction for {file_path}: {str(e)}")
        return {
            "corrected": False,
            "reason": f"Error during correction: {str(e)}",
            "file_map_json": file_map_json,
        }


def create_correction_prompt(
    file_path: str, content: str, file_map_json: str, validation_result: Dict[str, Any]
) -> str:
    """
    Creates a prompt for AI to correct the file map based on validation results.

    Args:
        file_path: Path to the file
        content: Content of the file
        file_map_json: Original file map JSON
        validation_result: Results from validation

    Returns:
        str: Formatted prompt for correction
    """
    file_ext = os.path.splitext(file_path)[1]
    file_name = os.path.basename(file_path)

    issues_text = "\n".join(
        [
            f"- {issue.get('type', 'unknown')}: {issue.get('description', 'No description')}"
            for issue in validation_result.get("issues", [])
        ]
    )

    corrections_text = json.dumps(validation_result.get("corrections", {}), indent=2)

    prompt = f"""# Role and Objective
You are a file map correction expert. Your mission is to fix the provided file map based on specific validation feedback.

# Correction Task
Apply the identified corrections to fix the file map and ensure it accurately represents the source file.

## File Information
- **File**: {file_path}
- **Name**: {file_name}
- **Extension**: {file_ext}

# Validation Issues Found
{issues_text}

# Specific Corrections to Apply
```json
{corrections_text}
```

# Source File Content
```
{content}
```

# Original File Map (to be corrected)
```json
{file_map_json}
```

# Correction Instructions

1. **Apply all corrections** specified in the corrections section
2. **Add missing functions** with correct signatures and line numbers
3. **Update existing functions** with correct signatures and async keywords
4. **Add missing methods** to classes
5. **Fix line numbers** to account for FILE_MAP header offset (+2 lines)
6. **Ensure async functions** are properly marked with "is_async": true
7. **Verify import accuracy** (only top-level imports)
8. **Maintain JSON structure** and all required fields

# Output Requirements

Provide your correction results in this EXACT JSON format:

```json
{{
  "corrected_file_map": {{
    "file_metadata": {{
      "type": "python",
      "language": "python",
      "title": "{file_name}",
      "description": "Updated description",
      "last_updated": "2025-01-27"
    }},
    "code_elements": {{
      "functions": [
        {{
          "name": "function_name",
          "line": 123,
          "signature": "async def function_name(param: str) -> bool",
          "is_async": true,
          "parameters": [...],
          "description": "Function description"
        }}
      ],
      "classes": [
        {{
          "name": "ClassName",
          "line": 200,
          "methods": [
            {{
              "name": "method_name",
              "line": 210,
              "signature": "async def method_name(self) -> None",
              "is_async": true
            }}
          ],
          "description": "Class description"
        }}
      ],
      "imports": [...],
      "constants": [...]
    }},
    "key_elements": [...],
    "sections": [...],
    "content_hash": "original_hash"
  }},
  "corrections_applied": [
    "Added missing async function: function_name",
    "Updated line numbers for FILE_MAP offset",
    "Added missing methods to ClassName"
  ],
  "summary": "Applied X corrections to fix file map accuracy"
}}
```

# Critical Requirements
- **Preserve all original data** that was correct
- **Apply only the specific corrections** identified by validation
- **Maintain proper JSON structure** with all required fields
- **Ensure line numbers** account for FILE_MAP header (+2 lines)
- **Mark async functions** with "is_async": true in signatures
- **Keep original content_hash** unless specifically correcting it

Apply the corrections systematically and provide ONLY the JSON correction result."""

    return prompt


async def validate_file_map_comprehensive(
    file_path: str,
    content: str,
    file_map_json: str,
    api_client,
    model: str,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Performs comprehensive validation of a file map with detailed correction guidance.

    Args:
        file_path: Path to the file
        content: Content of the file
        file_map_json: Generated file map JSON
        api_client: API client for making requests
        model: Model to use for validation
        config: Configuration dictionary

    Returns:
        Dict[str, Any]: Comprehensive validation results with correction guidance
    """
    debug(f"Performing comprehensive validation for {file_path}")

    # Use validation model from config if specified, otherwise fall back to the provided model
    validation_model = model
    if config and get_config_value(config, "validation.model"):
        validation_model = get_config_value(config, "validation.model")

    # Create the comprehensive validation prompt
    prompt = create_comprehensive_validation_prompt(file_path, content, file_map_json)

    try:
        # Call the AI validator
        debug(f"Calling comprehensive validation model: {validation_model}")

        # Split the prompt into system and user messages
        system_message = "You are an expert code analyzer tasked with comprehensive file map validation and correction guidance."
        user_message = prompt

        validation_response = await api_client.generate_completion(
            system_message=system_message,
            user_message=user_message,
            model=validation_model,
            max_tokens=3000,  # More tokens for comprehensive validation
        )

        # Parse the validation results
        try:
            # Look for JSON in the response
            json_start = validation_response.find("{")
            json_end = validation_response.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_content = validation_response[json_start:json_end]
                validation_results = json.loads(json_content)

                # Add additional validation metadata
                validation_results["file"] = file_path
                validation_results["model_used"] = validation_model
                validation_results["validation_type"] = "comprehensive"

                # Ensure required fields exist
                if not validation_results.get("issues"):
                    validation_results["issues"] = []

                if not validation_results.get("corrections"):
                    validation_results["corrections"] = {}

                if not validation_results.get("validation_details"):
                    validation_results["validation_details"] = {}

                # Set default summary if missing
                if not validation_results.get("summary"):
                    if validation_results.get("is_valid", False):
                        validation_results["summary"] = (
                            "File map validated successfully with comprehensive analysis."
                        )
                    else:
                        issue_count = len(validation_results.get("issues", []))
                        validation_results["summary"] = (
                            f"Comprehensive validation found {issue_count} issues requiring correction."
                        )

                debug(
                    f"Comprehensive validation results: {validation_results['summary']}"
                )
                return validation_results
            else:
                error(
                    f"Failed to parse comprehensive validation response: {validation_response}"
                )
                return {
                    "is_valid": False,
                    "file": file_path,
                    "summary": "Failed to parse comprehensive validation response",
                    "issues": [
                        {
                            "type": "validation_error",
                            "description": "Could not parse comprehensive validation response",
                            "severity": "high",
                        }
                    ],
                    "corrections": {},
                    "validation_details": {},
                }
        except json.JSONDecodeError as e:
            error(f"JSON parse error in comprehensive validation response: {str(e)}")
            return {
                "is_valid": False,
                "file": file_path,
                "summary": "JSON parse error in comprehensive validation response",
                "issues": [
                    {
                        "type": "validation_error",
                        "description": f"JSON parse error: {str(e)}",
                        "severity": "high",
                    }
                ],
                "corrections": {},
                "validation_details": {},
            }
    except Exception as e:
        error(
            f"Error during comprehensive file map validation for {file_path}: {str(e)}"
        )
        return {
            "is_valid": False,
            "file": file_path,
            "summary": f"Error during comprehensive validation: {str(e)}",
            "issues": [
                {
                    "type": "validation_error",
                    "description": f"Comprehensive validation API error: {str(e)}",
                    "severity": "high",
                }
            ],
            "corrections": {},
            "validation_details": {},
        }
