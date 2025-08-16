import logging
import os
import re
from typing import Any


class WorkflowPrompt:
    def __init__(self, name: str, content: str, dependencies: list[str]):
        self.name = name
        self.content = content
        self.dependencies = dependencies

    def __repr__(self):
        return f"WorkflowPrompt(name={self.name}, dependencies={self.dependencies})"


class ExecutionPlan:
    def __init__(self, prompts: list[WorkflowPrompt]):
        self.prompts = prompts
        self.plan = self._build_plan()

    def _build_plan(self) -> list[dict[str, Any]]:
        # Topological sort for dependency resolution (simple, assumes no cycles)
        resolved = set()
        plan = []
        prompts_by_name = {p.name: p for p in self.prompts}

        def visit(prompt):
            if prompt.name in resolved:
                return
            for dep in prompt.dependencies:
                if dep in prompts_by_name:
                    visit(prompts_by_name[dep])
            plan.append(prompt)
            resolved.add(prompt.name)

        for prompt in self.prompts:
            visit(prompt)
        return plan

    def pretty_print(self):
        print("Execution Plan:")
        for i, prompt in enumerate(self.plan):
            print(f"  Step {i+1}: {prompt.name} (depends on: {prompt.dependencies})")


class PromptParser:
    def __init__(self, prompt_path: str):
        self.prompt_path = prompt_path
        self.prompts: list[WorkflowPrompt] = []

    def parse(self):
        if not os.path.exists(self.prompt_path):
            raise FileNotFoundError(f"Prompt file not found: {self.prompt_path}")
        with open(self.prompt_path) as f:
            content = f.read()
        # Example: parse sections like '## Workflow: <name>'
        pattern = r"## Workflow: (.*?)\n(.*?)(?=^## Workflow: |\Z)"
        matches = re.findall(pattern, content, re.DOTALL | re.MULTILINE)
        for name, body in matches:
            dep_match = re.search(r"Dependencies: (.*)", body)
            dependencies = (
                [d.strip() for d in dep_match.group(1).split(",")] if dep_match else []
            )
            self.prompts.append(
                WorkflowPrompt(
                    name=name.strip(), content=body.strip(), dependencies=dependencies
                )
            )
        logging.debug(f"Parsed {len(self.prompts)} workflow prompts.")
        return self.prompts

    def build_execution_plan(self):
        return ExecutionPlan(self.prompts)


if __name__ == "__main__":
    # Example input for demonstration
    example_prompt = """
# Example Workflow Manifest

## Workflow: GenerateDocs
Description: Generate documentation for the project.
Dependencies:

## Workflow: GenerateCode
Description: Generate code for the project.
Dependencies: GenerateDocs

## Workflow: RunTests
Description: Run tests on the generated code.
Dependencies: GenerateCode
"""
    # Write example to temp file
    tmp_path = "example_prompt.md"
    with open(tmp_path, "w") as f:
        f.write(example_prompt)
    parser = PromptParser(tmp_path)
    parser.parse()
    plan = parser.build_execution_plan()
    plan.pretty_print()
    breakpoint()  # Pause for inspection
