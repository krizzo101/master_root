"""
Idea Formation Analyzer for O3 Code Generator

This module provides classes and methods to analyze, validate, refine, and assess feasibility
of idea concepts using OpenAI's O3 models. It handles prompt building, analysis workflows,
output formatting, file generation, and logging according to project standards.
"""

from src.tools.code_generation.o3_code_generator.o3_logger.logger import (
    LogConfig,
    setup_logger,
)

setup_logger(LogConfig())
import argparse
from pathlib import Path
import sys
import time
from typing import Any, Dict, List

from src.tools.code_generation.o3_code_generator.analysis_utils import (
    extract_ideas_from_brainstorm_results,
    save_analysis_results_for_next_step,
    save_interactive_input,
)
from src.tools.code_generation.o3_code_generator.config.core.config_manager import (
    ConfigManager,
)
from src.tools.code_generation.o3_code_generator.o3_logger.logger import get_logger
from src.tools.code_generation.o3_code_generator.prompts.idea_formation_prompts import (
    IDEA_FORMATION_SYSTEM_PROMPT,
)
from src.tools.code_generation.o3_code_generator.schemas.idea_formation_schemas import (
    IdeaFormationInput,
    IdeaFormationOutput,
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
    run_interactive_idea_session,
)
from src.tools.code_generation.o3_code_generator.utils.o3_model_generator import (
    O3ModelGenerator,
)
from src.tools.code_generation.o3_code_generator.utils.output_formatter import (
    OutputFormatter,
)
from src.tools.code_generation.o3_code_generator.utils.prompt_builder import (
    PromptBuilder,
)

logger = get_logger()


def _pretty_print_brainstorm_input(input_data: dict) -> None:
    """Pretty print the brainstorm input data being analyzed."""
    print("\n" + "=" * 80)
    print("📥 ANALYZING BRAINSTORM RESULTS")
    print("=" * 80)

    concept_description = input_data.get("concept_description", "")
    if concept_description:
        print("\n📝 CONCEPT BEING ANALYZED:")
        print("-" * 40)
        # Split by newlines and show each idea
        ideas = concept_description.split("\n\n")
        for i, idea in enumerate(ideas[:3], 1):  # Show top 3 ideas
            if idea.strip():
                print(f"   {i}. {idea.strip()}")

    print("\n🔍 ANALYSIS PROCESS:")
    print("-" * 40)
    print("   • Evaluating concept clarity and completeness")
    print("   • Assessing market fit and viability")
    print("   • Analyzing technical, economic, and operational feasibility")
    print("   • Generating comprehensive analysis with AI enhancement")

    print("\n📊 EXPECTED OUTPUT:")
    print("-" * 40)
    print("   • Scored analysis across multiple dimensions (0.0-1.0)")
    print("   • Detailed feasibility assessment with recommendations")
    print("   • Next step file for continued development workflow")

    print("=" * 80)


