"""
Brainstorming Tool for O3 Code Generator

This script handles idea generation, evaluation, prioritization,
and saving brainstorming ideas using O3ModelGenerator. It uses
the O3 models to generate and enhance brainstorming sessions.
"""

import argparse
import json
import sys
import time
from typing import Any

from src.tools.code_generation.o3_code_generator.analysis_utils import (
    save_brainstorm_results_for_next_step,
    save_interactive_input,
)
from src.tools.code_generation.o3_code_generator.config.core.config_manager import (
    ConfigManager,
)
from src.tools.code_generation.o3_code_generator.o3_logger.logger import (
    get_logger,
)
from src.tools.code_generation.o3_code_generator.prompts.idea_formation_prompts import (
    BRAINSTORMING_SYSTEM_PROMPT,
)
from src.tools.code_generation.o3_code_generator.schemas.idea_formation_schemas import (
    BrainstormingInput,
    BrainstormingOutput,
)
from src.tools.code_generation.o3_code_generator.utils.directory_manager import (
    DirectoryManager,
)
from src.tools.code_generation.o3_code_generator.utils.file_generator import (
    FileGenerator,
)
from src.tools.code_generation.o3_code_generator.utils.input_loader import (
    UniversalInputLoader,
)
from src.tools.code_generation.o3_code_generator.utils.interactive import (
    run_interactive_brainstorm_session,
)
from src.tools.code_generation.o3_code_generator.utils.o3_model_generator import (
    O3ModelGenerator,
)
from src.tools.code_generation.o3_code_generator.utils.prompt_builder import (
    PromptBuilder,
)


