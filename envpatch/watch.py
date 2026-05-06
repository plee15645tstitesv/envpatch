"""Watch a .env file for changes and report diffs on modification."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from envpatch.parser import EnvFile
from envpatch.diff import diff, DiffEntry


@dataclass
class WatchEvent:
    """Emitted each time a watched file changes."""

    path: Path
    previous: EnvFile
    current: EnvFile
    changes: list[DiffEntry] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.changes)


class FileWatcher:
    """Poll a .env file and invoke a callback when its content changes."""

    def __init__(
        self,
        path: Path | str,
        callback: Callable[[WatchEvent], None],
        interval: float = 1.0,
    ) -> None:
        self.path = Path(path)
        self.callback = callback
        self.interval = interval
        self._last_mtime: Optional[float] = None
        self._last_file: Optional[EnvFile] = None
        self._running = False

    def _load(self) -> EnvFile:
        return EnvFile.parse(self.path.read_text())

    def _check(self) -> None:
        try:
            mtime = self.path.stat().st_mtime
        except FileNotFoundError:
            return

        if self._last_mtime is None:
            self._last_mtime = mtime
            self._last_file = self._load()
            return

        if mtime == self._last_mtime:
            return

        current = self._load()
        previous = self._last_file
        self._last_mtime = mtime
        self._last_file = current

        changes = diff(previous, current)
        event = WatchEvent(
            path=self.path,
            previous=previous,
            current=current,
            changes=changes,
        )
        self.callback(event)

    def start(self, max_iterations: Optional[int] = None) -> None:
        """Begin polling. Runs until stop() is called or max_iterations reached."""
        self._running = True
        iterations = 0
        while self._running:
            self._check()
            if max_iterations is not None:
                iterations += 1
                if iterations >= max_iterations:
                    break
            time.sleep(self.interval)

    def stop(self) -> None:
        self._running = False
