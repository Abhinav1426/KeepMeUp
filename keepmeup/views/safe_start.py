"""
Safe Start dialog — confirmation overlay shown before the engine starts, so the
user can verify peripherals, target and estimated runtime before automation
takes over the mouse/keyboard.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGridLayout, QFrame,
)

from ..components import Color, FONT_MONO, hline


class SafeStartDialog(QDialog):
    def __init__(self, config, content_path, profile_name, target_label, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Confirm Start")
        self.setModal(True)
        self.setMinimumWidth(420)
        self.setStyleSheet(f"QDialog {{ background-color: {Color.SURFACE_CONTAINER}; }}")

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        title = QLabel("Ready to start?")
        title.setStyleSheet("font-size: 20px; font-weight: 700;")
        root.addWidget(title)
        warn = QLabel("The engine will control your mouse and keyboard. Make sure the correct "
                      "window is focused before the countdown ends.")
        warn.setWordWrap(True)
        warn.setStyleSheet(f"color: {Color.ON_SURFACE_VARIANT}; font-size: 13px;")
        root.addWidget(warn)
        root.addWidget(hline())

        grid = QGridLayout()
        grid.setVerticalSpacing(10)
        grid.setHorizontalSpacing(20)
        rows = [
            ("Mouse enabled", "Yes" if config.mouse_enabled else "No",
             Color.SUCCESS if config.mouse_enabled else Color.ON_SURFACE_DIM),
            ("Keyboard enabled", "Yes" if config.keyboard_enabled else "No",
             Color.SUCCESS if config.keyboard_enabled else Color.ON_SURFACE_DIM),
            ("Profile", profile_name, Color.ON_SURFACE),
            ("Target", target_label or "Focused window", Color.ON_SURFACE),
            ("Typing speed", f"{config.typing_wpm} WPM", Color.ON_SURFACE),
            ("Startup countdown", f"{config.startup_delay} s", Color.ON_SURFACE),
        ]
        for i, (k, v, col) in enumerate(rows):
            key = QLabel(k)
            key.setStyleSheet(f"color: {Color.ON_SURFACE_VARIANT}; font-size: 13px;")
            val = QLabel(v)
            val.setStyleSheet(f"font-family: {FONT_MONO}; color: {col}; font-size: 13px;")
            val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            grid.addWidget(key, i, 0, Qt.AlignLeft)
            grid.addWidget(val, i, 1, Qt.AlignRight)
        root.addLayout(grid)
        root.addWidget(hline())

        btns = QHBoxLayout()
        cancel = QPushButton("Cancel")
        cancel.setObjectName("Secondary")
        cancel.clicked.connect(self.reject)
        start = QPushButton("▶  Start")
        start.setObjectName("Primary")
        start.clicked.connect(self.accept)
        start.setDefault(True)
        btns.addStretch()
        btns.addWidget(cancel)
        btns.addWidget(start)
        root.addLayout(btns)
