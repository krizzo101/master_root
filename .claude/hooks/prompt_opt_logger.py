#!/usr/bin/env python3
"""
Simple logger for prompt optimization to track what's happening.
Logs to a JSON file for easy analysis.
"""

import json
import os
from datetime import datetime
from pathlib import Path


class PromptOptLogger:
    def __init__(self):
        self.log_dir = Path("/home/opsvi/master_root/.claude/hooks/logs/prompt_opt")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = (
            self.log_dir / f"prompt_opt_{datetime.now().strftime('%Y%m%d')}.jsonl"
        )

    def log(self, event_type, data):
        """Log an event with timestamp and data."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            "data": data,
        }

        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            # Silent fail to not break the hook
            pass

    def log_optimization(
        self, original, optimized, mode, triggered_by=None, cognitive=None
    ):
        """Log a complete optimization event."""
        self.log(
            "optimization",
            {
                "mode": mode,
                "triggered_by": triggered_by,
                "original_prompt": original[:200]
                if original
                else None,  # First 200 chars
                "optimized_prompt": optimized[:200] if optimized else None,
                "cognitive_guidance": cognitive[:100]
                if cognitive
                else None,  # First 100 chars
                "original_length": len(original) if original else 0,
                "optimized_length": len(optimized) if optimized else 0,
            },
        )

    def log_skip(self, reason, prompt=None):
        """Log when optimization is skipped."""
        self.log(
            "skip",
            {"reason": reason, "prompt_preview": prompt[:100] if prompt else None},
        )

    def log_error(self, error_msg, context=None):
        """Log errors."""
        self.log("error", {"error": str(error_msg), "context": context})

    def get_stats(self):
        """Read today's log and return statistics."""
        if not self.log_file.exists():
            return {}

        stats = {
            "total_requests": 0,
            "optimized": 0,
            "skipped": 0,
            "errors": 0,
            "modes": {},
        }

        try:
            with open(self.log_file, "r") as f:
                for line in f:
                    entry = json.loads(line)
                    stats["total_requests"] += 1

                    if entry["event"] == "optimization":
                        stats["optimized"] += 1
                        mode = entry["data"].get("mode", "unknown")
                        stats["modes"][mode] = stats["modes"].get(mode, 0) + 1
                    elif entry["event"] == "skip":
                        stats["skipped"] += 1
                    elif entry["event"] == "error":
                        stats["errors"] += 1
        except Exception:
            pass

        return stats


# Quick viewer utility
if __name__ == "__main__":
    import sys

    logger = PromptOptLogger()

    if len(sys.argv) > 1 and sys.argv[1] == "stats":
        stats = logger.get_stats()
        print(json.dumps(stats, indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "tail":
        # Show last 10 entries
        if logger.log_file.exists():
            with open(logger.log_file, "r") as f:
                lines = f.readlines()
                for line in lines[-10:]:
                    entry = json.loads(line)
                    print(f"{entry['timestamp']} | {entry['event']} | ", end="")
                    if entry["event"] == "optimization":
                        print(
                            f"Mode: {entry['data'].get('mode')} | Triggered: {entry['data'].get('triggered_by')}"
                        )
                    elif entry["event"] == "skip":
                        print(f"Reason: {entry['data'].get('reason')}")
                    else:
                        print(json.dumps(entry["data"])[:100])
    else:
        print("Usage:")
        print("  python prompt_opt_logger.py stats  # Show statistics")
        print("  python prompt_opt_logger.py tail   # Show last 10 entries")
