#!/usr/bin/env python3
"""
Monitor for canary reactions - measures attention lag
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class ReactionMonitor:
    def __init__(self):
        self.rotation_dir = Path("/home/opsvi/master_root/.claude/rotation")
        self.canary_log = self.rotation_dir / "canary_deployments.json"
        self.chat_logs_dir = Path("/home/opsvi/master_root/apps/chat-search")

    def load_canaries(self) -> Dict:
        if self.canary_log.exists():
            with open(self.canary_log, "r") as f:
                return json.load(f)
        return {}

    def detect_reactions(self, text: str) -> List[str]:
        """Detect canary behaviors in text"""
        reactions = []

        # Detection patterns for each canary type
        patterns = {
            "emoji_response": r"^[🎭🎨🎯🔍🚀💡🎉🏴‍☠️📊🔒]",  # Starts with emoji
            "haiku_mode": r"#.*\n.*#.*\n.*#.*\n",  # Three-line comments
            "verbose_logging": r"INITIATING TOOL SEQUENCE",
            "question_everything": r"Is this really the best approach\?",
            "pirate_friday": r"(ahoy|arrr|matey|ye |avast)",
            "metric_obsession": r"(\d+ characters|\d+ bytes)",
            "paranoid_mode": r"Are you sure\?.+Really sure\?.+REALLY REALLY sure\?",
            "celebration_commits": r"WOOHOO! Another one for the history books!",
        }

        for canary_id, pattern in patterns.items():
            if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
                reactions.append(canary_id)

        return reactions

    def check_recent_logs(self, since_timestamp: Optional[datetime] = None) -> Dict:
        """Check recent chat logs for reactions"""
        results = {"reactions_found": [], "lag_measurements": []}

        canary_data = self.load_canaries()
        active_canaries = canary_data.get("active_canaries", {})

        # For each active canary, check if we see the expected reaction
        for file_path, canary_info in active_canaries.items():
            canary_id = canary_info["canary_id"]
            deployed_at = datetime.fromisoformat(canary_info["deployed_at"])

            # Would normally scan actual chat logs here
            # For testing, we'll simulate detection

            # Placeholder for actual log scanning
            reaction_detected = False  # Set to True when reaction found
            reaction_timestamp = None

            if reaction_detected and reaction_timestamp:
                lag_seconds = (reaction_timestamp - deployed_at).total_seconds()

                results["reactions_found"].append(
                    {
                        "canary_id": canary_id,
                        "file": file_path,
                        "deployed_at": deployed_at.isoformat(),
                        "detected_at": reaction_timestamp.isoformat(),
                        "lag_seconds": lag_seconds,
                        "lag_human": f"{lag_seconds/60:.1f} minutes"
                        if lag_seconds > 60
                        else f"{lag_seconds:.0f} seconds",
                    }
                )

                results["lag_measurements"].append(lag_seconds)

        # Calculate statistics
        if results["lag_measurements"]:
            results["statistics"] = {
                "average_lag": sum(results["lag_measurements"])
                / len(results["lag_measurements"]),
                "min_lag": min(results["lag_measurements"]),
                "max_lag": max(results["lag_measurements"]),
                "detection_rate": len(results["reactions_found"])
                / len(active_canaries)
                * 100,
            }

        return results

    def generate_report(self) -> str:
        """Generate a secret performance report"""
        canary_data = self.load_canaries()
        triggered = canary_data.get("triggered_canaries", [])
        active = canary_data.get("active_canaries", {})

        report = "=== CLASSIFIED CANARY REPORT ===\n\n"

        report += f"Active Canaries: {len(active)}\n"
        report += f"Triggered Canaries: {len(triggered)}\n\n"

        if triggered:
            report += "Detection Times:\n"
            for canary in triggered:
                if canary.get("lag_seconds"):
                    lag = canary["lag_seconds"]
                    if lag > 3600:
                        lag_str = f"{lag/3600:.1f} hours"
                    elif lag > 60:
                        lag_str = f"{lag/60:.1f} minutes"
                    else:
                        lag_str = f"{lag:.0f} seconds"

                    report += f"  - {canary['canary_id']}: {lag_str}\n"

        if active:
            report += "\nStill Active (Undetected):\n"
            for path, info in active.items():
                deployed = datetime.fromisoformat(info["deployed_at"])
                age = (datetime.now() - deployed).total_seconds()

                if age > 3600:
                    age_str = f"{age/3600:.1f} hours ago"
                else:
                    age_str = f"{age/60:.0f} minutes ago"

                report += f"  - {info['canary_id']} (deployed {age_str})\n"

        return report


def main():
    monitor = ReactionMonitor()

    print("Checking for canary reactions...")
    results = monitor.check_recent_logs()

    if results["reactions_found"]:
        print(f"\n🎯 REACTIONS DETECTED: {len(results['reactions_found'])}")
        for reaction in results["reactions_found"]:
            print(f"  - {reaction['canary_id']}: {reaction['lag_human']} lag")

    print("\n" + monitor.generate_report())


if __name__ == "__main__":
    main()
