#!/usr/bin/env python3
import json
import os
import platform
import socket
import uuid
from datetime import datetime
from pathlib import Path


def gather_system_info():
    """Gather comprehensive system information with error handling."""
    system_info = {}

    try:
        system_info["timestamp"] = datetime.now().isoformat()
    except Exception as e:
        system_info["timestamp"] = f"Error: {str(e)}"

    try:
        system_info["uuid"] = str(uuid.uuid4())
    except Exception as e:
        system_info["uuid"] = f"Error: {str(e)}"

    try:
        system_info["hostname"] = socket.gethostname()
    except Exception as e:
        system_info["hostname"] = f"Error: {str(e)}"

    try:
        system_info["platform"] = {
            "system": platform.system(),
            "node": platform.node(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        }
    except Exception as e:
        system_info["platform"] = f"Error: {str(e)}"

    try:
        system_info["python_version"] = platform.python_version()
    except Exception as e:
        system_info["python_version"] = f"Error: {str(e)}"

    try:
        system_info["architecture"] = platform.architecture()
    except Exception as e:
        system_info["architecture"] = f"Error: {str(e)}"

    try:
        system_info["cpu_count"] = os.cpu_count()
    except Exception as e:
        system_info["cpu_count"] = f"Error: {str(e)}"

    try:
        system_info["current_directory"] = os.getcwd()
    except Exception as e:
        system_info["current_directory"] = f"Error: {str(e)}"

    try:
        system_info["user"] = os.environ.get("USER", "unknown")
    except Exception as e:
        system_info["user"] = f"Error: {str(e)}"

    try:
        system_info["home_directory"] = str(Path.home())
    except Exception as e:
        system_info["home_directory"] = f"Error: {str(e)}"

    try:
        if hasattr(os, "uname"):
            uname = os.uname()
            system_info["os_details"] = {
                "sysname": uname.sysname,
                "nodename": uname.nodename,
                "release": uname.release,
                "version": uname.version,
                "machine": uname.machine,
            }
    except Exception as e:
        system_info["os_details"] = f"Error: {str(e)}"

    return system_info


def save_system_info(filepath="system_info.json"):
    """Save system information to a JSON file with error handling."""
    try:
        info = gather_system_info()

        with open(filepath, "w") as f:
            json.dump(info, f, indent=2, default=str)

        print(f"✓ System info saved to {filepath}")
        print(f"  UUID: {info.get('uuid', 'N/A')}")
        print(f"  Timestamp: {info.get('timestamp', 'N/A')}")
        return True

    except PermissionError:
        print(f"✗ Permission denied: Cannot write to {filepath}")
        return False
    except IOError as e:
        print(f"✗ I/O error occurred: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = save_system_info()
    if not success:
        print("\nAttempting to save to temporary directory...")
        temp_path = f"/tmp/system_info_{uuid.uuid4().hex[:8]}.json"  # nosec B108
        if save_system_info(temp_path):
            print(f"✓ Backup saved to {temp_path}")
