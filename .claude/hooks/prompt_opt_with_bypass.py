#!/usr/bin/env python3
"""
Prompt optimizer with bypass mechanism for raw content.
Supports [RAW]...[/RAW] tags and !raw prefix.
"""
import json
import re
import sys
from typing import Optional, Tuple


def extract_raw_sections(prompt: str) -> Tuple[str, str, bool]:
    """
    Extract raw (unprocessed) and processable sections from prompt.

    Returns: (processable_text, raw_text, has_raw_sections)

    Supports:
    1. [RAW]...[/RAW] tags for inline raw sections
    2. [raw]...[/raw] (case insensitive)
    3. !raw prefix for entire message
    4. !exact prefix for entire message
    5. !verbatim prefix for entire message
    """

    # Check for prefix commands (entire message is raw)
    prompt_lower = prompt.lower().strip()
    if prompt_lower.startswith(("!raw ", "!exact ", "!verbatim ")):
        # Remove the prefix and return entire message as raw
        raw_content = prompt.split(" ", 1)[1] if " " in prompt else prompt[4:]
        return "", raw_content, True

    # Check for [RAW] tags
    raw_pattern = r"\[RAW\](.*?)\[/RAW\]"
    raw_pattern_case_insensitive = r"\[(?i)raw\]"

    raw_sections = []
    processable_sections = []
    last_end = 0

    # Find all RAW sections
    for match in re.finditer(raw_pattern, prompt, re.DOTALL | re.IGNORECASE):
        # Add text before this RAW section to processable
        processable_sections.append(prompt[last_end : match.start()])
        # Add RAW content
        raw_sections.append(match.group(1))
        last_end = match.end()

    # Add any remaining text after last RAW section
    processable_sections.append(prompt[last_end:])

    # Join sections
    processable_text = "".join(processable_sections).strip()
    raw_text = "\n\n".join(raw_sections).strip() if raw_sections else ""

    return processable_text, raw_text, bool(raw_sections)


def create_combined_prompt(optimized: str, raw: str, strategy: str = "merge") -> str:
    """
    Combine optimized and raw sections into final prompt.

    Strategies:
    - merge: Combine both with clear markers
    - raw_first: Raw content first, then optimized
    - raw_last: Optimized first, then raw content
    """

    if not raw:
        return optimized

    if not optimized:
        return raw

    if strategy == "raw_first":
        return f"{raw}\n\n{optimized}"
    elif strategy == "raw_last":
        return f"{optimized}\n\n[USER'S EXACT INSTRUCTIONS - DO NOT INTERPRET]\n{raw}\n[END EXACT INSTRUCTIONS]"
    else:  # merge
        return f"""{optimized}

[ADDITIONAL CONTEXT - EXACT USER TEXT]
{raw}
[END EXACT USER TEXT]"""


def format_help_message() -> str:
    """
    Return help text for bypass features.
    """
    return """
PROMPT OPTIMIZER BYPASS OPTIONS:

1. Use [RAW]...[/RAW] tags to preserve exact text:
   Example: "Create [RAW]MyClass::processData()[/RAW] method"

2. Use !raw prefix to send entire message as-is:
   Example: "!raw Just do exactly what I say here"

3. Mix processed and raw content:
   Example: "Build a web app [RAW]
   Technical requirements:
   - Must use legacy_framework v1.2.3
   - Connect to mainframe_db on port 3270
   [/RAW] with modern UI"

The optimizer will preserve raw sections exactly while enhancing the rest.
"""


# Test the functionality
if __name__ == "__main__":
    test_cases = [
        "Build an app that [RAW]connects to our proprietary API at https://internal.company.com/v2[/RAW] and displays data",
        "!raw Just run this exact command: docker-compose up --build --force-recreate",
        "Create a function [raw]calculateTax(income, state='CA')[/raw] that handles tax calculation",
        "Normal prompt without any raw sections",
        """Implement authentication
        [RAW]
        Use these exact environment variables:
        AUTH_SECRET_KEY=xY9$mN2@pQ5&vR8*
        DB_CONNECTION_STRING=postgresql://user:pass@localhost:5432/mydb
        [/RAW]
        Make it secure""",
    ]

    print("=== PROMPT OPTIMIZER BYPASS TESTS ===\n")

    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}:")
        print(f"Input: {test[:100]}..." if len(test) > 100 else f"Input: {test}")

        processable, raw, has_raw = extract_raw_sections(test)

        print(
            f"Processable: {processable[:80]}..."
            if len(processable) > 80
            else f"Processable: {processable}"
        )
        print(f"Raw: {raw[:80]}..." if len(raw) > 80 else f"Raw: {raw}")
        print(f"Has RAW sections: {has_raw}")
        print("-" * 50)

    print("\n" + format_help_message())
