"""
Telemetry aggregator — collects live signals from the engine workers into a
single session snapshot the UI can poll/observe. Keeps a rolling activity
buffer for the density graph.
"""

import time
from collections import deque

from PySide6.QtCore import QObject, Signal


class Telemetry(QObject):
    updated = Signal()             # emitted whenever a metric changes

    def __init__(self, history_len: int = 60, parent=None):
        super().__init__(parent)
        self.reset()
        self._activity = deque([0] * history_len, maxlen=history_len)
        self._last_bucket = 0

    def reset(self):
        self.chars_typed = 0
        self.pixels_moved = 0.0
        self.mouse_movements = 0
        self.start_time = None
        self.paused_seconds = 0.0
        self._pause_started = None

    # --- session lifecycle ----------------------------------------------

    def start(self):
        self.reset()
        self.start_time = time.time()
        self.updated.emit()

    def stop(self):
        self.start_time = None
        self.updated.emit()

    def set_paused(self, paused: bool):
        if paused and self._pause_started is None:
            self._pause_started = time.time()
        elif not paused and self._pause_started is not None:
            self.paused_seconds += time.time() - self._pause_started
            self._pause_started = None

    # --- incoming signals -----------------------------------------------

    def on_mouse_moved(self, distance: float):
        self.pixels_moved += distance
        self.mouse_movements += 1
        self._bump_activity(1)
        self.updated.emit()

    def on_chars_typed(self, count: int):
        self.chars_typed += count
        self._bump_activity(count)
        self.updated.emit()

    def _bump_activity(self, amount):
        now = int(time.time())
        if now != self._last_bucket:
            self._last_bucket = now
            self._activity.append(0)
        self._activity[-1] += amount

    # --- derived metrics -------------------------------------------------

    @property
    def runtime_seconds(self) -> float:
        if self.start_time is None:
            return 0.0
        elapsed = time.time() - self.start_time - self.paused_seconds
        if self._pause_started is not None:
            elapsed -= time.time() - self._pause_started
        return max(0.0, elapsed)

    @property
    def words_typed(self) -> int:
        return self.chars_typed // 5

    @property
    def average_wpm(self) -> float:
        minutes = self.runtime_seconds / 60.0
        if minutes <= 0:
            return 0.0
        return self.words_typed / minutes

    def activity_buffer(self):
        return list(self._activity)

    @staticmethod
    def fmt_duration(seconds: float) -> str:
        seconds = int(seconds)
        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"
