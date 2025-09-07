#!/usr/bin/env python3
"""
Enhanced Multi-Agent Log Tailer with Swarm Detection

Monitors Claude Code session logs in real-time with visual indicators for agent swarms
and beautiful formatting that preserves important details.

Features:
- Real-time multi-file tailing
- Swarm detection and visualization  
- Color-coded agent identification
- Chronological log interleaving
- Performance optimized for large numbers of agents
"""

import asyncio
import argparse
import json
import os
import signal
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import re

# Color management
class Colors:
    """ANSI color codes for terminal output"""
    COLORS = [
        '\033[91m',  # Red
        '\033[92m',  # Green  
        '\033[93m',  # Yellow
        '\033[94m',  # Blue
        '\033[95m',  # Magenta
        '\033[96m',  # Cyan
        '\033[31m',  # Dark Red
        '\033[32m',  # Dark Green
        '\033[33m',  # Dark Yellow
        '\033[34m',  # Dark Blue
        '\033[35m',  # Dark Magenta
        '\033[36m',  # Dark Cyan
        '\033[97m',  # White
        '\033[90m',  # Gray
    ]
    
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Role indicators
    ROLE_COLORS = {
        'user': '\033[96m👤\033[0m',      # Cyan user
        'assistant': '\033[92m🤖\033[0m', # Green assistant  
        'tool': '\033[93m⚡\033[0m',       # Yellow tool
        'tool_use': '\033[94m🔧\033[0m',  # Blue tool use
        'tool_result': '\033[90m📊\033[0m', # Gray tool result
    }
    
    # Swarm icons
    SWARM_ICONS = ['🐝', '🐜', '🦋', '🐞', '🦗', '🕷️', '🦂', '🐛', '🦟', '🐢']

    @classmethod
    def get_agent_color(cls, agent_id: str, color_index: int) -> str:
        """Get consistent color for agent"""
        return cls.COLORS[color_index % len(cls.COLORS)]
    
    @classmethod
    def colorize(cls, text: str, color: str) -> str:
        """Apply color to text"""
        return f"{color}{text}{cls.RESET}"

