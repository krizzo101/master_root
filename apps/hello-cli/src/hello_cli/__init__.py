"""Hello CLI - A production-ready Hello World CLI application."""

__version__ = "1.0.0"
__author__ = "OPSVI"
__email__ = "admin@opsvi.com"

from hello_cli.errors import HelloCliError, ValidationError

__all__ = ["HelloCliError", "ValidationError", "__version__"]
