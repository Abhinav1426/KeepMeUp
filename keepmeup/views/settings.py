"""
Settings view — application preferences and targets (startup delay, launch
target, tray behaviour) plus a quick "about / data" section.
"""

import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QFileDialog,
)

from ..components import Card, ToggleSwitch, LabeledSlider, Color, FONT_MONO
from ..services import config_dir


TARGET_APPS = {
    "Focused Window (manual)": "",
    "Notepad": "notepad.exe",
    "VS Code": "code",
    "Cursor": "cursor",
    "Sublime Text": "subl",
    "Custom…": "__custom__",
}


class SettingsView(QWidget):
    def __init__(self, controller, storage, on_changed, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.storage = storage
        self._on_changed = on_changed

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(20)

        head = QVBoxLayout()
        head.setSpacing(2)
        title = QLabel("Settings")
        title.setObjectName("Headline")
        sub = QLabel("Application preferences and launch targets.")
        sub.setObjectName("SubHeadline")
        head.addWidget(title)
        head.addWidget(sub)
        root.addLayout(head)

        prefs = storage.prefs

        # General
        general = Card("General", "⚙")
        self._toggle_row(general, "Minimize to tray on close", prefs["minimize_to_tray"],
                         lambda v: self._save("minimize_to_tray", v))
        self._toggle_row(general, "Start engine on launch", prefs["start_on_launch"],
                         lambda v: self._save("start_on_launch", v))
        self.delay_slider = LabeledSlider("Startup countdown", 0, 60,
                                          prefs.get("startup_delay", 30), 1, suffix=" s")
        self.delay_slider.valueChanged.connect(self._set_delay)
        general.add(self.delay_slider)
        root.addWidget(general)

        # Targets
        targets = Card("Target", "🎯")
        t_lbl = QLabel("Launch target before start")
        t_lbl.setStyleSheet("font-size: 12px; font-weight: 500;")
        targets.add(t_lbl)
        self.target_combo = QComboBox()
        self.target_combo.addItems(list(TARGET_APPS.keys()))
        targets.add(self.target_combo)
        desc = QLabel("On Start, the chosen application is launched, then the countdown begins "
                      "before simulation. 'Focused Window' types into whatever you focus manually.")
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {Color.ON_SURFACE_VARIANT}; font-size: 12px;")
        targets.add(desc)
        root.addWidget(targets)

        # Data
        data = Card("Data", "🗄")
        path_lbl = QLabel(os.path.join(config_dir(), "config.json"))
        path_lbl.setStyleSheet(f"font-family: {FONT_MONO}; color: {Color.ON_SURFACE_VARIANT}; font-size: 12px;")
        path_lbl.setWordWrap(True)
        data.add(QLabel("Settings & statistics are stored at:"))
        data.add(path_lbl)
        btn_row = QHBoxLayout()
        open_btn = QPushButton("Open config folder")
        open_btn.setObjectName("Secondary")
        open_btn.clicked.connect(self._open_config)
        reset_btn = QPushButton("Reset lifetime stats")
        reset_btn.setObjectName("Danger")
        reset_btn.clicked.connect(self._reset_stats)
        btn_row.addWidget(open_btn)
        btn_row.addWidget(reset_btn)
        btn_row.addStretch()
        data.body_layout().addLayout(btn_row)
        root.addWidget(data)
        root.addStretch()

    def _toggle_row(self, card, label, value, on_change):
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(QLabel(label))
        h.addStretch()
        toggle = ToggleSwitch(value)
        toggle.toggled.connect(on_change)
        h.addWidget(toggle)
        card.add(row)
        return toggle

    def _save(self, key, value):
        self.storage.prefs[key] = value
        self.storage.save()
        self._on_changed()

    def _set_delay(self, v):
        self.storage.prefs["startup_delay"] = int(v)
        self.controller.config.startup_delay = int(v)
        self.storage.save()

    def launch_target(self) -> str:
        return TARGET_APPS.get(self.target_combo.currentText(), "")

    def _open_config(self):
        path = config_dir()
        try:
            os.startfile(path)  # noqa: B606 (Windows)
        except AttributeError:
            import subprocess, sys
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.Popen([opener, path])

    def _reset_stats(self):
        lt = self.storage.lifetime
        for k in lt:
            lt[k] = 0
        self.storage.save()
        self._on_changed()
