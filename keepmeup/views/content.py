"""
Content view — manage the file that gets typed.

Select a content file, reload it, generate fresh content from presets, and view
character / line counts and an estimated typing duration.
"""

import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QFileDialog, QPlainTextEdit, QGridLayout, QSpinBox,
)

from ..components import Card, StatTile, Color, FONT_MONO
from ..core import generate_content, PRESETS, load_content


SUPPORTED = "Content files (*.txt *.md *.py *.js *.sql *.csv);;All files (*.*)"


class ContentView(QWidget):
    def __init__(self, controller, storage, resolve_content, on_content_changed, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.storage = storage
        self._resolve = resolve_content
        self._on_changed = on_content_changed

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(20)

        head = QVBoxLayout()
        head.setSpacing(2)
        title = QLabel("Content")
        title.setObjectName("Headline")
        sub = QLabel("Manage the text the keyboard engine types.")
        sub.setObjectName("SubHeadline")
        head.addWidget(title)
        head.addWidget(sub)
        root.addLayout(head)

        body = QHBoxLayout()
        body.setSpacing(20)
        body.addLayout(self._build_left(), 5)
        body.addLayout(self._build_right(), 4)
        root.addLayout(body, 1)

        self.refresh()

    def _build_left(self):
        col = QVBoxLayout()
        col.setSpacing(20)

        file_card = Card("Content File", "❏")
        path_row = QHBoxLayout()
        self.path_lbl = QLabel()
        self.path_lbl.setStyleSheet(
            f"font-family: {FONT_MONO}; color: {Color.ON_SURFACE}; font-size: 12px;")
        self.path_lbl.setWordWrap(True)
        path_row.addWidget(self.path_lbl, 1)
        file_card.body_layout().addLayout(path_row)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        sel = QPushButton("Select File…")
        sel.setObjectName("Secondary")
        sel.clicked.connect(self._select_file)
        reload_btn = QPushButton("Reload")
        reload_btn.setObjectName("Secondary")
        reload_btn.clicked.connect(self.refresh)
        btn_row.addWidget(sel)
        btn_row.addWidget(reload_btn)
        btn_row.addStretch()
        file_card.body_layout().addLayout(btn_row)
        col.addWidget(file_card)

        preview_card = Card("Preview", "👁")
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setStyleSheet(
            f"QPlainTextEdit {{ background:{Color.SURFACE_LOWEST}; border:1px solid {Color.OUTLINE_VARIANT};"
            f" border-radius:4px; font-family:{FONT_MONO}; font-size:12px; color:{Color.ON_SURFACE_VARIANT}; }}")
        self.preview.setMinimumHeight(220)
        preview_card.add(self.preview)
        col.addWidget(preview_card, 1)
        return col

    def _build_right(self):
        col = QVBoxLayout()
        col.setSpacing(20)

        stats = Card("Statistics", "📊")
        grid = QGridLayout()
        grid.setSpacing(12)
        self.tile_chars = StatTile("Characters", "0")
        self.tile_lines = StatTile("Lines", "0")
        self.tile_words = StatTile("Words", "0")
        self.tile_dur = StatTile("Est. duration", "0h")
        grid.addWidget(self.tile_chars, 0, 0)
        grid.addWidget(self.tile_lines, 0, 1)
        grid.addWidget(self.tile_words, 1, 0)
        grid.addWidget(self.tile_dur, 1, 1)
        stats.body_layout().addLayout(grid)
        col.addWidget(stats)

        gen = Card("Generate New Content", "✨")
        preset_row = QHBoxLayout()
        preset_lbl = QLabel("Preset")
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(list(PRESETS.keys()))
        self.preset_combo.setCurrentText("Mixed")
        preset_row.addWidget(preset_lbl)
        preset_row.addWidget(self.preset_combo, 1)
        gen.body_layout().addLayout(preset_row)

        size_row = QHBoxLayout()
        size_lbl = QLabel("Target size (chars)")
        self.size_spin = QSpinBox()
        self.size_spin.setRange(5_000, 1_000_000)
        self.size_spin.setSingleStep(10_000)
        self.size_spin.setValue(120_000)
        size_row.addWidget(size_lbl)
        size_row.addWidget(self.size_spin, 1)
        gen.body_layout().addLayout(size_row)

        gen_btn = QPushButton("Generate Content")
        gen_btn.setObjectName("Primary")
        gen_btn.clicked.connect(self._generate)
        gen.add(gen_btn)

        self.gen_status = QLabel("")
        self.gen_status.setStyleSheet(f"color: {Color.ON_SURFACE_VARIANT}; font-size: 12px;")
        gen.add(self.gen_status)
        col.addWidget(gen)
        col.addStretch()
        return col

    # --- actions ---------------------------------------------------------

    def _select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select content file", "", SUPPORTED)
        if path:
            self.storage.set(path, "content", "file")
            self.storage.save()
            self.refresh()
            self._on_changed()

    def _generate(self):
        path = self._resolve()
        preset = self.preset_combo.currentText()
        target = self.size_spin.value()
        try:
            size = generate_content(path, preset, target, append=False)
            self.gen_status.setText(f"✓ Generated {size:,} characters to {os.path.basename(path)}.")
            self.refresh()
            self._on_changed()
        except Exception as e:  # noqa: BLE001
            self.gen_status.setText(f"✗ Generation failed: {e}")

    def refresh(self):
        path = self._resolve()
        self.path_lbl.setText(path)
        try:
            text = load_content(path)
        except Exception:
            text = ""
        chars = len(text)
        lines = text.count("\n") + 1 if text else 0
        words = len(text.split())
        # ~3.3 chars/sec sustained including chunk pauses (original estimate)
        hours = chars / 3.3 / 3600 if chars else 0
        self.tile_chars.set_value(f"{chars:,}")
        self.tile_lines.set_value(f"{lines:,}")
        self.tile_words.set_value(f"{words:,}")
        self.tile_dur.set_value(f"{hours:.1f}h")
        self.preview.setPlainText(text[:4000] + ("\n\n… (truncated)" if len(text) > 4000 else ""))
