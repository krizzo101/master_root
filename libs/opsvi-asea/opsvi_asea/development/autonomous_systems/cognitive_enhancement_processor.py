#!/usr/bin/env python3
"""
Cognitive Enhancement Processor

A functional system that processes user prompts using the ASEA orchestrator
with real AI agents (cognitive_pre_analysis, ai_reasoning, cognitive_critic).

Usage:
    python3 cognitive_enhancement_processor.py "Your prompt here"
    python3 cognitive_enhancement_processor.py --interactive
"""
import sys
import asyncio
import argparse
import json
from typing import Dict, Any, Optional

# Add orchestrator to path
ORCHESTRATOR_PATH = "/home/opsvi/asea/asea_orchestrator/src"
if ORCHESTRATOR_PATH not in sys.path:
    sys.path.append(ORCHESTRATOR_PATH)

try:
    from asea_orchestrator.core import Orchestrator
    from asea_orchestrator.workflow import WorkflowManager
    from asea_orchestrator.plugins.types import PluginConfig
except ImportError as e:
    print(f"Error importing orchestrator: {e}")
    print("Make sure you're running from the correct directory")
    sys.exit(1)


class CognitiveEnhancementProcessor:
    """Processes prompts using real AI agents through the orchestrator."""

    def __init__(self):
        self.orchestrator = None
        self.plugin_dir = (
            "/home/opsvi/asea/asea_orchestrator/src/asea_orchestrator/plugins/available"
        )
        self.workflow_file = "/home/opsvi/asea/asea_orchestrator/workflows/cognitive_enhancement/enhanced_response_workflow.json"

    def _load_enhanced_workflow(self) -> Dict[str, Any]:
        """Load the enhanced response workflow with proper input/output mapping."""
        # Based on the documentation, input/output mapping works with workflow state as shared storage
        # inputs: plugin_parameter_name -> workflow_state_key
        # outputs: plugin_result_key -> workflow_state_key
        return {
            "ai_enhanced_response": {
                "steps": [
                    # Step 1: Pre-analysis to enhance understanding
                    {
                        "plugin_name": "cognitive_pre_analysis",
                        "parameters": {"analysis_depth": "standard"},
                        "inputs": {
                            "user_prompt": "user_prompt",  # plugin param <- workflow state key
                            "context": "context",
                        },
                        "outputs": {
                            "enhanced_understanding": "enhanced_understanding",  # plugin result -> workflow state
                            "thinking_approach": "thinking_approach",
                            "potential_challenges": "potential_challenges",
                        },
                    },
                    # Step 2: First AI reasoning with enhanced understanding
                    {
                        "plugin_name": "ai_reasoning",
                        "parameters": {
                            "model": "gpt-4.1-mini",
                            "temperature": 0.1,
                            "max_tokens": 3000,
                            "action": "reason",
                        },
                        "inputs": {
                            "prompt": "enhanced_understanding"  # Use enhanced understanding as the prompt
                        },
                        "outputs": {"final_conclusion": "draft_response"},
                    },
                    # Step 3: Cognitive critic reviews the response
                    {
                        "plugin_name": "cognitive_critic",
                        "parameters": {"critique_focus": "comprehensive"},
                        "inputs": {
                            "original_prompt": "user_prompt",
                            "agent_response": "draft_response",
                        },
                        "outputs": {
                            "critique": "critique",
                            "quality_score": "quality_score",
                            "needs_revision": "needs_revision",
                            "improvement_suggestions": "improvement_suggestions",
                        },
                    },
                    # Step 4: Create improvement prompt based on critique and quality score
                    {
                        "plugin_name": "ai_reasoning",
                        "parameters": {
                            "model": "gpt-4o-mini",
                            "temperature": 0.1,
                            "max_tokens": 1000,
                            "action": "reason",
                        },
                        "inputs": {
                            "prompt": "critique"  # Use the critique text from critic
                        },
                        "outputs": {"final_conclusion": "improvement_prompt"},
                    },
                    # Step 5: Final AI reasoning with comprehensive improvement guidance
                    {
                        "plugin_name": "ai_reasoning",
                        "parameters": {
                            "model": "gpt-4o-mini",
                            "temperature": 0.2,  # Slightly higher for creativity in improvements
                            "max_tokens": 4000,  # More tokens for comprehensive response
                            "action": "reason",
                        },
                        "inputs": {
                            "prompt": "improvement_prompt"  # Use the improvement guidance
                        },
                        "outputs": {"final_conclusion": "final_response"},
                    },
                ]
            }
        }

    async def initialize(self):
        """Initialize the orchestrator."""
        print("Initializing ASEA Orchestrator...")

        # Load the enhanced workflow
        workflow_definitions = self._load_enhanced_workflow()

        # Create workflow manager with the enhanced workflow
        workflow_manager = WorkflowManager(workflow_definitions)

        # Create orchestrator
        self.orchestrator = Orchestrator(
            plugin_dir=self.plugin_dir, workflow_manager=workflow_manager
        )

        print(
            f"✅ System ready: {len(self.orchestrator.plugin_manager.plugins)} plugins loaded"
        )

        return True

    async def process_prompt(
        self, user_prompt: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process a user prompt through the cognitive enhancement workflow."""

        if not self.orchestrator:
            await self.initialize()

        # Configure the AI plugins that actually call OpenAI
        plugin_configs = {
            "cognitive_reminder": PluginConfig(
                name="cognitive_reminder",
                enabled=True,
                config={"action": "get_reminders", "num_reminders": 3},
            ),
            "cognitive_pre_analysis": PluginConfig(
                name="cognitive_pre_analysis",
                enabled=True,
                config={"analysis_depth": "standard"},
            ),
            "ai_reasoning": PluginConfig(
                name="ai_reasoning",
                enabled=True,
                config={
                    "model": "gpt-4.1-mini",  # Use cost-effective model
                    "temperature": 0.1,
                    "max_tokens": 3000,
                },
            ),
            "cognitive_critic": PluginConfig(
                name="cognitive_critic",
                enabled=True,
                config={"critique_focus": "comprehensive"},
            ),
        }

        # Configure plugins in orchestrator
        self.orchestrator.temp_configure_plugins(plugin_configs)

        # Initial state with user prompt
        initial_state = {
            "user_prompt": user_prompt,
            "context": context or {},
            "task_type": "general",
        }

        print(f"Processing: {user_prompt[:100]}...")

        try:
            # Try enhanced_response_workflow first, fallback to ai_enhanced_response
            workflow_name = (
                "enhanced_response_workflow"
                if "enhanced_response_workflow"
                in self.orchestrator.workflow_manager.workflows
                else "ai_enhanced_response"
            )

            # Execute the workflow
            result = await self.orchestrator.run_workflow(
                workflow_name=workflow_name, initial_state=initial_state
            )

            return result

        except Exception as e:
            print(f"Error processing prompt: {e}")
            return {"error": str(e), "success": False}

    def format_response(self, result: Dict[str, Any]) -> str:
        """Format the orchestrator result for display."""

        if "error" in result:
            return f"❌ Error: {result['error']}"

        if not result.get("success", True):  # Default to True if not specified
            return (
                f"❌ Processing failed: {result.get('error_message', 'Unknown error')}"
            )

        # Look for AI response in various possible locations
        response_text = None

        # Check for enhanced_response (from enhanced_response_workflow)
        if "enhanced_response" in result:
            response_text = result["enhanced_response"]

        # Check for ai_response (from ai_enhanced_response workflow)
        elif "ai_response" in result:
            response_text = result["ai_response"]

        # Check for final_response (alternative location)
        elif "final_response" in result:
            response_text = result["final_response"]

        # Check for response in nested data
        elif "data" in result and isinstance(result["data"], dict):
            data = result["data"]
            response_text = (
                data.get("response")
                or data.get("final_response")
                or data.get("enhanced_response")
            )

        if response_text:
            output = f"\n🧠 ENHANCED RESPONSE:\n{response_text}\n"

            # Add cognitive metadata if available
            metadata = result.get("cognitive_metadata", {})
            if metadata:
                output += "\n📊 COGNITIVE ANALYSIS:\n"
                if "critique_score" in metadata:
                    output += f"   Quality Score: {metadata['critique_score']}/10\n"
                if "revision_needed" in metadata:
                    output += f"   Revision Applied: {metadata['revision_needed']}\n"

            # Add quality score if available directly in result
            if "quality_score" in result:
                output += f"\n📊 Quality Score: {result['quality_score']}/10\n"

            return output

        # Fallback: show whatever we got
        return f"\n📋 RESULT:\n{json.dumps(result, indent=2)}"


async def main():
    """Main function to handle command line usage."""

    parser = argparse.ArgumentParser(
        description="Process prompts with cognitive enhancement"
    )
    parser.add_argument("prompt", nargs="?", help="Prompt to process")
    parser.add_argument(
        "--interactive", "-i", action="store_true", help="Interactive mode"
    )

    args = parser.parse_args()

    processor = CognitiveEnhancementProcessor()

    try:
        if args.interactive:
            print("🧠 Cognitive Enhancement Processor - Interactive Mode")
            print("Type 'quit' to exit\n")

            while True:
                try:
                    prompt = input("Enter prompt: ").strip()
                    if prompt.lower() in ["quit", "exit", "q"]:
                        break

                    if prompt:
                        result = await processor.process_prompt(prompt)
                        print(processor.format_response(result))
                        print("-" * 60)

                except (KeyboardInterrupt, EOFError):
                    print("\nExiting...")
                    break

        elif args.prompt:
            result = await processor.process_prompt(args.prompt)
            print(processor.format_response(result))

        else:
            print("Please provide a prompt or use --interactive mode")
            parser.print_help()

    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