class BrainstormingProcessor:
    """Main processor for brainstorming using O3 models."""

    def __init__(self) -> None:
        """Initialize the brainstorming processor."""
        self.logger = get_logger()

        try:
            self.client = O3ModelGenerator()
            self.logger.log_info("O3ModelGenerator initialized successfully")
        except Exception as e:
            self.logger.log_error(f"Failed to initialize O3ModelGenerator: {e}")
            raise

        self.directory_manager = DirectoryManager()
        self.prompt_builder = PromptBuilder()
        self.file_generator = FileGenerator()
        self.directory_manager.create_module_directories("brainstorming")

    def run(self, input_data: BrainstormingInput) -> BrainstormingOutput:
        """
        Run a brainstorming session end-to-end with enhanced conversation context.

        Args:
            input_data: Structured input for brainstorming

        Returns:
            BrainstormingOutput with results and metadata
        """
        self.logger.log_info("Starting enhanced brainstorming session")
        start_time = time.time()
        try:
            # Build enhanced prompt with conversation context
            enhanced_prompt = self._build_enhanced_brainstorming_prompt(input_data)

            # Generate ideas directly with conversation context
            self.logger.log_info(
                f"Making API call to {input_data.model} with prompt length: {len(enhanced_prompt)}"
            )
            response = self.client.generate(
                messages=[
                    {"role": "system", "content": BRAINSTORMING_SYSTEM_PROMPT},
                    {"role": "user", "content": enhanced_prompt},
                ]
            )

            self.logger.log_info(
                f"Received response length: {len(response) if response else 0}"
            )
            self.logger.log_info(
                f"Response content preview: {response[:200] if response else 'None'}"
            )

            content = response
            try:
                ideas = json.loads(content)
                self.logger.log_info(
                    f"Successfully parsed JSON with {len(ideas.get('ideas', []))} ideas"
                )
            except json.JSONDecodeError as e:
                self.logger.log_error(
                    f"Failed to parse JSON response from O3 model: {e}"
                )
                self.logger.log_error(f"Raw response: {content}")
                ideas = {"ideas": [], "categories": []}

            # Process and categorize ideas
            ideas_list = ideas.get("ideas", []) if isinstance(ideas, dict) else ideas
            processed_ideas = self._process_and_categorize_ideas(ideas_list, input_data)

            # Prioritize ideas based on conversation context
            prioritized_ideas = self._prioritize_ideas(processed_ideas, input_data)

            # Extract categories from processed ideas
            categories = self._extract_categories(processed_ideas)

            self.logger.log_info(
                f"Generated {len(processed_ideas)} ideas across {len(categories)} categories"
            )

            # Create enhanced analysis data
            analysis_data: dict[str, Any] = {
                "ideas": processed_ideas,
                "categories": categories,
                "prioritized_ideas": prioritized_ideas,
                "conversation_insights": getattr(
                    input_data, "conversation_insights", {}
                ),
            }

            formats: list[str] | None = (
                [input_data.output_format.value] if input_data.output_format else None
            )
            output_files = self.file_generator.create_analysis_files(
                analysis_data=analysis_data,
                module_name="brainstorming",
                title="Enhanced Brainstorming Session",
                formats=formats,
            )

            duration = time.time() - start_time
            self.logger.log_info(
                f"Enhanced brainstorming session completed in {duration:.2f}s"
            )

            return BrainstormingOutput(
                success=True,
                ideas=processed_ideas,
                categories=categories,
                prioritized_ideas=prioritized_ideas,
                output_files=output_files,
                generation_time=duration,
                model_used=input_data.model,
            )
        except Exception as e:
            self.logger.log_error(f"Error during enhanced brainstorming session: {e}")
            raise

    def _build_enhanced_brainstorming_prompt(
        self, input_data: BrainstormingInput
    ) -> str:
        """Build enhanced prompt with conversation context."""
        conversation_context = ""
        if (
            hasattr(input_data, "conversation_insights")
            and input_data.conversation_insights
        ):
            insights = input_data.conversation_insights
            conversation_context = f"""
Conversation Context:
- Key Themes: {', '.join(insights.get('themes', []))}
- Problems Identified: {', '.join(insights.get('problems', []))}
- Opportunities Mentioned: {', '.join(insights.get('opportunities', []))}
- User Preferences: {', '.join(insights.get('preferences', []))}
- Constraints: {', '.join(insights.get('constraints', []))}
"""

        return f"""
Generate {input_data.idea_count} innovative ideas based on this problem and conversation context:

Problem Statement: {input_data.problem_statement}

{conversation_context}

Requirements:
1. Generate diverse, creative ideas that address the core problem
2. Consider the conversation context and user preferences
3. Categorize ideas by type (e.g., Technical, Business, User Experience, etc.)
4. Include impact assessment (High/Medium/Low) for each idea
5. Provide brief implementation considerations
6. Ensure ideas are actionable and specific

Return ideas in JSON format with structure:
{{
  "ideas": [
    {{
      "id": "idea_001",
      "title": "Idea Title",
      "description": "Detailed description",
      "category": "Technical/Business/UX/etc",
      "impact": "High/Medium/Low",
      "feasibility": "High/Medium/Low",
      "implementation_notes": "Brief implementation considerations"
    }}
  ]
}}
"""

    def _process_and_categorize_ideas(
        self, ideas: list[dict[str, Any]], input_data: BrainstormingInput
    ) -> list[dict[str, Any]]:
        """Process and categorize generated ideas."""
        processed_ideas = []

        for i, idea in enumerate(ideas):
            if isinstance(idea, dict):
                # Ensure idea has required fields
                processed_idea = {
                    "id": idea.get("id", f"idea_{i+1:03d}"),
                    "title": idea.get("title", f"Idea {i+1}"),
                    "description": idea.get("description", ""),
                    "category": idea.get("category", "General"),
                    "impact": idea.get("impact", "Medium"),
                    "feasibility": idea.get("feasibility", "Medium"),
                    "implementation_notes": idea.get("implementation_notes", ""),
                }
                processed_ideas.append(processed_idea)

        return processed_ideas

    def _prioritize_ideas(
        self, ideas: list[dict[str, Any]], input_data: BrainstormingInput
    ) -> list[dict[str, Any]]:
        """Prioritize ideas based on impact and feasibility."""
        # Simple prioritization: High impact + High feasibility = High priority
        for idea in ideas:
            impact_score = {"High": 3, "Medium": 2, "Low": 1}.get(
                idea.get("impact", "Medium"), 2
            )
            feasibility_score = {"High": 3, "Medium": 2, "Low": 1}.get(
                idea.get("feasibility", "Medium"), 2
            )
            idea["priority_score"] = impact_score + feasibility_score

        # Sort by priority score (descending)
        prioritized = sorted(
            ideas, key=lambda x: x.get("priority_score", 0), reverse=True
        )

        # Add priority ranking
        for i, idea in enumerate(prioritized):
            idea["priority_rank"] = i + 1

        return prioritized

    def _extract_categories(self, ideas: list[dict[str, Any]]) -> list[str]:
        """Extract unique categories from ideas."""
        categories = set()
        for idea in ideas:
            category = idea.get("category", "General")
            categories.add(category)
        return sorted(list(categories))


