#!/usr/bin/env python3
"""
WSL2 Memory Monitor and Manager
Monitors memory usage in WSL2, provides alerts, and performs automatic cleanup
"""

import os
import sys
import time
import json
import subprocess
import psutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import argparse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class WSLMemoryMonitor:
    def __init__(self, config_file: str = None):
        """Initialize the WSL Memory Monitor"""
        self.config_file = config_file or Path.home() / ".config" / "wsl_memory_monitor.json"
        self.log_file = Path.home() / ".local" / "log" / "wsl_memory_monitor.log"
        self.state_file = Path.home() / ".local" / "state" / "wsl_memory_state.json"
        
        # Create directories if they don't exist
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self.config = self.load_config()
        
        # Initialize state
        self.state = self.load_state()
        
    def load_config(self) -> Dict:
        """Load configuration from file or create default"""
        default_config = {
            "thresholds": {
                "warning_percent": 70,
                "critical_percent": 85,
                "swap_warning_percent": 50
            },
            "cleanup": {
                "auto_cleanup": True,
                "cleanup_threshold_percent": 80,
                "min_cleanup_interval_seconds": 300,
                "drop_caches": True,
                "kill_orphaned_processes": True,
                "compact_memory": True
            },
            "monitoring": {
                "check_interval_seconds": 60,
                "detailed_logging": False
            },
            "notifications": {
                "enabled": False,
                "desktop_notifications": True,
                "email_notifications": False,
                "email_config": {
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587,
                    "from_email": "",
                    "to_email": "",
                    "password": ""
                }
            },
            "cursor_specific": {
                "monitor_cursor_processes": True,
                "max_cursor_servers": 3,
                "max_extension_memory_mb": 1024,
                "restart_cursor_on_critical": False
            }
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults
                    return {**default_config, **loaded_config}
            except Exception as e:
                self.logger.error(f"Error loading config: {e}")
                return default_config
        else:
            # Create default config file
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=4)
            self.logger.info(f"Created default config at {self.config_file}")
            return default_config
    
    def load_state(self) -> Dict:
        """Load state from file"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            "last_cleanup": 0,
            "cleanup_count": 0,
            "alert_count": 0,
            "last_alert": 0
        }
    
    def save_state(self):
        """Save state to file"""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=4)
    
    def get_memory_info(self) -> Dict:
        """Get current memory information"""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # Get WSL-specific memory info
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
                
            # Parse cache information
            cached = 0
            buffers = 0
            for line in meminfo.split('\n'):
                if line.startswith('Cached:'):
                    cached = int(line.split()[1]) * 1024  # Convert KB to bytes
                elif line.startswith('Buffers:'):
                    buffers = int(line.split()[1]) * 1024
        except:
            cached = 0
            buffers = 0
        
        return {
            "total": mem.total,
            "available": mem.available,
            "used": mem.used,
            "free": mem.free,
            "percent": mem.percent,
            "cached": cached,
            "buffers": buffers,
            "swap_total": swap.total,
            "swap_used": swap.used,
            "swap_free": swap.free,
            "swap_percent": swap.percent
        }
    
    def get_cursor_processes(self) -> List[Dict]:
        """Get information about Cursor/VS Code processes"""
        cursor_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if '.cursor-server' in cmdline or 'code-server' in cmdline:
                    cursor_processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'memory_mb': proc.info['memory_info'].rss / 1024 / 1024,
                        'cmdline': cmdline[:200]  # Truncate long command lines
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return sorted(cursor_processes, key=lambda x: x['memory_mb'], reverse=True)
    
    def get_top_memory_processes(self, n: int = 10) -> List[Dict]:
        """Get top N memory-consuming processes"""
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'username']):
            try:
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'memory_mb': proc.info['memory_info'].rss / 1024 / 1024,
                    'username': proc.info['username']
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return sorted(processes, key=lambda x: x['memory_mb'], reverse=True)[:n]
    
    def drop_caches(self) -> bool:
        """Drop Linux caches to free memory"""
        try:
            # Sync first to flush filesystem buffers
            subprocess.run(['sync'], check=True)
            
            # Drop caches (requires sudo)
            # 1 = free pagecache
            # 2 = free dentries and inodes
            # 3 = free pagecache, dentries and inodes
            result = subprocess.run(
                ['sudo', 'sh', '-c', 'echo 3 > /proc/sys/vm/drop_caches'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.logger.info("Successfully dropped caches")
                return True
            else:
                self.logger.error(f"Failed to drop caches: {result.stderr}")
                return False
        except Exception as e:
            self.logger.error(f"Error dropping caches: {e}")
            return False
    
    def compact_memory(self) -> bool:
        """Compact memory to reduce fragmentation"""
        try:
            result = subprocess.run(
                ['sudo', 'sh', '-c', 'echo 1 > /proc/sys/vm/compact_memory'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.logger.info("Successfully compacted memory")
                return True
            else:
                self.logger.error(f"Failed to compact memory: {result.stderr}")
                return False
        except Exception as e:
            self.logger.error(f"Error compacting memory: {e}")
            return False
    
    def kill_orphaned_cursor_processes(self) -> int:
        """Kill orphaned Cursor/VS Code processes"""
        killed_count = 0
        cursor_procs = self.get_cursor_processes()
        
        # Group by server instance
        server_groups = {}
        for proc in cursor_procs:
            if 'bootstrap-fork' in proc['cmdline']:
                # This is a main server process
                server_groups[proc['pid']] = []
        
        # Keep only the most recent N server instances
        if len(server_groups) > self.config['cursor_specific']['max_cursor_servers']:
            # Sort by PID (usually correlates with age)
            sorted_servers = sorted(server_groups.keys())
            servers_to_kill = sorted_servers[:-self.config['cursor_specific']['max_cursor_servers']]
            
            for pid in servers_to_kill:
                try:
                    os.kill(pid, 9)
                    killed_count += 1
                    self.logger.info(f"Killed orphaned Cursor server process {pid}")
                except:
                    pass
        
        # Kill extension hosts using too much memory
        max_ext_mem = self.config['cursor_specific']['max_extension_memory_mb']
        for proc in cursor_procs:
            if 'extensionHost' in proc['cmdline'] and proc['memory_mb'] > max_ext_mem:
                try:
                    os.kill(proc['pid'], 9)
                    killed_count += 1
                    self.logger.info(f"Killed high-memory extension host {proc['pid']} ({proc['memory_mb']:.1f} MB)")
                except:
                    pass
        
        return killed_count
    
    def perform_cleanup(self, force: bool = False) -> Dict:
        """Perform memory cleanup operations"""
        # Check if cleanup is needed
        current_time = time.time()
        min_interval = self.config['cleanup']['min_cleanup_interval_seconds']
        
        if not force and (current_time - self.state['last_cleanup']) < min_interval:
            return {"skipped": True, "reason": "Too soon since last cleanup"}
        
        self.logger.info("Starting memory cleanup...")
        results = {
            "timestamp": datetime.now().isoformat(),
            "actions": []
        }
        
        # Get memory before cleanup
        mem_before = self.get_memory_info()
        results["memory_before"] = {
            "percent": mem_before["percent"],
            "used_gb": mem_before["used"] / 1024**3
        }
        
        # Drop caches
        if self.config['cleanup']['drop_caches']:
            if self.drop_caches():
                results["actions"].append("dropped_caches")
        
        # Compact memory
        if self.config['cleanup']['compact_memory']:
            if self.compact_memory():
                results["actions"].append("compacted_memory")
        
        # Kill orphaned processes
        if self.config['cleanup']['kill_orphaned_processes']:
            killed = self.kill_orphaned_cursor_processes()
            if killed > 0:
                results["actions"].append(f"killed_{killed}_processes")
        
        # Wait a bit for memory to be freed
        time.sleep(2)
        
        # Get memory after cleanup
        mem_after = self.get_memory_info()
        results["memory_after"] = {
            "percent": mem_after["percent"],
            "used_gb": mem_after["used"] / 1024**3
        }
        
        # Calculate freed memory
        freed_gb = (mem_before["used"] - mem_after["used"]) / 1024**3
        results["freed_gb"] = freed_gb
        
        # Update state
        self.state['last_cleanup'] = current_time
        self.state['cleanup_count'] += 1
        self.save_state()
        
        self.logger.info(f"Cleanup completed. Freed {freed_gb:.2f} GB")
        
        return results
    
    def send_notification(self, title: str, message: str, severity: str = "info"):
        """Send notification to user"""
        if not self.config['notifications']['enabled']:
            return
        
        # Desktop notification
        if self.config['notifications']['desktop_notifications']:
            try:
                # Try to use notify-send if available
                subprocess.run(
                    ['notify-send', '-u', 'critical' if severity == 'critical' else 'normal', title, message],
                    capture_output=True
                )
            except:
                pass
        
        # Email notification
        if self.config['notifications']['email_notifications'] and severity in ['warning', 'critical']:
            self.send_email_notification(title, message)
    
    def send_email_notification(self, subject: str, body: str):
        """Send email notification"""
        email_config = self.config['notifications']['email_config']
        
        if not all([email_config['from_email'], email_config['to_email'], email_config['password']]):
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = email_config['from_email']
            msg['To'] = email_config['to_email']
            msg['Subject'] = f"WSL Memory Alert: {subject}"
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
                server.starttls()
                server.login(email_config['from_email'], email_config['password'])
                server.send_message(msg)
                
            self.logger.info("Email notification sent")
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
    
    def check_memory_status(self) -> Dict:
        """Check current memory status and trigger actions if needed"""
        mem_info = self.get_memory_info()
        status = {
            "timestamp": datetime.now().isoformat(),
            "memory_percent": mem_info["percent"],
            "swap_percent": mem_info["swap_percent"],
            "alerts": [],
            "actions": []
        }
        
        # Check memory thresholds
        if mem_info["percent"] >= self.config['thresholds']['critical_percent']:
            status["alerts"].append("CRITICAL")
            self.send_notification(
                "Critical Memory Usage",
                f"Memory usage is at {mem_info['percent']:.1f}%",
                "critical"
            )
            
            # Perform automatic cleanup if enabled
            if self.config['cleanup']['auto_cleanup']:
                cleanup_result = self.perform_cleanup(force=True)
                status["actions"].append(cleanup_result)
                
        elif mem_info["percent"] >= self.config['thresholds']['warning_percent']:
            status["alerts"].append("WARNING")
            self.send_notification(
                "High Memory Usage",
                f"Memory usage is at {mem_info['percent']:.1f}%",
                "warning"
            )
            
            # Perform cleanup if above threshold
            if self.config['cleanup']['auto_cleanup'] and \
               mem_info["percent"] >= self.config['cleanup']['cleanup_threshold_percent']:
                cleanup_result = self.perform_cleanup()
                if not cleanup_result.get("skipped"):
                    status["actions"].append(cleanup_result)
        
        # Check swap usage
        if mem_info["swap_percent"] >= self.config['thresholds']['swap_warning_percent']:
            status["alerts"].append("SWAP_WARNING")
            self.send_notification(
                "High Swap Usage",
                f"Swap usage is at {mem_info['swap_percent']:.1f}%",
                "warning"
            )
        
        return status
    
    def monitor_loop(self):
        """Main monitoring loop"""
        self.logger.info("Starting WSL Memory Monitor")
        self.logger.info(f"Configuration: {json.dumps(self.config, indent=2)}")
        
        while True:
            try:
                status = self.check_memory_status()
                
                if self.config['monitoring']['detailed_logging'] or status["alerts"]:
                    self.logger.info(f"Status: {json.dumps(status, indent=2)}")
                
                # Log Cursor processes periodically
                if self.config['cursor_specific']['monitor_cursor_processes']:
                    cursor_procs = self.get_cursor_processes()
                    if cursor_procs:
                        total_cursor_mem = sum(p['memory_mb'] for p in cursor_procs)
                        self.logger.info(f"Cursor processes: {len(cursor_procs)}, "
                                       f"Total memory: {total_cursor_mem:.1f} MB")
                
            except KeyboardInterrupt:
                self.logger.info("Monitor stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Error in monitor loop: {e}")
            
            time.sleep(self.config['monitoring']['check_interval_seconds'])
    
    def print_status(self):
        """Print current memory status"""
        mem_info = self.get_memory_info()
        cursor_procs = self.get_cursor_processes()
        top_procs = self.get_top_memory_processes(5)
        
        print("\n" + "="*60)
        print("WSL2 MEMORY STATUS")
        print("="*60)
        
        print(f"\n📊 Memory Usage:")
        print(f"  Total:     {mem_info['total']/1024**3:.1f} GB")
        print(f"  Used:      {mem_info['used']/1024**3:.1f} GB ({mem_info['percent']:.1f}%)")
        print(f"  Available: {mem_info['available']/1024**3:.1f} GB")
        print(f"  Cached:    {mem_info['cached']/1024**3:.1f} GB")
        print(f"  Buffers:   {mem_info['buffers']/1024**3:.1f} GB")
        
        print(f"\n💾 Swap Usage:")
        print(f"  Total: {mem_info['swap_total']/1024**3:.1f} GB")
        print(f"  Used:  {mem_info['swap_used']/1024**3:.1f} GB ({mem_info['swap_percent']:.1f}%)")
        
        print(f"\n🖥️  Cursor/VS Code Processes ({len(cursor_procs)} total):")
        for proc in cursor_procs[:5]:
            print(f"  PID {proc['pid']:6d}: {proc['memory_mb']:8.1f} MB - {proc['name']}")
        
        if len(cursor_procs) > 5:
            print(f"  ... and {len(cursor_procs)-5} more")
        
        print(f"\n🔝 Top Memory Consumers:")
        for proc in top_procs:
            print(f"  PID {proc['pid']:6d}: {proc['memory_mb']:8.1f} MB - {proc['name']} ({proc['username']})")
        
        print("\n" + "="*60)

def main():
    parser = argparse.ArgumentParser(description='WSL2 Memory Monitor and Manager')
    parser.add_argument('command', choices=['monitor', 'status', 'cleanup', 'config'],
                       help='Command to execute')
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--force', action='store_true', help='Force cleanup')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon')
    
    args = parser.parse_args()
    
    monitor = WSLMemoryMonitor(args.config)
    
    if args.command == 'monitor':
        if args.daemon:
            # Fork to background
            pid = os.fork()
            if pid > 0:
                print(f"Monitor started with PID {pid}")
                sys.exit(0)
        monitor.monitor_loop()
    
    elif args.command == 'status':
        monitor.print_status()
    
    elif args.command == 'cleanup':
        result = monitor.perform_cleanup(force=args.force)
        print(json.dumps(result, indent=2))
    
    elif args.command == 'config':
        print(json.dumps(monitor.config, indent=2))
        print(f"\nConfiguration file: {monitor.config_file}")

if __name__ == "__main__":
    main()