#!/usr/bin/env python3
"""
Token Usage Monitor for 18 Parallel Execution

Monitors Claude token pool usage and parallel execution efficiency
"""
import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Add paths for imports
sys.path.append("/home/opsvi/master_root/apps/agent-orchestrator/src")


class TokenUsageMonitor:
    """Monitor token pool usage and parallel execution efficiency"""

    def __init__(self):
        self.base_dir = Path("/home/opsvi/master_root/apps/project-context")
        self.tokens_file = Path.home() / ".claude" / "tokens.json"

    def get_token_configuration(self) -> Dict:
        """Get current token pool configuration"""

        config = {
            "env_token": bool(os.environ.get("CLAUDE_CODE_TOKEN")),
            "env_tokens": os.environ.get("CLAUDE_CODE_TOKENS", "").split(",")
            if os.environ.get("CLAUDE_CODE_TOKENS")
            else [],
            "tokens_file_exists": self.tokens_file.exists(),
            "total_tokens": 0,
            "unique_tokens": 0,
            "configured_for_parallel": 0,
        }

        # Count environment tokens
        if config["env_token"]:
            config["total_tokens"] += 1
        config["total_tokens"] += len([t for t in config["env_tokens"] if t.strip()])

        # Read tokens file
        if config["tokens_file_exists"]:
            try:
                with open(self.tokens_file) as f:
                    data = json.load(f)

                file_tokens = data.get("tokens", [])
                config["total_tokens"] += len(file_tokens)
                config["configured_for_parallel"] = data.get(
                    "configured_for_parallel", 0
                )

                # Count unique tokens across all sources
                all_tokens = set()

                if config["env_token"]:
                    all_tokens.add(os.environ.get("CLAUDE_CODE_TOKEN", ""))

                for token in config["env_tokens"]:
                    if token.strip():
                        all_tokens.add(token.strip())

                for token in file_tokens:
                    all_tokens.add(token)

                config["unique_tokens"] = len([t for t in all_tokens if t])

            except Exception as e:
                config["tokens_file_error"] = str(e)

        return config

    def test_token_loading(self) -> Dict:
        """Test actual token loading using TokenLoader"""

        try:
            from token_loader import TokenLoader

            loader = TokenLoader()
            tokens = loader.load_tokens()

            return {
                "success": True,
                "tokens_loaded": len(tokens),
                "unique_tokens": len(set(tokens)),
                "tokens_preview": [t[:20] + "..." for t in tokens[:3]],
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def estimate_parallel_capacity(self) -> Dict:
        """Estimate optimal parallel execution capacity"""

        token_config = self.get_token_configuration()
        loading_test = self.test_token_loading()

        if loading_test["success"]:
            available_tokens = loading_test["tokens_loaded"]
        else:
            available_tokens = token_config["total_tokens"]

        # Calculate optimal parallel settings
        optimal_parallel = min(available_tokens, 18)  # Framework limit is ~18-20

        # Estimate performance improvement
        baseline_parallel = 3  # Original limitation
        speedup_factor = (
            optimal_parallel / baseline_parallel if baseline_parallel > 0 else 1
        )

        return {
            "available_tokens": available_tokens,
            "optimal_parallel": optimal_parallel,
            "baseline_parallel": baseline_parallel,
            "speedup_factor": speedup_factor,
            "efficiency": optimal_parallel / available_tokens
            if available_tokens > 0
            else 0,
        }

    def check_active_executions(self) -> List[Dict]:
        """Check for active parallel executions"""

        import subprocess

        active_executions = []

        try:
            result = subprocess.run(["ps", "aux"], capture_output=True, text=True)

            for line in result.stdout.split("\n"):
                if any(
                    script in line
                    for script in [
                        "execute_phase1_generic.py",
                        "execute_phase1_practical.py",
                        "execute_phase1_completion.py",
                        "execute_phase2",
                        "execute_phase3",
                    ]
                ):
                    parts = line.split()
                    if len(parts) >= 11:
                        active_executions.append(
                            {
                                "pid": parts[1],
                                "script": parts[10].split("/")[-1],
                                "cpu": parts[2],
                                "memory": parts[3],
                                "start_time": parts[8],
                            }
                        )

        except Exception as e:
            active_executions.append({"error": str(e)})

        return active_executions

    def get_recent_session_activity(self, minutes: int = 10) -> Dict:
        """Get recent Claude session activity"""

        claude_logs_dir = Path.home() / ".claude" / "projects"
        cutoff_time = time.time() - (minutes * 60)

        recent_activity = {
            "total_sessions": 0,
            "active_sessions": 0,
            "total_size_mb": 0,
            "recent_sessions": [],
        }

        try:
            for project_dir in claude_logs_dir.glob("*"):
                if project_dir.is_dir():
                    for session_file in project_dir.glob("*.jsonl"):
                        stat = session_file.stat()

                        recent_activity["total_sessions"] += 1
                        recent_activity["total_size_mb"] += stat.st_size / (1024 * 1024)

                        if stat.st_mtime > cutoff_time:
                            recent_activity["active_sessions"] += 1
                            recent_activity["recent_sessions"].append(
                                {
                                    "session_id": session_file.stem,
                                    "size_mb": stat.st_size / (1024 * 1024),
                                    "last_modified": datetime.fromtimestamp(
                                        stat.st_mtime
                                    ).strftime("%H:%M:%S"),
                                }
                            )

        except Exception as e:
            recent_activity["error"] = str(e)

        return recent_activity

    def print_dashboard(self):
        """Print comprehensive token usage dashboard"""

        print("🔧 TOKEN USAGE & PARALLEL EXECUTION MONITOR")
        print("=" * 60)
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Token configuration
        print("🪙 TOKEN CONFIGURATION")
        print("-" * 25)

        token_config = self.get_token_configuration()
        print(f"   Environment token: {'✅' if token_config['env_token'] else '❌'}")
        print(f"   Environment tokens list: {len(token_config['env_tokens'])} tokens")
        print(f"   Tokens file: {'✅' if token_config['tokens_file_exists'] else '❌'}")
        print(f"   Total configured tokens: {token_config['total_tokens']}")
        print(f"   Unique tokens: {token_config['unique_tokens']}")
        print(f"   Configured for parallel: {token_config['configured_for_parallel']}")
        print()

        # Token loading test
        print("🧪 TOKEN LOADING TEST")
        print("-" * 22)

        loading_test = self.test_token_loading()
        if loading_test["success"]:
            print(f"   ✅ TokenLoader working")
            print(f"   📊 Tokens loaded: {loading_test['tokens_loaded']}")
            print(f"   🔍 Unique tokens: {loading_test['unique_tokens']}")
            print(f"   👀 Sample tokens: {', '.join(loading_test['tokens_preview'])}")
        else:
            print(f"   ❌ TokenLoader failed: {loading_test['error']}")
        print()

        # Parallel capacity analysis
        print("⚡ PARALLEL EXECUTION ANALYSIS")
        print("-" * 30)

        capacity = self.estimate_parallel_capacity()
        print(f"   🔋 Available tokens: {capacity['available_tokens']}")
        print(f"   🎯 Optimal parallel: {capacity['optimal_parallel']}")
        print(f"   📏 Baseline parallel: {capacity['baseline_parallel']}")
        print(f"   🚀 Speedup factor: {capacity['speedup_factor']:.1f}x")
        print(f"   📊 Token efficiency: {capacity['efficiency']:.1%}")
        print()

        # Active executions
        print("🏃 ACTIVE EXECUTIONS")
        print("-" * 20)

        active_executions = self.check_active_executions()
        if active_executions:
            for execution in active_executions:
                if "error" in execution:
                    print(f"   ❌ Error: {execution['error']}")
                else:
                    print(f"   🔄 PID {execution['pid']}: {execution['script']}")
                    print(
                        f"      CPU: {execution['cpu']}%, Memory: {execution['memory']}%"
                    )
        else:
            print("   ⏸️  No active executions detected")
        print()

        # Recent session activity
        print("📊 RECENT SESSION ACTIVITY (10 minutes)")
        print("-" * 35)

        activity = self.get_recent_session_activity()
        if "error" in activity:
            print(f"   ❌ Error: {activity['error']}")
        else:
            print(f"   📈 Total sessions: {activity['total_sessions']}")
            print(f"   🔥 Active sessions: {activity['active_sessions']}")
            print(f"   💾 Total log size: {activity['total_size_mb']:.1f} MB")

            if activity["recent_sessions"]:
                print(f"   Recent activity:")
                for session in activity["recent_sessions"][:5]:
                    print(
                        f"      • {session['session_id']} ({session['size_mb']:.1f}MB @ {session['last_modified']})"
                    )
        print()

        # Recommendations
        print("💡 OPTIMIZATION RECOMMENDATIONS")
        print("-" * 32)

        if capacity["optimal_parallel"] < 18:
            print(f"   🔧 Add more tokens to reach 18 parallel execution")
            print(f"      Currently: {capacity['optimal_parallel']} parallel")
            print(f"      Target: 18 parallel for maximum speed")
        else:
            print(f"   ✅ Token configuration is optimal for maximum parallel execution")

        if loading_test["success"] and loading_test["unique_tokens"] == 1:
            print(f"   ⚠️  Only 1 unique token - all tokens are duplicates")
            print(f"      This may cause rate limiting with high parallel execution")
        else:
            print(f"   ✅ Using {capacity['unique_tokens']} unique tokens")

    def watch_mode(self, refresh_seconds: int = 15):
        """Continuous monitoring mode"""
        print(
            f"👁️  TOKEN MONITOR WATCH MODE - Refreshing every {refresh_seconds} seconds"
        )
        print("   Press Ctrl+C to exit")
        print()

        try:
            while True:
                # Clear screen
                os.system("clear" if os.name == "posix" else "cls")

                self.print_dashboard()

                print(f"🔄 Auto-refresh in {refresh_seconds}s... (Ctrl+C to exit)")
                time.sleep(refresh_seconds)

        except KeyboardInterrupt:
            print(f"\n👋 Token monitoring stopped")


def main():
    """Main monitoring interface"""
    import argparse

    parser = argparse.ArgumentParser(description="Token Usage Monitor")
    parser.add_argument(
        "--watch", action="store_true", help="Continuous monitoring mode"
    )
    parser.add_argument(
        "--refresh",
        type=int,
        default=15,
        help="Refresh interval in seconds (default: 15)",
    )

    args = parser.parse_args()

    monitor = TokenUsageMonitor()

    if args.watch:
        monitor.watch_mode(args.refresh)
    else:
        monitor.print_dashboard()


if __name__ == "__main__":
    main()
