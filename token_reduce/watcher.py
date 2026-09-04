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
        try:
            signal.signal(signal.SIGINT, self.stop)
            signal.signal(signal.SIGTERM, self.stop)
        except (ValueError, AttributeError):
            pass

        interval = interval_seconds if interval_seconds is not None else self.config.watcher_interval_seconds
        seen_mtimes: dict[str, float] = {}
        first_scan = True

        while self._running:
            changed: list[Path] = []
            current_rels: set[str] = set()

            for path in self.analyzer.collect_source_files():
                rel = str(path.relative_to(self.analyzer.project_root)).replace("\\", "/")
                current_rels.add(rel)
                try:
                    mtime = path.stat().st_mtime
                except OSError:
                    continue

                if rel not in seen_mtimes:
                    seen_mtimes[rel] = mtime
                    if not first_scan:
                        # New file created during watch
                        changed.append(path)
                    continue

                if mtime > seen_mtimes[rel]:
                    seen_mtimes[rel] = mtime
                    changed.append(path)

            # Detect deleted files and clean up graph
            deleted_rels = set(seen_mtimes.keys()) - current_rels
            for drel in deleted_rels:
                del seen_mtimes[drel]
                changed.append(self.analyzer.project_root / drel)

            if changed:
                self.analyzer.sync_files(changed)

            first_scan = False
            time.sleep(interval)

        self.analyzer.close()