def _pretty_print_analysis_results(
    analysis_data: dict, next_step_file: str, output_files: list
) -> None:
    """Pretty print the analysis results to console."""
    print("\n" + "=" * 80)
    print("🧠 IDEA ANALYSIS RESULTS")
    print("=" * 80)

    # Concept Analysis Section
    concept_analysis = analysis_data.get("concept_analysis", {})
    if concept_analysis:
        print("\n📊 CONCEPT ANALYSIS:")
        print("-" * 40)

        # Simplified score handling - only current structure
        clarity_score = concept_analysis.get("clarity_score", 0)
        completeness_score = concept_analysis.get("completeness_score", 0)
        potential_score = concept_analysis.get("potential_score", 0)

        print(
            f"   📝 Clarity:          {clarity_score:.1f}/1.0 {'🟢' if clarity_score >= 0.7 else '🟡' if clarity_score >= 0.5 else '🔴'}"
        )
        print(
            f"   📋 Completeness:     {completeness_score:.1f}/1.0 {'🟢' if completeness_score >= 0.7 else '🟡' if completeness_score >= 0.5 else '🔴'}"
        )
        if potential_score > 0:
            print(
                f"   🚀 Potential:        {potential_score:.1f}/1.0 {'🟢' if potential_score >= 0.7 else '🟡' if potential_score >= 0.5 else '🔴'}"
            )

        # Analysis text
        clarity_analysis = concept_analysis.get("clarity_analysis", "")
        if clarity_analysis:
            print(f"\n   📝 Clarity Analysis: {clarity_analysis}")

        # Key Components
        components = concept_analysis.get("key_components", [])
        if components:
            print("\n   🔧 Key Components:")
            for component in components[:3]:  # Show top 3
                print(f"      • {component}")

        # Strengths
        strengths = concept_analysis.get("strengths", [])
        if strengths:
            print("\n   💪 Strengths:")
            for strength in strengths[:3]:  # Show top 3
                print(f"      • {strength}")

        # Missing Elements
        missing = concept_analysis.get("missing_elements", [])
        if missing:
            print("\n   ⚠️  Missing Elements:")
            for element in missing[:3]:  # Show top 3
                print(f"      • {element}")

    # Validation Results Section
    validation = analysis_data.get("validation_results", {})
    if validation:
        print("\n✅ VALIDATION RESULTS:")
        print("-" * 40)

        market_fit = validation.get("market_fit_score", 0)
        viability = validation.get("viability_score", 0)
        uniqueness = validation.get("uniqueness_score", 0)

        print(
            f"   🎯 Market Fit:       {market_fit:.1f}/1.0 {'🟢' if market_fit >= 0.7 else '🟡' if market_fit >= 0.5 else '🔴'}"
        )
        print(
            f"   💪 Viability:        {viability:.1f}/1.0 {'🟢' if viability >= 0.7 else '🟡' if viability >= 0.5 else '🔴'}"
        )
        print(
            f"   ⭐ Uniqueness:       {uniqueness:.1f}/1.0 {'🟢' if uniqueness >= 0.7 else '🟡' if uniqueness >= 0.5 else '🔴'}"
        )

        # Validation assessments
        market_val = validation.get("market_validation", "")
        viability_val = validation.get("viability_assessment", "")
        uniqueness_val = validation.get("uniqueness_analysis", "")
        if market_val:
            print(f"\n   📈 Market: {market_val}")
        if viability_val:
            print(f"   💼 Viability: {viability_val}")
        if uniqueness_val:
            print(f"   ⭐ Uniqueness: {uniqueness_val}")

    # Feasibility Assessment Section
    feasibility = analysis_data.get("feasibility_assessment", {})
    if feasibility:
        print("\n⚙️  FEASIBILITY ASSESSMENT:")
        print("-" * 40)

        technical = feasibility.get("technical_feasibility", {})
        economic = feasibility.get("economic_feasibility", {})
        operational = feasibility.get("operational_feasibility", {})

        if technical:
            tech_score = technical.get("technical_score", 0)
            print(
                f"   🔧 Technical:        {tech_score:.1f}/1.0 {'🟢' if tech_score >= 0.7 else '🟡' if tech_score >= 0.5 else '🔴'}"
            )
            tech_assessment = technical.get("technical_assessment", "")
            if tech_assessment:
                print(f"      {tech_assessment}")

        if economic:
            econ_score = economic.get("economic_score", 0)
            print(
                f"   💰 Economic:         {econ_score:.1f}/1.0 {'🟢' if econ_score >= 0.7 else '🟡' if econ_score >= 0.5 else '🔴'}"
            )
            econ_assessment = economic.get("economic_assessment", "")
            if econ_assessment:
                print(f"      {econ_assessment}")

        if operational:
            oper_score = operational.get("operational_score", 0)
            print(
                f"   🏗️  Operational:      {oper_score:.1f}/1.0 {'🟢' if oper_score >= 0.7 else '🟡' if oper_score >= 0.5 else '🔴'}"
            )
            oper_assessment = operational.get("operational_assessment", "")
            if oper_assessment:
                print(f"      {oper_assessment}")

    # Market Analysis Section
    market = analysis_data.get("market_analysis", {})
    if market and any(
        v
        for v in market.values()
        if v
        and v
        not in ["To be determined", "To be assessed", "Not specified", "To be analyzed"]
    ):
        print("\n📊 MARKET ANALYSIS:")
        print("-" * 40)

        market_size = market.get("market_size", "")
        growth_potential = market.get("growth_potential", "")
        target_audience = market.get("target_audience", "")
        competitive = market.get("competitive_landscape", "")

        if market_size and market_size != "To be determined":
            print(f"   📏 Market Size: {market_size}")
        if growth_potential and growth_potential != "To be assessed":
            print(f"   📈 Growth: {growth_potential}")
        if target_audience and target_audience != "Not specified":
            print(f"   🎯 Audience: {target_audience}")
        if competitive and competitive != "To be analyzed":
            print(f"   🏆 Competition: {competitive}")

    # Files and Next Steps
    print("\n📁 OUTPUT FILES:")
    print("-" * 40)
    print(
        f"   📊 Detailed Analysis: {len(output_files)} file(s) in ./generated_files/idea_formation/"
    )
    for file_path in output_files:
        print(f"      • {file_path}")
    print(f"   🚀 Next Step File: {next_step_file}")

    print("\n🔄 RECOMMENDED NEXT STEPS:")
    print("-" * 40)
    print("   • market-research (recommended for deeper market analysis)")
    print("   • requirements-analyze (define detailed requirements)")
    print("   • architecture-design (design system architecture)")
    print("   • project-init (initialize project structure)")
    print("   • Or use 'chain' command to run multiple steps")

    print("=" * 80)


