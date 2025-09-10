#!/usr/bin/env python3
"""
Stealth deployment script - runs rotation without fanfare
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
from datetime import datetime

from claude_rotation_manager import ClaudeRotationManager


def deploy_stealth_rotation():
    """Deploy canaries quietly"""
    manager = ClaudeRotationManager()

    # Deploy with 40% canary rate for faster testing
    rotations = manager.rotate_instructions(
        directories=["apps/agent-orchestrator", "apps/chat-search", "."],
        canary_probability=0.4,
    )

    # Log deployment time (hidden from agents)
    deployment_log = {
        "deployed_at": datetime.now().isoformat(),
        "locations": [r["file"] for r in rotations],
        "canaries": [r for r in rotations if r["canary_deployed"]],
    }

    log_path = manager.rotation_dir / "stealth_deployment.json"
    with open(log_path, "w") as f:
        json.dump(deployment_log, f, indent=2)

    print("Configuration updated successfully.")  # Innocent message

    # Show secret metrics only to you
    print("\n--- CLASSIFIED METRICS ---")
    for rotation in rotations:
        if rotation["canary_deployed"]:
            print(
                f"🎯 Canary '{rotation['canary_deployed']}' deployed to {rotation['file']}"
            )

    return rotations


if __name__ == "__main__":
    deploy_stealth_rotation()
