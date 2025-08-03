"""
Main entry point for the genfilemap package when run as a module.

This allows the package to be run using 'python -m genfilemap'
"""

import sys
import os
from genfilemap.cli import setup_arg_parser, setup_config, main
from genfilemap.config import load_config, _deep_update

def main_with_config():
    """
    Main entry point that properly loads configuration files before processing CLI arguments.
    """
    # Parse command line arguments first to get potential config paths
    parser = setup_arg_parser()
    args = parser.parse_args()
    
    # Load both global and project configurations
    config = load_config(
        config_path=getattr(args, 'global_config', None),
        project_config_path=getattr(args, 'project_config', None)
    )
    
    # Convert args to config format (this creates a new config based only on args)
    cli_config = setup_config(args)
    
    # Merge the configuration with CLI config taking precedence
    _deep_update(config, cli_config)
    
    # Run the process with the merged configuration
    from genfilemap.core import run_process
    success = run_process(config)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main_with_config() 