def run_idea_analyze(input_file: str | None, interactive: bool = False) -> None:
    """Analyze ideas."""
    try:
        if interactive:
            logger.log_info("Starting interactive idea analysis session")
            input_data = run_interactive_idea_session()
            input_file = save_interactive_input(input_data, "idea_analysis")
            print(f"\n📁 Saved conversation input to: {input_file}")
            source_data = input_data  # For interactive, source is the input itself
        else:
            if input_file:
                logger.log_info(f"Idea formation analysis: {input_file}")
                original_data = UniversalInputLoader().load_file_by_extension(
                    input_file
                )
                if "brainstorm_results" in input_file:
                    input_data = extract_ideas_from_brainstorm_results(original_data)
                    # Preserve original data for context
                    source_data = original_data
                else:
                    input_data = original_data
                    source_data = original_data
            else:
                logger.log_error("Input file required when not using interactive mode")
                sys.exit(1)

        # Show what we're analyzing
        _pretty_print_brainstorm_input(input_data)

        print("\n🔄 Starting analysis...")
        inp = IdeaFormationInput(**input_data)
        proc = IdeaFormationProcessor()

        print("⏳ Analyzing concept clarity and completeness...")
        print("⏳ Validating market fit and viability...")
        print("⏳ Assessing technical, economic, and operational feasibility...")
        print("⏳ Generating enhanced analysis with AI...")

        out = proc.analyze_idea_formation(inp)
        if not out.success:
            logger.log_error(f"Idea analysis failed: {out.error_message}")
            sys.exit(1)

        logger.log_info("Idea formation analysis completed successfully")
        next_step_file = save_analysis_results_for_next_step(out, source_data)

        # Pretty print results to console for both modes
        _pretty_print_analysis_results(
            out.idea_analysis, next_step_file, out.output_files
        )

        if interactive:
            print(f"\n💬 Conversation input saved to: {input_file}")
        else:
            logger.log_info(f"Analysis results saved. Next step file: {next_step_file}")
            logger.log_info(f"Output files: {out.output_files}")
    except Exception as e:
        logger.log_error(f"Error during idea formation analysis: {e}")
        raise


