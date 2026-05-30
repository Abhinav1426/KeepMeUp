"""
Scheduler — wall-clock execution windows. A QTimer ticks every minute and
emits should-run transitions so the controller can auto start/stop the engine.
"""

from datetime import datetime

from PySide6.QtCore import QObject, QTimer, Signal


class Scheduler(QObject):
    enter_window = Signal()        # current time entered an active window
    exit_window = Signal()         # current time left the active window

    def __init__(self, parent=None):
        super().__init__(parent)
        self.enabled = False
        self.start = "09:00"
        self.end = "17:00"
        self.days = [0, 1, 2, 3, 4]
        self._inside = False
        self._timer = QTimer(self)
        self._timer.setInterval(30_000)  # 30s resolution
        self._timer.timeout.connect(self._tick)

    def configure(self, enabled, start, end, days):
        self.enabled = bool(enabled)
        self.start = start
        self.end = end
        self.days = list(days)
        if self.enabled:
            self._timer.start()
        else:
            self._timer.stop()
            self._inside = False

    def summary(self) -> str:
        if not self.enabled:
            return "No schedule set"
        names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        day_str = ", ".join(names[d] for d in sorted(self.days)) or "No days"
        return f"{day_str}  {self.start} → {self.end}"

    def is_active_now(self) -> bool:
        if not self.enabled:
            return False
        now = datetime.now()
        if now.weekday() not in self.days:
            return False
        cur = now.strftime("%H:%M")
        if self.start <= self.end:
            return self.start <= cur < self.end
        # overnight window
        return cur >= self.start or cur < self.end

    def _tick(self):
        active = self.is_active_now()
        if active and not self._inside:
            self._inside = True
            self.enter_window.emit()
        elif not active and self._inside:
            self._inside = False
            self.exit_window.emit()