class AgentLogTailer:
    """Enhanced multi-agent log tailer with swarm detection"""
    
    def __init__(self, projects_dir: str = None, pattern: str = "*agent-orchestrator*", 
                 include_historical: bool = False):
        self.projects_dir = Path(projects_dir or Path.home() / ".claude" / "projects")
        self.pattern = pattern
        self.include_historical = include_historical
        
        # Agent management
        self.agent_colors: Dict[str, str] = {}
        self.agent_positions: Dict[str, int] = {}
        self.swarm_groups: Dict[str, str] = {}  # agent_id -> swarm_id
        self.swarm_icons: Dict[str, str] = {}   # swarm_id -> icon
        self.agent_files: Dict[str, Path] = {}  # agent_id -> file_path
        
        # State management
        self.running = False
        self.color_index = 0
        self.swarm_count = 0
        
    def discover_agent_files(self) -> List[Path]:
        """Discover active agent log files"""
        if not self.projects_dir.exists():
            print(f"⚠️  Projects directory not found: {self.projects_dir}")
            return []
            
        agent_files = []
        cutoff_time = time.time() - 86400  # 24 hours ago
        
        for project_dir in self.projects_dir.glob(self.pattern):
            if not project_dir.is_dir():
                continue
                
            for jsonl_file in project_dir.glob("*.jsonl"):
                # Check if file is active (non-empty and recently modified)
                try:
                    stat = jsonl_file.stat()
                    if stat.st_size > 0 and stat.st_mtime > cutoff_time:
                        agent_files.append(jsonl_file)
                except OSError:
                    continue
                    
        return sorted(agent_files, key=lambda f: f.stat().st_mtime, reverse=True)
    
    def detect_swarms(self, agent_files: List[Path]) -> Dict[str, List[str]]:
        """Detect agent swarms based on directory grouping and timing"""
        swarms = defaultdict(list)
        
        # Group by project directory
        project_groups = defaultdict(list)
        for file_path in agent_files:
            project_dir = file_path.parent.name
            agent_id = file_path.stem[-8:]  # Last 8 chars of filename
            project_groups[project_dir].append((agent_id, file_path))
            
        # Identify swarms (multiple agents in same project within time window)
        swarm_id = 0
        for project_dir, agents in project_groups.items():
            if len(agents) > 1:
                # Check if agents were created within a 5-minute window
                timestamps = []
                for agent_id, file_path in agents:
                    try:
                        timestamps.append(file_path.stat().st_ctime)
                    except OSError:
                        continue
                
                if timestamps:
                    timestamps.sort()
                    if timestamps[-1] - timestamps[0] <= 300:  # 5 minutes
                        swarm_name = f"swarm_{swarm_id}"
                        swarms[swarm_name] = [agent_id for agent_id, _ in agents]
                        swarm_id += 1
                        
        return dict(swarms)
    
    def assign_colors_and_icons(self, agent_files: List[Path], swarms: Dict[str, List[str]]):
        """Assign colors and icons to agents"""
        # Clear existing assignments
        self.agent_colors.clear()
        self.swarm_groups.clear() 
        self.swarm_icons.clear()
        self.agent_files.clear()
        
        # Create reverse swarm mapping
        agent_to_swarm = {}
        for swarm_id, agent_list in swarms.items():
            for agent_id in agent_list:
                agent_to_swarm[agent_id] = swarm_id
                
        # Assign swarm icons
        for i, swarm_id in enumerate(swarms.keys()):
            self.swarm_icons[swarm_id] = Colors.SWARM_ICONS[i % len(Colors.SWARM_ICONS)]
            
        # Assign colors to agents
        self.color_index = 0
        for file_path in agent_files:
            agent_id = file_path.stem[-8:]
            self.agent_files[agent_id] = file_path
            
            # Assign color
            color = Colors.get_agent_color(agent_id, self.color_index)
            self.agent_colors[agent_id] = color
            self.color_index += 1
            
            # Assign swarm membership
            if agent_id in agent_to_swarm:
                self.swarm_groups[agent_id] = agent_to_swarm[agent_id]
                
    def get_agent_prefix(self, agent_id: str) -> str:
        """Get formatted prefix for agent (with swarm icon if applicable)"""
        color = self.agent_colors.get(agent_id, '')
        
        # Add swarm icon if agent is in a swarm
        swarm_icon = ""
        if agent_id in self.swarm_groups:
            swarm_id = self.swarm_groups[agent_id]
            swarm_icon = self.swarm_icons.get(swarm_id, '') + " "
            
        return f"{swarm_icon}{Colors.colorize(f'[{agent_id}]', color)}"
    
    def format_log_entry(self, agent_id: str, entry: Dict) -> Optional[str]:
        """Format a single log entry for display"""
        try:
            # Extract timestamp
            timestamp = entry.get('timestamp', '')
            if timestamp and 'T' in timestamp:
                # Convert to HH:MM:SS format
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime('%H:%M:%S')
                except ValueError:
                    # Try parsing without timezone
                    dt = datetime.fromisoformat(timestamp.split('.')[0])
                    time_str = dt.strftime('%H:%M:%S')
            else:
                time_str = '??:??:??'
                
            # Extract role and content - handle different log formats
            role = entry.get('role', entry.get('type', 'unknown'))
            content = entry.get('content', entry.get('message', {}))
            
            # Handle nested message structure
            if isinstance(content, dict) and 'content' in content:
                content = content['content']
            
            # Get role indicator
            role_icon = Colors.ROLE_COLORS.get(role, '❓')
            
            # Get agent prefix with swarm icon
            agent_prefix = self.get_agent_prefix(agent_id)
            
            # Skip empty entries
            if not content and not entry.get('tool_calls') and not entry.get('tool_results'):
                return None
            
            # Format content based on type
            formatted_content = ""
            
            if isinstance(content, list):
                # Handle structured content (tool calls, etc.)
                content_parts = []
                for item in content:
                    if isinstance(item, dict):
                        if item.get('type') == 'tool_use':
                            tool_name = item.get('name', 'unknown_tool')
                            content_parts.append(f"🔧 {tool_name}")
                        elif item.get('type') == 'text':
                            text = item.get('text', '')
                            if text.strip():
                                content_parts.append(text[:150])
                        elif item.get('type') == 'tool_result':
                            content_parts.append("📊 tool_result")
                            
                formatted_content = ' '.join(content_parts)
                
            elif isinstance(content, str) and content.strip():
                # Handle text content
                formatted_content = content.strip()[:150]
                if len(content) > 150:
                    formatted_content += "..."
                    
            # Check for tool calls/results in entry
            elif entry.get('tool_calls'):
                tools = []
                for tool_call in entry.get('tool_calls', []):
                    if isinstance(tool_call, dict):
                        func_name = tool_call.get('function', {}).get('name', 'unknown')
                        tools.append(func_name)
                formatted_content = f"🔧 {', '.join(tools)}"
                
            elif entry.get('tool_results'):
                formatted_content = f"📊 {len(entry['tool_results'])} tool results"
                
            # If still no content, try extracting from raw entry
            if not formatted_content:
                # Look for any text in the entry
                for key in ['text', 'output', 'result', 'response']:
                    if key in entry and entry[key]:
                        formatted_content = str(entry[key])[:100]
                        break
                        
            # Final fallback - show entry type info
            if not formatted_content:
                entry_type = entry.get('type', entry.get('role', 'unknown'))
                session_id = entry.get('sessionId', '')
                if session_id:
                    formatted_content = f"[{entry_type}] session: ...{session_id[-8:]}"
                else:
                    return None  # Skip truly empty entries
                    
            # Clean up content (remove excessive whitespace/newlines)
            formatted_content = re.sub(r'\s+', ' ', formatted_content).strip()
            
            # Skip if still empty
            if not formatted_content:
                return None
            
            return f"{time_str} {agent_prefix} {role_icon} {formatted_content}"
            
        except Exception as e:
            return f"⚠️  Error formatting entry for {agent_id}: {e}"
    
    async def tail_file(self, file_path: Path, agent_id: str, output_queue: asyncio.Queue):
        """Tail a single agent log file"""
        # Initialize position - start at end of file unless including historical
        if agent_id not in self.agent_positions:
            if self.include_historical:
                self.agent_positions[agent_id] = 0
                # print(f"📜 {agent_id}: Starting from beginning (historical mode)")
            else:
                try:
                    with open(file_path, 'rb') as f:
                        f.seek(0, 2)  # Seek to end of file
                        self.agent_positions[agent_id] = f.tell()
                    # print(f"📍 {agent_id}: Starting at end of file (position {self.agent_positions[agent_id]})")
                except (FileNotFoundError, PermissionError):
                    self.agent_positions[agent_id] = 0
        
        position = self.agent_positions[agent_id]
        
        try:
            while self.running:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        # Get current file size
                        f.seek(0, 2)  # Seek to end
                        current_size = f.tell()
                        
                        # If file was truncated or rotated, reset position
                        if position > current_size:
                            print(f"🔄 {agent_id}: File rotated/truncated, resetting position")
                            position = 0
                            
                        f.seek(position)
                        
                        new_lines = 0
                        for line in f:
                            if not line.strip():
                                continue
                                
                            try:
                                entry = json.loads(line.strip())
                                formatted_line = self.format_log_entry(agent_id, entry)
                                if formatted_line:
                                    # Add timestamp for sorting
                                    timestamp = entry.get('timestamp', '')
                                    await output_queue.put((timestamp, formatted_line))
                                    new_lines += 1
                            except json.JSONDecodeError:
                                continue
                                
                        # Update position
                        position = f.tell()
                        self.agent_positions[agent_id] = position
                        
                        # Debug output for new content (only in verbose mode)
                        # if new_lines > 0:
                        #     print(f"📝 {agent_id}: Processed {new_lines} new entries", flush=True)
                        
                except FileNotFoundError:
                    # File was deleted, remove from tracking
                    if agent_id in self.agent_positions:
                        del self.agent_positions[agent_id]
                    print(f"🗑️  {agent_id}: File deleted, stopping monitoring")
                    break
                except PermissionError:
                    print(f"⚠️  Permission denied reading {file_path}")
                    break
                    
                await asyncio.sleep(0.1)  # Check for new content every 100ms
                
        except asyncio.CancelledError:
            pass  # Normal shutdown
            
    async def output_processor(self, output_queue: asyncio.Queue):
        """Process and display output in chronological order"""
        output_buffer = []
        last_flush = time.time()
        
        try:
            while self.running:
                try:
                    # Collect messages for up to 100ms or until we have 5 messages
                    timeout = 0.1
                    batch_size = 0
                    
                    while batch_size < 5:  # Reduced batch size to prevent buffer issues
                        try:
                            timestamp, message = await asyncio.wait_for(
                                output_queue.get(), timeout=timeout
                            )
                            output_buffer.append((timestamp, message))
                            batch_size += 1
                            timeout = 0.01  # Shorter timeout for subsequent messages
                        except asyncio.TimeoutError:
                            break
                            
                    # Flush buffer if we have messages or it's been too long
                    current_time = time.time()
                    if output_buffer and (batch_size > 0 or current_time - last_flush > 0.3):
                        # Sort by timestamp
                        output_buffer.sort(key=lambda x: x[0])
                        
                        # Print messages safely with flush
                        try:
                            for timestamp, message in output_buffer:
                                print(message, flush=True)
                        except Exception as print_error:
                            # Fallback to sys.stdout.write to avoid reentrant issues
                            import sys
                            for timestamp, message in output_buffer:
                                try:
                                    sys.stdout.write(message + '\n')
                                    sys.stdout.flush()
                                except:
                                    pass  # Skip problematic messages
                            
                        output_buffer.clear()
                        last_flush = current_time
                        
                    else:
                        # Small delay to prevent spinning
                        await asyncio.sleep(0.01)
                        
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    # Log error but continue processing
                    try:
                        print(f"⚠️  Output processor error: {e}", flush=True)
                    except:
                        pass  # Can't even print error, just continue
                    
        except Exception as e:
            pass  # Fatal error, let the loop exit
            
        # Flush any remaining messages on shutdown
        if output_buffer:
            output_buffer.sort(key=lambda x: x[0])
            try:
                for timestamp, message in output_buffer:
                    print(message, flush=True)
            except:
                pass  # Best effort cleanup

    def print_startup_summary(self, agent_files: List[Path], swarms: Dict[str, List[str]]):
        """Print startup summary with swarm information"""
        print(f"\n🚀 {Colors.BOLD}Multi-Agent Log Tailer Started{Colors.RESET}")
        print(f"📁 Projects: {self.projects_dir}")
        print(f"🔍 Pattern: {self.pattern}")
        print(f"📊 Found {len(agent_files)} active agents")
        
        if swarms:
            print(f"\n🐝 {Colors.BOLD}Detected Swarms:{Colors.RESET}")
            for swarm_id, agents in swarms.items():
                icon = self.swarm_icons.get(swarm_id, '❓')
                print(f"  {icon} {swarm_id}: {len(agents)} agents ({', '.join(agents)})")
        else:
            print("\n🔍 No swarms detected (agents working independently)")
            
        print(f"\n⏱️  {Colors.DIM}Monitoring logs in real-time... (Ctrl+C to exit){Colors.RESET}\n")
        print("=" * 80)

    async def run(self):
        """Main execution loop"""
        self.running = True
        
        # Discover and setup
        agent_files = self.discover_agent_files()
        if not agent_files:
            print("❌ No active agent files found. Try adjusting the pattern or checking the projects directory.")
            return
            
        swarms = self.detect_swarms(agent_files)
        self.assign_colors_and_icons(agent_files, swarms)
        
        # Print startup summary
        self.print_startup_summary(agent_files, swarms)
        
        # Create output queue for chronological ordering
        output_queue = asyncio.Queue(maxsize=1000)
        
        # Start file tailing tasks
        tail_tasks = []
        for file_path in agent_files:
            agent_id = file_path.stem[-8:]
            task = asyncio.create_task(
                self.tail_file(file_path, agent_id, output_queue)
            )
            tail_tasks.append(task)
            
        # Start output processor
        output_task = asyncio.create_task(self.output_processor(output_queue))
        
        try:
            # Run until interrupted
            await asyncio.gather(*tail_tasks, output_task)
        except asyncio.CancelledError:
            pass
        finally:
            self.running = False
            
            # Cancel all tasks
            for task in tail_tasks:
                task.cancel()
            output_task.cancel()
            
            # Wait for cleanup
            await asyncio.gather(*tail_tasks, output_task, return_exceptions=True)
    
    def stop(self):
        """Stop the tailer"""
        self.running = False

