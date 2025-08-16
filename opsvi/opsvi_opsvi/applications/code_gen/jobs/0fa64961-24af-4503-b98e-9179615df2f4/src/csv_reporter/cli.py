"""
CLI interface for the CSV Report Generator tool.
Handles command-line parsing, entry point logic, and command dispatch.
"""
import sys
import argparse
from pathlib import Path
from typing import Optional
from csv_reporter.logger import configure_logging, logger
from csv_reporter.csv_parser import CSVParser
from csv_reporter.data_processor import DataProcessor
from csv_reporter.report_generator import ReportGenerator, SUPPORTED_FORMATS
from csv_reporter.config import Config
from csv_reporter.utils import print_progress_bar

__version__ = "1.0.0"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="csv-reporter",
        description="CSV Report Generator: Quickly analyze CSVs and generate summary reports.",
        epilog="Example usage: csv-reporter --input data.csv --report text --output report.txt",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input", "-i", required=True, help="Path to the input CSV file.", type=Path
    )
    parser.add_argument(
        "--report",
        "-r",
        default="text",
        choices=SUPPORTED_FORMATS,
        help=f'Select the output report format. Supported: {", ".join(SUPPORTED_FORMATS)}.',
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file path (writes to stdout if omitted).",
        type=Path,
    )
    parser.add_argument(
        "--config",
        "-c",
        help="Path to YAML configuration file (overrides defaults).",
        type=Path,
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging."
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Suppress non-error output."
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    return parser


def main(argv=None):
    """
    Entry point for the CLI tool. Parses arguments, sets up logging, and runs processing pipeline.
    """
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    # Logging configuration
    if args.quiet:
        log_level = "ERROR"
    elif args.verbose:
        log_level = "DEBUG"
    else:
        log_level = "INFO"
    configure_logging(log_level)

    logger.debug(f"Parsed arguments: {args}")
    config = Config()
    if args.config:
        try:
            config.load_from_file(args.config)
            logger.info(f"Loaded config from {args.config}")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            sys.exit(2)
    logger.debug(f"Using config: {config}")

    try:
        # --- Step 1: Parse & Validate CSV ---
        logger.info("Parsing CSV file...")
        parser = CSVParser(config=config)
        data_frame, parse_warnings = parser.parse_csv(args.input)
        if parse_warnings:
            for w in parse_warnings:
                logger.warning(f"CSV Warning: {w}")
        logger.info(f"Parsed CSV file: {args.input} with {len(data_frame)} rows.")

        # --- Step 2: Data Processing ---
        logger.info("Processing data...")
        processor = DataProcessor(config=config)
        with print_progress_bar(
            total=len(data_frame), desc="Analyzing data"
        ) as update_bar:
            summary = processor.process(data_frame, progress_cb=update_bar)

        logger.info("Generating report...")
        generator = ReportGenerator(config=config)
        report = generator.generate_report(summary, format=args.report)

        # --- Step 3: Output Report ---
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(report)
            logger.info(f"Report successfully written to {args.output}")
        else:
            print(report)
    except KeyboardInterrupt:
        logger.error("Operation cancelled by user.")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Critical error: {e}")
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
