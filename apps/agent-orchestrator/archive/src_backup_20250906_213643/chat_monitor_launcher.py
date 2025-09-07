"""
Chat Monitor Auto-Launcher for Orchestrators

Automatically opens chat monitor windows when orchestrators start,
providing immediate visibility into agent collaboration.
"""

import os
import subprocess
import time
from pathlib import Path
from typing import List, Optional


class ChatMonitorLauncher:
    """
    Launches chat monitor windows for orchestrator runs.

    Usage in orchestrator:
    ```python
    from chat_monitor_launcher import ChatMonitorLauncher

    # Auto-launch monitor when orchestrator starts
    launcher = ChatMonitorLauncher()
    monitor_window = launcher.launch_for_run(
        run_id=self.run_id,
        title="Research Pipeline Monitor",
        focus_mode="communication"
    )
    ```
    """

    def __init__(self):
        self.launched_windows: List[subprocess.Popen] = []
        self.display = os.getenv("DISPLAY", ":0")

    def launch_for_run(
        self,
        run_id: str,
        title: Optional[str] = None,
        focus_mode: str = "all",
        geometry: str = "120x40+100+100",
    ) -> Optional[subprocess.Popen]:
        """
        Launch chat monitor window for specific orchestrator run.

        Args:
            run_id: Orchestrator run ID to monitor
            title: Window title (auto-generated if None)
            focus_mode: Chat monitor focus (all, communication, workspace, handoffs)
            geometry: Window geometry (widthxheight+x+y)

        Returns:
            Subprocess handle for the launched window, or None if failed
        """
        if not self._check_x11_available():
            print("⚠️  X11 display not available - cannot launch chat monitor window")
            return None

        if not title:
            title = f"Chat Monitor - {run_id[:12]}"

        try:
            # Build command to launch chat monitor in xterm
            cmd = [
                "xterm",
                "-title",
                title,
                "-geometry",
                geometry,
                "-bg",
                "black",
                "-fg",
                "green",
                "-fa",
                "monospace",
                "-fs",
                "10",
                "-hold",  # Keep window open after command exits
                "-e",
                "chat-monitor",
                "--run",
                run_id,
                "--focus",
                focus_mode,
                "--verbose",
            ]

            print(f"🖥️  Launching chat monitor window: {title}")

            # Launch in background
            process = subprocess.Popen(
                cmd,
                env=dict(os.environ, DISPLAY=self.display),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )

            self.launched_windows.append(process)

            # Give window time to appear
            time.sleep(0.5)

            return process

        except Exception as e:
            print(f"❌ Failed to launch chat monitor window: {e}")
            return None

    def launch_system_wide(
        self,
        title: str = "Chat Monitor - All Agents",
        focus_mode: str = "all",
        geometry: str = "120x40+200+200",
    ) -> Optional[subprocess.Popen]:
        """Launch chat monitor for all system agents."""
        if not self._check_x11_available():
            return None

        try:
            cmd = [
                "xterm",
                "-title",
                title,
                "-geometry",
                geometry,
                "-bg",
                "black",
                "-fg",
                "cyan",
                "-fa",
                "monospace",
                "-fs",
                "10",
                "-hold",
                "-e",
                "chat-monitor",
                "--all-agents",
                "--focus",
                focus_mode,
                "--verbose",
            ]

            print(f"🖥️  Launching system-wide chat monitor: {title}")

            process = subprocess.Popen(
                cmd,
                env=dict(os.environ, DISPLAY=self.display),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )

            self.launched_windows.append(process)
            time.sleep(0.5)

            return process

        except Exception as e:
            print(f"❌ Failed to launch system-wide monitor: {e}")
            return None

    def launch_multi_focus(
        self, run_id: str, base_title: Optional[str] = None, geometry_offset: int = 50
    ) -> List[subprocess.Popen]:
        """
        Launch multiple chat monitor windows with different focus modes.

        Args:
            run_id: Orchestrator run ID to monitor
            base_title: Base window title
            geometry_offset: Pixel offset between windows

        Returns:
            List of subprocess handles for launched windows
        """
        if not base_title:
            base_title = f"Monitor {run_id[:8]}"

        focus_modes = [
            ("communication", "Communication", "green"),
            ("workspace", "Workspace", "yellow"),
            ("handoffs", "Handoffs", "cyan"),
        ]

        launched = []

        for i, (focus, title_suffix, color) in enumerate(focus_modes):
            window_title = f"{base_title} - {title_suffix}"
            x_offset = 100 + (i * geometry_offset)
            y_offset = 100 + (i * geometry_offset)
            geometry = f"100x30+{x_offset}+{y_offset}"

            process = self.launch_for_run(
                run_id=run_id, title=window_title, focus_mode=focus, geometry=geometry
            )

            if process:
                launched.append(process)
                time.sleep(0.2)  # Stagger window creation

        return launched

    def cleanup_windows(self):
        """Close all launched chat monitor windows."""
        closed_count = 0

        for process in self.launched_windows[:]:
            try:
                if process.poll() is None:  # Still running
                    process.terminate()
                    closed_count += 1
                self.launched_windows.remove(process)
            except:
                pass

        if closed_count > 0:
            print(f"🗑️  Closed {closed_count} chat monitor windows")

    def _check_x11_available(self) -> bool:
        """Check if X11 display is available."""
        if not self.display:
            return False

        try:
            # Test X11 connection
            result = subprocess.run(
                ["xset", "q"],
                env=dict(os.environ, DISPLAY=self.display),
                capture_output=True,
                timeout=2,
            )
            return result.returncode == 0
        except:
            return False

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup windows."""
        self.cleanup_windows()


# Integration helper for orchestrators
def auto_launch_chat_monitor(
    run_id: str, title: Optional[str] = None, multi_focus: bool = False
) -> Optional[ChatMonitorLauncher]:
    """
    Convenience function for orchestrators to auto-launch chat monitor.

    Args:
        run_id: Orchestrator run ID
        title: Base window title
        multi_focus: Launch multiple windows with different focus modes

    Returns:
        ChatMonitorLauncher instance or None if failed
    """
    try:
        launcher = ChatMonitorLauncher()

        if multi_focus:
            windows = launcher.launch_multi_focus(run_id, title)
            if windows:
                print(
                    f"🎯 Launched {len(windows)} chat monitor windows for run {run_id}"
                )
                return launcher
        else:
            window = launcher.launch_for_run(run_id, title)
            if window:
                print(f"🎯 Launched chat monitor window for run {run_id}")
                return launcher

        return None

    except Exception as e:
        print(f"❌ Auto-launch failed: {e}")
        return None


# Example usage
if __name__ == "__main__":
    # Demo the launcher
    print("🧪 Testing chat monitor launcher...")

    with ChatMonitorLauncher() as launcher:
        # Launch system-wide monitor
        launcher.launch_system_wide("Demo Monitor")

        print("Monitor launched! Press Enter to close...")
        input()

    print("✅ Launcher test complete")
