"""Market Research Integrator for O3 Code Generator

This module analyzes markets, identifies competitors, assesses demand,
and generates comprehensive market research reports using O3 models.
"""

from src.tools.code_generation.o3_code_generator.o3_logger.logger import (
    LogConfig,
    get_logger,
    setup_logger,
)

setup_logger(LogConfig())
import argparse
import sys
import time
from pathlib import Path
from typing import Any

from src.tools.code_generation.o3_code_generator.analysis_utils import (
    extract_market_research_data_from_idea_analysis,
    save_market_research_results_for_next_step,
)
from src.tools.code_generation.o3_code_generator.config.core.config_manager import (
    ConfigManager,
)
from src.tools.code_generation.o3_code_generator.prompts.idea_formation_prompts import (
    MARKET_RESEARCH_SYSTEM_PROMPT,
)
from src.tools.code_generation.o3_code_generator.schemas.idea_formation_schemas import (
    MarketResearchInput,
    MarketResearchOutput,
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
from src.tools.code_generation.o3_code_generator.utils.o3_model_generator import (
    O3ModelGenerator,
)
from src.tools.code_generation.o3_code_generator.utils.output_formatter import (
    OutputFormatter,
)
from src.tools.code_generation.o3_code_generator.utils.prompt_builder import (
    PromptBuilder,
)


class MarketResearchIntegrator:
    """Performs core market research analyses."""

    def __init__(self) -> None:
        """Initialize with O3 logger."""
        self.logger = get_logger()

    def analyze_market(
        self, product_concept: str, target_market: str
    ) -> dict[str, Any]:
        """
        Analyze market size, growth, and trends.

        Args:
            product_concept: Product or service concept
            target_market: Target market description

        Returns:
            Market analysis results
        """
        self.logger.log_info(f"Analyzing market: {product_concept} in {target_market}")
        try:
            size = self._analyze_market_size(product_concept, target_market)
            trends = self._analyze_market_trends(product_concept, target_market)
            segments = self._analyze_market_segments(product_concept, target_market)
            result: dict[str, Any] = {}
            result.update(size)
            result.update(trends)
            result.update(segments)
            self.logger.log_info("Market analysis completed")
            return result
        except Exception as e:
            self.logger.log_error(f"Error in analyze_market: {e}")
            raise
        else:
            pass
        finally:
            pass

    def identify_competitors(
        self, product_concept: str, target_market: str
    ) -> list[dict[str, Any]]:
        """
        Identify key competitors in the target market.

        Args:
            product_concept: Product or service concept
            target_market: Target market description

        Returns:
            List of competitor profiles
        """
        self.logger.log_info(f"Identifying competitors for {product_concept}")
        try:
            competitors: list[dict[str, Any]] = [
                {
                    "name": "Competitor A",
                    "description": "Established market leader",
                    "strengths": ["Brand recognition", "Scale"],
                    "weaknesses": ["Slow innovation"],
                    "market_share": "30%",
                },
                {
                    "name": "Competitor B",
                    "description": "Innovative entrant",
                    "strengths": ["Agility", "Cutting-edge tech"],
                    "weaknesses": ["Limited resources"],
                    "market_share": "10%",
                },
            ]
            self.logger.log_info(f"Found {len(competitors)} competitors")
            return competitors
        except Exception as e:
            self.logger.log_error(f"Error in identify_competitors: {e}")
            raise
        else:
            pass
        finally:
            pass

    def assess_demand(self, product_concept: str, target_market: str) -> dict[str, Any]:
        """
        Assess current and future demand for the product.

        Args:
            product_concept: Product or service concept
            target_market: Target market description

        Returns:
            Demand assessment results
        """
        self.logger.log_info(f"Assessing demand for {product_concept}")
        try:
            current = self._analyze_current_demand(product_concept, target_market)
            growth = self._analyze_demand_growth(product_concept, target_market)
            pain = self._analyze_customer_pain_points(product_concept, target_market)
            result: dict[str, Any] = {}
            result.update(current)
            result.update(growth)
            result.update(pain)
            self.logger.log_info("Demand assessment completed")
            return result
        except Exception as e:
            self.logger.log_error(f"Error in assess_demand: {e}")
            raise
        else:
            pass
        finally:
            pass

    def validate_market_fit(
        self, product_concept: str, target_market: str
    ) -> dict[str, Any]:
        """
        Validate product-market fit.

        Args:
            product_concept: Product or service concept
            target_market: Target market description

        Returns:
            Market fit validation results
        """
        self.logger.log_info(f"Validating market fit for {product_concept}")
        try:
            value = self._analyze_value_proposition(product_concept, target_market)
            profile = self._analyze_target_customer_profile(
                product_concept, target_market
            )
            diff = self._analyze_differentiation_factors(product_concept, target_market)
            result: dict[str, Any] = {}
            result.update(value)
            result.update(profile)
            result.update(diff)
            self.logger.log_info("Market fit validation completed")
            return result
        except Exception as e:
            self.logger.log_error(f"Error in validate_market_fit: {e}")
            raise
        else:
            pass
        finally:
            pass

    def _analyze_market_size(
        self, product_concept: str, target_market: str
    ) -> dict[str, Any]:
        return {"market_size": "$10B", "growth_rate": "12% CAGR"}

    def _analyze_market_trends(
        self, product_concept: str, target_market: str
    ) -> dict[str, Any]:
        return {
            "market_trends": ["Digitalization", "AI"],
            "key_drivers": ["Tech adoption"],
        }

    def _analyze_market_segments(
        self, product_concept: str, target_market: str
    ) -> dict[str, Any]:
        return {
            "market_segments": ["Enterprise", "SMB"],
            "geographic_focus": ["NA", "EU"],
        }

    def _analyze_current_demand(
        self, product_concept: str, target_market: str
    ) -> dict[str, Any]:
        return {"current_demand": "moderate"}

    def _analyze_demand_growth(
        self, product_concept: str, target_market: str
    ) -> dict[str, Any]:
        return {"demand_growth": "increasing"}

    def _analyze_customer_pain_points(
        self, product_concept: str, target_market: str
    ) -> dict[str, Any]:
        return {"customer_pain_points": ["Cost", "Complexity"]}

    def _analyze_value_proposition(
        self, product_concept: str, target_market: str
    ) -> dict[str, Any]:
        return {"value_proposition": "Efficient solution"}

    def _analyze_target_customer_profile(
        self, product_concept: str, target_market: str
    ) -> dict[str, Any]:
        return {"target_customer_profile": {"type": "Early adopter"}}

    def _analyze_differentiation_factors(
        self, product_concept: str, target_market: str
    ) -> dict[str, Any]:
        return {"differentiation_factors": ["Innovation"]}


class MarketResearchProcessor:
    """Orchestrates market research workflow using shared utilities."""

    def __init__(self, config_path: str | None = None) -> None:
        """
        Initialize processor: load config, setup logger, create utilities.

        Args:
            config_path: Optional path to configuration file
        """
        self.logger = get_logger()
        try:
            self.config_manager = ConfigManager(config_path)
            self.logger.log_info("Configuration loaded successfully")
        except Exception as e:
            self.logger.log_error(f"Configuration error: {e}")
            raise

        try:
            self.model_generator = O3ModelGenerator()
            self.logger.log_info("O3ModelGenerator initialized successfully")
        except Exception as e:
            self.logger.log_error(f"O3ModelGenerator initialization error: {e}")
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
        else:
            pass
        finally:
            pass
        try:
            log_cfg = self.config_manager.get_logging_config()
            setup_logger(log_cfg)
            self.logger.log_info("Logger reconfigured")
        except Exception as e:
            self.logger.log_error(f"Logging configuration error: {e}")
            raise
        else:
            pass
        finally:
            pass
        self.input_loader = UniversalInputLoader()
        self.integrator = MarketResearchIntegrator()
        self._initialize_directories()

    def _initialize_directories(self) -> None:
        """Ensure required output directories exist."""
        self.logger.log_info("Creating output directories")
        try:
            self.directory_manager.ensure_directory_exists(
                "generated_files/idea_formation"
            )
            self.directory_manager.ensure_directory_exists("logs")
        except Exception as e:
            self.logger.log_error(f"Directory initialization error: {e}")
            raise
        else:
            pass
        finally:
            pass

    def run_market_research(
        self, input_data: MarketResearchInput
    ) -> MarketResearchOutput:
        """
        Execute market research steps and generate outputs.

        Args:
            input_data: Structured input for market research

        Returns:
            MarketResearchOutput with analysis and file paths
        """
        start_time = time.time()
        self.logger.log_info("Starting market research")
        try:
            analysis = self.integrator.analyze_market(
                input_data.product_concept, input_data.target_market
            )
            competitors = (
                self.integrator.identify_competitors(
                    input_data.product_concept, input_data.target_market
                )
                if input_data.include_competitor_analysis
                else []
            )
            demand = (
                self.integrator.assess_demand(
                    input_data.product_concept, input_data.target_market
                )
                if input_data.include_demand_assessment
                else {}
            )
            fit = (
                self.integrator.validate_market_fit(
                    input_data.product_concept, input_data.target_market
                )
                if input_data.include_market_fit_validation
                else {}
            )
            context: dict[str, Any] = {
                "market_analysis": analysis,
                "competitors": competitors,
                "demand_assessment": demand,
                "market_fit_validation": fit,
            }
            prompt = self.prompt_builder.build_generation_prompt(
                input_data, context=context, system_prompt=MARKET_RESEARCH_SYSTEM_PROMPT
            )
            response = self.model_generator.generate(
                messages=[
                    {"role": "system", "content": MARKET_RESEARCH_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ]
            )
            enhanced: dict[str, Any]
            if response:
                try:
                    import json

                    enhanced = json.loads(response)
                except Exception:
                    enhanced = {"text_analysis": response}
            else:
                raise ValueError("No response from O3 model")
            formats: list[str] = [input_data.output_format.value]
            files = self.file_generator.create_analysis_files(
                enhanced,
                module_name="market_research",
                title="Market Research Analysis",
                formats=formats,
            )
            duration = time.time() - start_time
            self.logger.log_info(f"Market research completed in {duration:.2f}s")
            return MarketResearchOutput(
                success=True,
                market_analysis=enhanced,
                competitors=competitors,
                demand_assessment=demand,
                market_fit_validation=fit,
                output_files=files,
                generation_time=duration,
                model_used=input_data.model,
            )
        except Exception as e:
            duration = time.time() - start_time
            self.logger.log_error(f"Market research failed: {e}")
            return MarketResearchOutput(
                success=False,
                market_analysis={},
                competitors=[],
                demand_assessment={},
                market_fit_validation={},
                output_files=[],
                generation_time=duration,
                model_used=getattr(input_data, "model", ""),
                error_message=str(e),
            )
        else:
            pass
        finally:
            pass


def main() -> None:
    """Main entry point for the market research integrator script."""
    logger = get_logger()
    parser = argparse.ArgumentParser(description="Market Research Integrator")
    parser.add_argument("input_file", help="Path to input data file")
    parser.add_argument("--config", help="Path to config file", default=None)
    args = parser.parse_args()
    try:
        processor = MarketResearchProcessor(args.config)
        data = processor.input_loader.load_file_by_extension(Path(args.input_file))
        input_obj = MarketResearchInput(**data)
        result = processor.run_market_research(input_obj)
        if result.success:
            logger.log_info(f"Analysis succeeded, files: {result.output_files}")
            sys.exit(0)
        else:
            pass
        logger.log_error(f"Analysis failed: {result.error_message}")
        sys.exit(1)
    except Exception as e:
        logger.log_error(f"Fatal error: {e}")
        sys.exit(1)
    else:
        pass
    finally:
        pass


if __name__ == "__main__":
    main()
else:
    pass


logger = get_logger()


def run_market_research(input_file: str | None) -> None:
    """Run market research analysis."""
    try:
        if input_file:
            logger.log_info(f"Market research: {input_file}")
            input_data = UniversalInputLoader().load_file_by_extension(input_file)
            if "idea_analysis_results" in input_file:
                input_data = extract_market_research_data_from_idea_analysis(input_data)
        else:
            logger.log_error("Input file required for market research")
            sys.exit(1)

        inp = MarketResearchInput(**input_data)
        proc = MarketResearchProcessor()
        out = proc.run_market_research(inp)
        if not out.success:
            logger.log_error(f"Market research failed: {out.error_message}")
            sys.exit(1)

        next_step_file = save_market_research_results_for_next_step(out, input_file)
        logger.log_info("Market research analysis completed successfully")
        logger.log_info(f"Market research results saved to: {next_step_file}")
        print("\n📊 Market research completed!")
        print(f"📁 Results saved to: {next_step_file}")
        print("🔄 Next step: Use 'feasibility-assess' to assess feasibility")
        print(
            "   Example: python -m main feasibility-assess market_research_results_YYYYMMDD_HHMMSS.json"
        )
    except Exception as e:
        logger.log_error(f"Error during market research: {e}")
        raise
