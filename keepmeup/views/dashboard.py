"""
Dashboard — primary session control center.

Combines the live status card, the large focus timer/countdown, Start/Pause/Stop
controls, the mouse/keyboard target toggles and quick preferences. Talks only to
the EngineController via signals/slots.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGridLayout,
)

from ..components import Card, StatTile, StatusDot, ToggleSwitch, hline, Color, FONT_MONO
from ..services import State
from ..services.telemetry import Telemetry


class TargetCard(QFrame):
    """A simulation-target card with a toggle (Mouse / Keyboard)."""

    def __init__(self, icon, title, description, enabled, on_toggle, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self._on_toggle = on_toggle
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)

        top = QHBoxLayout()
        title_lbl = QLabel(f"{icon}  {title}")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: 600;")
        self.toggle = ToggleSwitch(enabled)
        self.toggle.toggled.connect(self._toggled)
        top.addWidget(title_lbl)
        top.addStretch()
        top.addWidget(self.toggle)
        lay.addLayout(top)

        desc = QLabel(description)
        desc.setWordWrap(True)
        desc.setObjectName("Muted")
        desc.setStyleSheet(f"color: {Color.ON_SURFACE_VARIANT}; font-size: 13px;")
        lay.addWidget(desc)

        lay.addWidget(hline())
        status_row = QHBoxLayout()
        status_row.setSpacing(8)
        self.dot = StatusDot(Color.SUCCESS if enabled else Color.ON_SURFACE_DIM)
        self.status_lbl = QLabel("Active" if enabled else "Standby")
        self.status_lbl.setStyleSheet(
            f"font-size: 12px; color: {Color.SUCCESS if enabled else Color.ON_SURFACE_DIM};")
        status_row.addWidget(self.dot)
        status_row.addWidget(self.status_lbl)
        status_row.addStretch()
        lay.addLayout(status_row)

    def _toggled(self, checked):
        self._refresh(checked)
        self._on_toggle(checked)

    def _refresh(self, checked):
        self.dot.set_color(Color.SUCCESS if checked else Color.ON_SURFACE_DIM)
        self.status_lbl.setText("Active" if checked else "Standby")
        self.status_lbl.setStyleSheet(
            f"font-size: 12px; color: {Color.SUCCESS if checked else Color.ON_SURFACE_DIM};")

    def set_checked(self, checked):
        self.toggle.setChecked(checked)
        self._refresh(checked)


class DashboardView(QWidget):
    def __init__(self, controller, storage, scheduler, on_start_request, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.storage = storage
        self.scheduler = scheduler
        self._on_start_request = on_start_request
        self._countdown = 0

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(20)

        header = QVBoxLayout()
        header.setSpacing(2)
        title = QLabel("Dashboard")
        title.setObjectName("Headline")
        sub = QLabel("Daily operation and quick control.")
        sub.setObjectName("SubHeadline")
        header.addWidget(title)
        header.addWidget(sub)
        root.addLayout(header)

        body = QHBoxLayout()
        body.setSpacing(20)
        body.addLayout(self._build_left(), 4)
        body.addWidget(self._build_timer(), 6)
        root.addLayout(body, 1)

        self._wire()
        self._refresh_state(self.controller.state)
        self._refresh_metrics()

    # --- left column -----------------------------------------------------

    def _build_left(self):
        col = QVBoxLayout()
        col.setSpacing(16)

        caps = QLabel("SIMULATION TARGETS")
        caps.setObjectName("LabelCaps")
        col.addWidget(caps)

        prefs = self.storage.prefs
        self.mouse_card = TargetCard(
            "🖱", "Mouse Movement",
            "Human-like Bezier cursor movement across the screen with easing and micro-jitter.",
            prefs["mouse_enabled"], self._set_mouse)
        self.kbd_card = TargetCard(
            "⌨", "Keyboard Input",
            "Types your content file character-by-character with natural cadence and typos.",
            prefs["keyboard_enabled"], self._set_keyboard)
        col.addWidget(self.mouse_card)
        col.addWidget(self.kbd_card)

        # quick prefs card
        quick = Card("Quick Settings", "⚙")
        self.tray_chk = self._pref_row(quick, "Minimize to tray", prefs["minimize_to_tray"],
                                       lambda v: self._save_pref("minimize_to_tray", v))
        self.launch_chk = self._pref_row(quick, "Start on launch", prefs["start_on_launch"],
                                         lambda v: self._save_pref("start_on_launch", v))
        col.addWidget(quick)

        # info card
        info = Card("Session Info", "ⓘ")
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)
        self.profile_val = self._info_pair(grid, 0, "Profile", prefs["current_profile"])
        self.wpm_val = self._info_pair(grid, 1, "Typing speed", f"{self.controller.config.typing_wpm} WPM")
        self.sched_val = self._info_pair(grid, 2, "Schedule", self.scheduler.summary())
        info.body_layout().addLayout(grid)
        col.addWidget(info)
        col.addStretch()
        return col

    def _pref_row(self, card, label, value, on_change):
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel(label)
        toggle = ToggleSwitch(value)
        toggle.toggled.connect(on_change)
        h.addWidget(lbl)
        h.addStretch()
        h.addWidget(toggle)
        card.add(row)
        return toggle

    def _info_pair(self, grid, row, key, value):
        k = QLabel(key)
        k.setStyleSheet(f"color: {Color.ON_SURFACE_VARIANT}; font-size: 13px;")
        v = QLabel(value)
        v.setStyleSheet(f"font-family: {FONT_MONO}; color: {Color.ON_SURFACE}; font-size: 13px;")
        v.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(k, row, 0, Qt.AlignLeft)
        grid.addWidget(v, row, 1, Qt.AlignRight)
        return v

    # --- timer / control column -----------------------------------------

    def _build_timer(self):
        card = QFrame()
        card.setObjectName("Card")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(28, 28, 28, 28)
        lay.setSpacing(8)

        top = QHBoxLayout()
        self.state_badge_dot = StatusDot(Color.ON_SURFACE_DIM)
        self.state_badge = QLabel("Stopped")
        self.state_badge.setObjectName("LabelCaps")
        top.addWidget(self.state_badge_dot)
        top.addWidget(self.state_badge)
        top.addStretch()
        runtime_caps = QLabel("RUNTIME")
        runtime_caps.setObjectName("LabelCaps")
        top.addWidget(runtime_caps)
        lay.addLayout(top)

        lay.addStretch()
        mode_lbl = QLabel("SESSION TIMER")
        mode_lbl.setObjectName("LabelCaps")
        mode_lbl.setAlignment(Qt.AlignCenter)
        mode_lbl.setStyleSheet(f"color: {Color.PRIMARY_LIGHT}; letter-spacing: 2px;")
        lay.addWidget(mode_lbl)

        self.timer_lbl = QLabel("00:00:00")
        self.timer_lbl.setAlignment(Qt.AlignCenter)
        self.timer_lbl.setStyleSheet(
            f"font-family: {FONT_MONO}; font-size: 56px; font-weight: 600; "
            f"color: {Color.ON_SURFACE}; letter-spacing: 4px;")
        lay.addWidget(self.timer_lbl)

        self.sub_status = QLabel("Engine ready. Press Start to begin.")
        self.sub_status.setAlignment(Qt.AlignCenter)
        self.sub_status.setStyleSheet(f"color: {Color.ON_SURFACE_DIM}; font-size: 13px;")
        lay.addWidget(self.sub_status)
        lay.addStretch()

        # metrics row
        metrics = QHBoxLayout()
        metrics.setSpacing(12)
        self.tile_wpm = StatTile("Current WPM", "0")
        self.tile_chars = StatTile("Chars typed", "0")
        self.tile_dist = StatTile("Mouse distance", "0 px")
        metrics.addWidget(self.tile_wpm)
        metrics.addWidget(self.tile_chars)
        metrics.addWidget(self.tile_dist)
        lay.addLayout(metrics)

        # controls
        controls = QHBoxLayout()
        controls.setSpacing(14)
        self.btn_stop = QPushButton("■  Abort")
        self.btn_stop.setObjectName("Danger")
        self.btn_stop.setMinimumHeight(46)
        self.btn_stop.clicked.connect(self.controller.stop)

        self.btn_pause = QPushButton("⏸  Pause")
        self.btn_pause.setObjectName("Secondary")
        self.btn_pause.setMinimumHeight(46)
        self.btn_pause.clicked.connect(self.controller.toggle_pause)

        self.btn_start = QPushButton("▶  Start Focus")
        self.btn_start.setObjectName("Primary")
        self.btn_start.setMinimumHeight(46)
        self.btn_start.clicked.connect(self._on_start_request)

        controls.addWidget(self.btn_stop, 1)
        controls.addWidget(self.btn_pause, 1)
        controls.addWidget(self.btn_start, 2)
        lay.addLayout(controls)
        return card

    # --- wiring ----------------------------------------------------------

    def _wire(self):
        self.controller.state_changed.connect(self._refresh_state)
        self.controller.countdown_changed.connect(self._on_countdown)
        self.controller.tick.connect(self._refresh_metrics)
        self.controller.telemetry.updated.connect(self._refresh_metrics)

    def _set_mouse(self, v):
        self.controller.config.mouse_enabled = v
        self._save_pref("mouse_enabled", v)

    def _set_keyboard(self, v):
        self.controller.config.keyboard_enabled = v
        self._save_pref("keyboard_enabled", v)

    def _save_pref(self, key, value):
        self.storage.prefs[key] = value
        self.storage.save()

    # --- state / metrics refresh ----------------------------------------

    def _on_countdown(self, remaining):
        self._countdown = remaining
        if remaining > 0:
            self.timer_lbl.setText(f"00:00:{remaining:02d}")
            self.sub_status.setText("Focus your target window — starting soon…")

    def _refresh_state(self, state):
        colors = {State.RUNNING: Color.SUCCESS, State.PAUSED: Color.WARNING,
                  State.STOPPED: Color.ON_SURFACE_DIM}
        self.state_badge.setText(state)
        self.state_badge_dot.set_color(colors[state])
        self.state_badge.setStyleSheet(f"color: {colors[state]};")

        running = state != State.STOPPED
        self.btn_start.setEnabled(not running)
        self.btn_pause.setEnabled(running)
        self.btn_stop.setEnabled(running)
        self.btn_pause.setText("▶  Resume" if state == State.PAUSED else "⏸  Pause")

        if state == State.STOPPED:
            self.timer_lbl.setText("00:00:00")
            self.sub_status.setText("Engine ready. Press Start to begin.")
        elif state == State.RUNNING and self._countdown == 0:
            self.sub_status.setText("System idle prevention active. Simulating human activity.")
        elif state == State.PAUSED:
            self.sub_status.setText("Paused — simulation suspended.")

    def _refresh_metrics(self):
        t: Telemetry = self.controller.telemetry
        if self.controller.state != State.STOPPED and self._countdown == 0:
            self.timer_lbl.setText(Telemetry.fmt_duration(t.runtime_seconds))
        self.tile_wpm.set_value(f"{t.average_wpm:.0f}")
        self.tile_chars.set_value(f"{t.chars_typed:,}")
        self.tile_dist.set_value(f"{int(t.pixels_moved):,} px")
        self.wpm_val.setText(f"{self.controller.config.typing_wpm} WPM")

    # --- external sync ---------------------------------------------------

    def sync_from_config(self):
        cfg = self.controller.config
        self.mouse_card.set_checked(cfg.mouse_enabled)
        self.kbd_card.set_checked(cfg.keyboard_enabled)
        self.profile_val.setText(self.storage.prefs["current_profile"])
        self.wpm_val.setText(f"{cfg.typing_wpm} WPM")
        self.sched_val.setText(self.scheduler.summary())
