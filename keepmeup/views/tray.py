"""
System tray manager — keeps the app running while hidden, exposes engine
controls and live status from the tray menu, and rebuilds its icon to reflect
the current run state.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush, QFont, QAction
from PySide6.QtWidgets import QSystemTrayIcon, QMenu

from ..components import Color
from ..services import State


def make_icon(state: str) -> QIcon:
    colors = {State.RUNNING: Color.SUCCESS, State.PAUSED: Color.WARNING,
              State.STOPPED: Color.ON_SURFACE_DIM}
    accent = colors.get(state, Color.ON_SURFACE_DIM)
    pm = QPixmap(64, 64)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    # rounded square background
    p.setBrush(QBrush(QColor(Color.PRIMARY)))
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(4, 4, 56, 56, 14, 14)
    # "K" mark
    p.setPen(QColor(Color.ON_PRIMARY))
    f = QFont("Inter", 30, QFont.Bold)
    p.setFont(f)
    p.drawText(pm.rect(), Qt.AlignCenter, "K")
    # state dot
    p.setBrush(QBrush(QColor(accent)))
    p.setPen(QColor(Color.SURFACE))
    p.drawEllipse(40, 40, 18, 18)
    p.end()
    return QIcon(pm)


class TrayManager(QSystemTrayIcon):
    def __init__(self, controller, on_show, on_quit, parent=None):
        super().__init__(parent)
        self.controller = controller
        self._on_show = on_show
        self._on_quit = on_quit

        self.setIcon(make_icon(State.STOPPED))
        self.setToolTip("KeepMeUp — Stopped")

        menu = QMenu()
        self.act_status = QAction("Status: Stopped", menu)
        self.act_status.setEnabled(False)
        menu.addAction(self.act_status)
        menu.addSeparator()

        self.act_show = QAction("Show Window", menu)
        self.act_show.triggered.connect(self._on_show)
        menu.addAction(self.act_show)

        self.act_start = QAction("Start", menu)
        self.act_start.triggered.connect(self.controller.start)
        menu.addAction(self.act_start)

        self.act_pause = QAction("Pause", menu)
        self.act_pause.triggered.connect(self.controller.toggle_pause)
        menu.addAction(self.act_pause)

        self.act_stop = QAction("Stop", menu)
        self.act_stop.triggered.connect(self.controller.stop)
        menu.addAction(self.act_stop)

        menu.addSeparator()
        act_quit = QAction("Quit", menu)
        act_quit.triggered.connect(self._on_quit)
        menu.addAction(act_quit)

        self.setContextMenu(menu)
        self.activated.connect(self._on_activated)

        self.controller.state_changed.connect(self._on_state)
        self._on_state(controller.state)

    def _on_activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self._on_show()

    def _on_state(self, state):
        self.setIcon(make_icon(state))
        self.setToolTip(f"KeepMeUp — {state}")
        self.act_status.setText(f"Status: {state}")
        running = state != State.STOPPED
        self.act_start.setEnabled(not running)
        self.act_pause.setEnabled(running)
        self.act_pause.setText("Resume" if state == State.PAUSED else "Pause")
        self.act_stop.setEnabled(running)
