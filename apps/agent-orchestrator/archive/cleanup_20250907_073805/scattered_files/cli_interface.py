#!/usr/bin/env python3
"""
Multi-Agent Log Tailer - Command Line Interface

Provides a robust CLI for the swarm log tailer with comprehensive argument parsing,
signal handling, and configuration validation.
"""

import argparse
import asyncio
import json
import logging
import os
import signal
import sys
from pathlib import Path
from typing import Dict, Optional, Any
import yaml


class CLIInterface:
    """Command-line interface for the Multi-Agent Log Tailer"""
    
    def __init__(self):
        self.parser = self._create_parser()
        self.args = None
        self.config = {}
        self.controller = None
        self.shutdown_event = asyncio.Event()
        self.logger = logging.getLogger(__name__)
        
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create and configure argument parser"""
        parser = argparse.ArgumentParser(
            prog='swarm-tailer',
            description='Multi-Agent Log Tailer - Monitor Claude Code session logs with swarm detection',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=self._get_examples()
        )
        
        # Core arguments
        parser.add_argument(
            '--projects-dir',
            type=str,
            default=os.getenv('SWARM_TAILER_PROJECTS_DIR', '~/.claude/projects'),
            help='Projects directory to monitor (default: ~/.claude/projects)'
        )
        
        parser.add_argument(
            '--pattern',
            type=str,
            default='*.jsonl',
            help='File pattern to match (default: *.jsonl)'
        )
        
        parser.add_argument(
            '--include-historical',
            action='store_true',
            help='Include historical log entries from the beginning of files'
        )
        
        # Swarm detection options
        swarm_group = parser.add_argument_group('swarm detection')
        swarm_group.add_argument(
            '--no-swarm-detection',
            action='store_true',
            help='Disable swarm detection algorithms'
        )
        
        swarm_group.add_argument(
            '--swarm-time-window',
            type=int,
            default=300,
            metavar='SECONDS',
            help='Time window for swarm detection (default: 300 seconds)'
        )
        
        swarm_group.add_argument(
            '--swarm-min-agents',
            type=int,
            default=3,
            metavar='N',
            help='Minimum agents for swarm detection (default: 3)'
        )
        
        # Visual options
        visual_group = parser.add_argument_group('visual options')
        visual_group.add_argument(
            '--color-scheme',
            choices=['default', 'high-contrast', 'colorblind'],
            default='default',
            help='Color scheme for output (default: default)'
        )
        
        visual_group.add_argument(
            '--no-color',
            action='store_true',
            help='Disable color output'
        )
        
        visual_group.add_argument(
            '--ascii-only',
            action='store_true',
            help='Use ASCII characters only (no emoji/unicode)'
        )
        
        visual_group.add_argument(
            '--no-emoji',
            action='store_true',
            help='Disable emoji in output'
        )
        
        # Performance options
        perf_group = parser.add_argument_group('performance tuning')
        perf_group.add_argument(
            '--workers',
            type=int,
            default=int(os.getenv('SWARM_TAILER_WORKERS', '50')),
            metavar='N',
            help='Number of worker threads (default: 50)'
        )
        
        perf_group.add_argument(
            '--buffer-size',
            type=int,
            default=1000,
            metavar='N',
            help='Output buffer size (default: 1000)'
        )
        
        perf_group.add_argument(
            '--poll-interval',
            type=int,
            default=100,
            metavar='MS',
            help='File polling interval in milliseconds (default: 100)'
        )
        
        perf_group.add_argument(
            '--max-files',
            type=int,
            default=1000,
            metavar='N',
            help='Maximum number of files to monitor (default: 1000)'
        )
        
        perf_group.add_argument(
            '--max-memory',
            type=int,
            default=500,
            metavar='MB',
            help='Maximum memory usage in MB (default: 500)'
        )
        
        # Monitoring options
        monitor_group = parser.add_argument_group('monitoring')
        monitor_group.add_argument(
            '--metrics-port',
            type=int,
            metavar='PORT',
            help='Prometheus metrics export port'
        )
        
        monitor_group.add_argument(
            '--health-port',
            type=int,
            metavar='PORT',
            help='Health check endpoint port'
        )
        
        # Configuration
        config_group = parser.add_argument_group('configuration')
        config_group.add_argument(
            '--config',
            type=str,
            metavar='FILE',
            help='Configuration file path (YAML format)'
        )
        
        config_group.add_argument(
            '--export-config',
            type=str,
            metavar='FILE',
            help='Export current configuration to file'
        )
        
        # Output options
        output_group = parser.add_argument_group('output')
        output_group.add_argument(
            '--output-format',
            choices=['text', 'json', 'csv'],
            default='text',
            help='Output format (default: text)'
        )
        
        output_group.add_argument(
            '--output-file',
            type=str,
            metavar='FILE',
            help='Write output to file instead of stdout'
        )
        
        output_group.add_argument(
            '--quiet',
            action='store_true',
            help='Suppress non-essential output'
        )
        
        # Debugging options
        debug_group = parser.add_argument_group('debugging')
        debug_group.add_argument(
            '--verbose', '-v',
            action='count',
            default=0,
            help='Verbose output (use multiple times for more detail)'
        )
        
        debug_group.add_argument(
            '--debug',
            action='store_true',
            help='Enable debug mode with detailed logging'
        )
        
        debug_group.add_argument(
            '--log-file',
            type=str,
            metavar='FILE',
            help='Log file path'
        )
        
        debug_group.add_argument(
            '--profile',
            action='store_true',
            help='Enable performance profiling'
        )
        
        # Commands
        parser.add_argument(
            '--version',
            action='version',
            version='%(prog)s 1.0.0'
        )
        
        parser.add_argument(
            '--health-check',
            action='store_true',
            help='Run health check and exit'
        )
        
        parser.add_argument(
            '--list-files',
            action='store_true',
            help='List matching files and exit'
        )
        
        parser.add_argument(
            '--test-config',
            action='store_true',
            help='Test configuration and exit'
        )
        
        return parser
    
    def _get_examples(self) -> str:
        """Get usage examples for help text"""
        return """
