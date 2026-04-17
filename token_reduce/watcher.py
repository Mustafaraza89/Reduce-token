from __future__ import annotations

import signal
import time
from pathlib import Path

from .analyzer import Analyzer
from .config import AppConfig, is_included


class Watcher:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.analyzer = Analyzer(config)
        self._running = True

    def stop(self, *_args: object) -> None:
        self._running = False

    def run(self, interval_seconds: float | None = None) -> None:
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)
        interval = interval_seconds if interval_seconds is not None else self.config.watcher_interval_seconds

        seen_mtimes: dict[str, float] = {}
        while self._running:
            changed: list[Path] = []
            for path in self.analyzer.collect_source_files():
                rel = str(path.relative_to(self.analyzer.project_root)).replace("\\", "/")
                if not is_included(self.config, rel):
                    continue
                stat = path.stat()
                mtime = stat.st_mtime
                if rel not in seen_mtimes:
                    seen_mtimes[rel] = mtime
                    continue
                if mtime > seen_mtimes[rel]:
                    seen_mtimes[rel] = mtime
                    changed.append(path)

            if changed:
                self.analyzer.sync_files(changed)

            time.sleep(interval)

        self.analyzer.close()