def signal_handler(signum, frame, tailer):
    """Handle Ctrl+C gracefully"""
    print(f"\n\n👋 {Colors.BOLD}Shutting down log tailer...{Colors.RESET}")
    tailer.stop()

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Enhanced Multi-Agent Log Tailer with Swarm Detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Monitor agent-orchestrator logs
  %(prog)s --pattern "*multi-agent*"         # Custom pattern
  %(prog)s --projects-dir /custom/path       # Custom projects directory
  %(prog)s --include-historical              # Include older logs
        """
    )
    
    parser.add_argument(
        '--projects-dir',
        help='Claude projects directory (default: ~/.claude/projects)'
    )
    
    parser.add_argument(
        '--pattern', 
        default='*agent-orchestrator*',
        help='Project directory pattern to match (default: *agent-orchestrator*)'
    )
    
    parser.add_argument(
        '--include-historical',
        action='store_true',
        help='Include logs older than 24 hours'
    )
    
    args = parser.parse_args()
    
    # Create tailer
    tailer = AgentLogTailer(
        projects_dir=args.projects_dir,
        pattern=args.pattern,
        include_historical=args.include_historical
    )
    
    # Setup signal handler
    def handle_signal(signum, frame):
        signal_handler(signum, frame, tailer)
        
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    try:
        await tailer.run()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
        
    print("✅ Log tailer stopped.")

if __name__ == "__main__":
    asyncio.run(main())