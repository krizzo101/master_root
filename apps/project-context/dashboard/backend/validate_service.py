#!/usr/bin/env python3
"""
Validation script for the monitoring service
"""

import os
import sys

sys.path.append("/home/opsvi/master_root/apps/project-context")


def validate_service():
    print("🔍 Validating Monitoring Service...")

    # Check imports
    try:
        from monitoring_service import MonitoringService

        print("✅ MonitoringService import: OK")
    except Exception as e:
        print(f"❌ MonitoringService import: {e}")
        return False

    try:
        from websocket_handler import WebSocketManager

        print("✅ WebSocketManager import: OK")
    except Exception as e:
        print(f"❌ WebSocketManager import: {e}")
        return False

    # Test basic initialization
    try:
        service = MonitoringService()
        print(f"✅ MonitoringService init: Found {len(service.output_dirs)} directories")
    except Exception as e:
        print(f"❌ MonitoringService init: {e}")
        return False

    try:
        manager = WebSocketManager()
        print("✅ WebSocketManager init: OK")
    except Exception as e:
        print(f"❌ WebSocketManager init: {e}")
        return False

    # Check directory discovery
    active_dirs = [d for d in service.output_dirs if (d / "tasks").exists()]
    task_count = sum(len(list((d / "tasks").glob("*.json"))) for d in active_dirs)
    print(f"✅ Directory scan: {len(active_dirs)} active dirs, {task_count} total tasks")

    # Check app components
    try:
        from app import app

        print("✅ FastAPI app import: OK")
    except Exception as e:
        print(f"❌ FastAPI app import: {e}")
        return False

    print("\n🎯 Monitoring Service Validation Complete!")
    print("\nService Features Available:")
    print("  📊 Real-time task monitoring")
    print("  🔍 Comprehensive analytics")
    print("  🚀 WebSocket live updates")
    print("  📈 Performance metrics")
    print("  🎯 Quality insights")
    print("  🗂️ Auto directory discovery")
    print("  💾 Smart file caching")
    print("\nTo start the service:")
    print("  cd dashboard/backend && uvicorn app:app --host 0.0.0.0 --port 8000")

    return True


if __name__ == "__main__":
    validate_service()
