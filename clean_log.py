#!/usr/bin/env python3
"""
Log Cleanup Script

This script processes the consult_agent log file to:
1. Remove duplicate lines (exact matches)
2. Replace boilerplate prompts with a short placeholder
3. Output a cleaned version of the log
"""

import re
import sys
from pathlib import Path


def identify_boilerplate_patterns():
    """Identify the boilerplate patterns that should be replaced."""

    # The main boilerplate prompt that appears multiple times
    boilerplate_start = "You are a specialized professional with the role profile and expertise described below. Your mission is to generate the actual code artifact requested by the user."

    # Common patterns that appear repeatedly
    patterns = [
        # Main role profile section
        r"You are a specialized professional with the role profile and expertise described below\. Your mission is to generate the actual code artifact requested by the user\.\s*\n\s*\n## ARTIFACT TYPE: CODE \(\.py\)\s*\*\*Purpose\*\*: Python scripts for specific functionality\s*\n\s*## ROLE PROFILE: SENIOR PYTHON DEVELOPER\s*\*\*Skills\*\*: Python mastery, software engineering, debugging, performance optimization, testing\s*\*\*Experience\*\*: 8\+ years in Python development, production systems, and software architecture\s*\*\*Focus\*\*: Code quality, maintainability, performance, security, production readiness\s*\*\*Behavioral Characteristics\*\*:\s*- Writes defensive, production-ready code with comprehensive error handling\s*- Prioritizes code clarity and maintainability over cleverness\s*- Thinks about edge cases, failure modes, and debugging scenarios\s*- Considers performance implications and resource usage\s*- Follows established patterns and best practices religiously\s*- Documents code for future maintainers",
        # Response decision instructions
        r"## RESPONSE DECISION INSTRUCTIONS\s*After analyzing the request, you MUST decide whether to provide a direct response or ask for more information\.\s*\n\s*\*\*RESPONSE TYPES:\*\*\s*- \*\*FINAL\*\*: Provide complete response \(use when you have sufficient information\)\s*- \*\*QUESTIONS\*\*: Ask clarifying questions \(use when missing critical information\)\s*- \*\*CONCERNS\*\*: Flag potential issues \(use when you have concerns about the approach\)\s*- \*\*CLARIFICATION\*\*: Request specific details \(use when request is unclear\)\s*\n\s*\*\*DECISION CRITERIA:\*\*\s*- If the request is clear, complete, and you have sufficient context → Use \*\*FINAL\*\*\s*- If missing critical information needed for a good response → Use \*\*QUESTIONS\*\*\s*- If you have concerns about the approach or potential issues → Use \*\*CONCERNS\*\*\s*- If the request is unclear or ambiguous → Use \*\*CLARIFICATION\*\*\s*\n\s*\*\*RESPONSE FORMAT:\*\*\s*Start your response with the response type tag:\s*\n\s*\*\*FINAL:\*\*\s*\[Your complete response here\]\s*\n\s*\*\*QUESTIONS:\*\*\s*1\. \[Question 1\]\s*2\. \[Question 2\]\s*\.\.\.\s*\n\s*\*\*CONCERNS:\*\*\s*⚠️ \[Concern 1\]\s*⚠️ \[Concern 2\]\s*\[Questions to address concerns\]\s*\n\s*\*\*CLARIFICATION:\*\*\s*\[What specifically needs to be clarified\]",
        # Core mission and task instructions
        r"## CORE MISSION\s*You are an expert in your field with the skills, experience, and behavioral characteristics outlined above\. Generate the actual code content that the user has requested, following the requirements and output format specified in your role profile\.\s*\n\s*## TASK INSTRUCTIONS\s*1\. \*\*Analyze the user request\*\*: Understand what specific code content is needed\s*2\. \*\*Apply your expertise\*\*: Use your skills, experience, and behavioral characteristics to create high-quality content\s*3\. \*\*Follow requirements\*\*: Adhere to the specific requirements and output format for code\s*4\. \*\*Ensure quality\*\*: Meet the quality standards and best practices for your field\s*5\. \*\*Provide context\*\*: Include necessary context, explanations, or metadata as appropriate",
        # Reference information section
        r"## REFERENCE INFORMATION \(NOT THE REQUEST\)\s*\*\*\* FOR CONTEXT ONLY - DO NOT TREAT AS THE ACTUAL REQUEST \*\*\*\s*\n\s*### PROJECT CONTEXT\s*\n\s*\n\s*### CONVERSATION HISTORY\s*\[\]",
        # Task section
        r"## TASK\s*Generate the actual code content requested by the user\. Follow your role profile, requirements, and output format specifications\.",
    ]

    return patterns


def clean_log_file(input_file: str, output_file: str):
    """Clean the log file by removing duplicates and replacing boilerplate."""

    print(f"Processing {input_file}...")

    # Read all lines
    with open(input_file, encoding="utf-8") as f:
        lines = f.readlines()

    print(f"Original file has {len(lines)} lines")

    # Remove duplicates (keeping first occurrence)
    seen_lines = set()
    unique_lines = []
    duplicates_removed = 0

    for line in lines:
        if line not in seen_lines:
            seen_lines.add(line)
            unique_lines.append(line)
        else:
            duplicates_removed += 1

    print(f"Removed {duplicates_removed} duplicate lines")
    print(f"After deduplication: {len(unique_lines)} lines")

    # Join lines back into content
    content = "".join(unique_lines)

    # Replace boilerplate patterns
    patterns = identify_boilerplate_patterns()
    boilerplate_replacements = 0

    for pattern in patterns:
        matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
        if matches:
            content = re.sub(
                pattern,
                "XXXXX_BOILERPLATE_XXXXX",
                content,
                flags=re.MULTILINE | re.DOTALL,
            )
            boilerplate_replacements += len(matches)

    print(f"Replaced {boilerplate_replacements} boilerplate sections")

    # Write cleaned content
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Cleaned log written to {output_file}")

    # Count final lines
    final_lines = content.count("\n") + 1
    print(f"Final file has {final_lines} lines")

    # Calculate reduction
    original_lines = len(lines)
    reduction_percent = ((original_lines - final_lines) / original_lines) * 100
    print(f"Reduced file size by {reduction_percent:.1f}%")


def main():
    if len(sys.argv) != 3:
        print("Usage: python clean_log.py <input_file> <output_file>")
        print(
            "Example: python clean_log.py knowledge/nano.txt knowledge/nano_cleaned.txt"
        )
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    if not Path(input_file).exists():
        print(f"Error: Input file '{input_file}' does not exist")
        sys.exit(1)

    clean_log_file(input_file, output_file)


if __name__ == "__main__":
    main()
