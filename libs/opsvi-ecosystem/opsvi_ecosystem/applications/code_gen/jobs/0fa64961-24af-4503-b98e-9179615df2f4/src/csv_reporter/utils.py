"""
Utility helpers for CLI (progress bar, etc).
"""
import sys
import threading


class print_progress_bar:
    """
    Context-manager for a simple text-mode progress bar.
    Usage:
      with print_progress_bar(total=123) as update:
          for i in range(...):
              update(i)
    """

    def __init__(self, total: int, desc: str = "", width: int = 40, stream=None):
        self.total = total
        self.desc = desc
        self.width = width
        self.stream = stream or sys.stderr
        self._lock = threading.Lock()
        self._last = -1

    def __enter__(self):
        if self.desc:
            print(f"{self.desc}:", file=self.stream, flush=True)

        def updater(n):
            with self._lock:
                if n == self._last:
                    return
                self._last = n
                self.print_bar(n)

        return updater

    def __exit__(self, exc_type, exc, tb):
        self.print_bar(self.total)
        print("", file=self.stream)
        return False

    def print_bar(self, n):
        pct = min(1.0, max(0.0, n / self.total if self.total else 1))
        fill = int(self.width * pct)
        bar = "[" + "=" * fill + " " * (self.width - fill) + "]"
        pct_disp = f"{int(pct*100):3d}%"
        print(f"\r{bar} {pct_disp}", end="", file=self.stream)
        self.stream.flush()
