"""
Demo script for the Auto Rules Generation System

Shows how to use the system to generate rules based on codebase patterns.
"""

from pathlib import Path
import sys

from src.tools.code_generation.o3_code_generator.auto_rules_generation.auto_rules_generator import (
    AutoRulesGenerator,
)
from src.tools.code_generation.o3_code_generator.o3_logger.logger import (
    LogConfig,
    get_logger,
    setup_logger,
)


def demo_auto_rules_generation():
    """Demonstrate the auto rules generation system."""
    # Setup logging with debug enabled by default
    config = LogConfig(level="DEBUG", enable_debug_log=True)
    setup_logger(config)
    logger = get_logger()

    logger.log_info("🚀 Starting Auto Rules Generation Demo")
    logger.log_info(f"📁 Working directory: {Path.cwd()}")
    logger.log_info(f"🐍 Python path: {sys.path[:3]}...")  # Show first 3 entries

    try:
        # Initialize the auto rules generator
        # Target a smaller scope for testing - just the auto_rules_generation directory
        base_path = Path(
            "src/tools/code_generation/o3_code_generator/auto_rules_generation"
        )
        output_dir = Path(
            "src/tools/code_generation/o3_code_generator/auto_rules_generation/demo_output"
        )

        generator = AutoRulesGenerator(base_path=base_path, output_dir=output_dir)

        # Generate rules
        logger.log_info("📊 Generating rules from codebase patterns...")
        result = generator.generate_rules()

        # Display results
        logger.log_info("✅ Auto Rules Generation Complete!")
        logger.log_info(f"⏱️  Execution Time: {result.execution_time:.2f} seconds")

        if result.success:
            logger.log_info(f"📋 Generated {len(result.generated_rules)} rules")
            logger.log_info(f"✅ Valid Rules: {result.validation_report.valid_rules}")
            logger.log_info(
                f"❌ Invalid Rules: {result.validation_report.invalid_rules}"
            )
            logger.log_info(
                f"📈 Average Confidence: {result.validation_report.average_confidence:.2f}"
            )
            logger.log_info(
                f"🛡️  Safety Score: {result.validation_report.safety_score:.2f}"
            )

            logger.log_info("\n📁 Generated Output Files:")
            for output_file in result.output_files:
                logger.log_info(f"  📄 {output_file}")

            logger.log_info("\n📝 Summary:")
            logger.log_info(result.summary)

            logger.log_info("\n💡 Recommendations:")
            for rec in result.recommendations:
                logger.log_info(f"  • {rec}")

            # Display example rules
            if result.generated_rules:
                logger.log_info("\n🎯 Example Generated Rules:")
                for i, rule in enumerate(result.generated_rules[:3], 1):
                    logger.log_info(f"\n  Rule {i}: {rule.rule_name}")
                    logger.log_info(f"    Type: {rule.rule_type.upper()}")
                    logger.log_info(f"    Text: {rule.rule_text}")
                    logger.log_info(f"    Confidence: {rule.confidence_score:.2f}")
                    logger.log_info(f"    Pattern: {rule.pattern_basis}")
        else:
            logger.log_error("❌ Generation failed!")
            logger.log_error(result.summary)

    except Exception as e:
        logger.log_error(f"💥 Demo failed with error: {e}")
        import traceback

        logger.log_error(traceback.format_exc())


if __name__ == "__main__":
    demo_auto_rules_generation()
