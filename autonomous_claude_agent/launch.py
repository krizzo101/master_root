#!/usr/bin/env python3
"""
Autonomous Claude Agent - Main Launch Script

This is the primary entry point for the Autonomous Claude Agent. It provides
a comprehensive command-line interface for launching the agent with various
configurations and operational modes.

Usage Examples:
    # Basic usage
    python launch.py --goal "Analyze code quality"
    
    # Advanced usage
    python launch.py \
        --goal "Implement web scraper" \
        --config config/production.yaml \
        --mode supervised \
        --max-iterations 500 \
        --dashboard
    
    # Resume from checkpoint
    python launch.py \
        --goal "Continue task" \
        --checkpoint checkpoint-abc123 \
        --no-dashboard

Features:
    - Flexible configuration management
    - Multiple operational modes
    - Comprehensive logging setup
    - Web dashboard integration
    - Graceful shutdown handling
    - Environment validation
    - Resource monitoring
"""

import asyncio
import signal
import sys
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import uuid
from datetime import datetime

import click
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.logging import RichHandler

# Add source directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import agent components
from src.core.agent import AutonomousAgent, AgentState
from src.utils.logger import setup_logging
from src.utils.config_loader import load_config, validate_config
from src.monitoring.dashboard import start_dashboard
from src.monitoring.health_checker import HealthChecker
from src.governance.resource_monitor import ResourceMonitor

# Global console for rich output
console = Console()

# Global shutdown event
shutdown_event = asyncio.Event()

# Agent instance for cleanup
agent_instance = None