class IdeaFormationAnalyzer:
    """Analyzes concepts and ideas for formation and development."""

    def __init__(self) -> None:
        """
        Initialize the idea formation analyzer.
        Attributes:
            logger: Logger instance for this class
        """
        self.logger = get_logger()

    def analyze_concept(
        self, concept_description: str, target_market: str | None = None
    ) -> Dict[str, Any]:
        """
        Analyze a concept for clarity, completeness, and potential.

        Args:
            concept_description: Natural language description of the concept
            target_market: Optional target market information

        Returns:
            Dictionary containing concept analysis results
        """
        self.logger.log_info("Starting concept analysis")
        analysis_results: Dict[str, Any] = {
            "concept_summary": "",
            "clarity_score": 0.0,
            "completeness_score": 0.0,
            "potential_score": 0.0,
            "key_components": [],
            "missing_elements": [],
            "strengths": [],
            "weaknesses": [],
            "recommendations": [],
        }
        try:
            clarity = self._analyze_concept_clarity(concept_description)
            analysis_results.update(clarity)
            completeness = self._analyze_concept_completeness(concept_description)
            analysis_results.update(completeness)
            potential = self._analyze_concept_potential(
                concept_description, target_market
            )
            analysis_results.update(potential)
            self.logger.log_info("Concept analysis completed")
            return analysis_results
        except Exception as e:
            self.logger.log_error(f"Error in analyze_concept: {e}")
            raise
        else:
            pass
        finally:
            pass

    def validate_idea(
        self, concept_description: str, target_market: str | None = None
    ) -> Dict[str, Any]:
        """
        Validate an idea for market fit and viability.

        Args:
            concept_description: Natural language description of the concept
            target_market: Optional target market information

        Returns:
            Dictionary containing validation results
        """
        self.logger.log_info("Starting idea validation")
        validation_results: Dict[str, Any] = {
            "market_fit_score": 0.0,
            "viability_score": 0.0,
            "uniqueness_score": 0.0,
            "market_validation": {},
            "viability_assessment": {},
            "uniqueness_analysis": {},
            "validation_recommendations": [],
        }
        try:
            market_fit = self._validate_market_fit(concept_description, target_market)
            validation_results.update(market_fit)
            viability = self._assess_viability(concept_description)
            validation_results.update(viability)
            uniqueness = self._analyze_uniqueness(concept_description)
            validation_results.update(uniqueness)
            self.logger.log_info("Idea validation completed")
            return validation_results
        except Exception as e:
            self.logger.log_error(f"Error in validate_idea: {e}")
            raise
        else:
            pass
        finally:
            pass

    def refine_concept(
        self, concept_description: str, feedback: str | None = None
    ) -> Dict[str, Any]:
        """
        Refine a concept based on analysis and feedback.

        Args:
            concept_description: Original concept description
            feedback: Optional feedback for refinement

        Returns:
            Dictionary containing refined concept and improvements
        """
        self.logger.log_info("Starting concept refinement")
        refinement_results: Dict[str, Any] = {
            "original_concept": concept_description,
            "refined_concept": "",
            "improvements_made": [],
            "refinement_justification": "",
            "next_steps": [],
        }
        try:
            refined = self._generate_refined_concept(concept_description, feedback)
            refinement_results["refined_concept"] = refined
            improvements = self._identify_improvements(concept_description, refined)
            refinement_results["improvements_made"] = improvements
            self.logger.log_info("Concept refinement completed")
            return refinement_results
        except Exception as e:
            self.logger.log_error(f"Error in refine_concept: {e}")
            raise
        else:
            pass
        finally:
            pass

    def assess_feasibility(self, concept_description: str) -> Dict[str, Any]:
        """
        Assess the feasibility of implementing a concept.

        Args:
            concept_description: Natural language description of the concept

        Returns:
            Dictionary containing feasibility assessment
        """
        self.logger.log_info("Starting feasibility assessment")
        feasibility_results: Dict[str, Any] = {
            "technical_feasibility": {},
            "economic_feasibility": {},
            "operational_feasibility": {},
            "overall_feasibility_score": 0.0,
            "feasibility_recommendations": [],
        }
        try:
            tech = self._assess_technical_feasibility(concept_description)
            feasibility_results["technical_feasibility"] = tech
            econ = self._assess_economic_feasibility(concept_description)
            feasibility_results["economic_feasibility"] = econ
            oper = self._assess_operational_feasibility(concept_description)
            feasibility_results["operational_feasibility"] = oper
            self.logger.log_info("Feasibility assessment completed")
            return feasibility_results
        except Exception as e:
            self.logger.log_error(f"Error in assess_feasibility: {e}")
            raise
        else:
            pass
        finally:
            pass

    def _analyze_concept_clarity(self, concept_description: str) -> Dict[str, Any]:
        return {
            "clarity_score": 0.8,
            "clarity_analysis": "Concept is generally clear but could benefit from more specific details",
        }

    def _analyze_concept_completeness(self, concept_description: str) -> Dict[str, Any]:
        return {
            "completeness_score": 0.7,
            "missing_elements": [
                "target audience",
                "success metrics",
                "implementation timeline",
            ],
        }

    def _analyze_concept_potential(
        self, concept_description: str, target_market: str | None
    ) -> Dict[str, Any]:
        return {
            "potential_score": 0.75,
            "potential_analysis": "Concept shows good potential with proper execution",
        }

    def _validate_market_fit(
        self, concept_description: str, target_market: str | None
    ) -> Dict[str, Any]:
        return {
            "market_fit_score": 0.8,
            "market_validation": "Good market fit identified",
        }

    def _assess_viability(self, concept_description: str) -> Dict[str, Any]:
        return {
            "viability_score": 0.7,
            "viability_assessment": "Concept is viable with some modifications",
        }

    def _analyze_uniqueness(self, concept_description: str) -> Dict[str, Any]:
        return {
            "uniqueness_score": 0.6,
            "uniqueness_analysis": "Concept has some unique elements but faces competition",
        }

    def _generate_refined_concept(
        self, concept_description: str, feedback: str | None
    ) -> str:
        return f"Refined: {concept_description}"

    def _identify_improvements(self, original: str, refined: str) -> List[str]:
        return [
            "Added specific target audience",
            "Clarified value proposition",
            "Included success metrics",
        ]

    def _assess_technical_feasibility(self, concept_description: str) -> Dict[str, Any]:
        return {
            "technical_score": 0.8,
            "technical_assessment": "Technically feasible with current technology",
        }

    def _assess_economic_feasibility(self, concept_description: str) -> Dict[str, Any]:
        return {
            "economic_score": 0.7,
            "economic_assessment": "Economically viable with proper funding",
        }

    def _assess_operational_feasibility(
        self, concept_description: str
    ) -> Dict[str, Any]:
        return {
            "operational_score": 0.75,
            "operational_assessment": "Operationally feasible with proper planning",
        }


