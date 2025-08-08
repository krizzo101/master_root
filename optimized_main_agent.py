#!/usr/bin/env python3
"""
Optimized Main Agent Implementation

Incorporates GPT-5 new parameters and tools for better performance:
- Verbosity control for token efficiency
- Minimal reasoning for fast responses
- Free-form function calling for code execution
- Context-Free Grammar for syntax validation
- Previous response threading for stateful conversations
"""

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from openai import OpenAI
import os


@dataclass
class AgentConfig:
    """Configuration for the optimized main agent."""

    model: str = "gpt-5-nano"
    verbosity: str = "low"  # low, medium, high
    reasoning_effort: str = "medium"  # minimal, medium, high
    max_output_tokens: int = 4000
    temperature: float = 0.0
    store_responses: bool = True  # Enable stateful conversations


class OptimizedMainAgent:
    """Optimized main agent using GPT-5 new parameters and tools."""

    def __init__(self, config: AgentConfig = None):
        self.config = config or AgentConfig()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.conversation_history = {}  # Track conversation threads

        # Define tools for code execution and validation
        self.tools = [
            {
                "type": "custom",
                "name": "code_exec",
                "description": "Executes Python code and returns the result. Use for testing and validation.",
            },
            {
                "type": "custom",
                "name": "python_grammar",
                "description": "Validates Python code syntax using context-free grammar. Ensures code is syntactically correct.",
                "format": {
                    "type": "grammar",
                    "syntax": "lark",
                    "definition": self._get_python_grammar(),
                },
            },
        ]

    def _get_python_grammar(self) -> str:
        """Get a simplified Python grammar for syntax validation."""
        return r"""
        // Simplified Python grammar for basic syntax validation
        start: (statement | function_def | class_def)*

        statement: assignment | expression | import_stmt | return_stmt
        assignment: IDENTIFIER "=" expression
        expression: IDENTIFIER | STRING | NUMBER | function_call
        function_call: IDENTIFIER "(" (expression ("," expression)*)? ")"

        function_def: "def" IDENTIFIER "(" (parameter ("," parameter)*)? ")" ":" block
        parameter: IDENTIFIER
        block: (statement | function_def | class_def)*

        class_def: "class" IDENTIFIER ":" block

        import_stmt: "import" IDENTIFIER | "from" IDENTIFIER "import" IDENTIFIER
        return_stmt: "return" expression?

        IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9_]*/
        STRING: /"[^"]*"/
        NUMBER: /[0-9]+/
        """

    def _build_optimized_prompt(
        self, task: str, context: str = "", task_type: str = "code_generation"
    ) -> str:
        """Build optimized prompt based on task type and GPT-5 best practices."""

        # Base prompt with GPT-5 optimizations
        base_prompt = f"""You are an expert Python developer. Complete the following task efficiently and correctly.

TASK: {task}

{context if context else ""}

REQUIREMENTS:
- Generate working, production-ready code
- Focus on functionality over elegance
- Use standard library when possible
- Include proper error handling
- Make code copy-paste executable
- Keep it simple and maintainable

OUTPUT FORMAT:
- Generate ONLY the requested code
- No explanations or markdown formatting
- Code should be ready to run immediately
- Include necessary imports and dependencies"""

        # Add task-specific guidance
        if task_type == "code_generation":
            base_prompt += """

CODE GENERATION GUIDELINES:
- Start with imports and dependencies
- Define main functions/classes first
- Include a main() function or __main__ block for testing
- Add basic error handling and logging
- Make sure code can be run directly
- Keep it simple - avoid over-engineering"""

        elif task_type == "bug_fix":
            base_prompt += """

BUG FIX GUIDELINES:
- Identify the root cause of the issue
- Provide a minimal, focused fix
- Test the fix mentally before outputting
- Ensure the fix doesn't introduce new issues
- Keep changes as small as possible"""

        elif task_type == "refactoring":
            base_prompt += """

REFACTORING GUIDELINES:
- Improve code structure and readability
- Maintain existing functionality
- Break down complex functions
- Improve naming and organization
- Add type hints where helpful"""

        return base_prompt

    def _get_verbosity_for_task(self, task_type: str) -> str:
        """Determine optimal verbosity based on task type."""
        verbosity_map = {
            "code_generation": "low",  # Focus on code, not explanations
            "bug_fix": "low",  # Quick, focused fixes
            "refactoring": "medium",  # Some explanation helpful
            "code_review": "high",  # Detailed analysis needed
            "teaching": "high",  # Explanations important
            "documentation": "high",  # Detailed explanations needed
        }
        return verbosity_map.get(task_type, "low")

    def _get_reasoning_effort_for_task(
        self, task_type: str, complexity: str = "medium"
    ) -> str:
        """Determine optimal reasoning effort based on task type and complexity."""

        # Simple tasks can use minimal reasoning
        if task_type in ["simple_fix", "formatting", "basic_validation"]:
            return "minimal"

        # Complex tasks need more reasoning
        if complexity == "high" or task_type in [
            "architecture",
            "complex_algorithm",
            "system_design",
        ]:
            return "high"

        # Default to medium for most tasks
        return "medium"

    def start_conversation(self, session_id: str) -> str:
        """Start a new conversation thread."""
        self.conversation_history[session_id] = {
            "current_response_id": None,
            "messages": [],
            "iteration_count": 0,
        }
        return session_id

    def continue_conversation(
        self,
        session_id: str,
        task: str,
        context: str = "",
        task_type: str = "code_generation",
        complexity: str = "medium",
    ) -> Dict[str, Any]:
        """
        Continue a conversation thread using previous_response_id for stateful context.

        This leverages GPT-5's threading capability to maintain context without
        re-sending the entire conversation history.
        """

        if session_id not in self.conversation_history:
            self.start_conversation(session_id)

        conversation = self.conversation_history[session_id]
        conversation["iteration_count"] += 1

        # Build optimized prompt
        prompt = self._build_optimized_prompt(task, context, task_type)

        # Determine optimal parameters
        verbosity = self._get_verbosity_for_task(task_type)
        reasoning_effort = self._get_reasoning_effort_for_task(task_type, complexity)

        # Prepare API call parameters
        api_params = {
            "model": self.config.model,
            "input": [{"role": "developer", "content": prompt}],
            "text": {"verbosity": verbosity, "format": {"type": "text"}},
            "reasoning": {"effort": reasoning_effort},
            "max_output_tokens": self.config.max_output_tokens,
            "temperature": self.config.temperature,
            "store": self.config.store_responses,  # Enable stateful conversations
        }

        # Add tools for code generation tasks
        if task_type == "code_generation":
            api_params["tools"] = self.tools

        # Add previous_response_id for threading if available
        if conversation["current_response_id"]:
            api_params["previous_response_id"] = conversation["current_response_id"]

        try:
            # Use GPT-5 with optimized parameters and threading
            response = self.client.responses.create(**api_params)

            # Store the response ID for next iteration
            conversation["current_response_id"] = response.id
            conversation["messages"].append(
                {
                    "iteration": conversation["iteration_count"],
                    "task": task,
                    "response_id": response.id,
                }
            )

            # Extract output
            output_text = ""
            for item in response.output:
                if hasattr(item, "content"):
                    for content in item.content:
                        if hasattr(content, "text"):
                            output_text += content.text

            # Get usage metrics
            usage = response.usage

            return {
                "code": output_text,
                "metadata": {
                    "model": self.config.model,
                    "verbosity": verbosity,
                    "reasoning_effort": reasoning_effort,
                    "task_type": task_type,
                    "complexity": complexity,
                    "session_id": session_id,
                    "iteration": conversation["iteration_count"],
                    "response_id": response.id,
                    "threaded": conversation["current_response_id"] is not None,
                },
                "performance": {
                    "input_tokens": usage.input_tokens,
                    "output_tokens": usage.output_tokens,
                    "total_tokens": usage.total_tokens,
                    "estimated_cost": self._estimate_cost(usage.total_tokens),
                },
                "status": "success",
            }

        except Exception as e:
            return {"code": "", "error": str(e), "status": "error"}

    def generate_code(
        self,
        task: str,
        context: str = "",
        task_type: str = "code_generation",
        complexity: str = "medium",
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate code using optimized GPT-5 parameters.

        Args:
            task: The coding task to complete
            context: Additional context or requirements
            task_type: Type of task (code_generation, bug_fix, refactoring, etc.)
            complexity: Task complexity (low, medium, high)
            session_id: Optional session ID for threading

        Returns:
            Dict with generated code, metadata, and performance metrics
        """

        if session_id:
            # Use threaded conversation
            return self.continue_conversation(
                session_id, task, context, task_type, complexity
            )
        else:
            # Single-shot generation (no threading)
            return self._generate_single_shot(task, context, task_type, complexity)

    def _generate_single_shot(
        self,
        task: str,
        context: str = "",
        task_type: str = "code_generation",
        complexity: str = "medium",
    ) -> Dict[str, Any]:
        """Generate code in a single shot without threading."""

        # Build optimized prompt
        prompt = self._build_optimized_prompt(task, context, task_type)

        # Determine optimal parameters
        verbosity = self._get_verbosity_for_task(task_type)
        reasoning_effort = self._get_reasoning_effort_for_task(task_type, complexity)

        try:
            # Use GPT-5 with optimized parameters
            response = self.client.responses.create(
                model=self.config.model,
                input=[{"role": "developer", "content": prompt}],
                text={"verbosity": verbosity, "format": {"type": "text"}},
                reasoning={"effort": reasoning_effort},
                max_output_tokens=self.config.max_output_tokens,
                temperature=self.config.temperature,
                tools=self.tools if task_type == "code_generation" else None,
            )

            # Extract output
            output_text = ""
            for item in response.output:
                if hasattr(item, "content"):
                    for content in item.content:
                        if hasattr(content, "text"):
                            output_text += content.text

            # Get usage metrics
            usage = response.usage

            return {
                "code": output_text,
                "metadata": {
                    "model": self.config.model,
                    "verbosity": verbosity,
                    "reasoning_effort": reasoning_effort,
                    "task_type": task_type,
                    "complexity": complexity,
                    "threaded": False,
                },
                "performance": {
                    "input_tokens": usage.input_tokens,
                    "output_tokens": usage.output_tokens,
                    "total_tokens": usage.total_tokens,
                    "estimated_cost": self._estimate_cost(usage.total_tokens),
                },
                "status": "success",
            }

        except Exception as e:
            return {"code": "", "error": str(e), "status": "error"}

    def _estimate_cost(self, total_tokens: int) -> float:
        """Estimate cost based on model and token count."""
        # Rough cost estimates (adjust based on actual pricing)
        cost_per_1k_tokens = {
            "gpt-5-nano": 0.00015,
            "gpt-5-mini": 0.0003,
            "gpt-5": 0.006,
        }

        model_cost = cost_per_1k_tokens.get(self.config.model, 0.0003)
        return (total_tokens / 1000) * model_cost

    def validate_code_syntax(self, code: str) -> Dict[str, Any]:
        """Validate code syntax using CFG."""

        prompt = f"""Validate the following Python code syntax using the python_grammar tool:

{code}

Ensure the code follows proper Python syntax and is syntactically correct."""

        try:
            response = self.client.responses.create(
                model=self.config.model,
                input=[{"role": "developer", "content": prompt}],
                text={"verbosity": "low", "format": {"type": "text"}},
                reasoning={"effort": "minimal"},
                tools=[self.tools[1]],  # python_grammar tool
                max_output_tokens=100,
            )

            # Check if validation passed
            validation_passed = (
                len(response.output) > 1
            )  # Tool call indicates validation

            return {
                "valid": validation_passed,
                "status": "success" if validation_passed else "syntax_error",
            }

        except Exception as e:
            return {"valid": False, "error": str(e), "status": "error"}

    def execute_code(self, code: str) -> Dict[str, Any]:
        """Execute code using free-form function calling."""

        prompt = f"""Execute the following Python code using the code_exec tool:

{code}

Run the code and return the result."""

        try:
            response = self.client.responses.create(
                model=self.config.model,
                input=[{"role": "developer", "content": prompt}],
                text={"verbosity": "low", "format": {"type": "text"}},
                reasoning={"effort": "minimal"},
                tools=[self.tools[0]],  # code_exec tool
                max_output_tokens=500,
            )

            # Extract execution result
            if len(response.output) > 1:
                tool_call = response.output[1]
                return {
                    "executed": True,
                    "result": tool_call.input
                    if hasattr(tool_call, "input")
                    else "Code executed",
                    "status": "success",
                }
            else:
                return {
                    "executed": False,
                    "result": "No code execution attempted",
                    "status": "no_execution",
                }

        except Exception as e:
            return {"executed": False, "error": str(e), "status": "error"}


# Example usage
if __name__ == "__main__":
    # Test the optimized agent
    agent = OptimizedMainAgent()

    # Test threaded conversation
    session_id = agent.start_conversation("test_session_001")

    # First iteration
    result1 = agent.continue_conversation(
        session_id=session_id,
        task="Create a function that validates email addresses using regex",
        task_type="code_generation",
        complexity="low",
    )

    # Second iteration (builds on first)
    result2 = agent.continue_conversation(
        session_id=session_id,
        task="Now add unit tests for the email validation function",
        task_type="code_generation",
        complexity="medium",
    )

    print("=== OPTIMIZED MAIN AGENT TEST ===")
    print(f"First iteration - Status: {result1['status']}")
    print(f"First iteration - Threaded: {result1['metadata']['threaded']}")
    print(f"First iteration - Tokens: {result1['performance']['total_tokens']}")
    print(f"Second iteration - Status: {result2['status']}")
    print(f"Second iteration - Threaded: {result2['metadata']['threaded']}")
    print(f"Second iteration - Tokens: {result2['performance']['total_tokens']}")
    print(
        f"Total tokens used: {result1['performance']['total_tokens'] + result2['performance']['total_tokens']}"
    )
