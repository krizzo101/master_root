"""Command-line interface for Hello CLI."""

import argparse
import sys
from pathlib import Path
from typing import Optional

from hello_cli import __version__
from hello_cli.config import Config
from hello_cli.errors import HelloCliError, ValidationError
from hello_cli.greeter import Greeter


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        prog="hello-cli",
        description="A production-ready Hello World CLI application",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  hello-cli World
  hello-cli "John Doe" --style emoji
  hello-cli Alice --uppercase
  hello-cli Bob --config ~/my-config.json
        """,
    )

    parser.add_argument("name", help="Name to greet")

    parser.add_argument(
        "-s",
        "--style",
        choices=["plain", "emoji", "banner"],
        help="Output style (default: plain)",
    )

    parser.add_argument(
        "-u", "--uppercase", action="store_true", help="Output in uppercase"
    )

    parser.add_argument("-c", "--config", type=Path, help="Path to configuration file")

    parser.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s {__version__}"
    )

    return parser


def main(argv: Optional[list] = None) -> int:
    """Main entry point for the CLI.

    Args:
        argv: Command line arguments (for testing)

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = create_parser()

    try:
        args = parser.parse_args(argv)

        # Load configuration
        config = Config(config_path=args.config) if args.config else Config()

        # Create greeter
        greeter = Greeter(config=config)

        # Generate greeting
        message = greeter.greet(
            name=args.name, style=args.style, uppercase=args.uppercase
        )

        # Output message
        print(message)

        return 0

    except ValidationError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    except HelloCliError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2

    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        return 130

    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
