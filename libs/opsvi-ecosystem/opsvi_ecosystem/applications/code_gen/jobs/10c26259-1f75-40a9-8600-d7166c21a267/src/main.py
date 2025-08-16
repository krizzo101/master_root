#!/usr/bin/env python3
"""Command-line tool."""
import argparse
import logging
from pathlib import Path


def setup_logging(verbose: bool = False) -> None:
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="CLI Tool")
    parser.add_argument("input", help="Input file or text")
    parser.add_argument("--output", "-o", help="Output file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()
    setup_logging(args.verbose)

    logger = logging.getLogger(__name__)
    logger.info(f"Processing: {args.input}")

    # Process input
    result = f"Processed: {args.input}"

    if args.output:
        Path(args.output).write_text(result)
        logger.info(f"Output written to: {args.output}")
    else:
        print(result)


if __name__ == "__main__":
    main()
