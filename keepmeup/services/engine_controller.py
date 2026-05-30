"""
EngineController — the ViewModel layer.

Owns the worker threads, the telemetry aggregator and the run state. The UI
talks only to this object via Qt signals/slots; it never touches the engines
or threads directly. This keeps business logic out of the widgets.
"""

import os

from PySide6.QtCore import QObject, QTimer, Signal

from ..core import MouseWorker, KeyboardWorker, EngineConfig
from .telemetry import Telemetry


class State:
    STOPPED = "Stopped"
    RUNNING = "Running"
    PAUSED = "Paused"


class EngineController(QObject):
    state_changed = Signal(str)            # State.*
    countdown_changed = Signal(int)        # seconds remaining (0 = done)
    tick = Signal()                        # ~1s heartbeat for runtime displays
    status_message = Signal(str)

    def __init__(self, config: EngineConfig, content_path_resolver, parent=None):
        super().__init__(parent)
        self._config = config
        self._resolve_content = content_path_resolver  # callable -> abs path
        self.state = State.STOPPED
        self.telemetry = Telemetry(parent=self)

        self._mouse_worker = None
        self._kbd_worker = None

        self._heartbeat = QTimer(self)
        self._heartbeat.setInterval(1000)
        self._heartbeat.timeout.connect(self.tick.emit)

    # --- config ----------------------------------------------------------

    @property
    def config(self) -> EngineConfig:
        return self._config

    def set_config(self, config: EngineConfig):
        self._config = config
        # live-apply to running workers
        if self._mouse_worker:
            self._mouse_worker.update_config(config.mouse)
        if self._kbd_worker:
            self._kbd_worker.update_config(config.keyboard)

    # --- lifecycle -------------------------------------------------------

    def start(self):
        if self.state != State.STOPPED:
            return
        cfg = self._config
        self.telemetry.start()

        if cfg.mouse_enabled:
            self._mouse_worker = MouseWorker(cfg.mouse, cfg.startup_delay)
            self._mouse_worker.moved.connect(self.telemetry.on_mouse_moved)
            self._mouse_worker.status.connect(self.status_message.emit)
            self._mouse_worker.start()

        if cfg.keyboard_enabled:
            content = self._resolve_content()
            self._kbd_worker = KeyboardWorker(cfg.keyboard, content, cfg.startup_delay)
            self._kbd_worker.typed.connect(self.telemetry.on_chars_typed)
            self._kbd_worker.status.connect(self.status_message.emit)
            self._kbd_worker.countdown.connect(self.countdown_changed.emit)
            self._kbd_worker.start()
        elif cfg.mouse_enabled:
            # No keyboard countdown source; emit a synthetic one.
            self._synthetic_countdown(cfg.startup_delay)

        self._set_state(State.RUNNING)
        self._heartbeat.start()

    def pause(self):
        if self.state != State.RUNNING:
            return
        self.telemetry.set_paused(True)
        if self._mouse_worker:
            self._mouse_worker.set_paused(True)
        if self._kbd_worker:
            self._kbd_worker.set_paused(True)
        self._set_state(State.PAUSED)

    def resume(self):
        if self.state != State.PAUSED:
            return
        self.telemetry.set_paused(False)
        if self._mouse_worker:
            self._mouse_worker.set_paused(False)
        if self._kbd_worker:
            self._kbd_worker.set_paused(False)
        self._set_state(State.RUNNING)

    def toggle_pause(self):
        if self.state == State.RUNNING:
            self.pause()
        elif self.state == State.PAUSED:
            self.resume()

    def stop(self):
        if self.state == State.STOPPED:
            return
        for worker in (self._mouse_worker, self._kbd_worker):
            if worker:
                worker.stop()
        for worker in (self._mouse_worker, self._kbd_worker):
            if worker:
                worker.wait(3000)
        self._mouse_worker = None
        self._kbd_worker = None
        self._heartbeat.stop()
        self.telemetry.stop()
        self._set_state(State.STOPPED)

    # --- helpers ---------------------------------------------------------

    def _synthetic_countdown(self, seconds):
        self._sc_remaining = seconds

        def step():
            self.countdown_changed.emit(self._sc_remaining)
            if self._sc_remaining <= 0:
                timer.stop()
            self._sc_remaining -= 1

        timer = QTimer(self)
        timer.setInterval(1000)
        timer.timeout.connect(step)
        timer.start()
        step()

    def _set_state(self, state):
        self.state = state
        self.state_changed.emit(state)