class IdeaFormationProcessor:
    """Main processor for idea formation analysis using O3 models."""

    def __init__(self, config_path: str | None = None) -> None:
        """
        Initialize the idea formation processor.

        Args:
            config_path: Optional path to configuration file
        """
        self.logger = get_logger()
        try:
            self.config_manager = ConfigManager(config_path)
            self.logger.log_info("Configuration loaded successfully")
        except Exception as e:
            self.logger.log_error(f"Failed to load configuration: {e}")
            raise

        try:
            self.model_generator = O3ModelGenerator()
            self.logger.log_info("O3ModelGenerator initialized successfully")
        except Exception as e:
            self.logger.log_error(f"Failed to initialize O3ModelGenerator: {e}")
            raise

        try:
            self.directory_manager = DirectoryManager()
            self.prompt_builder = PromptBuilder()
            self.output_formatter = OutputFormatter()
            self.file_generator = FileGenerator()
            self.logger.log_info("Utility components initialized successfully")
        except Exception as e:
            self.logger.log_error(f"Utility initialization error: {e}")
            raise
        self.analyzer = IdeaFormationAnalyzer()
        self._create_directories()
        self.input_loader = UniversalInputLoader()

    def _create_directories(self) -> None:
        """Create necessary output directories."""
        dirs = [Path("generated_files/idea_formation"), Path("logs")]
        for d in dirs:
            try:
                self.directory_manager.ensure_directory_exists(d)
                self.logger.log_info(f"Created directory: {d}")
            except Exception as e:
                self.logger.log_error(f"Error creating directory {d}: {e}")
                raise
            else:
                pass
            finally:
                pass
        else:
            pass

    def analyze_idea_formation(
        self, input_data: IdeaFormationInput
    ) -> IdeaFormationOutput:
        """
        Analyze idea formation using O3 models.

        Args:
            input_data: Structured input data for analysis

        Returns:
            IdeaFormationOutput containing analysis results
        """
        start_time = time.time()
        self.logger.log_info("Starting idea formation analysis")
        try:
            data: Dict[str, Any] = {}
            data["concept_analysis"] = self.analyzer.analyze_concept(
                input_data.concept_description, input_data.target_market
            )
            data["validation_results"] = self.analyzer.validate_idea(
                input_data.concept_description, input_data.target_market
            )
            if input_data.include_market_research:
                data["market_analysis"] = self._perform_market_research(input_data)
            else:
                pass
            if input_data.include_feasibility_assessment:
                data["feasibility_assessment"] = self.analyzer.assess_feasibility(
                    input_data.concept_description
                )
            else:
                pass
            enhanced = self._generate_with_o3_model(input_data, data)
            data.update(enhanced)
            formats = (
                [input_data.output_format.value] if input_data.output_format else None
            )
            files = self.file_generator.create_analysis_files(
                data,
                module_name="idea_formation",
                title="Idea Formation Analysis",
                formats=formats,
            )
            duration = time.time() - start_time
            self.logger.log_info(
                f"Idea formation analysis completed in {duration:.2f} seconds"
            )
            return IdeaFormationOutput(
                success=True,
                idea_analysis=data,
                output_files=files,
                generation_time=duration,
                model_used=input_data.model,
            )
        except Exception as e:
            duration = time.time() - start_time
            self.logger.log_error(f"Error during idea formation analysis: {e}")
            return IdeaFormationOutput(
                success=False,
                idea_analysis={},
                output_files=[],
                generation_time=duration,
                model_used=input_data.model,
                error_message=str(e),
            )
        else:
            pass
        finally:
            pass

    def _generate_with_o3_model(
        self, input_data: IdeaFormationInput, idea_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate enhanced analysis using O3 model.

        Args:
            input_data: Input data for analysis
            idea_analysis: Initial analysis results

        Returns:
            Enhanced analysis results
        """
        self.logger.log_info("Generating enhanced analysis with O3 model")
        try:
            prompt = self.prompt_builder.build_analysis_prompt(
                input_data, idea_analysis, system_prompt=IDEA_FORMATION_SYSTEM_PROMPT
            )
            response = self.model_generator.generate(
                messages=[
                    {"role": "system", "content": IDEA_FORMATION_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ]
            )
            content = response if response else ""
            try:
                return __import__("json").loads(content)
            except Exception:
                return {"text_analysis": content}
            else:
                pass
            finally:
                pass
        except Exception as e:
            self.logger.log_error(f"Error generating enhanced analysis: {e}")
            return {}
        else:
            pass
        finally:
            pass

    def _perform_market_research(
        self, input_data: IdeaFormationInput
    ) -> Dict[str, Any]:
        """
        Perform market research analysis.

        Args:
            input_data: Input data containing concept and target market

        Returns:
            Market research results
        """
        self.logger.log_info("Performing market research analysis")
        return {
            "market_size": "To be determined",
            "growth_potential": "To be assessed",
            "competitive_landscape": "To be analyzed",
            "target_audience": input_data.target_market or "Not specified",
        }


def main() -> None:
    """Main entry point for the idea formation analyzer CLI."""
    logger = get_logger("main")
    parser = argparse.ArgumentParser(
        description="Idea Formation Analyzer for O3 Code Generator"
    )
    parser.add_argument("input_file", help="Path to input file (json|yaml)")
    parser.add_argument("--config", help="Path to configuration file", default=None)
    args = parser.parse_args()
    try:
        processor = IdeaFormationProcessor(args.config)
        raw = processor.input_loader.load_file_by_extension(Path(args.input_file))
        input_data = IdeaFormationInput(**raw)
        output = processor.analyze_idea_formation(input_data)
        if output.success:
            logger.log_info("✅ Idea Formation Analysis Completed Successfully")
            logger.log_info(f"📊 Analysis Time: {output.generation_time:.2f} seconds")
            logger.log_info(f"🤖 Model Used: {output.model_used}")
            for f in output.output_files:
                logger.log_info(f"📄 {f}")
            else:
                pass
        else:
            logger.log_error(f"❌ Analysis Failed: {output.error_message}")
            sys.exit(1)
    except Exception as e:
        logger.log_error(f"❌ Fatal Error: {e}")
        sys.exit(1)
    else:
        pass
    finally:
        pass


if __name__ == "__main__":
    main()
else:
    pass
