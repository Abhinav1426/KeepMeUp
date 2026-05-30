"""
MainWindow — the application shell: sidebar navigation, top context bar, a
stacked content area for the six sections, and a status footer. Wires the
EngineController, Storage, Scheduler and TrayManager together.
"""

import os
import subprocess
import sys

from PySide6.QtCore import Qt, QByteArray
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QStackedWidget, QFrame, QButtonGroup, QApplication,
)

from ..components import Color, FONT_MONO, StatusDot
from ..services import State
from .dashboard import DashboardView
from .behavior import BehaviorView
from .content import ContentView
from .analytics import AnalyticsView
from .schedule import ScheduleView
from .settings import SettingsView
from .safe_start import SafeStartDialog
from .tray import TrayManager


NAV_ITEMS = [
    ("Dashboard", "▦"),
    ("Behavior", "⚡"),
    ("Content", "❏"),
    ("Analytics", "▣"),
    ("Schedule", "◷"),
    ("Settings", "⚙"),
]

APP_VERSION = "v1.0.0"


class MainWindow(QMainWindow):
    def __init__(self, controller, storage, scheduler, resolve_content):
        super().__init__()
        self.controller = controller
        self.storage = storage
        self.scheduler = scheduler
        self._resolve_content = resolve_content
        self._force_quit = False

        self.setWindowTitle("KeepMeUp")
        self.setMinimumSize(1080, 720)

        root = QWidget()
        root.setObjectName("Root")
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_sidebar())
        layout.addWidget(self._build_main(), 1)
        self.setCentralWidget(root)

        self._build_views()
        self._wire()
        self._restore_geometry()

        # tray
        self.tray = TrayManager(controller, self._show_window, self._quit)
        self.tray.show()

        # scheduler auto control
        sched = storage.data["schedule"]
        scheduler.configure(sched["enabled"], sched["start"], sched["end"], sched["days"])
        scheduler.enter_window.connect(self._on_schedule_enter)
        scheduler.exit_window.connect(self.controller.stop)

        self._select_nav(0)

        if storage.prefs.get("start_on_launch"):
            self._request_start(skip_dialog=True)

    # --- sidebar ---------------------------------------------------------

    def _build_sidebar(self):
        side = QFrame()
        side.setObjectName("Sidebar")
        side.setFixedWidth(232)
        lay = QVBoxLayout(side)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # brand
        brand = QFrame()
        bl = QHBoxLayout(brand)
        bl.setContentsMargins(20, 20, 20, 20)
        logo = QLabel("K")
        logo.setFixedSize(34, 34)
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet(
            f"background-color: {Color.PRIMARY}; color: {Color.ON_PRIMARY}; "
            f"border-radius: 8px; font-size: 18px; font-weight: 700;")
        name_col = QVBoxLayout()
        name_col.setSpacing(0)
        name = QLabel("KeepMeUp")
        name.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {Color.PRIMARY_LIGHT};")
        ver = QLabel(f"{APP_VERSION}-stable")
        ver.setStyleSheet(f"font-family: {FONT_MONO}; font-size: 11px; color: {Color.ON_SURFACE_DIM};")
        name_col.addWidget(name)
        name_col.addWidget(ver)
        bl.addWidget(logo)
        bl.addLayout(name_col)
        bl.addStretch()
        lay.addWidget(brand)

        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background-color: {Color.OUTLINE_VARIANT};")
        lay.addWidget(divider)
        lay.addSpacing(8)

        # nav
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_buttons = []
        for i, (label, icon) in enumerate(NAV_ITEMS):
            b = QPushButton(f"  {icon}    {label}")
            b.setObjectName("NavItem")
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, idx=i: self._select_nav(idx))
            self.nav_group.addButton(b)
            self.nav_buttons.append(b)
            lay.addWidget(b)

        lay.addStretch()

        # footer mini-status
        self.side_state_dot = StatusDot(Color.ON_SURFACE_DIM)
        state_row = QFrame()
        sr = QHBoxLayout(state_row)
        sr.setContentsMargins(20, 12, 20, 16)
        sr.addWidget(self.side_state_dot)
        self.side_state_lbl = QLabel("Stopped")
        self.side_state_lbl.setStyleSheet(f"font-family: {FONT_MONO}; font-size: 12px; color: {Color.ON_SURFACE_VARIANT};")
        sr.addWidget(self.side_state_lbl)
        sr.addStretch()
        lay.addWidget(state_row)
        return side

    # --- main area -------------------------------------------------------

    def _build_main(self):
        wrap = QWidget()
        lay = QVBoxLayout(wrap)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # top bar
        top = QFrame()
        top.setObjectName("TopBar")
        top.setFixedHeight(56)
        tl = QHBoxLayout(top)
        tl.setContentsMargins(24, 0, 24, 0)
        self.crumb = QLabel("KeepMeUp  ›  Dashboard")
        self.crumb.setObjectName("LabelCaps")
        tl.addWidget(self.crumb)
        tl.addStretch()

        self.top_state_dot = StatusDot(Color.ON_SURFACE_DIM)
        tl.addWidget(self.top_state_dot)
        self.top_state = QLabel("Status: Stopped")
        self.top_state.setObjectName("LabelCaps")
        tl.addWidget(self.top_state)
        lay.addWidget(top)

        # stacked content
        self.stack = QStackedWidget()
        lay.addWidget(self.stack, 1)

        # footer
        footer = QFrame()
        footer.setObjectName("Footer")
        footer.setFixedHeight(30)
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(16, 0, 16, 0)
        self.footer_lbl = QLabel("System Tray: Ready  |  Engine idle")
        self.footer_lbl.setStyleSheet(f"font-family: {FONT_MONO}; font-size: 11px; color: {Color.WARNING};")
        fl.addWidget(self.footer_lbl)
        fl.addStretch()
        hint = QLabel("KeepMeUp — local activity simulator")
        hint.setStyleSheet(f"font-family: {FONT_MONO}; font-size: 11px; color: {Color.ON_SURFACE_DIM};")
        fl.addWidget(hint)
        lay.addWidget(footer)
        return wrap

    def _build_views(self):
        self.dashboard = DashboardView(self.controller, self.storage, self.scheduler,
                                       self._request_start)
        self.behavior = BehaviorView(self.controller, self.storage, self._on_config_changed)
        self.content = ContentView(self.controller, self.storage, self._resolve_content,
                                   self._on_content_changed)
        self.analytics = AnalyticsView(self.controller, self.storage)
        self.schedule_view = ScheduleView(self.storage, self.scheduler, self._on_schedule_changed)
        self.settings = SettingsView(self.controller, self.storage, self._on_settings_changed)
        for v in [self.dashboard, self.behavior, self.content, self.analytics,
                  self.schedule_view, self.settings]:
            self.stack.addWidget(v)

    # --- wiring ----------------------------------------------------------

    def _wire(self):
        self.controller.state_changed.connect(self._on_state)
        self.controller.status_message.connect(self._on_status_msg)

    def _select_nav(self, index):
        self.nav_buttons[index].setChecked(True)
        self.stack.setCurrentIndex(index)
        self.crumb.setText(f"KeepMeUp  ›  {NAV_ITEMS[index][0]}")
        if index == 0:
            self.dashboard.sync_from_config()
        elif index == 2:
            self.content.refresh()

    def _on_state(self, state):
        colors = {State.RUNNING: Color.SUCCESS, State.PAUSED: Color.WARNING,
                  State.STOPPED: Color.ON_SURFACE_DIM}
        col = colors[state]
        self.top_state.setText(f"Status: {state}")
        self.top_state.setStyleSheet(f"color: {col};")
        self.top_state_dot.set_color(col)
        self.side_state_lbl.setText(state)
        self.side_state_dot.set_color(col)
        if state == State.STOPPED:
            self.footer_lbl.setText("System Tray: Ready  |  Engine idle")
            self.footer_lbl.setStyleSheet(f"font-family: {FONT_MONO}; font-size: 11px; color: {Color.WARNING};")
            self._persist_session()
        else:
            self.footer_lbl.setText(f"Engine {state.lower()}  |  simulating activity")
            self.footer_lbl.setStyleSheet(f"font-family: {FONT_MONO}; font-size: 11px; color: {Color.SUCCESS};")

    def _on_status_msg(self, msg):
        # transient status in the footer hint while running
        pass

    # --- start flow ------------------------------------------------------

    def _request_start(self, skip_dialog=False):
        if self.controller.state != State.STOPPED:
            return
        # launch target if configured
        target = self.settings.launch_target()
        if not skip_dialog:
            dlg = SafeStartDialog(
                self.controller.config, self._resolve_content(),
                self.storage.prefs.get("current_profile", "Custom"),
                self.settings.target_combo.currentText(), self)
            if dlg.exec() != dlg.DialogCode.Accepted:
                return
        if target:
            self._launch_target(target)
        self.controller.start()

    def _launch_target(self, target):
        try:
            if sys.platform == "win32" and target.endswith(".exe"):
                subprocess.Popen([target])
            else:
                subprocess.Popen(target, shell=True)
        except Exception:
            pass

    def _on_schedule_enter(self):
        if self.controller.state == State.STOPPED:
            self._request_start(skip_dialog=True)

    # --- persistence / change hooks -------------------------------------

    def _persist_session(self):
        t = self.controller.telemetry
        if t.chars_typed or t.pixels_moved:
            self.storage.add_session(t.runtime_seconds, t.chars_typed,
                                     t.pixels_moved, t.mouse_movements)
            self.storage.save()

    def _on_config_changed(self):
        self.dashboard.sync_from_config()

    def _on_content_changed(self):
        pass

    def _on_schedule_changed(self):
        self.dashboard.sync_from_config()

    def _on_settings_changed(self):
        self.analytics.refresh()

    # --- window state ----------------------------------------------------

    def _restore_geometry(self):
        geo = self.storage.get("window", "geometry", default="")
        if geo:
            try:
                self.restoreGeometry(QByteArray.fromBase64(geo.encode()))
            except Exception:
                pass

    def _save_geometry(self):
        self.storage.set(bytes(self.saveGeometry().toBase64()).decode(), "window", "geometry")
        self.storage.save()

    def _show_window(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _quit(self):
        self._force_quit = True
        self.controller.stop()
        self._save_geometry()
        QApplication.quit()

    def closeEvent(self, event):
        if self._force_quit or not self.storage.prefs.get("minimize_to_tray", True):
            self.controller.stop()
            self._save_geometry()
            event.accept()
            QApplication.quit()
        else:
            event.ignore()
            self.hide()
            self.tray.showMessage(
                "KeepMeUp", "Still running in the system tray.",
                self.tray.icon(), 3000)