EXAMPLES:
  Basic usage:
    swarm-tailer
  
  Monitor specific directory with pattern:
    swarm-tailer --projects-dir /path/to/logs --pattern "**/*.jsonl"
  
  Include historical entries with colorblind scheme:
    swarm-tailer --include-historical --color-scheme colorblind
  
  High-performance monitoring with metrics:
    swarm-tailer --workers 100 --buffer-size 5000 --metrics-port 9090
  
  Disable visual features for log processing:
    swarm-tailer --no-color --ascii-only --output-format json
  
  Debug mode with specific configuration:
    swarm-tailer --config config.yaml --debug --log-file tailer.log
  
  List matching files without monitoring:
    swarm-tailer --list-files --pattern "*agent*.jsonl"

SIGNAL HANDLING:
  SIGINT (Ctrl+C)   - Graceful shutdown
  SIGTERM           - Graceful shutdown
  SIGUSR1           - Toggle debug mode
  SIGUSR2           - Print statistics
  SIGHUP            - Reload configuration

ENVIRONMENT VARIABLES:
  SWARM_TAILER_CONFIG           - Default configuration file
  SWARM_TAILER_PROJECTS_DIR     - Default projects directory
  SWARM_TAILER_LOG_LEVEL        - Default log level
  SWARM_TAILER_WORKERS          - Default worker count
  SWARM_TAILER_NO_COLOR         - Disable color output
  
