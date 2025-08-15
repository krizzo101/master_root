#!/usr/bin/env python3
"""
Autonomous Claude Agent - Main Entry Point
"""

import asyncio
import signal
import sys
from pathlib import Path
import click
import yaml
from typing import Optional
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.agent import AutonomousAgent
from src.utils.logger import setup_logging
from src.monitoring.dashboard import start_dashboard

@click.command()
@click.option('--config', default='config/settings.yaml', help='Configuration file')
@click.option('--goal', required=True, help='Initial goal for the agent')
@click.option('--mode', default='autonomous', type=click.Choice(['autonomous', 'supervised', 'debug']))
@click.option('--dashboard/--no-dashboard', default=True, help='Enable web dashboard')
@click.option('--checkpoint', help='Resume from checkpoint')
@click.option('--max-iterations', default=1000, help='Maximum iterations')
def main(config: str, goal: str, mode: str, dashboard: bool, checkpoint: Optional[str], max_iterations: int):
    """Launch the Autonomous Claude Agent"""
    
    # Load configuration
    config_path = Path(config)
    if not config_path.exists():
        # Create default configuration
        config_data = create_default_config()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
    else:
        with open(config_path) as f:
            config_data = yaml.safe_load(f)
    
    # Override max iterations if specified
    config_data['max_iterations'] = max_iterations
    
    # Setup logging
    logger = setup_logging(config_data.get('logging', {}))
    logger.info(f"Starting Autonomous Agent with goal: {goal}")
    logger.info(f"Mode: {mode}, Max iterations: {max_iterations}")
    
    # Create agent
    agent = AutonomousAgent(config_data, mode=mode)
    
    # Setup graceful shutdown
    shutdown_event = asyncio.Event()
    
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal")
        shutdown_event.set()
        asyncio.create_task(agent.shutdown())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run async main
    asyncio.run(async_main(agent, goal, checkpoint, dashboard, shutdown_event))

async def async_main(agent, goal, checkpoint, dashboard, shutdown_event):
    """Async main function"""
    
    # Start dashboard if enabled
    dashboard_task = None
    if dashboard:
        dashboard_task = asyncio.create_task(start_dashboard(agent))
    
    try:
        # Run agent
        if checkpoint:
            agent_task = asyncio.create_task(agent.resume_from_checkpoint(checkpoint, goal))
        else:
            agent_task = asyncio.create_task(agent.run(goal))
        
        # Wait for either agent completion or shutdown
        done, pending = await asyncio.wait(
            [agent_task, shutdown_event.wait()],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Cancel pending tasks
        for task in pending:
            task.cancel()
            
    except Exception as e:
        logging.error(f"Agent failed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        if dashboard_task:
            dashboard_task.cancel()
            try:
                await dashboard_task
            except asyncio.CancelledError:
                pass

def create_default_config():
    """Create default configuration"""
    return {
        'max_iterations': 1000,
        'mode': 'autonomous',
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
            'max_recursion_depth': 5
        },
        'research': {
            'cache_ttl_hours': 24,
            'max_search_results': 10,
            'enable_web_search': True
        },
        'logging': {
            'level': 'INFO',
            'file': 'data/logs/agent.log',
            'max_bytes': 10485760,
            'backup_count': 5
        }
    }

if __name__ == "__main__":
    main()