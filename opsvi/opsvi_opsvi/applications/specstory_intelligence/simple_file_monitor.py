import json
from pathlib import Path
import sys
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

CONFIG_PATH = "file_monitor_config.json"


class SimpleFileMonitorHandler(FileSystemEventHandler):
    def __init__(self, patterns):
        super().__init__()
        self.patterns = [Path(pattern) for pattern in patterns]

    def _matches(self, path):
        # Only match .md files in docs/ (or as specified in config)
        return any(
            str(path).endswith(str(p)) or path.match(str(p)) for p in self.patterns
        )

    def on_created(self, event):
        if not event.is_directory and self._matches(Path(event.src_path)):
            print(f"[CREATED] {event.src_path} at {time.ctime()}")

    def on_modified(self, event):
        if not event.is_directory and self._matches(Path(event.src_path)):
            print(f"[MODIFIED] {event.src_path} at {time.ctime()}")

    def on_deleted(self, event):
        if not event.is_directory and self._matches(Path(event.src_path)):
            print(f"[DELETED] {event.src_path} at {time.ctime()}")


def load_config():
    try:
        with open(CONFIG_PATH) as f:
            config = json.load(f)
        watch_dir = config.get("watch_dir", "docs/")
        patterns = config.get("patterns", ["*.md"])
        return watch_dir, patterns
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)


def main():
    watch_dir, patterns = load_config()
    event_handler = SimpleFileMonitorHandler(patterns)
    observer = Observer()
    observer.schedule(event_handler, watch_dir, recursive=True)
    observer.start()
    print(f"[INFO] Watching {watch_dir} for patterns: {patterns}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
