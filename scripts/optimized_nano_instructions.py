#!/usr/bin/env python3
"""
Optimized Nano Model Instructions

Incorporates GPT-5 best practices and structured feedback handling for better code generation.
"""


def get_optimized_nano_prompt(
    artifact_type: str,
    original_prompt: str,
    critic_feedback: str = None,
    iteration_count: int = 1,
) -> str:
    """
    Get optimized prompt for nano model with GPT-5 best practices.

    Args:
        artifact_type: Type of artifact to generate (code, test, etc.)
        original_prompt: The original user request
        critic_feedback: Structured feedback from critic (if iterating)
        iteration_count: Which iteration this is

    Returns:
        Optimized prompt string
    """

    # Base role definition with GPT-5 optimizations
    base_prompt = f"""You are a specialized Python developer with expertise in creating {artifact_type} that meets production standards.

<self_reflection>
- Think of a brief internal rubric for quality: correctness, completeness, simplicity, runnability
- Iterate privately until confident in your approach
- Focus on the simplest functional solution that works
</self_reflection>

<tool_preambles>
- Rephrase the goal concisely: {original_prompt[:100]}...
- Outline a short plan: analyze requirements → design solution → implement → validate
- Summarize completion at the end with key features implemented
</tool_preambles>

<persistence>
- Keep going until the task is fully completed
- Don't stop until all requirements are addressed
- If unsure about details, make reasonable assumptions and document them
</persistence>

## CORE PRINCIPLES (Priority Order)
1. **IT WORKS** - Code must run without errors, copy-paste executable
2. **COMPLETE** - Implements all requirements from the prompt
3. **SIMPLE** - Prefer the simplest functional solution over complex elegance
4. **CLEAR** - Readable, well-structured, minimal but sufficient comments

## PYTHON STANDARDS
- Use standard library when possible
- Follow PEP 8 for basic formatting
- Include proper error handling
- Make code self-contained and runnable
- Use type hints where helpful
- Keep functions focused and small
- Prefer explicit over implicit

## OUTPUT FORMAT
Generate ONLY the requested {artifact_type}. No explanations, no markdown formatting, no extra text.
The output should be ready to use immediately."""

    # Add iteration-specific guidance
    if iteration_count > 1 and critic_feedback:
        iteration_guidance = f"""

## ITERATION {iteration_count} - IMPROVEMENT FOCUS

<self_reflection>
- Review the critic feedback carefully
- Prioritize fixes by severity: syntax errors → functional issues → improvements
- Focus on making the code work correctly first, then optimize
</self_reflection>

## CRITIC FEEDBACK TO ADDRESS:
{critic_feedback}

## IMPROVEMENT INSTRUCTIONS:
- Address ALL critical issues identified by the critic
- Fix syntax errors and functional problems first
- Implement missing functionality if any
- Improve code quality based on feedback
- Keep changes focused and minimal
- Test your changes mentally before outputting

## SUCCESS CRITERIA:
- All critic-identified issues are resolved
- Code is syntactically correct and runnable
- All original requirements are still met
- No new issues are introduced

After making improvements, evaluate if the code meets all requirements and critic feedback.
If satisfied, append [COMPLETE] to your output; otherwise, continue iterating."""
    else:
        iteration_guidance = ""

    # Add artifact-specific guidance
    if artifact_type == "code":
        artifact_guidance = """

## CODE GENERATION GUIDELINES
- Start with imports and dependencies
- Define main functions/classes first
- Include a main() function or __main__ block for testing
- Add basic error handling and logging
- Make sure code can be run directly
- Include example usage if helpful
- Keep it simple - avoid over-engineering"""
    elif artifact_type == "test":
        artifact_guidance = """

## TEST GENERATION GUIDELINES
- Use pytest format
- Test happy path and edge cases
- Include setup and teardown if needed
- Make tests deterministic
- Provide clear failure messages
- Test all major functionality
- Keep tests focused and readable"""
    else:
        artifact_guidance = ""

    # Combine all parts
    full_prompt = base_prompt + iteration_guidance + artifact_guidance

    return full_prompt


def get_structured_critic_feedback_parser() -> str:
    """Get instructions for parsing structured critic feedback."""

    return """
## PARSING CRITIC FEEDBACK

When you receive critic feedback, parse it systematically:

### 1. VERDICT
- "accept" = code is good, minor improvements only
- "revise" = significant issues need fixing

### 2. SCORES (0-1 scale)
- correctness: Does it work correctly?
- consistency: Does it follow conventions?
- safety: Are there security/robustness issues?
- efficiency: Is it reasonably performant?
- clarity: Is it readable and well-structured?

### 3. FAILURES (Priority order)
- syntax: Code won't run (fix first)
- test: Tests fail (fix second)
- contract: API mismatches (fix third)
- safety: Security/robustness issues (fix fourth)
- other: Style/quality issues (fix last)

### 4. NEXT ACTIONS
- Atomic, specific tasks to complete
- Each action ≤ 140 characters
- Focus on one action at a time

### 5. BLOCKING REASON
- Critical issue that prevents acceptance
- Must be resolved before proceeding

## RESPONSE STRATEGY
1. Fix syntax errors first (code must run)
2. Fix functional issues (code must work)
3. Address safety concerns
4. Improve clarity and style
5. Verify all original requirements are met
"""


# Example usage
if __name__ == "__main__":
    # Example for first iteration
    prompt1 = get_optimized_nano_prompt(
        artifact_type="code",
        original_prompt="Create a simple web scraper that extracts titles from a list of URLs",
        iteration_count=1,
    )

    print("=== FIRST ITERATION PROMPT ===")
    print(prompt1[:500] + "...")

    # Example for second iteration with critic feedback
    critic_feedback = """
{
  "verdict": "revise",
  "scores": {"correctness": 0.8, "consistency": 0.9, "safety": 0.7, "efficiency": 0.8, "clarity": 0.9},
  "failures": [
    {
      "category": "safety",
      "evidence": "requests.get() without timeout will hang indefinitely",
      "location": "web scraping function",
      "minimal_fix_hint": "Add timeout parameter to requests.get()"
    }
  ],
  "next_actions": ["Add timeout=30 to requests.get() calls"]
}
"""

    prompt2 = get_optimized_nano_prompt(
        artifact_type="code",
        original_prompt="Create a simple web scraper that extracts titles from a list of URLs",
        critic_feedback=critic_feedback,
        iteration_count=2,
    )

    print("\n=== SECOND ITERATION PROMPT ===")
    print(prompt2[:500] + "...")