def run_brainstorm(
    input_file: str | None, problem: str | None = None, interactive: bool = False
) -> None:
    """Run brainstorming session."""
    logger = get_logger()
    try:
        if interactive:
            logger.log_info("Starting interactive brainstorming session")
            try:
                input_data = run_interactive_brainstorm_session()
                input_file = save_interactive_input(input_data, "brainstorm")
                print(f"\n📁 Saved conversation input to: {input_file}")
                logger.log_info("Interactive brainstorming session completed")
                return  # Return early - interactive session handles everything
            except Exception as e:
                logger.log_error(f"Error in interactive session: {e}")
                print(f"❌ Interactive session failed: {e}")
                raise
        elif problem:
            logger.log_info(f"Brainstorming solutions for: {problem}")
            input_data = {
                "problem_statement": problem,
                "idea_count": 10,
                "include_prioritization": True,
                "output_format": "json",
                "model": "o4-mini",
                "max_tokens": 16000,
            }
        elif input_file:
            logger.log_info(f"Brainstorming: {input_file}")
            input_data = UniversalInputLoader().load_file_by_extension(input_file)
        else:
            logger.log_error(
                "Either input_file, --problem, or --interactive must be provided"
            )
            sys.exit(1)

        config_manager = ConfigManager()
        inp = BrainstormingInput(**input_data)
        proc = BrainstormingProcessor()
        out = proc.run(inp)
        if not out.success:
            logger.log_error(f"Brainstorming failed: {out.error_message}")
            sys.exit(1)

        next_step_file = save_brainstorm_results_for_next_step(
            out, inp.problem_statement
        )
        logger.log_info(f"Ideas generated: {len(out.ideas)}")
        logger.log_info(f"Brainstorming results saved to: {next_step_file}")
        print(f"\n💡 Brainstorming completed! Generated {len(out.ideas)} ideas.")
        print(f"📁 Results saved to: {next_step_file}")
        print("🔄 Next step: Use 'idea-analyze' to analyze the best ideas")
        print(
            "   Example: python -m main idea-analyze brainstorm_results_YYYYMMDD_HHMMSS.json"
        )
    except Exception as e:
        logger.log_error(f"Error during brainstorming: {e}")
        raise


def main() -> None:
    """
    CLI entry point for the Brainstorming Tool.
    """
    parser = argparse.ArgumentParser(
        description="Brainstorming Tool for O3 Code Generator"
    )
    parser.add_argument("input_file", help="Path to input JSON/YAML file")
    parser.add_argument("--config", help="Path to configuration file", default=None)
    args = parser.parse_args()
    logger = get_logger("main")
    try:
        loader = UniversalInputLoader()
        input_dict = loader.load_file_by_extension(args.input_file)
        input_data = BrainstormingInput(**input_dict)
        config: dict[str, Any] = (
            loader.load_file_by_extension(args.config) if args.config else {}
        )
        processor = BrainstormingProcessor()
        output = processor.run(input_data)
        logger.log_info(
            f"Brainstorming completed: {len(output.ideas)} ideas, files: {output.output_files}"
        )
    except Exception as e:
        logger.log_error(f"Fatal error: {e}")
        raise
    else:
        pass
    finally:
        pass


if __name__ == "__main__":
    main()
else:
    pass