For more information, visit: https://github.com/org/swarm-log-tailer
"""
    
    def parse_args(self, args=None) -> argparse.Namespace:
        """Parse command-line arguments"""
        self.args = self.parser.parse_args(args)
        return self.args
    
    def load_config(self) -> Dict[str, Any]:
        """Load and merge configuration from file and arguments"""
        config = {}
        
        # Load from config file if specified
        config_file = self.args.config or os.getenv('SWARM_TAILER_CONFIG')
        if config_file:
            config_path = Path(config_file).expanduser()
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        if config_path.suffix in ['.yaml', '.yml']:
                            config = yaml.safe_load(f) or {}
                        else:
                            config = json.load(f)
                    self.logger.info(f"Loaded configuration from {config_path}")
                except Exception as e:
                    self.logger.error(f"Failed to load config from {config_path}: {e}")
                    sys.exit(1)
        
        # Override with command-line arguments
        self.config = self._merge_args_to_config(config)
        
        # Validate configuration
        self._validate_config()
        
        return self.config
    
    def _merge_args_to_config(self, config: Dict) -> Dict:
        """Merge command-line arguments into configuration"""
        # System configuration
        if 'system' not in config:
            config['system'] = {}
        
        config['system']['projects_dir'] = Path(self.args.projects_dir).expanduser()
        config['system']['pattern'] = self.args.pattern
        config['system']['max_files'] = self.args.max_files
        
        # Monitoring configuration
        if 'monitoring' not in config:
            config['monitoring'] = {}
        
        config['monitoring']['poll_interval_ms'] = self.args.poll_interval
        config['monitoring']['buffer_size'] = self.args.buffer_size
        config['monitoring']['include_historical'] = self.args.include_historical
        
        # Swarm detection configuration
        if 'swarm_detection' not in config:
            config['swarm_detection'] = {}
        
        config['swarm_detection']['enabled'] = not self.args.no_swarm_detection
        config['swarm_detection']['time_window_seconds'] = self.args.swarm_time_window
        config['swarm_detection']['min_agents'] = self.args.swarm_min_agents
        
        # Visual configuration
        if 'visual' not in config:
            config['visual'] = {}
        
        config['visual']['color_scheme'] = self.args.color_scheme
        config['visual']['use_color'] = not self.args.no_color
        config['visual']['use_emoji'] = not self.args.no_emoji and not self.args.ascii_only
        config['visual']['ascii_only'] = self.args.ascii_only
        
        # Performance configuration
        if 'performance' not in config:
            config['performance'] = {}
        
        config['performance']['worker_threads'] = self.args.workers
        config['performance']['max_memory_mb'] = self.args.max_memory
        
        # Output configuration
        if 'output' not in config:
            config['output'] = {}
        
        config['output']['format'] = self.args.output_format
        config['output']['file'] = self.args.output_file
        config['output']['quiet'] = self.args.quiet
        
        # Logging configuration
        if 'logging' not in config:
            config['logging'] = {}
        
        if self.args.debug:
            config['logging']['level'] = 'DEBUG'
        elif self.args.verbose > 1:
            config['logging']['level'] = 'DEBUG'
        elif self.args.verbose > 0:
            config['logging']['level'] = 'INFO'
        else:
            config['logging']['level'] = config.get('logging', {}).get('level', 'WARNING')
        
        config['logging']['file'] = self.args.log_file
        
        # Monitoring endpoints
        if self.args.metrics_port:
            config['metrics_port'] = self.args.metrics_port
        if self.args.health_port:
            config['health_port'] = self.args.health_port
        
        return config
    
    def _validate_config(self) -> None:
        """Validate configuration values"""
        errors = []
        
        # Validate paths
        projects_dir = self.config['system']['projects_dir']
        if not projects_dir.exists():
            errors.append(f"Projects directory does not exist: {projects_dir}")
        
        # Validate numeric ranges
        if self.config['performance']['worker_threads'] < 1:
            errors.append("Worker threads must be at least 1")
        if self.config['performance']['worker_threads'] > 1000:
            errors.append("Worker threads cannot exceed 1000")
        
        if self.config['monitoring']['poll_interval_ms'] < 10:
            errors.append("Poll interval must be at least 10ms")
        if self.config['monitoring']['poll_interval_ms'] > 10000:
            errors.append("Poll interval cannot exceed 10000ms")
        
        if self.config['monitoring']['buffer_size'] < 10:
            errors.append("Buffer size must be at least 10")
        if self.config['monitoring']['buffer_size'] > 100000:
            errors.append("Buffer size cannot exceed 100000")
        
        # Report errors
        if errors:
            for error in errors:
                self.logger.error(f"Configuration error: {error}")
            sys.exit(1)
    
    def export_config(self, filepath: str) -> None:
        """Export current configuration to file"""
        output_path = Path(filepath).expanduser()
        try:
            with open(output_path, 'w') as f:
                if output_path.suffix in ['.yaml', '.yml']:
                    yaml.dump(self.config, f, default_flow_style=False, sort_keys=True)
                else:
                    json.dump(self.config, f, indent=2, sort_keys=True)
            print(f"Configuration exported to: {output_path}")
        except Exception as e:
            self.logger.error(f"Failed to export configuration: {e}")
            sys.exit(1)
    
    def setup_logging(self) -> None:
        """Configure logging based on arguments"""
        log_level = getattr(logging, self.config['logging']['level'])
        
        # Configure format
        if self.args.debug:
            log_format = '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        else:
            log_format = '%(asctime)s - %(levelname)s - %(message)s'
        
        # Configure handlers
        handlers = []
        
        # Console handler (unless quiet mode)
        if not self.args.quiet:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(log_format))
            handlers.append(console_handler)
        
        # File handler
        if self.config['logging'].get('file'):
            file_handler = logging.FileHandler(self.config['logging']['file'])
            file_handler.setFormatter(logging.Formatter(log_format))
            handlers.append(file_handler)
        
        # Configure root logger
        logging.basicConfig(
            level=log_level,
            handlers=handlers
        )
    
    def setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown and control"""
        loop = asyncio.get_event_loop()
        
        # Graceful shutdown handlers
        for sig in [signal.SIGINT, signal.SIGTERM]:
            loop.add_signal_handler(
                sig,
                lambda s=sig: asyncio.create_task(self._handle_shutdown(s))
            )
        
        # Control signal handlers (Unix only)
        if hasattr(signal, 'SIGUSR1'):
            loop.add_signal_handler(
                signal.SIGUSR1,
                self._toggle_debug
            )
        
        if hasattr(signal, 'SIGUSR2'):
            loop.add_signal_handler(
                signal.SIGUSR2,
                self._print_statistics
            )
        
        if hasattr(signal, 'SIGHUP'):
            loop.add_signal_handler(
                signal.SIGHUP,
                lambda: asyncio.create_task(self._reload_config())
            )
    
    async def _handle_shutdown(self, sig) -> None:
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {sig.name}, initiating graceful shutdown...")
        
        if not self.shutdown_event.is_set():
            self.shutdown_event.set()
            
            if self.controller:
                try:
                    await self.controller.stop()
                    self.logger.info("Controller stopped successfully")
                except Exception as e:
                    self.logger.error(f"Error during controller shutdown: {e}")
            
            # Cancel all running tasks
            tasks = [t for t in asyncio.all_tasks() if t != asyncio.current_task()]
            for task in tasks:
                task.cancel()
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
            self.logger.info("Shutdown complete")
    
    def _toggle_debug(self) -> None:
        """Toggle debug mode at runtime"""
        current_level = logging.getLogger().level
        new_level = logging.DEBUG if current_level != logging.DEBUG else logging.INFO
        logging.getLogger().setLevel(new_level)
        self.logger.info(f"Log level changed to: {logging.getLevelName(new_level)}")
    
    def _print_statistics(self) -> None:
        """Print current statistics"""
        if self.controller:
            stats = self.controller.get_statistics()
            self.logger.info(f"Statistics: {json.dumps(stats, indent=2)}")
    
    async def _reload_config(self) -> None:
        """Reload configuration at runtime"""
        self.logger.info("Reloading configuration...")
        try:
            self.load_config()
            if self.controller:
                await self.controller.reload_config(self.config)
            self.logger.info("Configuration reloaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to reload configuration: {e}")
    
    def list_files(self) -> None:
        """List matching files and exit"""
        from pathlib import Path
        import glob
        
        projects_dir = Path(self.args.projects_dir).expanduser()
        pattern = self.args.pattern
        
        # Find matching files
        if '**' in pattern:
            files = list(projects_dir.glob(pattern))
        else:
            files = list(projects_dir.glob(f"**/{pattern}"))
        
        if not files:
            print("No matching files found")
            return
        
        print(f"Found {len(files)} matching file(s):")
        for file in sorted(files):
            rel_path = file.relative_to(projects_dir)
            size = file.stat().st_size
            print(f"  {rel_path} ({size:,} bytes)")
    
    def run_health_check(self) -> int:
        """Run health check and return exit code"""
        checks = {
            'config': True,
            'projects_dir': False,
            'permissions': False,
        }
        
        # Check projects directory
        projects_dir = Path(self.args.projects_dir).expanduser()
        if projects_dir.exists() and projects_dir.is_dir():
            checks['projects_dir'] = True
            
            # Check permissions
            if os.access(projects_dir, os.R_OK):
                checks['permissions'] = True
        
        # Print results
        all_passed = all(checks.values())
        status = "HEALTHY" if all_passed else "UNHEALTHY"
        
        print(f"Health Check: {status}")
        for check, passed in checks.items():
            symbol = "✓" if passed else "✗"
            print(f"  {symbol} {check}")
        
        return 0 if all_passed else 1
    
    def test_config(self) -> int:
        """Test configuration and return exit code"""
        try:
            self.load_config()
            print("Configuration is valid")
            
            if self.args.verbose:
                print("\nConfiguration details:")
                print(json.dumps(self.config, indent=2, default=str))
            
            return 0
        except Exception as e:
            print(f"Configuration error: {e}")
            return 1
    
    async def run(self) -> int:
        """Main entry point for the CLI"""
        # Parse arguments
        self.parse_args()
        
        # Handle special commands
        if self.args.list_files:
            self.list_files()
            return 0
        
        if self.args.health_check:
            return self.run_health_check()
        
        if self.args.test_config:
            return self.test_config()
        
        # Load configuration
        self.load_config()
        
        # Export config if requested
        if self.args.export_config:
            self.export_config(self.args.export_config)
            return 0
        
        # Setup logging
        self.setup_logging()
        
        # Setup signal handlers
        self.setup_signal_handlers()
        
        # Import and create controller
        try:
            # Dynamic import to avoid circular dependencies
            from swarm_log_tailer import AgentLogTailer
            
            self.controller = AgentLogTailer(
                projects_dir=str(self.config['system']['projects_dir']),
                pattern=self.config['system']['pattern'],
                include_historical=self.config['monitoring']['include_historical']
            )
            
            # Start monitoring
            self.logger.info("Starting Multi-Agent Log Tailer...")
            await self.controller.run()
            
        except KeyboardInterrupt:
            self.logger.info("Interrupted by user")
        except Exception as e:
            self.logger.error(f"Fatal error: {e}", exc_info=True)
            return 1
        finally:
            if not self.shutdown_event.is_set():
                await self._handle_shutdown(signal.SIGTERM)
        
        return 0


def main():
    """Main entry point"""
    cli = CLIInterface()
    
    try:
        # Run the async main function
        exit_code = asyncio.run(cli.run())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()