def display_banner():
    """Display the application banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                   Autonomous Claude Agent                    ║
    ║                                                              ║
    ║  A self-improving AI agent that continuously enhances       ║
    ║  itself using Claude Code MCP for analysis and modification ║
    ║                                                              ║
    ║  Version: 1.0.0                                             ║
    ║  Build: 2025-01-15                                          ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    console.print(Panel(banner, style="bold blue"))


def validate_environment():
    """Validate the environment and dependencies"""
    validation_results = []
    
    # Check Python version
    python_version = sys.version_info
    if python_version >= (3, 11):
        validation_results.append(("Python Version", f"{python_version.major}.{python_version.minor}", "✅"))
    else:
        validation_results.append(("Python Version", f"{python_version.major}.{python_version.minor}", "❌"))
    
    # Check Claude API key
    api_key = os.getenv("CLAUDE_API_KEY")
    if api_key:
        validation_results.append(("Claude API Key", "Present", "✅"))
    else:
        validation_results.append(("Claude API Key", "Missing", "⚠️"))
    
    # Check required directories
    required_dirs = ["data", "data/logs", "data/cache", "data/checkpoints"]
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            validation_results.append((f"Directory {dir_path}", "Exists", "✅"))
        else:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            validation_results.append((f"Directory {dir_path}", "Created", "✅"))
    
    # Check disk space
    try:
        import shutil
        total, used, free = shutil.disk_usage(".")
        free_gb = free // (1024**3)
        if free_gb >= 1:
            validation_results.append(("Disk Space", f"{free_gb}GB free", "✅"))
        else:
            validation_results.append(("Disk Space", f"{free_gb}GB free", "⚠️"))
    except Exception:
        validation_results.append(("Disk Space", "Unknown", "⚠️"))
    
    # Display validation results
    table = Table(title="Environment Validation", show_header=True, header_style="bold magenta")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="white")
    table.add_column("Result", style="white")
    
    for component, status, result in validation_results:
        table.add_row(component, status, result)
    
    console.print(table)
    
    # Check for critical failures
    critical_failures = [r for r in validation_results if r[2] == "❌"]
    if critical_failures:
        console.print("\n[red]Critical validation failures detected. Please resolve before continuing.[/red]")
        return False
    
    warnings = [r for r in validation_results if r[2] == "⚠️"]
    if warnings:
        console.print(f"\n[yellow]Found {len(warnings)} warnings. Agent may have limited functionality.[/yellow]")
    
    return True


def create_default_config() -> Dict[str, Any]:
    """Create a default configuration"""
    return {
        'agent': {
            'id': str(uuid.uuid4())[:8],
            'name': 'autonomous-claude-agent',
            'version': '1.0.0'
        },
        'execution': {
            'max_iterations': 1000,
            'mode': 'autonomous',
            'checkpoint_interval': 10,
            'timeout_seconds': 3600
        },
        'claude': {
            'max_concurrent': 5,
            'timeout': 300,
            'retry_max': 3,
            'rate_limits': {
                'requests_per_minute': 60,
                'tokens_per_day': 100000
            }
        },
        'context': {
            'max_tokens': 8000,
            'summarization_threshold': 6000,
            'compression_ratio': 0.3
        },
        'limits': {
            'memory_mb': 4096,
            'cpu_percent': 80,
            'disk_mb': 10240,
            'daily_tokens': 100000,
            'max_file_size_mb': 10
        },
        'safety': {
            'allow_file_modifications': True,
            'allow_network_requests': True,
            'require_approval_for': ['delete', 'system_command'],
            'max_recursion_depth': 5,
            'sandbox_mode': False
        },
        'research': {
            'cache_ttl_hours': 24,
            'max_search_results': 10,
            'enable_web_search': True,
            'enable_documentation_analysis': True
        },
        'learning': {
            'pattern_extraction_enabled': True,
            'experience_replay_enabled': True,
            'knowledge_base_path': 'data/knowledge.db',
            'max_patterns': 1000
        },
        'monitoring': {
            'dashboard_enabled': True,
            'dashboard_port': 8080,
            'health_check_interval': 30,
            'metrics_export_enabled': True
        },
        'logging': {
            'level': 'INFO',
            'file': 'data/logs/agent.log',
            'max_bytes': 10485760,
            'backup_count': 5,
            'format': '%(asctime)s [%(levelname)8s] %(name)s: %(message)s'
        }
    }


def setup_signal_handlers():
    """Set up signal handlers for graceful shutdown"""
    def signal_handler(sig, frame):
        console.print(f"\n[yellow]Received signal {sig}. Initiating graceful shutdown...[/yellow]")
        shutdown_event.set()
        
        # If agent exists, request shutdown
        if agent_instance:
            asyncio.create_task(agent_instance.shutdown())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # On Windows, also handle SIGBREAK
    if sys.platform == "win32":
        signal.signal(signal.SIGBREAK, signal_handler)


def display_agent_info(agent: AutonomousAgent, config: Dict[str, Any]):
    """Display agent information and configuration summary"""
    info_table = Table(title="Agent Configuration", show_header=True, header_style="bold green")
    info_table.add_column("Setting", style="cyan")
    info_table.add_column("Value", style="white")
    
    info_table.add_row("Agent ID", agent.id)
    info_table.add_row("Mode", config['execution']['mode'])
    info_table.add_row("Max Iterations", str(config['execution']['max_iterations']))
    info_table.add_row("Dashboard Port", str(config['monitoring']['dashboard_port']))
    info_table.add_row("Log Level", config['logging']['level'])
    info_table.add_row("Memory Limit", f"{config['limits']['memory_mb']}MB")
    info_table.add_row("Safety Mode", "Enabled" if config['safety']['require_approval_for'] else "Disabled")
    
    console.print(info_table)


async def monitor_agent_progress(agent: AutonomousAgent):
    """Monitor and display agent progress"""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        
        task = progress.add_task("Agent running...", total=None)
        
        while not shutdown_event.is_set() and agent.should_continue():
            # Update progress description based on agent state
            state_descriptions = {
                AgentState.INITIALIZING: "Initializing components...",
                AgentState.IDLE: "Waiting for next iteration...",
                AgentState.PLANNING: "Planning next actions...",
                AgentState.EXECUTING: "Executing tasks...",
                AgentState.LEARNING: "Learning from results...",
                AgentState.MODIFYING: "Applying self-modifications...",
                AgentState.RESEARCHING: "Researching solutions...",
                AgentState.ERROR: "Handling errors...",
                AgentState.RECOVERING: "Recovering from errors...",
                AgentState.SHUTDOWN: "Shutting down..."
            }
            
            description = state_descriptions.get(agent.current_state, "Running...")
            description += f" (Iteration {agent.iteration}/{agent.max_iterations})"
            
            progress.update(task, description=description)
            
            await asyncio.sleep(1)


async def run_health_checks(agent: AutonomousAgent):
    """Run periodic health checks"""
    health_checker = HealthChecker(agent)
    
    while not shutdown_event.is_set():
        try:
            health_status = await health_checker.check_all()
            
            if not health_status['healthy']:
                console.print(f"[red]Health check failed: {health_status['issues']}[/red]")
                
                # Take corrective action if possible
                if 'memory' in health_status['issues']:
                    await agent.handle_resource_limit()
                
        except Exception as e:
            console.print(f"[red]Health check error: {e}[/red]")
        
        await asyncio.sleep(30)  # Check every 30 seconds


async def async_main(
    goal: str,
    config_path: str,
    mode: str,
    dashboard: bool,
    checkpoint: Optional[str],
    max_iterations: int,
    log_level: str
):
    """Main async execution function"""
    global agent_instance
    
    try:
        # Load configuration
        if Path(config_path).exists():
            config = load_config(config_path)
        else:
            console.print(f"[yellow]Config file {config_path} not found. Creating default configuration.[/yellow]")
            config = create_default_config()
            
            # Save default config
            Path(config_path).parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
        
        # Override configuration with command line options
        config['execution']['max_iterations'] = max_iterations
        config['execution']['mode'] = mode
        config['logging']['level'] = log_level.upper()
        config['monitoring']['dashboard_enabled'] = dashboard
        
        # Validate configuration
        if not validate_config(config):
            console.print("[red]Configuration validation failed. Please check your settings.[/red]")
            return 1
        
        # Setup logging
        logger = setup_logging(config['logging'])
        logger.info(f"Starting Autonomous Claude Agent - Goal: {goal}")
        
        # Create agent
        agent_instance = AutonomousAgent(config, mode=mode)
        
        # Display agent info
        display_agent_info(agent_instance, config)
        
        # Start background tasks
        tasks = []
        
        # Start dashboard if enabled
        if dashboard and config['monitoring']['dashboard_enabled']:
            dashboard_task = asyncio.create_task(
                start_dashboard(agent_instance, port=config['monitoring']['dashboard_port'])
            )
            tasks.append(dashboard_task)
            console.print(f"[green]Dashboard started at http://localhost:{config['monitoring']['dashboard_port']}[/green]")
        
        # Start progress monitor
        progress_task = asyncio.create_task(monitor_agent_progress(agent_instance))
        tasks.append(progress_task)
        
        # Start health checks
        health_task = asyncio.create_task(run_health_checks(agent_instance))
        tasks.append(health_task)
        
        # Start agent
        if checkpoint:
            console.print(f"[blue]Resuming from checkpoint: {checkpoint}[/blue]")
            agent_task = asyncio.create_task(
                agent_instance.resume_from_checkpoint(checkpoint, goal)
            )
        else:
            console.print(f"[blue]Starting agent with goal: {goal}[/blue]")
            agent_task = asyncio.create_task(agent_instance.run(goal))
        
        tasks.append(agent_task)
        
        # Wait for completion or shutdown
        done, pending = await asyncio.wait(
            [*tasks, asyncio.create_task(shutdown_event.wait())],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Cancel pending tasks
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Check results
        for task in done:
            if not task.cancelled() and task.exception():
                console.print(f"[red]Task failed with error: {task.exception()}[/red]")
                return 1
        
        console.print("[green]Agent execution completed successfully.[/green]")
        return 0
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Received interrupt signal.[/yellow]")
        return 0
    except Exception as e:
        console.print(f"[red]Fatal error: {e}[/red]")
        logging.exception("Fatal error during execution")
        return 1
    finally:
        # Ensure cleanup
        if agent_instance:
            try:
                await agent_instance.shutdown()
            except Exception as e:
                console.print(f"[red]Error during cleanup: {e}[/red]")


@click.command()
@click.option(
    '--goal', 
    required=True, 
    help='The initial goal for the agent to work towards'
)
@click.option(
    '--config', 
    default='config/settings.yaml', 
    help='Path to configuration file (default: config/settings.yaml)'
)
@click.option(
    '--mode', 
    default='autonomous', 
    type=click.Choice(['autonomous', 'supervised', 'debug', 'safe']),
    help='Agent operational mode (default: autonomous)'
)
@click.option(
    '--dashboard/--no-dashboard', 
    default=True, 
    help='Enable web dashboard (default: enabled)'
)
@click.option(
    '--checkpoint', 
    help='Resume from checkpoint ID'
)
@click.option(
    '--max-iterations', 
    default=1000, 
    type=int,
    help='Maximum number of iterations (default: 1000)'
)
@click.option(
    '--log-level', 
    default='INFO', 
    type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']),
    help='Logging level (default: INFO)'
)
@click.option(
    '--validate-only', 
    is_flag=True,
    help='Only validate environment and configuration, do not start agent'
)
@click.option(
    '--quiet', 
    is_flag=True,
    help='Suppress banner and progress output'
)
def main(
    goal: str,
    config: str,
    mode: str,
    dashboard: bool,
    checkpoint: Optional[str],
    max_iterations: int,
    log_level: str,
    validate_only: bool,
    quiet: bool
):
    """
    Autonomous Claude Agent - Self-Improving AI Agent
    
    Launch an autonomous agent that continuously improves itself using Claude Code MCP.
    The agent analyzes its performance, identifies opportunities for enhancement, and
    applies improvements to its own codebase.
    
    Examples:
    
        # Basic usage
        python launch.py --goal "Analyze code quality in src/ directory"
        
        # Advanced usage with custom config
        python launch.py \\
            --goal "Build a web scraper for news sites" \\
            --config config/production.yaml \\
            --mode supervised \\
            --max-iterations 500
        
        # Resume from checkpoint
        python launch.py \\
            --goal "Continue previous task" \\
            --checkpoint checkpoint-abc123
        
        # Validation only
        python launch.py --goal "test" --validate-only
    """
    
    # Display banner unless quiet mode
    if not quiet:
        display_banner()
    
    # Validate environment
    if not validate_environment():
        console.print("[red]Environment validation failed. Exiting.[/red]")
        sys.exit(1)
    
    # Exit if validation only
    if validate_only:
        console.print("[green]Environment validation completed successfully.[/green]")
        sys.exit(0)
    
    # Setup signal handlers
    setup_signal_handlers()
    
    # Run main execution
    try:
        exit_code = asyncio.run(async_main(
            goal=goal,
            config_path=config,
            mode=mode,
            dashboard=dashboard,
            checkpoint=checkpoint,
            max_iterations=max_iterations,
            log_level=log_level
        ))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        console.print("\n[yellow]Execution interrupted by user.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()